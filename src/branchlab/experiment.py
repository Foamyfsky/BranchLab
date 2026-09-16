"""Run the three-room air-cleaner placement and timing experiment."""

from __future__ import annotations

import csv
import os
import tempfile
from itertools import product
from pathlib import Path

import numpy as np

from branchlab.transport import (
    clean_air_budget,
    concentration_history,
    simulate_piecewise,
)


ROOMS = ("A", "B", "C")
VOLUMES = np.array([100.0, 100.0, 100.0])
EXCHANGE = np.array(
    [
        [0.0, 50.0, 0.0],
        [50.0, 0.0, 50.0],
        [0.0, 50.0, 0.0],
    ]
)
BACKGROUND_REMOVAL = np.array([0.1, 0.1, 0.1])
CLEANER_CAPACITY = 100.0
INITIAL_STATES = (
    np.array([2.0, 2.0, 2.5]),
    np.array([2.5, 2.0, 2.0]),
)
HORIZONS = (1.0, 5.0)
RESULTS_DIR = Path("results")
CSV_PATH = RESULTS_DIR / "transport.csv"
FIGURE_PATH = RESULTS_DIR / "transport.png"

Schedule = tuple[str | None, str | None]


def active_schedules() -> list[Schedule]:
    """Return all first-half/second-half room choices in stable order."""

    return list(product(ROOMS, repeat=2))


def schedule_name(schedule: Schedule) -> str:
    if schedule == (None, None):
        return "none"
    return f"{schedule[0]}->{schedule[1]}"


def schedule_segments(schedule: Schedule, horizon: float):
    """Convert a named two-half schedule into clean-air control vectors."""

    segments = []
    for room in schedule:
        clean_air = np.zeros(len(ROOMS), dtype=float)
        if room is not None:
            clean_air[ROOMS.index(room)] = CLEANER_CAPACITY
        segments.append((horizon / 2.0, clean_air))
    return segments


def evaluate_case(initial: np.ndarray, horizon: float) -> list[dict[str, object]]:
    """Evaluate the reference and nine branches from one unchanged state."""

    records: list[dict[str, object]] = []
    schedules = [(None, None), *active_schedules()]
    for schedule in schedules:
        segments = schedule_segments(schedule, horizon)
        final, integrated = simulate_piecewise(
            initial, VOLUMES, EXCHANGE, BACKGROUND_REMOVAL, segments
        )
        records.append(
            {
                "initial_state": f"({initial[0]:g}, {initial[1]:g}, {initial[2]:g})",
                "initial_A_ug_m3": float(initial[0]),
                "initial_B_ug_m3": float(initial[1]),
                "initial_C_ug_m3": float(initial[2]),
                "horizon_h": horizon,
                "schedule": schedule_name(schedule),
                "first_room": schedule[0] or "none",
                "second_room": schedule[1] or "none",
                "is_fixed_placement": bool(
                    schedule[0] is not None and schedule[0] == schedule[1]
                ),
                "cleaner_capacity_m3_h": (
                    0.0 if schedule == (None, None) else CLEANER_CAPACITY
                ),
                "cleaner_operating_h": (
                    0.0 if schedule == (None, None) else horizon
                ),
                "clean_air_budget_m3": clean_air_budget(segments),
                "final_A_ug_m3": float(final[0]),
                "final_B_ug_m3": float(final[1]),
                "final_C_ug_m3": float(final[2]),
                "integrated_A_ug_h_m3": float(integrated[0]),
                "integrated_B_ug_h_m3": float(integrated[1]),
                "integrated_C_ug_h_m3": float(integrated[2]),
                "J_mean_ug_h_m3": float(np.mean(integrated)),
            }
        )

    reference = records[0]
    for record in records:
        for metric in ("A", "B", "C"):
            key = f"integrated_{metric}_ug_h_m3"
            improvement = float(reference[key]) - float(record[key])
            record[f"improvement_{metric}_ug_h_m3"] = improvement
            record[f"improvement_{metric}_percent"] = (
                100.0 * improvement / float(reference[key])
            )
        improvement_j = float(reference["J_mean_ug_h_m3"]) - float(
            record["J_mean_ug_h_m3"]
        )
        record["improvement_J_ug_h_m3"] = improvement_j
        record["improvement_J_percent"] = (
            100.0 * improvement_j / float(reference["J_mean_ug_h_m3"])
        )
    return records


def evaluate_all() -> list[dict[str, object]]:
    return [
        record
        for initial in INITIAL_STATES
        for horizon in HORIZONS
        for record in evaluate_case(initial, horizon)
    ]


def _write_csv(records: list[dict[str, object]]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def _best_records(records: list[dict[str, object]]):
    active = [record for record in records if record["schedule"] != "none"]
    fixed = [record for record in active if record["is_fixed_placement"]]
    key = lambda record: float(record["J_mean_ug_h_m3"])
    return min(fixed, key=key), min(active, key=key)


def _print_table(records: list[dict[str, object]]) -> None:
    for initial in INITIAL_STATES:
        initial_label = f"({initial[0]:g}, {initial[1]:g}, {initial[2]:g})"
        for horizon in HORIZONS:
            case = [
                record
                for record in records
                if record["initial_state"] == initial_label
                and record["horizon_h"] == horizon
            ]
            print(f"\nInitial {initial_label} micrograms/m^3 | horizon {horizon:g} h")
            print(
                "schedule       J      dJ%       I_A     dI_A       I_B     dI_B"
                "       I_C     dI_C"
            )
            for record in case:
                print(
                    f"{record['schedule']:>7}  "
                    f"{record['J_mean_ug_h_m3']:8.5f}  "
                    f"{record['improvement_J_percent']:7.2f}  "
                    f"{record['integrated_A_ug_h_m3']:8.5f}  "
                    f"{record['improvement_A_ug_h_m3']:7.5f}  "
                    f"{record['integrated_B_ug_h_m3']:8.5f}  "
                    f"{record['improvement_B_ug_h_m3']:7.5f}  "
                    f"{record['integrated_C_ug_h_m3']:8.5f}  "
                    f"{record['improvement_C_ug_h_m3']:7.5f}"
                )
            best_fixed, best_all = _best_records(case)
            print(
                f"Best fixed: {best_fixed['schedule']} "
                f"(J={best_fixed['J_mean_ug_h_m3']:.8f}); "
                f"best of nine: {best_all['schedule']} "
                f"(J={best_all['J_mean_ug_h_m3']:.8f})."
            )


def _plot(records: list[dict[str, object]]) -> None:
    os.environ.setdefault(
        "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "branchlab-matplotlib")
    )
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(2, 4, figsize=(18, 9), constrained_layout=True)
    room_colors = ("#2166ac", "#1b7837", "#b2182b")

    for row, initial in enumerate(INITIAL_STATES):
        initial_label = f"({initial[0]:g}, {initial[1]:g}, {initial[2]:g})"
        for horizon_index, horizon in enumerate(HORIZONS):
            case = [
                record
                for record in records
                if record["initial_state"] == initial_label
                and record["horizon_h"] == horizon
            ]
            best_fixed, best_all = _best_records(case)
            history_axis = axes[row, 2 * horizon_index]
            loss_axis = axes[row, 2 * horizon_index + 1]
            times = np.linspace(0.0, horizon, 201)

            best_rooms = tuple(
                str(best_all[key]) for key in ("first_room", "second_room")
            )
            best_history = concentration_history(
                initial,
                VOLUMES,
                EXCHANGE,
                BACKGROUND_REMOVAL,
                schedule_segments(best_rooms, horizon),
                times,
            )
            reference_history = concentration_history(
                initial,
                VOLUMES,
                EXCHANGE,
                BACKGROUND_REMOVAL,
                schedule_segments((None, None), horizon),
                times,
            )
            for room_index, (room, color) in enumerate(zip(ROOMS, room_colors)):
                history_axis.plot(
                    times,
                    reference_history[:, room_index],
                    color=color,
                    linestyle="--",
                    alpha=0.5,
                    label=f"{room}, none",
                )
                history_axis.plot(
                    times,
                    best_history[:, room_index],
                    color=color,
                    label=f"{room}, {best_all['schedule']}",
                )
            history_axis.axvline(
                horizon / 2.0, color="0.25", linestyle=":", linewidth=1.0
            )
            history_axis.set_title(
                f"c(0)={initial_label}, T={horizon:g} h\n"
                f"best schedule {best_all['schedule']} (switch at dotted line)"
            )
            history_axis.set_xlabel("Time (h)")
            history_axis.set_ylabel("Concentration (micrograms/m^3)")
            history_axis.grid(alpha=0.2)
            history_axis.legend(fontsize=7, ncol=2)

            names = [str(record["schedule"]) for record in case]
            losses = [float(record["J_mean_ug_h_m3"]) for record in case]
            colors = ["#bdbdbd"] + ["#9ecae1"] * 9
            fixed_index = names.index(str(best_fixed["schedule"]))
            best_index = names.index(str(best_all["schedule"]))
            colors[fixed_index] = "#fdae6b"
            colors[best_index] = "#31a354"
            loss_axis.bar(range(len(names)), losses, color=colors)
            loss_axis.set_xticks(range(len(names)), names, rotation=55, ha="right")
            loss_axis.set_title(
                f"Integrated mean concentration, T={horizon:g} h\n"
                "orange=best fixed; green=best of nine"
            )
            loss_axis.set_ylabel("J (micrograms*h/m^3)")
            loss_axis.grid(axis="y", alpha=0.2)
            loss_axis.set_ylim(bottom=0.0)

    figure.suptitle(
        "Three-room deterministic reference: cleaner position and timing",
        fontsize=15,
    )
    figure.savefig(FIGURE_PATH, dpi=180)
    plt.close(figure)


def main() -> None:
    records = evaluate_all()
    _write_csv(records)
    _plot(records)
    _print_table(records)
    print(f"\nWrote {CSV_PATH} and {FIGURE_PATH} (existing files replaced).")


if __name__ == "__main__":
    main()
