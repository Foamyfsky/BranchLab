# BranchLab Engineering Contract

All Codex work must follow this file.

## Product identity

BranchLab is not a chat application and not a transit-operations forecasting product.
It is an educational scenario-analysis environment that lets users intervene in a living
network, fork a timeline, and inspect how effects propagate under explicit assumptions.

The competition world is **Sydney Pulse**, based on a curated subset of real TfNSW GTFS
network and schedule data. Passenger demand may be synthetic or calibrated, and the UI must
state its provenance.

## Non-negotiable invariants

1. GPT-5.6 is never the simulation engine.
2. The simulation core must be a pure TypeScript package with no React, map, or OpenAI dependency.
3. A run with the same world version, seed, initial state, and interventions must reproduce the
   same result.
4. A child branch begins from the exact parent state at its fork tick.
5. Parent branch state and history are immutable.
6. A no-op child branch must match its parent after the fork.
7. Paired baseline/fork comparisons use common exogenous random streams.
8. Passenger conservation must be checked:
   initial + generated = waiting + onboard + completed + abandoned.
9. Every numerical parameter must have a unit, meaning, default, valid range, and provenance.
10. Real, inferred, calibrated, and synthetic data must be visibly distinguished.
11. The 3D renderer is a view layer and must not mutate simulation time or state.
12. User natural language never directly changes the world. GPT proposes a typed intervention;
    application code validates it; the user confirms it.
13. API keys remain server-side and must never use a `NEXT_PUBLIC_` prefix.
14. The application must remain usable in mock-AI mode without an OpenAI key.
15. The project must not claim operational safety certification or real-world prediction accuracy.
16. Every round ends with lint, typecheck, relevant tests, documentation updates, and a report.
17. Do not begin a later round until the current round's acceptance gate passes.
18. Prefer simple, inspectable implementations over hidden framework magic.

## Required end-of-round report

Every Codex round must end with:

- **Status:** PASS / PARTIAL / BLOCKED
- **Goal completed**
- **Files created or changed**
- **Important decisions**
- **Commands run**
- **Lint/typecheck/test results**
- **Manual actions required from Robert**
- **Data or credentials still required**
- **Known limitations and risks**
- **Exact prerequisites for the next round**
- **Suggested next prompt**

Codex must also update:

- `docs/PROGRESS.md`
- `docs/MANUAL_ACTIONS.md`
- `docs/DECISION_LOG.md`

## Scope control

### Must ship

- Deterministic reference world
- Generic GTFS importer
- One curated Sydney Pulse world pack
- Markov-modulated stochastic demand
- Capacity-constrained queue and service evolution
- Immutable timeline forks
- Common-random-number paired comparison
- First-divergence and trade-off analysis
- 2.5D/3D geographic visualisation
- Contextual interventions
- Math Lens, Causal Lens, and World Fidelity panel
- Server-side GPT-5.6 structured intervention parsing and explanation
- Export/import of experiment recipes
- Tests, setup instructions, data attribution, and demo reset

### Stretch

- Browser GTFS upload
- Frozen GTFS-Realtime snapshot
- Custom 3D train models
- Ghost overlay comparison
- Additional world packs
- Real ridership calibration data

### Not in the event version

- Full-city operational digital twin
- Safety-critical recommendations
- User accounts or payments
- Multiplayer
- State merging between branches
- Native mobile app
- Arbitrary AI-generated simulators
