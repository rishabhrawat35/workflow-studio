---
description: the one code commit of deliver.commit; refuses any record not at deliver.commit, so nothing is committed before the PM accepts
enters: deliver.commit
speckit_equivalent: speckit.git.commit
entry: false
---
# /speckit.git.commit

You are the AI role of the product-development framework in this repository.
Read `AGENTS.md`, then `framework/README.md` if you have not this session.

1. Run `python3 framework/tools/orchestrate.py check`. If it is not CLOSED, stop and report.
2. This is not an entry command: it performs `deliver.commit` for the record in flight (see `changes/QUEUE.md`), which must be at `deliver.commit` (the PM answered "accepted" at `deliver.accept`). Run `python3 framework/tools/orchestrate.py start <record> --command speckit.git.commit`; it refuses any record not at that step. `$ARGUMENTS`, if given, is the PM's note.
3. Before the tool: write the lesson decision if there is one (`decisions/D-<nnnn>-<slug>.md`, category `process` or `code`, never superseding; `record:` naming this record); for a delivered rule, write the rule into `architecture.md` and mark the old rule's decision superseded. Stage nothing by hand.
4. Run `python3 framework/tools/commit.py <record> --dry-run` and check the file set and the message: the component folders the task lines name, the delivered node files, this record's decisions, the three indexes, the record. Then run it without `--dry-run`. It regenerates the indexes (the decision log must validate), sets each node's `Status: delivered <version>`, writes the outcome, moves the record `commit → was-rule → done` through `orchestrate.py advance` (add `--still-needs-logic` when the request that needed the rule continues in Define: `→ resume-define`), stages exactly that set and commits as `<record slug>: <title>`.
5. Re-sort any waiting record on a node this delivered, then `python3 framework/tools/orchestrate.py next <record>` to confirm it is closed.

Never write code before `deliver.approve-plan` is answered "execute". Never save a node before `define.approve`. Never mark done before `deliver.accept`. In doubt, take the exit with more review and write why into the record.
