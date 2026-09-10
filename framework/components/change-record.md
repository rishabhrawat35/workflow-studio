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
notes; for Foundation: the file or proposed rule as written and the PM's
accepted findings; findings (one block per challenge: logic, architecture,
plan, verify — what was found and how it was fixed); logic delta and
affected nodes; PM answers (approve, approve-plan, accept, with "what was
seen" for not matching); trace (affected code, reusable components); plan
for the PM (what changes for the user, what does not, the logic delta,
stored data, components reused or new by plain name, anything the PM must
supply, verified against which criteria); AI section (task list with ticks,
sources); test results and failed-pass count; outcome: delivered naming each
node version, dropped, rule dropped, already exists naming the node, or
answered.
`changes/QUEUE.md` indexes the records: waiting in order, the one in
flight, dependencies (**convention**).

## How to interact
PM: state the request at `intake`; read the plan section at
`deliver.approve-plan` and answer execute / revise the plan / revise the logic / revise the rule /
drop; never read the AI section.
AI: create the record at `intake`; update `status` at every step; write
the plan and sources at `deliver.plan`; put it through
`deliver.challenge-plan`; execute nothing until the PM says yes; complete
it inside `deliver.commit` or `deliver.drop`. Never describe changes the
node and the tags do not justify. Commit the queue whenever a record
changes (**convention**).

## Place in the system
The PM's audit trail and the system's memory of where every request is.
"What did we build for this logic, and when" and "where are we" are both
answered here.
