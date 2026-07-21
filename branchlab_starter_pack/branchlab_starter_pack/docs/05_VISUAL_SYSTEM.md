# Visual System

## Direction

A **futuristic diagnostic instrument wrapped around a cyber-city diorama**.

The supplied references suggest:

- dark violet/black environment;
- cyan, blue, magenta, amber, and warm-white luminous accents;
- compact isometric city blocks;
- monospaced diagnostic labels;
- scanline, waveform, grid, and machine-readout motifs;
- small precise panels rather than generic large cards;
- motion as information;
- dense atmosphere without sacrificing hierarchy.

Do not copy any reference screen literally. Extract design principles.

## Visual hierarchy

1. Living city and active flows.
2. Current time and branch relation.
3. Selected object and intervention.
4. First divergence and trade-off.
5. Equations and assumptions on demand.

## Proposed palette

- Canvas: deep violet-black.
- Baseline: warm amber/ivory.
- Active fork: electric cyan.
- Critical pressure: magenta-red.
- Healthy flow: blue-green.
- Panels: nearly black with thin low-opacity borders.
- Text: off-white, with muted blue-grey metadata.

Exact tokens should be stored as CSS variables and checked for contrast.

## Typography

- Interface/display: geometric sans.
- Diagnostic/data: monospaced font with tabular numerals.
- Avoid pixel fonts for paragraphs.
- Avoid illegibly small decorative text.

## Core layers

- MapLibre pitched geographic view.
- Extruded OSM-derived buildings.
- deck.gl transit paths and animated trips.
- Queue columns at stations.
- Pressure halos.
- Representative passenger-flow trails.
- Selected-object scan and focus animation.
- Split-reality comparison.

## Signature fork animation

1. Freeze logical playback.
2. Desaturate the city briefly.
3. Sweep a diagnostic scan across the intervention target.
4. Duplicate baseline and child visual states.
5. Mark the intervention delta.
6. Tint baseline warm and child cyan.
7. Resume both from the same logical tick.
8. Emit a pulse at the first meaningful divergence.

The animation must not advance or mutate simulation state.

## Motion semantics

- station breathing: normal activity;
- faster pulse: increasing load;
- expanding queue column/ring: accumulating queue;
- thicker path trail: higher flow;
- unstable edge flicker: disruption;
- ripple: causal divergence;
- translucent envelope: uncertainty.

## Layout

- Header: world, time, fidelity.
- Left: contextual intervention matrix.
- Centre: living geographic world.
- Right: diagnostic inspector and lenses.
- Bottom: transport controls and branch lanes.
- Expanded experiment tree: separate modal/panel.

## Implementation progression

1. 2D routes and stations.
2. Pitched camera and building extrusion.
3. Animated vehicle trips.
4. Queue columns and pressure halos.
5. Futuristic HUD.
6. Split-reality view.
7. Signature fork motion.
8. Optional custom 3D models only after all gates pass.
