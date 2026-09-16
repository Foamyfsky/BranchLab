"""Deterministic well-mixed multizone particle transport.

Concentrations use micrograms/m^3 and time uses hours. Volumes, exchange
flows, and equivalent clean-air delivery rates therefore use m^3, m^3/hour,
and m^3/hour, respectively.
"""

from collections.abc import Iterable, Sequence

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.linalg import expm


FloatArray = NDArray[np.float64]
Segment = tuple[float, ArrayLike]


def _as_vector(values: ArrayLike, name: str, *, positive: bool = False) -> FloatArray:
    vector = np.asarray(values, dtype=float)
    if vector.ndim != 1 or vector.size == 0:
        raise ValueError(f"{name} must be a nonempty one-dimensional array")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} must contain only finite values")
    if positive and np.any(vector <= 0.0):
        raise ValueError(f"{name} must be strictly positive")
    if not positive and np.any(vector < 0.0):
        raise ValueError(f"{name} must be nonnegative")
    return vector.copy()


def system_matrix(
    volumes: ArrayLike,
    exchange: ArrayLike,
    background_removal: ArrayLike,
    clean_air_delivery: ArrayLike | None = None,
) -> FloatArray:
    """Return the concentration generator for one constant operating period.

    ``exchange[i, j]`` is the symmetric exchange flow between rooms ``i`` and
    ``j``. Diagonal entries are ignored because self-exchange has no effect.
    """

    volume = _as_vector(volumes, "volumes", positive=True)
    removal = _as_vector(background_removal, "background_removal")
    room_count = volume.size
    if removal.shape != (room_count,):
        raise ValueError("background_removal must have one value per room")

    flow = np.asarray(exchange, dtype=float)
    if flow.shape != (room_count, room_count):
        raise ValueError("exchange must be a square matrix with one row per room")
    if not np.all(np.isfinite(flow)) or np.any(flow < 0.0):
        raise ValueError("exchange must contain finite nonnegative values")
    if not np.allclose(flow, flow.T, rtol=0.0, atol=1e-12):
        raise ValueError("exchange must be symmetric")

    if clean_air_delivery is None:
        clean_air = np.zeros(room_count, dtype=float)
    else:
        clean_air = _as_vector(clean_air_delivery, "clean_air_delivery")
        if clean_air.shape != (room_count,):
            raise ValueError("clean_air_delivery must have one value per room")

    off_diagonal_flow = flow.copy()
    np.fill_diagonal(off_diagonal_flow, 0.0)
    matrix = off_diagonal_flow / volume[:, np.newaxis]
    diagonal = -(off_diagonal_flow.sum(axis=1) / volume + removal + clean_air / volume)
    np.fill_diagonal(matrix, diagonal)
    return matrix


def propagate_with_integral(
    matrix: ArrayLike, initial_concentration: ArrayLike, duration: float
) -> tuple[FloatArray, FloatArray]:
    """Propagate concentration and its exact time integral over ``duration``.

    The cumulative concentrations are states in an augmented linear system,
    so the integral is independent of any plotting or sampling resolution.
    """

    generator = np.asarray(matrix, dtype=float)
    initial = _as_vector(initial_concentration, "initial_concentration")
    room_count = initial.size
    if generator.shape != (room_count, room_count):
        raise ValueError("matrix must be square and match initial_concentration")
    if not np.all(np.isfinite(generator)):
        raise ValueError("matrix must contain only finite values")
    if not np.isfinite(duration) or duration < 0.0:
        raise ValueError("duration must be finite and nonnegative")

    augmented = np.zeros((2 * room_count, 2 * room_count), dtype=float)
    augmented[:room_count, :room_count] = generator
    augmented[room_count:, :room_count] = np.eye(room_count)
    state = np.concatenate((initial, np.zeros(room_count, dtype=float)))
    propagated = expm(augmented * duration) @ state
    return propagated[:room_count].copy(), propagated[room_count:].copy()


def simulate_piecewise(
    initial_concentration: ArrayLike,
    volumes: ArrayLike,
    exchange: ArrayLike,
    background_removal: ArrayLike,
    segments: Iterable[Segment],
) -> tuple[FloatArray, FloatArray]:
    """Branch from ``initial_concentration`` through constant-control segments."""

    concentration = _as_vector(initial_concentration, "initial_concentration")
    cumulative = np.zeros_like(concentration)
    used_segment = False
    for duration, clean_air_delivery in segments:
        used_segment = True
        matrix = system_matrix(
            volumes, exchange, background_removal, clean_air_delivery
        )
        concentration, integrated = propagate_with_integral(
            matrix, concentration, duration
        )
        cumulative += integrated
    if not used_segment:
        raise ValueError("segments must contain at least one operating period")
    return concentration, cumulative


def concentration_history(
    initial_concentration: ArrayLike,
    volumes: ArrayLike,
    exchange: ArrayLike,
    background_removal: ArrayLike,
    segments: Sequence[Segment],
    sample_times: ArrayLike,
) -> FloatArray:
    """Evaluate the exact piecewise solution at sorted plotting times."""

    initial = _as_vector(initial_concentration, "initial_concentration")
    if not segments:
        raise ValueError("segments must contain at least one operating period")

    durations = np.asarray([segment[0] for segment in segments], dtype=float)
    if not np.all(np.isfinite(durations)) or np.any(durations < 0.0):
        raise ValueError("segment durations must be finite and nonnegative")
    times = np.asarray(sample_times, dtype=float)
    total_duration = float(durations.sum())
    if times.ndim != 1 or not np.all(np.isfinite(times)):
        raise ValueError("sample_times must be a finite one-dimensional array")
    if np.any(np.diff(times) < 0.0):
        raise ValueError("sample_times must be sorted")
    if np.any(times < -1e-12) or np.any(times > total_duration + 1e-12):
        raise ValueError("sample_times must lie within the schedule horizon")

    matrices = [
        system_matrix(volumes, exchange, background_removal, clean_air)
        for _, clean_air in segments
    ]
    boundaries = np.cumsum(durations)
    history = np.empty((times.size, initial.size), dtype=float)
    concentration = initial.copy()
    current_time = 0.0
    segment_index = 0

    for sample_index, target_time in enumerate(times):
        target = min(max(float(target_time), 0.0), total_duration)
        while (
            segment_index < len(segments) - 1
            and target > boundaries[segment_index] + 1e-12
        ):
            step = float(boundaries[segment_index] - current_time)
            concentration, _ = propagate_with_integral(
                matrices[segment_index], concentration, step
            )
            current_time = float(boundaries[segment_index])
            segment_index += 1
        step = target - current_time
        concentration, _ = propagate_with_integral(
            matrices[segment_index], concentration, step
        )
        current_time = target
        history[sample_index] = concentration

    return history


def clean_air_budget(segments: Iterable[Segment]) -> float:
    """Return total equivalent clean-air volume, in m^3, for a schedule."""

    budget = 0.0
    for duration, clean_air_delivery in segments:
        clean_air = _as_vector(clean_air_delivery, "clean_air_delivery")
        if not np.isfinite(duration) or duration < 0.0:
            raise ValueError("segment durations must be finite and nonnegative")
        budget += float(duration) * float(clean_air.sum())
    return budget
