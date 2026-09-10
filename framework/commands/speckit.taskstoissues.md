---
description: mirror the record's task list as GitHub issues, one per task, the number written back onto the task line; allowed at deliver.execute or later; moves nothing
enters: deliver.execute
speckit_equivalent: speckit.taskstoissues
entry: false
---
# /speckit.taskstoissues

You are the AI role of the product-development framework in this repository.
Read `AGENTS.md`, then `framework/README.md` if you have not this session.

1. Run `python3 framework/tools/orchestrate.py check`. If it is not CLOSED, stop and report.
2. This is not an entry command and it moves nothing: it mirrors the task list of the record in flight (see `changes/QUEUE.md`) as GitHub issues. The record must be at `deliver.execute` or a later Deliver step (the plan is approved); the tool refuses anything earlier.
3. Run `python3 framework/tools/tasks_to_issues.py <record> --dry-run` and show the PM what would be created (one issue per `- [ ] T001 [P] [node-id] …` line, label `workflow-studio`; tasks already carrying ` → #…` are skipped). `$ARGUMENTS`, if given, is `--repo owner/name` or the PM's note.
4. If the PM confirms, run it without `--dry-run`. The issue numbers are written back onto the task lines; commit the record as any record change.
5. Then continue with `python3 framework/tools/orchestrate.py next <record>`: the record stays where it was; the issues are a mirror, nothing is imported back, and no task is done because an issue was closed.

Never write code before `deliver.approve-plan` is answered "execute". Never save a node before `define.approve`. Never mark done before `deliver.accept`. In doubt, take the exit with more review and write why into the record.
