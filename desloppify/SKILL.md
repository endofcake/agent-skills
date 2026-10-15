---
name: desloppify
description: Remove LLM register defects (contrast-pattern phrasing, punctuation glue, importance theater, filler) from a finished draft, leaving the text otherwise unchanged. Use on any LLM-drafted prose before a human reader sees it.
license: MIT
metadata:
  author: endofcake
  source: https://github.com/endofcake/agent-skills
  version: "1.0"
---

# Desloppify

An edit pass over one finished text. Input: a file path, or quoted text. Output: the same text with instances of the patterns below rewritten, plus a change table. Nothing else changes. No new facts, no restructuring, same terminology, same examples, same order. The only cuts are restatements and framing that carries no fact.

## The catalogue

### Contrast abuse

- **Compressed antithesis** — "X, not Y" as the default sentence shape. *The boundary is situational, not fixed per pair* becomes *The boundary shifts with the situation.*
- **Contrastive escalation** — the second half one-ups the first: "not just X — Y", "more than X, this is Y". State Y.
- **Negative definition** — a thing described by what it is not. Say what it is.

A contrast may stay when it corrects a wrong assumption the intended reader actually brings. Name that assumption in the change table when you exempt one.

### Importance theater

- **Performative insight** — significance announced instead of shown: "the key insight is", "crucially", "what this really means". Delete the announcement, keep the fact.
- **Dramatized stakes** — hazard vocabulary on ordinary facts: "silently breaks", "the trap", "dangerous". State the consequence.
- **Sloganeering** — aphorism-shaped sentences built to be quoted, including balanced maxim pairs. State the fact once, plainly.

### Rhythm and filler

- **Punctuation glue** — em-dashes, semicolons, and colons used as all-purpose connectives. A semicolon fusing two complete sentences serves rhythm alone. Split them. Swapping one connective for another is the same defect, so watch for colons appearing where dashes were removed. A dash survives around a true parenthetical, and a colon before a list or an example.
- **Adjacent repetition** — the same connective, opener, or punctuation shape in consecutive sentences ("also… also", a colon in each of two neighbouring sentences). Drop or vary one.
- **Cadence triads** — three parallel items chosen for rhythm. Keep the items that carry facts.
- **Echo restatement** — the point repeated in other words: "in other words", a closing sentence summarising its own paragraph. Delete the echo. A deleted restatement loses no fact.
- **Insistence intensifiers and absolutes** — "genuinely", "actually", "really", "simply", "exactly" pressing a claim; performed sincerity ("honestly", "frankly", "to be clear"); "always" and "never" on a fact that has exceptions. Delete the intensifier. Scope the absolute.

### Lexical tells

- **Fashion vocabulary** — the detector keeps a small advisory list in `scripts/lexical_tells.txt`. Judge each hit in context and preserve domain terminology. Keep generation-specific examples in that data file; retire stale entries instead of accumulating word bans here.

### Stance

- **Meta-narration** — the text describing itself or its reader: "it is worth noting", "let's unpack this", "you might wonder". Delete it, or state the fact directly.
- **Agency in abstractions** — inanimate things performing intentional acts: "the rule wants", "the document resists". Name who does what, or use a literal verb.

### Contextual patterns

The detector has no proxy for these, so step 2 gives them a separate read. Quote the candidate and explain what its wording contributes before deciding to edit. If the decision needs unavailable reader context, preserve the passage and note the uncertainty.

- **Ritual validation** — generic praise or agreement cushioning a correction. Delete it when it contributes no premise or useful acknowledgment. *Your reasoning is sound, but the estimate omits storage costs* becomes *The estimate omits storage costs.* Keep specific agreement that the argument uses: *Your estimate includes storage, so we can compare total costs.* An endorsement that would read the same before the opposite recommendation carries nothing, so delete it.
- **Repeated choreography** — consecutive paragraphs share one move sequence (an endorsement, then a reveal, then a prescription) whatever their subject. This is adjacent repetition at paragraph scale. Fix the moves under their own entries: ritual validation and performative insight. Keep the facts and their order. Parallel structure stays when it answers parallel questions or supports a comparison. Do not reword only to hide the pattern.

## Preserve meaning and connections

Keep measurements, uncertainty, causal links, and deliberate voice. When splitting a sentence, retain the relationship between its facts with words such as "because" or "so" where needed. Avoid turning connected reasoning into a run of isolated statements.

A plainer rewrite must not invent an actor, mechanism, measurement, or qualification. If a slogan cannot be made plain from the supplied context, preserve it and record it in the change table as a contextual candidate kept.

## Procedure

1. Read the whole text first.
2. Mark catalogue instances, including a separate read for contextual patterns the detector cannot establish.
3. Rewrite each one minimally: the same fact, the same terms, plain syntax. Exempt a contrast only under the rule above, and record the exemption.
4. Check the rewrites against the catalogue and the preservation rules. Read the changed passages together for lost connections or newly repetitive rhythm. The pass must not introduce what it removes.
5. Run the deterministic backstop, bundled with this skill, on the edited file:

   ```bash
   python3 scripts/lint_prose_tells.py --details <the edited file>
   ```

   The path is relative to this skill's directory. Script needs Python 3.10+.

   Contrast-frame and importance-theater findings are catalogue instances. Rewrite or exempt each under the rules above. The punctuation-glue density must not be higher than the input text's (run the script on both). A rise means the pass introduced what it removes. Adjacent-repetition and lexical-tell findings are advisory. Act on one where you agree with it. Negation density is a report-only measure of "not" and "never": rewriting contrast frames positively lowers it, so compare the input and output numbers alongside the punctuation-glue check.

6. Deliver the edited text as a file, with a change table: one row per edit, before and after, with the pattern and reason. List contrast exemptions with the reader assumption each one corrects; record contextual candidates preserved because the wording serves the reader or context is missing.
