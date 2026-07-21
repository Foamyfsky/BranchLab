# `@branchlab/simulation-core`

## Ownership

Owns future deterministic mechanics that are independent of transit: logical ticks, named random
streams, snapshots, immutable branch ancestry, replay, event recording, and experiment
serialization.

## Forbidden dependencies

- No React, Next.js, MapLibre, deck.gl, Three.js, or browser rendering code.
- No OpenAI SDK or API routes.
- No GTFS parsing or transit-domain demand logic.
- No mutation of parent branch history once branch mechanics are implemented.
