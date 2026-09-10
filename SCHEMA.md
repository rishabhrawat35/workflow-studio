# Workflow Studio — Schema

This file is the single source of truth for what a workflow file may contain.
`tools/validate.py` enforces it. If the two ever disagree, this file wins and the
validator gets fixed.

## Files

| Path | What it is |
|---|---|
| `workflows/<id>.yaml` | One workflow. Filename must equal the workflow `id`. |
| `map.yaml` | Workflow of workflows: the registry of every workflow and how they are grouped. Cross-workflow links are **not** written here — they are derived from `handoff` steps and checked against this registry. |
| `DECISIONS.md` | Why things are the way they are. Append-only. |
| `studio.html` | Renderer. `tools/build.py` embeds the YAML (as JSON) into it. |

## Workflow file

```yaml
id: claim-intake            # kebab-case, unique, equals filename
name: Claim intake
owner: PM                   # who is accountable for the whole workflow; `input` is only allowed on PM-owned steps
purpose: >-                 # one or two sentences: why this workflow exists
  Turn a raw claim request into a validated claim ready for adjudication.
trigger: Member submits a claim in the app     # what starts it (free text)
steps:
  - id: receive             # kebab-case, unique within this workflow
    type: step              # step | decision | handoff | end
    title: Receive claim
    input: The claim form as the member submitted it   # what the PM provides here (PM-owned steps only)
    what: >-                # what actually happens here
      System creates a claim record and notifies the intake queue.
    notes: >-               # optional: comments, open questions, context
      Open question: do we dedupe against claims in the last 7 days?
    next: [check-docs]      # step ids in this workflow

  - id: check-docs
    type: decision
    title: Documents complete?
    what: Intake agent checks the mandatory document list.
    next:
      - to: adjudicate
        when: all documents present
      - to: request-docs
        when: anything missing

  - id: request-docs
    type: step
    title: Request missing documents
    what: Agent sends the missing-document list to the member.
    next: [check-docs]

  - id: adjudicate
    type: handoff
    title: Hand to adjudication
    what: Claim leaves intake.
    to: claim-adjudication.receive   # <workflow-id>.<step-id> in another workflow
    next: [done]

  - id: done
    type: end
    title: Intake complete
```

### Field rules

| Field | Required on | Rule |
|---|---|---|
| `id` | workflow, step | `^[a-z0-9]+(-[a-z0-9]+)*$` |
| `name`, `owner`, `purpose`, `trigger` | workflow | non-empty strings (quote values YAML would read as numbers or booleans) |
| `type` | step | one of `step`, `decision`, `handoff`, `end` |
| `title` | step | short label shown on the node |
| `what` | step, decision, handoff | what happens; `end` may omit it |
| `notes` | optional | free text; where comments and open questions live |
| `next` | step, decision, handoff | list of targets, see below; `end` must **not** have `next` |
| `to` | handoff only | `<workflow-id>.<step-id>`; must point to a step in a *different* workflow file (same-workflow flow uses `next`) |
| `owner` on a step | optional | only when it differs from the workflow owner; never repeat the workflow owner on every step |
| `input` | optional | what the PM provides at this step (words, a file, a decision). Present only on steps where the PM gives something; drawn as a PM INPUT badge |
| `output` | optional | what durable thing this step produces (a draft, a saved file, a commit, what a handoff carries). Present only where something leaves the step |

### `next` targets

Either a plain step id, or `{to: <step-id>, when: <condition>}`.
`decision` steps must have at least two targets and every target needs a `when`;
two exits of one decision may not share the same condition (the route would be ambiguous).
`step` and `handoff` normally have exactly one target. The same target listed twice
with the same condition is an error. Any string field that is present must be
non-blank; a YAML key given twice in one mapping is an error (YAML would silently
keep the last one).

### Graph rules (validator-enforced)

1. Every `next` / `to` target resolves.
2. Exactly one step is the entry point: the first step in the list. Nothing else is inferred from order. The renderer labels it ENTRY.
3. Every step is reachable from the entry.
4. Every non-`end` step has a path to an `end` step.
5. At least one `end` step. Every `end` and every `handoff` is an exit; the renderer labels them EXIT (a handoff's exit says where it goes).
6. Every workflow has at least one step with `input`: a workflow the PM cannot feed is not allowed.
7. `input` is only allowed on steps owned by the PM (workflow owner or step override); `output` is allowed on any step.
8. Every step of every workflow is reachable from the system entry in `map.yaml`, following `next` inside a workflow and `handoff.to` across workflows, and the system exit is reachable from the entry. A step that is not is a stale step and fails validation.

## `map.yaml`

```yaml
entry: claim-intake.receive      # the step where the PM's input enters the whole system
exit: claim-adjudication.done    # the end step where the finished result leaves it
groups:
  - id: ops
    name: Operations
    workflows: [claim-intake, claim-adjudication]
  - id: growth
    name: Growth
    workflows: [member-onboarding]
```

Rules: `entry` names an existing step that carries `input` and is the first step of its workflow; `exit` names an existing `end` step; group `id` is kebab-case and unique; every file in `workflows/` appears in exactly one group; every id listed exists as a file; no keys other than `entry`, `exit`, `groups` (and `id`, `name`, `workflows` in a group). The map draws the PM feeding `entry` and the result leaving at `exit`.
The map view is drawn from this grouping plus the handoffs found in the workflow files.

## What is deliberately not in the schema

- Positions / coordinates: layout is automatic.
- Per-step owner, SLA, systems, KPIs by default: add a field only when a real workflow needs it, and record that in `DECISIONS.md` first.
- A separate list of cross-workflow links: it would duplicate `handoff.to`.
