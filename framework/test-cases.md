# Test cases for the framework

The regression suite for the workflows. Every case is run against the
current `workflows/*.yaml` and gets one verdict:

- **PASS** — the workflows handle it as written (path given by step ids).
- **PASS, wasteful** — handled, but through more steps than the case deserves.
- **PARTIAL** — handled only by a convention in `framework/`, or with a weakness named.
- **GAP** — not handled; a proposal in the last section addresses it.
- **By design** — deliberately outside the framework; a decision for the PM, not a fix.

Cases marked **(Rira)** were given by him on 2026-09-09; the rest complete
each category. Re-run this file after every workflow change; a verdict that
flips is the signal. (Checked by a challenger pass on 2026-09-09; its
corrections are folded in.)

**Status:** sections A–K record the verdicts and step paths *as they were
before* the change sets of 2026-09-09; they are kept as the audit trail
(step names such as `covered`, `criteria`, `preview`, `waiting` no longer
exist). Section N is the current re-run: every case A–M with its verdict
against the workflows as they stand. Read N for the truth, A–M for the
history.

Note: the framework has three workflows (define, foundation, deliver); the
map is a view of them, not a fourth.

## A. Foundation and architecture

| # | Case | Verdict | Path / why |
|---|---|---|---|
| A1 **(Rira)** | Paste the entire architecture in one go | PASS | `define.intake → covered → to-foundation → foundation.new-or-change → architecture → glossary → save → ready → define.discuss`. |
| A2 **(Rira)** | Add a new technology later | PASS | `define.intake → covered → to-foundation → foundation.new-or-change → propose-rule → impact → deliver.trace → plan → challenge-plan → approve-plan → execute → verify → passes → preview → accept → commit` (rule written here) `→ was-rule → resume-define → define.discuss`. |
| A3 **(Rira)** | Replace an existing technology | PASS, weak | Same path. Weak: impact may cover most of the code and one preview must judge it all. See P7. |
| A4 | Remove a technology or rule | PASS | Same path; the proposal is a removal. |
| A5 | Change a rule with no code impact (naming, a process rule) | PASS, wasteful | Same path; trace finds nothing; plan says "no code changes". Weakness shared with A2/A4: for a rule delivery that touches no node, `passes` and `accept` have no criteria to judge against. P8 defines what accept means for a rule. |
| A6 | Architecture file contradicts itself | GAP | Nothing reads the file for contradictions when it is written (`save`) or changed (`propose-rule`). P8. |
| A7 | Architecture omits how to run the product | PARTIAL | Required by `foundation.architecture`, noticed only at `deliver.preview`. P8. |
| A8 | Architecture names a tool the AI cannot use | PARTIAL | Found at `deliver.execute` at the earliest. P8. |
| A9 | Stale architecture pasted from another product | PARTIAL | Only surfaces as conflicts in `define.challenge`. P8. |
| A10 | Third-party keys and secrets | GAP | The architecture names tools; nothing says where secrets live or how a PM who never opens code supplies one. P8 adds "where secrets live and how the PM provides them" to the architecture file's required content. |

## B. Business-logic tree

| # | Case | Verdict | Path / why |
|---|---|---|---|
| B1 | New top-level capability | PASS | `define.discuss` decides where it sits. |
| B2 | New sub-flow under an existing capability | PASS | Same. |
| B3 **(Rira)** | Which parent, or a new header? | PARTIAL | Discussed, but nothing makes the AI propose a placement with a reason or checks the tree stays readable. P3. |
| B4 | Move a node to another parent | PARTIAL | Allowed by convention (id stable); no step names it. P3. |
| B5 | Split or merge nodes | PARTIAL | Works by composition (two Define passes plus a retirement); nothing proposes it. P3 adds "node too large: propose a split". |
| B6 | Retire a capability | PARTIAL | A node updated to "this no longer exists" flows through Deliver and its tagged code is removed. Missing: marking the node retired in the tree, children of a retired parent, code tagged by several nodes. P4. |
| B7 | New node conflicts with an existing one | PARTIAL | `define.challenge` reports it and fixes the draft, but if the *existing* node must change, nothing routes that; it needs its own Define pass. P3 adds "conflict with an existing node → the PM is told which node to revise next". |
| B8 **(Rira)** | KT: a new person reads the tree and understands the business | PARTIAL | The tree (one file per node, nested, plain language, criteria) is the KT document by design; `changes/` is the history. No overview is generated. P9. |
| B9 | Cross-cutting logic (audit, permissions) touching many nodes | PASS, weak | One node, many tags; the plan is large. P7. |
| B10 | Same node changed by two requests at once | GAP | Nothing sequences. P5. |
| B11 | A request that is really two capabilities | PARTIAL | `discuss` can split it, but the second node has no entry unless restated at intake. P5's queue holds it. |
| B12 | Request contradicts an existing node | PARTIAL | Same as B7. |
| B13 | UI copy change ("rename the button") | PASS, wasteful | Full loop for one string. Accepted cost: it is a logic change (the node's text changes), and the loop is the guarantee. |
| B14 | Localisation, second language | PARTIAL | Glossary is "one meaning each" in one language; nothing models translated copy. Out of scope until a product needs it; then a rule in the architecture file and criteria per language. |

## C. Many people, timing, sequencing

| # | Case | Verdict | Path / why |
|---|---|---|---|
| C1 **(Rira)** | 56 people change many documents | By design | One PM, one AI. Others submit requests at `define.intake` ("a request from anyone"); only the PM decides and writes. If people edit logic files directly, nothing sees it. **Decision for Rira:** one PM as the sole writer (recommended), or roles. |
| C2 **(Rira)** | When does development start? | PASS | At `define.commit → to-deliver → deliver.trace`, immediately. |
| C3 **(Rira)** | Can several approved nodes be built together? | PARTIAL | `deliver.plan/verify/commit` already speak of "every node it touches"; only `define.to-deliver` and the trigger are singular. P5 lets the handoff carry several nodes and fixes the record naming. |
| C4 | Change B depends on change A | GAP | Nothing orders deliveries. P5. |
| C5 | Several approvers (PM + compliance) | By design | One PM. Same decision as C1. |
| C6 | PM is away; requests pile up | PARTIAL | Nothing executes without the PM, but waiting is not modelled (`intake` has one exit). P5. |

## D. Interruptions and resume

| # | Case | Verdict | Path / why |
|---|---|---|---|
| D1 **(Rira)** | Server or session dies mid-`execute` | PARTIAL | Convention: status line in the change record; uncommitted work in the working copy. Not stated whether a step's partial output survives. P6. |
| D2 **(Rira)** | Resume or start from scratch? | PARTIAL | With P6: resume from the last completed step. |
| D3 **(Rira)** | Is data lost? | PARTIAL | Nothing committed is lost. With P6 the loss is bounded to the current step. |
| D4 | AI context lost (new session) | PARTIAL | Status line + files; `framework/README.md` is the re-entry point. P6. |
| D5 | Interrupted during `deliver.commit` | PARTIAL | A git commit is atomic (git is a convention, hence PARTIAL). |
| D6 | PM wants to stop a change midway | GAP | Between `approve-plan` and `preview` the PM has no node to act on, and `accept` has no "drop" exit. P10. |
| D7 | A preview the PM cannot run (nightly job, API-only, needs production data) | GAP | `preview` assumes click-through; `accept` has no "cannot preview" answer; dead end at the last gate. P10 adds: the AI shows evidence (test output, logs, a recorded run) and the PM accepts on evidence; `accept.input` names both forms. |

## E. Code quality and hallucination

| # | Case | Verdict | Path / why |
|---|---|---|---|
| E1 **(Rira)** | Built "the right way, the latest way"? | GAP | Nothing consults current documentation or practice. P2. |
| E2 | AI invents a library or API | PARTIAL | Tests fail at `verify`. P2 catches it at plan time. |
| E3 | Tests written to pass rather than to check | PASS | `deliver.verify` is a second pass against the criteria, "not against the plan"; fresh context by convention. |
| E4 | Unverifiable criteria ("feels fast") | PASS | `define.challenge` reports "criteria that cannot be verified". |
| E5 | Security, accessibility, performance rules | PASS if written | `verify` checks architecture rules; an unwritten rule is never checked. P8 makes these required sections of the architecture file. |
| E6 | Performance regression in an untouched node | GAP | `verify` scopes to touched nodes. P2 adds: the whole test suite runs at verify, not only the touched nodes' tests. |
| E7 | Code drifts from tags | PARTIAL | Convention: untagged code is a finding. |
| E8 | Plan promises more than the node justifies | PASS | `deliver.challenge-plan`. |
| E9 | AI proposes an improvement the PM did not ask for | PARTIAL | Blocked from plans by "nothing is invented"; the only channel is `intake`. P5 states it: the AI may add a request to the queue, marked as its own; the PM decides at intake like any other. |

## F. Foundation change requested from the business side

| # | Case | Verdict | Path / why |
|---|---|---|---|
| F1 **(Rira)** | Capability needs a new rule; does the loop resume? | PASS | A2's path ends at `resume-define → define.discuss`. |
| F2 | Rule dropped in Deliver | PASS | `deliver.drop` discards it; PM restates the request if wanted. |
| F3 | Rule revised twice | PASS | `back-to-foundation → foundation.propose-rule → impact`. |
| F4 | Rule change arrives while a node is mid-delivery | GAP | P5. |
| F5 | Capability turns out not to need the rule | PASS | Drop, restate, `covered` says yes. |

## G. After delivery

| # | Case | Verdict | Path / why |
|---|---|---|---|
| G1 | Bug: code does not do what the approved node says | PASS, wasteful | Enters at intake, re-approves unchanged logic, then Deliver. P1 is an economy: a direct path when the PM names a failing criterion of a delivered node. |
| G2 | Bug that reveals the logic was wrong | PASS | A logic change: Define. |
| G3 | Roll back a delivery | PASS, wasteful | Restate at intake "return to the previous behaviour" → new node version → Deliver, where execute reverts the commit. No new path needed. |
| G4 | External dependency changes | PASS | A2 or G1 depending on what breaks. |
| G5 | PM changes mind after acceptance | PASS | New request at intake. |
| G6 | Urgent change, no time for the loop | By design | Every gate is a PM decision answerable in minutes; there is no bypass and should not be. |
| G7 | Dependency or security patch: no logic change, no rule change | GAP | `covered` says yes, `discuss` has nothing to discuss, no node to version. P1 covers it: the same direct path as a bug, with "keep behaviour, update dependency" as the reason. |
| G8 | Non-visible behaviour (analytics events) | PARTIAL | Plan says "what changes for the user"; the PM cannot click through an event. P10's evidence-based accept covers it. |

## H. Operating and visibility

| # | Case | Verdict | Path / why |
|---|---|---|---|
| H1 | Where are we right now? | PARTIAL | Status line in the latest change record. P5 makes one queue file the single place. |
| H2 | What did we build for node X, and when? | PASS | Change records name node versions; history. |
| H3 | Why does the code do Y? | PASS | Tag → node → description and criteria. |
| H4 | How long will a change take? | By design | No estimation. |
| H5 | Which requests wait, in what order? | GAP | P5. |

## I. Data and release

| # | Case | Verdict | Path / why |
|---|---|---|---|
| I1 | Change alters stored data | PARTIAL | Covered only if a criterion says so; nothing requires the plan to state it. P2. |
| I2 | "Delivered" means committed and previewed, not live | By design | Release is not modelled. **Decision for Rira:** add a release step after commit, or keep release outside. |

## J. Requests that already exist, or cut across the tree

| # | Case | Verdict | Path / why |
|---|---|---|---|
| J1 **(Rira)** | PM sends an idea whose logic already exists | PARTIAL | Only `define.challenge` (after write) reports a conflict; nothing at intake says "this exists as node X, nothing to do". P12. |
| J2 **(Rira)** | PM sends an idea whose logic exists partly | PARTIAL | Same; should become "change to node X". P12. |
| J3 **(Rira)** | The new case contradicts existing cases anywhere in the tree; PM must be told which | PARTIAL | `challenge` reports conflicts but only fixes the draft; the affected nodes are not listed for the PM, and the loop (discuss → write → challenge → approve until agreed) exists only for the new node. P3 + P15. |
| J4 **(Rira)** | A drastic change touching many business cases, on both sides | GAP | One node per Define pass; one node per delivery unless batched. No business-side impact trace (which other nodes change if this one does). P15. |
| J5 **(Rira)** | Business ideas saved separately, one per file | PASS by convention | One file per node under `logic/`; ideas not yet defined live only in the queue (P5) → P13 makes every request a file from intake. |
| J6 **(Rira)** | Intake categorises the request into a next step, same workflow | GAP | `intake` has one exit. P1 + P12 make it the routing decision: new logic / change to node X / already exists / code wrong or patch / needs foundation / cross-cutting set. |

## K. Code-side structure

| # | Case | Verdict | Path / why |
|---|---|---|---|
| K1 **(Rira)** | One request builds a huge codebase instead of components | GAP | Nothing constrains how code is organised; `execute` says "inside the architecture rules", but the architecture file has no required structure section. P14. |
| K2 **(Rira)** | Reuse an existing component instead of rewriting | GAP | `trace` finds code by node tag only; it never searches for an existing component that does the job. P14. |
| K3 **(Rira)** | Frontend, backend, services in separate places | GAP | `code/` is flat by convention. P14. |
| K4 **(Rira)** | Environment variables, infrastructure, secrets | GAP | Not stored anywhere named. P14 (architecture file section: systems, environments, where env vars and secrets live; never in logic files or change records). |
| K5 **(Rira)** | Readable by an AI agent reviewing the code | PARTIAL | Tags give logic → code. No code → overview. P14's generated component index. |
| K6 **(Rira)** | Documentation on both sides, including built use cases | PARTIAL | Business side: nodes (criteria are the use cases), change records, P9 tree index. Dev side: only tags. P14's component index is the dev-side document; nothing is hand-written on either side beyond what the workflows already produce. |

## Node-by-node review

Question at every node: cut, merge, or make cheaper for the PM, without losing a guarantee.

### define (pre-change: 12 steps, PM touchpoints intake, covered, discuss, criteria, approve; now 15 steps, touchpoints intake, confirm-exists on that path only, discuss, approve)

- `intake` — keep; entry. P1 adds the bug/patch exit (a new handoff step, since a decision cannot carry `to`).
- `covered` — **make AI-owned** (P11). It is a fact check; the PM only needs to hear the answer, which arrives at `foundation.new-or-change` or `discuss`. Removing `input` removes the gate. (Merging it into `intake` would not: the entry must carry `input`.)
- `to-foundation`, `waiting` — keep.
- `discuss` — keep; where the PM's content comes from.
- `write` — keep. P3: proposes placement.
- `criteria` — **merge into approve** (P11), with one safeguard: if the PM changes criteria at `approve`, the node goes back through `challenge` (new exit), so criteria the PM added are still checked for verifiability before saving. This keeps E4 a PASS and makes a one-word criteria tweak cheap (approve → challenge → approve), which today costs discuss + write + criteria + challenge + approve.
- `challenge` — keep.
- `approve` — keep; absorbs criteria; gains the re-challenge exit.
- `commit`, `to-deliver`, `done` — keep.

After P1 + P11: 12 steps (−covered as gate, −criteria, +bug handoff), PM decisions 3 → 1 (`approve`), PM touchpoints 5 → 3 (intake, discuss, approve).

### foundation (8 steps, PM touchpoints: new-or-change, architecture, glossary, propose-rule)

- `new-or-change` — **make AI-owned** (P11): the answer is already known from `covered`'s condition. Foundation keeps `input` on architecture, glossary, propose-rule, so it stays valid.
- `architecture`, `glossary` — keep.
- `save` — keep; P8 adds the architecture challenge with an exit back to `architecture` for findings the PM must resolve.
- `ready` — keep.
- `propose-rule` — keep; P8 challenges the proposal too.
- `impact`, `done` — keep.

### deliver (18 steps, PM touchpoints: approve-plan, preview, accept)

- `trace` — keep; P1 adds the bug input case.
- `plan` — keep. P2: consults current documentation; sources recorded in a non-PM section of the record (the PM's section stays code-free); states what happens to existing data.
- `challenge-plan` — keep.
- `approve-plan` — keep; the gate that never goes.
- `execute` — keep. `verify` — keep; P2: whole suite runs. `passes` — keep; third exit becomes `accept`.
- `preview` + `accept` — **merge** (P11): `accept` becomes "PM accepts after using it, or on evidence when it cannot be used" (P10). The AI's duty to run the product and guide the PM moves into `accept.what`.
- `commit`, `was-rule`, `resume-define`, `drop`, `back-to-define`, `back-to-foundation`, ends — keep. P10 adds `accept → drop` ("PM stops the change").

After P11: 17 steps, PM touchpoints 3 → 2 (approve-plan, accept), decisions unchanged at 2.

### Across the system, ordinary change

Today: 8 PM touchpoints (intake, covered, discuss, criteria, approve, approve-plan, preview, accept). After P11: 5 (intake, discuss, approve, approve-plan, accept), of which 3 are decisions. Each remaining decision holds one guarantee: `approve` — no code for unagreed logic; `approve-plan` — no code without a plan the PM said yes to; `accept` — nothing done the PM has not seen work. AI-only checks stay at three (challenge, challenge-plan, verify) and are the reason three PM decisions suffice.

## Proposed changes

| # | Change | Fixes | Safety (challenger) |
|---|---|---|---|
| P1 | `define.intake` becomes the entry decision with three answers: new or changed logic → `covered`; foundation missing or rule needed → `to-foundation` (folding `covered` here is not allowed: see P11); **existing logic, code wrong, or a dependency patch** → new handoff `to-deliver-fix` → `deliver.trace`, carrying node id, the failing criterion and what was observed. Guard: only when the PM names a criterion of a delivered node; otherwise it is a logic change. `deliver.trigger` and `trace` gain the third input case. | G1, G7 | Safe with the guard and the handoff step. |
| P2 | `deliver.plan` consults the current documentation of the tools the architecture names; sources go in a non-PM section of the change record; the plan states what happens to existing data. `deliver.verify` runs the whole test suite and checks the touched code against the same sources. | E1, E2, E6, I1 | Safe once sources are kept out of the PM section. |
| P3 | `define.write` proposes the placement (existing parent or new header, with reason) and, if the node is too large, a split. `define.challenge` checks the tree stays readable and, on conflict with an existing node, names the node the PM must revise next. | B3, B4, B5, B7, B12 | Safe. |
| P4 | Retirement: a node can be marked retired in Define; Deliver removes code tagged only by retired nodes; children are retired with the parent; the node stays in the tree marked retired with the date. | B6 | Safe. |
| P5 | One file `changes/queue.md`, committed on every change: waiting requests in order (including any the AI added, marked as its own), the one change in flight, and dependencies between nodes. One change in flight per node; a waiting request does not count as in flight. Batching: at `define.approve` the PM may say "deliver with <node>", and `to-deliver` carries several nodes; records are then named by the batch. If a dependency is dropped, its dependants return to waiting. | B10, B11, C3, C4, C6, E9, F4, H1, H5 | Safe. |
| P6 | Every step writes its output to disk before the next step starts; resume reads the queue's status and redoes only the current step. | D1–D4 | Safe. |
| P7 | A rule change too large for one preview is split into several change records. The rule is written with the **first** record, annotated with the nodes still to be brought under it; each later record removes its nodes from the annotation; `was-rule → resume-define` fires only when the annotation is empty. | A3, B9 | Safe in this form. (Writing the rule with the last record would let code be verified against a rule not yet in the file: rejected.) |
| P8 | Architecture challenge at `foundation.save` (new file) and `foundation.propose-rule` (change): contradictions, run instructions, tools the AI can reach, where secrets live and how the PM supplies them, security/accessibility/performance rules present. `save` gains an exit back to `architecture` for findings the PM must resolve. Also defines what `accept` means for a rule delivery that touches no node: the PM accepts on the evidence that every tagged piece still passes its criteria. | A5–A10, E5 | Safe. |
| P9 | A generator for a logic-tree index from `logic/`, like `steps.md`: the KT document. | B8 | Safe; tooling only. |
| P10 | `accept` gains "PM stops the change" → `drop`; a stop before `define.commit` discards the draft; a stop during Foundation follows the rule-discard path. `accept.input` becomes "the PM's own use of the changed flow, or the evidence shown when it cannot be used, and their answer". | D6, D7, G8 | Safe. (Rollback clause removed: rollback is G3, no new path.) |
| P11 | `covered` and `foundation.new-or-change` become AI-owned decisions (no `input`); `criteria` merges into `approve`, which gains the exit "PM changed criteria → challenge"; `preview` merges into `accept`. | 8 → 5 PM touchpoints | Safe with the re-challenge exit. |

| P12 | Duplicate check at intake: the AI searches the logic tree for nodes covering the request before anything is discussed, and `intake` routes: already exists (PM told, node named, nothing built) / partly exists (becomes a change to that node) / new. | J1, J2, J6 | Safe; AI-owned check, PM hears the result. |
| P13 | The change record is born at intake, not at plan: every request becomes `changes/<id>.md` the moment it is stated, with a `status` line that follows it through every step, and the queue is the index of those files. Replaces `waiting.md`. | J5, H1, D1–D4 | Safe; simplifies P5/P6. |
| P14 | Code structure. The architecture file gains a required section "systems and structure": the systems (frontends, backends, services), the folder per system, the component convention, the environments, and where env vars and secrets live. `deliver.trace` also searches existing components for reuse; `plan` states reused vs new components; `challenge-plan` reports a new component that duplicates an existing one; `execute` builds components under `code/<system>/<component>/`, each tagged by the nodes it serves; a generator writes `code/components.md` (component → nodes → system), the dev-side document. | K1–K6 | Safe. |
| P15 | Cross-cutting change: a Define pass may cover a node set. `challenge` adds a business-side impact trace (every other node whose text or links reference the changed node, listed for the PM at approve). One approval covers the set; `to-deliver` carries the set; one change record. | J3, J4 | Safe with P5's multi-node handoff. |

**Decided by Rira (2026-09-09):** one PM, no roles (C1/C5); release to users is out of scope, the framework is build-only (I2).

**Applied 2026-09-09:** P1–P6, P8–P15. P7 is documented as a convention only.

| Cases | Expected after the change set |
|---|---|
| A6–A10, E5 | PASS (`foundation.check`, `check-rule`, required architecture content) |
| B3, B4, B5, B7, B12, J3 | PASS (`define.write` placement/split, `define.challenge` affected-nodes list) |
| B6 | PASS (retired nodes; `execute` removes code tagged only by retired nodes) |
| B10, B11, C3, C4, C6, F4, H1, H5, J5 | PARTIAL → by convention (record born at intake, queue, one in flight per node, dependencies) |
| D1–D4, D6, D7, G8 | PASS (each workflow states that every step writes to disk; `accept` takes evidence and has "stop"; `define.approve` has "stop") |
| E1, E2, E6, I1 | PASS (`plan` sources section, stored-data statement; `verify` whole suite and sources) |
| G1, G7, J1, J2, J6 | PASS (`define.sort`: exists / fix → `to-fix`) |
| J4 | PASS (node set, one approval, one record) |
| K1–K6 | PASS (systems and structure in the architecture file; components; `code/COMPONENTS.md`; `logic/INDEX.md`) |
| B8 | PASS (`logic_index.py`) |
| C1, C5, I2, G6, H4 | By design, decided |

## L. The system as an agent ("Jarvis")

Added 2026-09-09 after the second change set; verdicts are against the
current YAML.

| # | Case | Verdict | Path / why |
|---|---|---|---|
| L1 | PM asks a question ("what does the product do for refunds?", "where is my request?", "is deployment in scope?") | PASS | `define.intake → sort → answer → answered`; answered only from the written business side; "not written anywhere" rather than a guess. |
| L2 | PM pastes a PRD with many capabilities | PASS | `define.intake` splits it into one record per request, listed back; each is sorted. |
| L3 | The AI is unsure how to sort a request | PASS | `define.sort` notes: choose the path with more PM gates and say why at the next PM step. |
| L4 | The AI cannot do a task as planned (tool missing, API different from the docs) | PASS | `deliver.execute`: stop, record goes back to plan; no improvising. |
| L5 | A challenger pass finds nothing | PASS | `define.challenge`, `foundation.check`, `deliver.challenge-plan` notes: zero findings on non-trivial work → run again with a different framing. |
| L6 | A new AI (or a new session) takes over mid-change | PASS by convention | `AGENTS.md` card → `changes/QUEUE.md` → record's `status` and last saved output; every step writes to disk. |
| L7 | A different AI vendor takes over the product | PASS | Nothing is Claude-specific: role is `AI`; `AGENTS.md` is the cross-tool convention; `CLAUDE.md` just imports it. |
| L8 | PM asks for something out of scope (deploy to users) | PASS | L1: answered as out of scope from the framework's scope statement. |
| L9 | PM gives contradictory answers over time | PARTIAL | The logic delta at `define.challenge` shows the PM what changed against the delivered version, and the decisions ledger keeps rulings; nothing detects a contradiction with an earlier ruling automatically. Acceptable: the PM is the authority. |
| L10 | A rename or refactor with no behaviour change | PASS | A fix ("keep behaviour") through `define.to-fix`; verified against unchanged criteria. |
| L11 | The AI wants to improve something nobody asked for | PASS | It adds a request to the queue marked as its own; sorted like any other; never done silently. |
| L12 | A stale step: a node in a workflow that nothing can reach | PASS | Validator rule 8: every step of every workflow must be reachable from the system entry through handoffs; the exit must be reachable. |
| L13 | A step with no way to end | PASS | Validator rules 4–5 (every step reaches an end) and 8. |
| L14 | Two PM gates in a row for the same document | PASS | None remain: three PM gates per change, each on a different artefact (node, plan, running product). |

### What was adopted from current practice (2026-09-09)

Compared against Spec Kit (constitution / spec / plan / tasks), OpenSpec
(spec deltas, change folders), BMad (readiness gates, adversarial review
where zero findings halts) and Gangsta Agents (ledger, negative
constraints, "spec is law"), plus the AGENTS.md convention. Taken: a task
list in every plan, ticked at execute (resumable, reviewable); the logic
delta shown to the PM for every change; "zero findings is suspicious"; a
decisions ledger appended at commit; a never-do list in the architecture
file; an AGENTS.md card (short, exact commands, boundaries) with CLAUDE.md
importing it. Not taken: bypassable gates (Spec Kit, OpenSpec), autonomous
mode without approval (Gangsta), multi-persona pipelines (BMad) — one PM,
one AI with independent passes is simpler and holds the same guarantees.


## M. First-week cases (from the assumption challenger, 2026-09-09)

| # | Case | Verdict now | Path / why |
|---|---|---|---|
| M1 | The first request of a product is the architecture itself | PASS | `foundation.save → foundation-only → done`; the record is closed as delivered, nothing to discuss. |
| M2 | Bug reported as a symptom ("button does nothing"), no criterion named | PASS | `define.sort`: sorted as a fix when the AI can name the violated criterion; the PM overrules at `discuss` or `approve-plan`. |
| M3 | PM answers a gate with "yes, and also add X" | PASS by convention | Every PM message is an intake; the "also" becomes a new record (`intake.input`, AGENTS card). |
| M4 | "Show me the product as it is now" | PASS | `define.answer` runs the product using the run instructions. |
| M5 | Cancel or reorder a waiting request | PASS | A queue instruction at `define.sort` → `answer` applies it and confirms. |
| M6 | Change the meaning of a glossary term | PASS | `define.sort` notes: a cross-cutting change to every node using the term → `discuss` as a node set. |
| M7 | Small wording fix in the plan | PASS | `deliver.approve-plan` → "revise the plan" → `plan` → `challenge-plan` again. |
| M8 | Flaky test | PASS | `deliver.verify`: a test that fails once and passes on rerun is reported as flaky, not a failed pass. |
| M9 | PM must supply a secret before work can start | PASS | `deliver.plan` lists what the PM must supply; supplied with the "execute" answer at `approve-plan`. |
| M10 | PM messages while the AI is mid-execute | PASS | `define.intake` notes: taken in and queued; "stop" honoured at the next task boundary → `tasks-done` → `drop`. |
| M11 | Bug on a node with a change already in flight | PASS by convention | Waits in the queue; re-sorted when the node is delivered (`deliver.commit`). |
| M12 | Empty test suite on the first delivery | PASS | `deliver.verify`: a criterion with no test is a finding. |
| M13 | A question that was really a build request | PASS | `define.settled`: the PM turns it into a request → `sort`. |
| M14 | Foundation abandoned halfway | PASS | `foundation.check` / `check-rule` → `drop`; "not needed" → back to `discuss`. |
| M15 | A rule dropped after its impact check | PASS | `deliver.drop → was-rule-drop → resume-define → define.discuss`: the PM goes on within the current rules or stops; the capability is not lost. |
| M16 | Verified code the PM sees does not match | PASS | `deliver.accept` "not matching" → `plan` (the plan or tasks were wrong), not the same tasks again. |
| M17 | A task cannot be done as planned | PASS | `deliver.tasks-done` → `plan` with the reason in the record. |
| M18 | Wrongly sorted request | PASS | `define.discuss` redirects to fix / exists / foundation / stop; Foundation input steps can say "not needed" → `discuss`. |
| M19 | PM is away for a week | PARTIAL | Nothing executes; the queue shows PM-blocked count and dates (convention); the AI may add one request of its own. Nothing alerts the PM; out of scope. |
| M20 | Two Define passes on one document in a row | PASS, by design | Only `approve → challenge → approve` after a criteria edit; stated in `approve.notes`. |

## N. Re-run against the current workflows (2026-09-09, final)

Fresh verdicts for every case. Paths use current step ids; filenames are
`changes/QUEUE.md`, `code/COMPONENTS.md`, `logic/INDEX.md`.

| Cases | Verdict | Why |
|---|---|---|
| A1, M1 | PASS | `intake → sort → to-foundation → foundation.new-or-change → architecture → check → glossary → save → foundation-only → done`. |
| A2, A4, F1, F3, F5 | PASS | `… → propose-rule → check-rule → impact → deliver.trace → plan → challenge-plan → approve-plan → execute → tasks-done → verify → passes → accept → commit` (rule written) `→ was-rule → resume-define → define.discuss`. |
| A3, B9 | PASS, weak | Same path; a huge impact is split by the P7 convention (rule written with the first record). |
| A5 | PASS | Rule delivery with no node: `accept` judges the evidence that every tagged piece still passes. |
| A6–A10, E5 | PASS | `foundation.check` / `check-rule`; required content includes secrets, never-do list, run instructions, rules. |
| B1–B5, B7, B12, J3 | PASS | `discuss` places it; `write` proposes placement and splits; `challenge` lists affected nodes and names the node to revise next. |
| B6 | PASS | Retired node → `execute` removes code tagged only by retired nodes; `logic/INDEX.md` shows retired (inherited by children); `COMPONENTS.md` flags components served only by retired nodes. |
| B8 | PASS | `logic/INDEX.md` with status per node. |
| B10, B11, C3, C4, C6, F4, H1, H5, J5, M11 | PASS by convention | Change record born at intake; `QUEUE.md`; one in flight per node; dependencies; re-sort on delivery. |
| B13 | PASS, wasteful | Accepted: a copy change is a logic change. |
| B14 | Out of scope until needed | Rule in the architecture file, criteria per language. |
| C1, C5 | Decided | One PM. |
| C2 | PASS | `define.commit → to-deliver → deliver.trace`. |
| D1–D4 | PASS | Every workflow states "every step writes its output to disk"; every step has an `output` in the record, including PM answers and discussion notes. |
| D5 | PASS by convention | Git commit is atomic. |
| D6, M10 | PASS | Stop at `discuss`, `approve`, Foundation input steps, `approve-plan`, during execution (task boundary), `accept`. |
| D7, G8 | PASS | `accept` takes evidence. |
| E1, E2 | PASS | `plan` AI section: current documentation and sources; `verify` checks against them. |
| E3, E4, E8 | PASS | `verify` not against the plan; `challenge` reports unverifiable criteria; `challenge-plan`. |
| E6, M12, M8 | PASS | Whole suite; criterion without a test is a finding; flaky handling. |
| E7 | PASS | Untagged code is a finding in `verify`; `COMPONENTS.md` flags untagged components and malformed tags. |
| E9 | PASS | AI adds a request marked as its own; at most one while the PM is away (convention). |
| F2 | PASS | `drop → was-rule-drop → resume-define`. |
| G1, G7, L10, M2 | PASS | `sort → to-fix → deliver.trace` (bug with a nameable criterion, patch, refactor). |
| G2, G5 | PASS | Define. |
| G3 | PASS, wasteful | Restate at intake → new version → Deliver. |
| G4 | PASS | A2 or G1. |
| G6, H4 | By design | No bypass; no estimation. |
| H2, H3 | PASS | Records name versions; tags → nodes. |
| I1 | PASS | `plan`: what happens to stored data. |
| I2 | Decided | Build only. |
| J1, J2, J6 | PASS | `sort` → `confirm-exists` / change to node X / routing. |
| J4 | PASS | Node set with one approval; one record. |
| K1–K6 | PASS | Architecture file: systems and structure; `trace` reuse search; `plan` reused vs new; `execute` components; `COMPONENTS.md`; `logic/INDEX.md`. |
| L1, L2, L8, M4, M5, M13 | PASS | `answer` (from written sources incl. the framework scope; runs the product; queue instructions) → `settled`. |
| L3 | PASS | Doubt rule at `sort`, written into the record. |
| L4, M17 | PASS | `tasks-done → plan`. |
| L5 | PASS | Zero-findings rule at `challenge`, `check`, `check-rule`, `challenge-plan`, `verify`, with named framings and a definition of non-trivial. |
| L6, L7 | PASS | AGENTS card; `framework/` copied into the product repo; nothing vendor-specific. |
| L9 | PARTIAL | Logic delta and ledger; no automatic contradiction detection. Accepted. |
| L11 | PASS | Marked request in the queue. |
| L12, L13 | PASS | Validator rules 4, 5, 8. |
| L14, M20 | PASS, by design | One deliberate double reading after a criteria edit. |
| M3, M6, M7, M9, M14–M16, M18 | PASS | See section M. |
| M19 | PARTIAL | PM absence is visible in the queue, not alerted. Out of scope. |

Step counts now: define 18, foundation 14, deliver 19 (51 steps). PM
touchpoints per ordinary change: intake, discuss, approve, approve-plan,
accept (5); PM gates: 3.


## O. Decisions (2026-09-09)

| # | Case | Verdict | Path / why |
|---|---|---|---|
| O1 **(Rira)** | Log every important decision, any category, in a structured way | PASS | `decisions/<date>-<n>-<slug>.md` with id, timestamp + timezone, region, category (product/business/ui/frontend/backend/code/infra/software/process), made_by, at_step, record, nodes, links, resources, status; body = decision, situation, reasons. Written at `foundation.check`, `foundation.save`, `define.approve`, `deliver.approve-plan`, `deliver.accept`, `deliver.commit`, every `drop`. |
| O2 **(Rira)** | A new decision alters an earlier one: bring the earlier one forward with its situation and reasons before changing it | PASS | `foundation.propose-rule` (rule behind the current rule), `define.challenge` → `define.approve`, `deliver.plan` → `deliver.approve-plan`: the earlier decision is shown side by side; changed only on an explicit yes; then `supersedes` / `superseded_by`. `challenge` and `challenge-plan` report an alteration nobody brought forward. |
| O3 | "Why does the product do X?" | PASS | `define.answer` reads the decision log first. |
| O4 | A decision edited in place | PASS | The index fails on any change to an existing decision file other than adding `superseded_by` (git diff check), on deletion, and on a broken supersede chain. |
| O5 | An AI choice inside an approved plan (a library, a data shape) that nobody decided explicitly | PASS | `deliver.approve-plan` output: a decision entry, made_by AI, for each such choice; a later plan that changes it brings it forward. |
| O6 | The reason for an architecture rule written months ago | PASS | `foundation.save` writes one decision per rule; `propose-rule` brings it forward. |
| O7 | Two decisions contradict each other without one superseding the other | PARTIAL | The index flags broken chains, not semantic contradictions; `challenge` / `challenge-plan` catch them only when a draft touches both. Accepted. |
| O8 | Log too noisy to search | PASS | Threshold: a decision file exists only where an alternative was rejected ("Instead of" line, validated); rules and choices with nothing weighed against them stay in the file or record. |
| O9 | A dropped change leaves its decisions active | PASS | `drop` supersedes every active decision under the same record. |
| O10 | An AI's library choice altered later on a different node | PASS | AI decisions must name `resources`; the gate search runs on components touched, not only nodes. |


## P. Orchestration and commands (2026-09-10)

| # | Case | Verdict | Path / why |
|---|---|---|---|
| P1 **(Rira)** | Slash command names match Spec Kit so a move is seamless | PASS | `orchestration/commands.yaml`: 13 names identical to Spec Kit's, 6 ours with the same prefix, 2 refusing stubs; installer writes Spec Kit ≥ 1.0's skills layout per tool; names whose meaning differs say so. |
| P2 **(Rira)** | No open node anywhere | PASS | Validator rules 3–5, 8 + `orchestrate.py check` (every step has a role/mode; every command enters a real step; every exit resolves). |
| P3 **(Rira)** | The AI invents a next step | PASS | `advance` refuses any exit not in the YAML, any decision without its condition, any mismatched condition, any handoff exit but its target. |
| P3a | The AI starts a record at execute with `/speckit-implement` | PASS | `start` only for entry commands (define.intake); others continue a record already at their step or are refused. |
| P3b | The AI leaves a challenge without findings, or a gate without the PM's answer | PASS | `advance` refuses without `## Findings — <step>` / without `--answer`; zero findings with an unused framing → refused until `rerun`. |
| P3c | The AI changes the lane to skip reruns | PASS | `--lane` accepted only at start or leaving `define.sort`, logged in history. |
| P4 **(Rira)** | State of the agent system | PASS | Record front matter: step, lane, waiting_on, since, counters, role, mode, history; written only by the tool. |
| P5 **(Rira)** | Multi-agent | PASS | Six roles, one per step, fresh context, listed inputs only (`roles.yaml`). |
| P6 **(Rira)** | Challenger mode | PASS | `mode: challenger` steps return findings only; `rerun` walks the framings; small lane never reruns. |
| P7 **(Rira)** | Agent mode | PASS | `mode: agent` produces the step's output; `mode: auto` routes without AI or PM. |
| P8 **(Rira)** | No wasted re-review | PASS | Small lane (one paragraph plan, single challenge); delta-scoped re-challenge after revisions; three PM gates only. |
| P9 | Clarification cap | PASS | `define.write`: max three questions, one at a time, options with a recommended one; defaults listed as Assumptions. |
| P10 | Task grammar and coverage | PASS | `deliver.plan` T001 [P] [node] grammar with phases; `challenge-plan` coverage table, empty row = finding. |
| P11 | A different AI tool takes over | PASS | `install_commands.py --agent <tool>`; `next` tells it exactly where it is. |
| P12 | Fourth failed verification pass | PASS | The `passes → execute` edge is counted by the tool; after three, `execute` and `accept` are refused, only `plan` is legal, and the count resets there. |
| P13 | Handoff's local end is a trap | PASS | A handoff's only legal exit is its target; the local end is recorded as `closes` in history; an end has `waiting_on: nobody`. |
| P14 | Who decides `passes` / `tasks-done` / `was-rule` | PASS | Judgment decisions are `agent` with the role that did the work (Verifier, Builder, Sorter); `auto` is only handoffs and ends. |
