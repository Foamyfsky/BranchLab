# System Architecture

## Repository layout

```text
branchlab/
├── apps/
│   └── web/                       Next.js application and server-only AI routes
├── packages/
│   ├── schemas/                   Zod schemas and versioned serialisation contracts
│   ├── simulation-core/           deterministic clock, RNG streams, snapshots, branches
│   ├── metro-model/               demand, routing, queues, vehicles, metrics
│   ├── gtfs-importer/             CLI and GTFS validation/normalisation
│   ├── experiment-analysis/       paired Monte Carlo and divergence analysis
│   └── reference-world/           tiny fictional fixture for tests and early UI
├── data/
│   ├── raw/                       downloaded data; gitignored
│   └── processed/
│       └── worlds/                compact, versioned curated world packs
├── docs/                          shared source of truth, readable in Obsidian
├── prompts/                       one prompt per Codex round
├── scripts/                       orchestration and data-preparation commands
├── AGENTS.md
├── pnpm-workspace.yaml
└── package.json
```

Do not add Turborepo unless build times or task orchestration actually require it. A plain pnpm
workspace is sufficient.

## Package boundaries

### `schemas`

Owns stable contracts:

- world manifest;
- station, edge, route, and service schemas;
- intervention schemas;
- simulation event schemas;
- branch recipe and export schemas;
- AI response schemas.

### `simulation-core`

Owns mechanics independent of transit:

- logical ticks;
- deterministic named random streams;
- state snapshots/checkpoints;
- immutable branch ancestry;
- replay;
- event recording;
- versioned experiment serialisation.

It must not import React, MapLibre, deck.gl, or OpenAI.

### `metro-model`

Owns the transport domain:

- Markov demand regimes;
- Bayesian parameter inputs/posteriors;
- origin-destination demand;
- route choice;
- trains and schedules;
- queue conservation;
- boarding/alighting;
- dwell and downstream delay;
- metrics and Math Lens records.

### `gtfs-importer`

Owns:

- ZIP/CSV parsing;
- GTFS validation;
- active-service date/time filtering;
- platform-to-station normalisation;
- directed graph creation;
- route-shape extraction;
- world-pack export;
- data-provenance metadata.

### `experiment-analysis`

Owns:

- paired seed schedules;
- common-random-number replications;
- effect distributions;
- uncertainty intervals;
- probability of improvement;
- first and largest divergence;
- causal propagation records.

### `apps/web`

Owns:

- MapLibre and deck.gl rendering;
- React controls and HUD;
- branch selection and playback state;
- server-only OpenAI routes;
- mock AI mode;
- demo reset;
- import/export UI.

## State separation

There are three distinct state categories:

1. **Simulation state** — immutable logical world history.
2. **Experiment state** — branches, interventions, comparisons, and selected result.
3. **UI state** — camera, selected object, open panel, animation mode, and playhead.

Never store simulation truth in UI animation objects.

## Rendering strategy

- MapLibre: map, camera, style, and building extrusion.
- deck.gl: routes, animated trips, queue columns, pressure halos, and difference overlays.
- React: HUD, intervention matrix, timeline, lenses, and controls.
- React Flow: expanded experiment-tree view only.

## AI boundary

The web app sends compact typed evidence to server routes. Server routes call the OpenAI Responses
API with Structured Outputs. Returned objects are validated with Zod before being shown.
