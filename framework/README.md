# Product-development framework — operating reference

This folder is the reference for operating the framework. It is written for
any AI assistant (Claude, Gemini, or other) and for the PM. It describes how
the framework works; it contains no product content.

## Source of truth and read order

The workflow files are the source of truth. If anything in this folder
disagrees with `../workflows/*.yaml`, the document is wrong and gets fixed.

1. This file — roles, terms, the loop, conventions.
2. `components/` — one file per distinct thing the framework uses. Each
   file has the same five sections: Definition, Inputs, Outputs, How to
   interact, Place in the system. Sentences marked **(convention)** are
   choices this reference makes where the workflows are silent; everything
   else restates the workflows.
3. `steps.md` — every step of every workflow, generated from the YAML by
   `tools/docs.py`. Do not edit it by hand.
4. `test-cases.md` — the regression suite: every use case the framework
   has been checked against, with its verdict. Re-run after any change.
5. `../workflows/*.yaml` and `../map.yaml` — the workflows. `../studio.html`
   draws them. `../SCHEMA.md` defines the step types (step, decision,
   handoff, end) and the `input`/`output` fields.
6. `tools/` here — generators to run inside a product repository
   (`logic_index.py`, `components_index.py`, `decisions_index.py`).
7. `templates/AGENTS.md` and `templates/CLAUDE.md` — the operating card to
   copy into a product repository so any AI (Codex, Cursor, Gemini, Claude
   Code) picks the framework up on entry; fill in the exact commands.
8. `orchestration/` — layer 1: `roles.yaml` (step → role, mode, inputs,
   framings), `commands.yaml` (slash commands, Spec Kit names), and its
   README; layer 2: `harness.yaml` (how `tools/run.py` spawns a harness)
   and `toolbox.yaml` (optional per-step plugin skills). `tools/orchestrate.py`
   is the only thing that moves a record; `tools/run.py` (`/speckit-run`)
   runs every AI step in a fresh process and stops at the PM steps;
   `tools/install_commands.py` installs the commands per AI tool;
   `tools/tasks_to_issues.py` (`/speckit-taskstoissues`, from
   `deliver.execute` on) mirrors a record's task list as GitHub issues, and
   `tools/commit.py` (`/speckit-git-commit`, at `deliver.commit` only)
   makes the one code commit and moves the record through `orchestrate.py`
   (and restores the record if git refuses the commit).

## Roles

**PM** — the only human; one person. Writes the architecture file, the
glossary and every request; takes part in every discussion; makes every
decision marked `Owner: PM` in `steps.md`. Reads nodes, change records and
the running product. Never reads or edits code.

**AI** — the system. The workflows name this role `AI`; any AI assistant
operating the framework takes it. Sorts requests, writes nodes from
discussion, challenges its own work in a second independent pass, writes
change records in plain language, writes component-based code and tests
only after the PM approves a plan, and keeps the history. It may add a
request of its own to the queue, marked as its own; the PM decides on it
like any other.

## Scope

Build only. A change is finished when it is committed and the PM has seen
it work (or seen the evidence). Releasing to users is outside the framework.

## Terms

- **Business side** — the architecture file, the glossary, the logic tree
  and the change records. The PM reads and decides here.
- **Code side** — components and tests, organised by system, tagged by node
  id. The PM never opens it.
- **Layers** — foundation (architecture file, glossary), business logic
  (the logic tree), code. One workflow each.
- **PM gate** — a decision the PM makes: `define.approve`,
  `deliver.approve-plan`, `deliver.accept`. Each is preceded by a challenger
  pass, so the PM judges finished work. Three per ordinary change; nothing
  can be cut without losing the guarantee each one holds. `define.discuss`,
  `define.settled` and `define.confirm-exists` are PM steps but not gates:
  they steer, they do not approve.
- **Sorting** — `define.sort`, AI-owned: reads the architecture file,
  searches the tree, and routes a request. The PM overrules at the first PM
  step of the chosen path: `define.confirm-exists` (already exists),
  `define.discuss` (logic), the Foundation input step, or
  `deliver.approve-plan` answering "revise the logic" (a fix that is really
  a logic change).
- **Node set** — several nodes changed together in one Define pass and one
  delivery (a cross-cutting change).
- **Fix** — a request against delivered logic whose criteria are unchanged
  (a bug, a dependency or security patch). Skips Define; keeps every Deliver
  gate.
- **Proposed rule** — a change to the architecture file written in
  `foundation.propose-rule`. Not a rule until `deliver.commit`; discarded at
  `deliver.drop`.
- **Node id** — stable identifier of a node: its file stem, kebab-case,
  unique across the whole tree, never changed after first save
  **(convention)**. Placement is the folder the file sits in and can
  change; the id cannot. Tags use the id, so moving a node breaks nothing.
- **Node version** — the save `define.commit` made; identified by its commit
  **(convention)**.
- **Component** — one unit of code under one system, doing one job,
  reusable; tagged by every node it serves.
- **Reviewer** — the challenger pass of the step in question.
- **Decision** — anything finalised, on either side, where an alternative
  was rejected, written as one file in the decision log with its
  situation, decision and reasons ("Instead of …"), timestamp with offset,
  optional region (market) and effective date, category, who made it and
  at which step. A decision is never edited; a later one supersedes it,
  and the earlier one is brought forward to the PM before that happens.
  See `components/decision-log.md`.
- **Lane** — `small` (touches one existing node, adds no component, needs
  no rule): every gate kept, each challenge runs once, the plan is one
  paragraph. `full`: everything. Set by `define.sort`, held in the record.
- **Role** — Sorter, Writer, Planner, Builder, Verifier, Challenger; one
  per step, in `orchestration/roles.yaml`; each a fresh context reading
  only the step's inputs.
- **Labels** — every drawing marks ENTRY (first step), EXIT (every end and
  handoff; a handoff names where it goes), PM INPUT (a step with `input`)
  and OUTPUT (a step with `output`). `../map.yaml` names the system entry
  (`define.intake`) and exit (`deliver.done`).

## The loop

Every message from the PM enters at one door, `define.intake`, and a change
record is born there. `define.sort` routes it and writes why:

- a question, "show me the product", or a queue instruction →
  `define.answer` (from the written business side only) → `settled`: the
  PM confirms, or turns it into a request, which is re-sorted.
- already exists → `define.confirm-exists`: the PM sees the node and
  confirms (nothing built) or says it differs (→ `discuss` as a change).
- new logic, a change, or a node set → `define.discuss`, itself a PM
  decision that can redirect a wrongly sorted request (fix, exists,
  foundation, stop) → `write` → `challenge` → `approve` (criteria confirmed
  here; changed criteria go back through `challenge`; "stop" →
  `define.drop`) → `commit` → `to-deliver`.
- needs the foundation → `define.to-foundation` → `foundation`: a new
  product writes the architecture file, `foundation.check` challenges it
  (findings back to the PM; "not needed" returns to `discuss`; "stop" drops),
  then the glossary, save, and `foundation-only` decides whether the
  request was the foundation itself (done) or continues (`ready` →
  `define.discuss`). An existing product proposes a rule, `check-rule`
  challenges it, and `impact` hands it to Deliver.
- a fix (a bug whose violated criterion the AI can name, a dependency
  patch, or a refactor that keeps behaviour) → `define.to-fix` →
  `deliver.trace` directly.

Deliver: `trace` (affected code and reusable components) → `plan` (plan
section for the PM; AI section with task list and sources) →
`challenge-plan` → `approve-plan` (execute / revise the plan / revise the
logic / revise the rule / drop) → `execute` (task by task, ticked) →
`tasks-done` (a task that cannot be done as planned goes back to `plan`)
→ `verify` (whole suite; a criterion without a test is a finding) →
`passes` (at most three failed passes before it returns to `plan`) →
`accept` (use it, or judge the evidence; "not matching" goes back to
`plan`, not to the same tasks) → `commit` → `was-rule`: a request that
needed the rule continues at `define.discuss`; otherwise done. A dropped
rule also returns its request to `define.discuss` (`was-rule-drop`), where
the PM goes on within the current rules or stops.

One record, one status line, wherever the record is: Define's
`handed-over` end means the record continues in Foundation or Delivery;
there is no waiting copy.

Nothing reaches `execute` without a PM yes on a plan; nothing is saved
before the PM approves it; nothing is done that the PM has not seen work
or seen evidence for.

**One command per request.** `python3 framework/tools/run.py <record>`
(`/speckit-run`) walks the record from wherever it is: every AI step in a
fresh harness process, every handoff advanced, until a PM step, where it
prints the question and the `advance --answer` command and exits 3. For an
ordinary change the PM is stopped at `define.discuss` and then at the three
gates, `define.approve`, `deliver.approve-plan` and `deliver.accept`
(`define.intake` is answered when the record is started, before the first
run); after `accepted` the same command runs `commit → was-rule → done` and
exits 0. The runner checks every move against the record's history: a step
whose front matter was edited by hand, a harness that answered a PM step
itself, or one that ran on into the next step stops the run (exit 4).
See `orchestration/README.md`, "Layer 2: the runner".

## When in doubt (from the workflows)

Every AI-owned decision has a default for uncertainty, and it always
points towards more review, never less: `define.sort` picks the path with
more PM gates (build over question, logic over fix, foundation over logic)
and writes why; `foundation.new-or-change` treats doubt as a rule change,
never as a fresh file; `foundation.check` / `check-rule` report a doubtful
finding and let the PM accept it as is; `deliver.tasks-done` treats a
doubtful deviation as "not as planned" and returns to plan;
`deliver.passes` sends doubt back to plan, never towards "pass";
`deliver.was-rule` continues the request rather than closing it;
`define.answer` says "not written anywhere" rather than guessing.
"Non-trivial" is defined in each challenge step (touches an existing node
or existing code, or more than one criterion); a challenge that finds
nothing on non-trivial work is run again with one of the named framings.

## Rules that apply everywhere (from the workflows)

- The business side is edited before the code side. Edits to logic go
  through Define again, including challenge and PM approval.
- Nothing is invented. A node holds only what follows from the discussion;
  a plan describes only what the node and the tags justify; code is built
  from the current documentation of the tools the architecture names, not
  from memory, and the sources are recorded.
- Nothing is written twice. Trace searches existing components before
  anything new is planned; a duplicate component is a finding.
- Everything is saved with its history. That history is git, with no
  separate versioning scheme **(convention)**.
- A second, independent AI pass reviews the architecture file, the node,
  the plan and the delivered code before the PM sees each.
- Everything the PM reads is in plain language, with no code and no code
  words.
- A record moves only through `framework/tools/orchestrate.py advance`,
  along an edge in the YAML with its condition; the AI never picks the
  next step itself. Challenges after a revision read only the delta since
  their last pass.
- When the PM's answer says the draft stands ("no change", "the draft
  stands", "unchanged"), the Writer or Planner it returns to changes
  nothing: one line under the step heading that the draft is re-submitted
  unchanged, then `advance`. The runner puts this in the prompt.
- Every finalising step writes a decision where an alternative was
  rejected: `foundation.check` (accepted findings), `foundation.save`
  (rules with an alternative), `define.approve`, `deliver.approve-plan`
  (the plan; AI choices that add a dependency or a stored data shape),
  `deliver.accept`, `deliver.commit` (lessons), every `drop` (which also
  supersedes the record's own decisions). Before a gate, the AI searches
  the log by nodes, glossary terms and components, repeats the search on
  the final draft at the gate, and shows an altered decision to the PM
  side by side; it changes only on an explicit yes. Decisions written at
  `accept` and `commit` never supersede. `define.challenge` and
  `deliver.challenge-plan` report a draft or plan that alters a decision
  nobody brought forward. The decision index must validate before
  `deliver.commit`.

## Conventions

Choices this reference makes where the workflows are silent; marked
**(convention)** where used in `components/`.

- **Layout of a product repository:**

  ```
  architecture.md          the architecture file
  glossary.md              the glossary
  logic/                   the logic tree: one file per node, folders for nesting
  logic/INDEX.md           generated by framework/tools/logic_index.py: the KT overview
  decisions/               the decision log: decisions/D-<nnnn>-<slug>.md, one per decision that had an alternative (product, business, ui, frontend, backend, code, infra, software, process); decisions/INDEX.md generated and validated by framework/tools/decisions_index.py
  AGENTS.md, CLAUDE.md     the operating card (from framework/templates), exact commands filled in
  changes/                 one change record per request, born at intake: changes/<YYYY-MM-DD>-<n>-<slug>.md
  changes/QUEUE.md         the index: waiting requests in order, the one in flight, dependencies, PM-blocked count
  code/<system>/<component>/   components and their tests, per system named in the architecture file
  code/COMPONENTS.md       generated by framework/tools/components_index.py: component → system → nodes
  docs/                    optional: architecture.archify.json, and architecture.html / architecture.delta.{html,json} written by framework/tools/archify_delta.py (see components/architecture-file.md)
  framework/               a copy of this framework's framework/ folder (README, components, tools, templates), copied in when the product starts
  framework/workflows/     the workflow YAML, copied in with it: `cp -r workflow-studio/framework . && cp -r workflow-studio/workflows framework/` (orchestrate.py refuses to run without it)
  ```

  Everything except `code/` is the business side. Environment variables and
  secrets live where the architecture file says, never in logic files or
  change records.
- **Change record** — created at `define.intake` with the request as
  stated; its `status` line reads `<step> · waiting on PM|AI · <date>` and
  is updated at every step; each step's output (sort reason, discussion
  notes, findings, answers, task ticks, test results, failed-pass count) is
  written into it, so resume never depends on memory; the plan section and
  the AI section (task list, sources) are added at `deliver.plan`; the
  outcome (delivered with node versions / dropped / rule dropped / already
  exists / answered) at the end. A document (PRD) at intake becomes one
  record per request it contains, ordered by the PM. The file is
  `changes/<YYYY-MM-DD>-<n>-<slug>.md`; nodes are referenced inside the
  record, never in its name. The queue is committed whenever a record changes.
- **One change in flight per node.** A second request on the same node
  waits in the queue; a waiting request does not count as in flight. A
  record can name a record it depends on; if that one is dropped, the
  dependant returns to waiting. When a node is delivered, waiting records
  on it are re-sorted (a bug against the old version may be gone). The
  queue shows how many records wait on the PM and since when; the AI may
  add at most one request of its own while the PM is away.
- **Every step writes its output to disk before the next step starts.**
  Resume after any interruption: read the queue and the record's status
  line, redo only the current step from its last saved output. For a PM
  step (discuss, a gate) the saved output is the notes or the answer in
  the record; if the interruption came before the PM answered, the step is
  simply asked again.
- **Node status** — a `Status:` line in the node file: `approved, not yet
  delivered` (set at `define.commit`), `delivered <version>` (set at
  `deliver.commit`), or `retired <date>`. Children of a retired parent are
  retired with it; `logic/INDEX.md` shows the status so nobody mistakes
  approved for built.
- **Commits** — record and queue updates are committed as they happen;
  "one commit" at `deliver.commit` means one *code* commit that also
  carries the completed record.
- **Challenger pass** runs in a fresh context given only the inputs listed
  for that step, never the conversation that produced the work.
- **Drafts** (a node before `define.approve`, a plan before
  `deliver.approve-plan`, a proposed rule before `deliver.commit`) exist
  uncommitted in the working copy.
- **Set-aside code** (`deliver.back-to-define`, `deliver.back-to-foundation`,
  `deliver.passes → plan`) is kept on a branch named for the change record
  and never merged unless a fresh plan is approved; discarded at `drop`.
- **Stopping.** The PM may stop a change at any point: in Define at
  `discuss` or `approve`; in Foundation at any input step ("stop" →
  `foundation.drop`); in Deliver at `approve-plan`, during execution (taken
  at the next task boundary → `tasks-done` → `drop`) or at `accept`.
  Foundation findings the PM disagrees with are marked "accepted as is"
  and not reported again.
- **Retired nodes** stay in the tree marked retired with the date; children
  of a retired parent are retired with it; code tagged by more than one
  node is removed only when every tag is retired.
- **Large rule changes** (replacing a technology) may be split into
  several change records; the rule is written with the first, annotated
  with the nodes still to be brought under it. At `was-rule`, "the request
  still needs logic" is answered no while the annotation is not empty, so
  the request resumes only after the last record.
- **Failed-pass count** in the record is reset whenever the record returns
  to `plan`, from `passes`, `tasks-done` or `accept`.
