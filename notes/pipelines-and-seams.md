# Pipelines and Seams

The tension between clean declarative programming and messy real-world interactions, and where the interesting problems live.

## The pipeline ideal

Unix got it right: data comes in, something happens, data comes out. `cat foo | grep bar | sort | uniq -c` — you can read it and know what it does. The spec and the implementation are the same thing. No gap between declaration and execution.

Functional programming follows the same pattern at a smaller scale. Function composition is pipelines. Data in, data out, no surprises.

Most software tries to be pipelines. And it works for a lot of things.

## The declaration-execution gap

The paradigms most fun to think in — logic programming, pure functional — exist in clean abstract space. Relationships, constraints, transformations. No time, no state, no side effects.

The real world is nothing but interactions. Things happen in order. State changes. External systems do unpredictable things.

Every pure paradigm has a boundary problem: how to talk to the impure world without lying about what you are. Prolog's cut operator, Erlang's message passing, Haskell's monads — all different answers to the same question.

LLM prompt engineering has the same structure. You declare what you want, the machine executes, the result often differs from intent, and the execution path is opaque.

## Where the seams leak

The pipeline ideal breaks at interaction points: databases, networks, user interfaces, hardware. You can wrap these in pipeline-shaped interfaces but the abstraction leaks.

- A database is a pipeline endpoint until two processes write at the same time
- An API is a pipeline until the network retries and sends the same request twice
- A job queue is a pipeline until a worker crashes mid-task

Teams paper over these with transactions, idempotency keys, retries with backoff, eventual consistency. It works until it doesn't. The bugs that survive live in the gaps between pipeline stages.

## TLA+ and formal verification

TLA+ (Leslie Lamport's specification language) addresses the non-pipeline parts directly. You specify behavior as states and temporal properties, the model checker explores every possible execution, finds violations.

The problem: TLA+ asks you to think in temporal logic and set notation. Brutal learning curve. Most programmers won't write their system twice in a harder language.

The opportunity: LLMs can write TLA+ specs, run model checkers, interpret counterexamples in plain language. The expensive part — learning the notation, translating mental models to formal logic, reading results — is exactly what machines are good at. Nobody has built the tool that hides TLA+ behind a natural language interface yet.

## Practical takeaway

Most real systems are mostly pipelines with a few non-pipeline seams. Don't try to make everything formally verifiable. Make pipelines easy, make the non-pipeline parts visible, focus attention where pipelines break down.

The catastrophic bugs — the ones you can't reproduce, can't debug from logs — live in those seams. That's where formal tools earn their keep, even if most of the system doesn't need them.
