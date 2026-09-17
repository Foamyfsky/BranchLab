"""Streamlit dashboard for the deterministic three-room particle world."""

from __future__ import annotations

import html
import math
from pathlib import Path
import time

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from branchlab.experiment import CLEANER_CAPACITY, HORIZONS, INITIAL_STATES, ROOMS
from branchlab.session import ExperimentSession


ROOM_COLORS = {"A": "#31d8e6", "B": "#ffb84a", "C": "#ef6f61"}
BRANCH_COLORS = ("#31d8e6", "#ffb84a", "#b58bd8", "#86c77a", "#ef6f61")
PLAYBACK_STEP_H = 0.05
PLAYBACK_DELAYS = {"Slow": 0.75, "Normal": 0.32, "Fast": 0.10}
PROJECT_ROOT = Path(__file__).resolve().parent
WORKED_EXAMPLE_PATH = PROJECT_ROOT / "examples" / "cleaner-relocation.json"


st.set_page_config(
    page_title="BranchLab Particle Console",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root {
        --charcoal: #0d1114; --panel: #171d21; --copper: #b66c35;
        --brass: #d1a64b; --cyan: #31d8e6; --amber: #ffb84a;
        --cream: #f1e3bf; --muted: #9fa8a6;
    }
    .stApp {
        background:
          linear-gradient(rgba(49,216,230,.025) 1px, transparent 1px),
          linear-gradient(90deg, rgba(49,216,230,.025) 1px, transparent 1px),
          radial-gradient(circle at 80% 0%, #20272a 0%, var(--charcoal) 44%);
        background-size: 24px 24px, 24px 24px, auto;
    }
    .block-container { padding-top: 1.25rem; padding-bottom: 2.5rem; max-width: 1500px; }
    h1, h2, h3 { letter-spacing: .035em; color: var(--cream); }
    h1 { font-size: 2rem !important; margin-bottom: .15rem !important; }
    h2 { font-size: 1.35rem !important; }
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #1b2226, #11171a);
        border: 1px solid #6e4729; border-left: 4px solid var(--copper);
        padding: .55rem .7rem; box-shadow: inset 0 0 18px rgba(0,0,0,.25);
    }
    [data-testid="stMetricValue"] { color: var(--cyan); font-size: 1.25rem; }
    [data-testid="stMetricLabel"] { color: #d8cfb6; }
    .lab-panel {
        border: 1px solid #745033; border-top: 3px solid var(--brass);
        background: linear-gradient(145deg, rgba(28,35,39,.96), rgba(14,19,22,.96));
        padding: .7rem .85rem; margin: .25rem 0 .75rem;
        box-shadow: 0 8px 24px rgba(0,0,0,.28), inset 0 0 0 1px rgba(255,184,74,.06);
    }
    .lab-kicker { color: var(--amber); font-size: .75rem; letter-spacing: .13em; text-transform: uppercase; }
    .status-line { color: #d8cfb6; font-family: monospace; margin: .15rem 0 .8rem; }
    .status-chip {
        display: inline-block; padding: .12rem .5rem; margin-right: .3rem;
        border: 1px solid var(--cyan); color: var(--cyan); background: rgba(49,216,230,.08);
        font-size: .76rem;
    }
    .status-chip.amber { border-color: var(--amber); color: var(--amber); background: rgba(255,184,74,.08); }
    .synthetic-note {
        border-left: 4px solid var(--amber); background: rgba(255,184,74,.07);
        padding: .55rem .75rem; color: #e8d9b6; margin: .35rem 0 .8rem;
    }
    div.stButton > button, div.stDownloadButton > button {
        border-radius: 0; border: 1px solid #a96636;
        box-shadow: inset 0 0 0 1px rgba(255,184,74,.08);
    }
    small.muted { color: var(--muted); }
    </style>
    """,
    unsafe_allow_html=True,
)


def current_experiment() -> ExperimentSession:
    if "experiment" not in st.session_state:
        if st.query_params.get("example") == "cleaner-relocation":
            restored, stay_id, move_id = load_worked_example()
            st.session_state.experiment = restored
            st.session_state.flash_message = (
                "Loaded and replay-verified the worked example. Playback is paused."
            )
            st.session_state.pending_full_sync = True
            st.session_state.pending_workspace_view = "Compare"
            st.session_state.pending_compare_reference = stay_id
            st.session_state.pending_compare_candidate = move_id
        else:
            st.session_state.experiment = ExperimentSession(
                INITIAL_STATES[0], 5.0, cleaner_location="C", cleaner_on=True
            )
    return st.session_state.experiment


def root_branch(experiment: ExperimentSession):
    return next(branch for branch in experiment.branches.values() if branch.parent_id is None)


def branch_display_name(experiment: ExperimentSession, branch_id: str) -> str:
    branch = experiment.branches[branch_id]
    if branch.parent_id is None and branch.name == "main":
        return "Original branch"
    return branch.name


def branch_label(experiment: ExperimentSession, branch_id: str) -> str:
    branch = experiment.branches[branch_id]
    status = "complete" if branch.is_complete(experiment.horizon_h) else "partial"
    return f"{branch_display_name(experiment, branch_id)} · t={branch.time_h:g} h · {status}"


def branch_selector_label(experiment: ExperimentSession, branch_id: str) -> str:
    """Return a stable selector label; live time/status are shown beside the widget."""

    branch = experiment.branches[branch_id]
    if branch.parent_id is None:
        return f"{branch_display_name(experiment, branch_id)} (root)"
    parent = experiment.branches[branch.parent_id]
    parent_name = branch_display_name(experiment, parent.branch_id)
    return f"{branch.name} (from {parent_name} at {branch.fork_time_h:g} h)"


def applied_control_text(experiment: ExperimentSession, branch_id: str | None = None) -> str:
    branch = experiment.active_branch if branch_id is None else experiment.branches[branch_id]
    state = "on" if branch.cleaner_on else "off"
    return f"{branch.cleaner_location} / {state}"


def setup_preset(experiment: ExperimentSession) -> str:
    initial = experiment.initial_concentration
    if np.array_equal(initial, INITIAL_STATES[0]):
        return "Preset: (2, 2, 2.5)"
    if np.array_equal(initial, INITIAL_STATES[1]):
        return "Preset: (2.5, 2, 2)"
    return "Custom"


def worked_example_branch_ids(experiment: ExperimentSession) -> tuple[str, str]:
    by_name = {branch.name: branch_id for branch_id, branch in experiment.branches.items()}
    try:
        stay_id = by_name["Stay in C"]
        move_id = by_name["Move to A"]
    except KeyError as error:
        raise ValueError("worked example branches are missing") from error
    stay = experiment.branches[stay_id]
    move = experiment.branches[move_id]
    if (
        stay.parent_id is not None
        or move.parent_id != stay_id
        or not math.isclose(move.fork_time_h, 2.5, abs_tol=1e-12)
        or not stay.is_complete(experiment.horizon_h)
        or not move.is_complete(experiment.horizon_h)
    ):
        raise ValueError("worked example lineage or completion state is invalid")
    return stay_id, move_id


def load_worked_example() -> tuple[ExperimentSession, str, str]:
    """Load the repository example through the validated replay implementation."""

    restored = ExperimentSession.from_json(WORKED_EXAMPLE_PATH.read_bytes())
    restored.pause()
    stay_id, move_id = worked_example_branch_ids(restored)
    return restored, stay_id, move_id


def reset_experiment(
    experiment: ExperimentSession,
    message: str,
    *,
    workspace_view: str = "Experiment",
    comparison: tuple[str, str] | None = None,
) -> None:
    st.session_state.experiment = experiment
    st.session_state.flash_message = message
    st.session_state.pending_full_sync = True
    st.session_state.pending_workspace_view = workspace_view
    if comparison is not None:
        st.session_state.pending_compare_reference = comparison[0]
        st.session_state.pending_compare_candidate = comparison[1]
    st.rerun()


def prepare_ui_state(experiment: ExperimentSession) -> None:
    pending_branch = st.session_state.pop("pending_active_branch", None)
    pending_workspace = st.session_state.pop("pending_workspace_view", None)
    pending_compare_reference = st.session_state.pop("pending_compare_reference", None)
    pending_compare_candidate = st.session_state.pop("pending_compare_candidate", None)
    full_sync = bool(st.session_state.pop("pending_full_sync", False))
    if pending_workspace in ("Experiment", "Compare"):
        st.session_state.workspace_view = pending_workspace
    elif "workspace_view" not in st.session_state:
        st.session_state.workspace_view = "Experiment"
    if full_sync:
        for key in ("compare_reference", "compare_candidate", "compare_quantity"):
            st.session_state.pop(key, None)
    if pending_compare_reference in experiment.branches:
        st.session_state.compare_reference = pending_compare_reference
    if pending_compare_candidate in experiment.branches:
        st.session_state.compare_candidate = pending_compare_candidate
    if pending_compare_reference is not None or pending_compare_candidate is not None:
        st.session_state.compare_quantity = "Room mean"
    if pending_branch is not None:
        st.session_state.active_branch_selector = pending_branch
    if full_sync or st.session_state.get("active_branch_selector") not in experiment.branches:
        st.session_state.active_branch_selector = experiment.active_branch_id
    branch = experiment.branches[st.session_state.active_branch_selector]
    if full_sync or "cleaner_location_draft" not in st.session_state:
        st.session_state.cleaner_location_draft = branch.cleaner_location
        st.session_state.cleaner_on_draft = branch.cleaner_on
    if full_sync or st.session_state.pop("pending_target_sync", False):
        st.session_state.advance_target_h = float(branch.time_h)
    setup_keys_missing = any(
        key not in st.session_state
        for key in ("setup_preset", "setup_horizon", "setup_location", "setup_on")
    )
    if full_sync or setup_keys_missing:
        st.session_state.setup_preset = setup_preset(experiment)
        st.session_state.setup_horizon = experiment.horizon_h
        st.session_state.setup_location = root_branch(experiment).actions[0].location
        st.session_state.setup_on = root_branch(experiment).actions[0].cleaner_on
        for index, room in enumerate(ROOMS):
            st.session_state[f"custom_initial_{room}"] = float(
                experiment.initial_concentration[index]
            )
    if st.session_state.pop("pending_branch_name_clear", False):
        st.session_state.new_branch_name = ""


def sync_branch_controls(experiment: ExperimentSession, *, force: bool = False) -> None:
    branch = experiment.active_branch
    values = {
        "cleaner_location_draft": branch.cleaner_location,
        "cleaner_on_draft": branch.cleaner_on,
        "advance_target_h": float(branch.time_h),
    }
    for key, value in values.items():
        if force or key not in st.session_state:
            st.session_state[key] = value


def format_percent(value: float | None) -> str:
    return "N/A" if value is None or not math.isfinite(value) else f"{value:.2f}%"


def plot_layout(title: str, height: int = 430) -> dict[str, object]:
    return {
        "title": {"text": title, "x": 0.01, "xanchor": "left", "font": {"size": 16}},
        "height": height,
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "#11171a",
        "font": {"family": "Arial, sans-serif", "color": "#f1e3bf"},
        "margin": {"l": 60, "r": 25, "t": 68, "b": 55},
        "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.03, "x": 0},
        "hovermode": "x unified",
    }


def schematic_html(experiment: ExperimentSession) -> str:
    branch = experiment.active_branch
    room_x = {"A": 35, "B": 305, "C": 575}
    rooms: list[str] = []
    for index, room in enumerate(ROOMS):
        x = room_x[room]
        cleaner_here = room == branch.cleaner_location
        border = "#31d8e6" if cleaner_here and branch.cleaner_on else "#8d6845"
        cleaner = ""
        if cleaner_here:
            cleaner_color = "#31d8e6" if branch.cleaner_on else "#b66c35"
            label = "CLEANER ON" if branch.cleaner_on else "CLEANER OFF"
            cleaner = f"""
              <g aria-label=\"{label}\">
                <rect x=\"{x + 158}\" y=\"52\" width=\"36\" height=\"36\"
                      fill=\"#0d1114\" stroke=\"{cleaner_color}\" stroke-width=\"3\"/>
                <circle cx=\"{x + 176}\" cy=\"70\" r=\"9\" fill=\"none\"
                        stroke=\"{cleaner_color}\" stroke-width=\"2\"/>
                <path d=\"M{x + 176} 61 v18 M{x + 167} 70 h18\"
                      stroke=\"{cleaner_color}\" stroke-width=\"2\"/>
                <text x=\"{x + 176}\" y=\"105\" text-anchor=\"middle\"
                      fill=\"{cleaner_color}\" font-size=\"11\" font-family=\"monospace\">{label}</text>
              </g>
            """
        rooms.append(
            f"""
            <g>
              <rect x=\"{x}\" y=\"42\" width=\"210\" height=\"142\" rx=\"4\"
                    fill=\"#131a1e\" stroke=\"{border}\" stroke-width=\"3\"/>
              <path d=\"M{x+12} 58 h34 M{x+12} 58 v20 M{x+198} 58 h-34 M{x+198} 58 v20\"
                    stroke=\"#d1a64b\" stroke-width=\"2\" fill=\"none\"/>
              <text x=\"{x+18}\" y=\"88\" fill=\"#f1e3bf\" font-size=\"22\" font-family=\"monospace\">ROOM {room}</text>
              <text x=\"{x+105}\" y=\"135\" text-anchor=\"middle\" fill=\"{ROOM_COLORS[room]}\"
                    font-size=\"29\" font-family=\"monospace\">{branch.concentration[index]:.4f}</text>
              <text x=\"{x+105}\" y=\"160\" text-anchor=\"middle\" fill=\"#9fa8a6\"
                    font-size=\"13\" font-family=\"monospace\">µg/m³ room average</text>
              {cleaner}
            </g>
            """
        )
    return f"""
    <style>
      html, body {{ margin: 0; background: transparent; color: #f1e3bf; font-family: Arial, sans-serif; }}
      .lab-panel {{
        box-sizing: border-box; border: 1px solid #745033; border-top: 3px solid #d1a64b;
        background: linear-gradient(145deg, rgba(28,35,39,.98), rgba(14,19,22,.98));
        padding: 10px 14px 6px; box-shadow: inset 0 0 0 1px rgba(255,184,74,.06);
      }}
      .lab-kicker {{ color: #ffb84a; font: 12px monospace; letter-spacing: .13em; text-transform: uppercase; }}
      svg {{ display: block; height: 225px; width: 100%; }}
    </style>
    <div class=\"lab-panel\">
      <div class=\"lab-kicker\">Live fully observed room-average state · {html.escape(branch_label(experiment, branch.branch_id))}</div>
      <svg viewBox=\"0 0 820 225\" width=\"100%\" role=\"img\"
           aria-label=\"Three connected well-mixed rooms and one movable air cleaner\">
        <defs>
          <marker id=\"arrow\" viewBox=\"0 0 10 10\" refX=\"5\" refY=\"5\"
                  markerWidth=\"5\" markerHeight=\"5\" orient=\"auto-start-reverse\">
            <path d=\"M 0 0 L 10 5 L 0 10 z\" fill=\"#ffb84a\"/>
          </marker>
        </defs>
        <path d=\"M250 106 H295\" stroke=\"#b66c35\" stroke-width=\"3\"
              marker-end=\"url(#arrow)\"/>
        <path d=\"M295 120 H250\" stroke=\"#b66c35\" stroke-width=\"3\"
              marker-end=\"url(#arrow)\"/>
        <path d=\"M520 106 H565\" stroke=\"#b66c35\" stroke-width=\"3\"
              marker-end=\"url(#arrow)\"/>
        <path d=\"M565 120 H520\" stroke=\"#b66c35\" stroke-width=\"3\"
              marker-end=\"url(#arrow)\"/>
        <text x=\"272\" y=\"91\" text-anchor=\"middle\" fill=\"#9fa8a6\" font-size=\"10\" font-family=\"monospace\">50 m³/h</text>
        <text x=\"542\" y=\"91\" text-anchor=\"middle\" fill=\"#9fa8a6\" font-size=\"10\" font-family=\"monospace\">50 m³/h</text>
        {''.join(rooms)}
        <text x=\"410\" y=\"213\" text-anchor=\"middle\" fill=\"#9fa8a6\" font-size=\"11\" font-family=\"monospace\">SYMMETRIC MODELED AIR EXCHANGE · A–B–C</text>
      </svg>
    </div>
    """


def add_event_markers(
    figure: go.Figure, experiment: ExperimentSession, branch_id: str, *, show_fork: bool = True
) -> None:
    branch = experiment.branches[branch_id]
    for action in branch.actions[1:]:
        state = "on" if action.cleaner_on else "off"
        figure.add_vline(
            x=action.time_h,
            line_width=1,
            line_dash="dot",
            line_color="#ffb84a",
            annotation_text=f"{action.location} {state}",
            annotation_position="top right",
        )
    if show_fork and branch.parent_id is not None and branch.fork_time_h > 0:
        figure.add_vline(
            x=branch.fork_time_h,
            line_width=2,
            line_dash="dash",
            line_color="#b58bd8",
            annotation_text="fork",
            annotation_position="bottom right",
        )


def history_figure(experiment: ExperimentSession, include_reference: bool) -> go.Figure:
    branch = experiment.active_branch
    times, concentrations = experiment.history(branch.branch_id)
    figure = go.Figure()
    for index, room in enumerate(ROOMS):
        figure.add_trace(
            go.Scatter(
                x=times,
                y=concentrations[:, index],
                name=f"Room {room}",
                mode="lines",
                line={"color": ROOM_COLORS[room], "width": 3},
                hovertemplate="t=%{x:.3f} h<br>%{y:.5f} µg/m³<extra>Room " + room + "</extra>",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=[0.0], y=[experiment.initial_concentration[index]], mode="markers",
                name=f"Room {room} initial", showlegend=False,
                marker={"color": ROOM_COLORS[room], "symbol": "diamond", "size": 9},
                hovertemplate="Initial: %{y:.5f} µg/m³<extra>Room " + room + "</extra>",
            )
        )
    if include_reference:
        reference_times, reference = experiment.no_cleaner_history(branch.time_h)
        for index, room in enumerate(ROOMS):
            figure.add_trace(
                go.Scatter(
                    x=reference_times,
                    y=reference[:, index],
                    name=f"Room {room}, no cleaner",
                    mode="lines",
                    line={"color": ROOM_COLORS[room], "width": 1.4, "dash": "dot"},
                    opacity=0.75,
                )
            )
    add_event_markers(figure, experiment, branch.branch_id)
    figure.update_layout(**plot_layout("Current branch: room-average concentration history"))
    figure.update_xaxes(title="Simulation time (h)", range=[0, experiment.horizon_h], gridcolor="#273238")
    figure.update_yaxes(title="Concentration (µg/m³)", rangemode="tozero", gridcolor="#273238")
    return figure


def comparison_history_figure(
    experiment: ExperimentSession, reference_id: str, comparison_id: str, quantity: str
) -> go.Figure:
    figure = go.Figure()
    quantity_index = None if quantity == "Room mean" else ROOMS.index(quantity[-1])
    y_title = "Room-mean concentration (µg/m³)" if quantity_index is None else f"Room {ROOMS[quantity_index]} concentration (µg/m³)"
    for color, branch_id in zip(("#31d8e6", "#ffb84a"), (reference_id, comparison_id)):
        times, values = experiment.history(branch_id)
        series = np.mean(values, axis=1) if quantity_index is None else values[:, quantity_index]
        figure.add_trace(
            go.Scatter(
                x=times, y=series, mode="lines", name=branch_label(experiment, branch_id),
                line={"color": color, "width": 3},
                hovertemplate="t=%{x:.3f} h<br>%{y:.5f} µg/m³<extra>%{fullData.name}</extra>",
            )
        )
        add_event_markers(figure, experiment, branch_id)
    figure.update_layout(**plot_layout(f"Like-for-like history: {quantity}", 420))
    figure.update_xaxes(title="Simulation time (h)", range=[0, experiment.horizon_h], gridcolor="#273238")
    figure.update_yaxes(title=y_title, rangemode="tozero", gridcolor="#273238")
    return figure


def cumulative_comparison_figure(
    experiment: ExperimentSession, reference_id: str, comparison_id: str
) -> go.Figure:
    figure = go.Figure()
    for color, branch_id in zip(("#31d8e6", "#ffb84a"), (reference_id, comparison_id)):
        summary = experiment.branch_summary(branch_id)
        figure.add_trace(
            go.Bar(
                x=["I_A", "I_B", "I_C", "J"],
                y=[*summary["integrals"], summary["J"]],
                name=branch_label(experiment, branch_id), marker_color=color,
                hovertemplate="%{x}: %{y:.8f} µg·h/m³<extra>%{fullData.name}</extra>",
            )
        )
    figure.update_layout(**plot_layout("Cumulative exposure outcomes", 360))
    figure.update_layout(barmode="group")
    figure.update_yaxes(title="Integrated concentration (µg·h/m³)", rangemode="tozero", gridcolor="#273238")
    return figure


def budget_comparison_figure(
    experiment: ExperimentSession, reference_id: str, comparison_id: str
) -> go.Figure:
    labels = [branch_label(experiment, branch_id) for branch_id in (reference_id, comparison_id)]
    values = [
        experiment.branches[branch_id].clean_air_volume_m3
        for branch_id in (reference_id, comparison_id)
    ]
    figure = go.Figure(
        go.Bar(x=labels, y=values, marker_color=["#31d8e6", "#ffb84a"],
               hovertemplate="%{y:.3f} m³<extra></extra>")
    )
    figure.update_layout(**plot_layout("Consumed clean-air volume", 320))
    figure.update_yaxes(title="Clean-air volume (m³)", rangemode="tozero", gridcolor="#273238")
    return figure


def render_metrics(experiment: ExperimentSession) -> None:
    branch = experiment.active_branch
    summary = experiment.branch_summary()
    reference = experiment.no_cleaner_reference(branch.time_h)
    improvement = experiment.percentage_improvement(float(summary["J"]), float(reference["J"]))
    cols = st.columns(5)
    for col, room, value in zip(cols[:3], ROOMS, summary["integrals"]):
        col.metric(
            f"Room {room} cumulative concentration (I_{room})",
            f"{float(value):.5f}",
            help="µg·h/m³",
        )
    cols[3].metric(
        "Cumulative mean concentration (J)",
        f"{float(summary['J']):.5f}",
        help="µg·h/m³",
    )
    cols[4].metric("Equivalent clean-air volume", f"{branch.clean_air_volume_m3:.1f} m³")
    status = "complete" if branch.is_complete(experiment.horizon_h) else "partial"
    st.caption(
        f"{status.capitalize()} values through t={branch.time_h:g} h. "
        f"J improvement versus the matching no-cleaner reference: {format_percent(improvement)}. "
        "Cumulative concentration normally increases with elapsed time, so compare matching intervals. "
        "Clean-air volume measures processed air, not energy use."
    )
    if branch.is_complete(experiment.horizon_h):
        values = " · ".join(
            f"{room} {float(value):.5f} µg/m³"
            for room, value in zip(ROOMS, branch.concentration)
        )
        st.caption(f"Final room-average concentrations: {values}.")


def render_rate_explanation(experiment: ExperimentSession) -> None:
    selected_room = st.radio("Explain current rate in room", ROOMS, horizontal=True, key="rate_room")
    rates = experiment.rate_contributions(selected_room)
    cols = st.columns(4)
    cols[0].metric("Net exchange", f"{rates['net_exchange']:+.6f} µg/m³/h")
    cols[1].metric("Background removal", f"{rates['background_removal']:+.6f} µg/m³/h")
    cols[2].metric("Cleaner removal", f"{rates['cleaner_removal']:+.6f} µg/m³/h")
    cols[3].metric("Total dc/dt", f"{rates['total']:+.6f} µg/m³/h")
    direction = "rising" if rates["total"] > 1e-12 else "falling" if rates["total"] < -1e-12 else "steady"
    st.caption(
        f"Room {selected_room} is currently {direction}: net exchange, background removal, "
        "and cleaner removal are the three contributions summed into dc/dt."
    )


def render_experiment_view(experiment: ExperimentSession) -> None:
    selector_col, identity_col = st.columns([1.05, 1.95])
    selected_branch_id = selector_col.selectbox(
        "Active branch",
        options=list(experiment.branches),
        format_func=lambda item: branch_selector_label(experiment, item),
        key="active_branch_selector",
    )
    if selected_branch_id != experiment.active_branch_id:
        experiment.switch_branch(selected_branch_id)
        sync_branch_controls(experiment, force=True)
        st.rerun()
    branch = experiment.active_branch
    parent_text = (
        "none — this is the original branch"
        if branch.parent_id is None
        else f"{branch_label(experiment, branch.parent_id)}; forked at t={branch.fork_time_h:g} h"
    )
    identity_col.markdown(
        f"**Branch identity:** `{branch.branch_id}` · **Parent:** {parent_text}  \n"
        f"**Applied control:** cleaner {applied_control_text(experiment)} since t={branch.actions[-1].time_h:g} h"
    )

    st.iframe(schematic_html(experiment), width="stretch", height=275, tab_index=0)

    control_col, advance_col, fork_col = st.columns([1.05, 1.05, 1.0], gap="large")
    with control_col:
        st.markdown("### 1 · Set cleaner")
        control_location = st.selectbox("Selected room", ROOMS, key="cleaner_location_draft")
        control_on = st.toggle("Cleaner selected on", key="cleaner_on_draft")
        selected_text = f"{control_location} / {'on' if control_on else 'off'}"
        st.caption(
            f"Selected: **{selected_text}** · Applied: **{applied_control_text(experiment)}**. "
            "Selection does not act until applied."
        )
        if st.button(
            "Apply cleaner change",
            disabled=branch.is_complete(experiment.horizon_h),
            type="primary",
            width="stretch",
            key="apply_control_button",
        ):
            action = experiment.set_control(location=control_location, cleaner_on=bool(control_on))
            st.session_state.flash_message = (
                f"Cleaner {action.location} / {'on' if action.cleaner_on else 'off'} "
                f"takes effect after t={action.time_h:g} h."
            )
            st.rerun()

    with advance_col:
        st.markdown("### 2 · Advance time")
        target = st.number_input(
            "Advance to time (h)", min_value=float(branch.time_h),
            max_value=float(experiment.horizon_h), step=0.1, key="advance_target_h",
        )
        c1, c2 = st.columns(2)
        if c1.button(
            "Advance exactly", disabled=branch.is_complete(experiment.horizon_h),
            width="stretch",
            key="advance_exact_button",
        ):
            experiment.advance_to(float(target))
            st.session_state.pending_target_sync = True
            st.rerun()
        if c2.button(
            "Finish this branch", disabled=branch.is_complete(experiment.horizon_h),
            width="stretch",
            key="finish_branch_button",
        ):
            experiment.run_to_end()
            st.session_state.pending_target_sync = True
            st.rerun()
        p1, p2, p3 = st.columns([1, 1, 1.2])
        if p1.button(
            "Play", disabled=branch.is_complete(experiment.horizon_h), width="stretch",
            key="play_button",
        ):
            experiment.play()
            st.rerun()
        if p2.button(
            "Pause", disabled=not experiment.playing, width="stretch", key="pause_button"
        ):
            experiment.pause()
            st.rerun()
        speed = p3.selectbox("Playback", list(PLAYBACK_DELAYS), index=1, key="playback_speed")
        st.caption(
            "Playback advances in bounded 0.05 h simulation steps. Speed changes only wall-clock refresh rate."
        )

    with fork_col:
        st.markdown("### 3 · Fork experiment")
        branch_name = st.text_input("New branch name", placeholder="e.g. Move to A", key="new_branch_name")
        st.caption(
            "A fork copies this paused timestamp, concentration, integrals, budget, and action history."
        )
        if st.button(
            "Create branch and switch",
            disabled=experiment.playing or not branch_name.strip(),
            width="stretch",
            key="create_branch_button",
        ):
            try:
                parent_id = branch.branch_id
                fork_time = branch.time_h
                new_id = experiment.fork(branch_name)
                experiment.switch_branch(new_id)
                st.session_state.pending_active_branch = new_id
                st.session_state.pending_full_sync = True
                st.session_state.pending_branch_name_clear = True
                st.session_state.flash_message = (
                    f"Created {branch_name.strip()} from {branch_label(experiment, parent_id)} "
                    f"at t={fork_time:g} h and switched to it."
                )
                st.rerun()
            except ValueError as error:
                st.error(str(error))
        if branch.parent_id is not None:
            parent = experiment.branches[branch.parent_id]
            parent_name = branch_display_name(experiment, parent.branch_id)
            st.caption(
                f"Current lineage: {parent_name} → {branch.name} "
                f"at {branch.fork_time_h:g} h."
            )

    st.markdown("## Outcomes and history")
    render_metrics(experiment)
    overlay_reference = st.checkbox(
        "Overlay matching no-cleaner room histories", value=False, key="overlay_reference"
    )
    st.plotly_chart(history_figure(experiment, overlay_reference), width="stretch", key="experiment_history")

    with st.expander("Why is a room rising or falling?", expanded=True):
        render_rate_explanation(experiment)

    with st.expander("Action timeline and replay record"):
        action_rows = [
            {
                "sequence": action.sequence,
                "simulation time (h)": action.time_h,
                "cleaner room": action.location,
                "cleaner": "on" if action.cleaner_on else "off",
                "effect": "subsequent evolution",
            }
            for action in branch.actions
        ]
        st.dataframe(action_rows, width="stretch", hide_index=True)
        st.caption(
            "Repeated controls at one timestamp are retained in sequence order; the last one controls the next nonzero segment."
        )


def render_compare_view(experiment: ExperimentSession) -> None:
    completed = [
        branch_id for branch_id, branch in experiment.branches.items()
        if branch.is_complete(experiment.horizon_h)
    ]
    st.markdown("## Compare completed branches")
    st.caption(
        "Comparisons are within this fixed initial state and horizon. Choose one physical quantity per history chart."
    )
    if len(completed) < 2:
        st.info(
            "Complete at least two branches to compare them. In Experiment: advance, fork, apply a different control, and finish both branches."
        )
        return
    if st.session_state.get("compare_reference") not in completed:
        st.session_state.compare_reference = completed[0]
    if st.session_state.get("compare_candidate") not in completed:
        st.session_state.compare_candidate = completed[1]
    c1, c2, c3 = st.columns([1, 1, .8])
    reference_id = c1.selectbox(
        "Reference branch", completed,
        format_func=lambda item: branch_label(experiment, item), key="compare_reference",
    )
    comparison_id = c2.selectbox(
        "Comparison branch", completed,
        format_func=lambda item: branch_label(experiment, item), key="compare_candidate",
    )
    quantity = c3.selectbox("History quantity", ["Room mean", "Room A", "Room B", "Room C"], key="compare_quantity")
    if reference_id == comparison_id:
        st.warning("Select two different completed branches for a meaningful comparison.")

    try:
        worked_reference, worked_alternative = worked_example_branch_ids(experiment)
    except ValueError:
        worked_reference = worked_alternative = ""
    if (reference_id, comparison_id) == (worked_reference, worked_alternative):
        reference_summary = experiment.branch_summary(reference_id)
        alternative_summary = experiment.branch_summary(comparison_id)
        reduction = experiment.percentage_improvement(
            float(alternative_summary["J"]), float(reference_summary["J"])
        )
        st.markdown(
            "**Worked example.** Both strategies share the first 2.5 hours and use the same "
            "clean-air budget. Moving to A lowers overall cumulative mean concentration, while "
            "increasing cumulative concentration in Room C."
        )
        st.caption(
            f"Stay in C: J = {float(reference_summary['J']):.10f}; "
            f"Move to A: J = {float(alternative_summary['J']):.10f}; "
            f"both budgets = {float(reference_summary['clean_air_volume_m3']):g} m³; "
            f"J reduction relative to Stay in C = {format_percent(reduction)}. "
            "Stay in C is the demonstration reference, not the best fixed placement."
        )

    st.plotly_chart(
        comparison_history_figure(experiment, reference_id, comparison_id, quantity),
        width="stretch", key="comparison_history",
    )
    left, right = st.columns([1.5, 1])
    with left:
        st.plotly_chart(
            cumulative_comparison_figure(experiment, reference_id, comparison_id),
            width="stretch", key="cumulative_comparison",
        )
    with right:
        st.plotly_chart(
            budget_comparison_figure(experiment, reference_id, comparison_id),
            width="stretch", key="budget_comparison",
        )

    reference = experiment.branch_summary(reference_id)
    comparison = experiment.branch_summary(comparison_id)
    metrics = [
        ("J", float(reference["J"]), float(comparison["J"]), "µg·h/m³"),
        *[
            (f"I_{room}", float(reference["integrals"][index]), float(comparison["integrals"][index]), "µg·h/m³")
            for index, room in enumerate(ROOMS)
        ],
        (
            "Clean-air volume",
            float(reference["clean_air_volume_m3"]),
            float(comparison["clean_air_volume_m3"]),
            "m³",
        ),
    ]
    rows = []
    for metric, reference_value, comparison_value, unit in metrics:
        difference = comparison_value - reference_value
        percent = None if abs(reference_value) <= 1e-10 else 100.0 * difference / reference_value
        rows.append(
            {
                "quantity": metric,
                "reference": f"{reference_value:.8f}",
                "comparison": f"{comparison_value:.8f}",
                "difference (comparison − reference)": f"{difference:+.8f} {unit}",
                "percent difference": format_percent(percent),
            }
        )
    st.dataframe(rows, width="stretch", hide_index=True)

    ref_budget = float(reference["clean_air_volume_m3"])
    cmp_budget = float(comparison["clean_air_volume_m3"])
    if math.isclose(ref_budget, cmp_budget, rel_tol=0.0, abs_tol=1e-10):
        st.success(f"Equal cleaner budgets: both branches consumed {ref_budget:g} m³ of clean air.")
    else:
        st.warning(
            f"Unequal cleaner budgets: reference {ref_budget:g} m³; comparison {cmp_budget:g} m³. "
            "Outcome differences combine placement/timing and resource-use effects."
        )
    j_reduction = experiment.percentage_improvement(float(comparison["J"]), float(reference["J"]))
    worse_rooms = [
        room for index, room in enumerate(ROOMS)
        if float(comparison["integrals"][index]) > float(reference["integrals"][index]) + 1e-10
    ]
    room_note = (
        "No room cumulative concentration is higher in the comparison."
        if not worse_rooms
        else "Higher cumulative concentration in comparison: room " + ", ".join(worse_rooms) + "."
    )
    st.info(
        f"Lower J means lower cumulative concentration averaged across rooms. "
        f"Comparison J reduction versus reference: {format_percent(j_reduction)}. {room_note} "
        "A lower system mean does not guarantee improvement in every room."
    )


def render_setup_and_replay(experiment: ExperimentSession) -> None:
    with st.expander("New experiment setup", expanded=False):
        st.caption(
            "Scenario settings stay fixed within an experiment. Editing these fields has no effect until you create a new experiment."
        )
        preset = st.selectbox(
            "Initial concentrations", ["Preset: (2, 2, 2.5)", "Preset: (2.5, 2, 2)", "Custom"],
            key="setup_preset",
        )
        custom_cols = st.columns(3)
        custom = np.array(
            [
                custom_cols[index].number_input(
                    f"Room {room} initial (µg/m³)", min_value=0.0, key=f"custom_initial_{room}"
                )
                for index, room in enumerate(ROOMS)
            ],
            dtype=float,
        )
        s1, s2, s3 = st.columns(3)
        horizon = s1.selectbox("Horizon (h)", HORIZONS, key="setup_horizon")
        location = s2.selectbox("Initial cleaner room", ROOMS, key="setup_location")
        cleaner_on = s3.toggle("Cleaner initially on", key="setup_on")
        if st.button("Create new experiment", width="stretch", key="create_experiment_button"):
            initial = (
                INITIAL_STATES[0] if preset == "Preset: (2, 2, 2.5)"
                else INITIAL_STATES[1] if preset == "Preset: (2.5, 2, 2)"
                else custom
            )
            reset_experiment(
                ExperimentSession(initial, float(horizon), location, bool(cleaner_on)),
                "Created a new independent experiment. Previous branches were not carried over.",
            )

    with st.expander("Save or load a reproducible experiment", expanded=False):
        st.caption(
            "JSON stores the versioned model, units, fixed scenario, lineage, timestamped controls, and replay-checked accumulated state."
        )
        st.download_button(
            "Download experiment JSON", data=experiment.to_json(),
            file_name="branchlab-particle-experiment.json", mime="application/json",
            width="stretch",
        )
        uploaded_json = st.file_uploader("Load experiment JSON", type=("json",), key="experiment_json")
        if st.button(
            "Validate, replay, and load", disabled=uploaded_json is None,
            width="stretch", key="load_experiment_button",
        ):
            try:
                restored = ExperimentSession.from_json(uploaded_json.getvalue())
                reset_experiment(restored, "Imported JSON, replayed every branch, and verified stored outcomes.")
            except ValueError as error:
                st.error(f"Import rejected: {error}")

    with st.expander("Model identity and fixed parameters"):
        st.markdown(
            "**Synthetic, deterministic, fully observed reference.** Three well-mixed 100 m³ rooms form A–B–C; "
            "adjacent symmetric exchange is 50 m³/h; background removal is 0.1 h⁻¹; cleaner capacity is "
            f"{CLEANER_CAPACITY:g} m³/h. There is no continuing source and relocation is instantaneous."
        )


def render_worked_example_loader() -> None:
    text_col, action_col = st.columns([3.2, 1.0], vertical_alignment="center")
    with text_col:
        st.markdown("### Worked comparison · cleaner relocation")
        st.caption(
            "Load two completed 5-hour branches: Stay in C versus Move to A after a shared "
            "2.5-hour history. Loading this example replaces the current experiment."
        )
    with action_col:
        if st.button(
            "Load worked example",
            type="primary",
            width="stretch",
            key="load_worked_example_button",
        ):
            try:
                restored, stay_id, move_id = load_worked_example()
                reset_experiment(
                    restored,
                    "Loaded and replay-verified the worked example. Playback is paused.",
                    workspace_view="Compare",
                    comparison=(stay_id, move_id),
                )
            except (OSError, ValueError) as error:
                st.error(f"Worked example could not be loaded: {error}")


experiment = current_experiment()
prepare_ui_state(experiment)

st.title("BranchLab · Particle World Console")
st.caption("Operate, branch, compare, and replay one deterministic three-room intervention experiment.")
branch = experiment.active_branch
play_state = "PLAYING" if experiment.playing else "PAUSED"
st.markdown(
    f"""
    <div class=\"status-line\">
      <span class=\"status-chip\">{play_state}</span>
      <span class=\"status-chip amber\">t = {branch.time_h:g} / {experiment.horizon_h:g} h</span>
      active = {html.escape(branch_label(experiment, branch.branch_id))} · cleaner {applied_control_text(experiment)}
    </div>
    <div class=\"synthetic-note\">
      Synthetic room-average concentrations, not resolved particle tracks. The entire state is visible;
      parameter learning and hidden-state inference are not implemented.
    </div>
    """,
    unsafe_allow_html=True,
)

flash = st.session_state.pop("flash_message", None)
if flash:
    st.success(flash)

render_worked_example_loader()
render_setup_and_replay(experiment)

view = st.segmented_control(
    "Workspace view", ["Experiment", "Compare"],
    selection_mode="single", key="workspace_view",
)
previous_view = st.session_state.get("_rendered_workspace_view")
if view == "Experiment" and previous_view != "Experiment":
    st.session_state.active_branch_selector = experiment.active_branch_id
    sync_branch_controls(experiment, force=True)
st.session_state._rendered_workspace_view = view
if view == "Compare":
    render_compare_view(experiment)
else:
    render_experiment_view(experiment)

if experiment.playing:
    time.sleep(PLAYBACK_DELAYS[st.session_state.get("playback_speed", "Normal")])
    experiment.playback_tick(PLAYBACK_STEP_H)
    st.session_state.pending_target_sync = True
    st.rerun()
