#!/usr/bin/env python3
"""Regression tests for lint_prose_tells.py, driven by annotated fixtures.

Run from the repository root::

    python3 -m unittest discover -s tests/desloppify

Each fixture under ``fixtures/`` is a markdown file. A line that should
produce counted findings ends with an HTML comment listing their rule ids,
one id per expected finding::

    The boundary is situational, not fixed per pair. <!-- expect: CF003 -->

Words after the ids are commentary and ignored, so a known misfire can be
recorded in place: ``<!-- expect: PG003 (misfire: clock time) -->``. A line
with no comment expects no counted finding. The detector blanks HTML comments
before scanning, so the annotations cannot affect the result.

Two fixtures carry a file-level expectation instead: ``clean.md`` expects no
counted finding anywhere, and ``markdown_stripping.md`` expects no
line-anchored finding of any family, counted or not.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parents[1] / "desloppify" / "scripts" / "lint_prose_tells.py"
FIXTURES = HERE / "fixtures"
EXPECT_RE = re.compile(r"<!--\s*expect:(.*?)-->")
RULE_RE = re.compile(r"\b[A-Z]{2}\d{3}\b")


def run_detector(*paths: Path) -> tuple[int, list[dict]]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", *map(str, paths)],
        capture_output=True,
        text=True,
        check=False,
    )
    records = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    return proc.returncode, records


def findings_by_line(records: list[dict], counted_only: bool) -> dict[int, Counter]:
    out: dict[int, Counter] = {}
    for rec in records:
        if rec.get("record") != "finding" or rec["anchor"].get("kind") != "line":
            continue
        if counted_only and not rec["counted"]:
            continue
        out.setdefault(rec["anchor"]["line"], Counter())[rec["rule_id"]] += 1
    return out


def expectations(path: Path) -> dict[int, Counter]:
    out: dict[int, Counter] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = EXPECT_RE.search(line)
        if match:
            out[number] = Counter(RULE_RE.findall(match.group(1)))
    return out


class AnnotatedFixtures(unittest.TestCase):
    ANNOTATED = ("contrast_frames.md", "punctuation_glue.md", "importance_theater.md")

    def test_counted_findings_match_annotations(self) -> None:
        for name in self.ANNOTATED:
            path = FIXTURES / name
            with self.subTest(fixture=name):
                code, records = run_detector(path)
                self.assertEqual(code, 0)
                actual = findings_by_line(records, counted_only=True)
                expected = expectations(path)
                lines = sorted(set(actual) | set(expected))
                mismatches = [
                    f"line {n}: expected {dict(expected.get(n, {}))}, got {dict(actual.get(n, {}))}"
                    for n in lines
                    if actual.get(n, Counter()) != expected.get(n, Counter())
                ]
                self.assertEqual(mismatches, [], "\n".join(mismatches))


class AdvisoryFixtures(unittest.TestCase):
    """Advisory families never count, so their fixture compares every finding
    of those families, counted or not, and ignores every other family."""

    FAMILIES = {"object_agency", "copula_avoidance", "nominalisation"}

    def test_structure_findings_match_annotations(self) -> None:
        path = FIXTURES / "structure.md"
        code, records = run_detector(path)
        self.assertEqual(code, 0)
        scoped = [r for r in records if r.get("family") in self.FAMILIES]
        actual = findings_by_line(scoped, counted_only=False)
        expected = expectations(path)
        lines = sorted(set(actual) | set(expected))
        mismatches = [
            f"line {n}: expected {dict(expected.get(n, {}))}, got {dict(actual.get(n, {}))}"
            for n in lines
            if actual.get(n, Counter()) != expected.get(n, Counter())
        ]
        self.assertEqual(mismatches, [], "\n".join(mismatches))

    def test_nominal_density_falls_when_actions_return_to_verbs(self) -> None:
        def density(text: str) -> float:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "draft.md"
                path.write_text(text, encoding="utf-8")
                _, records = run_detector(path)
            return next(
                r["metrics"]["per_100_words"] for r in records if r.get("rule_id") == "ND001"
            )

        before = density("The implementation of the validation requires the creation of a document.")
        after = density("We validate the input before we create a document.")
        self.assertGreater(before, after)
        self.assertEqual(after, 0.0)


class FileLevelFixtures(unittest.TestCase):
    def test_clean_prose_has_no_counted_findings(self) -> None:
        code, records = run_detector(FIXTURES / "clean.md")
        self.assertEqual(code, 0)
        actual = findings_by_line(records, counted_only=True)
        self.assertEqual(actual, {}, f"counted findings on clean prose: {actual}")

    def test_non_prose_spans_produce_nothing(self) -> None:
        code, records = run_detector(FIXTURES / "markdown_stripping.md")
        self.assertEqual(code, 0)
        actual = findings_by_line(records, counted_only=False)
        self.assertEqual(actual, {}, f"findings inside non-prose spans: {actual}")


class ExitCodes(unittest.TestCase):
    def test_missing_path_exits_2(self) -> None:
        code, records = run_detector(FIXTURES / "does-not-exist.md")
        self.assertEqual(code, 2)
        self.assertTrue(any(r.get("record") == "error" for r in records))


if __name__ == "__main__":
    unittest.main()
