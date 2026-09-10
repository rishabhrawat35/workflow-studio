# Decisions

Append-only log. Newest at the bottom. Each entry: date, decision, why.

## 2026-09-09 — Approach

- **Workflows as code.** One YAML file per workflow, edited by Claude, reviewed by Rira. Reason: text is diffable, versionable and reliably editable; drawings are not.
- **Repo location:** `~/Downloads/workflow-studio` on Rira's machine. Everything is saved here before any step is considered done.
- **Renderer:** a single self-contained `studio.html` with no external libraries (own layered layout; works offline), also published as a Claude artifact. Two views: one workflow, and the map of all workflows.
- **Cross-workflow links live only in `handoff.to`.** `map.yaml` holds the registry and grouping; links are derived, never typed twice.
- **Layout is automatic.** No coordinates in the files.
- **Schema is minimal.** Fields are added only when a real workflow needs them, logged here first.
- **Change loop:** edit YAML → `python3 tools/validate.py` → independent challenger review of the diff → `python3 tools/build.py` → commit → republish artifact. Nothing is saved without passing validation and review.
- **No invented content.** Workflows are written only from what Rira describes or documents he provides. Business and product case are discussed first; workflows are defined after.
- **Content order:** no workflow exists yet. First step is a discussion of the business case and product case; the first workflow follows from that.

## 2026-09-09 — Scaffold review

- Challenger review of the scaffold found 3 must-fix bugs (JSON embedding corrupted multi-line text; empty `map.yaml` skipped map checks; duplicate error lines) and a dozen minor ones. All fixed before the first commit.

## 2026-09-09 — First workflows: the product-development framework

- Three workflows, one per layer: `foundation` (architecture file + glossary), `define` (business side, PM's), `deliver` (code side, Claude's, PM gates only). Handoffs run both ways between define and deliver, so the map shows the closed loop Rira asked for.
- Content comes from Rira's brief plus additions he accepted in discussion: acceptance criteria, stable ids with code tags, git as versioning, one change record per change, challenger passes, PM preview, glossary, "what will not change".
- One addition is Claude's, kept after review: an architecture rule change on an existing product re-enters delivery for an impact check (`foundation.impact → deliver.trace`). Reason: without it, code built under an old rule is never re-checked.
- Challenger review of the first draft found 6 must-fix issues (architecture not consulted on the business side; an architecture-change path claimed in text but absent from the graph; the node "committed" twice; dropped changes left on the business side; a tool-specific clause; unfinished code left in limbo on send-back) and 13 minor ones. All applied.

## 2026-09-09 — Operating reference (`framework/`)

- Every distinct structure gets one definition file in `framework/components/` with five fixed sections (Definition, Inputs, Outputs, How to interact, Place in the system), written for any AI or the PM. Steps are not documented by hand: `tools/docs.py` generates `framework/steps.md` from the YAML, so nothing is written twice.
- Where the workflows are silent, the reference makes a choice and marks it **(convention)**; the workflows stay the source of truth.
- Challenger review of the reference exposed four gaps in the workflows themselves, fixed in the YAML rather than documented around: a challenger pass before the plan reaches the PM (`deliver.challenge-plan`); a changed architecture rule is saved before its impact check (`foundation.save-rule`); glossary additions are proposed in `define.write`, approved with the node and saved at `define.commit`; the system role is named `AI`, not `Claude`, so the SOP is platform-neutral. Also: the architecture file must include how the product is run (needed for preview); `deliver.drop` returns a node to its last delivered version or removes it if never delivered.

## 2026-09-09 — Node-by-node audit of the framework (Rira's review)

- **One door.** Every idea, request or change enters at `define.intake`; Define decides whether the foundation covers it and hands off to Foundation when not. Foundation is never entered directly. Reason: the earlier `foundation.ready → define.discuss` handoff was decorative; the real dependency is Define needing the architecture file and glossary as inputs.
- **A rule change is a proposal.** `foundation.save-rule` removed. A changed rule is written at `foundation.propose-rule`, impact-checked and planned in Deliver, decided by the PM at `deliver.approve-plan`, and written into the architecture file only at `deliver.commit` (discarded at `deliver.drop`). Reason: saving the rule before knowing its impact let the architecture file claim rules the code did not follow.
- **Rule impact is read, not tagged.** Tags map code to node ids; a rule has none, so `deliver.trace` reads every tagged piece against the rule.
- **Acceptance criteria are a PM gate.** New decision `define.criteria`: the AI proposes criteria from what the PM said in discussion; the PM confirms, adds or removes them before the node is challenged. Reason: the criteria are the contract verification uses, and earlier nothing showed where the PM agreed them.
- **Return paths for rules.** `deliver.approve-plan` and `deliver.accept` gain "the proposed rule needs revising" → `deliver.back-to-foundation` → `foundation.propose-rule`.
- **Waiting requests are resumed.** After a rule is delivered, `deliver.was-rule` → `deliver.resume-define` → `define.discuss` continues the request that needed the rule (challenger finding: it was orphaned). If the rule is dropped, the PM restates the request at intake.
- Challenger review of this change set: 3 must-fix (orphaned request, rule impact wrongly described as tag-based, intake request not carried across the Foundation handoff) and 7 minor, all applied.

## 2026-09-09 — Entry, exit, input and output labels (rule)

- Rule for every workflow, enforced by the validator and drawn by the renderer: exactly one ENTRY (first step); every `end` and `handoff` is an EXIT; a step where the PM provides something carries `input` and is drawn PM INPUT; a step producing something durable carries `output`; at least one `input` step per workflow; `input` only on PM-owned steps. Reason: Rira could not see from the drawing where he feeds the system or where things leave it.
- Entry/exit are derived (no new field); `input`/`output` are new fields because they cannot be derived from `what`.
- System-level entry and exit are explicit in `map.yaml` (`entry`, `exit`), validated (entry = first step with `input`; exit = an `end` step) and drawn on the map as a PM source and a RESULT terminal. Handoff arrows on the map are named by the step they leave from.

## 2026-09-09 — Test-case activity, decisions

- `framework/test-cases.md` is the regression suite: 74 cases in 11 categories with verdicts and step paths, a node-by-node cut list, and proposals P1–P15. Challenger-reviewed; seven verdicts corrected, two proposals rejected as unsafe (rule written with the last of several records; merging the foundation check into intake).
- Rira decided: one PM (himself), no roles; release/deployment is out of scope — the framework ends at a committed, previewed change.

## 2026-09-09 — Change set P1–P6, P8–P15 applied

- **Intake sorts.** `define.intake` (PM) creates the change record; `define.sort` (AI) routes: already exists → PM told, nothing built; logic → discuss; foundation → handoff; fix (bug with a named failing criterion, or a dependency patch) → `define.to-fix` → `deliver.trace` directly. Replaces the PM-owned `covered` decision.
- **Criteria confirmed at approval.** `define.criteria` removed; `define.approve` confirms the criteria and gains the exit "PM changed criteria → challenge", so added criteria are still checked for verifiability before saving.
- **Preview merged into accept.** `deliver.accept` takes the PM's own use of the flow or the evidence when it cannot be used; gains "PM stops the change → drop".
- **Foundation checked.** `foundation.check` (new file) and `check-rule` (proposed rule) are AI decisions with an exit back to the PM for findings. `new-or-change` is AI-owned. The architecture file's required content now includes security/accessibility/performance rules, run instructions, systems and structure, environments, and where env vars and secrets live.
- **Code side is component-based.** `deliver.trace` searches existing components for reuse; `plan` states reused vs new and what happens to stored data, and records the current documentation consulted in a sources section the PM never reads; `challenge-plan` and `verify` treat a duplicate component as a finding; `execute` builds under `code/<system>/<component>/`; `verify` runs the whole suite; `commit` regenerates the component index.
- **Node sets and retirement.** A Define pass may cover a node set with one approval; `write` proposes placement and splits and can mark a node retired; `challenge` lists every affected node for the PM.
- **Conventions added:** change record born at intake with a status line; queue as index; one change in flight per node; dependencies; every step writes output to disk (resume from last completed step); stopping; retired nodes; large rule changes split with the rule written first.
- **Generators for product repositories:** `framework/tools/logic_index.py` (KT overview, criteria = use cases) and `components_index.py` (component → system → nodes; untagged and unserved flagged).
- PM touchpoints per ordinary change: 8 → 5 (intake, discuss, approve, approve-plan, accept); PM decisions: 3.

## 2026-09-09 — Agent behaviour, doubt rules, practice review

- `define.sort` gains a "question" exit → `define.answer` (answers only from the written business side) → `answered`. Documents (PRDs) are split into one record per request at intake.
- Doubt rules written into the workflows at every AI-owned decision; they always point towards more review. A challenge with zero findings on non-trivial work is re-run with a different framing (adopted from BMad's adversarial review).
- Plans carry a task list ticked at execute (Spec Kit); the PM sees the logic delta for every change (OpenSpec); a decisions ledger is appended at commit and the architecture file carries a never-do list (Gangsta Agents); `framework/templates/AGENTS.md` + `CLAUDE.md` are the operating card for any AI in a product repository.
- Validator rule 8: every step of every workflow must be reachable from the system entry across handoffs, and the exit from the entry — the automated "no stale node" check. Proven to fail on an orphan workflow.
- Sources: HackerNoon comparison of Spec Kit / OpenSpec / BMad / Gangsta Agents; morphllm AGENTS.md guide.

## 2026-09-09 — Assumption challenge, third change set

- Challenger attacked assumptions and found 19 must-fix items. Structural fixes: `deliver.execute` now ends in `tasks-done` (a task that cannot be done as planned returns to plan; a PM stop is taken at the task boundary); `define.discuss` is a PM decision that can redirect a wrongly sorted request (fix / exists / foundation / stop); `define.answer` ends in a PM `settled` decision so a question can never swallow a build request; Foundation has "not needed" (back to discuss) and "stop" (drop) at both check steps; `foundation-only` closes a request that was the foundation itself; a dropped rule returns its request to Define (`was-rule-drop`) instead of dropping the capability; `accept` "not matching" goes to plan, not to the same tasks; `approve-plan` gains "revise the plan"; the record is one record with one status line wherever it is (`define.handed-over`); records are named `<date>-<n>-<slug>`; the task list and sources sit in one AI section the PM does not read; every step, including PM answers and discussion notes, writes its output into the record; zero-findings rule extended to `verify` and `check-rule` with named framings and a definition of "non-trivial"; the fix guard is "the AI can name the violated criterion", not "the PM names it"; `define.commit` creates no version for an unchanged node.
- Conventions added: status line `<step> · waiting on PM|AI · <date>`; node `Status:` line (approved / delivered / retired, inherited by children); `framework/` copied into the product repo; queue shows PM-blocked count; at most one AI-initiated request while the PM is away; re-sort waiting records on delivery.
- Tools: dotted or malformed tags are a finding; retirement inherited by children in both indexes; components served only by retired nodes flagged; node status shown in the logic index. Validator rule 8 message prefixed with `workflows/`.
- Test-cases: sections M (20 first-week cases) and N (full re-run, all current) added; A–L kept as history.

## 2026-09-09 — Decision log as a first-class component

- Every finalising step now writes a structured decision file (`decisions/`), in the same save as its output: id, timestamp with timezone, region, category (product, business, ui, frontend, backend, code, infra, software, process), made_by, at_step, record, nodes, links, resources, status; body = decision, situation, reasons. Decisions are immutable; a later one supersedes.
- Supersede rule: before any gate, the AI searches the log and brings an altered decision forward to the PM (situation, decision, reasons, side by side); it changes only on an explicit yes. `challenge` and `challenge-plan` report alterations nobody brought forward. `answer` reads the log first for "why".
- `framework/tools/decisions_index.py` generates `decisions/INDEX.md` and validates the log (required fields, categories, unique ids, supersede chain consistency); a failing log blocks `deliver.commit`.
- Spec Kit review (github/spec-kit): not adopted as runtime (advisory gates, single-feature scope, no spec→code link). To take when a product starts: clarification markers with a hard cap and a recommended option, the task-line grammar, analyze's coverage table, research Decision/Rationale/Alternatives; optionally package framework steps as command files per AI tool. This decision is to be brought forward whenever a new product is started with the framework.
- Challenger on the decision log: drop now supersedes the record's decisions; accept and commit never supersede; AI decisions must name resources and the gate search covers components; the search is repeated at the gate on the final draft; volume threshold "no alternative, no decision file", validated by an "Instead of" line; `status` removed as derivable, id is the filename; `made_at` quoted ISO with offset; region = market (optional); `effective_from` optional; git check enforces immutability.

## 2026-09-10 — Orchestration layer 1, Spec Kit command names

- Orchestration layer: `framework/orchestration/{roles.yaml, commands.yaml, README.md}` and `framework/tools/orchestrate.py`. The workflow YAML is the state machine; a record's front matter is its state; the tool is the only thing that moves it (`check`, `next`, `advance`, `start`, `rerun`, `fail`). Six roles, four modes (pm, agent, challenger, auto). `check` proves closedness: 51 steps mapped, 19 commands entering real steps, every exit resolving.
- Commands carry Spec Kit's names where the meaning overlaps (constitution, specify, clarify, checklist, plan, tasks, analyze, implement, converge, bug.assess/fix/test, assess.intake) and the same prefix for ours (approve, accept, rule, status, why, drop); `install_commands.py` writes them to the same per-tool folders Spec Kit uses, so a move either way is a file swap. Reason: Rira wants to be able to move to Spec Kit seamlessly.
- Taken from Spec Kit into the steps: clarification cap (3 questions, recommended option, stated defaults), task grammar with phases and [P], criterion-to-task coverage table, Decision/Rationale/Alternatives for tool choices.
- Efficiency: a small lane (one node, no new component, no rule) runs each challenge once and keeps the plan to a paragraph; re-challenges after a revision read only the delta. Gates unchanged.
- Challenger on the orchestration layer (2026-09-10): eight must-fix items applied. `start` is entry-only (a fresh record cannot begin at execute); `advance` requires the step's findings block (and a rerun when zero findings with framings left) and the PM's `--answer`; the `passes → execute` edge is the failed-pass counter, capped at three with `execute` and `accept` refused after; `--lane` only at start or leaving sort; a handoff's only exit is its target (local end recorded as `closes`); `auto` only for handoffs and ends, judgment decisions are `agent` with the responsible role; installer rewritten to Spec Kit ≥ 1.0's skills layout with `$ARGUMENTS`; `assess.intake`, `checklist`, `tasks` labelled where their meaning differs from Spec Kit; refusing stubs for `taskstoissues` and `git.commit`; roles' inputs completed (run instructions at accept, decisions index at gates, components index at verify/commit).
