# 🌱 Workflow Studio

### *Ship a product with one PM and one AI — define, found, deliver.*

**Three YAML workflows, 51 steps, 21 slash commands: a product manager who never reads code runs an AI coding agent through logic → plan → build → proof, with a PM yes at every gate and a tool that refuses to skip one.**

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue) ![Works with 5 AI tools](https://img.shields.io/badge/works%20with-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20Copilot%20%C2%B7%20Gemini%20%C2%B7%20Cursor-informational) ![Status](https://img.shields.io/badge/status-working%2C%20unreleased-orange)

![The three workflows and how a request moves between them](docs/map.png)

You describe what the product should do, in your own words. The AI sorts the request, drafts the logic, challenges its own draft, plans, builds, and proves the result against the criteria you confirmed. You decide three times: approve the logic, approve the plan, accept the result. `orchestrate.py` refuses to move a change past a gate without its artifact.

```bash
cp -r /path/to/workflow-studio/framework . && cp -r /path/to/workflow-studio/workflows framework/
python3 framework/tools/orchestrate.py check     # CLOSED — 51 steps …; then, in your AI tool: /speckit-specify …
```

> Are you the AI agent operating this framework? Jump to [🤖 For AI agents](#-for-ai-agents).

## Table of contents

- [🤔 Why](#-why)
- [🧭 The three workflows](#-the-three-workflows)
- [⚡ Get started](#-get-started)
- [🧾 Worked example](#-worked-example-refund-within-7-days)
- [📋 Slash commands](#-slash-commands)
- [🧱 How it works](#-how-it-works)
- [🤖 For AI agents](#-for-ai-agents)
- [🔌 Supported tools](#-supported-tools)
- [🧩 Customizing the workflows](#-customizing-the-workflows)
- [❓ FAQ](#-faq)
- [🔧 Prerequisites](#-prerequisites)
- [🚫 What it is not](#-what-it-is-not)
- [📖 Learn more](#-learn-more)
- [💬 Support](#-support)
- [🙏 Acknowledgements](#-acknowledgements)
- [📄 License](#-license)

## 🤔 Why

- **One PM, no code.** Everything the PM reads is plain language: nodes, change records, plans, evidence. `code/` is never opened by the PM.
- **Gates are enforced, not advised.** `orchestrate.py advance` is the only way a record moves. It refuses an edge not in the YAML, a PM step without the PM's answer, a challenge without its findings block, a fourth build after three failed verifications.
- **State lives in a file.** The record's front matter holds the step, lane, who it waits on, and every edge taken. Any AI, in any tool, resumes with `orchestrate.py next`.
- **Every draft is challenged before you see it.** Logic, architecture, plan and delivered code each get a second, independent AI pass in a fresh context; zero findings on non-trivial work forces a rerun (full lane).
- **Decisions are remembered.** Anything chosen over an alternative goes to `decisions/` and comes back to the PM before it can be reversed.
- **Commands mirror Spec Kit.** `/speckit-specify`, `-plan`, `-implement`… agents already know the shape.
- **Renders to one HTML file.** `studio.html` draws every workflow with no external requests.

## 🧭 The three workflows

| Workflow | Owner | Question it answers | Steps | You get |
|---|---|---|---|---|
| `define` | PM | What should the product do? | 18 | An approved node (description + acceptance criteria) on the business side |
| `foundation` | PM | What may the AI build with? | 14 | The architecture file, the glossary, or one changed rule |
| `deliver` | AI | Is it built and does it work? | 19 | Tagged, tested components, one commit, the record closed |

```
PM request → define.intake → sort → discuss → write → challenge → approve ✔ → commit
                                 ↘ foundation (new product / rule change) ↩
                                                     ↓
              deliver.trace → plan → challenge-plan → approve-plan ✔ → execute → verify → passes → accept ✔ → commit → done
```

✔ = a PM gate. Every way back is an edge in the YAML: revise the logic → `define.discuss`, revise the plan → `deliver.plan`, stop → `drop`.

### `define` — Define business logic (18 steps)

| Step | Owner | What | Badge |
|---|---|---|---|
| `intake` | PM | State the idea or request | ENTRY · PM INPUT · OUTPUT |
| `sort` | AI | What kind of request is this? | OUTPUT |
| `answer` | AI | Answer from the business side | OUTPUT |
| `settled` | PM | PM settled? | PM INPUT |
| `answered` | PM | Answered | EXIT |
| `confirm-exists` | PM | PM confirms it already exists? | PM INPUT |
| `exists` | PM | Already exists | EXIT · OUTPUT |
| `to-foundation` | PM | Set or change the foundation first | EXIT → `foundation.new-or-change` · OUTPUT |
| `to-fix` | PM | Send the fix straight to delivery | EXIT → `deliver.trace` · OUTPUT |
| `discuss` | PM | Discuss the capability | PM INPUT · OUTPUT |
| `write` | AI | Write or update the node, or the node set | OUTPUT |
| `challenge` | AI | Challenge the logic | OUTPUT |
| `approve` | PM | PM approves the logic? | PM INPUT · OUTPUT |
| `commit` | AI | Save the business side | OUTPUT |
| `to-deliver` | PM | Send to delivery | EXIT → `deliver.trace` · OUTPUT |
| `drop` | AI | Drop the request | OUTPUT |
| `handed-over` | PM | Handed over; the record continues in Foundation or Delivery | EXIT |
| `dropped` | PM | Request dropped | EXIT |

![The define workflow, opened in studio.html](docs/define.png)

<details>
<summary><b><code>foundation</code> — Foundation (14 steps)</b></summary>

| Step | Owner | What | Badge |
|---|---|---|---|
| `new-or-change` | AI | New product or rule change? | ENTRY |
| `architecture` | PM | Write the architecture file | PM INPUT · OUTPUT |
| `check` | AI | Architecture file complete and consistent? | OUTPUT |
| `glossary` | PM | Write the glossary | PM INPUT |
| `save` | AI | Save the foundation | OUTPUT |
| `foundation-only` | AI | Was the request the foundation itself? | — |
| `ready` | PM | Return to the discussion | EXIT → `define.discuss` · OUTPUT |
| `propose-rule` | PM | Propose the changed rule | PM INPUT · OUTPUT |
| `check-rule` | AI | Proposed rule consistent with the file? | OUTPUT |
| `impact` | PM | Send the proposal for an impact check | EXIT → `deliver.trace` · OUTPUT |
| `not-needed` | PM | Continue without a foundation change | EXIT → `define.discuss` · OUTPUT |
| `drop` | AI | Drop the request | OUTPUT |
| `dropped` | PM | Request dropped | EXIT |
| `done` | PM | Foundation handled | EXIT |

</details>

<details>
<summary><b><code>deliver</code> — Deliver code (19 steps)</b></summary>

| Step | Owner | What | Badge |
|---|---|---|---|
| `trace` | AI | Trace the affected code and reusable components | ENTRY · OUTPUT |
| `plan` | AI | Write the change plan in plain language | OUTPUT |
| `challenge-plan` | AI | Challenge the plan | OUTPUT |
| `approve-plan` | PM | PM approves the plan? | PM INPUT · OUTPUT |
| `execute` | AI | Execute the change | OUTPUT |
| `tasks-done` | AI | All tasks done as planned? | — |
| `verify` | AI | Verify against the acceptance criteria | OUTPUT |
| `passes` | AI | Verification passes? | OUTPUT |
| `accept` | PM | PM accepts the result? | PM INPUT · OUTPUT |
| `commit` | AI | Save code, tests and record together | OUTPUT |
| `was-rule` | AI | Was this a proposed rule? | — |
| `drop` | AI | Drop the change | OUTPUT |
| `was-rule-drop` | AI | Did a request need this rule? | — |
| `back-to-define` | AI | Return to the business side | EXIT → `define.discuss` · OUTPUT |
| `back-to-foundation` | AI | Return the rule to Foundation | EXIT → `foundation.propose-rule` · OUTPUT |
| `resume-define` | AI | Continue the request | EXIT → `define.discuss` · OUTPUT |
| `returned` | AI | Sent back for revision | EXIT |
| `dropped` | AI | Change dropped | EXIT |
| `done` | AI | Delivered | EXIT |

</details>

Generated from `workflows/*.yaml`; `framework/steps.md` has the long form.

## ⚡ Get started

### Quickstart

1. **Install** — copy `framework/` into the product repository, run the check, install the slash commands (once per product).
2. **Constitute** the architecture (`/speckit-constitution`) — once per product.
3. **Specify** a request (`/speckit-specify`) and discuss it.
4. **Approve the logic** (`/speckit-approve`).
5. **Approve the plan** the AI writes (`/speckit-plan`, then answer *execute*), then **accept** the result (`/speckit-accept`); the AI commits (`/speckit-git-commit`).

### 1. Install

No package: a product repository copies `framework/` in, with the workflows inside it.

```bash
mkdir my-product && cd my-product && git init
cp -r /path/to/workflow-studio/framework .
cp -r /path/to/workflow-studio/workflows framework/
cp framework/templates/AGENTS.md framework/templates/CLAUDE.md .
python3 framework/tools/orchestrate.py check
```

**Output:**

```
CLOSED — 51 steps, every one mapped to a role and mode; 21 commands, every one entering a real non-routing step
```

Then install the slash commands for your tool.

**Claude Code**

```bash
python3 framework/tools/install_commands.py --agent claude
```

```
claude: .claude/skills/
installed 21 file(s); invoke as /speckit-<name> (Gemini: /speckit.<name>)
```

<details>
<summary>Codex, Copilot, Gemini, Cursor, or all five</summary>

```bash
python3 framework/tools/install_commands.py --agent codex     # .agents/skills/speckit-<name>/SKILL.md
python3 framework/tools/install_commands.py --agent copilot   # .github/skills/speckit-<name>/SKILL.md
python3 framework/tools/install_commands.py --agent gemini    # .gemini/commands/speckit.<name>.toml
python3 framework/tools/install_commands.py --agent cursor    # .cursor/skills/speckit-<name>/SKILL.md
python3 framework/tools/install_commands.py --agent all
```

</details>

Fill in the two command placeholders in `AGENTS.md` (how to run the product, how to run the test suite).

### 2. Constitute the product

In your AI tool, paste or describe the architecture: tools, language, systems, rules, how to run it, where secrets live, what the AI must never do.

```
/speckit-constitution Node 20 + Fastify backend under code/backend, React frontend under code/frontend, Postgres on Supabase. Run with `npm run dev`. Never touch migrations/ by hand. Secrets only in .env, supplied by me.
```

Sorted to `foundation`: the AI challenges the file, you write the glossary, `architecture.md` and `glossary.md` are saved.

### 3. Specify a request

Focus on **what** and **for whom**, not the tech stack.

```
/speckit-specify Members can cancel a policy within 7 days of purchase and get the full premium back, as long as no claim was filed. Refund goes to the original payment method.
```

**Output** (the orchestrator, run by the AI):

```
$ python3 framework/tools/orchestrate.py start changes/2026-09-10-1-refund-unused-policy.md --command speckit.specify
started at define.intake via speckit.specify
step:     define.intake — State the idea or request
mode:     pm   role: Sorter   lane: full   waiting on: PM since 2026-09-10T07:50+00:00
inputs:   request
PM gives: The request in the PM's own words. For a bug, what was seen and where. Every PM message is an intake, including an answer at a gate that carries a new request inside it, and including "just fix the typo".  → record it with `advance --answer`
does:     PM states what is wanted: a new capability, a change to existing logic, a bug against delivered logic, a dependency patch or a refactor that keeps behaviour, a question about the product or its status, a queue instruction (cancel, reorder), a document (a PRD, notes) holding several of these, or a request received from someone else. A document is split by the AI into one record per request, listed back to the PM to order.
produces: A change record is created for the request the moment it is stated (named by date, number and a short slug), with a status line naming the current step, who it waits on, and since when; the queue lists all records in order.
exits:
  1. → define.sort
```

Your words are recorded; the AI sorts:

```
$ python3 framework/tools/orchestrate.py advance changes/2026-09-10-1-refund-unused-policy.md --to sort --answer "Refund within 7 days for unused policies"
define.intake → define.sort
step:     define.sort — What kind of request is this?
mode:     agent   role: Sorter   lane: full   waiting on: AI since 2026-09-10T07:50+00:00
inputs:   record, architecture, logic-index, queue, decisions-index
does:     The AI reads the architecture file and searches the logic tree and the queue, then sorts the request and writes why. The PM overrules the sorting at the first PM step of the chosen path: settled (a question), confirm-exists, discuss (which can redirect to any other path), the Foundation input step (which can say "not needed"), or deliver.approve-plan.
produces: The kind chosen, the reason, and the lane (small or full), written into the record's state
exits:
  1. → define.answer   when: a question (what does the product do, where is a request, why does it behave this way, is this in scope, show me the product) or a queue instruction (cancel or reorder a waiting request)
  2. → define.confirm-exists   when: the logic already exists as a node
  3. → define.discuss   when: new logic, a change to an existing node, or a cross-cutting change to several nodes
  4. → define.to-foundation   when: no architecture file yet, or the request needs a tool, language or rule the architecture does not allow
  5. → define.to-fix   when: existing logic and unchanged criteria — code wrong (the AI can name the violated criterion), a dependency patch, or a refactor that keeps behaviour
last edges:
  define.intake → define.sort  answer: Refund within 7 days for unused policies
```

It takes exit 3, you discuss, it writes and challenges the draft, and stops at `define.approve` with the draft, findings and criteria for you to read.

### 4. Approve the logic

```
/speckit-approve yes
```

The node is saved as `logic/<parent>/refund-unused-policy.md`, `Status: approved, not yet delivered`; the record is handed to `deliver.trace`.

### 5. Approve the plan, then accept the result

```
/speckit-plan
```

The AI traces the code, writes a plan section for you (no code words) and a task list for itself, challenges it, and stops at `deliver.approve-plan`: *execute*, *revise the plan*, *revise the logic* or *drop*. On *execute* it builds task by task, runs the whole suite, verifies against your criteria in a second pass, and stops at `deliver.accept` telling you what to try.

```
/speckit-accept accepted
/speckit-git-commit
```

One commit: code, tests, the completed record, regenerated indexes, node status `delivered <version>`.

### 6. Open the drawing

Open `studio.html` from this checkout in a browser: the map, each workflow, every node labelled ENTRY / EXIT / PM INPUT / OUTPUT. No server, no network.

### 7. What if the AI tries to skip ahead?

It cannot. Real refusals from the walk above:

```
$ python3 framework/tools/orchestrate.py start changes/2026-09-10-2-fresh.md --command speckit.implement
refused: speckit.implement is not an entry command; it continues a record already at deliver.execute (this one is at no state). New requests start with speckit.specify.

$ python3 framework/tools/orchestrate.py advance changes/2026-09-10-1-refund-unused-policy.md --to sort
refused: define.intake is a PM step; record the PM's answer with --answer "…"

$ python3 framework/tools/orchestrate.py advance changes/2026-09-10-1-refund-unused-policy.md --to approve
refused: write the block `## Findings — define.challenge` into the record before leaving (a line "none" if nothing was found)

$ python3 framework/tools/orchestrate.py advance changes/2026-09-10-1-refund-unused-policy.md --to execute
refused: deliver.trace has no edge to execute. Legal exits: 1. deliver.plan

$ python3 framework/tools/commit.py changes/2026-09-10-1-refund-unused-policy.md --dry-run
refused: the record is at deliver.trace, not deliver.commit; the commit happens only after the PM accepts at deliver.accept
```

Every refusal exits 1, so the command template stops. The fix is always the same: produce what the refusal names, then `advance` again.

## 🧾 Worked example: refund within 7 days

One request through the whole system. Paths follow the product-repository layout in `framework/README.md`; the record is the one from the walk above, the node, decision and component names are what this request would produce.

| Step | Who | What the PM types | What appears on disk |
|---|---|---|---|
| `define.intake` | PM | `/speckit-specify Members can cancel a policy within 7 days of purchase and get the full premium back, as long as no claim was filed…` | `changes/2026-09-10-1-refund-unused-policy.md` (front matter: `step`, `lane`, `waiting_on`, `history`), `changes/QUEUE.md` |
| `define.sort` | AI | — | Sort reason and lane (`small`: one node, no new component, no rule) written into the record |
| `define.discuss` | PM | "Members, not agents. No claim filed and no service used. Full premium, original payment method. Day 7 ends 23:59 local time." | Discussion notes appended to the record |
| `define.write` | AI | — | Draft node in the working copy: description, criteria, placement under `logic/policy/`, glossary addition *unused policy* |
| `define.challenge` | AI | — | `## Findings — define.challenge` in the record (e.g. "unused" was ambiguous → fixed), affected nodes listed |
| `define.approve` ✔ | PM | `/speckit-approve yes` | `logic/policy/refund-unused-policy.md` (`Status: approved, not yet delivered`), `glossary.md`, `logic/INDEX.md`, `decisions/D-0007-refund-window.md` |
| `deliver.trace` → `plan` → `challenge-plan` | AI | `/speckit-plan` | Plan section + task list (`- [ ] T001 [P] [refund-unused-policy] …`) with sources, in the record |
| `deliver.approve-plan` ✔ | PM | "execute" | Answer in `history`; a decision file for the plan and for any dependency it adds |
| `deliver.execute` → `verify` → `passes` | AI | — (optionally `/speckit-taskstoissues` to mirror tasks as GitHub issues) | `code/backend/refund-request/` with tests, tagged `@node refund-unused-policy`; tasks ticked; test results and `## Findings — deliver.verify` in the record |
| `deliver.accept` ✔ | PM | `/speckit-accept accepted` — after cancelling a test policy in the running product | Answer in `history` |
| `deliver.commit` → `done` | AI | `/speckit-git-commit` | One git commit `refund-unused-policy: <title>`: code, tests, record, `code/COMPONENTS.md`, `decisions/INDEX.md`, node status `delivered <version>` |

*Revise the logic* at `approve-plan` would have sent the record `back-to-define → define.discuss`: code set aside on a branch, node re-challenged, then a fresh plan.

## 📋 Slash commands

Names follow [GitHub Spec Kit](https://github.com/github/spec-kit) where the meaning overlaps. Entry commands create a record at `define.intake`; every other command continues a record already at its step, or is refused. Invoke as `/speckit-<name>` (Gemini: `/speckit.<name>`).

### Core

| Command | Enters step | When to run | Spec Kit equivalent |
|---|---|---|---|
| `/speckit-constitution` | `define.intake` | First request of a product: state the architecture; sorted to Foundation | `speckit.constitution` |
| `/speckit-specify` | `define.intake` | Any request; sorted, and for logic discussed and drafted as a node | `speckit.specify` |
| `/speckit-approve` | `define.approve` | The PM approves the logic and confirms the criteria | — |
| `/speckit-plan` | `deliver.trace` | After approval: trace affected code and components, then write the plan | `speckit.plan` |
| `/speckit-implement` | `deliver.execute` | Only after `approve-plan` was answered *execute*; refuses any other record | `speckit.implement` |
| `/speckit-converge` | `deliver.verify` | Verify against the criteria and route through `passes` | `speckit.converge` |
| `/speckit-accept` | `deliver.accept` | The PM uses the result or reads the evidence and answers | — |
| `/speckit-git-commit` | `deliver.commit` | After *accepted*: the one code commit (`framework/tools/commit.py`); refuses any record not at `deliver.commit` | `speckit.git.commit` |

### Optional

| Command | Enters step | When to run | Spec Kit equivalent |
|---|---|---|---|
| `/speckit-clarify` | `define.write` | Open questions on the current draft: max three, one at a time, each with a recommended option | `speckit.clarify` |
| `/speckit-checklist` | `define.challenge` | Challenge the draft node. Spec Kit's checklist is for the human to tick; ours runs the challenger | `speckit.checklist` |
| `/speckit-tasks` | `deliver.plan` | Re-plan: rewrites the plan and task list (`T001 [P] [node]`), then challenge-plan runs again | `speckit.tasks` |
| `/speckit-analyze` | `deliver.challenge-plan` | Challenge the plan with the criterion-to-task coverage table | `speckit.analyze` |
| `/speckit-taskstoissues` | `deliver.execute` | At `execute` or later: mirror the task list as GitHub issues (`tasks_to_issues.py`); moves nothing | `speckit.taskstoissues` |
| `/speckit-bug-assess` | `define.intake` | Report a bug; sorted as a fix when the violated criterion can be named | `speckit.bug.assess` |
| `/speckit-bug-fix` | `deliver.execute` | Execute the approved fix plan | `speckit.bug.fix` |
| `/speckit-bug-test` | `deliver.verify` | Verify the fix; passes only if the failing criterion now holds | `speckit.bug.test` |
| `/speckit-assess-intake` | `define.intake` | An idea, sorted like any request; the discussion and challenge replace Spec Kit's assess pipeline | `speckit.assess.intake` |
| `/speckit-rule` | `define.intake` | Ask for a change to one architecture rule; the decision behind the current rule is brought forward | — |
| `/speckit-status` | `define.intake` | Where is everything; answered from the queue | — |
| `/speckit-why` | `define.intake` | Why does it behave this way; answered from the decision log first | — |
| `/speckit-drop` | `define.intake` | Stop a request: a queue instruction, or a stop at the current gate | — |

Source: `framework/orchestration/commands.yaml`; templates: `framework/commands/`.

## 🧱 How it works

- **The workflows are YAML** (`workflows/*.yaml`; `map.yaml` names the system entry `define.intake` and exit `deliver.done`). `SCHEMA.md` is the contract; `tools/validate.py` enforces its 8 graph rules, including "no stale step".
- **The orchestrator reads them as a state machine.** `framework/orchestration/roles.yaml` maps each of the 51 steps to one of six roles (Sorter, Writer, Planner, Builder, Verifier, Challenger) and a mode (`pm`, `agent`, `challenger`, `auto`); `orchestrate.py check` proves the mapping is complete.
- **A change record is the state.** Its front matter carries `step`, `lane`, `waiting_on`, `failed_passes`, `rerun_count` and `history`; `advance` appends an edge and refuses anything the YAML does not allow.
- **The renderer draws it.** `tools/build.py` embeds the YAML into `studio.html` and regenerates `framework/steps.md`.

<details>
<summary>File layout of a product repository</summary>

```
architecture.md            the architecture file (PM)
glossary.md                the glossary (PM)
logic/                     the logic tree: one file per node; logic/INDEX.md generated
decisions/                 D-<nnnn>-<slug>.md, one per decision that had an alternative; INDEX.md generated
changes/                   one change record per request; changes/QUEUE.md is the index
code/<system>/<component>/ components and tests, tagged @node <id>; code/COMPONENTS.md generated
framework/                 copied from this repository, with framework/workflows/ inside
AGENTS.md, CLAUDE.md       the operating card, from framework/templates
.claude/skills/…           the installed slash commands (per tool)
```

</details>

## 🤖 For AI agents

You are the **AI** role. The PM is the only human.

1. Read `AGENTS.md` in the product repository, then `framework/README.md`, then `changes/QUEUE.md` for the record in flight.
2. Run `python3 framework/tools/orchestrate.py check`. If it does not print `CLOSED`, stop and report.
3. `python3 framework/tools/orchestrate.py next <record>` tells you the step, your role and mode, the inputs you may read, your framing if you are the challenger, and the numbered legal exits. Do exactly that step. Write its output into the record.
4. Move only with `python3 framework/tools/orchestrate.py advance <record> --to <exit number> --when <condition number>`; add `--answer "<the PM's words>"` at a PM step. Never edit the front matter. Never pick a step yourself.
5. A line starting `refused:` is not an error to work around. It names the missing artifact (the PM's answer, a `## Findings — <step>` block) or the only legal exit. Produce it, or stop and ask the PM.
6. When `next` shows `mode: pm`, stop and show the PM what they are asked, with the options as the YAML lists them.
7. As a challenger, read only the listed inputs, never the conversation that produced the work; return findings only. Zero findings on non-trivial work in the full lane → `orchestrate.py rerun`.

Never write code before `deliver.approve-plan` is answered *execute*. Never save a node before `define.approve`. Never mark done before `deliver.accept`. In doubt, take the exit with more review and write why into the record.

## 🔌 Supported tools

| Tool | Install | Commands land in | Invoke as |
|---|---|---|---|
| Claude Code | `python3 framework/tools/install_commands.py --agent claude` | `.claude/skills/speckit-<name>/SKILL.md` | `/speckit-<name>` |
| Codex | `… --agent codex` | `.agents/skills/speckit-<name>/SKILL.md` | `/speckit-<name>` |
| GitHub Copilot | `… --agent copilot` | `.github/skills/speckit-<name>/SKILL.md` | `/speckit-<name>` |
| Gemini CLI | `… --agent gemini` | `.gemini/commands/speckit.<name>.toml` | `/speckit.<name>` |
| Cursor | `… --agent cursor` | `.cursor/skills/speckit-<name>/SKILL.md` | `/speckit-<name>` |

`--agent all` installs all five (105 files). The layout mirrors Spec Kit ≥ 1.0's skills layout, so a move either way is a file swap; the installer is idempotent.

## 🧩 Customizing the workflows

The YAML is the source of truth; everything else is generated from it or checked against it.

| Goal | Edit | Then run |
|---|---|---|
| Change a step's wording, condition or exit | `workflows/<id>.yaml` | `python3 tools/check_all.py` |
| Add a step | `workflows/<id>.yaml` + a role/mode line in `framework/orchestration/roles.yaml` | `python3 tools/check_all.py` |
| Add or rename a slash command | `framework/orchestration/commands.yaml` + `framework/commands/speckit.<name>.md` | `orchestrate.py check`, then reinstall |
| Add a field to the schema | `SCHEMA.md`, `tools/validate.py`, a `DECISIONS.md` entry first | `python3 tools/check_all.py` |
| Change a challenger's framings | `framework/orchestration/roles.yaml` | `orchestrate.py check` |

`tools/check_all.py` runs the validator, the builder, the docs generator, the self-containment check on `studio.html`, `orchestrate.py check` and the product-side generators on a fixture; it ends with `ALL CHECKS PASSED` or stops at the first failure. Re-read `framework/test-cases.md` after any workflow change. Never edit `studio.html` or `framework/steps.md` by hand.

## ❓ FAQ

**Where is my data?** In your product repository, as files: `logic/`, `changes/`, `decisions/`, `code/`. History is git. Only `/speckit-taskstoissues` talks to a service (GitHub issues via `gh`, after you confirm).

**Can two people use it?** No: one PM, one AI, one change in flight per node. A second request on the same node waits in the queue.

## 🔧 Prerequisites

- Python 3.10+ with [PyYAML](https://pypi.org/project/PyYAML/) (`pip install pyyaml`), the only third-party package any tool imports.
- git.
- One of Claude Code, Codex, GitHub Copilot, Gemini CLI or Cursor.
- `gh` only if you use `/speckit-taskstoissues` (without it the tool prints a dry run).

## 🚫 What it is not

- Not a deployment pipeline. Build only; a change is done when it is committed and the PM has seen it work. Release is outside.
- Not a multi-approver system. One PM, by design.
- Not a spec-per-feature tool. The whole product is one logic tree; a change to a delivered node is a new version with a logic delta the PM can read.

## 📖 Learn more

- `framework/README.md` — operating reference: roles, terms, the loop, doubt defaults, conventions.
- `framework/orchestration/README.md` — the state machine and its refusals.
- `framework/steps.md` — every step, generated.
- `SCHEMA.md` — what a workflow file may contain.
- `DECISIONS.md` — why every design choice was made, in order.
- `framework/test-cases.md` — the regression suite: every case with its verdict and step path.

## 💬 Support

Working, unreleased; no CONTRIBUTING.md yet. For a bug, run `python3 tools/check_all.py` and open an issue with its output. For a workflow change, follow `AGENTS.md`: edit YAML → validate → challenger review → build.

## 🙏 Acknowledgements

[GitHub Spec Kit](https://github.com/github/spec-kit) for the command vocabulary and the skills layout, kept so muscle memory survives a move either way.

Built in September 2026 by [Rira](https://github.com/rishabhrawat35) with Claude, one challenge pass at a time.

## 📄 License

No license yet. Until one is added, the code is not licensed for reuse.
