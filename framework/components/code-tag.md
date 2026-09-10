# Code tag

## Definition
The id of a logic node written into every piece of code and test built for
that node. It is how the system finds what a change affects, without
guessing.

## Inputs
The node id, added in `deliver.execute`.

## Outputs
Components and tests on the code side that can be traced back to a node;
`code/COMPONENTS.md` lists the tags per component.

## How to interact
PM: nothing; the PM never sees code.
AI: in `deliver.execute`, tag every touched piece with the id of the node
it serves. In `deliver.trace`, find a node's affected code only by tag; a
proposed rule has no tag, so its impact is found by reading every tagged
piece against the rule. Untagged code is reported as a finding in
`deliver.verify`.

## Place in the system
The link between the business side and the code side. The set of tags is
the map of which code implements which logic.
