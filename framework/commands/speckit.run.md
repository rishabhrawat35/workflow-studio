---
description: run this record to the next PM stop; the runner starts every AI step in a fresh harness process and stops only at a PM step
enters: current
meta: true
speckit_equivalent: none
entry: false
---
# /speckit.run

You are the AI role of the product-development framework in this repository. This command does not run a step itself: it starts the runner, which spawns one fresh harness process per AI step and stops at the next PM step.

1. Run `python3 framework/tools/orchestrate.py check`. If it is not CLOSED, stop and report.
2. Run `python3 framework/tools/run.py $ARGUMENTS` (the record path; `--harness claude|codex|fake`, `--dry-run`, `--max-steps`, `--log-dir` are optional). If no record is given, take the record in flight from `changes/QUEUE.md`.
3. Read the exit code. `0`: the record is closed; report the one-line summary. `3`: a PM step; show the PM the question the runner printed, with the options as the YAML lists them, and the `advance --answer` command the runner spelled out. `4`: a step did not move after a retry; show the reason and the log file the runner named, and stop.
4. Never call `advance` yourself here, never edit the record, never commit. After the PM answers (`python3 framework/tools/orchestrate.py advance <record> --to <exit> [--when <n>] --answer "<the PM's words>"`), run this command again.

Logs: `changes/runs/<record-stem>/<n>-<step>.log` per step and `run.md` for the run.
