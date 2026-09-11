# Plan: large requests, and removals or breaking changes

Status: proposed, not executed. Execution follows `EXECUTION.md` in this folder, one phase at a time, each phase proven before the next begins. Nothing in the engine changes until Phase 1 starts.

## 1. The two problems

**P1 — a large request.** A request naming several capabilities, several user roles, or a whole product enters `define.intake` as one record and is discussed, written and challenged as one node. Only a *document* (PRD, notes) is split into one record per request today. A large spoken request produces one oversized node, or a split the Writer makes on its own with no PM confirmation of the chunks or their order.

**P2 — a removal or breaking change.** When the PM asks to remove a capability or change one that others depend on, the framework retires the node and, later, the challenger lists "affected nodes" and `trace` finds affected code. The repercussions are discovered piecemeal and after the decision; the PM is never shown "if you remove X, Y stops working; your options are…; recommended…" before choosing. Dependants are protected only by their tests failing at `verify`.

## 2. Outcome the PM sees

- A small addition: unchanged — intake, discuss, approve, plan, accept.
- A large request: one extra stop after the discussion. The AI shows the chunks it proposes, why the lines are there, what each depends on, and a recommended order with reasons. The PM confirms, merges, splits, reorders or drops chunks in words, or says "one thing". Each chunk then runs as its own record with its own gates, in the confirmed order; the queue shows the group's progress. If building an early chunk shows the split was wrong, any chunk's discussion sends the group back to the same confirmation stop with the proposed correction.
- A removal or breaking change: one extra stop after the discussion. The AI shows what is removed, every dependant (from the tree, the tags and the glossary, never guessed), what stops working for a user, the options per dependant with one recommendation, and what happens to stored data. The PM chooses per dependant in words. The AI then executes the confirmed set without further questions, and `verify` proves the dependants still work as chosen.

## 3. Design

### 3.1 New and changed steps in `workflows/define.yaml`

| Step | Type | Owner | Change |
|---|---|---|---|
| `sort` | decision | AI | Exits unchanged. The sort reason states whether the request is *large* (several capabilities, several user roles, or a whole product) and whether it is *breaking* (names a delivered node or rule with dependants, or removes one). Both flags feed `discuss`; neither routes. |
| `discuss` | decision, PM | PM | Two new exits: `breakdown` ("several capabilities; propose the chunks") and `impact` ("this removes or changes something others depend on; show the repercussions"). A child record's discussion gains `revise-breakdown` ("building this chunk showed the split or the order is wrong"). Existing exits stay: write, to-fix, confirm-exists, to-foundation, drop. |
| `breakdown` | step | AI (Writer) | New. Writes the breakdown section (3.3). Next: `confirm-breakdown`. Refused while no architecture file exists (E6). |
| `confirm-breakdown` | decision, PM | PM | New gate. Exits: `spawn` (yes), `breakdown` (merge, split, reorder or drop chunks; the PM's words drive the rewrite; three rounds, then only `write` or `drop`), `write` (one thing after all), `drop`. |
| `spawn` | step | AI (Sorter) | New. Creates one child record per confirmed chunk, in order, each with `parent`, `chunk`, `depends_on`; chunk 1 at `define.discuss`, others `waiting`; group block in `changes/QUEUE.md`; breakdown decision written. Refuses two chunks on one node without a dependency (E5). Next: `broken-down`. |
| `broken-down` | end | — | New end for the parent; the queue tracks the group. |
| `revise-breakdown` | step | AI (Sorter) | New; reached from a child's `discuss`. Writes the proposed correction into the parent, reopens the parent at `confirm-breakdown` with old vs proposed, pauses the child (`waiting_on: parent`). Next: `handed-over`. |
| `impact` | step | AI (Writer) | New. Writes the impact section (3.4) from the tree, the code tags, the glossary and the decision log. Next: `confirm-impact`. |
| `confirm-impact` | decision, PM | PM | New gate. Exits: `write` (proceed with the chosen set: the removed node marked retired plus each dependant's chosen treatment, as one node set), `impact` (revise the analysis or the options; three rounds, then `write` or `drop`), `breakdown` (the chosen treatments need a replacement built first — the set becomes chunks, replacement before removal), `drop`. |

Unchanged: `write`, `challenge`, `approve`, `commit`, Deliver, Foundation, the three existing gates, the runner contract, `commit.py`, every refusal that exists today. Small requests never see the new steps.

### 3.2 Doubt rules (written into the step notes)

Breakdown:
- Propose a split when the discussion names more than one capability, more than one user role, or a whole product; when in doubt propose one and let the PM say "one thing".
- Every chunk is a capability a user could see delivered on its own; a purely technical layer is folded into the capability that first needs it.
- Order: dependencies first; among independent chunks, the one that de-risks the rest (a rule, a shared term, an integration) before the one with most user value; every position carries its reason.
- More chunks than the PM can hold in one reading means the request is a document: say so and offer the PRD path (one record per request, no group).
- Two chunks touching one node share an explicit dependency; the second waits for the first's delivery.
- Foundation first: a whole-product request with no architecture file goes to Foundation as today; the breakdown is proposed only when Foundation has returned to `discuss`.

Impact:
- Dependants come from the logic tree (nodes that name the node or its glossary terms), the code tags (`@node`), and active decisions; never from memory. A dependant the AI cannot trace to one of these is listed as "possible, unverified".
- For every dependant, the options are: retire it too; keep it by replacing what it needed (a replacement chunk); narrow the removal so it keeps working; postpone. One recommendation, one reason.
- Stored data affected by the removal is named with the choice keep / migrate / delete, and the PM chooses; "delete" is never the default.
- A removal whose dependant is mid-Deliver is refused until that record closes (one change in flight per node).
- A rule removal follows the Foundation path; `check-rule` writes the same impact section against delivered nodes that rely on the rule.

### 3.3 The breakdown section (parent record)

```
## Breakdown — proposed <date>
Chunks:
  1. <slug> — <one-line capability, PM's words where possible>
     depends on: none | chunk <n> | rule <name> | delivered node <id>
     why this line: <one sentence>
  2. …
Order and reasons: <one line per position>
Not split further because: <one sentence>
Alternatives considered: <a coarser split; a finer split; a different first chunk>
```

The PM's answer is appended verbatim under `## Breakdown — PM answer`; a rewrite appends a new proposed block, never edits the old one.

### 3.4 The impact section (record)

```
## Impact — proposed <date>
Removing or changing: <node id> — <what the user loses or what changes>
Dependants (source in brackets):
  1. <node id> [tags: code/<system>/<component>/…; tree: names "<term>"]
     what stops working: <one sentence, from the user's side>
     options: retire it too | keep it by <replacement> | narrow the removal to <…> | postpone
     recommended: <option> — <reason>
  2. …
Rules and decisions affected: <rule or D-<nnnn>, and how>
Stored data: <table or field> — keep | migrate to <…> | delete; recommended: <…>
Possible, unverified: <anything the AI suspects but cannot trace>
```

The PM's answer is appended under `## Impact — PM answer`, one line per dependant; `write` then drafts the node set from it.

### 3.5 Records, queue, decisions

- Child front matter: `parent`, `chunk`, `depends_on`; `start` refuses a record with `parent` (E10).
- `changes/QUEUE.md` gains a group block per parent: parent title; chunks in order with each one's step; in flight; waiting-on; "n of m delivered".
- `next` on a waiting child states the wait; `advance` on it is refused until the named chunk is at `deliver.done` (or dropped → E3).
- Breakdown and impact answers are decisions (`decision-log.md` format): category `product`, `at_step` the gate, `## Decision` = the confirmed set, `## Reasons` with "Instead of …" lines from the rejected options. A revision supersedes.
- A child at `deliver.done` or `dropped` updates the group block and unblocks the next chunk.
- Delivered chunks are never touched by a revision; removed chunks are dropped with the reason; new chunks get new files.

### 3.6 Runner

`run.py` stops at `confirm-breakdown` and `confirm-impact` as at any PM step. One addition: `run.py --group <parent>` continues with the next unblocked child after a child reaches `deliver.done`; without the flag it stops after the child. A waiting child is a PM-visible stop (exit 3 with the wait reason). `/speckit-run` gains `--group`.

## 4. Edge cases

| # | Case | Handling |
|---|---|---|
| E1 | PM says "one thing" at `confirm-breakdown` | Exit `write`; single node; the proposal stays as history; decision "not split; instead of …". |
| E2 | PM merges, splits, reorders | Exit `breakdown` with the PM's words; rewrite; back to the gate; three rounds then only `write` or `drop`. |
| E3 | A chunk is dropped at its own gate | Dependants return to waiting; group block shows it; parent decision superseded by a note; next unblocked chunk proceeds; all dropped → group closes dropped. |
| E4 | Split found wrong mid-build | `revise-breakdown`; child pauses; parent reopens with old vs proposed; on confirm `spawn` reconciles: existing children keep files and history, new chunks new files, removed chunks dropped with reason, order rewritten. Delivered chunks untouched. |
| E5 | Two chunks on one node | `spawn` refuses without an explicit dependency between them. |
| E6 | No architecture file | Unchanged `sort → to-foundation`; `breakdown` and `impact` refused until it exists; Foundation returns to `discuss`. |
| E7 | Too many chunks | Doubt rule: the section says "this is a document" and offers the PRD path; the PM drops this record and resubmits as a document, or the AI does the document split from it. |
| E8 | New chunk added later | Normal intake; if `sort` sees it belongs to an open group, `discuss` proposes `revise-breakdown` on the parent. |
| E9 | Runner on a waiting child | `next` states the wait; `run.py` exits 3 with it. |
| E10 | Child started by hand | `start` refuses: "children are created by define.spawn; run the parent". |
| E11 | Parent missing or edited by hand | `check`/`next` on a child refuse when the parent file or its PM-answer block is missing, naming the file. |
| E12 | Lanes | Each child's lane set at spawn from chunk size (small: one node, no component); the parent is always full. |
| E13 | Renderer | New steps drawn from the YAML; validator rules 1–8 hold: `broken-down` is an end; `revise-breakdown` exits only to `handed-over`. |
| E14 | Existing products | No group, no change; `check` CLOSED after copying the new workflows; a `QUEUE.md` without group blocks is valid. |
| E15 | Removal with no dependants | No impact stop; `write` retires the node as today; the sort reason says "no dependants found (tags, tree, glossary)". |
| E16 | PM keeps a dependant that needs a replacement | `confirm-impact → breakdown`: the set becomes chunks with the replacement ordered before the removal; then the breakdown machinery applies. |
| E17 | Rule removal | Foundation path; `check-rule` writes the impact section against delivered nodes relying on the rule; the PM chooses at Foundation's existing gate. |
| E18 | Dependant mid-Deliver | Removal refused until that record closes; the record waits in the queue on it. |
| E19 | Stored data | Impact section names each store; PM chooses keep / migrate / delete; "delete" never defaulted; the plan carries the migration as tasks. |
| E20 | Impact analysis misses a tagged dependant | `challenge` (existing) compares the impact section against the tags and reports the omission as a finding before `approve`. |
| E21 | PM overrules the recommendation | Their choice is recorded as the decision with the recommendation as "instead of"; no re-argument. |

## 5. What does not change

Deliver and Foundation workflows, the three existing PM gates, the runner's contract, `commit.py`, `archify_delta.py`, the decision-log format, `install_commands.py`, `new_product.py`, every existing refusal.

## 6. Acceptance for the whole plan

1. `validate.py` OK; `orchestrate.py check` CLOSED with the new step count (51 → 58); `check_all.py` green on Python 3.9 syntax.
2. Fake-harness: large request → breakdown → confirm(yes) → spawn → three children → child 1 to `deliver.done` → `--group` continues → child 2 at `discuss`; queue shows "1 of 3 delivered".
3. Fake-harness: removal with two dependants → impact → confirm (retire one, keep one via replacement) → `breakdown` → replacement chunk before removal chunk → both delivered; `verify` runs the kept dependant's tests.
4. Fake-harness: E1, E2 (three rounds), E3, E4, E5, E9, E10, E11, E15, E18, E20 each end in the stated refusal or state.
5. `studio.html` renders Define with the new steps, badges correct, no overlaps (screenshot reviewed).
6. Docs agree with the YAML (`framework/README.md`, `steps.md`, `change-record.md`, `decision-log.md`, `orchestration/README.md`, `DECISIONS.md`, `test-cases.md` §T, `README.md` counts and worked example); lint OK.
7. Challenger pass with zero must-fix findings.
8. Live trial on the owner's Mac: one large request and one removal, through Claude Code.

## 7. Backlog acknowledged, not in this plan

Recorded so nothing discussed is lost: executable test-cases (pytest), live record status in `studio.html`, stalled-record report (`status --stale`), decision-supersede flow exercised live, slash commands verified inside Claude Code end to end, ECC comparison run (toolbox exists; comparison pending).
