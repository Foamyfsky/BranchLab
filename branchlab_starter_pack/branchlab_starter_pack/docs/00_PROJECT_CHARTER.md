# Project Charter

## One-line product

BranchLab lets a user pause a living real-world network, apply an operational intervention,
fork the timeline under controlled randomness, and see where, when, and why the futures diverge.

## Category

Primary submission category: **Education**.

The educational advance is model-based, counterfactual learning. The user learns feedback loops,
queues, uncertainty, delayed consequences, bottlenecks, and local-versus-system trade-offs by
manipulating a transparent executable model rather than reading generated answers.

## Primary user

A curious learner, student, teacher, planner, or technically interested member of the public who
wants to understand how connected systems react to interventions.

## Competition experience

The first curated world is **Sydney Pulse**:

- a real TfNSW public-transport subset imported from GTFS;
- a sixty-minute scenario;
- a demand surge near an event location;
- a transfer bottleneck;
- no more than four intervention types;
- a challenge to prevent network collapse with limited interventions.

## Core loop

1. Load a curated world.
2. Observe the baseline.
3. Pause at any tick.
4. Select or describe an intervention.
5. Inspect the proposed typed change.
6. Fork the timeline.
7. Run baseline and child branch under common exogenous randomness.
8. Compare representative trajectories and paired Monte Carlo effects.
9. Inspect first divergence, propagation chain, equations, and trade-offs.
10. Fork again or export the experiment tree.

## Product principles

- **AI is the engine assistant, not the interface.**
- **The simulation computes; GPT interprets.**
- **The user changes operational concepts, not opaque distribution parameters.**
- **Mathematics is revealed on demand, not hidden and not forced on beginners.**
- **Aesthetic movement communicates state rather than decorating a dashboard.**
- **Every result carries an assumption and provenance trail.**

## Scientific claim boundary

BranchLab performs scenario analysis under a simplified stochastic transport model. Real GTFS
supply data does not make synthetic passenger demand real. The product must display a World
Fidelity panel and must not describe a result as an operational forecast, engineering safety
assessment, or causal estimate from observational city data.

## Definition of MVP completion

A fresh user can:

- open Sydney Pulse;
- watch a real imported route network evolve;
- pause and change service frequency or station throughput;
- create a child branch;
- see both realities remain synchronised;
- identify a downstream unintended effect;
- open Math Lens and understand the queue update;
- view a paired uncertainty summary;
- receive a grounded GPT-5.6 explanation;
- export and reload the experiment recipe.
