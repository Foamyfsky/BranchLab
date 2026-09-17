"""Interactive experiment state and deterministic replay for the particle world."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

from branchlab.experiment import (
    BACKGROUND_REMOVAL,
    CLEANER_CAPACITY,
    EXCHANGE,
    HORIZONS,
    ROOMS,
    VOLUMES,
)
from branchlab.transport import propagate_with_integral, system_matrix


FloatArray = NDArray[np.float64]
MODEL_ID = "branchlab.three-room-particle"
MODEL_VERSION = "1.0.0"
SCHEMA_VERSION = 1
TIME_TOLERANCE = 1e-12
STATE_TOLERANCE = 1e-10

MODEL_PARAMETERS: dict[str, object] = {
    "topology": "A-B-C",
    "rooms": list(ROOMS),
    "volumes": {"values": VOLUMES.tolist(), "unit": "m^3"},
    "exchange": {"values": EXCHANGE.tolist(), "unit": "m^3/hour"},
    "background_removal": {
        "values": BACKGROUND_REMOVAL.tolist(),
        "unit": "1/hour",
    },
    "cleaner_capacity": {"value": CLEANER_CAPACITY, "unit": "m^3/hour"},
    "source_after_initial_state": False,
    "relocation_time": {"value": 0.0, "unit": "hour"},
}
OBSERVATION_MODE: dict[str, str] = {
    "id": "full_state",
    "description": "All three room-average concentrations are known.",
}
OBJECTIVE: dict[str, str] = {
    "id": "integrated_mean_concentration",
    "definition": "J = (I_A + I_B + I_C) / 3",
    "unit": "micrograms*hour/m^3",
    "direction": "lower_is_better",
}


def _finite_float(value: object, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a finite number") from error
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number")
    return result


def _concentration_vector(values: ArrayLike, name: str) -> FloatArray:
    vector = np.asarray(values, dtype=float)
    if vector.shape != (len(ROOMS),):
        raise ValueError(f"{name} must contain one value for each of A, B, and C")
    if not np.all(np.isfinite(vector)) or np.any(vector < 0.0):
        raise ValueError(f"{name} must contain finite nonnegative values")
    return vector.copy()


def _validate_location(location: object) -> str:
    if location not in ROOMS:
        raise ValueError("cleaner location must be A, B, or C")
    return str(location)


@dataclass(frozen=True)
class ControlAction:
    """A complete cleaner control that takes effect at one simulation time."""

    sequence: int
    time_h: float
    location: str
    cleaner_on: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "time_h": self.time_h,
            "location": self.location,
            "cleaner_on": self.cleaner_on,
        }


@dataclass
class BranchState:
    """The accumulated deterministic state of one branch."""

    branch_id: str
    name: str
    parent_id: str | None
    fork_time_h: float
    fork_action_count: int
    time_h: float
    concentration: FloatArray
    integrals: FloatArray
    clean_air_volume_m3: float
    cleaner_location: str
    cleaner_on: bool
    actions: list[ControlAction]

    def is_complete(self, horizon_h: float) -> bool:
        return self.time_h >= horizon_h - TIME_TOLERANCE

    def to_dict(self, horizon_h: float) -> dict[str, object]:
        return {
            "branch_id": self.branch_id,
            "name": self.name,
            "parent_id": self.parent_id,
            "fork_time_h": self.fork_time_h,
            "fork_action_count": self.fork_action_count,
            "time_h": self.time_h,
            "status": "completed" if self.is_complete(horizon_h) else "partial",
            "current_control": {
                "location": self.cleaner_location,
                "cleaner_on": self.cleaner_on,
            },
            "concentration_ug_m3": self.concentration.tolist(),
            "integrated_concentration_ug_h_m3": self.integrals.tolist(),
            "clean_air_volume_m3": self.clean_air_volume_m3,
            "actions": [action.to_dict() for action in self.actions],
        }


class ExperimentSession:
    """Manage one fixed scenario and its deterministic intervention branches."""

    def __init__(
        self,
        initial_concentration: ArrayLike,
        horizon_h: float,
        cleaner_location: str = "C",
        cleaner_on: bool = True,
    ) -> None:
        self.initial_concentration = _concentration_vector(
            initial_concentration, "initial_concentration"
        )
        horizon = _finite_float(horizon_h, "horizon_h")
        if not any(
            math.isclose(horizon, allowed, abs_tol=TIME_TOLERANCE)
            for allowed in HORIZONS
        ):
            raise ValueError(f"horizon_h must be one of {HORIZONS}")
        self.horizon_h = horizon
        location = _validate_location(cleaner_location)
        if not isinstance(cleaner_on, bool):
            raise ValueError("cleaner_on must be a boolean")

        root_action = ControlAction(0, 0.0, location, cleaner_on)
        root = BranchState(
            branch_id="branch-0",
            name="main",
            parent_id=None,
            fork_time_h=0.0,
            fork_action_count=1,
            time_h=0.0,
            concentration=self.initial_concentration.copy(),
            integrals=np.zeros(len(ROOMS), dtype=float),
            clean_air_volume_m3=0.0,
            cleaner_location=location,
            cleaner_on=cleaner_on,
            actions=[root_action],
        )
        self.branches: dict[str, BranchState] = {root.branch_id: root}
        self.active_branch_id = root.branch_id
        self.playing = False
        self._next_branch_number = 1

    @property
    def active_branch(self) -> BranchState:
        return self.branches[self.active_branch_id]

    def switch_branch(self, branch_id: str) -> None:
        if branch_id not in self.branches:
            raise ValueError(f"unknown branch: {branch_id}")
        self.active_branch_id = branch_id
        self.playing = False

    def play(self) -> None:
        if not self.active_branch.is_complete(self.horizon_h):
            self.playing = True

    def pause(self) -> None:
        self.playing = False

    def playback_tick(self, maximum_step_h: float) -> bool:
        """Advance one bounded playback step only while playback is active."""

        step = _finite_float(maximum_step_h, "maximum_step_h")
        if step <= 0.0:
            raise ValueError("maximum_step_h must be positive")
        if not self.playing:
            return False
        branch = self.active_branch
        if branch.is_complete(self.horizon_h):
            self.playing = False
            return False
        self.advance_to(min(branch.time_h + step, self.horizon_h))
        if self.active_branch.is_complete(self.horizon_h):
            self.playing = False
        return True

    def set_control(
        self,
        *,
        location: str | None = None,
        cleaner_on: bool | None = None,
    ) -> ControlAction:
        """Record a control that affects evolution after the current time."""

        branch = self.active_branch
        if branch.is_complete(self.horizon_h):
            raise ValueError("controls cannot change after the horizon")
        new_location = (
            branch.cleaner_location if location is None else _validate_location(location)
        )
        new_cleaner_on = branch.cleaner_on if cleaner_on is None else cleaner_on
        if not isinstance(new_cleaner_on, bool):
            raise ValueError("cleaner_on must be a boolean")
        action = ControlAction(
            sequence=len(branch.actions),
            time_h=branch.time_h,
            location=new_location,
            cleaner_on=new_cleaner_on,
        )
        branch.actions.append(action)
        branch.cleaner_location = new_location
        branch.cleaner_on = new_cleaner_on
        return action

    def advance_to(self, target_time_h: float) -> None:
        """Advance exactly to a simulation timestamp using the active control."""

        target = _finite_float(target_time_h, "target_time_h")
        branch = self.active_branch
        if target < branch.time_h - TIME_TOLERANCE:
            raise ValueError("target_time_h cannot be earlier than the branch time")
        if target > self.horizon_h + TIME_TOLERANCE:
            raise ValueError("target_time_h cannot exceed the experiment horizon")
        target = min(max(target, branch.time_h), self.horizon_h)
        duration = target - branch.time_h
        if duration <= TIME_TOLERANCE:
            branch.time_h = target
            return

        clean_air = self._clean_air_vector(branch.cleaner_location, branch.cleaner_on)
        matrix = system_matrix(VOLUMES, EXCHANGE, BACKGROUND_REMOVAL, clean_air)
        final, integrated = propagate_with_integral(
            matrix, branch.concentration, duration
        )
        branch.concentration = final
        branch.integrals = branch.integrals + integrated
        if branch.cleaner_on:
            branch.clean_air_volume_m3 += CLEANER_CAPACITY * duration
        branch.time_h = target
        if branch.is_complete(self.horizon_h):
            self.playing = False

    def run_to_end(self) -> None:
        self.advance_to(self.horizon_h)

    def fork(self, name: str) -> str:
        """Create an independent branch from the current paused snapshot."""

        if self.playing:
            raise ValueError("pause playback before creating a fork")
        clean_name = str(name).strip()
        if not clean_name:
            raise ValueError("branch name must not be empty")
        if any(branch.name == clean_name for branch in self.branches.values()):
            raise ValueError("branch name must be unique")
        parent = self.active_branch
        while f"branch-{self._next_branch_number}" in self.branches:
            self._next_branch_number += 1
        branch_id = f"branch-{self._next_branch_number}"
        self._next_branch_number += 1
        child = BranchState(
            branch_id=branch_id,
            name=clean_name,
            parent_id=parent.branch_id,
            fork_time_h=parent.time_h,
            fork_action_count=len(parent.actions),
            time_h=parent.time_h,
            concentration=parent.concentration.copy(),
            integrals=parent.integrals.copy(),
            clean_air_volume_m3=parent.clean_air_volume_m3,
            cleaner_location=parent.cleaner_location,
            cleaner_on=parent.cleaner_on,
            actions=list(parent.actions),
        )
        self.branches[branch_id] = child
        return branch_id

    def branch_summary(self, branch_id: str | None = None) -> dict[str, object]:
        branch = self._branch(branch_id)
        return {
            "branch_id": branch.branch_id,
            "name": branch.name,
            "parent_id": branch.parent_id,
            "fork_time_h": branch.fork_time_h,
            "fork_action_count": branch.fork_action_count,
            "time_h": branch.time_h,
            "status": (
                "completed" if branch.is_complete(self.horizon_h) else "partial"
            ),
            "integrals": branch.integrals.copy(),
            "J": float(np.mean(branch.integrals)),
            "concentration": branch.concentration.copy(),
            "clean_air_volume_m3": branch.clean_air_volume_m3,
        }

    def completed_summaries(self) -> list[dict[str, object]]:
        return [
            self.branch_summary(branch_id)
            for branch_id, branch in self.branches.items()
            if branch.is_complete(self.horizon_h)
        ]

    def no_cleaner_reference(self, time_h: float | None = None) -> dict[str, object]:
        target = (
            self.active_branch.time_h
            if time_h is None
            else _finite_float(time_h, "time_h")
        )
        if target < -TIME_TOLERANCE or target > self.horizon_h + TIME_TOLERANCE:
            raise ValueError("reference time must be within the experiment horizon")
        target = min(max(target, 0.0), self.horizon_h)
        matrix = system_matrix(
            VOLUMES,
            EXCHANGE,
            BACKGROUND_REMOVAL,
            np.zeros(len(ROOMS), dtype=float),
        )
        final, integrated = propagate_with_integral(
            matrix, self.initial_concentration, target
        )
        return {
            "time_h": target,
            "concentration": final,
            "integrals": integrated,
            "J": float(np.mean(integrated)),
            "clean_air_volume_m3": 0.0,
        }

    def no_cleaner_history(
        self, time_h: float | None = None, points_per_hour: int = 50
    ) -> tuple[FloatArray, FloatArray]:
        """Return an exact sampled history for the matching no-cleaner branch."""

        target = self.active_branch.time_h if time_h is None else _finite_float(time_h, "time_h")
        if target < -TIME_TOLERANCE or target > self.horizon_h + TIME_TOLERANCE:
            raise ValueError("reference time must be within the experiment horizon")
        if points_per_hour < 1:
            raise ValueError("points_per_hour must be positive")
        target = min(max(target, 0.0), self.horizon_h)
        count = max(2, int(math.ceil(target * points_per_hour)) + 1)
        times = np.linspace(0.0, target, count) if target > 0.0 else np.array([0.0])
        history = np.empty((times.size, len(ROOMS)), dtype=float)
        history[0] = self.initial_concentration
        concentration = self.initial_concentration.copy()
        matrix = system_matrix(
            VOLUMES,
            EXCHANGE,
            BACKGROUND_REMOVAL,
            np.zeros(len(ROOMS), dtype=float),
        )
        for index in range(1, times.size):
            concentration, _ = propagate_with_integral(
                matrix, concentration, float(times[index] - times[index - 1])
            )
            history[index] = concentration
        return times, history

    @staticmethod
    def percentage_improvement(value: float, reference: float) -> float | None:
        if abs(reference) <= STATE_TOLERANCE:
            return None
        return 100.0 * (reference - value) / reference

    def rate_contributions(
        self, room: str, branch_id: str | None = None
    ) -> dict[str, float]:
        branch = self._branch(branch_id)
        location = _validate_location(room)
        room_index = ROOMS.index(location)
        concentration = branch.concentration
        net_exchange = float(
            np.sum(EXCHANGE[room_index] * (concentration - concentration[room_index]))
            / VOLUMES[room_index]
        )
        background_removal = float(
            -BACKGROUND_REMOVAL[room_index] * concentration[room_index]
        )
        cleaner_removal = 0.0
        if branch.cleaner_on and branch.cleaner_location == location:
            cleaner_removal = float(
                -CLEANER_CAPACITY / VOLUMES[room_index] * concentration[room_index]
            )
        return {
            "net_exchange": net_exchange,
            "background_removal": background_removal,
            "cleaner_removal": cleaner_removal,
            "total": net_exchange + background_removal + cleaner_removal,
        }

    def history(
        self, branch_id: str | None = None, points_per_hour: int = 50
    ) -> tuple[FloatArray, FloatArray]:
        """Return exact sampled histories for display, including every event time."""

        branch = self._branch(branch_id)
        if points_per_hour < 1:
            raise ValueError("points_per_hour must be positive")
        segments, _ = self._segments_for_actions(branch.actions, branch.time_h)
        times = [0.0]
        concentrations = [self.initial_concentration.copy()]
        current = self.initial_concentration.copy()
        current_time = 0.0
        for start, end, location, cleaner_on in segments:
            if not math.isclose(start, current_time, abs_tol=TIME_TOLERANCE):
                raise RuntimeError("action history contains a gap")
            count = max(2, int(math.ceil((end - start) * points_per_hour)) + 1)
            targets = np.linspace(start, end, count)[1:]
            matrix = system_matrix(
                VOLUMES,
                EXCHANGE,
                BACKGROUND_REMOVAL,
                self._clean_air_vector(location, cleaner_on),
            )
            for target in targets:
                current, _ = propagate_with_integral(
                    matrix, current, float(target - current_time)
                )
                current_time = float(target)
                times.append(current_time)
                concentrations.append(current.copy())
        return np.asarray(times, dtype=float), np.asarray(concentrations, dtype=float)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "model": {"id": MODEL_ID, "version": MODEL_VERSION},
            "parameters": MODEL_PARAMETERS,
            "initial_conditions": {
                "concentration": self.initial_concentration.tolist(),
                "unit": "micrograms/m^3",
            },
            "horizon": {"value": self.horizon_h, "unit": "hour"},
            "observation_mode": OBSERVATION_MODE,
            "objective": OBJECTIVE,
            "active_branch_id": self.active_branch_id,
            "branches": [
                branch.to_dict(self.horizon_h) for branch in self.branches.values()
            ],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @classmethod
    def from_json(cls, payload: str | bytes) -> ExperimentSession:
        """Validate, replay, and load one versioned experiment document."""

        try:
            data = json.loads(payload)
        except (TypeError, json.JSONDecodeError) as error:
            raise ValueError("experiment JSON is not valid") from error
        if not isinstance(data, dict):
            raise ValueError("experiment JSON must contain an object")
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        if data.get("model") != {"id": MODEL_ID, "version": MODEL_VERSION}:
            raise ValueError("model identity or version is not supported")
        if data.get("parameters") != MODEL_PARAMETERS:
            raise ValueError("imported model parameters do not match this model")
        if data.get("observation_mode") != OBSERVATION_MODE:
            raise ValueError("observation mode is not supported")
        if data.get("objective") != OBJECTIVE:
            raise ValueError("objective definition is not supported")

        initial_data = data.get("initial_conditions")
        horizon_data = data.get("horizon")
        if not isinstance(initial_data, dict) or initial_data.get("unit") != "micrograms/m^3":
            raise ValueError("initial conditions or units are invalid")
        if not isinstance(horizon_data, dict) or horizon_data.get("unit") != "hour":
            raise ValueError("horizon or units are invalid")
        initial = _concentration_vector(
            initial_data.get("concentration"), "initial concentration"
        )
        horizon = _finite_float(horizon_data.get("value"), "horizon")
        session = cls(initial, horizon, cleaner_location="A", cleaner_on=False)
        session.branches = {}

        branches_data = data.get("branches")
        if not isinstance(branches_data, list) or not branches_data:
            raise ValueError("branches must be a nonempty list")
        for branch_data in branches_data:
            branch = session._load_branch(branch_data)
            if branch.branch_id in session.branches:
                raise ValueError("branch identifiers must be unique")
            if any(existing.name == branch.name for existing in session.branches.values()):
                raise ValueError("branch names must be unique")
            session.branches[branch.branch_id] = branch

        session._validate_lineage()

        active_branch_id = data.get("active_branch_id")
        if active_branch_id not in session.branches:
            raise ValueError("active_branch_id does not identify an imported branch")
        session.active_branch_id = str(active_branch_id)
        session.playing = False
        session._next_branch_number = 1
        while f"branch-{session._next_branch_number}" in session.branches:
            session._next_branch_number += 1
        return session

    def _validate_lineage(self) -> None:
        roots = [branch for branch in self.branches.values() if branch.parent_id is None]
        if len(roots) != 1:
            raise ValueError("an experiment must contain exactly one root branch")
        root = roots[0]
        if not math.isclose(root.fork_time_h, 0.0, abs_tol=TIME_TOLERANCE):
            raise ValueError("the root branch fork time must be zero")
        if root.fork_action_count != 1:
            raise ValueError("the root branch fork_action_count must be one")

        for branch in self.branches.values():
            seen: set[str] = set()
            cursor = branch
            while cursor.parent_id is not None:
                if cursor.branch_id in seen:
                    raise ValueError("branch lineage contains a cycle")
                seen.add(cursor.branch_id)
                if cursor.parent_id not in self.branches:
                    raise ValueError("branch parent does not exist")
                cursor = self.branches[cursor.parent_id]
            if cursor.branch_id != root.branch_id:
                raise ValueError("branch lineage does not reach the root")

            if branch.parent_id is None:
                continue
            parent = self.branches[branch.parent_id]
            if branch.fork_time_h < parent.fork_time_h - TIME_TOLERANCE:
                raise ValueError("branch fork time precedes its parent")
            if branch.fork_time_h > branch.time_h + TIME_TOLERANCE:
                raise ValueError("branch fork time exceeds branch time")
            if branch.fork_time_h > parent.time_h + TIME_TOLERANCE:
                raise ValueError("branch fork time exceeds parent time")

            copied = branch.fork_action_count
            if copied > len(parent.actions):
                raise ValueError("fork_action_count exceeds the parent's action history")
            if branch.actions[:copied] != parent.actions[:copied]:
                raise ValueError("forked branch does not preserve its parent's action history")
            if any(
                action.time_h > branch.fork_time_h + TIME_TOLERANCE
                for action in branch.actions[:copied]
            ):
                raise ValueError("copied actions cannot occur after the fork time")
            if any(
                action.time_h < branch.fork_time_h - TIME_TOLERANCE
                for action in branch.actions[copied:]
            ):
                raise ValueError("child actions after the copied prefix precede the fork")
            if any(
                action.time_h < branch.fork_time_h - TIME_TOLERANCE
                for action in parent.actions[copied:]
            ):
                raise ValueError("parent actions after the copied prefix precede the fork")

            parent_at_fork = [
                action
                for action in parent.actions
                if action.time_h <= branch.fork_time_h + TIME_TOLERANCE
            ]
            child_at_fork = [
                action
                for action in branch.actions
                if action.time_h <= branch.fork_time_h + TIME_TOLERANCE
            ]
            parent_state = self._replay(parent_at_fork, branch.fork_time_h)
            child_state = self._replay(child_at_fork, branch.fork_time_h)
            for parent_value, child_value in zip(parent_state[:2], child_state[:2]):
                if not np.allclose(
                    parent_value, child_value, rtol=0.0, atol=STATE_TOLERANCE
                ):
                    raise ValueError("forked branch state is not continuous with its parent")
            if not math.isclose(
                parent_state[2],
                child_state[2],
                rel_tol=0.0,
                abs_tol=STATE_TOLERANCE,
            ):
                raise ValueError("forked branch budget is not continuous with its parent")

    def _load_branch(self, data: object) -> BranchState:
        if not isinstance(data, dict):
            raise ValueError("each branch must be an object")
        branch_id = data.get("branch_id")
        name = data.get("name")
        parent_id = data.get("parent_id")
        if not isinstance(branch_id, str) or not branch_id:
            raise ValueError("branch_id must be a nonempty string")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("branch name must be a nonempty string")
        if parent_id is not None and not isinstance(parent_id, str):
            raise ValueError("parent_id must be a string or null")
        fork_time = _finite_float(data.get("fork_time_h"), "fork_time_h")
        fork_action_count = data.get("fork_action_count")
        if (
            isinstance(fork_action_count, bool)
            or not isinstance(fork_action_count, int)
            or fork_action_count < 1
        ):
            raise ValueError("fork_action_count must be a positive integer")
        time_h = _finite_float(data.get("time_h"), "branch time_h")
        if fork_time < -TIME_TOLERANCE or time_h < -TIME_TOLERANCE:
            raise ValueError("branch times must be nonnegative")
        if time_h > self.horizon_h + TIME_TOLERANCE:
            raise ValueError("branch time exceeds the horizon")

        actions_data = data.get("actions")
        if not isinstance(actions_data, list) or not actions_data:
            raise ValueError("each branch must contain control actions")
        actions: list[ControlAction] = []
        previous_time = -math.inf
        for expected_sequence, action_data in enumerate(actions_data):
            if not isinstance(action_data, dict):
                raise ValueError("each control action must be an object")
            sequence = action_data.get("sequence")
            action_time = _finite_float(action_data.get("time_h"), "action time_h")
            location = _validate_location(action_data.get("location"))
            cleaner_on = action_data.get("cleaner_on")
            if sequence != expected_sequence:
                raise ValueError("action sequences must be contiguous and ordered")
            if action_time < previous_time - TIME_TOLERANCE:
                raise ValueError("action timestamps must be nondecreasing")
            if action_time > time_h + TIME_TOLERANCE:
                raise ValueError("action timestamp exceeds branch time")
            if not isinstance(cleaner_on, bool):
                raise ValueError("action cleaner_on must be a boolean")
            actions.append(
                ControlAction(expected_sequence, action_time, location, cleaner_on)
            )
            previous_time = action_time
        if not math.isclose(actions[0].time_h, 0.0, abs_tol=TIME_TOLERANCE):
            raise ValueError("the first action must start at time zero")
        if fork_action_count > len(actions):
            raise ValueError("fork_action_count exceeds the branch action history")

        stored_concentration = _concentration_vector(
            data.get("concentration_ug_m3"), "stored concentration"
        )
        stored_integrals = _concentration_vector(
            data.get("integrated_concentration_ug_h_m3"), "stored integrals"
        )
        stored_budget = _finite_float(
            data.get("clean_air_volume_m3"), "stored clean-air volume"
        )
        if stored_budget < -STATE_TOLERANCE:
            raise ValueError("stored clean-air volume must be nonnegative")
        control_data = data.get("current_control")
        if not isinstance(control_data, dict):
            raise ValueError("current_control must be an object")
        control_location = _validate_location(control_data.get("location"))
        control_on = control_data.get("cleaner_on")
        if not isinstance(control_on, bool):
            raise ValueError("current cleaner_on must be a boolean")

        replay_concentration, replay_integrals, replay_budget, replay_control = (
            self._replay(actions, time_h)
        )
        if not np.allclose(
            stored_concentration, replay_concentration, rtol=0.0, atol=STATE_TOLERANCE
        ):
            raise ValueError("stored concentration does not match deterministic replay")
        if not np.allclose(
            stored_integrals, replay_integrals, rtol=0.0, atol=STATE_TOLERANCE
        ):
            raise ValueError("stored integrals do not match deterministic replay")
        if not math.isclose(
            stored_budget, replay_budget, rel_tol=0.0, abs_tol=STATE_TOLERANCE
        ):
            raise ValueError("stored clean-air volume does not match deterministic replay")
        if replay_control != (control_location, control_on):
            raise ValueError("current control does not match the action history")

        return BranchState(
            branch_id=branch_id,
            name=name.strip(),
            parent_id=parent_id,
            fork_time_h=fork_time,
            fork_action_count=fork_action_count,
            time_h=min(max(time_h, 0.0), self.horizon_h),
            concentration=replay_concentration,
            integrals=replay_integrals,
            clean_air_volume_m3=replay_budget,
            cleaner_location=replay_control[0],
            cleaner_on=replay_control[1],
            actions=actions,
        )

    def _replay(
        self, actions: list[ControlAction], end_time_h: float
    ) -> tuple[FloatArray, FloatArray, float, tuple[str, bool]]:
        segments, final_control = self._segments_for_actions(actions, end_time_h)
        concentration = self.initial_concentration.copy()
        integrals = np.zeros(len(ROOMS), dtype=float)
        budget = 0.0
        for start, end, location, cleaner_on in segments:
            clean_air = self._clean_air_vector(location, cleaner_on)
            matrix = system_matrix(VOLUMES, EXCHANGE, BACKGROUND_REMOVAL, clean_air)
            concentration, integrated = propagate_with_integral(
                matrix, concentration, end - start
            )
            integrals += integrated
            if cleaner_on:
                budget += CLEANER_CAPACITY * (end - start)
        return concentration, integrals, budget, final_control

    @staticmethod
    def _segments_for_actions(
        actions: list[ControlAction], end_time_h: float
    ) -> tuple[list[tuple[float, float, str, bool]], tuple[str, bool]]:
        if not actions:
            raise ValueError("at least one control action is required")
        current_time = 0.0
        location = actions[0].location
        cleaner_on = actions[0].cleaner_on
        segments: list[tuple[float, float, str, bool]] = []
        for action in actions[1:]:
            if action.time_h > current_time + TIME_TOLERANCE:
                segments.append(
                    (current_time, action.time_h, location, cleaner_on)
                )
                current_time = action.time_h
            location = action.location
            cleaner_on = action.cleaner_on
        if end_time_h > current_time + TIME_TOLERANCE:
            segments.append((current_time, end_time_h, location, cleaner_on))
        return segments, (location, cleaner_on)

    @staticmethod
    def _clean_air_vector(location: str, cleaner_on: bool) -> FloatArray:
        clean_air = np.zeros(len(ROOMS), dtype=float)
        if cleaner_on:
            clean_air[ROOMS.index(location)] = CLEANER_CAPACITY
        return clean_air

    def _branch(self, branch_id: str | None) -> BranchState:
        selected = self.active_branch_id if branch_id is None else branch_id
        if selected not in self.branches:
            raise ValueError(f"unknown branch: {selected}")
        return self.branches[selected]
