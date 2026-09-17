"""Focused Streamlit regressions for dashboard branch and control semantics."""

import unittest
from pathlib import Path

from numpy.testing import assert_allclose
from streamlit.testing.v1 import AppTest


class DashboardInteractionTests(unittest.TestCase):
    def setUp(self):
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        self.app = AppTest.from_file(str(app_path)).run(timeout=20)
        self.assertEqual(list(self.app.exception), [])

    def test_fork_switches_to_child_and_branch_controls_stay_independent(self):
        app = self.app
        app.number_input(key="advance_target_h").set_value(2.5)
        app.button(key="advance_exact_button").click().run(timeout=20)

        experiment = app.session_state["experiment"]
        parent_snapshot = experiment.active_branch.concentration.copy()
        self.assertEqual(experiment.active_branch.time_h, 2.5)

        app.text_input(key="new_branch_name").set_value("Move to A").run(timeout=20)
        app.button(key="create_branch_button").click().run(timeout=20)

        experiment = app.session_state["experiment"]
        self.assertEqual(experiment.active_branch_id, "branch-1")
        self.assertEqual(app.selectbox(key="active_branch_selector").value, "branch-1")
        self.assertEqual(experiment.active_branch.parent_id, "branch-0")
        self.assertEqual(experiment.active_branch.fork_time_h, 2.5)
        assert_allclose(experiment.active_branch.concentration, parent_snapshot, atol=0.0)

        # A widget selection is only a draft: it cannot change physics until applied.
        app.selectbox(key="cleaner_location_draft").select("A").run(timeout=20)
        self.assertEqual(app.session_state["experiment"].active_branch.cleaner_location, "C")
        app.button(key="apply_control_button").click().run(timeout=20)
        self.assertEqual(app.session_state["experiment"].active_branch.cleaner_location, "A")

        app.selectbox(key="active_branch_selector").select("branch-0").run(timeout=20)
        experiment = app.session_state["experiment"]
        self.assertEqual(experiment.active_branch_id, "branch-0")
        self.assertEqual(experiment.active_branch.time_h, 2.5)
        self.assertEqual(experiment.active_branch.cleaner_location, "C")
        self.assertEqual(app.selectbox(key="cleaner_location_draft").value, "C")
        self.assertEqual(len(experiment.active_branch.actions), 1)
        self.assertEqual(list(app.exception), [])

    def test_walkthrough_buttons_preserve_expected_outcomes(self):
        app = self.app
        app.number_input(key="advance_target_h").set_value(2.5)
        app.button(key="advance_exact_button").click().run(timeout=20)
        app.text_input(key="new_branch_name").set_value("Move to A").run(timeout=20)
        app.button(key="create_branch_button").click().run(timeout=20)
        app.selectbox(key="cleaner_location_draft").select("A").run(timeout=20)
        app.button(key="apply_control_button").click().run(timeout=20)
        app.button(key="finish_branch_button").click().run(timeout=20)

        app.selectbox(key="active_branch_selector").select("branch-0").run(timeout=20)
        app.button(key="finish_branch_button").click().run(timeout=20)
        experiment = app.session_state["experiment"]
        fixed = experiment.branch_summary("branch-0")
        moved = experiment.branch_summary("branch-1")

        self.assertAlmostEqual(float(fixed["J"]), 5.3927154554, places=9)
        assert_allclose(
            fixed["integrals"],
            [6.9573536052, 5.9383787319, 3.2824140291],
            rtol=0.0,
            atol=1e-10,
        )
        self.assertAlmostEqual(float(moved["J"]), 5.0700339391, places=9)
        assert_allclose(
            moved["integrals"],
            [5.5962274750, 5.7210923174, 3.8927820251],
            rtol=0.0,
            atol=1e-10,
        )
        self.assertEqual(fixed["clean_air_volume_m3"], 500.0)
        self.assertEqual(moved["clean_air_volume_m3"], 500.0)
        self.assertGreater(float(moved["integrals"][2]), float(fixed["integrals"][2]))
        self.assertEqual(list(app.exception), [])


if __name__ == "__main__":
    unittest.main()
