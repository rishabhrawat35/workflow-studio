# Challenger pass

## Definition
A second, independent AI pass that reviews work before the PM sees it. It
reads only the inputs listed for its step (**convention**) and reports
findings; the first pass (the AI that wrote the work) fixes them
(**convention**).

## Inputs
`foundation.check` / `check-rule`: the architecture file, or the proposed
rule and the file.
`define.challenge`: the draft node(s), the proposed glossary additions, the
glossary, the logic tree, the architecture file.
`deliver.challenge-plan`: the plan, the record, the node(s), the traced code
and existing components.
`deliver.verify`: the code and tests, the confirmed acceptance criteria of
every node touched, the architecture file, the sources the plan recorded.
Not the plan.

## Outputs
A list of findings. In `foundation.check` / `check-rule` they go back to
the PM with the file. In `define.challenge` and `deliver.challenge-plan`
they are fixed in the draft before the PM sees it, and the affected-nodes
list goes to the PM. In `deliver.verify` they go to `deliver.passes`, which
routes to `deliver.execute` (fixable in code), `deliver.plan` (the plan was
wrong) or `deliver.accept` (none open).

## How to interact
PM: nothing directly; the PM sees work only after it has passed.
AI: run it in a fresh context given only the listed inputs, never the
conversation that produced the work (**convention**). Report: missing required content, contradictions, unreachable tools,
foreign content (architecture); ambiguity, unverifiable criteria, conflicts
with the architecture, terms not in the glossary, placement that hurts the
tree, every other node affected (Define); promises the node and tags do not
justify, affected code the plan omits, a duplicate component, missing or
outdated sources, code words in the PM section (plan); failed criteria,
architecture violations, untagged code, duplicate components (verify).

A pass that finds nothing on non-trivial work is run once more with a
different framing before the work proceeds (stated in the workflows).

## Place in the system
The quality gate before each of the three PM gates (`define.approve`,
`deliver.approve-plan`, `deliver.accept`) and before the foundation is
saved, so the PM judges finished work rather than drafts.
