"""Focused checks for the deterministic multizone transport reference."""

import unittest
from itertools import product

import numpy as np
from numpy.testing import assert_allclose

from branchlab.experiment import (
    BACKGROUND_REMOVAL,
    CLEANER_CAPACITY,
    EXCHANGE,
    ROOMS,
    VOLUMES,
    schedule_segments,
)
from branchlab.transport import (
    clean_air_budget,
    concentration_history,
    propagate_with_integral,
    simulate_piecewise,
    system_matrix,
)


class TransportTests(unittest.TestCase):
    def simulate(self, initial, horizon, schedule):
        return simulate_piecewise(
            initial,
            VOLUMES,
            EXCHANGE,
            BACKGROUND_REMOVAL,
            schedule_segments(schedule, horizon),
        )

    def test_exchange_only_conserves_particle_mass(self):
        volumes = np.array([80.0, 100.0, 140.0])
        exchange = np.array(
            [[0.0, 30.0, 0.0], [30.0, 0.0, 45.0], [0.0, 45.0, 0.0]]
        )
        initial = np.array([1.0, 4.0, 0.5])
        matrix = system_matrix(volumes, exchange, np.zeros(3))
        final, _ = propagate_with_integral(matrix, initial, 7.0)
        self.assertAlmostEqual(
            float(volumes @ final), float(volumes @ initial), places=11
        )

    def test_isolated_room_matches_analytic_exponential_decay(self):
        initial = np.array([3.0])
        rate = 0.1 + 100.0 / 100.0
        duration = 2.3
        matrix = system_matrix([100.0], [[0.0]], [0.1], [100.0])
        final, integrated = propagate_with_integral(matrix, initial, duration)
        expected_final = initial * np.exp(-rate * duration)
        expected_integral = initial * (1.0 - np.exp(-rate * duration)) / rate
        assert_allclose(final, expected_final, rtol=0.0, atol=1e-12)
        assert_allclose(integrated, expected_integral, rtol=0.0, atol=1e-12)

    def test_active_schedules_have_equal_clean_air_budgets(self):
        for horizon in (1.0, 5.0):
            budgets = [
                clean_air_budget(schedule_segments(schedule, horizon))
                for schedule in product(ROOMS, repeat=2)
            ]
            assert_allclose(budgets, CLEANER_CAPACITY * horizon, atol=0.0)

    def test_branches_do_not_mutate_or_depend_on_shared_inputs(self):
        initial = np.array([2.0, 2.0, 2.5])
        original = initial.copy()
        expected_final, expected_integral = self.simulate(initial, 5.0, ("B", "C"))
        other_final, other_integral = self.simulate(initial, 5.0, ("A", "A"))
        actual_final, actual_integral = self.simulate(initial, 5.0, ("B", "C"))
        assert_allclose(initial, original, rtol=0.0, atol=0.0)
        assert_allclose(actual_final, expected_final, rtol=0.0, atol=0.0)
        assert_allclose(actual_integral, expected_integral, rtol=0.0, atol=0.0)
        other_final[0] = -999.0
        other_integral[0] = -999.0
        assert_allclose(initial, original, rtol=0.0, atol=0.0)

    def test_concentrations_remain_nonnegative(self):
        initial_states = (
            np.array([2.0, 2.0, 2.5]),
            np.array([2.5, 2.0, 2.0]),
        )
        for initial in initial_states:
            for horizon in (1.0, 5.0):
                for schedule in [(None, None), *product(ROOMS, repeat=2)]:
                    history = concentration_history(
                        initial,
                        VOLUMES,
                        EXCHANGE,
                        BACKGROUND_REMOVAL,
                        schedule_segments(schedule, horizon),
                        np.linspace(0.0, horizon, 51),
                    )
                    self.assertGreaterEqual(float(history.min()), -1e-12)

    def test_mirroring_initial_state_and_rooms_preserves_outcomes(self):
        left_initial = np.array([2.0, 2.0, 2.5])
        right_initial = left_initial[::-1]
        mirror = {"A": "C", "B": "B", "C": "A", None: None}
        for horizon in (1.0, 5.0):
            for schedule in [(None, None), *product(ROOMS, repeat=2)]:
                mirrored_schedule = (mirror[schedule[0]], mirror[schedule[1]])
                left_final, left_integrated = self.simulate(
                    left_initial, horizon, schedule
                )
                right_final, right_integrated = self.simulate(
                    right_initial, horizon, mirrored_schedule
                )
                assert_allclose(left_final, right_final[::-1], rtol=0.0, atol=1e-12)
                assert_allclose(
                    left_integrated, right_integrated[::-1], rtol=0.0, atol=1e-12
                )
                self.assertAlmostEqual(
                    float(np.mean(left_integrated)),
                    float(np.mean(right_integrated)),
                    places=12,
                )

    def test_supplied_fixed_placement_reference_losses(self):
        initial = np.array([2.0, 2.0, 2.5])
        references = {
            1.0: {
                (None, None): 2.06185594,
                ("A", "A"): 1.82348265,
                ("B", "B"): 1.81072381,
                ("C", "C"): 1.77332755,
            },
            5.0: {
                (None, None): 8.52516904,
                ("A", "A"): 5.71877629,
                ("B", "B"): 5.21845964,
                ("C", "C"): 5.39271546,
            },
        }
        for horizon, schedules in references.items():
            for schedule, expected in schedules.items():
                _, integrated = self.simulate(initial, horizon, schedule)
                self.assertAlmostEqual(float(np.mean(integrated)), expected, delta=1e-5)


if __name__ == "__main__":
    unittest.main()
