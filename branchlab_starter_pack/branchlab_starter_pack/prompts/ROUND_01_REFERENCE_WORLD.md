# Round 01 — Deterministic Reference World

Read the engineering contract, architecture, scientific model, progress, and decision log.

Implement the smallest transport-independent deterministic foundation plus the fictional
eight-station reference world. Do not use GTFS yet.

## Build

- versioned Zod schemas for world manifest, station, directed edge, service, intervention placeholder,
  and serialisable simulation state;
- deterministic named random streams whose values depend on world seed, stream name, tick, and
  entity identifiers rather than mutable call order;
- logical tick runner;
- immutable initial-state creation;
- tiny reference world matching the planning example;
- basic scheduled vehicle movement and a minimal metric;
- serialisation suitable for equality testing;
- documentation of RNG design.

## Tests

- same seed and inputs produce identical serialised results;
- different seed changes stochastic outputs where expected;
- random streams for arrivals and delays do not interfere;
- world schemas reject invalid references;
- runner does not depend on wall-clock time.

Do not implement realistic passenger queues, Bayesian calibration, UI, branches, or AI.
Stop when the acceptance gate passes.
