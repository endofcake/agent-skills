# agent-skills

Portable skills for coding agents, in the [Agent Skills](https://agentskills.io/specification) format. Each skill is a folder with a `SKILL.md` and any scripts it needs. The same folder works in Claude Code, GitHub Copilot (VS Code, CLI, cloud agent), and any other harness that reads the spec.

## Skills

### [desloppify](desloppify/SKILL.md)

Removes LLM register defects from a finished draft while leaving the facts, terminology, and structure unchanged. The catalogue covers contrast-pattern phrasing ("it's not X, it's Y"), punctuation glue, importance theater ("crucially", "the key insight"), cadence filler, objects that act ("the table teaches"), and actions hidden in nouns ("make a decision").

The skill runs a deterministic detector, [`lint_prose_tells.py`](desloppify/scripts/lint_prose_tells.py) (Python 3.10+, standard library), as a backstop on its own edits. The script also works standalone:

```bash
python3 desloppify/scripts/lint_prose_tells.py --details draft.md
```

The output is a report. Judging the findings and rewriting the text are left to the reader and the skill procedure.

## Installing

A skill is installed by putting its folder where your agent looks for skills. Clone this repo, then copy or symlink the skill folders you want.

### Claude Code

Personal (all projects) or per-project:

```bash
ln -s "$(pwd)/desloppify" ~/.claude/skills/desloppify
```

```bash
ln -s "$(pwd)/desloppify" /path/to/project/.claude/skills/desloppify
```

### GitHub Copilot

Per-repository, in `.github/skills/`:

```bash
cp -R desloppify /path/to/project/.github/skills/desloppify
```

VS Code also reads `.claude/skills/` and `.agents/skills/`, and supports personal skill locations. See the [VS Code Agent Skills docs](https://code.visualstudio.com/docs/agent-customization/agent-skills).

A symlink keeps the skill on this repo's latest commit. A copy pins it, and Copilot's cloud agent needs the copy committed to the target repo.

## Development

A skill's folder holds only what an install needs. Each skill's regression tests live in `tests/<skill>/` and its model-judged evals in `evals/<skill>/`, so copying or symlinking the skill leaves them behind. From the repository root:

```bash
python3 -m unittest discover -s tests/desloppify
```

[`evals/desloppify/README.md`](evals/desloppify/README.md) explains how the evals run and records their results.
