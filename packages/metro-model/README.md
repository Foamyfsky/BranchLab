# `@branchlab/metro-model`

## Ownership

Owns future transit-domain science: demand regimes, queues, vehicles, route choice, dwell, delay,
passenger conservation, metrics, and Math Lens records.

## Forbidden dependencies

- No React, Next.js, MapLibre, deck.gl, or HUD state.
- No OpenAI SDK or direct AI-generated simulator code.
- No raw GTFS file reads; consume normalized importer/world-pack outputs instead.
- No branch ancestry implementation; use `@branchlab/simulation-core` once it exists.
