# Acceptance criteria

## Definition
Part of every logic node: sentences of the form "when X happens, Y must be
true" that say what the product must do for the node to count as done.

## Inputs
What the PM says in `define.discuss` must be true for the capability to
count as working; proposed by the AI in `define.write`; confirmed by the PM
at `define.approve`, where the PM may add or remove any (changed criteria go
back through `define.challenge` before saving).

## Outputs
The criteria inside the node. Tests written in `deliver.execute` check them;
`deliver.verify` and `deliver.passes` judge the code against them; the PM
uses them at `deliver.accept` to judge the running product or the
evidence.

## How to interact
PM: say in discussion what "working" means; at `define.approve`, confirm,
add or remove criteria until they say exactly that. Nothing is saved until
the PM confirms them.
AI: propose one criterion per behaviour the PM described, in the PM's
words; `define.challenge` reports criteria that cannot be verified. In
`deliver.verify`, check the result against the agreed criteria of every
touched node and the architecture rules, never against the plan.

## Place in the system
The contract between the business side and the code side. They are how the
PM judges code without reading it.
