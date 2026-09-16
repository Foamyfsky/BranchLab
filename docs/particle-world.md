# Particle world: model, intervention, and evaluation

This guide is the authoritative description of BranchLab's current three-room particle-transport experiment. For installation and run commands, start with the [README](../README.md#run-it-from-a-fresh-clone).

## Purpose and scene

The particle world is a small, transparent environment for studying how transport through a network interacts with the location and timing of an intervention. Three rooms form the path A–B–C. A removable particle class begins at a known concentration in each room, exchanges between neighboring rooms, and is removed by background processes and one movable air cleaner.

The broader BranchLab research question is whether partial observations can support useful hidden-state inference and intervention decisions, and when those methods fail. That observation–inference–intervention loop is a future capability. The implementation described here is instead a deterministic, fully observed reference: every initial concentration and parameter is known, and every predetermined action branch is propagated exactly under the model. It provides ground-truth trajectories against which later observation, inference, or learned-dynamics methods can be compared.

## Model

For room \(i\), the mass balance is

\[
V_i \frac{dc_i}{dt}
= \sum_j q_{ij}(c_j-c_i) - (k_iV_i+u_i(t))c_i.
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(t\) | elapsed time | h |
| \(c_i(t)\) | particle concentration in room \(i\) | µg/m³ |
| \(V_i\) | room volume | m³ |
| \(q_{ij}\) | symmetric exchange flow between rooms \(i\) and \(j\) | m³/h |
| \(k_i\) | first-order background removal rate | 1/h |
| \(u_i(t)\) | cleaner's equivalent clean-air delivery in room \(i\) | m³/h |

The current synthetic parameters are:

| Quantity | Value |
| --- | --- |
| Topology | A–B–C; no direct A–C exchange |
| Volumes | \(V=(100,100,100)\) m³ |
| Neighbor exchange | \(q_{AB}=q_{BA}=q_{BC}=q_{CB}=50\) m³/h |
| Other exchange | 0 m³/h |
| Background removal | \(k=(0.1,0.1,0.1)\) 1/h |
| Cleaner capacity | 100 m³/h in exactly one room while active |
| Initial states | \((2,2,2.5)\) and \((2.5,2,2)\) µg/m³ |
| Horizons | 1 h and 5 h |
| Continuing source | none after the initial state |

### Transfer, removal, and exponential evolution

The exchange term transfers particle mass rather than creating or destroying it. For a connected pair with symmetric flow, the contribution \(q_{ij}(c_j-c_i)\) to room \(i\) is cancelled by \(q_{ji}(c_i-c_j)\) in room \(j\) when the room mass balances are summed. With exchange alone, total particle mass \(\sum_i V_ic_i\) is therefore conserved.

Background removal and filtration are sinks. Their combined removal from room \(i\) is \((k_iV_i+u_i)c_i\), so with no continuing source,

\[
\frac{d}{dt}\sum_i V_ic_i
=-\sum_i(k_iV_i+u_i)c_i.
\]

Within each half-horizon, all rates and the cleaner location are fixed. The coupled equations can therefore be written \(\dot{\mathbf c}=A\mathbf c\), whose solution is \(\mathbf c(t+\Delta)=\exp(A\Delta)\mathbf c(t)\). The histories are combinations of exponential modes. `scipy.linalg.expm` is used directly for each constant-control segment.

### Assumptions and provenance

- Each room is internally well mixed, so it has one concentration value.
- Exchange is fixed and symmetric.
- Background removal and cleaner performance are constant.
- The cleaner has no ramp-up and relocation at the halfway point takes negligible time.
- Only one removable particle class is represented.
- There is no continuing emission after the supplied initial state.

The equal volumes and symmetric path deliberately isolate position, timing, and horizon effects. All values are synthetic examples supplied for this experiment, not field measurements, fitted parameters, or a calibrated building. The model makes no exposure-safety claim. The [NIST discussion of CONTAM 3.0](https://www.nist.gov/publications/using-cfd-capabilities-contam-30-simulating-airflow-and-contaminant-transport-and) provides scientific context for multizone contaminant transport and for using more detailed CFD treatment when a well-mixed zone is inadequate.

## Intervention strategy

Each branch begins independently from the same initial concentration vector. One cleaner operates at 100 m³/h in a selected room during the first half of the horizon and in a selected room during the second half. The two room choices are drawn from A, B, and C, producing nine active schedules:

| First half | Second-half choices |
| --- | --- |
| A | A, B, C |
| B | A, B, C |
| C | A, B, C |

A separate no-cleaner branch supplies the reference. Two initial states × two horizons × ten branches produce the 40 records in `results/transport.csv`.

Schedules are predetermined and evaluated by exhaustive enumeration. There is no sensor feedback, feedback controller, adaptive replanning, optimizer over switching times, or learned policy. “Best fixed” means the lowest loss among A→A, B→B, and C→C. “Best of nine” means the lowest loss among all nine two-half schedules. These are different candidate sets, and neither phrase establishes optimality over arbitrary relocation times or other control strategies.

## Evaluation

Each room retains its own integrated concentration,

\[
I_i=\int_0^T c_i(t)\,dt,
\]

in µg·h/m³. The primary loss is the integrated mean concentration,

\[
J=\int_0^T\frac{c_A(t)+c_B(t)+c_C(t)}{3}\,dt
=\frac{I_A+I_B+I_C}{3}.
\]

Lower values mean less modeled cumulative concentration. Keeping \(I_A\), \(I_B\), and \(I_C\) prevents the mean from hiding which room receives the modeled benefit or burden.

For a metric \(X\), either one room's \(I_i\) or the mean loss \(J\), improvement relative to the matching no-cleaner branch is

\[
\Delta X=X_{\mathrm{none}}-X_{\mathrm{schedule}},
\qquad
\Delta X_{\%}=100\frac{X_{\mathrm{none}}-X_{\mathrm{schedule}}}
{X_{\mathrm{none}}}.
\]

The denominator is always the no-cleaner value for the same initial state and horizon. A schedule's improvement versus no cleaner is not the same quantity as its advantage over the best fixed placement. The latter is reported below as \(J_{\mathrm{best\ fixed}}-J_{\mathrm{best\ of\ nine}}\).

Every active schedule within a horizon has the same clean-air budget,

\[
B=\int_0^T\sum_i u_i(t)\,dt=100T,
\]

which is 100 m³ at 1 h and 500 m³ at 5 h. The no-cleaner budget is zero. Different horizons have different budgets and integration intervals, so 1-hour and 5-hour losses are separate comparisons, not entries in one ranking.

The cumulative states \(I_i\) are propagated in an augmented linear system. Scores are consequently independent of the 201 plotting samples used to draw a history.

## Results and interpretation

The table below is derived from the current `results/transport.csv`. Percentages in the fixed and tested-schedule columns are improvements versus the matching no-cleaner branch.

| Initial state (µg/m³) | Horizon | No-cleaner \(J\) | Best fixed | Best of nine tested | Tested relocation advantage over best fixed |
| --- | ---: | ---: | --- | --- | ---: |
| (2, 2, 2.5) | 1 h | 2.06185594 | C→C: 1.77332755 (13.99%) | C→A: 1.75913460 (14.68%) | 0.01419295 |
| (2, 2, 2.5) | 5 h | 8.52516904 | B→B: 5.21845964 (38.79%) | C→A: 5.07003394 (40.53%) | 0.14842570 |
| (2.5, 2, 2) | 1 h | 2.06185594 | A→A: 1.77332755 (13.99%) | A→C: 1.75913460 (14.68%) | 0.01419295 |
| (2.5, 2, 2) | 5 h | 8.52516904 | B→B: 5.21845964 (38.79%) | A→C: 5.07003394 (40.53%) | 0.14842570 |

All \(J\) values and absolute differences are in µg·h/m³.

For a 1-hour fixed placement, the initially higher end room is best. Over 5 hours, fixed placement in central room B is best among the three fixed choices because B directly exchanges with both ends. In the tested two-stage menu, the best schedule cleans the initially higher end first and then the opposite end. This relocation reduces \(J\) by 0.01419295 µg·h/m³ beyond the best fixed placement at 1 hour and by 0.14842570 µg·h/m³ at 5 hours. Those are tested-menu comparisons, not general control optima.

After the cleaner moves from the initially higher room, that room's concentration can rebound: exchange can temporarily carry particles back into it faster than background removal takes them out. This rebound is redistribution within the closed source-free model, not a new emission. The figure makes the effect most visible after the C→A switch in the 5-hour case.

Swapping rooms A and C and mirroring the initial state gives mirrored trajectories, room integrals, and schedules with unchanged \(J\). The mirrored cases are a structural symmetry check. The 40 rows are deterministic evaluations of action branches, not independent statistical trials; they do not quantify sampling variability or uncertainty.

These examples establish, within the stated model, that transport makes the best fixed location horizon dependent and that one tested relocation can improve on the best tested fixed placement. They do not test noisy or missing observations, uncertain parameters, alternative switching times, real occupancy or emissions, multiple cleaners, nonlinear filters, time-varying airflow, learned dynamics, or safety thresholds.

## Verification and code navigation

The focused unit tests check:

- total-mass conservation under exchange alone;
- agreement with analytic exponential decay for one isolated room;
- nonnegative concentration histories within numerical tolerance;
- equal clean-air budgets for all active schedules in a horizon;
- independence and non-mutation of branch inputs;
- A/C mirror symmetry; and
- the supplied independent fixed-placement loss values to within \(10^{-5}\).

| Path | Responsibility |
| --- | --- |
| `src/branchlab/transport.py` | input validation, system matrix, matrix-exponential propagation, augmented concentration integrals, exact sampled histories, and budgets |
| `src/branchlab/experiment.py` | synthetic parameters, schedule enumeration, evaluation, console reporting, CSV writing, and plotting |
| `tests/test_transport.py` | physical invariants, numerical checks, branch independence, symmetry, and reference losses |
| `results/transport.csv` | all 40 deterministic branch records with room-level and mean outcomes |
| `results/transport.png` | four-panel presentation of histories and tested schedules for the `(2, 2, 2.5)` initial state |

Use the [README run instructions](../README.md#run-it-from-a-fresh-clone) to reproduce both result files. In future work, this exact full-state reference can supply ground-truth trajectories for controlled comparisons with partial observation, hidden-state inference, intervention selection, and learned transport models. None of those later layers is implemented yet.
