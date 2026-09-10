# Preview

## Definition
The product running so the PM can click through the changed flow before
deciding whether to accept a delivery.

## Inputs
Code that has passed `deliver.passes`; the run instructions in the
architecture file.

## Outputs
The PM's decision in `deliver.accept`: accepted; does not match the approved
logic (back to `deliver.execute`); changed the PM's mind about the logic
(back to Define through `deliver.back-to-define`); or changed the PM's mind
about the rule (back to Foundation through `deliver.back-to-foundation`).

## How to interact
PM: use the changed flow as a user would and compare it with the approved
node and its acceptance criteria.
AI: start the product using the architecture file's run instructions and
tell the PM, in plain language, where to go and what to try
(**convention**). Do not describe the code.

## Place in the system
The last step before the final PM gate. Acceptance is given on the working
product, not on a written summary.
