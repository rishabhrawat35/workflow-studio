# Glossary

## Definition
The terms and things the product deals with, one meaning each, so every
logic node uses the same words with the same meaning.

## Inputs
The PM's list in `foundation.glossary` for a new product (reached when
`define.sort` finds no architecture file); afterwards, additions proposed in
`define.write` and approved by the PM in `define.approve`.

## Outputs
The glossary on the business side (`glossary.md`, **convention**), saved at
`foundation.save` and, for additions, at `define.commit` together with the
node that introduced them.

## How to interact
PM: write the first list in Foundation; approve or reject proposed
additions when approving a node.
AI: use each glossary term with its glossary meaning. In `define.write`,
propose any product term the discussion introduced that is not yet
defined; in `define.challenge`, report a term used in a node that is
neither in the glossary nor proposed. Never add a term without PM
approval.

## Place in the system
Set in Foundation, grown through Define. The shared language between what
the PM says and what the AI writes.
