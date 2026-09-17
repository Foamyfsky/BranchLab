"""Streamlit dashboard for the deterministic three-room particle world."""

from __future__ import annotations

import html
import time

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from branchlab.experiment import HORIZONS, INITIAL_STATES, ROOMS
from branchlab.session import ExperimentSession


ROOM_COLORS = {"A": "#28d7e5", "B": "#e0a12b", "C": "#df5f52"}
BRANCH_COLORS = ("#b7a176", "#78a6a9", "#d9995b", "#a783c1", "#79a86b")
PLAYBACK_STEP_H = 0.05
PLAYBACK_DELAYS = {"Slow": 0.8, "Normal": 0.35, "Fast": 0.12}


st.set_page_config(
    page_title="BranchLab Particle Console",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --charcoal: #0d1114;
        --panel: #171d21;
        --panel-deep: #11171a;
        --copper: #b66c35;
        --brass: #d1a64b;
        --cyan: #28d7e5;
        --amber: #ffbd4a;
        --cream: #f1e3bf;
        --muted: #9fa8a6;
    }
    .stApp {
        background:
            linear-gradient(rgba(40, 215, 229, 0.025) 1px, transparent 1px),
            linear-gradient(90deg, rgba(40, 215, 229, 0.025) 1px, transparent 1px),
            radial-gradient(circle at 80% 0%, #20272a 0%, var(--charcoal) 42%);
        background-size: 24px 24px, 24px 24px, auto;
    }
    [data-testid="stSidebar"] {
        border-right: 2px solid #7b4b2a;
        background: linear-gradient(180deg, #171d21 0%, #101518 100%);
    }
    h1, h2, h3 { letter-spacing: 0.04em; }
    h1 { color: var(--cream); text-shadow: 0 0 18px rgba(40, 215, 229, 0.18); }
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #1b2226, #11171a);
        border: 1px solid #6e4729;
        border-left: 4px solid var(--copper);
        padding: 0.7rem 0.8rem;
        box-shadow: inset 0 0 18px rgba(0,0,0,0.25);
    }
    [data-testid="stMetricValue"] { color: var(--cyan); }
    .lab-panel {
        border: 1px solid #745033;
        border-top: 3px solid var(--brass);
        background: linear-gradient(145deg, rgba(28,35,39,.96), rgba(14,19,22,.96));
        padding: 0.8rem 1rem;
        margin: 0.4rem 0 1rem 0;
        box-shadow: 0 8px 24px rgba(0,0,0,.28), inset 0 0 0 1px rgba(255,189,74,.06);
    }
    .lab-kicker {
        color: var(--amber);
        font-size: .78rem;
        text-transform: uppercase;
        letter-spacing: .16em;
    }
    .status-chip {
        display: inline-block;
        padding: .15rem .55rem;
        margin-right: .35rem;
        border: 1px solid var(--cyan);
        color: var(--cyan);
        background: rgba(40,215,229,.08);
        font-size: .78rem;
    }
    .status-chip.amber { border-color: var(--amber); color: var(--amber); background: rgba(255,189,74,.08); }
    .synthetic-note {
        border-left: 4px solid var(--amber);
        background: rgba(255,189,74,.07);
        padding: .65rem .85rem;
        color: #e8d9b6;
        margin-bottom: 1rem;
    }
    div.stButton > button, div.stDownloadButton > button {
        border-radius: 0;
        border: 1px solid #a96636;
        box-shadow: inset 0 0 0 1px rgba(255,189,74,.08);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def current_experiment() -> ExperimentSession:
    if "experiment" not in st.session_state:
        st.session_state.experiment = ExperimentSession(
            INITIAL_STATES[0], 5.0, cleaner_location="C", cleaner_on=True
        )
    return st.session_state.experiment


def reset_experiment(experiment: ExperimentSession, message: str) -> None:
    st.session_state.experiment = experiment
    st.session_state.flash_message = message
    st.session_state.sync_setup_controls = True
    st.session_state.pop("branch_selector", None)
    st.rerun()


def sync_setup_controls(experiment: ExperimentSession, *, force: bool = False) -> None:
    """Initialize the prospective scenario controls from the experiment root."""

    initial = experiment.initial_concentration
    if np.allclose(initial, INITIAL_STATES[0], rtol=0.0, atol=0.0):
        preset = "Preset: (2, 2, 2.5)"
    elif np.allclose(initial, INITIAL_STATES[1], rtol=0.0, atol=0.0):
        preset = "Preset: (2.5, 2, 2)"
    else:
        preset = "Custom"
    root = next(branch for branch in experiment.branches.values() if branch.parent_id is None)
    root_control = root.actions[0]
    values: dict[str, object] = {
        "setup_preset": preset,
        "setup_horizon": experiment.horizon_h,
        "setup_location": root_control.location,
        "setup_on": root_control.cleaner_on,
        **{
            f"custom_initial_{room}": float(initial[index])
            for index, room in enumerate(ROOMS)
        },
    }
    for key, value in values.items():
        if force or key not in st.session_state:
            st.session_state[key] = value


def format_percent(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.2f}%"


def plot_layout(title: str, height: int = 470) -> dict[str, object]:
    return {
        "title": {"text": title, "x": 0.02, "xanchor": "left"},
        "height": height,
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "#11171a",
        "font": {"family": "Consolas, monospace", "color": "#f1e3bf"},
        "margin": {"l": 55, "r": 30, "t": 60, "b": 55},
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1.0,
        },
        "hovermode": "x unified",
    }


def schematic_svg(experiment: ExperimentSession) -> str:
    branch = experiment.active_branch
    room_x = {"A": 40, "B": 310, "C": 580}
    room_blocks: list[str] = []
    for index, room in enumerate(ROOMS):
        x = room_x[room]
        concentration = branch.concentration[index]
        active = room == branch.cleaner_location
        border = "#28d7e5" if active and branch.cleaner_on else "#9b693f"
        room_blocks.append(
            f"""
            <g>
              <rect x="{x}" y="42" width="210" height="142" rx="4"
                    fill="#131a1e" stroke="{border}" stroke-width="3" />
              <path d="M{x+12} 58 h34 M{x+12} 58 v20 M{x+198} 58 h-34 M{x+198} 58 v20"
                    stroke="#d1a64b" stroke-width="2" fill="none" />
              <text x="{x+18}" y="88" fill="#f1e3bf" font-size="23" font-family="monospace">ROOM {room}</text>
              <text x="{x+105}" y="132" text-anchor="middle" fill="{ROOM_COLORS[room]}"
                    font-size="29" font-family="monospace">{concentration:.4f}</text>
              <text x="{x+105}" y="157" text-anchor="middle" fill="#9fa8a6"
                    font-size="14" font-family="monospace">µg/m³ room average</text>
            </g>
            """
        )

    cleaner_x = room_x[branch.cleaner_location] + 165
    cleaner_color = "#28d7e5" if branch.cleaner_on else "#b66c35"
    cleaner_label = "ON" if branch.cleaner_on else "OFF"
    branch_name = html.escape(branch.name)
    return f"""
    <div class="lab-panel">
      <div class="lab-kicker">Live room-average state · branch {branch_name}</div>
      <svg viewBox="0 0 830 230" width="100%" role="img"
           aria-label="Three connected well-mixed rooms with one movable air cleaner">
        <defs>
          <filter id="glow"><feGaussianBlur stdDeviation="2.4" result="blur"/></filter>
        </defs>
        <path d="M250 112 H310 M520 112 H580" stroke="#b66c35" stroke-width="6" />
        <path d="M265 100 l14 12 -14 12 M295 100 l-14 12 14 12
                 M535 100 l14 12 -14 12 M565 100 l-14 12 14 12"
              stroke="#ffbd4a" stroke-width="2" fill="none" />
        <text x="280" y="90" text-anchor="middle" fill="#9fa8a6" font-size="12" font-family="monospace">50 m³/h</text>
        <text x="550" y="90" text-anchor="middle" fill="#9fa8a6" font-size="12" font-family="monospace">50 m³/h</text>
        {''.join(room_blocks)}
        <g>
          <rect x="{cleaner_x}" y="50" width="34" height="34" fill="#0d1114"
                stroke="{cleaner_color}" stroke-width="3" />
          <path d="M{cleaner_x+17} 57 v20 M{cleaner_x+7} 67 h20"
                stroke="{cleaner_color}" stroke-width="3" />
          <text x="{cleaner_x+17}" y="103" text-anchor="middle" fill="{cleaner_color}"
                font-size="12" font-family="monospace">{cleaner_label}</text>
        </g>
        <text x="415" y="215" text-anchor="middle" fill="#9fa8a6" font-size="13" font-family="monospace">
          Cleaner position is instantaneous · visualization is not a particle trajectory
        </text>
      </svg>
    </div>
    """


def history_figure(experiment: ExperimentSession) -> go.Figure:
    branch = experiment.active_branch
    times, histories = experiment.history(branch.branch_id)
    figure = go.Figure()
    for index, room in enumerate(ROOMS):
        figure.add_trace(
            go.Scatter(
                x=times,
                y=histories[:, index],
                mode="lines",
                name=f"{branch.name} · Room {room}",
                line={"color": ROOM_COLORS[room], "width": 3},
            )
        )

    reference_times, reference_history = experiment.no_cleaner_history(branch.time_h)
    figure.add_trace(
        go.Scatter(
            x=reference_times,
            y=np.mean(reference_history, axis=1),
            mode="lines",
            name="No cleaner · room mean",
            line={"color": "#d0d0c8", "width": 2, "dash": "dash"},
        )
    )

    for other_index, (branch_id, other) in enumerate(experiment.branches.items()):
        if branch_id == branch.branch_id or other.time_h <= 0.0:
            continue
        other_times, other_history = experiment.history(branch_id)
        figure.add_trace(
            go.Scatter(
                x=other_times,
                y=np.mean(other_history, axis=1),
                mode="lines",
                name=f"{other.name} · room mean",
                line={
                    "color": BRANCH_COLORS[other_index % len(BRANCH_COLORS)],
                    "width": 1.8,
                    "dash": "dot",
                },
            )
        )

    actions_by_time: dict[float, list[str]] = {}
    for action in branch.actions[1:]:
        state = f"{action.location} {'ON' if action.cleaner_on else 'OFF'}"
        actions_by_time.setdefault(action.time_h, []).append(state)
    for action_time, labels in actions_by_time.items():
        figure.add_vline(
            x=action_time,
            line_width=1.5,
            line_dash="dot",
            line_color="#ffbd4a",
        )
        figure.add_annotation(
            x=action_time,
            y=1.0,
            yref="paper",
            text=" → ".join(labels),
            showarrow=False,
            textangle=-90,
            xanchor="left",
            yanchor="top",
            font={"color": "#ffbd4a", "size": 10},
        )
    figure.add_vline(
        x=branch.time_h,
        line_width=1,
        line_dash="dash",
        line_color="#28d7e5",
    )
    figure.update_layout(
        **plot_layout("Concentration histories and intervention events"),
        xaxis={"title": "Simulation time (h)", "range": [0.0, experiment.horizon_h]},
        yaxis={"title": "Room-average concentration (µg/m³)", "rangemode": "tozero"},
    )
    return figure


def completed_comparison_figure(experiment: ExperimentSession) -> go.Figure:
    summaries = experiment.completed_summaries()
    names = [str(summary["name"]) for summary in summaries]
    losses = [float(summary["J"]) for summary in summaries]
    budgets = [float(summary["clean_air_volume_m3"]) for summary in summaries]
    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=names,
            y=losses,
            name="J",
            marker_color="#28d7e5",
            text=[f"{value:.6f}" for value in losses],
            textposition="outside",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=names,
            y=budgets,
            name="Clean-air volume",
            mode="lines+markers",
            marker={"color": "#ffbd4a", "size": 10},
            line={"color": "#ffbd4a", "width": 2},
            yaxis="y2",
        )
    )
    layout = plot_layout("Completed branches in this fixed scenario", height=390)
    layout.update(
        {
            "yaxis": {"title": "J (µg·h/m³)", "rangemode": "tozero"},
            "yaxis2": {
                "title": "Clean-air volume (m³; not energy)",
                "overlaying": "y",
                "side": "right",
                "rangemode": "tozero",
            },
            "barmode": "group",
        }
    )
    figure.update_layout(**layout)
    return figure


experiment = current_experiment()
sync_setup_controls(
    experiment,
    force=bool(st.session_state.pop("sync_setup_controls", False)),
)

st.sidebar.markdown("## Experiment setup")
st.sidebar.caption(
    "Scenario settings are fixed after creation. Editing these controls does nothing until Create new experiment is pressed."
)
preset_options = (
    "Preset: (2, 2, 2.5)",
    "Preset: (2.5, 2, 2)",
    "Custom",
)
preset = st.sidebar.selectbox(
    "Initial concentration preset", preset_options, key="setup_preset"
)
if preset == preset_options[0]:
    requested_initial = [2.0, 2.0, 2.5]
elif preset == preset_options[1]:
    requested_initial = [2.5, 2.0, 2.0]
else:
    requested_initial = [
        st.sidebar.number_input(
            f"Initial Room {room} (µg/m³)",
            min_value=0.0,
            format="%.6f",
            key=f"custom_initial_{room}",
        )
        for room in ROOMS
    ]
requested_horizon = st.sidebar.selectbox(
    "Horizon (h)", HORIZONS, key="setup_horizon"
)
requested_location = st.sidebar.selectbox(
    "Initial cleaner location", ROOMS, key="setup_location"
)
requested_on = st.sidebar.toggle(
    "Cleaner initially on", key="setup_on"
)
if st.sidebar.button("Create new experiment", width="stretch"):
    reset_experiment(
        ExperimentSession(
            requested_initial,
            requested_horizon,
            cleaner_location=requested_location,
            cleaner_on=requested_on,
        ),
        "Created a new fixed scenario. Previous in-memory branches were replaced.",
    )

st.sidebar.divider()
st.sidebar.markdown("## Branch console")
branch_ids = list(experiment.branches)
selected_branch_id = st.sidebar.selectbox(
    "Active branch",
    branch_ids,
    index=branch_ids.index(experiment.active_branch_id),
    format_func=lambda branch_id: (
        f"{experiment.branches[branch_id].name} · {branch_id}"
    ),
    key="branch_selector",
)
if selected_branch_id != experiment.active_branch_id:
    experiment.switch_branch(selected_branch_id)
    st.rerun()

branch = experiment.active_branch
control_key = f"control-{branch.branch_id}-{len(branch.actions)}-{branch.time_h:.9f}"
control_location = st.sidebar.selectbox(
    "Cleaner location",
    ROOMS,
    index=ROOMS.index(branch.cleaner_location),
    key=f"location-{control_key}",
    disabled=branch.is_complete(experiment.horizon_h),
)
control_on = st.sidebar.toggle(
    "Cleaner on",
    value=branch.cleaner_on,
    key=f"on-{control_key}",
    disabled=branch.is_complete(experiment.horizon_h),
)
st.sidebar.caption(
    f"A submitted control takes effect at simulation time {branch.time_h:.6f} h and affects only subsequent evolution."
)
if st.sidebar.button(
    "Apply timestamped control",
    width="stretch",
    disabled=branch.is_complete(experiment.horizon_h),
):
    experiment.set_control(location=control_location, cleaner_on=control_on)
    st.session_state.flash_message = (
        f"Control recorded at t={branch.time_h:.6f} h: {control_location} "
        f"{'ON' if control_on else 'OFF'}."
    )
    st.rerun()

fork_name = st.sidebar.text_input("New fork name", value="alternate")
if st.sidebar.button(
    "Fork paused state",
    width="stretch",
    disabled=experiment.playing or branch.is_complete(experiment.horizon_h),
):
    try:
        new_branch_id = experiment.fork(fork_name)
    except ValueError as error:
        st.sidebar.error(str(error))
    else:
        st.session_state.flash_message = (
            f"Created {fork_name} ({new_branch_id}) at t={branch.time_h:.6f} h."
        )
        st.rerun()

st.sidebar.divider()
st.sidebar.markdown("## Save and replay")
st.sidebar.download_button(
    "Download verified experiment JSON",
    data=experiment.to_json(),
    file_name="branchlab-particle-experiment.json",
    mime="application/json",
    width="stretch",
)
uploaded_json = st.sidebar.file_uploader("Experiment JSON", type=("json",))
if st.sidebar.button(
    "Import and replay JSON",
    width="stretch",
    disabled=uploaded_json is None,
):
    try:
        imported = ExperimentSession.from_json(uploaded_json.getvalue())
    except ValueError as error:
        st.sidebar.error(f"Import rejected: {error}")
    else:
        reset_experiment(
            imported,
            "Imported experiment was replayed and its accumulated state matched the solver.",
        )

st.title("BRANCHLAB // PARTICLE CONTROL CONSOLE")
st.markdown(
    """
    <div class="synthetic-note">
      <strong>Synthetic, source-free, fully observed reference.</strong>
      Each room is well mixed. The display shows room-average concentration, not resolved particles or a real-building safety prediction.
    </div>
    """,
    unsafe_allow_html=True,
)

if "flash_message" in st.session_state:
    st.success(st.session_state.pop("flash_message"))

status = "COMPLETED" if branch.is_complete(experiment.horizon_h) else "PARTIAL"
playback_state = "PLAYING" if experiment.playing else "PAUSED"
st.markdown(
    f"""
    <div class="lab-panel">
      <span class="status-chip">{status}</span>
      <span class="status-chip amber">{playback_state}</span>
      <span class="lab-kicker">branch {html.escape(branch.name)} · parent {html.escape(branch.parent_id or 'none')} · fork t={branch.fork_time_h:.3f} h</span>
    </div>
    """,
    unsafe_allow_html=True,
)

time_col, status_col, control_col, action_col = st.columns(4)
time_col.metric("Simulation time", f"{branch.time_h:.6f} h", f"of {experiment.horizon_h:g} h")
status_col.metric("Result status", status, playback_state)
control_col.metric(
    "Current control",
    f"{branch.cleaner_location} · {'ON' if branch.cleaner_on else 'OFF'}",
    f"effective since {branch.actions[-1].time_h:.6f} h",
)
action_col.metric("Recorded controls", str(len(branch.actions)), "ordered events")

play_col, pause_col, target_col, advance_col, end_col = st.columns((1, 1, 2.2, 1.3, 1.3))
if play_col.button(
    "Play",
    width="stretch",
    disabled=experiment.playing or branch.is_complete(experiment.horizon_h),
):
    experiment.play()
    st.rerun()
if pause_col.button(
    "Pause", width="stretch", disabled=not experiment.playing
):
    experiment.pause()
    st.rerun()
target_time = target_col.number_input(
    "Exact target time (h)",
    min_value=float(branch.time_h),
    max_value=float(experiment.horizon_h),
    value=float(branch.time_h),
    step=0.05,
    format="%.6f",
    disabled=experiment.playing or branch.is_complete(experiment.horizon_h),
    key=f"target-{branch.branch_id}-{branch.time_h:.9f}",
)
if advance_col.button(
    "Advance to time",
    width="stretch",
    disabled=experiment.playing or branch.is_complete(experiment.horizon_h),
):
    experiment.advance_to(target_time)
    st.rerun()
if end_col.button(
    "Run to end",
    width="stretch",
    disabled=experiment.playing or branch.is_complete(experiment.horizon_h),
):
    experiment.run_to_end()
    st.rerun()

speed = st.select_slider(
    "Playback cadence",
    options=list(PLAYBACK_DELAYS),
    value="Normal",
    help=(
        "Cadence changes wall-clock refresh delay only. Every update advances at most "
        f"{PLAYBACK_STEP_H:g} physical hours with exact propagation."
    ),
)

st.markdown(schematic_svg(experiment), unsafe_allow_html=True)

reference = experiment.no_cleaner_reference(branch.time_h)
current_j = float(np.mean(branch.integrals))
reference_j = float(reference["J"])
improvement = reference_j - current_j
improvement_percent = experiment.percentage_improvement(current_j, reference_j)

st.markdown("## Accumulated outcome")
metric_columns = st.columns(6)
for index, room in enumerate(ROOMS):
    metric_columns[index].metric(
        f"I_{room}", f"{branch.integrals[index]:.6f} µg·h/m³"
    )
metric_columns[3].metric(
    "J · mean cumulative",
    f"{current_j:.6f} µg·h/m³",
    f"{improvement:+.6f} vs no cleaner",
)
metric_columns[4].metric(
    "Improvement", format_percent(improvement_percent), "matching elapsed time"
)
metric_columns[5].metric(
    "Clean-air volume", f"{branch.clean_air_volume_m3:.3f} m³", "not energy use"
)
st.caption(
    f"Matching no-cleaner reference at t={branch.time_h:.6f} h: "
    f"J={reference_j:.6f} µg·h/m³. Partial values integrate only the elapsed interval."
)

concentration_title = "Final concentrations" if status == "COMPLETED" else "Current concentrations (final values pending)"
st.markdown(f"### {concentration_title}")
concentration_columns = st.columns(3)
for index, room in enumerate(ROOMS):
    concentration_columns[index].metric(
        f"Room {room}", f"{branch.concentration[index]:.6f} µg/m³"
    )

st.plotly_chart(history_figure(experiment), width="stretch")

st.markdown("## Why is a room rising or falling?")
selected_room = st.radio("Inspect room", ROOMS, horizontal=True)
contributions = experiment.rate_contributions(selected_room)
rate_columns = st.columns(4)
labels = (
    ("Net exchange", "net_exchange"),
    ("Background removal", "background_removal"),
    ("Cleaner removal", "cleaner_removal"),
    ("Total dc/dt", "total"),
)
for column, (label, key) in zip(rate_columns, labels):
    column.metric(label, f"{contributions[key]:+.6f} µg/m³/h")
total_rate = contributions["total"]
if total_rate > 1e-10:
    trend = "rising"
elif total_rate < -1e-10:
    trend = "falling"
else:
    trend = "approximately steady"
exchange_phrase = (
    "adds concentration to the room"
    if contributions["net_exchange"] > 1e-10
    else "removes concentration from the room"
    if contributions["net_exchange"] < -1e-10
    else "is balanced"
)
cleaner_phrase = (
    "The cleaner contributes removal here."
    if contributions["cleaner_removal"] < -1e-10
    else "The cleaner is not removing particles from this room."
)
st.markdown(
    f"Room **{selected_room}** is **{trend}** at the current computed state. "
    f"Net exchange {exchange_phrase}; background removal is always a sink. "
    f"{cleaner_phrase} The four rates sum to the displayed total."
)

st.markdown("## Branches and action timeline")
branch_rows = []
for candidate in experiment.branches.values():
    branch_rows.append(
        {
            "Branch": candidate.name,
            "ID": candidate.branch_id,
            "Parent": candidate.parent_id or "—",
            "Fork time (h)": candidate.fork_time_h,
            "Current time (h)": candidate.time_h,
            "Status": (
                "completed"
                if candidate.is_complete(experiment.horizon_h)
                else "partial"
            ),
            "Clean-air volume (m³)": candidate.clean_air_volume_m3,
        }
    )
st.dataframe(branch_rows, hide_index=True, width="stretch")

timeline_rows = [
    {
        "Sequence": action.sequence,
        "Time (h)": action.time_h,
        "Location": action.location,
        "Cleaner": "ON" if action.cleaner_on else "OFF",
        "Meaning": "affects subsequent evolution",
    }
    for action in branch.actions
]
st.dataframe(timeline_rows, hide_index=True, width="stretch")
st.caption(
    "Repeated controls at the same timestamp remain ordered; the last recorded control governs the following positive-duration segment."
)

st.markdown("## Completed branch comparison")
completed = experiment.completed_summaries()
if completed:
    st.plotly_chart(completed_comparison_figure(experiment), width="stretch")
    full_reference = experiment.no_cleaner_reference(experiment.horizon_h)
    comparison_rows = []
    for summary in completed:
        summary_j = float(summary["J"])
        summary_percent = experiment.percentage_improvement(
            summary_j, float(full_reference["J"])
        )
        final = np.asarray(summary["concentration"])
        comparison_rows.append(
            {
                "Branch": summary["name"],
                "J (µg·h/m³)": summary_j,
                "Improvement vs no cleaner": format_percent(summary_percent),
                "Clean-air volume (m³)": summary["clean_air_volume_m3"],
                "Final A (µg/m³)": final[0],
                "Final B (µg/m³)": final[1],
                "Final C (µg/m³)": final[2],
            }
        )
    st.dataframe(comparison_rows, hide_index=True, width="stretch")
else:
    st.info("No branches are complete yet. Run one or more branches to the horizon to compare them.")

st.markdown(
    """
    <div class="lab-panel">
      <div class="lab-kicker">Interpretation boundary</div>
      Playback speed changes only screen refresh timing. Physics is reconstructed from simulation timestamps and exact matrix exponentials.
      Clean-air volume is equivalent delivered clean air, not electrical energy. Parameter learning and hidden-state inference are not implemented.
    </div>
    """,
    unsafe_allow_html=True,
)

if experiment.playing:
    time.sleep(PLAYBACK_DELAYS[speed])
    if experiment.playback_tick(PLAYBACK_STEP_H):
        st.rerun()
