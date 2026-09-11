# Change record

## Definition
One file per request, born at `define.intake` the moment the request is
stated, that follows the request through every step to its end. It holds
the request in the PM's words, a `status` line naming the current step, and
later the plan (for the PM, no code) and the outcome.

## Inputs
`define.intake` (the request); `define.sort` (its kind); `deliver.trace`
and `deliver.plan` (affected code, reused and new components, the plan);
every step (status).

## Outputs
`changes/<YYYY-MM-DD>-<n>-<slug>.md` (**convention**). Front matter is the
orchestration state (`step`, `lane`, `waiting_on`, `since`,
`failed_passes`, `rerun_count`, `role`, `mode`, `command`, `history`),
written only by `orchestrate.py`. Sections, in the order the steps write
them: request (as stated at intake); sort (kind and reason); discussion
notes; for a large request: `## Breakdown — proposed <date>` (the chunks,
each with `depends on:` and `why this line:`; the order and reasons; why not
split further; alternatives) and `## Breakdown — PM answer <date>` (the
PM's words verbatim); for a removal or breaking change: `## Impact —
proposed <date>` (what is removed, every dependant with its source in
brackets, what stops working, options and one recommendation, rules and
decisions affected, stored data) and `## Impact — PM answer <date>` (one
line per dependant and per store of data); for Foundation: the file or
proposed rule as written and the PM's
accepted findings; findings (one block per challenge: logic, architecture,
plan, verify — what was found and how it was fixed); logic delta and
affected nodes; PM answers (approve, approve-plan, accept, with "what was
seen" for not matching); trace (affected code, reusable components); plan
for the PM (what changes for the user, what does not, the logic delta,
stored data, components reused or new by plain name, anything the PM must
supply, verified against which criteria); AI section (task list with ticks,
sources); test results and failed-pass count; outcome: delivered naming each
node version, dropped, rule dropped, already exists naming the node, broken
down (a parent: the chunks continue as their own records), or answered.
A proposal is never edited: a rewrite appends a new proposed block after
the PM's answer, and the confirmed set is the last proposal followed by a
yes.

**Parent and children (convention).** A large request confirmed at
`define.confirm-breakdown` is the *parent*; `define.spawn` writes one
*child* record per chunk, `changes/<YYYY-MM-DD>-<n>.<chunk>-<slug>.md`
(the parent's date and number, a dot, the chunk number, the chunk's slug;
the slug is unique across every record). A child's front matter carries
`parent` (the parent's path, relative to the product root), `chunk` (its
number in the confirmed order) and `depends_on` (the child records it
waits for; a chunk with no explicit dependency depends on the previous
chunk). A child is created only by `define.spawn`: `start` refuses a
record with `parent`. A child is readable only while its parent file and
the parent's `## Breakdown — PM answer` block exist; `next`, `advance` and
`check <child>` refuse otherwise, naming the file. The parent ends at
`define.broken-down`; a child runs as its own record with its own gates
and its own lane (set at spawn from the chunk's size). On a revision
(`define.revise-breakdown` from a child's discussion) the parent is
reopened at `define.confirm-breakdown` with the proposed correction and
the previous chunks side by side; on the PM's yes, spawn keeps the
existing children by slug (files and history), gives new chunks new files,
drops chunks no longer listed with the reason, and never touches a
delivered one or one in Deliver (a chunk being built keeps its file, its
history and its step; only its number and dependencies follow the new
order; a revision that removes it or makes it wait on an undelivered chunk
is refused at `spawn` until it closes). `spawn` runs once per yes at the
gate; a second run on the same confirmation is refused. While the parent
has children, the reopened gate takes only `spawn` (a yes) or `breakdown`
(a rewrite): to stop the group, each chunk is dropped at its own gate. A
`## Breakdown — PM answer` or `## Impact — PM answer` block is written only
by `advance --answer` at the gate; a record carrying more of them than the
gate was answered is refused. The breakdown and impact answers are decisions in the
log, category `product`, `at_step` the gate: the breakdown decision
(`decisions/D-<nnnn>-breakdown-<parent-slug>.md`) is written by
`orchestrate.py` itself when `spawn` runs; the impact decision is written
by the AI at `define.write` from the `## Impact — PM answer` block, in the
same save as the node set. A revision supersedes the earlier one. See
`components/decision-log.md`.

**Waiting (convention).** Chunk 1 starts at `define.discuss`; every other
child starts at the pseudo-step `waiting` (`step: waiting`, `mode:
waiting`, `waiting_on: chunk <n>` — its first unmet dependency). `waiting`
is not a workflow step: it has one exit, `advance --to define.discuss`,
refused until every dependency is at `deliver.done` (or dropped — a dropped
dependency no longer blocks, but hands its own dependencies on, so the wait
moves to the next unmet one). A child that left `waiting` any other way
(its `step:` edited by hand while a dependency is open) is refused by
`next`, `advance` and `check` until `step: waiting` is put back.
`next` on a waiting child states the wait; the runner exits 3 with it, and
`run.py --group <parent>` releases the next unblocked child itself after a
child reaches `deliver.done` or is dropped.

`changes/QUEUE.md` indexes the records: waiting in order, the one in
flight, dependencies (**convention**). It also carries one **group block**
per parent, written by `define.spawn` and rewritten by `orchestrate.py` on
every move of a child or of the parent, fenced so nothing else in the file
is touched:

```
<!-- group: changes/<parent>.md -->
## Group: <parent title>

Parent: changes/<parent>.md (<parent's step>)

| n | file | step | waiting on |
|---|---|---|---|
| 1 | changes/<date>-<n>.1-<slug>.md | deliver.done | nobody |
| 2 | changes/<date>-<n>.2-<slug>.md | define.discuss | PM |
| 3 | changes/<date>-<n>.3-<slug>.md | waiting | chunk 2 |

1 of 3 delivered; in flight: chunk 2
<!-- /group -->
```

Dropped chunks are listed last. The `waiting on` column of a waiting chunk
is its first still-blocking dependency as of the last write, or `release`
when every dependency is delivered or dropped and only the release is
missing. The closing line reads `<n> of <m> delivered`, then `; <k> dropped` when any chunk was dropped, then `; in
flight: chunk …` or `; nothing in flight`, and `; group closed` (or `;
group closed dropped` when nothing was delivered) once every chunk is done
or dropped. The fence markers are how the block is found; a `QUEUE.md`
without any group block is valid.

## How to interact
PM: state the request at `intake`; read the plan section at
`deliver.approve-plan` and answer execute / revise the plan / revise the logic / revise the rule /
drop; never read the AI section.
AI: create the record at `intake`; update `status` at every step; write
the plan and sources at `deliver.plan`; put it through
`deliver.challenge-plan`; execute nothing until the PM says yes; complete
it inside `deliver.commit` or `deliver.drop`. Never describe changes the
node and the tags do not justify. Commit the queue whenever a record
changes (**convention**). For a group: run the children in the confirmed
order (`run.py --group <parent>`); never create or release a child by
hand, never edit the parent's proposed or answer blocks, never touch a
delivered chunk.

## Place in the system
The PM's audit trail and the system's memory of where every request is.
"What did we build for this logic, and when" and "where are we" are both
answered here.
