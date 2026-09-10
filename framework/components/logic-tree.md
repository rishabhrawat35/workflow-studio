# Logic tree

## Definition
The nested structure of all business logic for one product. A top-level
entry is a page or capability; under it sit its sub-flows, each its own
node (e.g. login page > logout, forgot password).

## Inputs
Logic nodes approved in `define`; the position chosen in `define.discuss`.

## Outputs
The `logic/` folder of the business side: one file per node, folders for
nesting (**convention**). The node id is the file stem, unique across the
tree; the folder is the placement. The tree is what "everything the product
does" looks like when read top to bottom.

## How to interact
PM: decide where a capability sits during `define.discuss`; the AI's
proposed placement (existing parent or new header, with its reason) is
confirmed at `define.approve`.
AI: at `define.sort`, search the tree so an existing node is never built
twice; at `define.write`, propose the placement and a split when a node is
too large; at `define.challenge`, report a placement that makes the tree
harder to read and list every node a change affects. A node keeps its id
if moved; never rename an id (**convention**). Regenerate `logic/INDEX.md`
with `framework/tools/logic_index.py` at `define.commit` (**convention**):
that index, with each node's criteria, is the knowledge-transfer document
and the list of built use cases.

## Place in the system
The whole business logic seen as one structure. Code is organised by the
same ids through tags, so the tree and the code map onto each other.
