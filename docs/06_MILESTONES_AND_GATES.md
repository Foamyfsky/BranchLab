# Milestones and Acceptance Gates

## Round 00 — Repository bootstrap

Build the workspace, tracked documents, toolchain, CI skeleton, environment examples, and reporting
protocol. No simulation feature work.

**Gate:** clean install; lint/typecheck/test scripts exist; docs and package boundaries match the
architecture; no secrets.

## Round 01 — Deterministic reference world

Implement schemas, named deterministic RNG streams, clock, tiny eight-station fixture, initial state,
and basic replay.

**Gate:** identical seed produces byte-equivalent serialisable state and metrics.

## Round 02 — GTFS importer

Implement a generic CLI using generated tiny GTFS fixtures first, then run it against the manually
downloaded TfNSW ZIP.

**Gate:** validates feed, filters service date/time/area, groups stops, constructs directed edges,
extracts shapes/schedules, emits deterministic versioned world packs and a candidate-subset report.

## Round 03 — Metro scientific kernel

Implement demand regimes, arrivals, OD cohorts, route choice, vehicles, queues, boarding/alighting,
dwell, delays, conservation, metrics, and Math Lens records.

**Gate:** all scientific tests pass and the reference-world surge has a plausible propagation story.

## Round 04 — Sydney Pulse curation and calibration

Use importer output to select a real subset, create demand prior and event scenario, tune only within
documented ranges, and create the World Fidelity data.

**Gate:** a 60-minute baseline is stable initially and visibly congests after the event.

## Round 05 — Branch engine and paired analysis

Implement immutable ancestry, exact snapshot/replay, interventions, common random streams, paired
Monte Carlo, first divergence, trade-offs, and experiment export/import.

**Gate:** no-op equivalence, parent immutability, shared randomness, and recipe replay tests pass.

## Round 06 — Web shell and 2.5D world

Build the Next.js shell, MapLibre/deck.gl view, playback controls, object selection, baseline
visualisation, and diagnostic placeholders.

**Gate:** the user can understand congestion and vehicle motion without opening raw charts.

## Round 07 — Intervention and fork UX

Build contextual controls, confirmation, branch lanes, split reality, lenses, challenge budget, and
signature fork animation.

**Gate:** a new user can perform pause → intervene → fork → compare without instructions.

## Round 08 — GPT-5.6 integration

Add server-side Responses API calls, Zod Structured Outputs, intervention proposals, grounded
explanations, experiment suggestions, mock mode, and error/cost controls.

**Gate:** AI output cannot mutate state directly; invalid proposals are rejected; app works without AI.

## Round 09 — Submission hardening

Add end-to-end tests, performance checks, deployment, README, data attribution, scientific
limitations, demo-reset path, scripted scenario, and `/feedback` evidence.

**Gate:** a judge can clone, configure, run, fork, compare, and reproduce the prepared scenario.
