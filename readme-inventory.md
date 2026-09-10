# Inventory of `workflow-studio`

- **Reader:** anyone opening the repository for the first time; a second reader, the AI agent operating the framework inside a product repository, is redirected to AGENTS.md and framework/README.md.
- **Goal:** in ten minutes, understand what the three workflows do, copy the framework into a product folder, see `orchestrate.py check` print CLOSED, and watch one request move through a PM gate.
- **Doubt:** "Does the AI really get stopped at the gates, or is this advice?" — answered by the six refusals captured from a real walk, and "is this maintained?" — answered by the status line with the date checked.

Every line below was ticked after the file was opened during the run of 2026-09-10 (67 files: the 66 in the repository plus `README.prev.md`, the copy of the earlier README made by this run). `workflows/*.yaml` were read through their heads and their generated form, `framework/steps.md`, and the 51 step titles were compared against the YAML.

## File count by top-level folder

- `framework/` — 48 files
- `(root)` — 8 files
- `tools/` — 5 files
- `workflows/` — 4 files
- `docs/` — 2 files

## Every file in the repository

- [x] `docs/define.png` (image)
- [x] `docs/map.png` (image)
- [x] `framework/commands/speckit.accept.md` (text) — the PM uses the result or reads the evidence and answers — command/skill template
- [x] `framework/commands/speckit.analyze.md` (text) — challenge the plan with the criterion-to-task coverage table — command/skill template
- [x] `framework/commands/speckit.approve.md` (text) — the PM approves the logic and confirms the criteria — command/skill template
- [x] `framework/commands/speckit.assess.intake.md` (text) — an idea, sorted like any request. Spec Kit's assess pipeline (research, shape, decide) has no equivalent here; — command/skill template
- [x] `framework/commands/speckit.bug.assess.md` (text) — report a bug; sorted as a fix when the violated criterion can be named; traced without touching code — command/skill template
- [x] `framework/commands/speckit.bug.fix.md` (text) — execute the approved fix plan — command/skill template
- [x] `framework/commands/speckit.bug.test.md` (text) — verify the fix; verified only if the failing criterion now holds — command/skill template; test or fixture; shows real use and expected output
- [x] `framework/commands/speckit.checklist.md` (text) — challenge the draft node. Note: Spec Kit's checklist writes a requirements checklist for the human to tick; ou — command/skill template
- [x] `framework/commands/speckit.clarify.md` (text) — ask the open questions on the current draft: max three, one at a time, each with a recommended option — command/skill template
- [x] `framework/commands/speckit.constitution.md` (text) — state the architecture (their constitution) as the first request; sorted to Foundation, where the PM writes or — command/skill template
- [x] `framework/commands/speckit.converge.md` (text) — verify against the criteria and route through passes — command/skill template
- [x] `framework/commands/speckit.drop.md` (text) — stop a request: a queue instruction applied at answer, or a stop at the current gate — command/skill template
- [x] `framework/commands/speckit.git.commit.md` (text) — the one code commit of deliver.commit; refuses any record not at deliver.commit, so nothing is committed befor — command/skill template
- [x] `framework/commands/speckit.implement.md` (text) — continue a record already at deliver.execute (approve-plan answered execute); refuses any other record — command/skill template
- [x] `framework/commands/speckit.plan.md` (text) — trace affected code and components, then write the plan — command/skill template
- [x] `framework/commands/speckit.rule.md` (text) — ask for a change to one architecture rule; sorted to Foundation, where the decision behind the current rule is — command/skill template
- [x] `framework/commands/speckit.specify.md` (text) — state a request; it is sorted and, for logic, discussed and drafted as a node — command/skill template
- [x] `framework/commands/speckit.status.md` (text) — where is everything: sorted as a question, answered from the queue — command/skill template
- [x] `framework/commands/speckit.tasks.md` (text) — re-plan: re-enters deliver.plan, which rewrites the plan and its task list (T001 [P] [node] grammar), then cha — command/skill template
- [x] `framework/commands/speckit.taskstoissues.md` (text) — mirror the record's task list as GitHub issues, one per task, the number written back onto the task line; allo — command/skill template
- [x] `framework/commands/speckit.why.md` (text) — why does it behave this way: sorted as a question, answered from the decision log first — command/skill template
- [x] `framework/components/acceptance-criteria.md` (text) — Acceptance criteria
- [x] `framework/components/acceptance.md` (text) — Acceptance
- [x] `framework/components/architecture-file.md` (text) — Architecture file
- [x] `framework/components/challenger-pass.md` (text) — Challenger pass
- [x] `framework/components/change-record.md` (text) — Change record
- [x] `framework/components/code-tag.md` (text) — Code tag
- [x] `framework/components/component.md` (text) — Component
- [x] `framework/components/decision-log.md` (text) — Decision log
- [x] `framework/components/glossary.md` (text) — Glossary
- [x] `framework/components/history.md` (text) — History
- [x] `framework/components/logic-node.md` (text) — Logic node
- [x] `framework/components/logic-tree.md` (text) — Logic tree
- [x] `framework/orchestration/commands.yaml` (text) — Slash commands. Names follow GitHub Spec Kit where the meaning overlaps, so a
- [x] `framework/orchestration/README.md` (text) — Orchestration layer 1 — existing README of 1115 words; keep a copy before rewriting
- [x] `framework/orchestration/roles.yaml` (text) — Orchestration layer 1 — who runs each step, in which mode, reading what.
- [x] `framework/templates/AGENTS.md` (text) — AGENTS.md — operating card for any AI on this product — agent instructions
- [x] `framework/templates/CLAUDE.md` (text) — agent instructions
- [x] `framework/tools/commit.py` (text) — The one code commit of `deliver.commit` (`/speckit-git-commit`). — python script (`python3 framework/tools/commit.py`); CLI with flags; run it with --help; has main(); executable script (shebang)
- [x] `framework/tools/components_index.py` (text) — Generate code/COMPONENTS.md for a product repository built with the framework. — python script (`python3 framework/tools/components_index.py`); has main(); executable script (shebang)
- [x] `framework/tools/decisions_index.py` (text) — Generate decisions/INDEX.md for a product repository and validate the decision log. — python script (`python3 framework/tools/decisions_index.py`); has main(); executable script (shebang)
- [x] `framework/tools/install_commands.py` (text) — Install the framework's slash commands into a product repository for one AI tool. — python script (`python3 framework/tools/install_commands.py`); CLI with flags; run it with --help; has main(); executable script (shebang)
- [x] `framework/tools/logic_index.py` (text) — Generate logic/INDEX.md for a product repository built with the framework. — python script (`python3 framework/tools/logic_index.py`); has main(); executable script (shebang)
- [x] `framework/tools/orchestrate.py` (text) — Orchestration layer 1 for a product built with the framework. — python script (`python3 framework/tools/orchestrate.py`); CLI with flags; run it with --help; has main(); executable script (shebang)
- [x] `framework/tools/tasks_to_issues.py` (text) — Export a change record's task list to GitHub issues (`/speckit-taskstoissues`). — python script (`python3 framework/tools/tasks_to_issues.py`); CLI with flags; run it with --help; has main(); executable script (shebang)
- [x] `framework/README.md` (text) — Product-development framework — operating reference — existing README of 2630 words; keep a copy before rewriting
- [x] `framework/steps.md` (text) — Step reference
- [x] `framework/test-cases.md` (text) — Test cases for the framework
- [x] `tools/build.py` (text) — Embed map.yaml and workflows/*.yaml (as JSON) into the renderer. — python script (`python3 tools/build.py`); has main(); executable script (shebang)
- [x] `tools/check_all.py` (text) — One command that proves the repository. — python script (`python3 tools/check_all.py`); has main(); executable script (shebang)
- [x] `tools/docs.py` (text) — Generate framework/steps.md from workflows/*.yaml and map.yaml. — python script (`python3 tools/docs.py`); has main(); executable script (shebang)
- [x] `tools/studio.template.html` (text) — Workflow Studio
- [x] `tools/validate.py` (text) — Validate workflow-studio files against SCHEMA.md. — python script (`python3 tools/validate.py`); has main(); executable script (shebang)
- [x] `workflows/.gitkeep` (text)
- [x] `workflows/define.yaml` (text) — name: Define business logic
- [x] `workflows/deliver.yaml` (text) — name: Deliver code
- [x] `workflows/foundation.yaml` (text) — name: Foundation
- [x] `.gitignore` (text) — build/
- [x] `AGENTS.md` (text) — AGENTS.md — editing the workflow studio itself — agent instructions
- [x] `DECISIONS.md` (text) — Decisions
- [x] `map.yaml` (text) — Workflow of workflows. See SCHEMA.md.
- [x] `README.md` (text) — 🌱 Workflow Studio — existing README of 4186 words; keep a copy before rewriting
- [x] `README.prev.md` (text) — 🌱 Workflow Studio
- [x] `SCHEMA.md` (text) — Workflow Studio — Schema
- [x] `studio.html` (text) — Workflow Studio

## Vendored and generated folders, listed but not opened

- `build/` — 1 files (e.g. `studio.artifact.html`)
- `framework/tools/__pycache__/` — 1 files (e.g. `tasks_to_issues.cpython-311.pyc`)
- `tools/__pycache__/` — 1 files (e.g. `validate.cpython-311.pyc`)

## Python imports outside the standard library (verify that each is declared as a dependency)

`yaml`

Total: 67 files listed; 0 symlinks; 3 folders not opened; 0 secret files not read.
