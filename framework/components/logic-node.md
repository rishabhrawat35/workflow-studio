# Logic node

## Definition
One unit of business logic in the logic tree: a stable id, a plain-language
description of what the product must do, its acceptance criteria (see
`acceptance-criteria.md`) and its placement. It holds only what follows
from the discussion with the PM: nothing the PM did not say or approve. A
cross-cutting change edits several nodes together as a node set, with one
approval. A node whose capability is removed is marked retired and stays in
the tree.

## File format (convention)
Markdown. First line `# <title>`. A `Status:` line: `approved, not yet
delivered`, `delivered <version>`, or `retired <date>`. A description in
plain language. A `## Acceptance criteria` section, one criterion per
line. Optional `## Links` to other node ids. The id is the file stem.

## Inputs
The request stated at `define.intake`, `define.discuss` (the PM's words),
the glossary, the architecture file, the existing logic tree.

## Outputs
One file under `logic/` (**convention**), saved with its history at
`define.commit` after PM approval. A later edit is a new version of the same
file. The node version is the save that `define.commit` made
(**convention**).

## How to interact
PM: read it in `define.approve` as a non-technical document; approve
(confirming the criteria), change or add criteria (it goes back through
`challenge`), send it back to discussion with what to change, or stop.
AI: write it in `define.write` with glossary terms, checked against the
architecture file, with a proposed placement; put it through
`define.challenge`, which also lists every other node the change affects,
before the PM sees it;
keep it uncommitted until `define.approve` (**convention**); never change it
from the code side. If seeing the running product changes the PM's mind
(`deliver.accept`), the node goes back through Define.

## Place in the system
One of Deliver's three inputs (approved logic, a fix against delivered
logic, a proposed rule). The change record that delivers it names its
version.
