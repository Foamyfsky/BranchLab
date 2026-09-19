# BranchLab — Observe, Infer, Intervene

**Live dashboard: [branchlab-dashboard.streamlit.app](https://branchlab-dashboard.streamlit.app/)**

BranchLab asks: when only part of a network can be observed, can its hidden state be inferred well enough to choose useful interventions, and when does that approach fail? The current dashboard is the deterministic full-state reference for that broader research direction: operate one air cleaner in a synthetic three-room world, pause and fork an experiment, compare completed outcomes, and export or replay the exact timestamped intervention history.

One removable particle class moves through three connected, well-mixed rooms with fixed symmetric exchange and background removal. The cleaner has constant capacity, there is no continuing source, and every room-average concentration and model parameter is known. These are synthetic example parameters—not calibrated measurements or safety guidance.

**Read [the particle-world guide](docs/particle-world.md) for the authoritative model, units, assumptions, intervention protocol, evaluation definitions, results, interpretation, and verification map.**

## Explore the worked comparison

Install the dashboard, launch it from the repository root, and choose **Load worked example**:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[ui]"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The button loads a validated, replayed 5-hour experiment and opens **Compare** with **Stay in C** as the reference and **Move to A** as the alternative. Both strategies share the first 2.5 hours and use the same 500 m³ clean-air budget. Moving to A reduces cumulative room-mean concentration $J$ by 5.98%, from 5.3927154554 to 5.0700339391 µg·h/m³, while increasing cumulative concentration in Room C. Stay in C is the demonstration reference, not the best fixed placement.

![BranchLab interactive particle-control dashboard](docs/dashboard.png)

After exploring the example, use **New experiment setup** to choose an initial state and horizon, then operate, advance, fork, and compare your own branches. **Save or load a reproducible experiment** downloads or validates a versioned JSON replay record.

## Current capabilities

- deterministic three-room transport with symmetric exchange, background removal, and piecewise-constant filtration;
- exact matrix-exponential propagation and augmented-state concentration integrals;
- independent evaluation of 40 branches across two initial states, two horizons, and ten schedules;
- interactive on/off and location controls with exact simulation timestamps;
- independent named forks plus validated versioned JSON export/import;
- room-level and mean outcomes in CSV, a readable console table, and a four-panel figure; and
- a local Streamlit and Plotly dashboard with separate Experiment and Compare views, a vector room schematic, like-for-like histories, an event timeline, a rate explanation, and completed-branch comparisons.

These capabilities form a reproducible synthetic reference, not a safety model or a prediction for a real building. Current implementation status and limitations are tracked in [STATUS.md](STATUS.md).

## Run it from a fresh clone

BranchLab requires Python 3.11 or newer. The `ui` extra installs Streamlit and Plotly in addition to the core numerical and plotting dependencies. The commands below create an isolated environment, install the complete local dashboard, reproduce the fixed outputs, and run all tests.

### Windows PowerShell

```powershell
git clone https://github.com/Foamyfsky/BranchLab.git
Set-Location BranchLab
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[ui]"
.\.venv\Scripts\python.exe -m branchlab.experiment
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

If `py -3` is unavailable, use any installed Python 3.11-or-newer executable for the `-m venv .venv` step. The machine used for the current verification also provides this local-only fallback; it is not a portable project requirement:

```powershell
& 'C:\Users\22246\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m venv .venv
```

### macOS or Linux

```bash
git clone https://github.com/Foamyfsky/BranchLab.git
cd BranchLab
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -e ".[ui]"
./.venv/bin/python -m branchlab.experiment
./.venv/bin/python -m unittest discover -s tests -v
```

The experiment replaces `results/transport.csv` and `results/transport.png` on every run. The CSV retains both initial states and all 40 deterministic branch records; the figure presents the `(2, 2, 2.5)` µg/m³ case at both horizons.

Install only the core fixed experiment with `python -m pip install -e .` if the dashboard is not needed.

## Launch the interactive dashboard

From the repository root on Windows:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

On macOS or Linux, use `./.venv/bin/python -m streamlit run app.py`.

For the shortest walkthrough, choose **Load worked example**, inspect the shared history, fork marker, room-level tradeoff, and equal budgets in **Compare**, then open **New experiment setup** to start a separate experiment. The manual controls also support exact advancement, bounded play/pause, named forks, cleaner relocation/on-off changes, run-to-end, and validated JSON export/import.

Changing initial conditions or horizon does not silently mutate an experiment; press **Create new experiment** explicitly. Playback cadence changes only wall-clock refresh timing, not the timestamped physical solution.

For Streamlit Community Cloud, create an app from `Foamyfsky/BranchLab`, branch `main`, with `app.py` as the entrypoint. Choose Python 3.12 in **Advanced settings**. The root `requirements.txt` installs this local project with its `ui` extra, so dependency versions remain declared in `pyproject.toml`.

## Representative result

For the `(2, 2, 2.5)` µg/m³ initial state, fixed placement is horizon dependent. At 1 hour, C→C is the best of the three fixed placements, while C→A is best among the nine tested two-half schedules. At 5 hours, B→B is the best fixed placement, while C→A remains best among the nine tested schedules.

| Horizon | No-cleaner J | Best fixed | Best of nine tested |
| --- | ---: | --- | --- |
| 1 h | 2.06185594 | C→C: 1.77332755 | C→A: 1.75913460 |
| 5 h | 8.52516904 | B→B: 5.21845964 | C→A: 5.07003394 |

`J` is integrated mean concentration in µg·h/m³; lower is better. See the [world guide's evaluation and interpretation](docs/particle-world.md#evaluation) for denominators, room-level results, equal-budget reasoning, relocation comparisons, and limits.

![Concentration histories and schedule comparisons for the three-room particle world](results/transport.png)
