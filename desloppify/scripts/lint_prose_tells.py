#!/usr/bin/env python3
"""Deterministic prose-tells detector.

Measures the mechanically detectable share of the desloppify catalogue
(``../SKILL.md``) over markdown and bare text. Run::

    python3 lint_prose_tells.py [--details] [--json] PATH [PATH ...]

Every rule is a named surface proxy: it matches literal text shapes, and its
known misfires are listed with it. The output is a report. Judging the
findings and rewriting the text are left to the reader.

Exit codes
----------

``0``  ran to completion (findings do not change the exit code)
``2``  input error: a path did not exist, no given path held a scannable
       file, or a file could not be decoded

Anchoring
---------

Findings carry ``{"kind": "line", "line": N}``, the 1-based line of the
original file. Non-prose spans are blanked in place with same-length
whitespace rather than deleted, so every character offset in the measured
text still indexes the original file exactly.

Non-prose stripping
-------------------

Markdown: front matter, fenced code blocks, pipe tables, ATX headings, HTML
comments, inline code spans and link URLs are blanked; list and blockquote
markers are blanked but their text is kept; emphasis markers are blanked but
the emphasised text is kept. A fence closes only on a run of the same
character at least as long as the opener; code spans accept multi-backtick
delimiters; a pipe table is found by its ``--- | ---`` delimiter row, which
also covers the common no-leading-pipe form. Bare-text mode blanks emphasis
markers only. Everything else is prose.

Stripping leaves punctuation behind, and orphaned punctuation is not glue:
blanking a code span leaves the dash beside it joining nothing. So the
punctuation rules evaluate against the pre-strip text. A mark whose adjacent
operand carried content in the original but carries none after stripping is
notation punctuation and is not counted (``Segment.operand_stripped``).

Sentence segmentation
---------------------

A documented simple splitter: split after ``.``/``!``/``?`` (optionally
followed by a closing quote or bracket) when the next non-space character
opens a new sentence. Guards: single-letter initials, decimals (``3.5``),
ellipses and two classes of abbreviation.

``BOUND_ABBREVIATIONS`` ("Dr.", "St.", "e.g.", "No.") never end a sentence,
so their guard is unconditional. ``SENTENCE_FINAL_ABBREVIATIONS`` ("etc.",
"al.", "approx.") routinely do, so their guard applies only when the
following token does not open a new sentence. An unconditional guard there
fused two sentences into one and corrupted the sentence denominator plus
every adjacent-repetition pair across the join.

Known failure modes, all accepted:

1. Abbreviations outside both closed lists split a sentence in two.
2. A ``SENTENCE_FINAL_ABBREVIATIONS`` member followed by a capitalised
   proper noun inside the same sentence splits it in two.
3. An ordinary English word that collides with a ``BOUND_ABBREVIATIONS``
   entry fuses two real sentences into one. ``"no"`` is the live case: it is
   in the list for "No. 3", so ``I said no. Then I left.`` counts as one
   sentence. Dropping the entry would trade this for the over-split on
   numbered references, so the collision is accepted rather than fixed.
4. A sentence-ending period inside a quotation splits at the wrong place.
5. Text with no terminal punctuation (a heading-shaped line, a bare list
   item) is treated as one sentence however long it is.
6. Semicolon- and dash-joined clauses count as one sentence, deliberately.
   Punctuation glue is what several rules measure.
7. Adjacent-repetition findings inherit every one of these errors, because
   they compare consecutive segmentation output.

Family dispositions
-------------------

Each family carries a disposition, which says how far its findings are
trusted (``FAMILY_DISPOSITION``; emitted on every finding and summary
record):

``keep``          the finding is actionable as it stands: address or exempt each
``density_only``  the per-100-words number carries the signal, not the rows
``advisory``      surfaced for a reader's judgement, never counted
``report_only``   a measurement rather than a finding, never counted

``keep`` and ``density_only`` findings reach the headline density;
``advisory`` and ``report_only`` never do. ``--details`` labels every row
with its disposition so an advisory row cannot be read as a trusted one.

Rule families
-------------

**punctuation_glue** (density_only): PG001 em-dash (every U+2014 and spaced
``--``; the en-dash is excluded as range typography), PG002 semicolon outside
an enumerated series or list line, PG003 colon not introducing a list,
column, or quoted example. An inline list is a remainder with two or more
commas, and a colon with no whitespace on either side is a path reference
or clock time. Each rule skips a mark whose operands were stripped. Known
misfire: a dash pair around a parenthetical.

**contrast_frames** (keep): literal frames for the catalogue's contrast
patterns. CF001 not-just escalation, CF002 more-than escalation, CF003
clause-final ", not Y", CF004 clause-final ", never Y", CF005 "rather than",
CF006 negative-definition opener ("This is not..."), CF007 do-support
minimiser ("does not simply describe"), CF008 copular antithesis ("it's not
X, it's Y"), CF009 not-really restatement, CF010 "not merely". CF007-CF010
were mined from real LLM drafts rather than derived from the catalogue.
A match inside a short double-quoted span is reported as MN001 instead.
Misfire class for the whole family: a contrast that corrects a wrong
assumption the reader actually brings is legitimate, and no regex knows
that.

**adjacent_repetition** (advisory): AR001 shared opener word (minus a
function-word stoplist), AR002 shared opener bigram, AR003 shared connective,
AR004 shared punctuation shape within a paragraph. Comparison runs over the
whole document's sentence stream, so a pair that straddles a paragraph break
still counts. A repeated opener is often deliberate, which is why the family
is advisory.

**importance_theater** (keep): IT001 performative insight ("crucially", "the
key insight"), IT002 insistence intensifiers ("genuinely", "actually"),
IT003 performative candour ("honestly", "to be clear"). Whole-word matches
only, so "actually" is a finding and "factually" is not. IT002 yields to a
contrast frame that contains the same word ("does not simply retry" is
CF007 alone). A match inside a short double-quoted span is reported as
MN001 instead; a quoted span over 80 characters stays in scope.

**lexical_tells** (advisory): LX001 word or phrase from
``lexical_tells.txt``, a short list of the current model generation's
fashion vocabulary ("load-bearing", "blast radius", "mint"). The list is
data beside the script: entries rotate out when the tic does, and a missing
or empty file disables the family. Each word has legitimate uses, which is
why the family is advisory.

**object_agency** (advisory): AG001 a determiner, at most one modifier, a
noun for something that is not a person (``AGENT_NOUNS``: text, note, page,
screen, rule, brief, app…), then a verb of saying, showing, meaning, wanting
or serving (``AGENT_VERBS``: names, shows, tells, explains, serves,
carries…). A mass noun (``MASS_AGENT_NOUNS``: chrome, feedback…) also
matches bare at the start of a sentence. AG002 is the same shape with a noun for an absence
(``ABSENCE_NOUNS``) or any noun after "empty", where nothing is there to
act. The verbs a field uses
literally for its own objects ("stress falls", "the function returns") are
left off the verb list. Misfires: conventions a register accepts ("Figure 2
shows", "the spec says"), and a person-noun outside the list is never
caught.

**copula_avoidance** (advisory): CA001 an inflated verb standing in for
"is" or "has" ("serves as", "acts as", "stands as", "bears the name").
Misfire: a literal role ("the host serves as a relay while the primary
restarts").

**nominalisation** (advisory): NM001 a light verb whose object is a
verb-derived noun ("make a decision", "provide an explanation"), NM002 a
nominalisation after "through" or "by means of" ("respected through
clarity"), NM003 an action noun between an article and "of" ("the
implementation of the cache"), NM004 a possessive actor, an action noun,
then "of" ("the system's handling of the request"). All four carry an
action in a noun. NM003 and NM004 also take the action nouns in
``LISTED_ACTION_NOUNS`` ("removal", "failure", "change") and, before "of",
"-ing" nouns outside ``ING_STOPLIST``. NM003 yields to an NM001 or NM002
match over the same words. Misfires: an established term ("take action",
"the definition of done") and a noun that names a thing rather than an
act.

**dangling_possessive** (keep): DP001 a possessive whose noun has been
dropped, after a copula ("the decision is the maintainer's", "the call is
yours", "the cut is the maintainer's to make"). Once a sentence has one, a
later clause that drops the copula too ("…, the risk the user's") or
follows a contrast ("…, not the adapter's") also counts. DP002 marks a
sentence with two or more. An "'s" after a word in ``CONTRACTION_HOSTS``
("it's", "that's") is skipped. Literal ownership of a thing ("the laptop
is Sam's") matches as well, and the catalogue rewrites it like the rest.

**pronoun_reference** (advisory): PR001 a paragraph that opens on "Its" or
"Their", before anything in the paragraph they could point back to. PR002 a
fronted phrase that names its owner only as a possessive, then a pronoun
that must point back to that owner ("In Smith's proposal, he argues").
Misfire for PR001: a paragraph under a heading that names the referent.

**mention** (advisory): MN001 a match of any rule above, except punctuation
glue, adjacent repetition and lexical tells, that starts inside a short
double-quoted span (``QUOTED_SPAN``). A quoted phrase is usually a mention:
'Delete "crucially"' talks about the word. The row names the rule it stands
in for, so a quoted sentence the writer also asserts stays visible without
counting against the text.

**negation** (report_only): NG001 density of "not" (including "n't"
contractions and "cannot"), NG002 density of "never". Contrast abuse
concentrates negation, so the input text and the edited text are compared on
these numbers. Ordinary scoped negation keeps the floor above zero, so no
threshold is committed to and single occurrences are not listed.

**nominal_density** (report_only): ND001 density of words ending in
"-tion", "-sion", "-ment", "-ance", "-ence", "-ity" or "-ness" after a stem of
three or more letters, minus ``NOMINAL_STOPLIST`` (concrete nouns that end
that way by accident: "document", "sentence"). A pass that turns hidden
actions back into verbs lowers it, so input and output are compared, as
with negation. Nominalisations without a suffix ("encounter", "change") are
not counted, and no threshold is committed to.

**uniformity** (report_only): UM001 sentence-length mean, stddev and
coefficient of variation; UM002 sentence-opener diversity. Suppressed below
``UNIFORMITY_MIN_SENTENCES`` sentences. Uniform sentence length and low
opener diversity are LLM tendencies, but no benchmark is committed to here;
the numbers are reported for a reader who has a baseline.

**cadence_triads** (report_only): CT001 comma-parallel three-item run where
the second and third items are within one word of each other in length. The
first item's left edge is not recoverable without parsing. Cannot
distinguish a factual list from a rhythmic triad and does not claim to.

Determinism
-----------

Two runs over the same input produce byte-identical output: paths are walked
in sorted order, findings are emitted in document order, floats are rounded
to four places, and JSON is ASCII-escaped. No timestamps, no run ids, no
hostnames.

Evidence quotes
---------------

A quote is the matched sentence with whitespace collapsed, capped at 160
characters plus elision markers. When the sentence is longer than the cap,
the window is centred on the matched span, so the quote always contains the
match. Elided ends are marked with ``…``.
"""

from __future__ import annotations

import argparse
import bisect
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

TOOL_VERSION = "1.5.0"

# Per-family disposition: how far each family's findings are trusted, in
# declaration order (which is also report order). See the module docstring.
FAMILY_DISPOSITION: dict[str, str] = {
    "punctuation_glue": "density_only",
    "contrast_frames": "keep",
    "adjacent_repetition": "advisory",
    "importance_theater": "keep",
    "lexical_tells": "advisory",
    "object_agency": "advisory",
    "copula_avoidance": "advisory",
    "nominalisation": "advisory",
    "dangling_possessive": "keep",
    "pronoun_reference": "advisory",
    "mention": "advisory",
    "negation": "report_only",
    "nominal_density": "report_only",
    "uniformity": "report_only",
    "cadence_triads": "report_only",
}

# Only `keep` and `density_only` findings reach the headline density.
# Deriving the flag from the disposition keeps one source of truth: a
# re-disposition changes the line above and nothing else.
COUNTED_DISPOSITIONS = frozenset({"keep", "density_only"})

FAMILY_COUNTED: dict[str, bool] = {
    family: disposition in COUNTED_DISPOSITIONS
    for family, disposition in FAMILY_DISPOSITION.items()
}

# rule id -> (family, version, one-line literal description)
RULES: dict[str, tuple[str, int, str]] = {
    "PG001": ("punctuation_glue", 2, "em-dash used as a connective"),
    "PG002": ("punctuation_glue", 2, "semicolon outside an enumerated series or list"),
    "PG003": ("punctuation_glue", 4, "colon not introducing a list, column or quoted example"),
    "CF001": ("contrast_frames", 2, "not-just escalation"),
    "CF002": ("contrast_frames", 2, "more-than escalation"),
    "CF003": ("contrast_frames", 3, "clause-final ', not Y'"),
    "CF004": ("contrast_frames", 2, "clause-final ', never Y'"),
    "CF005": ("contrast_frames", 2, "'X rather than Y'"),
    "CF006": ("contrast_frames", 2, "negative-definition opener"),
    "CF007": ("contrast_frames", 2, "do-support minimiser ('does not simply V')"),
    "CF008": ("contrast_frames", 2, "copular antithesis (\"it's not X, it's Y\")"),
    "CF009": ("contrast_frames", 2, "not-really restatement"),
    "CF010": ("contrast_frames", 2, "'not merely'"),
    "AR001": ("adjacent_repetition", 3, "consecutive sentences share an opener word"),
    "AR002": ("adjacent_repetition", 3, "consecutive sentences share an opener bigram"),
    "AR003": ("adjacent_repetition", 3, "consecutive sentences share a connective"),
    "AR004": ("adjacent_repetition", 3, "consecutive sentences share a punctuation shape"),
    "IT001": ("importance_theater", 3, "performative-insight frame"),
    "IT002": ("importance_theater", 4, "insistence intensifier"),
    "IT003": ("importance_theater", 3, "performative candour"),
    "LX001": ("lexical_tells", 1, "word from the current fashion-vocabulary list"),
    "AG001": ("object_agency", 1, "object takes a verb of saying, showing, meaning or wanting"),
    "AG002": ("object_agency", 1, "an absence takes a verb of saying, showing, meaning or wanting"),
    "CA001": ("copula_avoidance", 1, "inflated verb in place of 'is' or 'has'"),
    "NM001": ("nominalisation", 1, "light verb with a nominalised action as its object"),
    "NM002": ("nominalisation", 1, "nominalisation after 'through' or 'by means of'"),
    "NM003": ("nominalisation", 1, "action noun between an article and 'of'"),
    "NM004": ("nominalisation", 1, "possessive actor, an action noun, then 'of'"),
    "DP001": ("dangling_possessive", 1, "possessive whose noun is dropped after a copula"),
    "DP002": ("dangling_possessive", 1, "two or more dangling possessives in one sentence"),
    "PR001": ("pronoun_reference", 1, "paragraph opens on 'Its' or 'Their'"),
    "PR002": ("pronoun_reference", 1, "pronoun whose only antecedent is a possessive"),
    "MN001": ("mention", 1, "another rule's match inside a short quoted span"),
    "NG001": ("negation", 1, "density of 'not' (including contractions)"),
    "NG002": ("negation", 1, "density of 'never'"),
    "ND001": ("nominal_density", 1, "density of suffix-derived nominalisations"),
    "UM001": ("uniformity", 1, "sentence-length mean / stddev / coefficient of variation"),
    "UM002": ("uniformity", 1, "sentence-opener diversity"),
    "CT001": ("cadence_triads", 1, "comma-parallel three-item run"),
}

UNIFORMITY_MIN_SENTENCES = 15

SCANNED_SUFFIXES = {".md", ".markdown", ".txt"}

WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")
# Any alphanumeric character in any script. Used to ask whether a punctuation
# mark's neighbouring operand still carries content after stripping.
CONTENT_CHAR = re.compile(r"[^\W_]")

# Abbreviations whose trailing period never ends a sentence, because the next
# token belongs to the same phrase: "Dr. Smith", "St. Petersburg", "No. 3",
# "Fig. 2". The guard here is unconditional. A following capital is the
# normal case, so it cannot be used as a split signal.
BOUND_ABBREVIATIONS = frozenset(
    {
        "e.g",
        "i.e",
        "cf",
        "vs",
        "fig",
        "no",
        "vol",
        "ch",
        "sec",
        "dr",
        "mr",
        "mrs",
        "ms",
        "prof",
        "st",
        "jan",
        "feb",
        "mar",
        "apr",
        "jun",
        "jul",
        "aug",
        "sep",
        "sept",
        "oct",
        "nov",
        "dec",
    }
)

# Abbreviations that routinely end a sentence ("...vowels, etc. Also we
# cover..."). Their guard is conditional: it suppresses the split only when
# the following token does not open a new sentence.
SENTENCE_FINAL_ABBREVIATIONS = frozenset({"etc", "al", "approx"})

OPENER_STOPWORDS = frozenset(
    {
        "the", "a", "an", "it", "this", "that", "these", "those", "there", "here",
        "in", "on", "at", "for", "to", "of", "and", "but", "or", "if", "when",
        "you", "we", "i", "they", "he", "she", "his", "her", "their", "its",
        "is", "are", "was", "were", "be", "as", "by", "with", "from", "so",
    }
)

CONNECTIVES = frozenset(
    {
        "also", "however", "but", "so", "and", "because", "therefore", "though",
        "although", "yet", "meanwhile", "instead", "moreover", "furthermore",
        "still", "then", "thus", "hence",
    }
)

INSIGHT_FRAMES = (
    "crucially",
    "importantly",
    "notably",
    "the key insight",
    "the key point",
    "the real question",
    "what this really means",
    "what really matters",
    "what matters here",
    "it is worth noting",
    "it's worth noting",
    "worth noting",
    "let's unpack",
    "let us unpack",
    "you might wonder",
    "the important thing is",
    "here's the thing",
)

INTENSIFIERS = ("genuinely", "actually", "really", "simply", "exactly")

CANDOUR_FRAMES = (
    "honestly",
    "frankly",
    "to be clear",
    "honest warning",
    "let's be honest",
    "let us be honest",
    "in all honesty",
    "truth be told",
)

# AG001/AG002 subjects: things that are not people and that drafts hand
# verbs of saying, showing, meaning, wanting or serving. AG002 takes the
# subset that names an absence, where nothing is there to act at all.
AGENT_NOUNS = (
    "app", "brief", "button", "card", "chrome", "correction", "course", "data",
    "design", "doc", "document", "evidence", "example", "explanation",
    "feedback", "field", "form", "heading", "interface", "label", "lesson",
    "link", "list", "menu", "message", "note", "page", "paragraph", "prompt",
    "report", "rule", "screen", "section", "sentence", "skill", "spec",
    "string", "system", "table", "template", "text", "tool", "verdict",
)
ABSENCE_NOUNS = ("absence", "blank", "gap", "silence", "void")
# Mass nouns that open a sentence without a determiner ("Chrome serves…").
MASS_AGENT_NOUNS = ("chrome", "data", "evidence", "feedback", "text")
# Base forms; the third-person singular is derived. Verbs a field uses
# literally for its own objects ("falls", "marks", "returns") are not here.
AGENT_VERBS = (
    "address", "admit", "apologise", "apologize", "argue", "ask", "bring",
    "carry", "celebrate", "claim", "decide", "deliver", "demand", "describe",
    "encourage", "expect", "explain", "hide", "identify", "insist", "invite", "know",
    "mean", "name", "promise", "reassure", "refuse", "remind", "resist",
    "reveal", "reward", "say", "serve", "show", "speak", "teach", "tell",
    "trust", "urge", "want", "warn", "welcome",
)
AGENT_DETERMINERS = (
    "a", "an", "any", "each", "every", "its", "our", "that", "the", "their",
    "this", "your",
)

# CA001: an inflated verb standing in for "is" or "has".
COPULA_FRAMES = (
    "serves as", "serve as", "served as", "serving as",
    "acts as", "act as", "acted as", "acting as",
    "stands as", "stand as", "stood as",
    "functions as", "function as", "functioned as",
    "bears the name", "bear the name", "bore the name",
)

# NM001: a light verb whose object is a nominalisation carrying the action
# ("make a decision", "provide an explanation").
LIGHT_VERB_FORMS = (
    "achieve", "achieves", "achieved", "achieving",
    "carry out", "carries out", "carried out", "carrying out",
    "conduct", "conducts", "conducted", "conducting",
    "give", "gives", "gave", "given", "giving",
    "make", "makes", "made", "making",
    "offer", "offers", "offered", "offering",
    "perform", "performs", "performed", "performing",
    "provide", "provides", "provided", "providing",
    "reach", "reaches", "reached", "reaching",
    "take", "takes", "took", "taken", "taking",
    "undertake", "undertakes", "undertook", "undertaken", "undertaking",
)
# ND001 counts derivational suffixes. These words end in one by accident
# or name concrete things, and are left out of the count.
NOMINAL_STOPLIST = frozenset(
    {
        "audience", "balance", "business", "city", "comment", "commitment", "community",
        "condition", "definition", "department", "destination", "dimension",
        "distance", "document", "element", "entity", "environment", "evidence",
        "experiment", "fraction", "fragment", "function", "government",
        "information", "instance", "instrument", "location", "moment", "option",
        "portion", "position", "proportion", "provenance", "question", "section",
        "segment", "sentence", "session", "silence", "station", "substance",
        "university", "version",
    }
)
# NM003 and NM004 also take action nouns that no suffix rule can find:
# "-al", "-ure" and "-age" are too common as plain endings, and a noun
# converted from a verb with no ending ("change", "review") has no shape.
LISTED_ACTION_NOUNS = (
    "analysis", "approval", "arrival", "attempt", "breakage", "change", "closure",
    "decrease", "delay", "denial", "departure", "disclosure", "dismissal",
    "disposal", "exposure", "failure", "increase", "leakage", "loss", "proposal",
    "refusal", "release", "removal", "renewal", "request", "retrieval", "reversal",
    "review", "survival", "update", "usage", "use", "withdrawal",
)
# NM003 takes "-ing" nouns before "of" ("the handling of"). These name
# things or fixed senses instead of an action.
ING_STOPLIST = frozenset(
    {
        "beginning", "building", "ceiling", "ending", "evening", "heading",
        "meaning", "morning", "nothing", "padding", "setting", "sibling",
        "something", "spelling", "string", "substring", "wording",
    }
)
# DP001 and NM004 read "'s" as a possessive. After these words it is a
# contraction of "is" or "has" ("it's", "that's").
CONTRACTION_HOSTS = frozenset(
    {"he", "here", "how", "it", "let", "one", "she", "that", "there", "what", "where", "who"}
)
# DP001: a copula, then a possessive whose noun has been dropped ("the
# decision is the maintainer's").
POSSESSIVE_COPULAS = (
    "is", "are", "was", "were", "remain", "remains", "remained",
    "stay", "stays", "stayed", "become", "becomes", "became",
)
INDEPENDENT_POSSESSIVES = ("hers", "mine", "ours", "theirs", "yours")
# PR002: a fronted phrase that names its owner only in a possessive, then a
# pronoun that has to point back at that owner ("In Smith's proposal, he").
FRONTING_PREPOSITIONS = (
    "according to", "at", "despite", "for", "from", "in", "on", "throughout",
    "under", "within",
)


def _phrase_pattern(phrases: tuple[str, ...]) -> re.Pattern[str]:
    """Word-boundary alternation over a closed literal phrase list, longest first.

    The alternation must stay wrapped in a non-capturing group. Alternation
    binds looser than concatenation, so without the group the lookarounds
    attach to the first and last alternatives only, and every phrase between
    them matches mid-word: "actually" inside "factually".
    """
    ordered = sorted(phrases, key=len, reverse=True)
    body = "|".join(re.escape(p).replace(r"\ ", r"\s+") for p in ordered)
    return re.compile(rf"(?<![A-Za-z])(?:{body})(?![A-Za-z])", re.IGNORECASE)


LEXICAL_TELLS_FILE = Path(__file__).resolve().with_name("lexical_tells.txt")


def _load_lexical_tells(path: Path) -> re.Pattern[str] | None:
    """Compile the fashion-vocabulary list, or ``None`` when it is absent or empty.

    The list is data, not code: one entry per line, ``#`` comments and blank
    lines ignored, matched with the same word-boundary semantics as the
    importance-theater phrase lists.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    phrases = tuple(
        line.strip()
        for line in raw.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    return _phrase_pattern(phrases) if phrases else None


# "cannot" carries its own "not" without a word boundary, so it is listed
# explicitly; "n't" catches every contraction in one shape.
NOT_RE = re.compile(r"\bnot\b|\bcannot\b|n['’]t\b", re.IGNORECASE)
NEVER_RE = re.compile(r"\bnever\b", re.IGNORECASE)

INSIGHT_RE = _phrase_pattern(INSIGHT_FRAMES)
INTENSIFIER_RE = _phrase_pattern(INTENSIFIERS)
CANDOUR_RE = _phrase_pattern(CANDOUR_FRAMES)
LEXICAL_RE = _load_lexical_tells(LEXICAL_TELLS_FILE)
COPULA_RE = _phrase_pattern(COPULA_FRAMES)


def _third_person(verb: str) -> str:
    if verb.endswith(("s", "sh", "ch", "x", "z")):
        return verb + "es"
    if verb.endswith("y") and verb[-2:-1] not in "aeiou":
        return verb[:-1] + "ies"
    return verb + "s"


def _agent_pattern(nouns: tuple[str, ...], mass: tuple[str, ...] = ()) -> re.Pattern[str]:
    """Determiner, at most one modifier, a listed noun, then a listed verb.

    A singular noun takes the third-person form and a plural noun the base
    form. The modifier slot admits "an empty screen names" and also lets a
    compound noun through ("the error message tells"). A ``mass`` noun also
    matches bare at the start of a sentence.
    """
    det = "|".join(AGENT_DETERMINERS)
    noun = "|".join(nouns)
    singular = "|".join(_third_person(v) for v in AGENT_VERBS)
    base = "|".join(AGENT_VERBS)
    body = (
        rf"(?<![A-Za-z])(?:{det})\s+(?:[A-Za-z][\w'’-]*\s+)?"
        rf"(?:(?:{noun})\s+(?:{singular})|(?:{noun})s\s+(?:{base}))(?![A-Za-z])"
    )
    if mass:
        body += rf"|(?:^|(?<=[.!?]\s))(?:{'|'.join(mass)})\s+(?:{singular})(?![A-Za-z])"
    return re.compile(body, re.IGNORECASE | re.MULTILINE)


AGENT_RE = _agent_pattern(AGENT_NOUNS, MASS_AGENT_NOUNS)
ABSENCE_AGENT_RE = _agent_pattern(ABSENCE_NOUNS)
# Any noun after "empty" names an absence ("an empty space names…").
EMPTY_AGENT_RE = re.compile(
    rf"(?<![A-Za-z])(?:{'|'.join(AGENT_DETERMINERS)})\s+empty\s+[A-Za-z]+\s+"
    rf"(?:{'|'.join(_third_person(v) for v in AGENT_VERBS)}|{'|'.join(AGENT_VERBS)})(?![A-Za-z])",
    re.IGNORECASE,
)

# A nominalisation by suffix: three or more letters of stem, then one of the
# derivational endings. NM001 takes the verb-derived endings only; NM002 and
# ND001 add the adjective-derived "-ity" and "-ness".
VERBAL_NOMINAL = r"[A-Za-z]{3,}(?:tion|sion|ment|ance|ence)s?"
ANY_NOMINAL = r"[A-Za-z]{3,}(?:tion|sion|ment|ance|ence|ity|ness)s?"
MODIFIER = r"(?:[A-Za-z][\w'’-]*\s+)?"

# Joined outside the f-string: a backslash inside an f-string expression is
# a syntax error before Python 3.12.
_LIGHT_VERB_ALT = "|".join(f.replace(" ", r"\s+") for f in LIGHT_VERB_FORMS)
LIGHT_VERB_RE = re.compile(
    rf"(?<![A-Za-z])(?:{_LIGHT_VERB_ALT})"
    rf"\s+(?:a|an|the|some|any|its|their|our|this|further)\s+{MODIFIER}"
    rf"{VERBAL_NOMINAL}(?![A-Za-z])",
    re.IGNORECASE,
)
# NM002: an abstract noun after "through" or "by means of" carrying the
# manner of an action ("respected through clarity").
THROUGH_NOMINAL_RE = re.compile(
    rf"(?<![A-Za-z])(?:through|by\s+means\s+of)\s+{MODIFIER}{ANY_NOMINAL}(?![A-Za-z])",
    re.IGNORECASE,
)
NOMINAL_RE = re.compile(rf"(?<![A-Za-z]){ANY_NOMINAL}(?![A-Za-z])", re.IGNORECASE)

# One word with no apostrophe, so a possessive cannot fill a modifier slot.
PLAIN = r"[A-Za-z][\w-]*"
_LISTED_ACTION = rf"(?:{'|'.join(LISTED_ACTION_NOUNS)})(?:e?s)?"
# NM003: an action noun between an article and "of" ("the implementation
# of the cache"). The noun group is checked against the stoplists.
OF_NOMINAL_RE = re.compile(
    rf"(?<![A-Za-z])(?:the|a|an)\s+(?:{PLAIN}\s+)?"
    rf"(?P<noun>{VERBAL_NOMINAL}|{_LISTED_ACTION}|[A-Za-z]{{3,}}ing)\s+of(?![A-Za-z])",
    re.IGNORECASE,
)
# A possessive word: "maintainer's", or the plural "maintainers'". The owner
# group is checked against CONTRACTION_HOSTS.
POSSESSIVE_WORD = rf"(?P<owner>[A-Za-z][\w-]*)(?:['’]s|s['’])(?![A-Za-z])"
# NM004: a possessive actor, an action noun, then "of" ("the system's
# handling of the request"). Both the actor and the object of the action
# sit in noun phrases. Without the "of" the shape is mostly a plain noun
# with an owner ("the brief's reference").
POSSESSIVE_NOMINAL_RE = re.compile(
    rf"(?<![\w'’]){POSSESSIVE_WORD}\s+(?:{PLAIN}\s+)?"
    rf"(?P<noun>{VERBAL_NOMINAL}|{_LISTED_ACTION}|[A-Za-z]{{3,}}ing)\s+of(?![A-Za-z])",
    re.IGNORECASE,
)
# The possessive ends its clause: punctuation, a dash, the end of the text,
# or a short tail that keeps the noun dropped ("the maintainer's to make").
_CLAUSE_END = (
    r"(?=\s*(?:[,.;:!?)\]]|—|--|$)"
    r"|\s+(?:to\s+[A-Za-z]+|alone|and|or|not|too)(?![A-Za-z]))"
)
_POSSESSIVE_DET = r"(?:the|a|an|this|that|each|every|our|your|their|its)"
PREDICATIVE_POSSESSIVE_RE = re.compile(
    rf"(?<![A-Za-z])(?:{'|'.join(POSSESSIVE_COPULAS)})(?:\s+[A-Za-z]+ly)?\s+"
    rf"(?:(?:{_POSSESSIVE_DET}\s+(?:{PLAIN}\s+)?)?{POSSESSIVE_WORD}"
    rf"|(?:{'|'.join(INDEPENDENT_POSSESSIVES)})(?![A-Za-z])){_CLAUSE_END}",
    re.IGNORECASE | re.MULTILINE,
)
# A later clause that drops the copula as well ("…, the risk the user's").
# Searched only after a predicative possessive in the same sentence.
GAPPED_POSSESSIVE_RE = re.compile(
    rf"(?:[,;]|—|(?<![A-Za-z])and)\s+(?:and\s+)?{_POSSESSIVE_DET}\s+(?:{PLAIN}\s+){{1,2}}?"
    rf"(?:(?:the|a|an)\s+)?{POSSESSIVE_WORD}(?=\s*(?:[,.;:!?)\]]|—|--|$))",
    re.IGNORECASE | re.MULTILINE,
)
# The same after a contrast, with the noun dropped as well ("…is the
# extractor's, not the adapter's").
CONTRAST_POSSESSIVE_RE = re.compile(
    rf"(?<![A-Za-z])(?:not|but|nor|rather\s+than)\s+(?:{_POSSESSIVE_DET}\s+)?(?:{PLAIN}\s+)?"
    rf"{POSSESSIVE_WORD}(?=\s*(?:[,.;:!?)\]]|—|--|$))",
    re.IGNORECASE | re.MULTILINE,
)
# PR001: a paragraph that opens on a possessive pronoun, before anything it
# could point back to.
PARAGRAPH_PRONOUN_RE = re.compile(r"\s*(?:Its|Their)(?![A-Za-z])")
# PR002: the owner appears only as a possessive in a fronted phrase, and the
# main clause opens on a pronoun ("In Smith's proposal, he argues").
_FRONTING_ALT = "|".join(p.replace(" ", r"\s+") for p in FRONTING_PREPOSITIONS)
POSSESSIVE_ANTECEDENT_RE = re.compile(
    rf"\s*(?:{_FRONTING_ALT})\s+(?:(?:the|a|an|this|that)\s+)?(?:{PLAIN}\s+)?{POSSESSIVE_WORD}"
    rf"\s+(?:{PLAIN}\s+){{0,3}}?{PLAIN}\s*,\s+(?:he|she|they|it)(?![A-Za-z])",
    re.IGNORECASE,
)

# PG001's target is the em-dash (U+2014) used as a prose connective, plus the
# ASCII `--` convention for it. The en-dash (U+2013) is excluded outright: it
# joins tokens in ranges and pairs ("pages 3-7"), which is typography rather
# than glue.
EMDASH_RE = re.compile(r"—|(?<=\s)--(?=\s)")

# PG003's quoted-example exemption: a colon whose remainder opens with one of
# these shapes introduces a quoted example. A module-level constant so a
# wrapper adding its own quoting notation can extend the pattern.
COLON_EXAMPLE_PREFIX = re.compile(r"^\s*[\"'“«]")

# A short double-quoted span is a mention, not a use: 'Delete "crucially"
# wherever it appears' talks about the word. A match that starts inside one
# is reported as MN001 instead of under its own rule. The length cap keeps a
# quoted paragraph of draft text in scope. A span may cross a single line
# break, because markdown source wraps prose, but not a blank line.
QUOTED_SPAN = re.compile(
    r"\"(?:[^\"\n]|\n(?![ \t]*\n)){1,80}\"|“(?:[^”\n]|\n(?![ \t]*\n)){1,80}”"
)


def quoted_spans(text: str) -> list[tuple[int, int]]:
    return [(m.start(), m.end()) for m in QUOTED_SPAN.finditer(text)]


def _inside(spans: list[tuple[int, int]], offset: int) -> bool:
    return any(s <= offset < e for s, e in spans)

CONTRAST_PATTERNS: dict[str, re.Pattern[str]] = {
    "CF001": re.compile(
        r"\b(?:not|isn'?t|aren'?t|wasn'?t|weren'?t|won'?t)\s+just\b"
        r"|\bnot\s+only\b[^.!?]{0,80}\bbut\b",
        re.IGNORECASE,
    ),
    "CF002": re.compile(
        r"\bmore\s+than\s+just\b"
        r"|\bmore\s+than\s+(?:a|an|the)\b[^.!?,—]{0,40}[,—]",
        re.IGNORECASE,
    ),
    # `only`/`just` are CF001's shape and `merely` is CF010's. They are
    # excluded here so one clause is not counted twice. `simply` is deliberately not
    # excluded: CF007 reaches only the do-support form ("does not simply V"),
    # so excluding it here would leave ", not simply the label" owned by no
    # rule at all.
    "CF003": re.compile(
        r",\s+not\s+(?!only\b|just\b|merely\b)[^.!?;:]{1,70}(?=[.!?;:]|$)",
        re.IGNORECASE,
    ),
    "CF004": re.compile(r",\s+never\s+[^.!?;:]{1,70}(?=[.!?;:]|$)", re.IGNORECASE),
    "CF005": re.compile(r"\brather\s+than\b", re.IGNORECASE),
    "CF006": re.compile(
        r"(?:^|(?<=[.!?]\s))(?:This|That|It|These|Those)\s+(?:is|are|was|were)\s+not\b",
    ),
    "CF007": re.compile(
        r"\b(?:do|does|did)\s+not\s+(?:just|simply|merely)\b"
        r"|\b(?:don'?t|doesn'?t|didn'?t)\s+(?:just|simply|merely)\b",
        re.IGNORECASE,
    ),
    "CF008": re.compile(
        r"\b(?:it'?s|it\s+is|this\s+is|that\s+is)\s+not\s+[^.!?;]{1,60}"
        r",\s+(?:it'?s|it\s+is|this\s+is|that\s+is)\b",
        re.IGNORECASE,
    ),
    "CF009": re.compile(
        r"\b(?:is|are|was|were)\s+not\s+really\b[^.!?]{0,70}"
        r"[—–-]\s*(?:it|this|that|they)\s+(?:is|are|was|were)\b",
        re.IGNORECASE,
    ),
    "CF010": re.compile(r"\bnot\s+merely\b", re.IGNORECASE),
}

TRIAD_RE = re.compile(
    r"\b([A-Za-z][\w'’-]*(?:\s+[\w'’-]+){0,4}),\s+"
    r"([A-Za-z][\w'’-]*(?:\s+[\w'’-]+){0,4}),\s+"
    r"(?:and|or)\s+([A-Za-z][\w'’-]*(?:\s+[\w'’-]+){0,4})\b"
)


# --------------------------------------------------------------------------
# Records
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    rule_id: str
    file: str
    anchor: dict[str, Any]
    evidence: str
    order: tuple[int, int]  # (segment index, offset): document order, not emitted
    metrics: dict[str, float] | None = None

    def record(self, words: int, sentences: int) -> dict[str, Any]:
        family, version, _desc = RULES[self.rule_id]
        rec: dict[str, Any] = {
            "record": "finding",
            "rule_id": self.rule_id,
            "rule_version": version,
            "family": family,
            "disposition": FAMILY_DISPOSITION[family],
            "counted": FAMILY_COUNTED[family],
            "file": self.file,
            "anchor": self.anchor,
            "evidence": self.evidence,
            "words": words,
            "sentences": sentences,
        }
        if self.metrics is not None:
            rec["metrics"] = self.metrics
        return rec


@dataclass
class Segment:
    """One paragraph of measurable prose, plus everything needed to anchor it.

    ``raw`` and ``clean`` are the same length: cleaning blanks non-prose
    spans in place rather than deleting them, so an offset into ``clean``
    indexes ``raw`` (and the original file) exactly.

    Subclassing is the extension point for structured inputs (a document
    assembled from separate fields rather than lines): override ``anchor_at``
    to emit a custom anchor (include a ``label`` key and the report renders
    it), and override ``group`` so sentences from different fields are not
    treated as neighbours.
    """

    raw: str
    clean: str
    abs_start: int = 0
    line_starts: tuple[int, ...] = ()

    def anchor_at(self, offset: int) -> dict[str, Any]:
        line = bisect.bisect_right(self.line_starts, self.abs_start + offset)
        return {"kind": "line", "line": line}

    @property
    def group(self) -> str:
        """Sentences compare for adjacent repetition only inside one group."""
        return ""

    def _adjacent_run(self, offset: int, direction: int) -> tuple[int, int] | None:
        """The run of non-space raw characters next to ``offset`` on one side.

        Returns ``None`` when that side holds no operand at all (the mark
        sits at a line or segment edge). Newlines terminate the search: an
        operand on the next line is a different clause.
        """
        index = offset + direction
        while 0 <= index < len(self.raw) and self.raw[index] in " \t":
            index += direction
        if not 0 <= index < len(self.raw) or self.raw[index] == "\n":
            return None
        end = index
        while 0 <= end < len(self.raw) and self.raw[end] not in " \t\n":
            end += direction
        return (end + 1, index + 1) if direction < 0 else (index, end)

    def operand_stripped(self, offset: int) -> bool:
        """True when the mark at ``offset`` joins material that stripping removed.

        A punctuation mark is prose glue only if it connects prose.
        When an adjacent operand carried content in ``raw`` but carries none
        in ``clean``, the mark was left orphaned by stripping and is notation
        punctuation, not a connective: the dash between two inline code
        spans, the colon introducing a blanked link. A mark with no operand
        on either side is orphaned by definition.
        """
        sides = [self._adjacent_run(offset, -1), self._adjacent_run(offset, 1)]
        present = [side for side in sides if side is not None]
        if not present:
            return True
        for start, end in present:
            if CONTENT_CHAR.search(self.raw[start:end]) and not CONTENT_CHAR.search(
                self.clean[start:end]
            ):
                return True
        return False

    def quote(
        self, start: int, end: int, focus: tuple[int, int] | None = None
    ) -> str:
        focus_text = self.raw[focus[0] : min(focus[1], end)] if focus else None
        return normalise_quote(self.raw[start:end], focus=focus_text)


@dataclass
class Document:
    path: str
    segments: list[Segment] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    # Original 1-based line numbers that were markdown list items. PG002's
    # "semicolon separating list items" exemption needs them and nothing else
    # does.
    list_lines: set[int] = field(default_factory=set)


def normalise_quote(text: str, limit: int = 160, focus: str | None = None) -> str:
    """Collapse whitespace and cap length.

    ``focus`` is the matched span. A long sentence is windowed around it, so
    the quote always contains the matched text.
    """
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    needle = " ".join(focus.split()) if focus else ""
    if needle:
        if len(needle) >= limit:
            return needle[: limit - 1].rstrip() + "…"
        at = collapsed.find(needle)
        if at >= 0:
            pad = (limit - len(needle)) // 2
            high = min(len(collapsed), max(at + len(needle) + pad, limit))
            low = max(0, high - limit)
            window = collapsed[low:high]
            return ("…" if low else "") + window + ("…" if high < len(collapsed) else "")
    return collapsed[: limit - 1].rstrip() + "…"


# --------------------------------------------------------------------------
# Cleaning: every pass blanks in place, preserving length and newlines
# --------------------------------------------------------------------------


def _blank(chars: list[str], start: int, end: int) -> None:
    for i in range(start, min(end, len(chars))):
        if chars[i] != "\n":
            chars[i] = " "


def strip_emphasis(chars: list[str]) -> None:
    """Blank emphasis markers, keeping the emphasised text."""
    for index, char in enumerate(chars):
        if char == "*":
            chars[index] = " "


_TABLE_DELIMITER = re.compile(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?(?:-{3,})?:?\s*\|?\s*$")


def _table_line_numbers(lines: list[str]) -> set[int]:
    """1-based line numbers belonging to a pipe table, found via its delimiter row.

    GitHub markdown does not require a leading pipe, so ``startswith("|")``
    alone misses the common ``Header | Header`` / ``--- | ---`` form and
    hands its cells to the prose rules, where a cell reading "Honestly this
    matters." scores as performative candour. The delimiter row is the
    unambiguous marker: from it, the header line above and the body lines
    below (while they still contain a pipe) are the table.
    """
    table: set[int] = set()
    for index, line in enumerate(lines):
        if "|" not in line or not _TABLE_DELIMITER.match(line):
            continue
        table.add(index + 1)
        if index > 0 and "|" in lines[index - 1]:
            table.add(index)
        follow = index + 1
        while follow < len(lines) and "|" in lines[follow]:
            table.add(follow + 1)
            follow += 1
    return table


def clean_markdown(text: str) -> tuple[str, set[int]]:
    """Blank markdown non-prose. Returns cleaned text plus the set of list-item lines."""
    chars = list(text)
    lines: list[tuple[int, int, str]] = []
    pos = 0
    for line in text.splitlines(keepends=True):
        lines.append((pos, pos + len(line), line))
        pos += len(line)

    table_lines = _table_line_numbers([line for _s, _e, line in lines])

    list_lines: set[int] = set()
    in_fence = False
    fence_char = ""
    fence_len = 0
    in_front_matter = False
    for number, (start, end, line) in enumerate(lines, start=1):
        stripped = line.strip()
        if number == 1 and stripped == "---":
            in_front_matter = True
            _blank(chars, start, end)
            continue
        if in_front_matter:
            _blank(chars, start, end)
            if stripped == "---":
                in_front_matter = False
            continue
        fence = re.match(r"^\s*(`{3,}|~{3,})", line)
        if in_fence:
            _blank(chars, start, end)
            # CommonMark: a fence closes only on a run of the same character
            # at least as long as the opener, so ``` does not close ````.
            if fence and fence.group(1)[0] == fence_char and len(fence.group(1)) >= fence_len:
                in_fence = False
            continue
        if fence:
            in_fence = True
            fence_char = fence.group(1)[0]
            fence_len = len(fence.group(1))
            _blank(chars, start, end)
            continue
        if stripped.startswith("#"):
            _blank(chars, start, end)
            continue
        if number in table_lines or stripped.startswith("|"):
            _blank(chars, start, end)
            continue
        marker = re.match(r"^(\s*(?:[-*+]|\d+[.)])\s+)", line)
        if marker:
            list_lines.add(number)
            _blank(chars, start, start + marker.end(1))
        quote_marker = re.match(r"^(\s*>+\s*)", line)
        if quote_marker:
            _blank(chars, start, start + quote_marker.end(1))

    text = "".join(chars)
    for match in re.finditer(r"<!--.*?-->", text, re.DOTALL):
        _blank(chars, match.start(), match.end())
    text = "".join(chars)
    # Multi-backtick delimiters are how a code span quotes a backtick, so a
    # single-backtick-only pattern leaks ``like `this` `` into the prose.
    for match in re.finditer(r"(`+)[^\n]*?\1", text):
        _blank(chars, match.start(), match.end())
    text = "".join(chars)
    for match in re.finditer(r"\]\([^)\s]*\)", text):
        _blank(chars, match.start(), match.end())
    strip_emphasis(chars)
    return "".join(chars), list_lines


def clean_plain(text: str) -> str:
    """Bare-text cleaning: emphasis markers only, everything else is prose."""
    chars = list(text)
    strip_emphasis(chars)
    return "".join(chars)


def line_starts_of(text: str) -> tuple[int, ...]:
    starts = [0]
    for index, char in enumerate(text):
        if char == "\n":
            starts.append(index + 1)
    return tuple(starts)


def paragraph_spans(clean: str) -> list[tuple[int, int]]:
    """Split on blank (post-cleaning all-whitespace) lines; drop empty paragraphs."""
    spans: list[tuple[int, int]] = []
    start: int | None = None
    pos = 0
    for line in clean.splitlines(keepends=True):
        if line.strip():
            if start is None:
                start = pos
            end = pos + len(line)
        else:
            if start is not None:
                spans.append((start, end))
                start = None
        pos += len(line)
    if start is not None:
        spans.append((start, len(clean)))
    return [(s, e) for s, e in spans if clean[s:e].strip()]


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------


def _segments_from(raw: str, clean: str) -> list[Segment]:
    starts = line_starts_of(raw)
    return [
        Segment(raw=raw[s:e], clean=clean[s:e], abs_start=s, line_starts=starts)
        for s, e in paragraph_spans(clean)
    ]


def load_markdown(name: str, raw: str) -> Document:
    doc = Document(path=name)
    clean, list_lines = clean_markdown(raw)
    doc.segments = _segments_from(raw, clean)
    doc.list_lines = list_lines
    return doc


def load_text(name: str, raw: str) -> Document:
    doc = Document(path=name)
    doc.segments = _segments_from(raw, clean_plain(raw))
    return doc


def load_document(path: Path) -> Document:
    name = str(path)
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        doc = Document(path=name)
        doc.errors.append(f"unreadable: {exc}")
        return doc
    raw = unicodedata.normalize("NFC", raw)
    if path.suffix.lower() in {".md", ".markdown"}:
        return load_markdown(name, raw)
    return load_text(name, raw)


# --------------------------------------------------------------------------
# Segmentation
# --------------------------------------------------------------------------


def split_sentences(text: str) -> list[tuple[int, int]]:
    """Return (start, end) spans. See the module docstring for failure modes."""
    spans: list[tuple[int, int]] = []
    start = 0
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char in ".!?":
            run_end = index
            while run_end < length and text[run_end] in ".!?…":
                run_end += 1
            terminator = text[index:run_end]
            after = run_end
            while after < length and text[after] in "\")]’”»":
                after += 1
            rest = text[after:]
            tail = rest.lstrip()
            opens_new_sentence = bool(tail) and (tail[0].isupper() or tail[0] in "\"'“«[(-—")
            if char == "." and len(terminator) > 1:
                index = run_end
                continue
            if char == "." and _is_guarded_period(text, index, opens_new_sentence):
                index = run_end
                continue
            if (not rest or rest[0] in " \t\n") and (not tail or opens_new_sentence):
                spans.append((start, after))
                start = after
                while start < length and text[start] in " \t\n":
                    start += 1
                index = start
                continue
            index = run_end
            continue
        index += 1
    if start < length and text[start:].strip():
        spans.append((start, length))
    return [(s, e) for s, e in spans if text[s:e].strip()]


def _is_guarded_period(text: str, index: int, opens_new_sentence: bool) -> bool:
    """True when this period is a decimal point, an initial, or an abbreviation.

    ``opens_new_sentence`` says whether the following token has a
    new-sentence shape. It only matters for ``SENTENCE_FINAL_ABBREVIATIONS``:
    those routinely end a sentence, so an unconditional guard fuses two
    sentences into one and corrupts every count downstream.
    """
    if index + 1 < len(text) and text[index + 1].isdigit() and index and text[index - 1].isdigit():
        return True
    back = index - 1
    while back >= 0 and (text[back].isalnum() or text[back] == "."):
        back -= 1
    token = text[back + 1 : index].lower()
    if not token:
        return False
    # A letter after an apostrophe is a possessive or contraction ending
    # ("the user's."), not an initial.
    if len(token) == 1 and token.isalpha() and (back < 0 or text[back] not in "'’"):
        return True
    if token in SENTENCE_FINAL_ABBREVIATIONS:
        return not opens_new_sentence
    return token in BOUND_ABBREVIATIONS


# --------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------


def _opener_tokens(sentence: str) -> list[str]:
    return [w.lower() for w in WORD.findall(sentence)]


def punctuation_findings(
    doc: Document, seg_index: int, seg: Segment, sentences: list[tuple[int, int]]
) -> list[Finding]:
    out: list[Finding] = []
    for match in EMDASH_RE.finditer(seg.clean):
        if seg.operand_stripped(match.start()):
            continue
        out.append(_make(doc, seg_index, seg, "PG001", match.start(), sentences, match.end()))
    for start, end in sentences:
        sentence = seg.clean[start:end]
        semis = [m.start() + start for m in re.finditer(";", sentence)]
        if len(semis) < 2:
            for offset in semis:
                if seg.operand_stripped(offset):
                    continue
                anchor = seg.anchor_at(offset)
                if anchor.get("line") in doc.list_lines:
                    continue
                out.append(_make(doc, seg_index, seg, "PG002", offset, sentences, offset + 1))
        for match in re.finditer(":", sentence):
            offset = match.start() + start
            rest = seg.clean[offset + 1 :]
            if re.match(r"^[ \t]*(?:\n|$)", rest):
                continue
            # The quoted-example exemption consults the raw text: an opening
            # quote may be an emphasis-adjacent curly quote that stripping
            # left alone, and the stripped-operand test below covers a quoted
            # example that stripping blanked.
            if COLON_EXAMPLE_PREFIX.match(seg.raw[offset + 1 :]):
                continue
            if seg.operand_stripped(offset):
                continue
            # No whitespace on either side is a path reference or clock
            # time ("file:line", "10:30"), which is a column, not glue.
            if offset > 0 and not seg.clean[offset - 1].isspace() and not seg.clean[offset + 1].isspace():
                continue
            # Inline-list exemption: the catalogue lets a colon introduce a
            # list, and "state: trigger, observed behaviour, expected
            # behaviour" is one. Two commas in the remainder of the sentence
            # is the proxy. A clause with one comma still counts.
            if seg.clean[offset + 1 : end].count(",") >= 2:
                continue
            out.append(_make(doc, seg_index, seg, "PG003", offset, sentences, offset + 1))
    return out


def contrast_spans(seg: Segment, sentences: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Every contrast-frame match as a (start, end) span in segment offsets."""
    spans: list[tuple[int, int]] = []
    for start, end in sentences:
        sentence = seg.clean[start:end]
        for pattern in CONTRAST_PATTERNS.values():
            spans.extend((m.start() + start, m.end() + start) for m in pattern.finditer(sentence))
    return spans


def contrast_findings(
    doc: Document, seg_index: int, seg: Segment, sentences: list[tuple[int, int]]
) -> list[Finding]:
    out: list[Finding] = []
    quoted = quoted_spans(seg.clean)
    for start, end in sentences:
        sentence = seg.clean[start:end]
        for rule_id, pattern in CONTRAST_PATTERNS.items():
            for match in pattern.finditer(sentence):
                out.append(
                    _make_or_mention(
                        doc,
                        seg_index,
                        seg,
                        rule_id,
                        match.start() + start,
                        sentences,
                        match.end() + start,
                        quoted,
                    )
                )
    return out


def importance_findings(
    doc: Document, seg_index: int, seg: Segment, sentences: list[tuple[int, int]]
) -> list[Finding]:
    out: list[Finding] = []
    families = (("IT001", INSIGHT_RE), ("IT002", INTENSIFIER_RE), ("IT003", CANDOUR_RE))
    # "does not simply retry" and "is not really latency" are CF007 and
    # CF009 matches whose own words are intensifiers. The contrast rule
    # owns them, so IT002 skips a match inside any contrast span.
    owned = contrast_spans(seg, sentences)
    quoted = quoted_spans(seg.clean)
    for rule_id, pattern in families:
        for match in pattern.finditer(seg.clean):
            if rule_id == "IT002" and any(s <= match.start() < e for s, e in owned):
                continue
            out.append(
                _make_or_mention(
                    doc, seg_index, seg, rule_id, match.start(), sentences, match.end(), quoted
                )
            )
    return out


def lexical_findings(
    doc: Document, seg_index: int, seg: Segment, sentences: list[tuple[int, int]]
) -> list[Finding]:
    if LEXICAL_RE is None:
        return []
    out: list[Finding] = []
    for match in LEXICAL_RE.finditer(seg.clean):
        found = _make(doc, seg_index, seg, "LX001", match.start(), sentences, match.end())
        word = " ".join(match.group(0).lower().split())
        out.append(replace(found, evidence=f"'{word}' — {found.evidence}"))
    return out


def structure_findings(
    doc: Document, seg_index: int, seg: Segment, sentences: list[tuple[int, int]]
) -> list[Finding]:
    """Object agency, copula avoidance and nominalisation."""
    out: list[Finding] = []
    quoted = quoted_spans(seg.clean)
    # An empty listed noun ("an empty screen names") matches AG001 too; the
    # absence rule owns it.
    absence_starts = {m.start() for m in EMPTY_AGENT_RE.finditer(seg.clean)}
    # "provides a clear explanation of" and "through the creation of" match
    # NM003 too; the light-verb and "through" rules own them.
    owned = [
        (m.start(), m.end())
        for pattern in (LIGHT_VERB_RE, THROUGH_NOMINAL_RE)
        for m in pattern.finditer(seg.clean)
    ]
    rules = (
        ("AG001", AGENT_RE),
        ("AG002", ABSENCE_AGENT_RE),
        ("AG002", EMPTY_AGENT_RE),
        ("CA001", COPULA_RE),
        ("NM001", LIGHT_VERB_RE),
        ("NM002", THROUGH_NOMINAL_RE),
        ("NM003", OF_NOMINAL_RE),
        ("NM004", POSSESSIVE_NOMINAL_RE),
    )
    for rule_id, pattern in rules:
        for match in pattern.finditer(seg.clean):
            if not _passes_word_lists(match):
                continue
            if rule_id == "AG001" and match.start() in absence_starts:
                continue
            if rule_id == "NM003" and _inside(owned, match.start()):
                continue
            out.append(
                _make_or_mention(
                    doc, seg_index, seg, rule_id, match.start(), sentences, match.end(), quoted
                )
            )
    return out


def _passes_word_lists(match: re.Match[str]) -> bool:
    """Reject a stoplisted noun, and an "'s" that is a contraction."""
    groups = match.groupdict()
    noun = (groups.get("noun") or "").lower()
    if noun and (_singular(noun) in NOMINAL_STOPLIST or noun in ING_STOPLIST):
        return False
    owner = (groups.get("owner") or "").lower()
    return owner not in CONTRACTION_HOSTS


def possessive_findings(
    doc: Document, seg_index: int, seg: Segment, sentences: list[tuple[int, int]]
) -> list[Finding]:
    """Dangling possessives, and pronouns whose owner is only a possessive."""
    out: list[Finding] = []
    quoted = quoted_spans(seg.clean)

    def make(rule_id: str, offset: int, end: int, note: str = "") -> Finding:
        return _make_or_mention(
            doc, seg_index, seg, rule_id, offset, sentences, end, quoted, note
        )

    for start, end in sentences:
        sentence = seg.clean[start:end]
        spans = [
            (m.start(), m.end())
            for m in PREDICATIVE_POSSESSIVE_RE.finditer(sentence)
            if _passes_word_lists(m)
        ]
        if spans:
            spans += [
                (m.start(), m.end())
                for pattern in (GAPPED_POSSESSIVE_RE, CONTRAST_POSSESSIVE_RE)
                for m in pattern.finditer(sentence, spans[0][1])
                if _passes_word_lists(m)
            ]
            spans.sort()
        for s, e in spans:
            out.append(make("DP001", start + s, start + e))
        if len(spans) >= 2:
            s, e = spans[1]
            out.append(make("DP002", start + s, start + e, f"{len(spans)} in one sentence"))
        antecedent = POSSESSIVE_ANTECEDENT_RE.match(sentence)
        if antecedent and _passes_word_lists(antecedent):
            out.append(make("PR002", start + antecedent.start(), end))
    if sentences:
        start, end = sentences[0]
        opener = PARAGRAPH_PRONOUN_RE.match(seg.clean, start, end)
        if opener:
            out.append(make("PR001", opener.start(), opener.end()))
    return out


def _make_or_mention(
    doc: Document,
    seg_index: int,
    seg: Segment,
    rule_id: str,
    offset: int,
    sentences: list[tuple[int, int]],
    match_end: int,
    quoted: list[tuple[int, int]],
    note: str = "",
) -> Finding:
    """A finding, or an MN001 row naming the rule when the match is quoted.

    A match that starts inside a short quoted span is usually a mention: the
    text talks about the phrase. It is still reported, as an advisory row,
    so a phrase the writer quoted but also asserts stays visible. ``note``
    goes before the quote ("2 in one sentence").
    """
    found = _make(doc, seg_index, seg, rule_id, offset, sentences, match_end)
    if note:
        found = replace(found, evidence=f"{note} — {found.evidence}")
    if not _inside(quoted, offset):
        return found
    return replace(found, rule_id="MN001", evidence=f"{rule_id} — {found.evidence}")


def _counted_mark(seg: Segment, start: int, end: int, pattern: re.Pattern[str]) -> bool:
    """Whether a sentence carries a mark that survives the orphan test."""
    return any(
        not seg.operand_stripped(start + m.start())
        for m in pattern.finditer(seg.clean[start:end])
    )


COLON_RE = re.compile(":")


def repetition_findings(
    doc: Document,
    stream: list[tuple[int, Segment, int, int]],
    seg_sentences: list[list[tuple[int, int]]],
) -> list[Finding]:
    """Adjacent repetition over the whole document's sentence stream.

    Consecutive sentences are consecutive whether or not a paragraph break
    falls between them: the catalogue defect is "the same opener or
    connective twice in a row", and a blank line does not repair it. Scoping
    the comparison to one paragraph would exempt every cross-paragraph pair,
    which is where a drafted text repeats an opener. ``AR004`` alone resets
    at a paragraph boundary: a shared punctuation shape is a rhythm defect
    within a paragraph, and two paragraphs that each happen to contain a
    colon are not the same thing.
    """
    out: list[Finding] = []
    for index in range(1, len(stream)):
        prev_index, prev_seg, prev_start, prev_end = stream[index - 1]
        curr_index, curr_seg, curr_start, curr_end = stream[index]
        if prev_seg.group != curr_seg.group:
            continue
        sentences = seg_sentences[curr_index]
        prev = prev_seg.clean[prev_start:prev_end]
        curr = curr_seg.clean[curr_start:curr_end]
        prev_tokens, curr_tokens = _opener_tokens(prev), _opener_tokens(curr)
        if (
            prev_tokens
            and curr_tokens
            and prev_tokens[0] == curr_tokens[0]
            and prev_tokens[0] not in OPENER_STOPWORDS
            and len(prev_tokens[0]) > 1
        ):
            out.append(_make(doc, curr_index, curr_seg, "AR001", curr_start, sentences))
        if (
            len(prev_tokens) > 1
            and len(curr_tokens) > 1
            and prev_tokens[:2] == curr_tokens[:2]
        ):
            out.append(_make(doc, curr_index, curr_seg, "AR002", curr_start, sentences))
        shared = (set(prev_tokens) & set(curr_tokens)) & CONNECTIVES
        if shared:
            out.append(_make(doc, curr_index, curr_seg, "AR003", curr_start, sentences))
        if prev_index != curr_index:
            continue
        for pattern in (COLON_RE, EMDASH_RE):
            if _counted_mark(prev_seg, prev_start, prev_end, pattern) and _counted_mark(
                curr_seg, curr_start, curr_end, pattern
            ):
                out.append(_make(doc, curr_index, curr_seg, "AR004", curr_start, sentences))
                break
    return out


def triad_findings(
    doc: Document, seg_index: int, seg: Segment, sentences: list[tuple[int, int]]
) -> list[Finding]:
    out: list[Finding] = []
    for match in TRIAD_RE.finditer(seg.clean):
        # The first item's left edge is not recoverable without parsing (the
        # regex swallows the whole clause head), so the phrase-length
        # similarity test compares items 2 and 3 only, whose edges are both
        # literal delimiters. A documented narrowing of "three items of
        # similar length".
        lengths = [len(match.group(n).split()) for n in (2, 3)]
        if max(lengths) - min(lengths) <= 1:
            out.append(
                _make(doc, seg_index, seg, "CT001", match.start(), sentences, match.end())
            )
    return out


def _make(
    doc: Document,
    seg_index: int,
    seg: Segment,
    rule_id: str,
    offset: int,
    sentences: list[tuple[int, int]],
    match_end: int | None = None,
) -> Finding:
    span = next(((s, e) for s, e in sentences if s <= offset < e), None)
    if span is None:
        span = (max(0, offset - 60), min(len(seg.clean), offset + 60))
    focus = (offset, match_end if match_end is not None else offset + 1)
    return Finding(
        rule_id=rule_id,
        file=doc.path,
        anchor=seg.anchor_at(offset),
        evidence=seg.quote(span[0], span[1], focus),
        order=(seg_index, offset),
    )


def negation_findings(doc: Document, words: int) -> list[Finding]:
    """Per-file negation densities. Report-only; single occurrences are not listed."""
    if not words:
        return []
    counts = {
        "NG001": ("not", sum(len(NOT_RE.findall(seg.clean)) for seg in doc.segments)),
        "NG002": ("never", sum(len(NEVER_RE.findall(seg.clean)) for seg in doc.segments)),
    }
    out: list[Finding] = []
    for position, (rule_id, (label, count)) in enumerate(counts.items()):
        density = round(100.0 * count / words, 4) if words else 0.0
        out.append(
            Finding(
                rule_id=rule_id,
                file=doc.path,
                anchor={"kind": "file"},
                evidence=f"{count} '{label}' over {words} words (density={density:.2f}/100w)",
                order=(10**6 - 1, position),
                metrics={"count": count, "per_100_words": density},
            )
        )
    return out


def _singular(word: str) -> str:
    return word[:-1] if word.endswith("s") and not word.endswith("ss") else word


def nominal_density_findings(doc: Document, words: int) -> list[Finding]:
    """Per-file nominalisation density. Report-only, compared input to output."""
    if not words:
        return []
    count = sum(
        1
        for seg in doc.segments
        for match in NOMINAL_RE.finditer(seg.clean)
        if _singular(match.group(0).lower()) not in NOMINAL_STOPLIST
    )
    density = round(100.0 * count / words, 4)
    return [
        Finding(
            rule_id="ND001",
            file=doc.path,
            anchor={"kind": "file"},
            evidence=f"{count} nominalisations over {words} words (density={density:.2f}/100w)",
            order=(10**6 - 1, 2),
            metrics={"count": count, "per_100_words": density},
        )
    ]


def uniformity_findings(doc: Document, lengths: list[int], openers: list[str]) -> list[Finding]:
    """Report-only, and only above the suppression threshold."""
    if len(lengths) < UNIFORMITY_MIN_SENTENCES:
        return []
    count = len(lengths)
    mean = sum(lengths) / count
    variance = sum((n - mean) ** 2 for n in lengths) / count
    stddev = variance**0.5
    cv = stddev / mean if mean else 0.0
    anchor = {"kind": "file"}
    unique = len(set(openers))
    diversity = unique / len(openers) if openers else 0.0
    return [
        Finding(
            rule_id="UM001",
            file=doc.path,
            anchor=anchor,
            evidence=(
                f"sentence length mean={mean:.2f} stddev={stddev:.2f} cv={cv:.3f} "
                f"over {count} sentences"
            ),
            order=(10**6, 0),
            metrics={
                "mean": round(mean, 4),
                "stddev": round(stddev, 4),
                "coefficient_of_variation": round(cv, 4),
            },
        ),
        Finding(
            rule_id="UM002",
            file=doc.path,
            anchor=anchor,
            evidence=(
                f"{unique} distinct non-stopword openers over {len(openers)} sentences "
                f"(diversity={diversity:.3f})"
            ),
            order=(10**6, 1),
            metrics={
                "distinct_openers": unique,
                "opener_sentences": len(openers),
                "diversity": round(diversity, 4),
            },
        ),
    ]


# --------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------


def analyse(doc: Document) -> tuple[list[Finding], int, int]:
    findings: list[Finding] = []
    words = 0
    lengths: list[int] = []
    openers: list[str] = []
    # (segment index, segment, sentence start, sentence end) in document
    # order. Adjacent repetition reads this stream, so it sees pairs that
    # straddle a paragraph break instead of restarting at every blank line.
    stream: list[tuple[int, Segment, int, int]] = []
    seg_sentences: list[list[tuple[int, int]]] = []
    for seg_index, seg in enumerate(doc.segments):
        sentences = split_sentences(seg.clean)
        seg_sentences.append(sentences)
        for start, end in sentences:
            tokens = _opener_tokens(seg.clean[start:end])
            words += len(tokens)
            lengths.append(len(tokens))
            non_stop = [t for t in tokens if t not in OPENER_STOPWORDS]
            if non_stop:
                openers.append(non_stop[0])
            stream.append((seg_index, seg, start, end))
        findings.extend(punctuation_findings(doc, seg_index, seg, sentences))
        findings.extend(contrast_findings(doc, seg_index, seg, sentences))
        findings.extend(importance_findings(doc, seg_index, seg, sentences))
        findings.extend(lexical_findings(doc, seg_index, seg, sentences))
        findings.extend(structure_findings(doc, seg_index, seg, sentences))
        findings.extend(possessive_findings(doc, seg_index, seg, sentences))
        findings.extend(triad_findings(doc, seg_index, seg, sentences))
    findings.extend(repetition_findings(doc, stream, seg_sentences))
    findings.extend(negation_findings(doc, words))
    findings.extend(nominal_density_findings(doc, words))
    findings.extend(uniformity_findings(doc, lengths, openers))
    findings.sort(key=lambda f: (f.order[0], f.order[1], f.rule_id))
    return findings, words, len(lengths)


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------


def build_records(doc: Document, findings: list[Finding], words: int, sentences: int) -> list[dict]:
    records: list[dict[str, Any]] = [f.record(words, sentences) for f in findings]
    for family, counted in FAMILY_COUNTED.items():
        count = sum(1 for f in findings if RULES[f.rule_id][0] == family)
        records.append(
            {
                "record": "summary",
                "file": doc.path,
                "family": family,
                "disposition": FAMILY_DISPOSITION[family],
                "counted": counted,
                "findings": count,
                "words": words,
                "sentences": sentences,
                "per_100_words": round(100.0 * count / words, 4) if words else 0.0,
            }
        )
    counted_total = sum(1 for f in findings if FAMILY_COUNTED[RULES[f.rule_id][0]])
    records.append(
        {
            "record": "file_total",
            "file": doc.path,
            "tool_version": TOOL_VERSION,
            "counted_findings": counted_total,
            "uncounted_findings": len(findings) - counted_total,
            "words": words,
            "sentences": sentences,
            "per_100_words": round(100.0 * counted_total / words, 4) if words else 0.0,
        }
    )
    return records


def _where(anchor: dict[str, Any]) -> str:
    if "label" in anchor:
        return str(anchor["label"])
    if anchor["kind"] == "line":
        return f"line {anchor['line']}"
    return "file"


def render_report(records: list[dict[str, Any]], details: bool = False) -> str:
    """Render the per-family summary, plus per-instance rows with --details.

    The summary table is what a reader acts on: the counts per family, each
    labelled with its disposition. The per-row battery is a drill-down, so
    it lives behind ``--details``.
    """
    lines: list[str] = []
    by_file: dict[str, list[dict[str, Any]]] = {}
    for rec in records:
        by_file.setdefault(rec["file"], []).append(rec)
    for path, recs in by_file.items():
        lines.append(f"== {path}")
        errors = [r for r in recs if r["record"] == "error"]
        if errors:
            for err in errors:
                lines.append(f"   ERROR  {err['message']}")
            lines.append("")
            continue
        lines.append(
            f"   {'family':<20} {'disposition':<13} {'findings':>8} {'per 100w':>9}"
        )
        for rec in (r for r in recs if r["record"] == "summary"):
            lines.append(
                f"   {rec['family']:<20} {rec['disposition']:<13} "
                f"{rec['findings']:>8} {rec['per_100_words']:>9.2f}"
            )
        for rec in (r for r in recs if r["record"] == "file_total"):
            lines.append(
                f"   == TOTAL counted {rec['counted_findings']} "
                f"({rec['per_100_words']:.2f}/100 words) over {rec['words']} words, "
                f"{rec['sentences']} sentences; "
                f"{rec['uncounted_findings']} advisory/report-only"
            )
        findings = [r for r in recs if r["record"] == "finding"]
        if details and findings:
            for family, disposition in FAMILY_DISPOSITION.items():
                rows = [r for r in findings if r["family"] == family]
                if not rows:
                    continue
                lines.append(f"   -- {family} [{disposition}]")
                for rec in rows:
                    desc = RULES[rec["rule_id"]][2]
                    lines.append(
                        f"      {rec['rule_id']} {_where(rec['anchor'])}: {desc}"
                    )
                    lines.append(f"          {rec['evidence']}")
        elif findings:
            lines.append(f"   ({len(findings)} findings — re-run with --details to list them)")
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def collect_paths(raw_paths: list[str]) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    missing: list[str] = []
    for raw in raw_paths:
        path = Path(raw)
        if path.is_dir():
            files.extend(
                sorted(
                    p
                    for p in path.rglob("*")
                    if p.is_file() and p.suffix.lower() in SCANNED_SUFFIXES
                )
            )
        elif path.is_file():
            files.append(path)
        else:
            missing.append(raw)
    return files, missing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lint_prose_tells.py",
        description="Report mechanically detectable prose tells. Makes no edits.",
    )
    parser.add_argument("paths", nargs="+", help="files or directories to scan")
    parser.add_argument(
        "--details",
        action="store_true",
        help="list per-instance rows under the summary, grouped and labelled by disposition",
    )
    parser.add_argument("--json", action="store_true", help="emit the JSONL finding record")
    args = parser.parse_args(argv)

    files, missing = collect_paths(args.paths)
    records: list[dict[str, Any]] = []
    for raw in missing:
        records.append({"record": "error", "file": raw, "message": f"no such path: {raw}"})
    if not files and not missing:
        print("lint_prose_tells: no scannable files in the given paths", file=sys.stderr)
        return 2

    had_error = bool(missing)
    for path in files:
        doc = load_document(path)
        if doc.errors:
            had_error = True
            for message in doc.errors:
                records.append({"record": "error", "file": doc.path, "message": message})
            continue
        findings, words, sentences = analyse(doc)
        records.extend(build_records(doc, findings, words, sentences))

    if args.json:
        for rec in records:
            print(json.dumps(rec, ensure_ascii=True, sort_keys=False))
    else:
        print(render_report(records, details=args.details))

    return 2 if had_error else 0


if __name__ == "__main__":
    sys.exit(main())
