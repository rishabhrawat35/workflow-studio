---
description: run this record to the next PM stop; the runner starts every AI step in a fresh harness process and stops only at a PM step; `--group <parent>` runs a broken-down request chunk by chunk
enters: current
meta: true
speckit_equivalent: none
entry: false
---
# /speckit.run

You are the AI role of the product-development framework in this repository. This command does not run a step itself: it starts the runner, which spawns one fresh harness process per AI step and stops at the next PM step.

1. Run `python3 framework/tools/orchestrate.py check`. If it is not CLOSED, stop and report.
2. Run `python3 framework/tools/run.py $ARGUMENTS` (the record path; `--harness claude|codex|fake`, `--dry-run`, `--max-steps`, `--log-dir` are optional). If no record is given, take the record in flight from `changes/QUEUE.md`. For a broken-down request (a parent at `define.broken-down`, or a child record carrying `parent:`), run `python3 framework/tools/run.py --group <parent>`: it runs the parent while it is open, then the children in the confirmed order, and after a child reaches `deliver.done` (or is dropped) it releases the next unblocked child itself and continues to that child's discussion. Without `--group`, a child's run stops when that child closes.
3. Read the exit code. `0`: the record is closed (with `--group`: the group is closed, or nothing can be released); report the one-line summary and, for a group, the "n of m delivered" line. `3`: a PM step; show the PM the question the runner printed, with the options as the YAML lists them, and the `advance --answer` command the runner spelled out — at `define.confirm-breakdown` and `define.confirm-impact` that is the whole proposed block the record carries, read to the PM as it stands; or a waiting child: show the wait sentence (which chunk it waits for, and that `--group` releases it once that chunk is delivered). `4`: a step did not move after a retry, or `--group` named a record that is not a parent with children; show the reason and the log file the runner named, and stop.
4. Never call `advance` yourself here, never edit the record, never commit; never answer `define.confirm-breakdown` or `define.confirm-impact` for the PM. After the PM answers (`python3 framework/tools/orchestrate.py advance <record> --to <exit> [--when <n>] --answer "<the PM's words>"`), run this command again.

Logs: `changes/runs/<record-stem>/<n>-<step>.log` per step and `run.md` for the run; with `--group`, one folder per record run.
