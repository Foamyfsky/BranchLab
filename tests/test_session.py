"""Behavioral checks for interactive particle-world sessions."""

import json
import unittest

import numpy as np
from numpy.testing import assert_allclose

from branchlab.experiment import (
    BACKGROUND_REMOVAL,
    CLEANER_CAPACITY,
    EXCHANGE,
    VOLUMES,
)
from branchlab.session import ExperimentSession
from branchlab.transport import simulate_piecewise


class ExperimentSessionTests(unittest.TestCase):
    def test_walkthrough_forks_are_continuous_and_independent(self):
        session = ExperimentSession([2.0, 2.0, 2.5], 5.0, "C", True)
        session.advance_to(2.5)
        session.pause()
        fork_concentration = session.active_branch.concentration.copy()
        fork_integrals = session.active_branch.integrals.copy()
        fork_budget = session.active_branch.clean_air_volume_m3

        moved_branch_id = session.fork("move to A")
        moved_branch = session.branches[moved_branch_id]
        self.assertEqual(moved_branch.parent_id, "branch-0")
        self.assertEqual(moved_branch.fork_time_h, 2.5)
        self.assertEqual(moved_branch.fork_action_count, 1)
        assert_allclose(moved_branch.concentration, fork_concentration, atol=0.0)
        assert_allclose(moved_branch.integrals, fork_integrals, atol=0.0)
        self.assertEqual(moved_branch.clean_air_volume_m3, fork_budget)

        session.run_to_end()
        fixed_summary = session.branch_summary("branch-0")
        self.assertAlmostEqual(float(fixed_summary["J"]), 5.39271546, delta=1e-8)
        self.assertAlmostEqual(
            float(fixed_summary["clean_air_volume_m3"]), 500.0, places=12
        )

        self.assertEqual(moved_branch.time_h, 2.5)
        assert_allclose(moved_branch.concentration, fork_concentration, atol=0.0)
        session.switch_branch(moved_branch_id)
        session.set_control(location="A", cleaner_on=True)
        session.run_to_end()
        moved_summary = session.branch_summary(moved_branch_id)
        self.assertAlmostEqual(float(moved_summary["J"]), 5.07003394, delta=1e-8)
        self.assertAlmostEqual(
            float(moved_summary["clean_air_volume_m3"]), 500.0, places=12
        )

        self.assertEqual(session.branches["branch-0"].cleaner_location, "C")
        self.assertEqual(len(session.branches["branch-0"].actions), 1)
        self.assertEqual(len(session.branches[moved_branch_id].actions), 2)

    def test_incremental_advancement_matches_direct_piecewise_propagation(self):
        initial = np.array([2.0, 2.0, 2.5])
        session = ExperimentSession(initial, 5.0, "C", True)
        session.advance_to(1.0)
        session.advance_to(2.5)
        session.set_control(location="A", cleaner_on=True)
        session.advance_to(3.1)
        session.advance_to(5.0)

        cleaner_c = np.array([0.0, 0.0, CLEANER_CAPACITY])
        cleaner_a = np.array([CLEANER_CAPACITY, 0.0, 0.0])
        expected_final, expected_integrals = simulate_piecewise(
            initial,
            VOLUMES,
            EXCHANGE,
            BACKGROUND_REMOVAL,
            [(2.5, cleaner_c), (2.5, cleaner_a)],
        )
        assert_allclose(
            session.active_branch.concentration,
            expected_final,
            rtol=0.0,
            atol=1e-12,
        )
        assert_allclose(
            session.active_branch.integrals,
            expected_integrals,
            rtol=0.0,
            atol=1e-12,
        )

    def test_pause_exact_timing_and_horizon_stopping(self):
        session = ExperimentSession([2.0, 2.0, 2.5], 1.0, "B", False)
        self.assertFalse(session.playback_tick(0.2))
        self.assertEqual(session.active_branch.time_h, 0.0)

        session.set_control(location="C", cleaner_on=True)
        self.assertEqual(session.active_branch.time_h, 0.0)
        session.play()
        self.assertTrue(session.playback_tick(0.2))
        self.assertAlmostEqual(session.active_branch.time_h, 0.2)
        session.pause()
        session.set_control(location="A", cleaner_on=True)
        self.assertFalse(session.playback_tick(0.2))
        self.assertAlmostEqual(session.active_branch.time_h, 0.2)

        session.advance_to(0.75)
        self.assertAlmostEqual(session.active_branch.actions[-1].time_h, 0.2)
        session.play()
        self.assertTrue(session.playback_tick(10.0))
        self.assertAlmostEqual(session.active_branch.time_h, 1.0)
        self.assertFalse(session.playing)
        self.assertFalse(session.playback_tick(0.2))
        with self.assertRaisesRegex(ValueError, "cannot exceed"):
            session.advance_to(1.01)

    def test_budget_on_off_zero_state_and_same_time_controls(self):
        zero_session = ExperimentSession([0.0, 0.0, 0.0], 5.0, "C", True)
        zero_session.advance_to(1.0)
        zero_session.set_control(cleaner_on=False)
        zero_session.run_to_end()
        assert_allclose(zero_session.active_branch.concentration, 0.0, atol=0.0)
        assert_allclose(zero_session.active_branch.integrals, 0.0, atol=0.0)
        self.assertAlmostEqual(
            zero_session.active_branch.clean_air_volume_m3, 100.0, places=12
        )
        reference = zero_session.no_cleaner_reference(5.0)
        self.assertEqual(reference["J"], 0.0)
        self.assertIsNone(
            zero_session.percentage_improvement(
                float(np.mean(zero_session.active_branch.integrals)),
                float(reference["J"]),
            )
        )

        repeated = ExperimentSession([2.0, 2.0, 2.5], 1.0, "A", True)
        repeated.set_control(location="B", cleaner_on=False)
        repeated.set_control(location="C", cleaner_on=True)
        repeated.run_to_end()
        direct = ExperimentSession([2.0, 2.0, 2.5], 1.0, "C", True)
        direct.run_to_end()
        assert_allclose(
            repeated.active_branch.concentration,
            direct.active_branch.concentration,
            rtol=0.0,
            atol=1e-12,
        )
        assert_allclose(
            repeated.active_branch.integrals,
            direct.active_branch.integrals,
            rtol=0.0,
            atol=1e-12,
        )
        self.assertEqual([action.sequence for action in repeated.active_branch.actions], [0, 1, 2])

    def test_json_export_import_replays_every_branch(self):
        session = ExperimentSession([2.0, 2.0, 2.5], 5.0, "C", True)
        session.advance_to(2.5)
        child_id = session.fork("move to A")
        session.run_to_end()
        session.switch_branch(child_id)
        session.set_control(location="A", cleaner_on=True)
        session.run_to_end()

        payload = session.to_json()
        restored = ExperimentSession.from_json(payload)
        self.assertEqual(restored.active_branch_id, child_id)
        self.assertFalse(restored.playing)
        self.assertEqual(set(restored.branches), set(session.branches))
        for branch_id in session.branches:
            original = session.branches[branch_id]
            replayed = restored.branches[branch_id]
            self.assertEqual(replayed.name, original.name)
            self.assertEqual(replayed.parent_id, original.parent_id)
            self.assertEqual(replayed.fork_time_h, original.fork_time_h)
            self.assertEqual(replayed.fork_action_count, original.fork_action_count)
            self.assertEqual(replayed.time_h, original.time_h)
            self.assertEqual(replayed.actions, original.actions)
            assert_allclose(replayed.concentration, original.concentration, atol=1e-12)
            assert_allclose(replayed.integrals, original.integrals, atol=1e-12)
            self.assertAlmostEqual(
                replayed.clean_air_volume_m3,
                original.clean_air_volume_m3,
                places=12,
            )

        corrupted = json.loads(payload)
        corrupted["branches"][0]["concentration_ug_m3"][0] += 0.01
        with self.assertRaisesRegex(ValueError, "does not match"):
            ExperimentSession.from_json(json.dumps(corrupted))

        broken_lineage = json.loads(payload)
        broken_lineage["branches"][1]["fork_action_count"] = 2
        with self.assertRaisesRegex(ValueError, "parent's action history"):
            ExperimentSession.from_json(json.dumps(broken_lineage))


if __name__ == "__main__":
    unittest.main()
