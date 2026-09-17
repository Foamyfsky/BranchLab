# Status

BranchLab currently provides a deterministic, fully observed reference for the three-room particle world. The authoritative experiment description is [docs/particle-world.md](docs/particle-world.md); setup and run commands are in [README.md](README.md).

## Implemented capabilities

- A linear well-mixed A–B–C transport model with symmetric exchange, background removal, and one piecewise-constant cleaner intervention.
- Exact matrix-exponential state propagation and augmented-state integration of per-room concentrations.
- Exhaustive evaluation of a no-cleaner reference and nine predetermined two-half schedules for two mirrored initial states and 1-hour and 5-hour horizons.
- A reproducible 40-record CSV with room-level and mean outcomes, plus a four-panel figure for the `(2, 2, 2.5)` initial state.
- Separate identification of the best fixed placement and the best of the nine tested schedules.
- A local Streamlit and Plotly dashboard for fixed-scenario creation, timestamped cleaner location/on-off controls, bounded playback, pause, exact advancement, and run-to-end operation.
- Independent named forks that preserve the current concentration, room integrals, actual clean-air budget, current control, and copied action history.
- Partial and completed metrics, a matching no-cleaner reference, branch histories and event markers, rate-contribution explanations, and completed-branch comparisons.
- Explicit export and validated import of a versioned JSON experiment, including model metadata, units, branch lineage, ordered actions, and deterministic replay checks.

Supplied initial conditions and synthetic parameters, cleaner interventions, deterministic state trajectories, and calculated outcomes remain distinct. The code contains no observation process or inferred state.

## Verification

The verification workflow covers exchange-only mass conservation, isolated-room analytic exponential decay, concentration nonnegativity within numerical tolerance, equal fixed-protocol budgets, independent branch inputs, A/C mirror symmetry, and supplied fixed-placement reference losses. Interactive-session checks cover fork continuity and independence, incremental versus direct propagation, exact action timing, pause behavior, horizon stopping, actual on/off budget accounting, zero inputs, deterministic same-time controls, branch-lineage validation, and JSON replay equivalence.

The current verification installed the `ui` extra, reproduced the fixed experiment, compiled the source and tests, passed all 12 unit tests and `pip check`, and retained the 40-row CSV byte-for-byte (SHA-256 `858c739f8a2aa5fd8e2686743f2914af631d927c10714b7532e327941b70be4a`). A real 1440×900 browser walkthrough advanced C to 2.5 h, forked, completed C→C and C→A, exported and re-imported JSON, and confirmed losses of 5.39271546 and 5.07003394 with 500 m³ consumed by each branch. Controls, units, legends, timeline, comparison, rate explanation, and the README screenshot were inspected in the rendered dashboard.

## Unresolved and out of scope

- Parameters are synthetic and have no measured-data provenance or calibration.
- No partial-observation model, hidden-state inference, uncertainty propagation, learned dynamics, adaptive controller, or learned policy is implemented.
- Interactive state is local and in-memory until the user explicitly downloads JSON; there is no database, authentication, multi-user synchronization, or background service.
- Continuing sources, multiple particle classes or cleaners, arbitrary switching times, time-varying exchange, nonlinear filter behavior, occupancy, and safety thresholds are untested.
- The well-mixed, fixed-exchange, constant-capacity assumptions require evidence before any real-building application.
- Exhaustive enumeration is limited to the current two-half action menu and does not establish general optimality.
