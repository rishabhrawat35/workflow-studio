# Acceptance

## Definition
The final PM gate, `deliver.accept`: the PM decides whether the delivered
change is done, either by using the running product or, where nothing can
be used (a background job, an event, a rule change touching no node), by
judging the evidence the AI shows.

## Inputs
Code that has passed `deliver.passes`; the run instructions in the
architecture file; the approved node(s) and their confirmed acceptance
criteria.

## Outputs
The PM's answer: accepted (→ `commit`); not matching (→ `execute`);
changed mind about the logic (→ Define); changed mind about the rule (→
Foundation); stop (→ `drop`).

## How to interact
PM: use the changed flow as a user would and compare with the approved
node and its criteria; or read the evidence: test output, logs, a recorded
run. For a rule delivery, the evidence is that every tagged piece still
passes its criteria.
AI: start the product using the architecture file's run instructions and
tell the PM, in plain language, where to go and what to try; where nothing
can be tried, present the evidence. Do not describe the code.

## Place in the system
Nothing is done that the PM has not seen work or seen evidence for. It is
the third and last PM gate.
