# History

## Definition
Every file on both sides is saved with its history. That history is git,
with no separate versioning scheme (**convention**).

## Inputs
Saves at `foundation.save`, `define.commit`, `deliver.commit` and
`deliver.drop`; and whenever a change record or the queue changes
(`define.intake`, `define.exists`, every status update, the returns
through `deliver.back-to-define` / `back-to-foundation`) (**convention**).

## Outputs
For any file: what it said at any earlier point and when it changed.
`deliver.trace` uses it to compare the business side with the last
delivered version.

## How to interact
PM: ask "what changed in X" or "what did we build for X"; never touch git.
AI: `foundation.save` saves the architecture file and glossary;
`define.commit` saves the node(s), any approved glossary additions and the
regenerated logic index (**convention**), business side only; `deliver.commit` saves code,
tests, the completed change record and the regenerated component index
together, naming each node version delivered, and writes an accepted rule
into the architecture file in the same commit; `deliver.drop` marks the
record dropped, reverts or removes the node, or discards the proposed rule,
in one save (**convention**). A proposed rule is never saved before
`deliver.commit`. Decision files are written in the same save as the step
that finalised them and are never edited afterwards; a change is a new
file that supersedes the old. Every step writes its output to disk before the next
starts, so resume is from the last completed step (**convention**).

## Place in the system
The memory of the framework. Traceability, audit and "what changed" all read
from it.
