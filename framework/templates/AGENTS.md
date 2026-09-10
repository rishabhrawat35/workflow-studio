# AGENTS.md — operating card for any AI on this product

You are the **AI** role of the product-development framework; the PM is the
only human. Read `framework/README.md` (rules, gates, doubt defaults), then
`changes/QUEUE.md` (where every request is). This card only says what those
files cannot: where things are here, the exact commands, and how to resume.

## Where things are
- Business side: `architecture.md`, `glossary.md`, `logic/` (`INDEX.md` = overview), `changes/` (`QUEUE.md` = index), `decisions/` (one file per decision; `INDEX.md` = index).
- Code side: `code/<system>/<component>/`, tests beside code, tags `@node <id>`; `code/COMPONENTS.md` = map.
- Secrets and environment values: only where `architecture.md` says.

## Commands (exact; fill in for this product)
- Run the product: `<from architecture.md>`
- Whole test suite: `<exact command>`
- Regenerate indexes: `python3 framework/tools/logic_index.py && python3 framework/tools/components_index.py && python3 framework/tools/decisions_index.py`

## Entry and resume
- Every PM message is `define.intake`, including "just fix the typo" and a new request hidden in a gate answer. Slash commands: `/speckit.specify`, `/speckit.plan`, `/speckit.implement`, `/speckit.accept`, `/speckit.status`, `/speckit.why` (full list: `framework/orchestration/commands.yaml`).
- Before anything: `python3 framework/tools/orchestrate.py check` must print CLOSED.
- To act: `python3 framework/tools/orchestrate.py next <record>` tells you the step, your role, your inputs and the legal exits. Do that step; move with `advance --to <exit> --when "<condition>"`. Never pick a step yourself.
- To resume: `next` on the record in flight (see `changes/QUEUE.md`). Never start from scratch.

## Decisions
- At every gate answer, drop, saved rule with an alternative, and AI choice that adds a dependency or a stored data shape: write `decisions/D-<nnnn>-<slug>.md` with an "Instead of …" line (format in `framework/components/decision-log.md`). No alternative, no decision file.
- Before it: search `decisions/` for an active decision this alters; show it to the PM (situation, decision, reasons) next to the new one; change it only on an explicit yes, then mark it superseded.

## Never
- Anything under "never" in `architecture.md`.
- Code before `deliver.approve-plan` says execute; a saved node before `define.approve`; "done" before `deliver.accept`.
