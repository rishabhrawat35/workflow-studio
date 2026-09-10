# Component

## Definition
One unit of code under one system (frontend, backend, service), doing one
job, reusable by any node that needs it, with its tests beside it. Tagged
by the id of every node it serves. The way the code side is organised so
that nothing is written twice and an AI agent can read it.

## Inputs
The architecture file's systems-and-structure section (which systems
exist, the folder and component convention); the plan's list of reused and
new components.

## Outputs
`code/<system>/<component>/` (**convention**), and `code/COMPONENTS.md`
generated at `deliver.commit` by `framework/tools/components_index.py`:
component → system → nodes served. That index is the dev-side document.

## How to interact
PM: nothing; the PM sees components only by their plain names in the plan.
AI: at `deliver.trace`, search existing components for ones that already do
part of the job; at `deliver.plan`, state reused versus new; at
`deliver.challenge-plan` and `deliver.verify`, a new component that
duplicates an existing one is a finding; at `deliver.execute`, build under
the system's folder, reuse what the plan named, tag every touched piece;
at `deliver.commit`, regenerate the index. Environment variables and
secrets are read from where the architecture file says, never stored in a
component.

## Place in the system
The code side's unit of structure, mirroring the node as the business
side's unit. Tags connect the two; the index is the map.
