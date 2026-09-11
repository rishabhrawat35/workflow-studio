---
description: state a request; it is sorted and, for logic, discussed and drafted as a node
enters: define.intake
speckit_equivalent: speckit.specify
entry: true
---
# /speckit.specify

You are the AI role of the product-development framework in this repository.
Read `AGENTS.md`, then `framework/README.md` if you have not this session.

1. Run `python3 framework/tools/orchestrate.py check`. If it is not CLOSED, stop and report.
2. This is an entry command: `python3 framework/tools/orchestrate.py start changes/<YYYY-MM-DD>-<n>-<slug>.md --command speckit.specify`, with the PM's words (`$ARGUMENTS`) written under `## Request`.
3. `python3 framework/tools/orchestrate.py next <record>` prints the step, your role and mode, the inputs you may read, the framing if you are the challenger, and the numbered legal exits. Do exactly that step; write its output into the record. A challenger writes `## Findings — <step>` (a line "none" if nothing was found).
4. Move with `python3 framework/tools/orchestrate.py advance <record> --to <exit number> --when <condition number>`; at a PM step add `--answer "<the PM's words>"`. The tool refuses anything else; never pick a step yourself.
5. Repeat 3–4 until `next` shows mode `pm`. Then stop and show the PM what they are asked, with the options as the YAML lists them.
6. Two requests stop once more after the discussion. A large request (several capabilities, several user roles, or a whole product) goes `discuss → breakdown` and stops at `define.confirm-breakdown`: show the PM the proposed chunks, their dependencies, the order with its reasons and the alternatives, as the `## Breakdown — proposed` block stands; the PM answers "yes" (one child record per chunk is created and the request continues as a group, `run.py --group <parent>`), or says in words which chunks to merge, split, reorder or drop (at most three rewrites), or "one thing" (a single node after all), or stop. A removal or breaking change goes `discuss → impact` and stops at `define.confirm-impact`: show what is removed, every dependant with its source, what stops working, the options with one recommendation, and the stored data, as the `## Impact — proposed` block stands; the PM answers one line per dependant (retire it too, keep it by a replacement, narrow the removal, postpone) and one per store of data (keep, migrate, delete), or asks for a revision (at most three), or stop. A removal nobody depends on has no impact stop. Never answer either gate yourself.

Never write code before `deliver.approve-plan` is answered "execute". Never save a node before `define.approve`. Never mark done before `deliver.accept`. In doubt, take the exit with more review and write why into the record.
