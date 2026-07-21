# Product Specification

## Main scenario

The exact Sydney subset is selected only after the importer can inspect the current GTFS feed.
The curated subset should contain:

- 10–25 simulation stations;
- 2–3 intersecting services;
- one legible transfer bottleneck;
- one event or demand-surge station;
- one 60-minute operating window;
- clear route geometry and active scheduled trips.

Do not hard-code fictional station names into the production world. Keep an eight-station fictional
reference world in tests and development.

## User-facing controls

The user manipulates operational quantities:

1. **Service headway** — e.g. six minutes to four minutes.
2. **Vehicle capacity** — increase/decrease capacity for a service.
3. **Station throughput** — gate or boarding processing limit.
4. **Network/guidance intervention** — close an edge or alter perceived route cost.

Optional event controls can be enabled in Explore mode but should not be necessary for the main
challenge.

## Interaction model

- Clicking a line opens service controls.
- Clicking a station opens throughput, queue, and fidelity information.
- Clicking an edge opens closure/guidance controls.
- Natural language opens a proposed-intervention card, not a chat transcript.
- The user must confirm before forking.
- Branches never merge state.
- An intervention recipe may be copied and replayed on a different branch.

## Views

### Living World

Pitched geographic city view with route geometry, vehicles, queue columns, passenger-flow traces,
crowd-pressure halos, and selected-object diagnostics.

### Timeline and Branch Lanes

Time scrubber plus branch ancestry. A branch lane starts at its fork tick and remains aligned with
the parent's logical time.

### Split Reality

Baseline and selected branch share time and camera. This is the first comparison mode to complete.

### Diagnostic Inspector

Shows first divergence, largest effect, trade-off, paired uncertainty, and selected-station details.

### Math Lens

Shows the exact update at a selected station and tick:

`next queue = previous queue + arrivals + transfers - boarded - abandoned`.

### Causal Lens

Shows a temporal dependency chain grounded in recorded simulator events.

### World Fidelity

Labels each data layer as real, derived, calibrated, synthetic, stochastic, or disabled.

## Challenge success

The initial challenge should include:

- an intervention budget;
- a maximum number of forks;
- a peak crowd-pressure limit;
- a minimum completed-passenger fraction;
- at least one trade-off so that a locally obvious intervention is not globally optimal.

Exact thresholds are tuned after the first complete simulation, not invented in advance.

## Accessibility and performance

- Full functionality with mouse; keyboard support for play/pause and timeline.
- Do not encode baseline versus branch only by colour.
- Target a stable demonstration on the recording machine.
- Aggregate passengers mathematically; render representative particles only.
- Keep the selected subset small enough for smooth browser execution.
