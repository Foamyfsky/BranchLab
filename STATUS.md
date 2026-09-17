# Status

BranchLab currently provides a deterministic, fully observed reference for the three-room particle world. The authoritative experiment description is [docs/particle-world.md](docs/particle-world.md); setup and run commands are in [README.md](README.md).

## Implemented capabilities

- A linear well-mixed A–B–C transport model with symmetric exchange, background removal, and one piecewise-constant cleaner intervention.
- Exact matrix-exponential state propagation and augmented-state integration of per-room concentrations.
- Exhaustive evaluation of a no-cleaner reference and nine predetermined two-half schedules for two mirrored initial states and 1-hour and 5-hour horizons.
- A reproducible 40-record CSV with room-level and mean outcomes, plus a four-panel figure for the `(2, 2, 2.5)` initial state.
- Separate identification of the best fixed placement and the best of the nine tested schedules.
- A local Streamlit and Plotly dashboard with separate Experiment and Compare views, a directly rendered vector room schematic, fixed-scenario creation, timestamped cleaner location/on-off controls, bounded playback, pause, exact advancement, and run-to-end operation.
- Independent named forks that preserve the current concentration, room integrals, actual clean-air budget, current control, and copied action history.
- Partial and completed metrics, matching no-cleaner room overlays, branch histories and event markers, rate-contribution explanations, like-for-like completed-branch histories, and separate outcome and resource-use comparisons.
- Explicit export and validated import of a versioned JSON experiment, including model metadata, units, branch lineage, ordered actions, and deterministic replay checks.
- A one-click, replay-validated worked comparison with named Stay in C and Move to A branches, preserved 2.5-hour lineage, equal-budget and room-level tradeoff reporting, and automatic Compare selection.
- Streamlit Community Cloud-ready root packaging for `app.py`, with Python 3.12 as the documented deployment selection.

Supplied initial conditions and synthetic parameters, cleaner interventions, deterministic state trajectories, and calculated outcomes remain distinct. The code contains no observation process or inferred state.

## Verification

The verification workflow covers exchange-only mass conservation, isolated-room analytic exponential decay, concentration nonnegativity within numerical tolerance, equal fixed-protocol budgets, independent branch inputs, A/C mirror symmetry, and supplied fixed-placement reference losses. Interactive-session checks cover fork continuity and independence, incremental versus direct propagation, exact action timing, pause behavior, horizon stopping, actual on/off budget accounting, zero inputs, deterministic same-time controls, branch-lineage validation, and JSON replay equivalence.

The current verification installed the root `requirements.txt` into a clean Python 3.12 environment, reproduced the fixed experiment, passed all 15 model/session/UI tests and `pip check`, and retained the 40-row CSV byte-for-byte (SHA-256 `858c739f8a2aa5fd8e2686743f2914af631d927c10714b7532e327941b70be4a`). A real 1440×900 browser walkthrough loaded the reusable example in one click, confirmed the paused 2.5-hour lineage and selected Stay in C/Move to A comparison, created a separate new experiment afterward, exported JSON, uploaded the stored example, and verified deterministic replay. It confirmed $J=5.3927154554$ with $I=(6.9573536052,5.9383787319,3.2824140291)$ for Stay in C and $J=5.0700339391$ with $I=(5.5962274750,5.7210923174,3.8927820251)$ for Move to A; each consumed 500 m³, and moving increased $I_C$ by 0.61036800 µg·h/m³. The vector schematic visibly showed separate arrows in both directions for A–B and B–C, and a second browser tab started with an independent experiment at $t=0$. Controls, units, labels, legends, fork/action markers, comparison table, rate explanation, and the refreshed README screenshot were inspected in the rendered dashboard.

## Unresolved and out of scope

- Parameters are synthetic and have no measured-data provenance or calibration.
- No partial-observation model, hidden-state inference, uncertainty propagation, learned dynamics, adaptive controller, or learned policy is implemented.
- Interactive state is local and in-memory until the user explicitly downloads JSON; there is no database, authentication, multi-user synchronization, or background service.
- Community Cloud deployment is prepared for `Foamyfsky/BranchLab`, `main`, and `app.py` on Python 3.12, but a live app has not been created because no authenticated Streamlit Community Cloud session was available during verification.
- Continuing sources, multiple particle classes or cleaners, arbitrary switching times, time-varying exchange, nonlinear filter behavior, occupancy, and safety thresholds are untested.
- The well-mixed, fixed-exchange, constant-capacity assumptions require evidence before any real-building application.
- Exhaustive enumeration is limited to the current two-half action menu and does not establish general optimality.
