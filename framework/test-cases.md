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
| P1 **(Rira)** | Slash command names match Spec Kit so a move is seamless | PASS | `orchestration/commands.yaml`: 15 names identical to Spec Kit's, 6 ours with the same prefix, no stubs (21 commands, every one entering a real step); installer writes Spec Kit ≥ 1.0's skills layout per tool; names whose meaning differs say so. |
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
| P15 | `next` / `advance` / `rerun` on a record that does not exist | PASS | Each prints `refused: no record at changes/nope.md`, exit 1; no traceback (QA 2026-09-10, run). |
| P16 | `start` in a product repository with no `changes/` folder yet | PASS | `start changes/x.md --command speckit.specify` creates `changes/` (the documented location) and the record; a refused start creates nothing. |
| P17 | Front matter that is a list or a scalar | PASS | `refused: record front matter must be a mapping`, exit 1, for `- a` and for `just text`. |
| P18 | `failed_passes: abc` / `rerun_count: x` | PASS | `refused: record field \`failed_passes\` must be an integer, not 'abc'` (same for `rerun_count` on `rerun`), exit 1. |
| P19 | `history: notalist` / `history: [1, 2]` | PASS | `refused: record field \`history\` must be a list of edges (mappings)`, exit 1, on `next` and on `advance`. |
| P20 | `--to` with a bare step id | PASS | `advance --to sort`, `--to discuss` resolve to `define.sort`, `define.discuss` among the current exits (full ref, bare id, index and unique prefix all accepted, usage text says so); `--to nowhere` still refused with the legal exits listed. |
| P21 | Product repository with only `framework/` copied, no workflows | PASS | `check` prints `refused: no workflow files in workflows/; … run \`cp -r /path/to/workflow-studio/workflows framework/\` so they sit in framework/workflows/`, exit 1; after the copy, CLOSED. `framework/README.md` layout now names `framework/workflows/` with that command. |

### P (continued). `taskstoissues` and `git.commit` as real commands (2026-09-10)

Run in a scratch product repository built with the quickstart (`framework/` and `framework/workflows/` copied, `git init`, one node `login`, one record walked with `orchestrate.py` only). Verdicts are from the runs, not from reading.

| # | Case | Verdict | Path / why |
|---|---|---|---|
| P22 | `/speckit-taskstoissues` before the plan is approved | PASS | `tasks_to_issues.py` refused with exit 1 at `deliver.plan` and at `deliver.approve-plan` ("tasks are exported only once the plan is approved"); the step is read from the record's front matter with `orchestrate.py`'s parser. |
| P23 | `/speckit-taskstoissues` at `deliver.execute`, no `gh` installed | PASS | Falls back to `--dry-run` and says so; prints one "would create" line per task with nodes and label; exit 0; record untouched. |
| P24 | Issues created and written back | PASS | With `gh` on the path (a shim returning issue URLs): `label create workflow-studio --force`, then `issue create --title "T001 …" --body "Task T001 of change record … Nodes: login" --label workflow-studio --repo acme/prod` per task; the task lines gain ` → #6` / ` → #12`; exit 0. |
| P25 | Rerun after a re-plan | PASS | Second run skips both exported tasks ("already exported #6"), creates none; a new task line would be the only one exported. Idempotent. |
| P26 | An issue closed in GitHub ticks a task | By design | Nothing is imported back; the task is ticked only at `deliver.execute`. The issue body says so. |
| P27 | `/speckit-git-commit` before the PM accepts | PASS | `commit.py` refused with exit 1 at `deliver.execute` and at `deliver.accept` ("not deliver.commit; the commit happens only after the PM accepts"); refused again at `deliver.done` after the commit (no double commit). |
| P28 | `/speckit-git-commit` outside a git repository | PASS | Copied `framework/` and `changes/` to a folder without `.git`: refused, "run from the root of the product's git repository", exit 1. |
| P29 | A stray file already staged | PASS | `git add stray.md` then `commit.py --dry-run`: refused, names `stray.md`, exit 1; after `git reset` the dry run passes. |
| P30 | The one code commit | PASS | At `deliver.commit` with two ticked tasks and one lesson decision under the record: indexes regenerated (`decisions_index.py` validated), `logic/login.md` set to `Status: delivered 848c791` (the node's last commit), `## Outcome` written, record moved `commit → was-rule → done` by `orchestrate.py advance`, commit `login: …` with body `Nodes: login / Decisions: D-0001`; `git show --stat` lists exactly the record, `code/backend/login/{login.py,test_login.py}`, `code/COMPONENTS.md`, the decision, `decisions/INDEX.md`, `logic/INDEX.md`, `logic/login.md`; `git status` clean apart from files outside the delivery. |
| P31 | The decision log does not validate at commit | PASS | In a copy of the repository with a decision lacking its "Instead of" line and the record fixture at `deliver.commit`: `decisions_index.py` exits 1, `commit.py` prints its finding and refuses (exit 1); the record is still at `deliver.commit`, `git log` unchanged. `--still-needs-logic --dry-run` announces `commit → was-rule → resume-define` for a rule whose request continues. |
| P32 | The system stays closed | PASS | `orchestrate.py check`: CLOSED, 51 steps, 21 commands, no stubs; `tools/validate.py`: OK. `taskstoissues` enters `deliver.execute`, `git.commit` enters `deliver.commit`; `start --command speckit.git.commit` on a record elsewhere is refused like any non-entry command. |
| P33 | A different AI tool takes over | PASS | `install_commands.py --agent claude` installed 21 skills including `speckit-taskstoissues` and `speckit-git-commit` (templates are globbed, no list to update). |



## Q. Adversarial QA of the tools (2026-09-10)

Every case was run against the tools as they stood at the start of the pass
(repro given), then re-run after the fix. Verdicts here are for the tools,
not the workflows: **PASS** = handled with a clear message naming the file
and step, **FIXED** = it crashed or passed silently before this pass, now
PASS. Harness: 90 validator mutations, 40 product-tree cases for the three
generators, the installer for every `--agent`, and `studio.html` loaded in
headless Chromium (console errors, network requests, node/badge counts,
overlaps) with plain, hostile (`</script>`, quotes, backslashes, CJK, emoji),
dark and 400 px-wide renders.

| # | Case | Verdict | Path / why |
|---|---|---|---|
| Q1 | Malformed YAML, tabs, empty file, list at top level, `steps` a scalar/dict, a step that is a scalar or null | PASS | `validate.py` reports `workflows/<id>.yaml: …` and continues; no traceback. |
| Q2 | Workflow file that is not UTF-8 | FIXED | Was a `UnicodeDecodeError` traceback; now `not valid UTF-8 text`. A BOM is accepted. |
| Q3 | A YAML key written twice in one mapping (`next:` twice on a step) | FIXED | PyYAML silently kept the last one; the validator now loads with a strict loader and reports `duplicate key`. |
| Q4 | Duplicate step id; missing `next`; `next` on an `end`; decision with one or zero exits; empty `when`; `to` not a string; `next` as scalar/dict/null item; unknown target | PASS | Each named by workflow and step. |
| Q5 | Two exits of one decision with the same `when` | FIXED | Passed silently (the route was ambiguous); now `two exits share the condition …`. Whitespace and case are normalised. `orchestrate.py check` already caught it downstream; the validator is the first gate. |
| Q6 | Same target listed twice with the same condition | FIXED | Silent before; now an error. Same target with *different* conditions stays legal (the renderer joins them with ` / `). |
| Q7 | Blank strings: `what: "   "`, `purpose: "  "`, `input: ""` | FIXED | All passed silently; `input: ""` even satisfied "one step with input" and drew an empty PM INPUT badge. Now `… is blank`. |
| Q8 | Non-string fields (title 42, what a list, input `true`, name 1.5, owner `yes`) | PASS | `must be a string (quote it)`. |
| Q9 | Unknown keys on a workflow or step; unicode titles; CRLF line endings | PASS | Unknown keys refused; unicode and CRLF accepted. A non-ASCII step id is refused as non-kebab-case. |
| Q10 | Stray file / `.yml` / directory in `workflows/`; workflow not in `map.yaml`; map entry or exit naming a missing workflow or step; exit not an `end`; entry not first; `map.yaml` missing, empty, a list, a scalar, malformed | PASS | All named as `map.yaml: …` or `workflows/<name>: …`. |
| Q11 | Duplicate group id in `map.yaml`; unknown top-level or group key; `workflows:` a scalar or nested list | FIXED | Duplicate group id and unknown keys passed silently (steps already refused unknown keys; the map did not). |
| Q12 | Malformed `next` under rule 8 (system reachability) | FIXED | The error was printed twice, the second time with an empty location (`: \`next\` must be …`); rule 8 now reuses the parsed targets without re-reporting. |
| Q13 | Self-loop only, unreachable cluster, no `end`, no `input` anywhere, `input` on an AI step, step owner repeating the workflow owner, handoff to own workflow / unknown workflow / unknown step / `to` with two dots or no dots / `to` not a string, stale workflow, stale island inside the entry workflow | PASS | Graph rules 1–8 all fire with the step named. |
| Q14 | `build.py` with `</script>`, `<!--`, quotes, backslashes, `\u003c` literal, CJK and emoji in title / what / notes / when | PASS | JSON is embedded with `<` escaped; the page parses it back unchanged; the inspector and nodes show the text literally (no HTML injection, no console error). |
| Q15 | `studio.html` makes an external request | FIXED | The template loaded IBM Plex from Google Fonts — the one external request, contradicting the 2026-09-09 decision "works offline". Removed; the font is used only if installed locally. `check_all.py` now fails on any `src`/`href`/`url()` to another host. |
| Q16 | All 51 nodes and their badges render in the map and each workflow view | PASS | Chromium: map 3 nodes, define 18, deliver 19, foundation 14; 66 badges; zero console errors or warnings in light and dark themes. |
| Q17 | Bottom row of `end` nodes hidden behind the legend | FIXED | `fit()` ignored the legend overlay; in Deliver the three EXIT nodes sat under it. The fit now reserves the legend's height. |
| Q18 | Edge labels printed on top of each other and over neighbouring nodes | FIXED | Direct-edge labels were anchored at the target's top-right, so a decision fanning out to adjacent steps (Deliver `accept`, Foundation `check`/`check-rule`) and two edges converging on one step (`resume-define`) overlapped. Labels now sit at the curve's midpoint on the outer side of the fan, measured with `getComputedTextLength`, and a collision pass stacks any that still touch, bounded between their own source and target. Rank gap 64 → 76. Verified: zero label/label and label/node overlaps in all three workflows. |
| Q19 | Badge row wider than its node (`EXIT → FOUNDATION` + `OUTPUT`) | FIXED | Node width now includes the badge row. |
| Q20 | Page at 400 px wide | FIXED | The 240 px + 320 px side columns left no canvas and hid the header buttons; below 900 px the page now stacks header / workflow strip / canvas / inspector, no horizontal scroll. |
| Q21 | `docs.py` run standalone on invalid YAML | FIXED | Crashed (KeyError / ValueError); it now runs the validator first and aborts with its report. |
| Q22 | `logic_index.py`: missing `logic/`, empty folder, node with no `Status:` line, duplicate stem in two folders, three levels of nesting with retirement inherited, a folder with no node file, an empty node file, a nested README | PASS | Missing folder exits 1 with the message; the rest are findings inside `INDEX.md`; nesting and inherited retirement render correctly. |
| Q23 | `logic_index.py`: node file that is not UTF-8; node stem that is not kebab-case (`Bad Stem.md`) | FIXED | Traceback on the first; the second was accepted although the framework says ids are kebab-case. Now read with replacement characters, and a non-kebab stem is flagged as a finding. |
| Q24 | `components_index.py`: missing / empty `code/`, loose file under a system, malformed and unknown tags, binary file, no `logic/` at all, duplicate node stems | PASS | Findings sections as documented; no crash. |
| Q25 | `decisions_index.py`: missing / empty `decisions/`, bad front matter, no front matter, duplicate id, `supersedes` an unknown id, `made_at` without offset or as a bare date, `made_at` a list, bad filename, one-way supersede, no "Instead of", AI decision without `resources`, CRLF | PASS | Each a finding; exit 1. |
| Q26 | `decisions_index.py`: front matter that is a list or a scalar; a file that is not UTF-8 | FIXED | Both were tracebacks (`'list' object has no attribute 'get'`, `UnicodeDecodeError`); now findings. |
| Q27 | `decisions_index.py`: `nodes: login` (scalar instead of list); `region: {a: 1}` | FIXED | The index listed the nodes as `` `l`, `o`, `g`, `i`, `n` ``; list fields must now be lists of strings and scalar fields strings, each a finding. |
| Q28 | `decisions_index.py`: file with a UTF-8 BOM | FIXED | Reported "no YAML front matter"; now read as `utf-8-sig`. |
| Q29 | `install_commands.py` for `claude`, `codex`, `copilot`, `cursor`, `gemini`, `all`; run twice; unknown `--agent`; wrong cwd | PASS | Paths are `.claude/skills/speckit-<name>/SKILL.md`, `.agents/skills/…`, `.github/skills/…`, `.cursor/skills/…`, `.gemini/commands/speckit.<name>.toml`; 21 commands × 5 = 105 files; a second run is byte-identical; `foo` is refused by argparse (exit 2); wrong cwd exits 1 with the message. All 21 TOML files parse. |
| Q30 | A command body or description containing a backslash | FIXED | Gemini TOML uses a basic `"""` string, so `\d` or `C:\path` produced invalid or altered TOML; backslashes are now doubled in TOML and in the SKILL.md description. |
| Q31 | One command proves the repo | PASS | `tools/check_all.py`: validate → build → docs → studio.html self-contained → `orchestrate.py check` → the three generators and the installer (twice) on a fixture product tree → a broken decision log is refused. Exit 1 on the first failure. |
| Q32 | `orchestrate.py` (not edited here; for the orchestration owner) | PARTIAL | Crashes instead of refusing on: a record path that does not exist (`next`/`advance`/`rerun`); `start` when `changes/` does not exist; front matter that is a list; `failed_passes` or `rerun_count` not an integer; `history` that is not a list of mappings. `--to` needs the full `workflow.step` or its prefix although the usage text says `<step>`. `check` in a product repository copied per `framework/README.md` (only `framework/`) is NOT CLOSED because `workflows/` is not in the copy. Repro in the DECISIONS entry of the same date. |

## R. Challenger pass on `commit.py`, `tasks_to_issues.py`, the validator and the renderer (2026-09-10)

Run against the tools as they stood after §P (P22–P33) and §Q, in a scratch product repository walked with `orchestrate.py` only (define.intake → deliver.commit), with failure injection; renders measured in headless Chromium at 1440 and 400 px. **FIXED** = a confirmed defect, fixed in place and re-run; **PASS** = attacked and held.

| # | Case | Verdict | Path / why |
|---|---|---|---|
| R1 | `git commit` fails at `deliver.commit` (pre-commit hook exits 1) | FIXED | Before: the record was already at `deliver.done`, the nodes said `delivered <sha>`, the index was staged, nothing committed, and a rerun was refused ("the record is at deliver.done") — a dead end the AI could leave only by editing the front matter by hand. Now the record and the node files are snapshotted before step 3 and restored on any failure in steps 4–5 (an `orchestrate.py` refusal or git), the index is unstaged, the message says so, and the rerun commits. Re-run: hook → `refused: git: hook says no … still at deliver.commit`, `git diff --cached` empty, `Status:` unchanged; hook removed → `committed 87a5b12`. |
| R2 | A path named in the trace or plan prose, not in a task line ("Reusable, unchanged: code/backend/shared/util.py", "Do not touch code/backend/audit/") | FIXED | `commit.py` scanned the whole record body for `code/…` paths, so both folders were staged — WIP in a component the plan said not to touch would have gone into the delivery commit. Now only the task lines' text is scanned, as the docstring and the README say. |
| R3 | The Builder changed a code file no task line names (`code/backend/shared/util.py`) | FIXED | Silently left out, with the record at `done` and nothing to notice it later. Now `note: changed code files no task line names; they stay uncommitted …` is printed (dry run and real run); they are still never staged (a task that touched them must name them — a `tasks-done` deviation). A task line naming a path that does not exist is reported the same way. |
| R4 | Paths with spaces; empty task list; `--dry-run` writes nothing | PASS | A space ends a path (`docs/readme with space.md` is outside `code/` anyway; a `code/…/my comp/` folder would be reported as missing under R3's note, ids are kebab-case by convention). No tasks → refused. Dry run: no index regenerated, no `Status:` change, no `## Outcome`, no record move, `git status` unchanged before and after. |
| R5 | `Status: delivered <sha>` meaning | PASS | The sha is `git log -n1 -- logic/<id>.md` at read time: the save `define.commit` made (the node version per `components/logic-node.md`); for a fix that skipped Define it is the previous delivery's commit, which exists too. Read before the delivery commit, so it never names the commit being made. |
| R6 | Task grammar: `[x]`/`[X]`, indented sub-line, `[login][reset]` without a space, `[Login]`, `→` inside the text, `T14`, a task with no text | FIXED | Glued tags were parsed as text (`nodes: []`); now `\s*` between tags. `→ A → B` inside the text is not an issue ref. `[Login]` is dropped as non-kebab (convention). `T14` and a text-less task are not task lines. Indented sub-lines are tasks (they are exported and staged like any other). |
| R7 | `gh issue create` prints a URL without `/issues/<n>` (the tool writes back the URL), then a rerun | FIXED | The rerun did not recognise ` → https://…` as exported and would have created the issue twice; the issue group now accepts `#…` or an `http(s)://` URL. |
| R8 | `gh` fails on the 4th of 5 tasks, then a rerun | PASS | 1–3 and 5 written back one by one, exit 1, "4 created, 0 skipped, 1 failed"; rerun creates only T004 (`→ #6`), exit 0. `commit.py` and `orchestrate.py` parse the lines with ` → #n` unchanged. |
| R9 | `advance --to ""` | FIXED | An empty `--to` prefix-matched the single exit of a step and moved the record (`define.drop → define.dropped`). Now refused like any unknown target. Bare ids cannot be ambiguous across workflows: a step's exits all lie in its own workflow and a handoff has exactly one; `--to d` at `define.discuss` (five `d…` exits) is refused with the list. |
| R10 | `commit.py` / `tasks_to_issues.py` on a record whose front matter is a list, or with `failed_passes: abc`; output piped to `head` | FIXED | `orchestrate.Refused` propagated as a traceback out of both tools (they import the parser but caught only `RuntimeError`); `BrokenPipeError` likewise. Both now print `refused: …`, exit 1. |
| R11 | `commands.yaml` with a `stub: true` key on a command | FIXED | `check` skipped the `enters` test for it — a bypass left over from the stub era; with no stubs left the key is gone from `orchestrate.py` and a command without `enters` is a problem. `check`: CLOSED, 51 steps, 21 commands. |
| R12 | `StrictLoader` and YAML merge keys (`<<: *anchor`, two merges, explicit key overriding a merged one) | FIXED | Every merge failed with `could not determine a constructor for the tag 'tag:yaml.org,2002:merge'` because the duplicate check constructed the `<<` key before the parent loader flattened it. Merge keys are skipped by the check and expanded as before; an explicit key after a merge is legal; a key written twice (with or without a merge) is still `duplicate key`. An unhashable key (`? [1,2]`) was a `TypeError` traceback; now a parse error naming the file. `notes: ""` and a merged `notes: "   "` are both `notes is blank`. Fuzz harness: 90/90 OK; real workflows OK. |
| R13 | Foundation view at 1440 px: `check` and `check-rule` fan out to the same three targets | FIXED | Q18's "zero label/label overlaps in all three workflows" did not reproduce: six labels shared one 76 px band; "PM says the foundation is not needed after all" printed over "PM says the rule is not needed after all", "consistent" over "PM stops" (screenshot). The band can hold four rows; the renderer now opens the rank gap by 14 px per label beyond three when labelled direct edges crowd one band (Foundation: 118 px). Measured after: 0 label/label, 0 label/node, 0 cut labels, 0 nodes off-canvas or under the legend in all views at 1440 px; no console errors; no external requests. Edges of a crossing fan still pass behind a label's halo. |
| R14 | Page at 400 px: map and each workflow | PASS | No horizontal scroll (`scrollWidth` 400), every node inside the 280 px canvas, nothing under the legend; labels measure as touching only because the whole drawing is 0.25× — pan and wheel-zoom make them legible, as at any size. |
| R15 | `install_commands.py`: a command body or description containing `"` or `"""` | FIXED | Q30 fixed backslashes, but a `"` was silently turned into `'` and `"""` into `'''` in the Gemini TOML and the SKILL.md description (parses, but the text the AI reads is altered). Now escaped (`\"`, `""\"`) so `tomllib` and YAML read the original text; all 22 TOML files and 110 skills parse. |
| R16 | Docs agree with the code | FIXED | `orchestration/README.md` said "every non-stub command"; P1 counted "13 Spec Kit names … 2 refusing stubs" (it is 15 + 6, no stubs); `README.md` listed 12 Spec Kit names (missing `-assess-intake`, `-taskstoissues`, `-git-commit`); two sections were both lettered Q (the `taskstoissues`/`git.commit` cases are now P22–P33 under P, and `DECISIONS.md` points there). `grep -rn stub` outside history entries: none. Command count 21 in `check`, the installer (21 × 5 = 105) and the READMEs. |
| R17 | Six §P/§Q verdicts re-run at random: P15, P17, P20, P29, P31, Q7, Q30 | PASS | P15/P17/P20/P29/P31 reproduce exactly (P17's "just text" case holds for `---\njust text\n---`; a file with no front matter at all prints "record has no state; use `start`", exit 1). Q7 reproduces. Q30 parsed but altered the text — see R15. |

## S. Orchestration layer 2, the runner (2026-09-11)

Run in a scratch product repository (framework copied in, `architecture.md` naming ECC so the toolbox rows apply) with `framework/tools/run.py --harness fake`, and again inside `tools/check_all.py` on its fixture. **PASS** = ran as described; **NOT RUN** = could not be run in this session, said so.

| # | Case | Verdict | Path / why |
|---|---|---|---|
| S1 | `orchestrate.py next <record> --json` at `define.sort` | PASS | One JSON object: step, title, type, mode `agent`, role `Sorter`, role_card, waiting_on, lane, exits with `to`/`when`/`index` (five), `command`/`template` null (no command enters sort), what/output/notes, failed_passes 0, rerun_count 0. Text output of `next` byte-identical to before. |
| S2 | `run.py --dry-run` at `define.sort` | PASS | Prints the harness command with `<prompt>` in place of the prompt, then the prompt: role card (may / may not / reads only), the step block, the contract with the five numbered exits and their conditions; spawns nothing; the record is unchanged. |
| S3 | `run.py --harness fake` from `define.sort` | PASS | `define.sort` spawned (fake sorts → `discuss`), stop at `define.discuss`: title, what the PM must provide, the five options, `advance <record> --to <exit> [--when <n>] --answer "…"`, "none enters this step", exit 3; `1-define.sort.log`, `2-define.discuss.log`, `run.md`. |
| S4 | The PM answers `write`; run again | PASS | `define.write` → `define.challenge` (findings block with one finding, `advance --to 1`) → stop at `define.approve` (exit 3), slash command `/speckit-approve` named. |
| S5 | `yes`; run again | PASS | `define.commit` → `define.to-deliver` (auto: the runner advances to `deliver.trace`, `closes define.handed-over` in history) → `trace` → `plan` (task list T001/T002) → `challenge-plan` (toolbox row `code-reviewer`, `Never:` list in the prompt) → stop at `deliver.approve-plan`. |
| S6 | `execute`; run again | PASS | `execute` (ticks) → `tasks-done` (fake → `verify` "all tasks done as planned") → `verify` as **four fresh sessions** (`tdd-workflow`, `code-reviewer`, `security-reviewer`, `<language>-reviewer`), the first three append a finding and do not advance (the runner checks the record's hash changed), the last advances → `passes` (→ `accept`, "all criteria hold") → stop at `deliver.accept`. `run.md`: `deliver.verify | Verifier | fake | … | moved (4 sessions)`. |
| S7 | `accepted`; run again | PASS | `deliver.commit` → `deliver.was-rule` (→ `done`) → `deliver.done`: "closed at deliver.done", exit 0, summary "2 step(s) run, 0 PM stop(s), … (deliver.commit 0.1s, deliver.was-rule 0.2s)". 18 step logs across the five runs, numbered without collision; `run.md` has one section per run. |
| S8 | A step that stalls once (`FAKE_HARNESS_STALL=define.sort`) | PASS | Attempt 1 leaves the record at `define.sort`; the runner re-spawns with "Your previous attempt did not move the record; the orchestrator said:" + the fake's last lines; attempt 2 moves; exit 3 at `discuss`. Both attempts and the retry addendum are in `1-define.sort.log`. |
| S9 | A step that never moves (`FAKE_HARNESS_STALL=always`) | PASS | `stuck: define.write did not move the record after a retry; see changes/runs/…/3-define.write.log`, exit 4; `run.md` row `stuck`. |
| S10 | `--max-steps 1` on a record at `define.write` | PASS | `define.write` runs (one step), then `stuck: --max-steps 1 reached: 1 step(s) run, the record waits on the AI at define.challenge; run again to continue`, exit 4. The limit counts steps run (auto steps included, PM stops not); the record is left at a consistent step. (Corrected 2026-09-11: the earlier text said "reached at define.write", which the runner never printed.) |
| S11 | `--check-harness` for `fake`, `claude`, `codex`; an unknown `--harness nope` | PASS | `fake: /usr/bin/python3 — Python 3.11.15` (0); `claude: /opt/node22/bin/claude — 2.1.268 (Claude Code)` (0); `codex: \`codex\` is not on PATH` (4); `stuck: harness nope is not in framework/orchestration/harness.yaml (known: claude, codex, fake)` (4). |
| S12 | `harness.yaml` with `--dangerously-skip-permissions` in `extra_flags` | PASS | Refused before anything is spawned: "a flag that skips every permission is never passed", exit 4. |
| S13 | `toolbox.yaml` naming an unknown step; `architecture.md` without "ECC" | PASS | `check`: NOT CLOSED, "toolbox.yaml: unknown step deliver.nope". Without the substring the prompt carries no toolbox section and `verify` runs as one session. |
| S14 | `commands.yaml` with `speckit.run` (`meta: true`, `enters: current`) | PASS | `check`: CLOSED, "21 commands, every one entering a real non-routing step; 1 meta command entering the record's current step; toolbox: 3 step row(s)". `start … --command speckit.run` refused with the `run.py` hint. The installer writes 22 × 5 = 110 files, idempotent. |
| S15 | `install_commands.py --check-ecc-hooks` with a settings.json carrying `node ~/.claude/hooks/ecc/pre.js` under `PreToolUse`; and with none | PASS | Lists `PreToolUse: node ~/.claude/hooks/ecc/pre.js`, "REGISTERED, remove them", exit 1; "none registered", exit 0. |
| S16 | `install_commands.py --agent claude --with-ecc` (the npx path) | NOT RUN | The npm registry answered 403 through this session's proxy, so the flags are taken from ECC's README of 2026-09-11 (`install --profile minimal --target claude --yes --no-hooks`; source-checkout `./install.sh --profile minimal --target claude`). The fallback and the hook check are coded; the live install is to be run once on Rira's Mac. |
| S17 | A real `claude -p` step through `run.py --harness claude` | NOT RUN | `claude` 2.1.268 is on PATH here but a live model call was not made in this session; the command line is the documented one (`-p <prompt> --output-format text --allowedTools <list>`), shown by `--dry-run`. |
| S18 | Python 3.9 syntax | PASS | `ast.parse(feature_version=(3,9))` over `framework/tools/*.py` and `tools/*.py`; `from __future__ import annotations` in every new file, no `match`, no `X \| Y` in `isinstance`. `tools/check_all.py` → ALL CHECKS PASSED. |

### S (continued). Challenger pass on the runner (2026-09-11)

Attacks run in a scratch product repository with a hostile harness (`evil.py`, added to `harness.yaml` as a fourth entry) that does what a misbehaving AI would; then the fix, then the same attack again. **FIXED** = confirmed, fixed in place, re-run; **OPEN** = confirmed, left as is, with the reason.

| # | Case | Verdict | Path / why |
|---|---|---|---|
| S19 | The harness at `define.challenge` writes its findings, advances to `define.approve`, then calls `advance --to commit --when 3 --answer yes` itself | FIXED | Before: the runner saw the step change, counted it as moved and went on through `commit`, `trace`, `plan`; the PM gate was skipped without a word. After: `next --json` carries `edges` and `last_edges`; the runner requires exactly one new edge from the spawned step with no `answer`; `stuck: define.challenge: the harness answered the PM step define.approve itself (edge define.approve → define.commit); a PM step is left only by the PM`, exit 4, the record left at `define.commit` with the fabricated answer in `history` for the PM to read. |
| S20 | The harness edits `step: define.challenge` to `step: deliver.execute` in the front matter, no `advance` | FIXED | Before: counted as moved; the runner spawned a Builder at `deliver.execute` with no plan approved. After: `stuck: … the record's step changed define.challenge → deliver.execute without an edge in its history: the front matter was edited by hand instead of orchestrate.py advance`, exit 4. |
| S21 | The first of the four `deliver.verify` reviewer sessions advances to `deliver.passes` | FIXED | Before: the hash had changed, so it counted as "changed"; the next two reviewers ran with a `deliver.verify` prompt against a record at `passes`, the last "moved" trivially, `run.md` said `moved (4 sessions)`. After: a non-last session must change the record without moving it: `stuck: deliver.verify [tdd-workflow]: a reviewer session moved the record deliver.verify → deliver.passes; only the last session may advance`, exit 4. |
| S22 | The harness at `deliver.trace` advances, then also writes the plan and advances `deliver.plan → challenge-plan` | FIXED | Refused: `the harness went on past its step: it also took deliver.plan → deliver.challenge-plan (agent step); one step per process`, exit 4. A harness at `define.commit` that also takes the handoff `define.to-deliver → deliver.trace` is accepted (the extra edge is from an `auto` step), and its non-zero exit shows in `run.md` as `moved (harness exit 7)`. |
| S23 | `Bash(python3 *)` in the built-in claude allow-list | FIXED | `python3 -c "import os; os.system(...)"` matches it, so it was `Bash(*)` by another name and made every narrower pattern decorative. Removed; the built-in list is the framework's tools, read-only git, pytest and `npm test`; a product adds its own run and test commands in `harness.yaml` `allowed_tools`. Documented in `orchestration/README.md` with the reason. |
| S24 | `harness.yaml` with `allowed_tools: ["Bash( * )"]`; with `extra_flags: ["--sandbox=danger-full-access"]` | FIXED | Both refused before anything is spawned: "a tool entry that allows every shell command is never passed", "a flag that skips every permission is never passed" (the check now also reads `allowed_tools`, matches a flag's value after `=`, and ignores spaces and case in the tool entry), exit 4. |
| S25 | Prompt injection through the record | OPEN, by design | The runner never puts record content into a prompt, only the path; the harness reads the record itself, as any AI would in any tool, so a record carrying text shaped like the contract is the ordinary "untrusted input" problem of the harness, not the runner's. The retry addendum, which does quote harness output, now quotes it line by line with `> ` and says it is output, not instructions; the fake harness's exit parser ignores quoted lines. |
| S26 | The command template inside the prompt told the AI to run `start`, and to "repeat 3–4 until `next` shows mode `pm`"; `$ARGUMENTS` became the record path, so it read "`changes/p.md`, if given, is the PM's note" | FIXED | The template section is prefaced: its procedure is the runner's job and the contract replaces it (one step, one `advance`); the note sentence is rewritten as "The PM left no note for this step; the runner started it." Read at `define.write`, `deliver.plan`, `deliver.verify` with `--dry-run --harness claude`: the legal-exit lists are right (write → challenge; plan → challenge-plan; verify → passes), `--when` numbers equal `--to` numbers as `resolve_when` expects, the record path is the one given on the command line everywhere (prompt, `advance` line, fake), the toolbox section appears only when `architecture.md` carries `ECC` as a whole word (an `ECCN` or `eccentric` no longer enables it). |
| S27 | The last of the four verify sessions was told to "write" the findings block that the other three had already appended to; no prompt mentioned `rerun` | FIXED | The last reviewer is told to append and keep the other reviewers' lines; a challenger is told that `advance` refuses zero findings while a framing is unused and to run `rerun` and challenge again in the same session; an agent step may use the headings its Produces names (the plan's two sections) instead of `## <step>`. |
| S28 | A record path that does not exist | FIXED | Before: `changes/runs/<stem>/run.md` was created for the typo. After: `stuck: no record at changes/nope.md; nothing was started and no log folder was created`, exit 4. |
| S29 | `--harness codex` with `codex` absent, at an AI step | FIXED | Before: the OSError surfaced from `spawn` with no log and no `run.md` row. After: refused before the first step: `stuck: harness codex: \`codex\` is not on PATH; nothing was started (run.py --check-harness --harness codex)`, exit 4. A harness that disappears mid-run, or a record that `next` can no longer read after a step, now writes the step's log (prompt, attempts, the reason under `## stopped`) and a `stuck` row before exit 4. |
| S30 | Ctrl-C while a harness runs | FIXED | `subprocess.run` kills the child on the interrupt; the runner now writes the `interrupted` row and the `run.md` section, prints where to look, and exits 130. The record is whatever the harness and `advance` last wrote (each an atomic single write). |
| S31 | A record at `deliver.done` or `define.dropped` | PASS | "closed at deliver.done", exit 0; no `run.md` section is written for a run that spawned nothing (before: an empty section per invocation). A run at a PM step writes the question as `<n>-<step>.log`, so re-running at the same PM step consumes a number each time; accepted, the log is the question the PM was asked. |
| S32 | The fake harness on the happy path | PASS | Every Deliver decision with judgment is taken by the fake: `tasks-done → verify`, `passes → accept`, `was-rule → done` (`approve-plan` and `accept` are PM). "Four PM stops" is the runner's count: `define.intake` is a PM step too, but it is answered with `advance` when the record is started, before the first run; `framework/README.md` now says so. |
| S33 | Docs vs code | PASS | `check`: 51 steps, 21 commands, 1 meta, 3 toolbox rows; 22 templates × 5 = 110 installed files; 18 step logs on the fixture; the Quickstart summary line format unchanged; `python3 tools/check_all.py` → ALL CHECKS PASSED; `ast.parse(feature_version=(3, 9))` clean over `framework/tools/*.py` and `tools/*.py`. |

### S (continued). First live run on Rira's Mac (2026-09-11)

The runner drove a record through Define with `--harness claude` (real sessions of 40–180 s each). It worked end to end and exposed six defects; each was reproduced against the fake harness in a scratch product repository (a `slow` harness entry that sleeps 22 s before running the fake stood in for the long sessions), fixed, and re-run. **FIXED** = confirmed, fixed in place, re-run.

| # | Case | Verdict | Path / why |
|---|---|---|---|
| S34 | Silence while a session runs: nothing on either stream for up to three minutes | FIXED | stderr now carries `<step> · <role> · <harness> · m:ss`, refreshed every 10 s (`\r` in place on a TTY; one line per refresh otherwise) and a final line with the outcome. Slow fake, non-TTY: `define.write · Writer · slow · 0:00`, `0:10`, `0:20`, `0:22 · moved`; then the same for `define.challenge`. Under a pty: `\rdefine.write · Writer · fake · 0:00\rdefine.write · Writer · fake · 0:00 · moved\r\n`. Outcomes: `moved`, `changed the record` (a reviewer session), `did not move; retrying once`, `did not move`, `stuck`. stdout is unchanged (`check_all` asserts the outcome line on stderr). |
| S35 | `run.md` only written at the run's end: a second terminal saw the previous run's section for three steps | FIXED | The section is now rewritten at every step start and end: the header with `outcome: running` and an in-flight row (`\| 3 \| define.write \| Writer \| slow \| … \| running since 13:16:53 \|`) before the harness starts, the finished row as soon as the step ends, the final outcome line as before. Read from a second shell 6 s and 36 s into the slow run: the in-flight row, then `define.write … 22.2 … moved` plus `define.challenge … running since`. `check_all` reads it mid-run through `FAKE_HARNESS_SHOW_RUNMD` (the fake echoes the file into its log). A run that spawns nothing still leaves no section (S31). |
| S36 | The PM stop lists the options but not which exit means yes; the PM typed `--to 2` for "yes" at `define.approve` | FIXED | After the options: `Most common answer: --to 3 --when 3 ("PM says yes")` and the paste-ready line `python3 framework/tools/orchestrate.py advance changes/p.md --to 3 --when 3 --answer "yes" && python3 framework/tools/run.py changes/p.md`, `--harness` appended when it is not `claude`. The exit is the first whose condition contains yes / execute / accepted / write it / PM says yes: `discuss` → `--to 1 --when 1 ("it is business logic; write it")`, `approve-plan` → `--to 1 --when 1 ("yes, execute")`, `accept` → `--to 1 --when 1 ("accepted")`, `confirm-exists` → `--to 1`; `define.intake` (one unconditional exit) prints no such line. |
| S37 | The command template's numbered procedure inside the prompt: "Run `check`", "`start` …", "Repeat 3–4 until `next` shows mode `pm`"; the live Writer ran `next` and `start` and reported instead of writing | FIXED | `template_body` drops every numbered line naming `check`, `start`, `next`, `advance` or `Repeat` and keeps the role/intent lines (the heading, "You are the AI role …", "Read AGENTS.md …", the "Never write code before …" paragraph); one sentence says the runner already ran `check`, started the record and read `next`. `--dry-run` at `define.write` on the fixture: no `Repeat 3–4`, no `start <record>`, no `orchestrate.py check`; the same at `deliver.plan`. |
| S38 | The PM answered "No change, the draft stands" at `discuss`; the live Writer rewrote the whole node anyway | FIXED | When the edge that entered `define.write` or `deliver.plan` carries a PM answer starting with "no change" / "the draft stands" / "unchanged" (case-insensitive), the contract carries "The PM said the draft stands. Change nothing in the draft; write only a one-line note under the step heading that it is re-submitted unchanged, then advance." Seen in `--dry-run` at `define.write` after `--answer "No change, the draft stands"` and at `deliver.plan` after `approve-plan --to plan --when 2 --answer "Unchanged; execute as planned"`; absent otherwise. The rule is in `workflows/define.yaml` (`write` notes, validator OK) and `framework/README.md` "Rules that apply everywhere". |
| S39 | A person pasted the PM-stop command at `define.challenge` (an AI step); the refusal talked about `--when` | FIXED | `advance` with `--answer` at a non-PM step is refused first: `refused: define.sort is an AI step, not a PM step; the runner (or the AI) moves it` (also `deliver.plan`, `deliver.commit`), exit 1, before the target and the condition are resolved. The other refusals are unchanged; `check_all` asserts the message at `deliver.commit`. `python3 tools/check_all.py` → ALL CHECKS PASSED; `ast.parse(feature_version=(3, 9))` clean; `tools/validate.py` OK. |

## T. Large requests and removals (2026-09-11)

`tools/check_all.py` step 8 drives the fake harness through the two paths of `docs/plans/2026-09-11-breakdown/PLAN.md` §6.2–6.3 and the refusals of §6.4, on the step 7 fixture (`code/backend/auth/auth.py` tagged `@node login` and `@node reset-password`). One case per `==` line the step prints, in the order it prints them; the assertions the script makes silently between two lines are folded into the case they belong to. **PASS** = asserted green on 2026-09-11 (127 `==` lines, exit 0, Python 3.9 syntax); **FIXED** = a defect found by the assertion during Phase 4, fixed in place, re-run. The edge cases not driven here (E6, E7, E8, E12, E13, E14, E17) were proven by hand in Phases 1–2 (`EXECUTION.md` in the plan folder) or hold by construction; `DECISIONS.md` ("Large requests and removals") lists all twenty-one.

| # | Case | Verdict | Path / why |
|---|---|---|---|
| T1 | `start changes/2026-09-11-3-habit-tracker.md --command speckit.specify` | PASS | `started at define.intake via speckit.specify`, exit 0; no traceback in any step 8 command (the harness fails the run on one). |
| T2 | The PM's intake answer: `advance --to sort --answer "a habit tracker: log a habit, see a weekly streak, get a reminder"` | PASS | `define.intake → define.sort`, exit 0. |
| T3 | `run.py changes/2026-09-11-3-habit-tracker.md --harness fake` from `define.sort` | PASS | The fake sorts to `discuss`; the runner stops there: `PM step: define.discuss`, exit 3. |
| T4 | PM at `discuss`: `--to breakdown --when 2 --answer "three capabilities: log, streak, reminder; propose the chunks"` | PASS | `define.discuss → define.breakdown  (when: several capabilities; propose the chunks)`, exit 0. |
| T5 | `run.py` from `define.breakdown`: the fake writes the proposal, the runner stops at the gate | PASS | Exit 3 with `PM step: define.confirm-breakdown`, `Most common answer: --to 1 --when 1` and the paste-ready `--answer "yes" && python3 framework/tools/run.py ` line. The record carries `## Breakdown — proposed`, `1. habit-tracker-log`, `3. habit-tracker-remind`, `depends on: chunk 1`, `Order and reasons:` and `Alternatives considered:`, and no `## Breakdown — PM answer` (the fake never answers a gate). |
| T6 | PM at `confirm-breakdown`: `--to spawn --when 1 --answer yes` | PASS | `define.confirm-breakdown → define.spawn  (when: yes, these chunks in this order)`, exit 0. |
| T7 | `run.py` from `define.spawn`: the fake spawns, the parent closes | PASS | Exit 0 with `closed at define.broken-down` and the group line `0 of 3 delivered; in flight: chunk 1`; the three child files exist; chunk 1 at `define.discuss`, chunks 2 and 3 at `waiting`. |
| T8 | E9: `run.py changes/2026-09-11-3.2-habit-tracker-streak.md` on the waiting child | PASS | Exit 3 with `Waiting: chunk 2 of changes/2026-09-11-3-habit-tracker.md waits for chunk 1 (changes/2026-09-11-3.1-habit-tracker-log.md at define.discuss) to reach deliver.done`; nothing spawned. |
| T9 | E10: `start changes/2026-09-11-3.2-habit-tracker-streak.md --command speckit.specify` | PASS | Refused, exit 1: `children are created by define.spawn; run the parent (E10)`. |
| T10 | `run.py --group changes/2026-09-11-3.1-habit-tracker-log.md` (a child) | PASS | Exit 4: `names a child (chunk 1 of …)`, `pass its parent: --group changes/2026-09-11-3-habit-tracker.md`. |
| T11 | `run.py --group changes/2026-09-11-1-runner.md` (step 7's record, no children, at `deliver.done`) | PASS | Exit 4: `names a record with no children` that is not at the breakdown. |
| T12 | PM at chunk 1's `discuss`: `--to write --when 1 --answer "a log page"` | PASS | `define.discuss → define.write`, exit 0. |
| T13 | `run.py changes/2026-09-11-3.1-habit-tracker-log.md` to `define.approve` | PASS | Exit 3, `PM step: define.approve`; the stop text carries the `Group: ` line. |
| T14 | PM at chunk 1's `approve`: `--to commit --when 3 --answer yes` | PASS | `define.approve → define.commit`, exit 0. |
| T15 | `run.py changes/2026-09-11-3.1-habit-tracker-log.md` to `deliver.approve-plan` | PASS | Exit 3, `PM step: deliver.approve-plan`, the `Group: ` line present; five steps run (`commit`, `to-deliver`, `trace`, `plan`, `challenge-plan`). |
| T16 | PM at chunk 1's `approve-plan`: `--to execute --when 1 --answer execute` | PASS | `deliver.approve-plan → deliver.execute`, exit 0. |
| T17 | `run.py changes/2026-09-11-3.1-habit-tracker-log.md` to `deliver.accept` | PASS | Exit 3, `PM step: deliver.accept`, the `Group: ` line present; `execute`, `tasks-done`, `verify` (four sessions), `passes` run. |
| T18 | PM at chunk 1's `accept`: `--to commit --when 1 --answer accepted` | PASS | `deliver.accept → deliver.commit`, exit 0. |
| T19 | `run.py changes/2026-09-11-3.1-habit-tracker-log.md` without `--group` after the last answer | PASS | Exit 0, `closed at deliver.done`, the group line `1 of 3 delivered; nothing in flight`; the word `released` absent: without `--group` the run stops when the child closes. Chunk 1 at `deliver.done`, chunk 2 still at `waiting`. |
| T20 | `run.py --group changes/2026-09-11-3-habit-tracker.md` after chunk 1 is delivered | FIXED | Exit 3 with `group: released chunk 2 (changes/2026-09-11-3.2-habit-tracker-streak.md)`, `group: running changes/2026-09-11-3.2-habit-tracker-streak.md`, `PM step: define.discuss` and `Then run again: python3 framework/tools/run.py --group changes/2026-09-11-3-habit-tracker.md`; chunk 2 at `define.discuss`. Before the Phase 4 fix, `next --json` on a *parent* never carried `group` (its `path` variable was shadowed by the template lookup), so `--group` reported "no children" for every parent; fixed in `orchestrate.py`, one line. |
| T21 | `changes/QUEUE.md` after the release | PASS | The group block carries `1 of 3 delivered; in flight: chunk 2` and the row `| 1 | changes/2026-09-11-3.1-habit-tracker-log.md | deliver.done | nobody |`. |
| T22 | PM at chunk 2's `discuss`: `--to drop --when 8 --answer "stop, the streak is not wanted"` | PASS | `define.discuss → define.drop`, exit 0. |
| T23 | E3: `run.py --group changes/2026-09-11-3-habit-tracker.md` with chunk 2 at `drop` | PASS | Exit 3: chunk 2 `closed at define.dropped`, then `group: released chunk 3 (changes/2026-09-11-3.3-habit-tracker-remind.md)` and `PM step: define.discuss` on chunk 3. |
| T24 | E3: `changes/QUEUE.md` after the drop | PASS | `1 of 3 delivered; 1 dropped; in flight: chunk 3`. |
| T25 | E4: `fake_harness.py --discuss changes/2026-09-11-3.3-habit-tracker-remind.md` | PASS | Exit 0; the fake writes chunk 3's discussion as a proposed correction in the §3.3 format (the parent's chunks minus the dropped one, plus a new `habit-tracker-settings` chunk depending on this one); the record is not advanced. |
| T26 | PM at chunk 3's `discuss`: `--to revise-breakdown --when 4 --answer "building this showed a settings capability is missing"` | PASS | `define.discuss → define.revise-breakdown`; the parent reopened at `define.confirm-breakdown` with a new `## Breakdown — proposed` block; chunk 3 at `define.revise-breakdown`, `waiting_on: parent`. |
| T27 | E4: `run.py --group changes/2026-09-11-3-habit-tracker.md` on the reopened parent | PASS | Exit 3, `PM step: define.confirm-breakdown`, `Most common answer: --to 1 --when 1`; the parent carries `## Breakdown — previous chunks` beside the proposal. |
| T28 | PM at the reopened `confirm-breakdown`: `--to spawn --when 1 --answer yes` | PASS | `define.confirm-breakdown → define.spawn`, exit 0. |
| T29 | E4: `run.py --group changes/2026-09-11-3-habit-tracker.md` spawns the revised set | PASS | Exit 3: the parent `closed at define.broken-down`; `group: released chunk 2 (changes/2026-09-11-3.3-habit-tracker-remind.md)` (the old chunk 3, kept by slug) and `PM step: define.discuss` on it. |
| T30 | E4: the delivered chunk and the new chunk after the re-spawn | PASS | Chunk 1's file is byte-for-byte what it was before the revision and still at `deliver.done`; changes/2026-09-11-3.3-habit-tracker-remind.md at `define.discuss`; the new changes/2026-09-11-3.3-habit-tracker-settings.md at `waiting`; the group block reads `1 of 4 delivered; 1 dropped; in flight: chunk 2` with `| 3 | changes/2026-09-11-3.3-habit-tracker-settings.md | waiting | chunk 2 |`; two files `D-*-breakdown-habit-tracker.md`, the second with `supersedes: `, the first with `superseded_by: `. |
| T31 | E11: `next changes/2026-09-11-3.3-habit-tracker-remind.md` with the parent file moved away | PASS | Refused, exit 1: `changes/2026-09-11-3-habit-tracker.md, which does not exist (E11)`; the file restored. |
| T32 | E11: `check changes/2026-09-11-3.3-habit-tracker-remind.md` with the parent's `## Breakdown — PM answer` heading renamed | PASS | Refused, exit 1: ``has no `## Breakdown — PM answer` block (E11)``; the heading restored. |
| T33 | `check changes/2026-09-11-3.3-habit-tracker-remind.md` with parent and block restored | PASS | `CLOSED — 58 steps, … ; changes/2026-09-11-3.3-habit-tracker-remind.md is chunk 2 of changes/2026-09-11-3-habit-tracker.md (parent and PM answer present)`, exit 0. |
| T34 | `start changes/2026-09-11-4-remove-reminders.md --command speckit.specify` | PASS | Started at `define.intake`, exit 0. |
| T35 | The PM's intake answer: ``remove `reminder`, nobody uses it`` | PASS | `define.intake → define.sort`, exit 0. |
| T36 | `run.py changes/2026-09-11-4-remove-reminders.md` from `define.sort` | PASS | Exit 3 at `PM step: define.discuss`. |
| T37 | PM at `discuss`: `--to impact --when 3 --answer "show me the repercussions"` | PASS | `define.discuss → define.impact  (when: this removes or changes something others depend on; show the repercussions)`, exit 0 (the fixture has `architecture.md`, so E6 does not fire). |
| T38 | `run.py` from `define.impact`: the fake writes the impact section, the runner stops at the gate | PASS | Exit 3 with `PM step: define.confirm-impact`, `Most common answer: --to 1 --when 1`, the condition `proceed with the chosen set` and the placeholder `<dependant>: retire it too …` in the paste-ready line. The record carries `## Impact — proposed`, `Removing or changing: reminder`, `1. login [tags: code/backend/auth/auth.py`, `2. reset-password [tags:` (both dependants read from the `@node` tags), `options: retire it too | keep it by`, `recommended:`, `Stored data: reminder table — keep | migrate` and `recommended: keep`; no `## Impact — PM answer`. |
| T39 | PM at `confirm-impact`: `--to breakdown --when 3 --answer "login: retire it too; reset-password: keep it by a replacement; reminder table: keep"` (E16, E19, E21) | PASS | `define.confirm-impact → define.breakdown  (when: a chosen treatment needs a replacement built first; make the set chunks, replacement before removal)`, exit 0; the answer names every dependant listed, so it is accepted. |
| T40 | `run.py changes/2026-09-11-4-remove-reminders.md` from `define.breakdown` after an impact answer | PASS | Exit 3 at `PM step: define.confirm-breakdown`; the proposal lists `1. remove-reminders-replacement` before `2. remove-reminders-removal`, the removal with `depends on: chunk 1`. |
| T41 | PM at `confirm-breakdown`: `--to spawn --when 1 --answer yes` | PASS | `define.confirm-breakdown → define.spawn`, exit 0. |
| T42 | `run.py --group changes/2026-09-11-4-remove-reminders.md` on the parent at `spawn` | PASS | Exit 3: the parent `closed at define.broken-down`, then chunk 1 (the replacement) run to `PM step: define.discuss`. |
| T43 | The removal group in `changes/QUEUE.md` | PASS | `| 1 | changes/2026-09-11-4.1-remove-reminders-replacement.md | define.discuss | PM |` and `| 2 | changes/2026-09-11-4.2-remove-reminders-removal.md | waiting | chunk 1 |`: the replacement first, the removal waiting on it. |
| T44 | `start changes/2026-09-11-5-reports.md` | PASS | Started at `define.intake`, exit 0. |
| T45 | The PM's intake answer: `reports: daily, weekly, monthly` | PASS | `define.intake → define.sort`, exit 0. |
| T46 | `run.py changes/2026-09-11-5-reports.md` from `define.sort` | PASS | Exit 3 at `PM step: define.discuss`. |
| T47 | PM at `discuss`: `--to breakdown --when 2 --answer "propose the chunks"` | PASS | `define.discuss → define.breakdown`, exit 0. |
| T48 | E1: `run.py` from `define.breakdown` | PASS | Exit 3 at `PM step: define.confirm-breakdown`. |
| T49 | E1: PM at `confirm-breakdown`: `--to write --when 3 --answer "one thing"` | PASS | `define.confirm-breakdown → define.write  (when: one thing after all; write it as a single node)`, exit 0. |
| T50 | E1: `run.py` from `define.write` | PASS | Exit 3 at `PM step: define.approve`: `write` and `challenge` ran on a single node. |
| T51 | E1: the record after the single node | PASS | It carries both `## Breakdown — proposed` (the proposal stays as history) and `## define.write` (the node was written). |
| T52 | `start changes/2026-09-11-6-accounts.md` | PASS | Started at `define.intake`, exit 0. |
| T53 | The PM's intake answer: `accounts: sign up, log in, reset the password` | PASS | `define.intake → define.sort`, exit 0. |
| T54 | `run.py changes/2026-09-11-6-accounts.md` from `define.sort` | PASS | Exit 3 at `PM step: define.discuss`. |
| T55 | PM at `discuss`: `--to breakdown --when 2 --answer "propose the chunks"` | PASS | `define.discuss → define.breakdown`, exit 0. |
| T56 | E2: round 1, `run.py` from `define.breakdown` | PASS | Exit 3 at `PM step: define.confirm-breakdown`. |
| T57 | E2: PM at `confirm-breakdown`: `--to breakdown --when 2 --answer "merge 1 and 2, round 1"` | PASS | `define.confirm-breakdown → define.breakdown  (when: merge, split, reorder or drop chunks; rewrite from the PM's words)`, exit 0. |
| T58 | E2: the rewrite, round 1 | PASS | Exit 3 at `PM step: define.confirm-breakdown`; a second `## Breakdown — proposed` block appended, the first untouched. |
| T59 | E2: PM at `confirm-breakdown`: `--to breakdown --when 2 --answer "merge 1 and 2, round 2"` | PASS | `define.confirm-breakdown → define.breakdown`, exit 0. |
| T60 | E2: the rewrite, round 2 | PASS | Exit 3 at `PM step: define.confirm-breakdown`; the record holds exactly three `## Breakdown — proposed` blocks, the last opening with `Rewritten from the PM's words: merge 1 and 2, round 2`. |
| T61 | E2: a yes after three rounds: `--to spawn --when 1 --answer yes` | PASS | Refused, exit 1: `proposed 3 times (the cap is 3); only write (one node) or drop` are legal. |
| T62 | E2: a fourth rewrite: `--to breakdown --when 2 --answer "split again"` | PASS | Refused, exit 1, naming `the cap is 3`. |
| T63 | E2: PM at `confirm-breakdown` after the cap: `--to drop --when 4 --answer stop` | PASS | `define.confirm-breakdown → define.drop`, exit 0: drop stays legal after the cap. |
| T64 | `start changes/2026-09-11-7-shop.md` | PASS | Started at `define.intake`, exit 0. |
| T65 | The PM's intake answer: `a shop: catalogue, basket, checkout` | PASS | `define.intake → define.sort`, exit 0. |
| T66 | `run.py changes/2026-09-11-7-shop.md` from `define.sort` | PASS | Exit 3 at `PM step: define.discuss`. |
| T67 | PM at `discuss`: `--to breakdown --when 2 --answer "propose the chunks"` | PASS | `define.discuss → define.breakdown`, exit 0. |
| T68 | E5: `run.py` from `define.breakdown` with `FAKE_HARNESS_E5=1` (chunk 3 names chunk 2's node, no dependency) | PASS | Exit 3 at `PM step: define.confirm-breakdown`: the proposal itself is accepted; the check is at `spawn`. |
| T69 | E5: PM at `confirm-breakdown`: `--to spawn --when 1 --answer yes` | PASS | `define.confirm-breakdown → define.spawn`, exit 0. |
| T70 | E5: `advance … --to broken-down` out of `spawn` | PASS | Refused, exit 1: `both touch node shop-streak with no dependency between them (E5)`; no child file written. |
| T71 | `start changes/2026-09-11-8-remove-login.md` | PASS | Started at `define.intake`, exit 0. |
| T72 | The PM's intake answer: ``remove `login` `` | PASS | `define.intake → define.sort`, exit 0. |
| T73 | `run.py changes/2026-09-11-8-remove-login.md` from `define.sort` | PASS | Exit 3 at `PM step: define.discuss`. |
| T74 | E18: `--to impact --when 3 --answer show` while a hand-written `changes/2026-09-10-9-build-login.md` sits at `deliver.execute` with `nodes: [login]` and this record carries `nodes: [login]` | PASS | Refused, exit 1: ``is in Deliver (deliver.execute) on node login, which this request names in its front matter `nodes:` (E18)``. |
| T75 | E18 lifted: the same `advance` after the busy record is removed | PASS | `define.discuss → define.impact`, exit 0. |
| T76 | E18 lifted: `run.py` from `define.impact` | PASS | Exit 3 at `PM step: define.confirm-impact`. |
| T77 | PM at `confirm-impact`: `--to write --when 1 --answer "reset-password: keep it by a replacement; login table: keep"` | PASS | `define.confirm-impact → define.write  (when: proceed with the chosen set)`, exit 0 (`reset-password` is the only dependant the block lists once `login` is the removed node). |
| T78 | E20: `run.py` from `define.write` after `code/backend/notify/notify.py` (`@node notification-settings`) was added | PASS | Exit 3 at `PM step: define.approve`: `write` then `challenge` ran. |
| T79 | E20: the challenge's finding | PASS | The record carries ``the impact block omits the tagged dependant `notification-settings` (@node notification-settings in code/backend/notify/notify.py)``: the omission is a finding before `approve`. |
| T80 | `start changes/2026-09-11-9-remove-orphan.md` | PASS | Started at `define.intake`, exit 0. |
| T81 | The PM's intake answer: ``remove `orphan` `` | PASS | `define.intake → define.sort`, exit 0. |
| T82 | `run.py changes/2026-09-11-9-remove-orphan.md` from `define.sort` | PASS | Exit 3 at `PM step: define.discuss`. |
| T83 | PM at `discuss`: `--to impact --when 3 --answer show` | PASS | `define.discuss → define.impact`, exit 0. |
| T84 | E15: `run.py` from `define.impact` with `FAKE_HARNESS_NO_DEPENDANTS=1` | PASS | Exit 4, `did not move the record` after a retry: `advance` refuses to leave `impact` on a block with no dependants. |
| T85 | E15: the refusal in the step log | PASS | The log the runner names carries `with no dependants there is no impact stop (E15)`. |
| T86 | `start changes/2026-09-11-10-retire-orphan.md` | PASS | Started at `define.intake`, exit 0. |
| T87 | The PM's intake answer: ``remove `orphan`, no dependants found (tags, tree, glossary)`` | PASS | `define.intake → define.sort`, exit 0. |
| T88 | `run.py changes/2026-09-11-10-retire-orphan.md` from `define.sort` | PASS | Exit 3 at `PM step: define.discuss`. |
| T89 | E15: PM at `discuss`: `--to write --when 1 --answer "no dependants found (tags, tree, glossary): retire it"` | PASS | `define.discuss → define.write  (when: it is business logic; write it)`, exit 0: a removal nobody depends on takes the ordinary path. |
| T90 | E15: `run.py` from `define.write` | PASS | Exit 3 at `PM step: define.approve`, as for any node. |

### T (continued). Challenger pass on large requests and removals (2026-09-11, Phase 6)

The challenger's attack list (`docs/plans/2026-09-11-breakdown/challenge.md`, items C1–C9 below are the ones that became `check_all.py` cases; the report holds all seventeen) was run by hand in a scratch product first, then the confirmed defects were fixed in `orchestrate.py` (Phase 2 scope) and one sentence in `define.yaml` (Phase 1 scope), and the cases were added to step 8 (127 → 207 `==` lines; 80 of them here). Same convention as above: one case per `==` line, in print order. **FIXED** = the assertion failed on the Phase 5 engine and passes after the fix.

| # | Case | Verdict | Step path and what was seen |
|---|---|---|---|
| T91 | `start changes/2026-09-11-11-fleet.md --command speckit.specify` | PASS | `started at define.intake via speckit.specify`, exit 0. |
| T92 | The PM's intake answer "a fleet: vehicles, drivers, trips" | PASS | `define.intake → define.sort`, exit 0. |
| T93 | `run.py` from `define.sort` | PASS | Exit 3 at `PM step: define.discuss`. |
| T94 | PM at `discuss`: `--to breakdown --when 2 --answer "propose the chunks"` | PASS | `define.discuss → define.breakdown`, exit 0. |
| T95 | C1: `run.py` writes the breakdown (fake) | PASS | Exit 3 at `PM step: define.confirm-breakdown`. |
| T96 | C1: the PM's yes typed as `Yes.` (capital, full stop) | PASS | `define.confirm-breakdown → define.spawn  (when: yes, these chunks in this order)`, exit 0: punctuation and case do not matter; extra words do ("yes but rename chunk 2" is not a yes and goes back to `breakdown`, T13 in the plan folder's `challenge.md`). |
| T97 | C1: `run.py` spawns | PASS | Exit 0, `closed at define.broken-down`; three children, chunk 1 at `define.discuss`, 2 and 3 `waiting`. |
| T98 | C1: chunk 2's front matter set to `step: define.discuss` / `mode: pm` by hand while chunk 1 is still open; `next` | FIXED | Before: `next` showed `define.discuss` and `advance --to write` moved it, skipping the dependency. Now: `refused: … is chunk 2 of … at define.discuss, but it depends on chunk 1 (… at define.discuss, not deliver.done); a chunk leaves \`waiting\` only by \`advance --to define.discuss\` once every dependency is delivered or dropped — the record was edited by hand; set \`step: waiting\` and \`mode: waiting\` back`, exit 1. The check lives in `check_parent`, so `next`, `advance` and `check <child>` all refuse; closed chunks and `handed-over` are exempt. |
| T99 | C1: `advance --to write --when 1 --answer x` on the same hand-edited child | FIXED | The same refusal, exit 1; the record is not moved. |
| T100 | C1: the front matter restored; `next` | PASS | The wait again: `1. → define.discuss   when: every dependency at deliver.done (or dropped)`, exit 0. |
| T101 | C2: spawn twice — the parent's `step:` set back to `define.spawn` by hand, `advance --to broken-down` | FIXED | Before: the children were matched by slug (no duplicate files) but a second decision `D-<n+1>` superseding the first was written and chunk 1's history gained a second `define.spawn → define.discuss` edge with a new `since`. Now: `refused: the breakdown confirmed in the last \`## Breakdown — PM answer\` of … was already spawned (1 spawn(s) for 1 yes(es) in the history; its group block is in changes/QUEUE.md); spawn runs once per confirmation — to change the chunks, use revise-breakdown from a chunk still in Define`, exit 1. Every yes at the gate allows exactly one `spawn → broken-down`. |
| T102 | C2: one decision file, one spawn edge on chunk 1 | FIXED | `decisions/D-*-breakdown-fleet.md` count 1; chunk 1's history has one `to: define.discuss`. |
| T103 | PM at chunk 1's `discuss`: `--to write --when 1 --answer "a vehicles page"` | PASS | `define.discuss → define.write`, exit 0. |
| T104 | C3: `run.py` chunk 1 to `define.approve` | PASS | Exit 3 at `PM step: define.approve`. |
| T105 | PM at `approve`: `--to commit --when 3 --answer yes` | PASS | `define.approve → define.commit`, exit 0. |
| T106 | C3: `run.py` chunk 1 to `deliver.approve-plan` | PASS | Exit 3 at `PM step: deliver.approve-plan`. |
| T107 | PM at `approve-plan`: `--to execute --when 1 --answer execute` | PASS | `deliver.approve-plan → deliver.execute`, exit 0. |
| T108 | C3: `run.py` chunk 1 to `deliver.accept` | PASS | Exit 3 at `PM step: deliver.accept`. |
| T109 | PM at `accept`: `--to commit --when 1 --answer accepted` | PASS | `deliver.accept → deliver.commit`, exit 0. |
| T110 | C3: `run.py --group` closes chunk 1 and releases chunk 2 | PASS | `closed at deliver.done`, `group: released chunk 2 (changes/2026-09-11-11.2-fleet-streak.md)`, exit 3 at chunk 2's `define.discuss`. |
| T111 | PM at chunk 2's `discuss`: `--to write --when 1 --answer "a drivers page"` | PASS | `define.discuss → define.write`, exit 0. |
| T112 | C3: `run.py` chunk 2 to `define.approve` | PASS | Exit 3 at `PM step: define.approve`. |
| T113 | PM at `approve`: `--to commit --when 3 --answer yes` | PASS | `define.approve → define.commit`, exit 0. |
| T114 | C3: `run.py` chunk 2 to `deliver.approve-plan` | PASS | Exit 3 at `PM step: deliver.approve-plan`. |
| T115 | PM at `approve-plan`: `--to execute --when 1 --answer execute` | PASS | `deliver.approve-plan → deliver.execute`, exit 0; chunk 2 is now mid-Deliver with an approved plan. |
| T116 | C3: `advance changes/2026-09-11-11.3-fleet-remind.md --to define.discuss` (its dependency, chunk 1, is delivered) | PASS | `waiting → define.discuss  (released: every dependency at deliver.done or dropped)`, exit 0; chunk 3 is in flight beside chunk 2. |
| T117 | C3: `fake_harness.py --discuss` on chunk 3 (a proposed correction that keeps chunk 2 and adds a settings chunk) | PASS | Exit 0; `## define.discuss` written, not advanced. |
| T118 | PM at chunk 3's `discuss`: `--to revise-breakdown --when 4 --answer "a settings chunk is missing"` | PASS | `define.discuss → define.revise-breakdown`; the parent reopened at `define.confirm-breakdown`, exit 0. |
| T119 | C4: the reopened parent answered `--to write --when 3 --answer "one thing"` while four children exist | FIXED | Before: the parent moved to `define.write` as a single node with its children still in flight and delivered (a hole in the reopened gate). Now: `refused: … has children (the group block in changes/QUEUE.md); from the reopened gate only spawn (a yes, reconciled) or breakdown (a rewrite) are legal — to stop the group, drop each chunk at its own gate; to build the rest as one node, drop the chunks and start a new request`, exit 1. A first-time gate (no children yet) still takes `write` (E1, T61). |
| T120 | C4: the same with `--to drop --when 4 --answer stop` | FIXED | The same refusal, exit 1. |
| T121 | PM at the reopened gate: `--to spawn --when 1 --answer yes` | PASS | `define.confirm-breakdown → define.spawn`, exit 0. |
| T122 | C3: `advance --to broken-down` (the re-spawn) with chunk 2 at `deliver.execute` | FIXED | Before: the re-spawn put chunk 2 back to `define.discuss` (`child_state` rewrote every kept chunk that was not delivered or dropped) — an approved plan and code in progress were rewritten from the parent. Now: `define.spawn → define.broken-down`, exit 0; a chunk in Deliver is treated like a delivered one: its file, history and state are untouched, only its chunk number and `depends_on` follow the confirmed order. |
| T123 | C3: chunk 2's bytes before and after the re-spawn; the others re-planned | FIXED | Bytes equal, `step: deliver.execute`; chunk 3 back to `waiting` (release) and the new `11.4-fleet-settings` `waiting` on it. |
| T124 | C4: `advance` chunk 3 `--to define.discuss` again | PASS | Released, exit 0. |
| T125 | C4: a second `## define.discuss` written by hand into chunk 3 that drops the drivers chunk (chunk 2, mid-Deliver) and renumbers | FIXED | Before: `child_discussion()` returned the *first* `## define.discuss` section, so a chunk re-discussed after a revision would have reopened the parent with its stale first discussion. Now the newest section is the proposal. |
| T126 | PM at chunk 3's `discuss`: `--to revise-breakdown --when 4 --answer "drop the drivers chunk"` | PASS | The parent reopened with the new proposal, exit 0. |
| T127 | PM at the reopened gate: `--to spawn --when 1 --answer yes` | PASS | `define.confirm-breakdown → define.spawn`, exit 0. |
| T128 | C4: `advance --to broken-down` with a proposal that removes chunk 2 while it is at `deliver.execute` | FIXED | Before: the chunk would have been moved to `define.dropped` by `set_state` from a Deliver step (a wrong workflow, code in progress abandoned). Now: `refused: chunk 2 (fleet-streak) is in Deliver (deliver.execute, …); a revision never rewrites or removes a chunk being built — keep it in the proposal, wait for it to reach deliver.done, or drop it at its own gate`, exit 1; the parent stays at `define.spawn` (safely paused). A revision that makes a chunk mid-Deliver depend on an undelivered chunk is refused the same way ("a chunk being built cannot wait"). |
| T129 | C4: `run.py` chunk 2 from `deliver.execute` | PASS | Exit 3 at `PM step: deliver.accept`. |
| T130 | PM at `accept`: `--to commit --when 1 --answer accepted` | PASS | `deliver.accept → deliver.commit`, exit 0. |
| T131 | C4: `run.py` chunk 2 to `deliver.done` | PASS | Exit 0, `closed at deliver.done`. |
| T132 | C4: the same `advance --to broken-down` once chunk 2 is delivered | PASS | `define.spawn → define.broken-down`, exit 0: the delivered chunk is not in the set and is left as it is (never touched, never dropped); remind becomes chunk 2, settings chunk 3. |
| T133 | C4: the group block after the revision | PASS | `\| 2 \| changes/2026-09-11-11.3-fleet-remind.md \| waiting \| release \|`, `2 of 4 delivered` (the delivered drivers chunk keeps its row and its old number 2, so two rows read "2"; a delivered chunk is never rewritten). |
| T134 | `start changes/2026-09-11-12-remove-reset.md` | PASS | Started, exit 0. |
| T135 | The PM's intake answer ``remove `reset-password` `` | PASS | `define.intake → define.sort`, exit 0. |
| T136 | `run.py` from `define.sort` | PASS | Exit 3 at `PM step: define.discuss`. |
| T137 | PM at `discuss`: `--to impact --when 3 --answer show` | PASS | `define.discuss → define.impact`, exit 0. |
| T138 | C5: `run.py` writes the impact block (one dependant, `login`; one store, `reset_password table`, keep recommended) | PASS | Exit 3 at `PM step: define.confirm-impact`. |
| T139 | C5: the PM pastes the "Most common answer" command verbatim, placeholder and all (`<dependant>: retire it too \| … ; <store>: keep \| migrate \| delete`) | PASS | `refused: the PM's answer names no choice for dependant 'login' …`, exit 1: the placeholder cannot skip the choice because it names no dependant. |
| T140 | C5: `--to write --when 1 --answer "login: retire it too"` (every dependant, no store) | FIXED | Before: accepted — the store's handling was left to the AI at `write`, so "delete" could become the default by omission (E19). Now: `refused: the PM's answer names no choice for the stored data 'reset_password table' listed in … (E19); add \`reset_password table: keep \| migrate to <…> \| delete\` — nothing is defaulted, delete least of all`, exit 1. |
| T141 | C5: `--answer "login: retire it too; reset_password table: migrate to the audit log"` | PASS | `define.confirm-impact → define.write`, exit 0. |
| T142 | `start changes/2026-09-11-13-remove-orphan2.md` | PASS | Started, exit 0. |
| T143 | The PM's intake answer ``remove `orphan2` `` | PASS | `define.intake → define.sort`, exit 0. |
| T144 | `run.py` from `define.sort` | PASS | Exit 3 at `PM step: define.discuss`. |
| T145 | PM at `discuss`: `--to impact --when 3 --answer show` | PASS | `define.discuss → define.impact`, exit 0. |
| T146 | C5: an `## Impact — proposed` block written by hand whose stored-data line ends `recommended: delete`; `advance --to confirm-impact` | FIXED | Before: accepted. Now: `refused: the block … recommends delete for the stored data 'orphan2 table'; "delete" is never the default (E19) — recommend keep or migrate, the PM may still choose delete at define.confirm-impact`, exit 1. |
| T147 | `start changes/2026-09-11-14-remove-login2.md` | PASS | Started, exit 0. |
| T148 | The PM's intake answer ``remove `login`, the SSO replaces it`` | PASS | `define.intake → define.sort`, exit 0. |
| T149 | `run.py` from `define.sort` | PASS | Exit 3 at `PM step: define.discuss`. |
| T150 | C6: E18 with no `nodes:` anywhere — a hand-written `2026-09-10-8-build-login.md` at `deliver.execute` whose body has `- [ ] T001 [P] [login] …`; `--to impact` | FIXED | Before: E18 compared only front-matter `nodes:` lists, a field no step or command writes, so the refusal could never fire in live use. Now the removal record names a node in `nodes:`, in a task tag, or in backticks in its body or its PM answers (the intake request lives in the history), and the record in Deliver names it in `nodes:` or in a task line's `[<id>]` tag: `refused: changes/2026-09-10-8-build-login.md is in Deliver (deliver.execute) on node login, which this request names (E18); … (heuristic: … a record in Deliver with neither is not compared)`, exit 1. |
| T151 | PM at `discuss`: `--to impact --when 3 --answer show` after the busy record's task line is replaced by prose that mentions `login` | PASS | `define.discuss → define.impact`, exit 0. |
| T152 | C6: a record in Deliver naming the node only in prose is not compared | PASS | Stated in the refusal text (the residual gap: a record at `deliver.trace` or `deliver.plan` has no task list yet; the plan carries the tags from `deliver.plan` on). |
| T153 | `start changes/2026-09-11-15-inventory.md` | PASS | Started, exit 0. |
| T154 | The PM's intake answer "inventory: stock, orders, suppliers" | PASS | `define.intake → define.sort`, exit 0. |
| T155 | `run.py` from `define.sort` | PASS | Exit 3 at `PM step: define.discuss`. |
| T156 | PM at `discuss`: `--to breakdown --when 2 --answer "propose the chunks"` | PASS | `define.discuss → define.breakdown`, exit 0. |
| T157 | C7: `run.py` writes the breakdown | PASS | Exit 3 at `PM step: define.confirm-breakdown`. |
| T158 | C7: the record set back to `define.breakdown` by hand; chunk 1's slug changed to `../../etc/inventory-log`; `advance --to confirm-breakdown` | FIXED | Before: the chunk line did not match the slug pattern and was silently dropped from the parse (the block "lost" a chunk; a spawn would then have complained about numbering). Now the slug is parsed as any token and validated: `refused: chunk 1 in … has the slug '../../etc/inventory-log', which cannot name a record file; a slug is lowercase letters, digits and hyphens (no \`/\`, \`..\`, \`_\` or spaces)`, exit 1 — at `breakdown` (before the PM reads it) and again at `spawn`. |
| T159 | C7: chunk 2 made to depend on chunk 3 | FIXED | Before: accepted by `spawn` (a forward dependency; chunk 1 could even depend on chunk 2 and be started at `discuss` with an unmet dependency). Now: `refused: chunk 2 (inventory-streak) depends on chunk 3, which comes after it; dependencies first — reorder the chunks so every dependency precedes the chunk that needs it`, exit 1. |
| T160 | C7: a `## Breakdown — PM answer` block appended by hand (as an AI at `breakdown` could) with no gate exit in the history | FIXED | Before: the block sat in the body; `spawn` could not consume it without a real yes edge (the `advance` at the gate appends its own), but a forged heading inside the proposed block cut the proposal short at that line. Now: `refused: … carries 1 \`## Breakdown — PM answer\` block(s) but the PM has answered define.confirm-breakdown 0 time(s); that block is written only by \`advance --answer\` at the gate — remove the one written by hand or by the AI`, exit 1; the same count holds for `## Impact — PM answer` at `impact`, and at `spawn`. |
| T161 | C8: `changes/QUEUE.md` edited by hand — the fleet block's closing fence removed; a child moves | FIXED | Before: the block pattern `<!-- group: X -->.*?<!-- /group -->` ran on to the *next* group's closing fence and rewrote both blocks as one (the other group's block was lost until its next move); with no later fence at all the block was appended a second time. Now the pattern never crosses another `<!-- group:` marker, a block with no closing fence is rewritten up to the next group (or the end) and the move prints `changes/QUEUE.md: the group block for … had no closing fence (edited by hand); rewritten`. The queue is never read for state: a mangled table row or a removed `Parent:` line is simply regenerated. |
| T162 | C8: the queue after the move | FIXED | One fleet block, fenced, with the moved row; the habit-tracker and remove-reminders blocks intact. |
| T163 | `start changes/2026-09-11-16-billing.md` | PASS | Started, exit 0. |
| T164 | The PM's intake answer "billing: invoices, payments, refunds" | PASS | `define.intake → define.sort`, exit 0. |
| T165 | `run.py` from `define.sort` | PASS | Exit 3 at `PM step: define.discuss`. |
| T166 | PM at `discuss`: `--to breakdown --when 2 --answer "propose the chunks"` | PASS | `define.discuss → define.breakdown`, exit 0. |
| T167 | C9: `run.py` writes the breakdown; chunk 3's line edited to `depends on: chunk 2` (a chain 1 → 2 → 3) | PASS | Exit 3 at `PM step: define.confirm-breakdown`. |
| T168 | PM at the gate: `--to spawn --when 1 --answer yes` | PASS | `define.confirm-breakdown → define.spawn`, exit 0. |
| T169 | C9: `run.py` spawns | PASS | Exit 0; chunk 2 waits on chunk 1, chunk 3 on chunk 2. |
| T170 | C9: chunk 2 marked `define.dropped` by hand while chunk 1 is still at `discuss`; `advance` chunk 3 `--to define.discuss` | FIXED | Before: released — a dropped dependency counted as met and chunk 3 lost the dependency it had on chunk 1 through chunk 2. Now a dropped dependency hands its own dependencies on: `wait moved: chunk 2 → chunk 1`, then `refused: chunk 3 waits on chunk 1 (changes/2026-09-11-16.1-billing-log.md is at define.discuss, not deliver.done)`, exit 1. The group block's "waiting on" column follows the same rule. |
