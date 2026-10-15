<!-- Human-written prose taken from this repository's README and from the
maintainer's own agent definitions and skills. Each paragraph produced no
counted finding when its source file was scanned. The test expects none. -->

The output is a report. Judging the findings and rewriting the text are left to the reader and the skill procedure.

A skill is installed by putting its folder where your agent looks for skills. Clone this repo, then copy or symlink the skill folders you want.

A symlink keeps the skill on this repo's latest commit. A copy pins it, and Copilot's cloud agent needs the copy committed to the target repo.

You work across projects. You discover the project's context by reading what's in front of you. You do not perform live testing, do not run exploit code, and do not assume the project has authorised offensive testing.

Your reader is a busy decision-maker who did not watch your process and holds no shorthand from it.

Drive these steps in order. Do not skip any. The whole safety model is "user reviews the diff", which only works if every step holds.

Confirm with the user which file is being tightened. If they pointed at it directly, confirm the path. If they were vague, surface the candidate path as a yes/no.

If the user has explicitly forbidden auto-commits, stop here and ask them to commit manually before continuing.

The editor will run its own pre-flight check, perform the cuts, and return a cut log.

The tool returns only Fable's text (thinking blocks are omitted).
