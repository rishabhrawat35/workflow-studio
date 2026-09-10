---
description: verify against the criteria and route through passes
enters: deliver.verify
speckit_equivalent: speckit.converge
entry: false
---
# /speckit.converge

You are the AI role of the product-development framework in this repository.
Read `AGENTS.md`, then `framework/README.md` if you have not this session.

1. Run `python3 framework/tools/orchestrate.py check`. If it is not CLOSED, stop and report.
2. This is not an entry command: it continues the record in flight (see `changes/QUEUE.md`) that is already at `deliver.verify`. Run `python3 framework/tools/orchestrate.py start <record> --command speckit.converge`; it refuses any record not at that step. `$ARGUMENTS`, if given, is the PM's note for this step.
3. `python3 framework/tools/orchestrate.py next <record>` prints the step, your role and mode, the inputs you may read, the framing if you are the challenger, and the numbered legal exits. Do exactly that step; write its output into the record. A challenger writes `## Findings — <step>` (a line "none" if nothing was found).
4. Move with `python3 framework/tools/orchestrate.py advance <record> --to <exit number> --when <condition number>`; at a PM step add `--answer "<the PM's words>"`. The tool refuses anything else; never pick a step yourself.
5. Repeat 3–4 until `next` shows mode `pm`. Then stop and show the PM what they are asked, with the options as the YAML lists them.

Never write code before `deliver.approve-plan` is answered "execute". Never save a node before `define.approve`. Never mark done before `deliver.accept`. In doubt, take the exit with more review and write why into the record.
