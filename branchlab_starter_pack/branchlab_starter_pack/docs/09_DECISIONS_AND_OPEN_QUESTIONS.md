# Decisions and Open Questions

## Fixed decisions

- Category: Education.
- MVP world: Metro Pulse / working title Sydney Pulse.
- Product type: web application with game-like simulation.
- Core engine: controlled discrete-time stochastic transport model.
- AI role: typed intervention proposal and grounded explanation only.
- Simulation language: TypeScript.
- Renderer: MapLibre + deck.gl; Three.js only as a later enhancement.
- Real data: static GTFS supply and geography.
- Demand: synthetic/calibrated and transparently labelled.
- Fork fairness: immutable histories and common random numbers.
- First comparison mode: split reality.
- Repository is the Obsidian vault and source of truth.

## Open questions that must be resolved by evidence

### Final Sydney subset

Resolve after the GTFS importer produces candidate reports. Criteria:

- 10–25 stations;
- 2–3 intersecting services;
- clear transfer bottleneck;
- active trips in the chosen window;
- visually coherent map bounds;
- plausible event-surge story.

### Exact intervention set

The four categories are fixed, but target ranges and costs require simulator tuning.

### Demand calibration

Determine whether an accessible ridership/count dataset can be used. The MVP must remain valid with
synthetic priors.

### Challenge thresholds

Set only after repeated baseline and intervention runs. They must create a solvable challenge with a
non-obvious trade-off.

### Map delivery

Begin with a keyless online style. Decide later whether the demonstration area requires local
GeoJSON/tiles for reliability.

### Simulation tick and replication count

Starting targets are 10-second ticks and 32 paired replications. Confirm browser performance before
freezing.

### Name

“BranchLab” is the product name. “Sydney Pulse” is the curated world name unless a stronger name is
chosen before visual branding is frozen.
