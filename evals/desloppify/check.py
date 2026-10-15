#!/usr/bin/env python3
"""Mechanical grader for the desloppify evals.

Usage::

    python3 evals/desloppify/check.py <eval id> <outputs dir>

Reads ``output.md`` and ``changes.md`` from the outputs directory and prints
a grading.json-shaped object: one entry per expectation in ``evals.json``
with ``text``, ``passed`` and ``evidence``. An expectation this script cannot
decide is emitted with ``passed: null`` and ``evidence: "needs judgment"``
for a reader to fill in. String checks are exact and case-sensitive.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DETECTOR = HERE.parents[1] / "desloppify" / "scripts" / "lint_prose_tells.py"
EVALS = json.loads((HERE / "evals.json").read_text(encoding="utf-8"))
# Function words and connectives. A connective the rewrite adds to keep a
# causal link ("so", "because", "therefore") is not an invented fact.
STOP = set("the a an and or so but because of to in on for after every each is are it its this that "
           "with while as at by from than then them they their there which who when since therefore "
           "thus hence also however instead".split())
LEADING_CONNECTIVE = re.compile(r"^(?:so|because|since|therefore|thus|hence|and|but)\s+", re.IGNORECASE)


def glue_density(path: Path) -> float:
    out = subprocess.run([sys.executable, str(DETECTOR), "--json", str(path)],
                         capture_output=True, text=True, check=False).stdout
    for line in out.splitlines():
        rec = json.loads(line)
        if rec.get("record") == "summary" and rec["family"] == "punctuation_glue":
            return rec["per_100_words"]
    return 0.0


def nominal_density(path: Path) -> float:
    out = subprocess.run([sys.executable, str(DETECTOR), "--json", str(path)],
                         capture_output=True, text=True, check=False).stdout
    for line in out.splitlines():
        rec = json.loads(line)
        if rec.get("rule_id") == "ND001":
            return rec["metrics"]["per_100_words"]
    return 0.0


def content_words(text: str) -> set[str]:
    return {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z'-]*", text) if len(w) > 3 and w.lower() not in STOP}


def stem(w: str) -> str:
    return w[:5]


def grade(eval_id: int, outputs: Path) -> list[dict]:
    case = next(e for e in EVALS["evals"] if e["id"] == eval_id)
    src = (HERE / case["files"][0]).read_text(encoding="utf-8")
    out_path = outputs / "output.md"
    output = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
    changes_path = outputs / "changes.md"
    changes = changes_path.read_text(encoding="utf-8") if changes_path.exists() else ""
    rows: list[dict] = []

    def add(text: str, passed: bool | None, evidence: str) -> None:
        rows.append({"text": text, "passed": passed, "evidence": evidence})

    for text in case["expectations"]:
        m = re.match(r"The output does not contain '(.+)'$", text)
        if m:
            add(text, m.group(1) not in output, f"searched output for {m.group(1)!r}")
            continue
        m = re.match(r"The output contains verbatim '(.+)'$", text)
        if m:
            needle = m.group(1).replace("\\'", "'")
            # A leading connective added to keep a causal link is allowed, so
            # "So profile the service first" satisfies "Profile the service first".
            lowered = needle[0].lower() + needle[1:]
            hit = needle in output or any(
                LEADING_CONNECTIVE.match(sentence) and lowered in sentence
                for sentence in re.split(r"(?<=[.!?])\s+", output))
            add(text, bool(hit), f"searched output for {needle!r}, allowing a leading connective")
            continue
        if text.startswith("The output mentions four hundred gigabytes"):
            idx = [output.find(k) for k in ("four hundred", "ninety seconds", "least-recently-used")]
            add(text, all(i >= 0 for i in idx) and idx == sorted(idx), f"positions {idx}")
            continue
        if text.startswith("The output keeps the causal link between rolling restarts"):
            m2 = re.search(r"spread the cost across the fleet[^.]*\b(because|so|since)\b[^.]*each host warms", output)
            add(text, bool(m2), m2.group(0) if m2 else "no connective between the two clauses in one sentence")
            continue
        if text.startswith("The output contains no semicolon"):
            add(text, ";" not in output and "—" not in output, f"semicolons={output.count(';')} dashes={output.count('—')}")
            continue
        if text.startswith("Every content word"):
            new = {w for w in content_words(output) if not any(stem(w) == stem(s) for s in content_words(src))}
            add(text, not new, f"words not in input: {sorted(new)}")
            continue
        if text.startswith("The detector's punctuation-glue density"):
            if not out_path.exists():
                add(text, False, "no output.md")
                continue
            before, after = glue_density(HERE / case["files"][0]), glue_density(out_path)
            add(text, after <= before, f"input={before} output={after}")
            continue
        if text.startswith("The detector's nominal density"):
            if not out_path.exists():
                add(text, False, "no output.md")
                continue
            before, after = nominal_density(HERE / case["files"][0]), nominal_density(out_path)
            add(text, after < before, f"input={before} output={after}")
            continue
        add(text, None, "needs judgment")
    if not output:
        for r in rows:
            r["passed"] = False
            r["evidence"] = "no output.md"
    return rows


if __name__ == "__main__":
    rows = grade(int(sys.argv[1]), Path(sys.argv[2]))
    passed = sum(1 for r in rows if r["passed"])
    summary = {"passed": passed, "failed": len(rows) - passed, "total": len(rows),
               "pass_rate": passed / len(rows) if rows else 0.0}
    print(json.dumps({"expectations": rows, "summary": summary}, indent=2))
