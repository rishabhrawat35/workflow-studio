# Execution plan: large requests, removals and breaking changes

Stateful checklist for `PLAN.md`. Each phase is executed by a fresh agent with only this file, `PLAN.md` and the repository; the agent ticks its boxes here, pastes the proof command and its output under the phase, and stops. The next phase does not start until the previous phase's proof is green and its tick is written. A phase that fails is fixed within that phase; nothing in a later phase is touched early. The existing engine must pass `python3 tools/check_all.py` at the end of every phase, on Python 3.9 syntax (`ast.parse(feature_version=(3,9))` over `framework/tools/*.py` and `tools/*.py`).

Rollback rule: every phase edits only the files in its scope. If a phase cannot reach green in two attempts, its edits are reverted (`git checkout -- <files>`), the reason is written under the phase, and execution stops for the owner.

State legend: `[ ]` not started · `[~]` in progress · `[x]` done and proven · `[!]` failed, reverted.

## Phase 0 — Baseline (no edits)

- [x] Paste here: `check_all.py` tail, `orchestrate.py check` line, `validate.py` line, `wc -l workflows/define.yaml framework/tools/orchestrate.py framework/tools/run.py`.
- [x] Copy `workflows/define.yaml` to this folder as `define.before.yaml`.

Proof (2026-09-11, before any edit):

```
$ python3 tools/check_all.py | tail -15
   claude: .claude/skills/
   installed 22 file(s); invoke as /speckit-<name> (Gemini: /speckit.<name>)
   CLOSED — 51 steps, every one mapped to a role and mode; 21 commands, every one entering a real non-routing step; 1 meta command entering the record's current step; toolbox: 3 step row(s)

   Next:
     1. Complete architecture.md (or answer /speckit-constitution in your AI tool).
     2. Open your AI tool in /tmp/workflow-studio-newproduct-vdcq_sth/p and type: /speckit-specify <what the product should do, in your words>
     3. Or from a terminal: python3 framework/tools/orchestrate.py start changes/<date>-1-<slug>.md --command speckit.specify
== new_product: refuses a non-empty folder
   refused: /tmp/workflow-studio-newproduct-vdcq_sth/p exists and is not empty
== optional: archify_delta (skipped: archify CLI not installed on this machine)
== optional: archify_delta refuses without the CLI
   refused: archify CLI not found; install with: python3 framework/tools/archify_delta.py install   (or: npx skills add tt-a1i/archify -g)

ALL CHECKS PASSED

$ python3 framework/tools/orchestrate.py check
CLOSED — 51 steps, every one mapped to a role and mode; 21 commands, every one entering a real non-routing step; 1 meta command entering the record's current step; toolbox: 3 step row(s)

$ python3 tools/validate.py
OK — 3 workflow(s), map consistent

$ wc -l workflows/define.yaml framework/tools/orchestrate.py framework/tools/run.py
  304 workflows/define.yaml
  531 framework/tools/orchestrate.py
  632 framework/tools/run.py
 1467 total

$ cp workflows/define.yaml docs/plans/2026-09-11-breakdown/define.before.yaml
```

## Phase 1 — Workflow YAML and roles

Scope: `workflows/define.yaml`, `workflows/foundation.yaml` (only `check-rule` notes, E17), `framework/orchestration/roles.yaml`, `SCHEMA.md` (expected: no new field).

- [x] `discuss`: exits `breakdown`, `impact`, `revise-breakdown` (condition text names "a child record").
- [x] New steps with `what`/`output`/`notes` from PLAN §3.1–3.4: `breakdown`, `confirm-breakdown` (PM, `input`), `spawn`, `broken-down` (end), `revise-breakdown`, `impact`, `confirm-impact` (PM, `input`). Doubt rules from §3.2 in the notes of `breakdown` and `impact`; the round cap in both gates' notes.
- [x] `sort`: `what` gains the two flags (large, breaking) in the sort reason. `write`: `what` says it drafts the node set from the impact answer when one exists.
- [x] `foundation.check-rule`: notes gain the impact section for a rule removal (E17).
- [x] `roles.yaml`: rows for the seven new steps (modes pm/agent as in §3.1).
- [x] Proof: `validate.py` OK; `check` CLOSED, 58 steps; `build.py`; Define view screenshot in this folder with no overlaps or hidden nodes; `check_all.py` green (small-request path untouched).

Files edited: `workflows/define.yaml` (304 → 505 lines), `workflows/foundation.yaml` (`check-rule` notes only), `framework/orchestration/roles.yaml` (seven rows). `SCHEMA.md` untouched: no new field was needed. New steps are placed after `discuss` and before `write` in the file, in the order breakdown, confirm-breakdown, spawn, broken-down, revise-breakdown, impact, confirm-impact. The new `when:` strings are quoted. `write` stays the first exit of `discuss` and `commit` the third exit of `approve`, so the runner test in `check_all.py` (`--when 1`, `--when 3`) drives the same small-request path as before.

Roles added (mode, role): `define.breakdown` agent/Writer · `define.confirm-breakdown` pm/Writer · `define.spawn` agent/Sorter · `define.broken-down` auto/Sorter · `define.revise-breakdown` agent/Sorter · `define.impact` agent/Writer · `define.confirm-impact` pm/Writer. `define.write` inputs gain `impact-answer`.

Proof (2026-09-11):

```
$ python3 tools/validate.py
OK — 3 workflow(s), map consistent

$ python3 framework/tools/orchestrate.py check
CLOSED — 58 steps, every one mapped to a role and mode; 21 commands, every one entering a real non-routing step; 1 meta command entering the record's current step; toolbox: 3 step row(s)

$ python3 tools/build.py
OK — 3 workflow(s), map consistent
built studio.html and build/studio.artifact.html with 3 workflow(s)
wrote framework/steps.md (58 steps)

$ python3 -c "import ast,glob; [ast.parse(open(f).read(),f,feature_version=(3,9)) for f in glob.glob('framework/tools/*.py')+glob.glob('tools/*.py')]; print('py39 syntax OK')"
py39 syntax OK

$ python3 tools/check_all.py | tail -5      (exit 0; the orchestrate-check line inside it reads "CLOSED — 58 steps, …")
== optional: archify_delta (skipped: archify CLI not installed on this machine)
== optional: archify_delta refuses without the CLI
   refused: archify CLI not found; install with: python3 framework/tools/archify_delta.py install   (or: npx skills add tt-a1i/archify -g)

ALL CHECKS PASSED
```

Screenshot: `define-phase1.png` (Playwright, chromium, 1440×900 at 2× scale, the "Define business logic" nav entry clicked; the sidebar reads "25 steps · PM"). Reviewed: all 25 nodes are drawn (intake, sort, answer, settled, answered, confirm-exists, exists, to-foundation, to-fix, discuss, impact, revise-breakdown, confirm-impact, breakdown, confirm-breakdown, write, spawn, challenge, approve, commit, drop, to-deliver, broken-down, handed-over, dropped); `confirm-breakdown` and `confirm-impact` carry the PM INPUT badge; `broken-down` carries EXIT and is listed under Exits; no node overlaps another and no edge label sits on top of another (the stacked labels at the left and right margins — "settled" / "PM stops the request", "PM wants changes to the logic" / "merge, split, reorder or drop chunks; rewr…" — are on separate lines, checked at 2× zoom). No YAML reordering was needed.

## Phase 2 — Orchestrator: parent, children, waiting, impact

Scope: `framework/tools/orchestrate.py` only.

- [x] Front-matter fields `parent`, `chunk`, `depends_on` read and preserved; `start` refuses a record with `parent` (E10).
- [x] Parser for `## Breakdown — PM answer` (§3.3) and `## Impact — PM answer` (§3.4); zero chunks or unparseable answer → refusal naming the block.
- [x] `advance` out of `spawn`: creates child files in confirmed order; chunk 1 at `define.discuss`, others `waiting` with `waiting_on: chunk <n>`; lane per E12; refuses E5 and E6; writes the decision file; slug collision with an existing record → refusal.
- [x] Waiting child: `next` prints the wait; `advance` refused until the dependency is at `deliver.done`; a dropped dependency moves the wait to the next chunk or releases the child (E3).
- [x] `revise-breakdown`: child `waiting_on: parent`; parent reopened at `confirm-breakdown` with a new proposed block; refused for a chunk already delivered.
- [x] Round caps: `breakdown → confirm-breakdown` and `impact → confirm-impact` at most three times, then only `write`/`drop` legal.
- [x] `impact` and `breakdown` refused with no `architecture.md` (E6); `impact` refused while a named dependant's record is in Deliver (E18).
- [x] `check`/`next` on a child with a missing parent or a parent without the PM-answer block refuse, naming the file (E11).
- [x] `next --json` carries `parent`, `chunk`, `depends_on`, `group`.
- [x] Proof: scratch product from `new_product.py`; a parent walked by hand through spawn; three child files with correct front matter; each refusal reproduced with its exact message pasted; `check_all.py` green.

Files edited: `framework/tools/orchestrate.py` (531 → 1155 lines; Python 3.9: `from __future__ import annotations`, no `match`, no runtime `X | Y`). `run.py`, `fake_harness.py`, the YAML and the docs untouched; `check_all.py` step 7 (the small-request runner path) passes unchanged.

How it is built (the design notes, as implemented):

- The confirmed breakdown is the last `## Breakdown — proposed` block as confirmed by the last `## Breakdown — PM answer` block, which must come after it and be a yes (`yes`, `y`, `ok`, `confirm`, `confirmed`, `agreed`, or the gate's own condition "yes, these chunks in this order"). Anything else is refused at the gate with `--to spawn` and is recorded with `--to breakdown`, where the AI rewrites and appends a new proposed block; a yes is refused with `--to breakdown`. So `spawn` only ever consumes a proposal and a yes. The PM's `--answer` at `confirm-breakdown` / `confirm-impact` is appended verbatim to the record body as `## Breakdown — PM answer <date>` / `## Impact — PM answer <date>` (the history keeps it too, as before).
- Parser (`parse_breakdown`): chunk lines `  <n>. <slug> — <text>`, then `depends on:` and `why this line:`; `Order and reasons:`, `Not split further because:`, `Alternatives considered:` (split on `;`) at the top level. `depends on: chunk 2, chunk 3` gives the chunk dependencies; `delivered node <id>` and backticked `` `<id>` `` in the chunk text give the nodes a chunk touches (E5). A chunk with no explicit chunk dependency depends on the previous chunk, so every chunk but the first waits on something. Leaving `define.breakdown` needs the block with at least one chunk; leaving `define.impact` needs `## Impact — proposed` with at least one numbered dependant (E15 is named in the refusal). At `confirm-impact`, `--to write` and `--to breakdown` need the answer to name every dependant listed in the proposed block.
- Child files: `changes/<parent-date>-<parent-n>.<chunk>-<slug>.md`; refused when the slug is the slug of any existing record (request or child of another group). Front matter: `parent` (relative path), `chunk` (int), `depends_on` (list of child paths), `lane` (E12 heuristic: "component" or "new system" in the chunk text, or more than one node → full; else small), the normal state fields, `command` copied from the parent. Chunk 1 at `define.discuss`; the others at the pseudo-step `waiting` (`step: waiting`, `mode: waiting`, `waiting_on: chunk <n>`, the first unmet dependency). `waiting` is not a YAML step: `check` never sees it; `read_record`, `next` and `advance` handle it. A waiting child has one exit, `advance --to define.discuss`, refused until every dependency is at `deliver.done`, `deliver.dropped` or `define.dropped`; when the first blocking dependency changes, the refusal also moves `waiting_on` to the next one (E3) and rewrites the group block.
- Group block: `changes/QUEUE.md` gains a section fenced by `<!-- group: <parent> -->` … `<!-- /group -->` (`## Group: <parent title>`, the parent's step, the chunk table n / file / step / waiting on, "n of m delivered; k dropped; in flight: …", "group closed" when every chunk is done or dropped). Written at spawn and rewritten on every `advance` of a child (including the release and the drop). Phase 3 documents it.
- Decision file: `decisions/D-<nnnn>-breakdown-<parent-slug>.md`, `made_by: PM`, `at_step: define.confirm-breakdown`, `category: product`, `record:` the parent, `nodes:` the chunk slugs; `## Decision` lists the confirmed chunks with their record files; `## Reasons` has one "Instead of …" line per alternative considered (fallback: "one node for the whole request"). A re-spawn writes a new decision with `supersedes:` and adds `superseded_by:` to the earlier one; `decisions_index.py` validates both.
- `revise-breakdown` (E4): from a child at `define.discuss`, `advance --to revise-breakdown --when 4`; refused on a record without `parent`, and on a delivered chunk (`deliver.done`). The child moves to `define.revise-breakdown` with `waiting_on: parent`; the parent's step is set back to `define.confirm-breakdown` (history edge "revise-breakdown from chunk n") with a new `## Breakdown — proposed <date>` block copied from the child's `## define.discuss` section (else its last section), followed by `## Breakdown — previous chunks (for the PM's comparison)`. On the PM's yes, `spawn` reconciles: existing children are matched by slug and keep their files and history (chunk number, dependencies and state rewritten, unless delivered or dropped), new chunks get new files, chunks no longer listed are moved to `define.dropped` with the reason.
- Caps: `gate_rounds` counts `define.breakdown → define.confirm-breakdown` (and `define.impact → define.confirm-impact`) edges in the record's history; at three, only `write` or `drop` are legal from the gate.
- E6: `--to breakdown` and `--to impact` (from any step) are refused while `architecture.md` is missing. E18: `--to impact` is refused when any record under `changes/` whose step starts with `deliver.` and is not done/dropped has a front-matter `nodes:` list sharing an id with this record's `nodes:`; the heuristic is stated in the refusal text.
- E11: `next`, `advance` and `check <child>` (the `check` subcommand gained an optional record argument) refuse when the parent file is missing or has no `## Breakdown — PM answer` block, naming both files.
- `next --json` adds `parent`, `chunk`, `depends_on` and `group` (title, parent step, chunks with step and waiting-on, delivered, dropped, total, in flight); a waiting child's JSON has `mode: waiting`, a `wait` sentence, `blocked_by`, and the single release exit. `run.py` is untouched (Phase 4 makes the waiting child exit 3).

Proof (2026-09-11; scratch product under the session scratchpad `p2/p`, built with `tools/new_product.py … --agent claude --no-git`; the script `p2/proof.sh` produced this log; each `[exit n]` is the command's exit code):

```
CLOSED — 58 steps, every one mapped to a role and mode; 21 commands, every one entering a real non-routing step; 1 meta command entering the record's current step; toolbox: 3 step row(s)

### 1. parent: start → intake answer → sort→discuss → discuss→breakdown
$ python3 framework/tools/orchestrate.py start changes/2026-09-11-1-habit-tracker.md --command speckit.specify
started at define.intake via speckit.specify
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1-habit-tracker.md --to sort --answer a habit tracker: log a habit, see a weekly streak, get a reminder
define.intake → define.sort
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1-habit-tracker.md --to discuss --when 3
define.sort → define.discuss  (when: new logic, a change to an existing node, or a cross-cutting change to several nodes)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1-habit-tracker.md --to breakdown --when 2 --answer three capabilities, propose the chunks
define.discuss → define.breakdown  (when: several capabilities; propose the chunks)

### 2. zero-chunk refusals at define.breakdown
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1-habit-tracker.md --to confirm-breakdown
refused: write the block `## Breakdown — proposed <date>` into changes/2026-09-11-1-habit-tracker.md before leaving define.breakdown (chunks as `  1. <slug> — <capability>`, each with `depends on:` and `why this line:`)
  [exit 1]
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1-habit-tracker.md --to confirm-breakdown
refused: the block `## Breakdown — proposed 2026-09-11` in changes/2026-09-11-1-habit-tracker.md lists no chunks; expected numbered lines `  1. <slug> — <capability>` with `depends on:` and `why this line:` under each
  [exit 1]
(the §3.3 block with three chunks written into the parent; chunk 3 depends on chunk 1)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1-habit-tracker.md --to confirm-breakdown
define.breakdown → define.confirm-breakdown

### 3. the gate: a non-yes cannot spawn; a yes cannot go back to breakdown
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1-habit-tracker.md --to spawn --when 1 --answer merge 2 and 3
refused: the PM's answer 'merge 2 and 3' is not a yes; spawn consumes only a proposal and a yes — record it with --to breakdown (the AI rewrites the proposal from those words), --to write (one thing) or --to drop
  [exit 1]
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1-habit-tracker.md --to breakdown --when 2 --answer yes
refused: the PM's answer is a yes; a yes goes to spawn (--to spawn --when 1), not back to breakdown
  [exit 1]
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1-habit-tracker.md --to spawn --when 1 --answer yes
define.confirm-breakdown → define.spawn  (when: yes, these chunks in this order)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1-habit-tracker.md --to broken-down
define.spawn → define.broken-down
  child 1: changes/2026-09-11-1.1-log-habit.md  step: define.discuss  waiting on: PM  lane: small  depends on: nothing
  child 2: changes/2026-09-11-1.2-weekly-streak.md  step: waiting  waiting on: chunk 1  lane: small  depends on: changes/2026-09-11-1.1-log-habit.md
  child 3: changes/2026-09-11-1.3-reminder.md  step: waiting  waiting on: chunk 1  lane: full  depends on: changes/2026-09-11-1.1-log-habit.md
  decision: decisions/D-0001-breakdown-habit-tracker.md   group block: changes/QUEUE.md
step:     define.broken-down — Broken down; the chunks continue as their own records

### 4. the three child files' front matter
-- changes/2026-09-11-1.1-log-habit.md
command: speckit.specify
parent: changes/2026-09-11-1-habit-tracker.md
chunk: 1
depends_on: []
step: define.discuss
mode: pm
role: Writer
waiting_on: PM
since: 2026-09-11T14:00+00:00
lane: small
failed_passes: 0
rerun_count: 0
-- changes/2026-09-11-1.2-weekly-streak.md
command: speckit.specify
parent: changes/2026-09-11-1-habit-tracker.md
chunk: 2
depends_on:
- changes/2026-09-11-1.1-log-habit.md
step: waiting
mode: waiting
role: Sorter
waiting_on: chunk 1
since: 2026-09-11T14:00+00:00
lane: small
failed_passes: 0
rerun_count: 0
-- changes/2026-09-11-1.3-reminder.md
command: speckit.specify
parent: changes/2026-09-11-1-habit-tracker.md
chunk: 3
depends_on:
- changes/2026-09-11-1.1-log-habit.md
step: waiting
mode: waiting
role: Sorter
waiting_on: chunk 1
since: 2026-09-11T14:00+00:00
lane: full
failed_passes: 0
rerun_count: 0
-- changes/QUEUE.md
# Queue

No records yet.

<!-- group: changes/2026-09-11-1-habit-tracker.md -->
## Group: Habit tracker

Parent: changes/2026-09-11-1-habit-tracker.md (define.broken-down)

| n | file | step | waiting on |
|---|---|---|---|
| 1 | changes/2026-09-11-1.1-log-habit.md | define.discuss | PM |
| 2 | changes/2026-09-11-1.2-weekly-streak.md | waiting | chunk 1 |
| 3 | changes/2026-09-11-1.3-reminder.md | waiting | chunk 1 |

0 of 3 delivered; in flight: chunk 1
<!-- /group -->
-- decisions/D-0001-breakdown-habit-tracker.md
---
made_at: "2026-09-11T14:00+00:00"
category: product
made_by: PM
at_step: define.confirm-breakdown
record: changes/2026-09-11-1-habit-tracker.md
nodes: [log-habit, weekly-streak, reminder]
---
# Breakdown of Habit tracker: 3 chunks in the confirmed order

## Situation

The request in changes/2026-09-11-1-habit-tracker.md named several capabilities. At define.confirm-breakdown the PM read the proposed chunks, their dependencies, the order and the alternatives, and answered: yes

## Decision

1. log-habit — a member logs a habit for today, one tap per habit (depends on: none; record changes/2026-09-11-1.1-log-habit.md)
2. weekly-streak — a member sees the streak for each habit over the last seven days (depends on: none; record changes/2026-09-11-1.2-weekly-streak.md)
3. reminder — a member gets a reminder at a chosen time for each habit; a new notification component (depends on: chunk 1; record changes/2026-09-11-1.3-reminder.md)

Order and reasons: 1 first because both others read it; 2 before 3 because the streak de-risks the read model the reminder also uses

## Reasons

Not split further because: each chunk is one capability a user sees on its own
- Instead of one node for the whole tracker, the request is built as these 3 chunks.
- Instead of a finer split with the habit list as its own chunk, the request is built as these 3 chunks.
- Instead of reminders first, the request is built as these 3 chunks.
$ python3 framework/tools/decisions_index.py
wrote decisions/INDEX.md (1 decisions, 0 finding(s))
  [exit 0]

### 5. waiting child: next (E9), advance refused, next --json fields, start by hand (E10)
$ python3 framework/tools/orchestrate.py next changes/2026-09-11-1.2-weekly-streak.md
step:     waiting — chunk 2 of changes/2026-09-11-1-habit-tracker.md
mode:     waiting   role: Sorter   lane: small   waiting on: chunk 1 since 2026-09-11T14:00+00:00
waits for: chunk 1 (changes/2026-09-11-1.1-log-habit.md at define.discuss) to reach deliver.done
depends on: changes/2026-09-11-1.1-log-habit.md
exits:
  1. → define.discuss   when: every dependency at deliver.done (or dropped); `advance --to define.discuss` releases it
  [exit 0]
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1.2-weekly-streak.md --to define.discuss
refused: chunk 2 waits on chunk 1 (changes/2026-09-11-1.1-log-habit.md is at define.discuss, not deliver.done)
  [exit 1]
$ python3 framework/tools/orchestrate.py next changes/2026-09-11-1.3-reminder.md --json   (parent, chunk, depends_on, group, wait)
{"step": "waiting", "mode": "waiting", "wait": "chunk 1 (changes/2026-09-11-1.1-log-habit.md at define.discuss) to reach deliver.done", "parent": "changes/2026-09-11-1-habit-tracker.md", "chunk": 3, "depends_on": ["changes/2026-09-11-1.1-log-habit.md"], "group": {"title": "Habit tracker", "delivered": 0, "total": 3, "in_flight": [1], "chunks": [[1, "define.discuss", "PM"], [2, "waiting", "chunk 1"], [3, "waiting", "chunk 1"]]}}
$ python3 framework/tools/orchestrate.py start changes/2026-09-11-1.2-weekly-streak.md --command speckit.specify
refused: changes/2026-09-11-1.2-weekly-streak.md carries `parent: changes/2026-09-11-1-habit-tracker.md`; children are created by define.spawn; run the parent (E10)
  [exit 1]

### 6. E3: chunk 1 dropped at its own gate; chunk 3 (depends on 1) is released; chunk 2 released
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1.1-log-habit.md --to drop --when 8 --answer stop, we already have a log elsewhere
define.discuss → define.drop  (when: PM stops the request)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1.1-log-habit.md --to dropped
define.drop → define.dropped
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1.3-reminder.md --to discuss
waiting → define.discuss  (released: every dependency at deliver.done or dropped)
step:     define.discuss — Discuss the capability
mode:     pm   role: Writer   lane: full   waiting on: PM since 2026-09-11T14:00+00:00
chunk:    3 of changes/2026-09-11-1-habit-tracker.md   depends on: changes/2026-09-11-1.1-log-habit.md
inputs:   record, architecture, glossary, nodes-touched, sort-reason
PM gives: What the product must do, for whom, where it sits in the tree, what must be true to call it working; for a cross-cutting change, which nodes it touches. Or a correction of the sorting: it is a fix, it already exists, it needs the foundation, or stop.  → record it with `advance --answer`
does:     PM and the AI talk it through (a page or capability, then its sub-flows, e.g. login page > logout, forgot password). Inputs: the architecture file, the glossary, and for a change the current node(s). The discussion is where the PM redirects a wrongly sorted request. When the sort reason flagged the request as large, the discussion ends with a proposed breakdown; when it flagged it as breaking, with the repercussions shown before anything is written. A small request never sees either.
produces: Discussion notes appended to the record
exits:
  1. → define.write   when: it is business logic; write it
  2. → define.breakdown   when: several capabilities; propose the chunks
  3. → define.impact   when: this removes or changes something others depend on; show the repercussions
  4. → define.revise-breakdown   when: on a child record, building this chunk showed the split or the order is wrong
  5. → define.to-fix   when: the logic is unchanged; it is a fix
  6. → define.confirm-exists   when: it already exists
  7. → define.to-foundation   when: it needs the foundation first
  8. → define.drop   when: PM stops the request
last edges:
  define.spawn → waiting
  waiting → define.discuss  (released: every dependency at deliver.done or dropped)
  [exit 0]
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1.2-weekly-streak.md --to discuss
waiting → define.discuss  (released: every dependency at deliver.done or dropped)
<!-- group: changes/2026-09-11-1-habit-tracker.md -->
## Group: Habit tracker

Parent: changes/2026-09-11-1-habit-tracker.md (define.broken-down)

| n | file | step | waiting on |
|---|---|---|---|
| 2 | changes/2026-09-11-1.2-weekly-streak.md | define.discuss | PM |
| 3 | changes/2026-09-11-1.3-reminder.md | define.discuss | PM |
| 1 | changes/2026-09-11-1.1-log-habit.md | define.dropped | nobody |

0 of 3 delivered; 1 dropped; in flight: chunk 2, chunk 3
<!-- /group -->

### 7. revise from a delivered chunk (chunk 3 put at deliver.done by hand for the proof)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1.3-reminder.md --to revise-breakdown --when 4
refused: chunk 3 of changes/2026-09-11-1-habit-tracker.md is already delivered (deliver.done); a delivered chunk is never revised — revise the breakdown from a chunk still in Define
  [exit 1]

### 8. E11: parent missing; parent without the PM-answer block; check on a healthy child
$ python3 framework/tools/orchestrate.py next changes/2026-09-11-1.2-weekly-streak.md
refused: changes/2026-09-11-1.2-weekly-streak.md is chunk 2 of changes/2026-09-11-1-habit-tracker.md, which does not exist (E11); restore the parent file (it was moved or deleted by hand)
  [exit 1]
$ python3 framework/tools/orchestrate.py check changes/2026-09-11-1.2-weekly-streak.md
refused: changes/2026-09-11-1.2-weekly-streak.md is chunk 2 of changes/2026-09-11-1-habit-tracker.md, which does not exist (E11); restore the parent file (it was moved or deleted by hand)
  [exit 1]
$ python3 framework/tools/orchestrate.py next changes/2026-09-11-1.2-weekly-streak.md
refused: parent changes/2026-09-11-1-habit-tracker.md of changes/2026-09-11-1.2-weekly-streak.md has no `## Breakdown — PM answer` block (E11); the parent was edited by hand — restore the block the PM answered at define.confirm-breakdown
  [exit 1]
$ python3 framework/tools/orchestrate.py check changes/2026-09-11-1.2-weekly-streak.md
CLOSED — 58 steps, every one mapped to a role and mode; 21 commands, every one entering a real non-routing step; 1 meta command entering the record's current step; toolbox: 3 step row(s); changes/2026-09-11-1.2-weekly-streak.md is chunk 2 of changes/2026-09-11-1-habit-tracker.md (parent and PM answer present)
  [exit 0]

### 9. E4: revise-breakdown from chunk 2 at define.discuss; PM confirms; spawn reconciles (files and history kept)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1.2-weekly-streak.md --to revise-breakdown --when 4 --answer '…'
define.discuss → define.revise-breakdown  (when: on a child record, building this chunk showed the split or the order is wrong)
  parent changes/2026-09-11-1-habit-tracker.md reopened at define.confirm-breakdown with a new `## Breakdown — proposed` block; this chunk waits on parent
-- child:
step: define.revise-breakdown
waiting_on: parent
-- parent:
step: define.confirm-breakdown
waiting_on: PM
50:## Breakdown — proposed 2026-09-11
66:## Breakdown — PM answer 2026-09-11
70:## Breakdown — proposed 2026-09-11
87:## Breakdown — previous chunks (for the PM's comparison)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1-habit-tracker.md --to spawn --when 1 --answer yes
define.confirm-breakdown → define.spawn  (when: yes, these chunks in this order)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1.2-weekly-streak.md --to handed-over
define.revise-breakdown → define.handed-over
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1-habit-tracker.md --to broken-down
define.spawn → define.broken-down
  child 1: changes/2026-09-11-1.2-weekly-streak.md  step: define.discuss  waiting on: PM  lane: small  depends on: nothing
  child 2: changes/2026-09-11-1.3-reminder.md  step: waiting  waiting on: chunk 1  lane: full  depends on: changes/2026-09-11-1.2-weekly-streak.md
  decision: decisions/D-0002-breakdown-habit-tracker.md   group block: changes/QUEUE.md
<!-- group: changes/2026-09-11-1-habit-tracker.md -->
## Group: Habit tracker

Parent: changes/2026-09-11-1-habit-tracker.md (define.broken-down)

| n | file | step | waiting on |
|---|---|---|---|
| 1 | changes/2026-09-11-1.2-weekly-streak.md | define.discuss | PM |
| 2 | changes/2026-09-11-1.3-reminder.md | waiting | chunk 1 |
| 1 | changes/2026-09-11-1.1-log-habit.md | define.dropped | nobody |

0 of 3 delivered; 1 dropped; in flight: chunk 1
<!-- /group -->
decisions/D-0001-breakdown-habit-tracker.md:superseded_by: D-0002
decisions/D-0002-breakdown-habit-tracker.md:supersedes: D-0001
$ python3 framework/tools/decisions_index.py
wrote decisions/INDEX.md (2 decisions, 0 finding(s))
  [exit 0]

### 10. E5, slug collision, the wait moving to the next chunk, E6, E18, the cap after three rounds (fresh parents)
$ python3 framework/tools/orchestrate.py start changes/2026-09-11-2-accounts.md --command speckit.specify
started at define.intake via speckit.specify
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-2-accounts.md --to sort --answer accounts: sign up, log in, reset the password
define.intake → define.sort
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-2-accounts.md --to discuss --when 3
define.sort → define.discuss  (when: new logic, a change to an existing node, or a cross-cutting change to several nodes)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-2-accounts.md --to breakdown --when 2 --answer propose the chunks
define.discuss → define.breakdown  (when: several capabilities; propose the chunks)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-2-accounts.md --to confirm-breakdown
define.breakdown → define.confirm-breakdown
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-2-accounts.md --to spawn --when 1 --answer yes
define.confirm-breakdown → define.spawn  (when: yes, these chunks in this order)
(E5: chunks 2 and 3 both touch node login with no dependency between them)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-2-accounts.md --to broken-down
refused: chunks 2 (log-in) and 3 (reset-password) both touch node login with no dependency between them (E5); add `depends on: chunk 2` to chunk 3 (a node is named as `delivered node <id>` or as `<id>` in backticks)
  [exit 1]
(slug collision: chunk 2 is now 'reminder', the slug of changes/2026-09-11-1.3-reminder.md in the first group)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-2-accounts.md --to broken-down
refused: chunk 2 (reminder) collides with the existing record changes/2026-09-11-1.3-reminder.md (same slug); choose another slug for the chunk
  [exit 1]
(fixed: 1. sign-up; 2. log-in depends on chunk 1; 3. reset-password depends on chunk 1, chunk 2)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-2-accounts.md --to broken-down
define.spawn → define.broken-down
  child 1: changes/2026-09-11-2.1-sign-up.md  step: define.discuss  waiting on: PM  lane: small  depends on: nothing
  child 2: changes/2026-09-11-2.2-log-in.md  step: waiting  waiting on: chunk 1  lane: small  depends on: changes/2026-09-11-2.1-sign-up.md
  child 3: changes/2026-09-11-2.3-reset-password.md  step: waiting  waiting on: chunk 1  lane: small  depends on: changes/2026-09-11-2.1-sign-up.md, changes/2026-09-11-2.2-log-in.md
  decision: decisions/D-0003-breakdown-accounts.md   group block: changes/QUEUE.md
(E3, the wait moves: chunk 1 dropped; chunk 3 depends on chunks 1 and 2, so its wait moves to chunk 2)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-2.1-sign-up.md --to drop --when 8 --answer stop
define.discuss → define.drop  (when: PM stops the request)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-2.1-sign-up.md --to dropped
define.drop → define.dropped
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-2.3-reset-password.md --to discuss
wait moved: chunk 1 → chunk 2
refused: chunk 3 waits on chunk 2 (changes/2026-09-11-2.2-log-in.md is at waiting, not deliver.done)
  [exit 1]
waiting_on: chunk 2
(E6: architecture.md removed)
$ python3 framework/tools/orchestrate.py start changes/2026-09-11-3-remove-reminders.md --command speckit.specify
started at define.intake via speckit.specify
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-3-remove-reminders.md --to sort --answer remove reminders
define.intake → define.sort
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-3-remove-reminders.md --to discuss --when 3
define.sort → define.discuss  (when: new logic, a change to an existing node, or a cross-cutting change to several nodes)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-3-remove-reminders.md --to impact --when 3 --answer show the repercussions
refused: impact needs architecture.md, which does not exist (E6); sort the request to to-foundation first, and propose the impact when Foundation has returned to define.discuss
  [exit 1]
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-3-remove-reminders.md --to breakdown --when 2 --answer propose the chunks
refused: breakdown needs architecture.md, which does not exist (E6); sort the request to to-foundation first, and propose the breakdown when Foundation has returned to define.discuss
  [exit 1]
(E18: a record mid-Deliver on node reminder; this request names reminder in its nodes:)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-3-remove-reminders.md --to impact --when 3 --answer show the repercussions
refused: changes/2026-09-10-9-build-reminders.md is in Deliver (deliver.execute) on node reminder, which this request names in its front matter `nodes:` (E18); one change in flight per node — the impact is shown once that record reaches deliver.done or is dropped (heuristic: the two records' `nodes:` lists share an id; a record without `nodes:` is not compared)
  [exit 1]
(the impact block, §3.4, and the PM answer parsed against its dependants)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-3-remove-reminders.md --to impact --when 3 --answer show the repercussions
define.discuss → define.impact  (when: this removes or changes something others depend on; show the repercussions)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-3-remove-reminders.md --to confirm-impact
refused: write the block `## Impact — proposed <date>` into changes/2026-09-11-3-remove-reminders.md before leaving define.impact (dependants as numbered lines `  1. <node id> [source]`)
  [exit 1]
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-3-remove-reminders.md --to confirm-impact
define.impact → define.confirm-impact
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-3-remove-reminders.md --to write --when 1 --answer weekly-streak: keep it by removing the button; reminder_schedule: keep
refused: the PM's answer names no choice for dependant 'notification-settings' listed in `## Impact — proposed 2026-09-11` of changes/2026-09-11-3-remove-reminders.md; one line per dependant (retire it too | keep it by … | narrow the removal to … | postpone) and one per store of data (keep | migrate | delete)
  [exit 1]
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-3-remove-reminders.md --to write --when 1 --answer weekly-streak: keep it by removing the button; notification-settings: retire it too; reminder_schedule: keep
define.confirm-impact → define.write  (when: proceed with the chosen set)
43:## Impact — proposed 2026-09-11
59:## Impact — PM answer 2026-09-11
(the cap: breakdown → confirm-breakdown three times on a fourth parent, then only write/drop)
$ python3 framework/tools/orchestrate.py start changes/2026-09-11-4-reports.md --command speckit.specify
started at define.intake via speckit.specify
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-4-reports.md --to sort --answer reports: daily, weekly, monthly
define.intake → define.sort
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-4-reports.md --to discuss --when 3
define.sort → define.discuss  (when: new logic, a change to an existing node, or a cross-cutting change to several nodes)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-4-reports.md --to breakdown --when 2 --answer propose the chunks
define.discuss → define.breakdown  (when: several capabilities; propose the chunks)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-4-reports.md --to confirm-breakdown
define.breakdown → define.confirm-breakdown
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-4-reports.md --to breakdown --when 2 --answer merge 1 and 2, round 1
define.confirm-breakdown → define.breakdown  (when: merge, split, reorder or drop chunks; rewrite from the PM's words)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-4-reports.md --to confirm-breakdown
define.breakdown → define.confirm-breakdown
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-4-reports.md --to breakdown --when 2 --answer merge 2 and 2, round 2
define.confirm-breakdown → define.breakdown  (when: merge, split, reorder or drop chunks; rewrite from the PM's words)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-4-reports.md --to confirm-breakdown
define.breakdown → define.confirm-breakdown
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-4-reports.md --to spawn --when 1 --answer yes
refused: the breakdown has been proposed 3 times (the cap is 3); only write (one node) or drop are legal from define.confirm-breakdown now
  [exit 1]
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-4-reports.md --to breakdown --when 2 --answer split again
refused: the breakdown has been proposed 3 times (the cap is 3); only write (one node) or drop are legal from define.confirm-breakdown now
  [exit 1]
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-4-reports.md --to write --when 3 --answer one thing
define.confirm-breakdown → define.write  (when: one thing after all; write it as a single node)

### 11. check_all and the 3.9 syntax scan
py39 syntax OK
check_all exit 0
37
   refused: archify CLI not found; install with: python3 framework/tools/archify_delta.py install   (or: npx skills add tt-a1i/archify -g)

ALL CHECKS PASSED
```

`check_all.py` tail (exit 0; 37 `==` steps, the orchestrate-check line reads "CLOSED — 58 steps, …"):

```
$ python3 -c "import ast,glob; [ast.parse(open(f).read(),f,feature_version=(3,9)) for f in glob.glob('framework/tools/*.py')+glob.glob('tools/*.py')]; print('py39 syntax OK')"
py39 syntax OK

$ python3 tools/check_all.py | tail -3
   refused: archify CLI not found; install with: python3 framework/tools/archify_delta.py install   (or: npx skills add tt-a1i/archify -g)

ALL CHECKS PASSED

$ wc -l framework/tools/orchestrate.py
1155 framework/tools/orchestrate.py
```

Notes for Phase 3 and Phase 4: the group block's fence markers and the row format above are what Phase 3 documents; a chunk released from `waiting` is released by an explicit `advance --to define.discuss` (the runner's `--group` in Phase 4 issues it after `deliver.done`), so two chunks whose dependency was dropped can both be released and both show as "in flight" until the runner picks one. `commit.py`'s `slug_of` still strips only `<date>-<n>-`; a child's commit message would carry `1.2-slug` — Phase 5's docs or a later phase may adjust it (out of this phase's scope).

## Phase 3 — Queue and record conventions

Scope: `framework/tools/orchestrate.py` (queue writer only), `framework/components/change-record.md`, `framework/README.md` (conventions only). Added to the scope in this phase: `framework/tools/commit.py`, `slug_of` only — reason: Phase 2's closing note left a child's commit message carrying `1.2-slug`; the child file name `<date>-<n>.<chunk>-<slug>` is a Phase 3 convention (documented here), so the one function that reads it back is fixed where the convention is written down, before Phase 4 runs children through Deliver.

- [x] Group block in `QUEUE.md` written by spawn, updated at every child step change, `deliver.done` and `dropped`; "n of m delivered".
- [x] Documented in `change-record.md` and the README conventions (parent, child, group, waiting).
- [x] Proof: after child 1 reaches `deliver.done` via the fake harness, `QUEUE.md` shows "1 of 3 delivered" and child 2 at `define.discuss`; pasted here.

Files edited: `framework/tools/orchestrate.py` (1155 → 1172 lines: queue writer only — `write_group_block` docstring states the block's format; the block is now also rewritten when a *parent* with children moves, so a parent reopened by `revise-breakdown` shows its current step in the `Parent:` line between the reopening and the next spawn; a new `live_wait` computes the `waiting on` column of a waiting chunk from its dependencies as of the write — `chunk <n>` for the first still-blocking one, `release` when every dependency is delivered or dropped — instead of copying the front matter's `waiting_on`, which moves only at the next release attempt and read "chunk 1" after chunk 1 was delivered). `framework/tools/commit.py` (`slug_of` accepts `<date>-<n>.<chunk>-<slug>`; 1 line plus a docstring). `framework/components/change-record.md` (68 → 124 lines: the breakdown and impact sections in the section list, "broken down" as an outcome, the paragraphs **Parent and children** and **Waiting**, the group block with an example and the meaning of every line, the AI's rules for a group). `framework/README.md` (313 → 341 lines: layout rows for child records, the group block and `changes/runs/`; conventions **Parent, child, group** and **Waiting**). The loop and the terms of the README are Phase 5's.

Proof (2026-09-11; scratch product under the session scratchpad `p3/p`, built with `tools/new_product.py … --agent claude --no-git`, the edited tools copied in; the script `p3/proof.sh` produced this log; the breakdown block was written by hand as in Phase 2 because the fake harness learns to write it in Phase 4; the PM's answers on child 1 are the ones `check_all.py` step 7 scripts):

```
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1-habit-tracker.md --to sort --answer a habit tracker: log a habit, see a weekly streak, get a reminder
define.intake → define.sort
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1-habit-tracker.md --to discuss --when 3
define.sort → define.discuss  (when: new logic, a change to an existing node, or a cross-cutting change to several nodes)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1-habit-tracker.md --to breakdown --when 2 --answer three capabilities, propose the chunks
define.discuss → define.breakdown  (when: several capabilities; propose the chunks)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1-habit-tracker.md --to confirm-breakdown
define.breakdown → define.confirm-breakdown
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1-habit-tracker.md --to spawn --when 1 --answer yes
define.confirm-breakdown → define.spawn  (when: yes, these chunks in this order)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1-habit-tracker.md --to broken-down
define.spawn → define.broken-down
  child 1: changes/2026-09-11-1.1-log-habit.md  step: define.discuss  waiting on: PM  lane: small  depends on: nothing
  child 2: changes/2026-09-11-1.2-weekly-streak.md  step: waiting  waiting on: chunk 1  lane: small  depends on: changes/2026-09-11-1.1-log-habit.md
  child 3: changes/2026-09-11-1.3-reminder.md  step: waiting  waiting on: chunk 1  lane: small  depends on: changes/2026-09-11-1.1-log-habit.md

### child 1 to deliver.done with the fake harness (the PM's answers scripted as in check_all step 7)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1.1-log-habit.md --to write --when 1 --answer a log page
define.discuss → define.write  (when: it is business logic; write it)
PM step: define.approve — PM approves the logic?
run: 2 step(s) run, 1 PM stop(s), 1.1s total (define.write 0.2s, define.challenge 0.2s); stopped at PM step define.approve
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1.1-log-habit.md --to commit --when 3 --answer yes
define.approve → define.commit  (when: PM says yes)
PM step: deliver.approve-plan — PM approves the plan?
run: 5 step(s) run, 1 PM stop(s), 2.3s total (define.commit 0.2s, define.to-deliver 0.1s, deliver.trace 0.2s, deliver.plan 0.2s, deliver.challenge-plan 0.2s); stopped at PM step deliver.approve-plan
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1.1-log-habit.md --to execute --when 1 --answer execute
deliver.approve-plan → deliver.execute  (when: yes, execute)
PM step: deliver.accept — PM accepts the result?
run: 4 step(s) run, 1 PM stop(s), 2.6s total (deliver.execute 0.2s, deliver.tasks-done 0.2s, deliver.verify 0.3s, deliver.passes 0.2s); stopped at PM step deliver.accept
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1.1-log-habit.md --to commit --when 1 --answer accepted
deliver.accept → deliver.commit  (when: accepted)
run: 2 step(s) run, 0 PM stop(s), 1.1s total (deliver.commit 0.2s, deliver.was-rule 0.2s); closed at deliver.done
step: deliver.done

### the group block after child 1 delivered (rewritten at every child move)
<!-- group: changes/2026-09-11-1-habit-tracker.md -->
## Group: 2026-09-11-1-habit-tracker

Parent: changes/2026-09-11-1-habit-tracker.md (define.broken-down)

| n | file | step | waiting on |
|---|---|---|---|
| 1 | changes/2026-09-11-1.1-log-habit.md | deliver.done | nobody |
| 2 | changes/2026-09-11-1.2-weekly-streak.md | waiting | release |
| 3 | changes/2026-09-11-1.3-reminder.md | waiting | release |

1 of 3 delivered; nothing in flight
<!-- /group -->

### child 2 released with the runner's command (Phase 4 issues it from --group)
$ python3 framework/tools/orchestrate.py advance changes/2026-09-11-1.2-weekly-streak.md --to define.discuss
waiting → define.discuss  (released: every dependency at deliver.done or dropped)
<!-- group: changes/2026-09-11-1-habit-tracker.md -->
## Group: 2026-09-11-1-habit-tracker

Parent: changes/2026-09-11-1-habit-tracker.md (define.broken-down)

| n | file | step | waiting on |
|---|---|---|---|
| 1 | changes/2026-09-11-1.1-log-habit.md | deliver.done | nobody |
| 2 | changes/2026-09-11-1.2-weekly-streak.md | define.discuss | PM |
| 3 | changes/2026-09-11-1.3-reminder.md | waiting | release |

1 of 3 delivered; in flight: chunk 2
<!-- /group -->

### commit.py slug_of on a child name
weekly-streak habit-tracker
```

`check_all.py` tail (exit 0; 37 `==` steps; the orchestrate-check line reads "CLOSED — 58 steps, …"):

```
$ python3 -c "import ast,glob; [ast.parse(open(f).read(),f,feature_version=(3,9)) for f in glob.glob('framework/tools/*.py')+glob.glob('tools/*.py')]; print('py39 syntax OK')"
py39 syntax OK

$ python3 tools/check_all.py | tail -3
   refused: archify CLI not found; install with: python3 framework/tools/archify_delta.py install   (or: npx skills add tt-a1i/archify -g)

ALL CHECKS PASSED
```

## Phase 4 — Fake harness and runner

Scope: `framework/tools/fake_harness.py`, `framework/tools/run.py`, `framework/commands/speckit.run.md`, plus `tools/check_all.py` for the new step 8. Added to the scope in this phase: `framework/tools/orchestrate.py`, one line in `next_info` — reason: the proof found that `next --json` on a *parent* never carried `group` (the function's `path` parameter was shadowed by `name, path = template_for(…)` before `add_group_info` read it; a child's JSON was unaffected because it reads `meta["parent"]`), so `run.py --group <parent>` saw "no children" for every parent. A Phase 2 defect, fixed where it lives (`path` → `tmpl` for the template), nothing else in the file touched.

- [x] Fake harness: writes a valid breakdown block (three chunks, one dependency) at `breakdown`; a valid impact block (two dependants, one store) at `impact`; a valid discussion at a child's `discuss`; never answers a PM gate.
- [x] `run.py --group <parent>` continues with the next unblocked child after `deliver.done`; without it stops as today; a waiting child is exit 3 with the wait reason (E9); `--group` on a non-parent refused.
- [x] Proof: `check_all.py` step 8 (new): the two happy paths from PLAN §6.2–6.3 and the refusals in §6.4; tail pasted here.

Files edited: `framework/tools/fake_harness.py` (158 → 383 lines), `framework/tools/run.py` (632 → 764 lines), `framework/commands/speckit.run.md` (`--group`, the waiting stop, the two new gates read to the PM as the block stands, never answered by the AI), `tools/check_all.py` (248 → 473 lines: `group_fixture`, step 8, run on the step-7 fixture after the runner test; 37 → 127 `==` lines), `framework/tools/orchestrate.py` (the one line above). Python 3.9 throughout (`from __future__ import annotations`, no `match`, no runtime `X | Y`).

How it is built:

- Fake harness. `define.breakdown` writes `## Breakdown — proposed <date>` in the §3.3 format: three chunks named after the record's slug (`<slug>-log`, `<slug>-streak`, `<slug>-remind`), each naming its own node in backticks, chunk 3 `depends on: chunk 1`, the order line, "Not split further because", three alternatives; when the record already carries an `## Impact — proposed` block (the gate sent it `confirm-impact → breakdown`, E16) it writes two chunks, `<slug>-replacement` before `<slug>-removal` (`depends on: chunk 1`); when a `## Breakdown — PM answer` follows the last proposal (a rewrite round, E2) the new block opens with "Rewritten from the PM's words: …" and is appended, never edited in. `define.impact` writes `## Impact — proposed <date>` in the §3.4 format: "Removing or changing" is the first backticked id after "remove"/"retire" in the record (else its slug); the dependants are every `@node` tag under `code/` except the removed node — read, never guessed — each with what stops working, the four options and one recommendation (the last dependant "keep it by a replacement", the others "retire it too"); "Rules and decisions affected"; one "Stored data" line with keep recommended; "Possible, unverified". `define.challenge` on a record with an impact block compares the block's dependants against the `@node` tags and adds one finding per tagged node the block omits (E20): "the impact block omits the tagged dependant `<id>` (@node <id> in <file>); list it with its options before approve (E20)". `fake_harness.py --discuss <record>` (outside the runner) writes the discussion a PM step leaves and does not advance; on a child it is a proposed correction in the §3.3 format — the parent's chunks minus the dropped ones, plus one new chunk `<parent-slug>-settings` depending on this one — so `revise-breakdown` reopens the parent with a block `spawn` can consume (E4). `--answer` is never passed: the fake never answers a gate, `confirm-breakdown` and `confirm-impact` included (the runner stops before them). Test switches: `FAKE_HARNESS_E5=1` (chunk 3 names chunk 2's node with no dependency), `FAKE_HARNESS_NO_DEPENDANTS=1` (an impact block with no dependants).
- Runner. A record whose `next --json` says `mode: waiting` is a PM-visible stop (E9): exit 3 with "Waiting: chunk n of <parent> waits for chunk k (<file> at <step>) to reach deliver.done; nothing runs until then.", the release command and the `--group` command; nothing is spawned. `--group <parent>` (with or without a record): refused (exit 4) when the path names a child ("pass its parent: --group <parent>") or a record with no children that is not at `define.breakdown` / `confirm-breakdown` / `spawn`; when a record is also given it must be the parent or one of its children. The group loop runs the parent while it is open (a reopened parent stops at `confirm-breakdown`; a parent at `spawn` is spawned by the fake), then picks the first child in flight (not waiting, not closed), else the first waiting child that `advance --to define.discuss` releases (a refusal is printed and the next one tried), runs it to its end or PM stop, and after a close (`deliver.done`, `define.dropped`, `deliver.dropped`) picks again; exit 0 with "group closed: … n of m delivered" when every chunk is done or dropped, or "group: nothing to run" when the rest is blocked. Without `--group` a child's run stops when the child closes, as before. Every close and every PM stop print the group line ("Group: <title> (<parent>) — n of m delivered; k dropped; in flight: chunk …"); inside a group run the "Then run again" hint names `--group <parent>`. `COMMON_YES` gains "proceed with the chosen set", so `confirm-impact` shows "Most common answer: --to 1 --when 1" (→ write) like `confirm-breakdown` (→ spawn, `--answer "yes"`); because that gate's answer must name every dependant, the pasted command carries the placeholder `<dependant>: retire it too | keep it by <replacement> | narrow the removal to <…> | postpone; <store>: keep | migrate | delete` instead of the bare phrase.
- `check_all.py` step 8 (`group_fixture`, on the step-7 fixture, whose `code/backend/auth/auth.py` carries `@node login` and `@node reset-password`): (a) `3-habit-tracker`: start → intake → fake sort→discuss → PM breakdown → fake breakdown (block asserted; no PM-answer block written by the fake; "Most common answer: --to 1 --when 1" and `--answer "yes" &&` asserted) → PM yes → fake spawn → three children, chunk 1 at discuss, 2 and 3 waiting; E9 on child 2; E10; `--group` on a child and on `1-runner`; child 1 to `deliver.done` with the step-7 answers, the last run without `--group` (asserted: closed, "1 of 3 delivered; nothing in flight", nothing released); `--group` releases chunk 2 and stops at its discussion; `QUEUE.md` asserted "1 of 3 delivered; in flight: chunk 2" with chunk 1's row at `deliver.done`. (c) on the same group: E3 (chunk 2 dropped at its gate; `--group` closes it and releases chunk 3; "1 of 3 delivered; 1 dropped; in flight: chunk 3"), E4 (`--discuss` on chunk 3, revise-breakdown, `--group` stops at the reopened parent showing "previous chunks", yes, `--group` spawns and releases chunk 2 = the old chunk 3; chunk 1's bytes equal before and after, still `deliver.done`; the new `3.3-habit-tracker-settings` waits on chunk 2; "1 of 4 delivered; 1 dropped; in flight: chunk 2"; two breakdown decisions, the second `supersedes:` the first), E11 (parent file moved away; parent's PM-answer heading renamed; both restored, `check <child>` CLOSED again). (b) `4-remove-reminders`: PM impact → fake impact (two dependants from the tags, options, recommendation, the stored-data line asserted; no PM answer written) → PM "login: retire it too; reset-password: keep it by a replacement; reminder table: keep" `--to breakdown` → fake breakdown with `1. remove-reminders-replacement` before `2. remove-reminders-removal` (`depends on: chunk 1`) → yes → `--group` on the parent at spawn: spawns, runs chunk 1 to its discussion; the group block asserted with the replacement first and the removal waiting on chunk 1. E1 (`5-reports`: write from confirm-breakdown; the proposal stays; approve reached). E2 (`6-accounts`: three proposals, the third "Rewritten from the PM's words: merge 1 and 2, round 2"; a yes and a fourth rewrite refused with the cap; drop legal). E5 (`7-shop`, `FAKE_HARNESS_E5`; `advance --to broken-down` refused naming both chunks and the node). E18 (`8-remove-login` with `nodes: [login]`; a hand-written `2026-09-10-9-build-login.md` at `deliver.execute` on `login`; refused; the record removed; impact reached). E20 (same record: PM answer → write; `code/backend/notify/notify.py` with `@node notification-settings` added; the fake's challenge writes the finding; asserted in the record; the tag removed after). E15 (`9-remove-orphan`, `FAKE_HARNESS_NO_DEPENDANTS`: the runner exits 4 and the step log carries "lists no dependants; with no dependants there is no impact stop (E15)"; `10-retire-orphan`: the same removal answered `discuss → write` with "no dependants found (tags, tree, glossary)" and run to approve).

Proof (2026-09-11; `python3 tools/check_all.py`, exit 0, 127 `==` lines; step 8's lines below are the exact output with the repeated PM-stop bodies filtered out — the `Options`, `Record the answer`, `Most common answer`, `Group:` and `next`-style lines the runner prints at every stop — by `grep -vE "^   (Options|  [0-9]\.|Record the|Slash|The PM must|What happens|PM step|Then run|Most common|  python3|Group:|fake harness|step:|mode:|…)"`; every `(exit n)` in a title is the exit code asserted for that run):

```
== group: start changes/2026-09-11-3-habit-tracker.md
   started at define.intake via speckit.specify
== group: intake answer
   define.intake → define.sort
== group: changes/2026-09-11-3-habit-tracker.md sort → discuss (exit 3)
   run: 1 step(s) run, 1 PM stop(s), 0.6s total (define.sort 0.2s); stopped at PM step define.discuss
== group: PM answers at changes/2026-09-11-3-habit-tracker.md: --to breakdown --when 2 --answer three capabilities: log, streak, reminder; propose the chunks
   define.discuss → define.breakdown  (when: several capabilities; propose the chunks)
== group: breakdown (fake) → the PM stop at confirm-breakdown (exit 3)
   run: 1 step(s) run, 1 PM stop(s), 0.6s total (define.breakdown 0.2s); stopped at PM step define.confirm-breakdown
== group: PM answers at changes/2026-09-11-3-habit-tracker.md: --to spawn --when 1 --answer yes
   define.confirm-breakdown → define.spawn  (when: yes, these chunks in this order)
== group: spawn (fake) → broken-down (exit 0)
   run: 1 step(s) run, 0 PM stop(s), 0.7s total (define.spawn 0.3s); closed at define.broken-down
== group: E9: the runner on the waiting child 2 (exit 3)
   Waiting: chunk 2 of changes/2026-09-11-3-habit-tracker.md waits for chunk 1 (changes/2026-09-11-3.1-habit-tracker-log.md at define.discuss) to reach deliver.done; nothing runs until then.
   Release it when that holds: python3 framework/tools/orchestrate.py advance changes/2026-09-11-3.2-habit-tracker-streak.md --to define.discuss (refused before)
   Or run the group, which releases it itself: python3 framework/tools/run.py --group changes/2026-09-11-3-habit-tracker.md --harness fake
   run: 0 step(s) run, 0 PM stop(s), 0.1s total (no AI steps); stopped: chunk 2 waits on chunk 1
== group: E10: start on a child
   refused: changes/2026-09-11-3.2-habit-tracker-streak.md carries `parent: changes/2026-09-11-3-habit-tracker.md`; children are created by define.spawn; run the parent (E10)
== group: --group on a child is refused (exit 4)
   stuck: --group changes/2026-09-11-3.1-habit-tracker-log.md names a child (chunk 1 of changes/2026-09-11-3-habit-tracker.md); pass its parent: --group changes/2026-09-11-3-habit-tracker.md
== group: --group on a record with no children is refused (exit 4)
   stuck: --group changes/2026-09-11-1-runner.md names a record with no children that is not at the breakdown (it is at deliver.done); --group takes a parent that define.spawn has broken down, or one on its way there (run the record itself: python3 framework/tools/run.py changes/2026-09-11-1-runner.md)
== group: PM answers at changes/2026-09-11-3.1-habit-tracker-log.md: --to write --when 1 --answer a log page
   define.discuss → define.write  (when: it is business logic; write it)
== group: child 1 to the PM stop define.approve (exit 3)
   run: 2 step(s) run, 1 PM stop(s), 1.0s total (define.write 0.2s, define.challenge 0.2s); stopped at PM step define.approve
== group: PM answers at changes/2026-09-11-3.1-habit-tracker-log.md: --to commit --when 3 --answer yes
   define.approve → define.commit  (when: PM says yes)
== group: child 1 to the PM stop deliver.approve-plan (exit 3)
   run: 5 step(s) run, 1 PM stop(s), 2.3s total (define.commit 0.2s, define.to-deliver 0.1s, deliver.trace 0.2s, deliver.plan 0.2s, deliver.challenge-plan 0.2s); stopped at PM step deliver.approve-plan
== group: PM answers at changes/2026-09-11-3.1-habit-tracker-log.md: --to execute --when 1 --answer execute
   deliver.approve-plan → deliver.execute  (when: yes, execute)
== group: child 1 to the PM stop deliver.accept (exit 3)
   run: 4 step(s) run, 1 PM stop(s), 3.0s total (deliver.execute 0.2s, deliver.tasks-done 0.2s, deliver.verify 0.4s, deliver.passes 0.2s); stopped at PM step deliver.accept
== group: PM answers at changes/2026-09-11-3.1-habit-tracker-log.md: --to commit --when 1 --answer accepted
   deliver.accept → deliver.commit  (when: accepted)
== group: child 1 to deliver.done (no --group: stops after the child) (exit 0)
   run: 2 step(s) run, 0 PM stop(s), 1.2s total (deliver.commit 0.2s, deliver.was-rule 0.2s); closed at deliver.done
== group: --group continues: releases child 2 and stops at its discussion (exit 3)
   group: released chunk 2 (changes/2026-09-11-3.2-habit-tracker-streak.md) — every dependency delivered or dropped
   group: running changes/2026-09-11-3.2-habit-tracker-streak.md
   run: 0 step(s) run, 1 PM stop(s), 0.2s total (no AI steps); stopped at PM step define.discuss
== group: QUEUE.md shows "1 of 3 delivered; in flight: chunk 2"
== group: PM answers at changes/2026-09-11-3.2-habit-tracker-streak.md: --to drop --when 8 --answer stop, the streak is not wanted
   define.discuss → define.drop  (when: PM stops the request)
== group: E3: --group drops chunk 2 and releases chunk 3 (exit 3)
   group: running changes/2026-09-11-3.2-habit-tracker-streak.md
   run: 1 step(s) run, 0 PM stop(s), 0.6s total (define.drop 0.2s); closed at define.dropped
   group: released chunk 3 (changes/2026-09-11-3.3-habit-tracker-remind.md) — every dependency delivered or dropped
   group: running changes/2026-09-11-3.3-habit-tracker-remind.md
   run: 0 step(s) run, 1 PM stop(s), 0.1s total (no AI steps); stopped at PM step define.discuss
== group: E3: QUEUE.md shows "1 of 3 delivered; 1 dropped; in flight: chunk 3"
== group: E4: the fake writes chunk 3's discussion (a proposed correction)
== group: PM answers at changes/2026-09-11-3.3-habit-tracker-remind.md: --to revise-breakdown --when 4 --answer building this showed a settings capability is missing
   define.discuss → define.revise-breakdown  (when: on a child record, building this chunk showed the split or the order is wrong)
     parent changes/2026-09-11-3-habit-tracker.md reopened at define.confirm-breakdown with a new `## Breakdown — proposed` block; this chunk waits on parent
== group: E4: --group runs the parent, reopened at confirm-breakdown (exit 3)
   group: running changes/2026-09-11-3-habit-tracker.md
   run: 0 step(s) run, 1 PM stop(s), 0.1s total (no AI steps); stopped at PM step define.confirm-breakdown
== group: PM answers at changes/2026-09-11-3-habit-tracker.md: --to spawn --when 1 --answer yes
   define.confirm-breakdown → define.spawn  (when: yes, these chunks in this order)
== group: E4: --group spawns the revised set and releases the next chunk (exit 3)
   group: running changes/2026-09-11-3-habit-tracker.md
   run: 1 step(s) run, 0 PM stop(s), 0.8s total (define.spawn 0.3s); closed at define.broken-down
   group: released chunk 2 (changes/2026-09-11-3.3-habit-tracker-remind.md) — every dependency delivered or dropped
   group: running changes/2026-09-11-3.3-habit-tracker-remind.md
   run: 0 step(s) run, 1 PM stop(s), 0.2s total (no AI steps); stopped at PM step define.discuss
== group: E4: chunk 1 untouched (bytes equal, deliver.done); the new chunk waits on chunk 2; two breakdown decisions
== group: E11: next on a child whose parent file is missing
   refused: changes/2026-09-11-3.3-habit-tracker-remind.md is chunk 2 of changes/2026-09-11-3-habit-tracker.md, which does not exist (E11); restore the parent file (it was moved or deleted by hand)
== group: E11: check on a child whose parent lost its PM-answer block
   refused: parent changes/2026-09-11-3-habit-tracker.md of changes/2026-09-11-3.3-habit-tracker-remind.md has no `## Breakdown — PM answer` block (E11); the parent was edited by hand — restore the block the PM answered at define.confirm-breakdown
== group: check on the child again
   CLOSED — 58 steps, every one mapped to a role and mode; 21 commands, every one entering a real non-routing step; 1 meta command entering the record's current step; toolbox: 3 step row(s); changes/2026-09-11-3.3-habit-tracker-remind.md is chunk 2 of changes/2026-09-11-3-habit-tracker.md (parent and PM answer present)
== group: start changes/2026-09-11-4-remove-reminders.md
   started at define.intake via speckit.specify
== group: intake answer
   define.intake → define.sort
== group: changes/2026-09-11-4-remove-reminders.md sort → discuss (exit 3)
   run: 1 step(s) run, 1 PM stop(s), 0.6s total (define.sort 0.2s); stopped at PM step define.discuss
== group: PM answers at changes/2026-09-11-4-remove-reminders.md: --to impact --when 3 --answer show me the repercussions
   define.discuss → define.impact  (when: this removes or changes something others depend on; show the repercussions)
== group: impact (fake) → the PM stop at confirm-impact (exit 3)
   run: 1 step(s) run, 1 PM stop(s), 0.7s total (define.impact 0.2s); stopped at PM step define.confirm-impact
== group: PM answers at changes/2026-09-11-4-remove-reminders.md: --to breakdown --when 3 --answer login: retire it too; reset-password: keep it by a replacement; reminder table: keep
   define.confirm-impact → define.breakdown  (when: a chosen treatment needs a replacement built first; make the set chunks, replacement before removal)
== group: breakdown after the impact answer: the replacement chunk before the removal (exit 3)
   run: 1 step(s) run, 1 PM stop(s), 0.6s total (define.breakdown 0.2s); stopped at PM step define.confirm-breakdown
== group: PM answers at changes/2026-09-11-4-remove-reminders.md: --to spawn --when 1 --answer yes
   define.confirm-breakdown → define.spawn  (when: yes, these chunks in this order)
== group: --group on the parent at spawn: spawns, then runs chunk 1 to its discussion (exit 3)
   group: running changes/2026-09-11-4-remove-reminders.md
   run: 1 step(s) run, 0 PM stop(s), 0.8s total (define.spawn 0.3s); closed at define.broken-down
   group: running changes/2026-09-11-4.1-remove-reminders-replacement.md
   run: 0 step(s) run, 1 PM stop(s), 0.2s total (no AI steps); stopped at PM step define.discuss
== group: the removal group shows the replacement chunk first, the removal waiting on it
== group: start changes/2026-09-11-5-reports.md
   started at define.intake via speckit.specify
== group: intake answer
   define.intake → define.sort
== group: changes/2026-09-11-5-reports.md sort → discuss (exit 3)
   run: 1 step(s) run, 1 PM stop(s), 0.7s total (define.sort 0.2s); stopped at PM step define.discuss
== group: PM answers at changes/2026-09-11-5-reports.md: --to breakdown --when 2 --answer propose the chunks
   define.discuss → define.breakdown  (when: several capabilities; propose the chunks)
== group: E1: breakdown → confirm-breakdown (exit 3)
   run: 1 step(s) run, 1 PM stop(s), 0.7s total (define.breakdown 0.2s); stopped at PM step define.confirm-breakdown
== group: PM answers at changes/2026-09-11-5-reports.md: --to write --when 3 --answer one thing
   define.confirm-breakdown → define.write  (when: one thing after all; write it as a single node)
== group: E1: write as a single node → the PM stop at approve (exit 3)
   run: 2 step(s) run, 1 PM stop(s), 1.2s total (define.write 0.2s, define.challenge 0.2s); stopped at PM step define.approve
== group: E1: single node written; the proposal stays in the record
== group: start changes/2026-09-11-6-accounts.md
   started at define.intake via speckit.specify
== group: intake answer
   define.intake → define.sort
== group: changes/2026-09-11-6-accounts.md sort → discuss (exit 3)
   run: 1 step(s) run, 1 PM stop(s), 0.7s total (define.sort 0.2s); stopped at PM step define.discuss
== group: PM answers at changes/2026-09-11-6-accounts.md: --to breakdown --when 2 --answer propose the chunks
   define.discuss → define.breakdown  (when: several capabilities; propose the chunks)
== group: E2: round 1 (exit 3)
   run: 1 step(s) run, 1 PM stop(s), 0.7s total (define.breakdown 0.2s); stopped at PM step define.confirm-breakdown
== group: PM answers at changes/2026-09-11-6-accounts.md: --to breakdown --when 2 --answer merge 1 and 2, round 1
   define.confirm-breakdown → define.breakdown  (when: merge, split, reorder or drop chunks; rewrite from the PM's words)
== group: E2: rewrite after the PM's words, round 1 (exit 3)
   run: 1 step(s) run, 1 PM stop(s), 0.6s total (define.breakdown 0.2s); stopped at PM step define.confirm-breakdown
== group: PM answers at changes/2026-09-11-6-accounts.md: --to breakdown --when 2 --answer merge 1 and 2, round 2
   define.confirm-breakdown → define.breakdown  (when: merge, split, reorder or drop chunks; rewrite from the PM's words)
== group: E2: rewrite after the PM's words, round 2 (exit 3)
   run: 1 step(s) run, 1 PM stop(s), 0.7s total (define.breakdown 0.2s); stopped at PM step define.confirm-breakdown
== group: E2: a yes after three rounds
   refused: the breakdown has been proposed 3 times (the cap is 3); only write (one node) or drop are legal from define.confirm-breakdown now
== group: E2: a fourth rewrite
   refused: the breakdown has been proposed 3 times (the cap is 3); only write (one node) or drop are legal from define.confirm-breakdown now
== group: PM answers at changes/2026-09-11-6-accounts.md: --to drop --when 4 --answer stop
   define.confirm-breakdown → define.drop  (when: PM stops the request)
== group: start changes/2026-09-11-7-shop.md
   started at define.intake via speckit.specify
== group: intake answer
   define.intake → define.sort
== group: changes/2026-09-11-7-shop.md sort → discuss (exit 3)
   run: 1 step(s) run, 1 PM stop(s), 0.6s total (define.sort 0.2s); stopped at PM step define.discuss
== group: PM answers at changes/2026-09-11-7-shop.md: --to breakdown --when 2 --answer propose the chunks
   define.discuss → define.breakdown  (when: several capabilities; propose the chunks)
== group: E5: a breakdown whose chunks 2 and 3 share a node (exit 3)
   run: 1 step(s) run, 1 PM stop(s), 0.6s total (define.breakdown 0.2s); stopped at PM step define.confirm-breakdown
== group: PM answers at changes/2026-09-11-7-shop.md: --to spawn --when 1 --answer yes
   define.confirm-breakdown → define.spawn  (when: yes, these chunks in this order)
== group: E5: spawn refuses
   refused: chunks 2 (shop-streak) and 3 (shop-remind) both touch node shop-streak with no dependency between them (E5); add `depends on: chunk 2` to chunk 3 (a node is named as `delivered node <id>` or as `<id>` in backticks)
== group: start changes/2026-09-11-8-remove-login.md
   started at define.intake via speckit.specify
== group: intake answer
   define.intake → define.sort
== group: changes/2026-09-11-8-remove-login.md sort → discuss (exit 3)
   run: 1 step(s) run, 1 PM stop(s), 0.6s total (define.sort 0.2s); stopped at PM step define.discuss
== group: E18: impact while a record in Deliver names the node
   refused: changes/2026-09-10-9-build-login.md is in Deliver (deliver.execute) on node login, which this request names in its front matter `nodes:` (E18); one change in flight per node — the impact is shown once that record reaches deliver.done or is dropped (heuristic: the two records' `nodes:` lists share an id; a record without `nodes:` is not compared)
== group: PM answers at changes/2026-09-11-8-remove-login.md: --to impact --when 3 --answer show
   define.discuss → define.impact  (when: this removes or changes something others depend on; show the repercussions)
== group: E18 lifted: impact → confirm-impact (exit 3)
   run: 1 step(s) run, 1 PM stop(s), 0.6s total (define.impact 0.2s); stopped at PM step define.confirm-impact
== group: PM answers at changes/2026-09-11-8-remove-login.md: --to write --when 1 --answer reset-password: keep it by a replacement; login table: keep
   define.confirm-impact → define.write  (when: proceed with the chosen set)
== group: E20: write → challenge finds the tagged dependant the impact block omits (exit 3)
   run: 2 step(s) run, 1 PM stop(s), 1.2s total (define.write 0.2s, define.challenge 0.2s); stopped at PM step define.approve
== group: E20: finding present: the impact block omits the tagged dependant `notification-settings` (@node notification-settings in code/backend/notify/notify.py)
== group: start changes/2026-09-11-9-remove-orphan.md
   started at define.intake via speckit.specify
== group: intake answer
   define.intake → define.sort
== group: changes/2026-09-11-9-remove-orphan.md sort → discuss (exit 3)
   run: 1 step(s) run, 1 PM stop(s), 0.6s total (define.sort 0.2s); stopped at PM step define.discuss
== group: PM answers at changes/2026-09-11-9-remove-orphan.md: --to impact --when 3 --answer show
   define.discuss → define.impact  (when: this removes or changes something others depend on; show the repercussions)
== group: E15: the impact block lists no dependants; leaving impact is refused (exit 4)
   stuck: define.impact did not move the record after a retry; see changes/runs/2026-09-11-9-remove-orphan/3-define.impact.log
   run: 1 step(s) run, 0 PM stop(s), 0.8s total (define.impact 0.3s); stuck
== group: E15: refused with "no dependants … there is no impact stop (E15)"
== group: start changes/2026-09-11-10-retire-orphan.md
   started at define.intake via speckit.specify
== group: intake answer
   define.intake → define.sort
== group: changes/2026-09-11-10-retire-orphan.md sort → discuss (exit 3)
   run: 1 step(s) run, 1 PM stop(s), 0.6s total (define.sort 0.2s); stopped at PM step define.discuss
== group: PM answers at changes/2026-09-11-10-retire-orphan.md: --to write --when 1 --answer no dependants found (tags, tree, glossary): retire it
   define.discuss → define.write  (when: it is business logic; write it)
== group: E15: the same removal goes discuss → write, as today (exit 3)
   run: 2 step(s) run, 1 PM stop(s), 1.2s total (define.write 0.2s, define.challenge 0.2s); stopped at PM step define.approve
```

`check_all.py` tail (exit 0) and the 3.9 syntax scan:

```
$ python3 -c "import ast,glob; [ast.parse(open(f).read(),f,feature_version=(3,9)) for f in glob.glob('framework/tools/*.py')+glob.glob('tools/*.py')]; print('py39 syntax OK')"
py39 syntax OK

$ python3 tools/check_all.py | tail -3
   refused: archify CLI not found; install with: python3 framework/tools/archify_delta.py install   (or: npx skills add tt-a1i/archify -g)

ALL CHECKS PASSED

$ wc -l framework/tools/run.py framework/tools/fake_harness.py tools/check_all.py framework/commands/speckit.run.md framework/tools/orchestrate.py
   764 framework/tools/run.py
   383 framework/tools/fake_harness.py
   473 tools/check_all.py
    17 framework/commands/speckit.run.md
  1172 framework/tools/orchestrate.py
```

Notes for Phase 5: `framework/orchestration/commands.yaml`'s `does:` line for `speckit.run` does not yet mention `--group` (commands are Phase 5's scope); the README's loop and terms (chunk, group, parent, impact, waiting) are Phase 5's; `speckit.specify.md` says nothing yet about a large request or a removal. The fake's breakdown names chunks after the record's slug, so two large requests never collide on chunk slugs in the fixture; a live Writer chooses its own.

## Phase 5 — Commands, docs, counts

Scope: `framework/commands/speckit.specify.md`, `speckit.run.md`, `framework/README.md` (loop, terms: chunk, group, parent, impact; rules), `framework/components/change-record.md`, `decision-log.md` (breakdown and impact decisions), `framework/orchestration/README.md`, `framework/steps.md` (generated), `DECISIONS.md` (entry: situation, decision, reasons, instead-of, E1–E21 as the test list), `framework/test-cases.md` §T, `README.md` (worked example: one sentence each for a large request and a removal; every step count recomputed by script; `lint.py` OK).

- [x] All files above updated; counts computed, not typed.
- [x] Proof: `grep -rn "51 steps" README.md framework/ docs/` returns only historical lines; `lint.py README.md` OK; `check_all.py` green.

Files edited: `framework/commands/speckit.specify.md` (18 → 19 lines: item 6, the two extra stops — what the PM sees at `define.confirm-breakdown` and `define.confirm-impact`, what they answer, the three-round cap, "a removal nobody depends on has no impact stop", "never answer either gate yourself"). `framework/commands/speckit.run.md` (the front-matter `description` names `--group <parent>`; the body already did since Phase 4). `framework/orchestration/commands.yaml` (the `speckit.run` `does:` line gains `--group`; `check` still CLOSED). `framework/README.md` (341 → 420 lines: the term **PM gate** names the two new gates; new terms **Chunk**, **Parent**, **Child**, **Group**, **Waiting**, **Impact** (with the note that `foundation.impact` shares the name, not the meaning); "The loop" gains the large-request bullet — `discuss → breakdown → confirm-breakdown → spawn | breakdown | write | drop`, the children, `revise-breakdown` — and the removal bullet — `discuss → impact → confirm-impact → write | impact | breakdown | drop`, `challenge` reporting an omitted dependant, the no-dependants case; "One command per request" gains `--group` and the waiting stop; "Rules that apply everywhere" gains the two compact doubt rules from PLAN §3.2 and the two gates in the list of finalising steps; the Phase 3 conventions **Parent, child, group** and **Waiting** were checked against the new terms and left as they were — same file name, same fields, same release rule). `framework/components/change-record.md` (124 → 128 lines: the Phase 3 text stands; the one change says who writes which decision — `orchestrate.py` writes the breakdown decision at `spawn`, the AI writes the impact decision at `define.write` from the PM-answer block). `framework/components/decision-log.md` (96 → 120 lines: Inputs gain `define.confirm-breakdown` and `define.confirm-impact`; a new paragraph **Breakdown and impact decisions (convention)** — `category: product`, `made_by: PM`, `at_step` the gate, what `## Decision` holds for each, the "Instead of" lines (the alternatives considered; the split itself when the PM said "one thing"; each overruled recommendation), the supersede on a re-spawn, "never re-argued"). `framework/orchestration/README.md` (254 → 309 lines: State gains `parent`, `chunk`, `depends_on`, `waiting_on: chunk <n> | parent` and the `waiting` pseudo-state; `check [<child>]`; the group refusals of `advance`; `start` refusing a child; the `next --json` fields `parent`, `chunk`, `depends_on`, `group`, `mode: waiting`, `wait`, `blocked_by`; a Layer 2 bullet for the waiting stop and `--group`; the exit codes and the log folder per record run). `framework/steps.md` regenerated by `tools/docs.py` (58 steps). `DECISIONS.md` (146 → 155 lines: the entry "2026-09-11 — Large requests and removals": situation, decision, reasons, instead-of, the Phases 0–4 paragraph, E1–E21 as the test list with where each was proven). `framework/test-cases.md` (557 → 654 lines: section T, 90 cases T1–T90, one per `==` line `check_all.py` step 8 prints, in print order, the silent assertions between two lines folded into the case they belong to; T20 is FIXED — the Phase 4 defect in `next --json` on a parent — the rest PASS). `README.md` (580 → 616 lines; body prose 1,683 → 1,638 words). `docs/define.png` replaced by the Phase 1 screenshot (25 steps; the old file showed 18) and its alt text updated.

README counts, each computed by script on 2026-09-11 before it was typed: steps 58 (`yaml.safe_load` over `workflows/*.yaml`: define 25, foundation 14, deliver 19); commands 22 in `commands.yaml`, of which 1 `meta` and 8 `entry` (`check` prints "21 commands … 1 meta command"); templates 22 (`framework/commands/*.md`); installer files 110 (`install_commands.py --agent all` inside `check_all.py`: "installed 110 file(s)"); component files 12; test-case rows 336 (rows `| <letter><n>` in sections A–M and O–T, that is every table row except the "Proposed changes" list and section N's re-run rows, which repeat A–M; 246 before section T, so the badge's 225 and the text's 240 were both stale); `check_all.py` `==` lines 127 (90 of them in step 8). Where they appear: the badge (336), the two `CLOSED — 58 steps` blocks, the workflows table (define 25), the `define.png` alt text (25 steps, five exits), "The 58 steps below", "The 25 steps of define" (seven rows added), the `/speckit-run` and `orchestrate.py` table rows, `install_commands.py` "22 command templates" (was 21, wrong before), "maps the 58 steps", "one run of 127 checks" and stage 8 in Tests and evaluation, "336 cases in sections A–M and O–T" and "The regression suite of 336 cases". The Main-path diagram gains the two stops. Key features gains one bullet. Troubleshooting gains the waiting stop and the E10 refusal. To stay under 1,700 words the stage list became a table, "How it works" lost the renderer bullet, and a dozen sentences were shortened without losing a claim.

The worked example's new subsection "define.confirm-breakdown stops a large request" is real: a scratch product built with `tools/new_product.py … --agent claude --no-git` under the session scratchpad `p5/p`, `architecture.md` filled, the request "a habit tracker: log a habit, see a weekly streak, get a reminder" started with `speckit.specify`, `run.py --harness fake` to `discuss`, the PM's `--to breakdown --when 2`, then `run.py --harness fake` again; the block pasted is that run's stdout with the two lines "Record the answer with:" and the generic `advance … --to <exit> [--when <n>] --answer "<the PM's words>"` cut (the README linter refuses `<n>` inside a command; the cut is stated in the README sentence). The same scratch product then took the yes, `run.py --group` spawned three children and stopped at chunk 1's discussion (`0 of 3 delivered; in flight: chunk 1` in `QUEUE.md`), and a second request "remove `log-habit`" against two tagged components (`code/backend/streak/streak.py` with `@node weekly-streak` and `@node log-habit`, `code/backend/log/log.py`) went `discuss → impact` and stopped at `define.confirm-impact` with `weekly-streak [tags: code/backend/streak/streak.py; tree: names "log-habit"]`, its four options, `recommended: keep it by a replacement` and `Stored data: log_habit table — keep | migrate to the replacement | delete; recommended: keep`; that is the removal sentence's basis.

Proof (2026-09-11):

```
$ python3 tools/docs.py
wrote framework/steps.md (58 steps)

$ python3 tools/validate.py
OK — 3 workflow(s), map consistent

$ python3 framework/tools/orchestrate.py check
CLOSED — 58 steps, every one mapped to a role and mode; 21 commands, every one entering a real non-routing step; 1 meta command entering the record's current step; toolbox: 3 step row(s)

$ python3 -c "import ast,glob; [ast.parse(open(f).read(),f,feature_version=(3,9)) for f in glob.glob('framework/tools/*.py')+glob.glob('tools/*.py')]; print('py39 syntax OK')"
py39 syntax OK

$ python3 tools/check_all.py > check5.log 2>&1; echo "exit $?"; tail -3 check5.log; grep -c "^== " check5.log
exit 0
   refused: archify CLI not found; install with: python3 framework/tools/archify_delta.py install   (or: npx skills add tt-a1i/archify -g)

ALL CHECKS PASSED
127

$ python3 /mnt/user-data/outputs/github-readme-writer/lint.py README.md
OK — README.md: 27 headings, 1638 body words; every link and anchor resolves.

$ grep -rn "51 steps" README.md framework/ docs/
framework/test-cases.md:357:Step counts now: define 18, foundation 14, deliver 19 (51 steps). PM
framework/test-cases.md:423:| P32 | The system stays closed | PASS | `orchestrate.py check`: CLOSED, 51 steps, 21 commands, no stubs; …
framework/test-cases.md:491:| R11 | `commands.yaml` with a `stub: true` key on a command | FIXED | … `check`: CLOSED, 51 steps, 21 commands. |
framework/test-cases.md:544:| S33 | Docs vs code | PASS | `check`: 51 steps, 21 commands, 1 meta, 3 toolbox rows; …
docs/plans/2026-09-11-breakdown/EXECUTION.md:20:   CLOSED — 51 steps, …   (the Phase 0 baseline)
docs/plans/2026-09-11-breakdown/EXECUTION.md:35:CLOSED — 51 steps, …   (the Phase 0 baseline)
docs/plans/2026-09-11-breakdown/EXECUTION.md:836:- [x] Proof: `grep -rn "51 steps" …`   (this checklist line)
(every hit is a historical verdict in test-cases.md, the Phase 0 baseline, or this line; README.md and the rest of framework/ carry none)

$ python3 - (the counts, computed from the files)
steps 58 (define 25, deliver 19, foundation 14); commands 22, meta 1, entry 8; templates 22; components 12; test-case rows in A–M and O–T: 336; check_all `==` lines: 127
```

## Phase 6 — Challenger

Scope: read-only pass by a fresh agent over Phases 1–5; fixes applied within each phase's scope.

- [x] Attack list: child advancing while its dependency is not done; spawn run twice; parent re-confirmed while a child is in Deliver; `revise-breakdown` from a delivered chunk; PM answer that parses to zero chunks; slug collisions; `QUEUE.md` edited by hand; dropped middle chunk; `--group` on a non-parent; impact section that omits a tagged dependant (E20 must be a finding at `challenge`); removal whose dependant is mid-Deliver (E18); stored data defaulted to delete (must not happen); rule removal path (E17); all on Python 3.9.
- [x] Proof: zero must-fix findings; report saved here as `challenge.md`; `check_all.py` green.

Done 2026-09-11. Seventeen attacks (the list above plus the runner's paste-ready answer at `confirm-impact`, injection into a proposed block, `python3 -X dev`, and every documented count), each run with real commands in a scratch product under the session scratchpad `p6/p`; the verdict per item is in `challenge.md`. Ten defects confirmed and fixed within their phase's scope: `framework/tools/orchestrate.py` (1172 → 1295 lines: a child edited past `waiting` by hand is refused; `spawn` runs once per yes; a chunk mid-Deliver is never rewritten or removed by a revision; the reopened gate refuses `write`/`drop` while children exist; the impact answer must name every store and an impact block may not recommend delete (E19); E18 reads task tags and backticked ids, not only a `nodes:` field nobody writes; slugs validated and "dependencies first" enforced at `breakdown`; a PM-answer block the gate never wrote is refused by count; a group block with no closing fence no longer swallows the next group; a dropped dependency hands its own dependencies on; `child_discussion` takes the newest section; every print after the last file write), one sentence in `workflows/define.yaml` (`define.challenge` now tells a live challenger to compare the impact section against the tags, E20; `steps.md` and `studio.html` rebuilt), `tools/check_all.py` step 8 (127 → 207 `==` lines; the new cases labelled C1–C9), `framework/test-cases.md` §T (T91–T170), the conventions in `change-record.md`, `framework/README.md` and `orchestration/README.md`, `README.md` counts (207 checks; 396 test cases — Phase 5's 336 had counted section N's re-run rows), `DECISIONS.md`. Prose-only, stated as such: E17 and E20 for a live challenger. Accepted: two `--group` runners racing converge; a non-English yes is refused with the accepted words listed.

Proof (2026-09-11):

```
$ python3 tools/validate.py
OK — 3 workflow(s), map consistent

$ python3 framework/tools/orchestrate.py check
CLOSED — 58 steps, every one mapped to a role and mode; 21 commands, every one entering a real non-routing step; 1 meta command entering the record's current step; toolbox: 3 step row(s)

$ python3 -c "import ast,glob; [ast.parse(open(f).read(),f,feature_version=(3,9)) for f in glob.glob('framework/tools/*.py')+glob.glob('tools/*.py')]; print('py39 syntax OK')"
py39 syntax OK

$ PYTHONDEVMODE=1 PYTHONWARNINGS=error python3 -X dev tools/check_all.py > check6.log 2>&1; echo "exit $?"; tail -3 check6.log; grep -c "^== " check6.log; grep -ci warning check6.log
exit 0
   refused: archify CLI not found; install with: python3 framework/tools/archify_delta.py install   (or: npx skills add tt-a1i/archify -g)

ALL CHECKS PASSED
207
0

$ python3 /mnt/user-data/outputs/github-readme-writer/lint.py README.md
OK — README.md: 27 headings, 1638 body words; every link and anchor resolves.

$ grep -ci "must-fix" docs/plans/2026-09-11-breakdown/challenge.md; tail -1 docs/plans/2026-09-11-breakdown/challenge.md
2
Must-fix findings open: 0.
```

## Phase 7 — Live trial on the owner's Mac

Scope: none in the repo.

- [ ] `new_product.py` a fresh folder; large request "a habit tracker: log a habit, see a weekly streak, get a reminder" through Claude Code; PM confirms or edits the breakdown; child 1 to `deliver.done`; `--group` continues.
- [ ] Removal request on the same product ("remove reminders") through `impact` and `confirm-impact`; the kept dependant still passes `verify`.
- [ ] Findings written to `DECISIONS.md` as "first live run"; owner decides keep, adjust thresholds, or revert per phase.

## Completion

All phases `[x]`; `check_all.py` green on Python 3.9; owner commits and pushes with the message `Define: breakdown of large requests and impact of removals (PLAN 2026-09-11, phases 0-7)`.
