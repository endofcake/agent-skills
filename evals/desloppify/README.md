# Desloppify evals

Model-judged cases for the behaviours the detector cannot see. `evals.json`
follows the skill-creator plugin's layout, so its runner, grader and
aggregator apply, except that input paths are relative to this folder
rather than to the skill. Inputs live in `files/`. `check.py` grades every
string-level expectation and the detector density comparison mechanically
and marks the rest for judgment:

```bash
python3 evals/desloppify/check.py <eval id> <outputs dir>
```

The outputs directory holds `output.md`, the edited text, and `changes.md`,
the change table.

## Results

### Iteration 5: skill 1.2

Iteration 5 ran on 2026-10-29 on Claude Sonnet 5.5, passed explicitly to
each run, against the skill at commit 7c2958a. The skill ran every case three
times. Case 10 also ran three times with no skill, where the run gets the
skill's one-line description as its only instruction. The table counts runs
that passed every expectation.

| Case | Skill 1.2 | No skill |
|------|-----------|----------|
| choreographed-review | 3 of 3 | not run |
| glued-causal | 3 of 3 | not run |
| legitimate-contrast | 3 of 3 | not run |
| slogan-without-context | 3 of 3 | not run |
| mention-versus-use | 3 of 3 | not run |
| specific-agreement-only | 3 of 3 | not run |
| derivable-slogan | 2 of 3 | not run |
| object-agency | 3 of 3 | not run |
| hidden-actions | 2 of 3 | not run |
| dangling-possessives | 2 of 3 | 1 of 3 |

Counted by expectation, skill 1.2 passed 122 of 126. On case 10 alone, the
skill passed 25 of 27 and no skill 25 of 27.

- On dangling-possessives, every skill run rewrote the three dropped-noun
  possessives with the owner as subject ("The maintainer decides whether to
  ship, and the user bears the risk", "Sam owns the release laptop") and
  added no actor. The failing run kept "Its cache holds the last ten grades"
  because the grader is the subject of the paragraph above. It also kept
  "the pipeline's handling of retries" under the rule that a noun stays when
  the only subject is not a person. Commit 8036212 narrowed both rules after
  the run. The case has not been rerun since.
- Every skill run dropped "not the adapter's" from "The judgment on stress
  marks is the extractor's, not the adapter's", as compressed antithesis.
  Two no-skill runs kept "not the adapter". No expectation checks whether
  the adapter's exclusion survives, and the catalogue does not say whether
  it is a fact or a restatement.
- Without the skill, Sonnet also rewrote every dangling possessive. One run
  wrote "The release laptop belongs to Sam", which keeps the laptop as
  subject, and another kept "Its".
- Against iteration 3, derivable-slogan fell from 3 of 3 to 2 of 3. One run
  rewrote "profiling later showed" and "what the profile shows" as objects
  that act. The other two kept them as the field's literal verbs.
  Hidden-actions stayed at 2 of 3, and again one run left "respected through
  clarity". Object-agency passed in every run, on *is* or *has*.
- A run used 64,000 tokens and 18 seconds on average with the skill, and
  59,000 and 15 with no skill. The round used 2.1 million tokens.

### Iteration 3: skill 1.1

Iteration 3 ran on 2026-10-15 on Claude Sonnet 5.5, passed explicitly to
each run. It compares three configurations:

- **Current skill**: the skill as committed.
- **Snapshot**: the skill as first published, commit 5c6bfe6, before the contextual-patterns
  and preservation rules and the catalogue entries for objects that act and
  nominalisation.
- **No skill**: the run gets the skill's one-line description as its only
  instruction.

Each case ran three times per configuration. Glued-causal ran six times for
the two skill versions. Runs and benchmark files are not committed. The
table counts runs that passed every expectation.

| Case | Current skill | Snapshot | No skill |
|------|---------------|----------|----------|
| choreographed-review | 3 of 3 | 0 of 3 | 3 of 3 |
| glued-causal | 6 of 6 | 6 of 6 | 0 of 3 |
| legitimate-contrast | 3 of 3 | 3 of 3 | 3 of 3 |
| slogan-without-context | 3 of 3 | 0 of 3 | 1 of 3 |
| mention-versus-use | 3 of 3 | 3 of 3 | 3 of 3 |
| specific-agreement-only | 3 of 3 | 3 of 3 | 3 of 3 |
| derivable-slogan | 3 of 3 | 3 of 3 | 2 of 3 |
| object-agency | 0 of 3 | 0 of 3 | 0 of 3 |
| hidden-actions | 2 of 3 | 0 of 3 | 0 of 3 |

Counted by expectation, the current skill passed 107 of 111, the snapshot
83 of 111, and no skill 84 of 99.

- The contextual-patterns rule separates the two skill versions on
  choreographed-review and slogan-without-context. The snapshot kept both
  empty endorsements and rewrote the slogan in every run. Without any skill,
  Sonnet deleted the endorsements but deleted the slogan in two of three
  runs.
- On glued-causal, both skill versions kept the causal link in all six
  runs, and Sonnet without the skill lost it in all three. The snapshot's
  four failures on Fable 5.1 did not recur on Sonnet, so the link survives
  because of rules both versions share.
- On hidden-actions, the current skill turned "make a decision" into
  "decide" in every run and kept "Praise and reassurance" as a label. One
  run left "respected through clarity". The snapshot made no edits. Without
  the skill, Sonnet rewrote the labels too, and two runs gave an object a
  new action ("Feedback respects the learner").
- No configuration passed object-agency. Two current-skill runs wrote "the
  content to come is named by the absence", a passive in which the absence
  still names. The third invented a label the input does not mention. The
  catalogue entry said to use a passive but not that the object must leave
  the sentence. After the entry was changed to say so, three more
  current-skill runs of the case passed every expectation. Each rewrote the
  sentence on *is* ("the absence is the name of the content to come").
- A run used 60,000 tokens and 17 seconds on average with the current
  skill, 59,000 and 16 with the snapshot, and 55,000 and 10 with no skill.

Two earlier iterations on 2026-09-21 ran cases 1 to 7 on Claude Fable 5.1,
because the runs inherited the session model. They are superseded.

## Known gaps

- Case 10 has not been rerun since commit 8036212 changed the two rules its
  failing run relied on.
- The passing object-agency rewrites keep the figure: "the absence is the
  name of the content to come" still calls an absence a name. No
  expectation checks whether a rewrite stays figurative, and no run
  recorded the figure as a contextual candidate kept.
- One reader graded the expectations that need judgment. A second grader
  would test those verdicts.
- Three runs per configuration cannot separate a one-run difference from
  noise.
