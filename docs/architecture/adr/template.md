# [ADR-XXXX] [Short title of solved problem and decision]

* **Status:** [Draft | Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-YYYY]
* **Date:** [YYYY-MM-DD]
* **Deciders:** [List of deciders / Specialist roles]
* **Consulted:** [Specialist panel roles consulted]
* **Informed:** [Team / Stakeholders informed]

## Context and Problem Statement

[Describe the context and problem statement in 2-3 sentences. What forces are at play, what banking or technical requirement drives this decision?]

## Decision Drivers

* [Driver 1, e.g. strict financial precision and avoidance of rounding drift]
* [Driver 2, e.g. auditability and BCBS 239 compliance]
* [Driver 3, e.g. performance and restartability]

## Considered Options

* Option 1: [Name of option 1]
* Option 2: [Name of option 2]
* Option 3: [Name of option 3]

## Decision Outcome

Chosen option: "[Option X]", because [justification. e.g., only option that meets constraint Y without incurring complexity Z].

### Positive Consequences

* [e.g. Invariant guaranteed at the database level]
* [e.g. Predictable query plans and clean index usage]

### Negative Consequences / Trade-offs

* [e.g. Additional storage required for reversal entries]
* [e.g. Increased schema strictness requiring explicit migrations]

## Oracle / Enterprise Bridge Note

[Explain how this concept compares to the Oracle RDBMS, PL/SQL, or traditional enterprise banking architectures (e.g. Oracle Sequences vs Identity columns, PL/SQL packages vs Python service modules, Autonomous Transactions vs Outbox).]

## Pros and Cons of the Options

### [Option 1]

* Good, because [argument a]
* Bad, because [argument b]

### [Option 2]

* Good, because [argument a]
* Bad, because [argument b]
