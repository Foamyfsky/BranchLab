# Status

BranchLab currently provides a deterministic, fully observed reference for the three-room particle world. The authoritative experiment description is [docs/particle-world.md](docs/particle-world.md); setup and run commands are in [README.md](README.md).

## Implemented capabilities

- A linear well-mixed A–B–C transport model with symmetric exchange, background removal, and one piecewise-constant cleaner intervention.
- Exact matrix-exponential state propagation and augmented-state integration of per-room concentrations.
- Exhaustive evaluation of a no-cleaner reference and nine predetermined two-half schedules for two mirrored initial states and 1-hour and 5-hour horizons.
- A reproducible 40-record CSV with room-level and mean outcomes, plus a four-panel figure for the `(2, 2, 2.5)` initial state.
- Separate identification of the best fixed placement and the best of the nine tested schedules.

Supplied initial conditions and synthetic parameters, cleaner interventions, deterministic state trajectories, and calculated outcomes remain distinct. The code contains no observation process or inferred state.

## Verification

The verification workflow covers exchange-only mass conservation, isolated-room analytic exponential decay, concentration nonnegativity within numerical tolerance, equal active-schedule budgets, independent branch inputs, A/C mirror symmetry, and supplied fixed-placement reference losses. It also checks fresh-environment installation, experiment reproduction, source/test compilation, dependency consistency, documentation links, generated-data stability, figure readability, and Git whitespace.

Latest verification used a temporary Python 3.12.14 virtual environment created independently of the working environment. Editable installation from `pyproject.toml`, the experiment, all seven unit tests, compilation, and `pip check` passed; the temporary environment was then removed. Reproduction retained the committed 40-row CSV content exactly (SHA-256 `858c739f8a2aa5fd8e2686743f2914af631d927c10714b7532e327941b70be4a`). The regenerated 2450×1550 figure was inspected at full and reduced display sizes.

## Unresolved and out of scope

- Parameters are synthetic and have no measured-data provenance or calibration.
- No partial-observation model, hidden-state inference, uncertainty propagation, learned dynamics, adaptive controller, or learned policy is implemented.
- Continuing sources, multiple particle classes or cleaners, arbitrary switching times, time-varying exchange, nonlinear filter behavior, occupancy, and safety thresholds are untested.
- The well-mixed, fixed-exchange, constant-capacity assumptions require evidence before any real-building application.
- Exhaustive enumeration is limited to the current two-half action menu and does not establish general optimality.
