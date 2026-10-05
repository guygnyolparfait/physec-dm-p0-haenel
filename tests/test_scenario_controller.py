import unittest

from physec_dm.case_studies import build_five_case_studies

from physec_dm.scenario_controller import (
    ScenarioController,
    build_common_random_traces,
    resolve_active_phase,
    resolve_effective_speed_m_s,
    resolve_progress_fraction
)


class TestCommonRandomTraces(unittest.TestCase):

    # Test demandé : traces communes P0/B1 — même graine
    # doit produire exactement la même trace, indépendamment
    # de la politique évaluée (le contrôleur ne connaît même
    # pas la notion de politique).
    def test_same_seed_gives_identical_traces(self):

        traces_a = build_common_random_traces(
            seed=2000,
            max_steps=50
        )

        traces_b = build_common_random_traces(
            seed=2000,
            max_steps=50
        )

        self.assertEqual(
            list(
                traces_a["criticality_uniform"]
            ),
            list(
                traces_b["criticality_uniform"]
            )
        )

        self.assertEqual(
            list(traces_a["attack_uniform"]),
            list(traces_b["attack_uniform"])
        )

        self.assertEqual(
            list(traces_a["shadowing_normal"]),
            list(traces_b["shadowing_normal"])
        )

    def test_different_seeds_give_different_traces(
        self
    ):

        traces_a = build_common_random_traces(
            seed=2000,
            max_steps=50
        )

        traces_b = build_common_random_traces(
            seed=2001,
            max_steps=50
        )

        self.assertNotEqual(
            list(
                traces_a["criticality_uniform"]
            ),
            list(
                traces_b["criticality_uniform"]
            )
        )

    def test_invalid_max_steps_is_rejected(self):

        with self.assertRaises(ValueError):

            build_common_random_traces(
                seed=1,
                max_steps=0
            )


class TestPhaseResolution(unittest.TestCase):

    def setUp(self):

        self.case_studies = {
            case_study["scenario_id"]: case_study
            for case_study in (
                build_five_case_studies()
            )
        }

    def test_progress_fraction(self):

        self.assertAlmostEqual(
            resolve_progress_fraction(0, 100),
            0.0
        )

        self.assertAlmostEqual(
            resolve_progress_fraction(50, 100),
            0.5
        )

    # Test demandé : événements S2 aux bonnes périodes
    # (alarme entre 40 % et 50 %).
    def test_s2_alarm_phase_boundaries(self):

        s2 = self.case_studies[
            "S2-INDUSTRIAL-CRITICAL-ALARM"
        ]

        max_steps = 1000

        phase_at_39_percent = resolve_active_phase(
            s2, 390, max_steps
        )

        phase_at_45_percent = resolve_active_phase(
            s2, 450, max_steps
        )

        phase_at_55_percent = resolve_active_phase(
            s2, 550, max_steps
        )

        self.assertEqual(
            phase_at_39_percent["phase_name"],
            "Fonctionnement normal"
        )

        self.assertEqual(
            phase_at_45_percent[
                "criticality_forced"
            ],
            1
        )

        self.assertIsNone(
            phase_at_55_percent[
                "criticality_forced"
            ]
        )

    # Test demandé : événements S3 aux bonnes périodes
    # (cinq phases 20/20/20/20/20 %).
    def test_s3_phase_boundaries(self):

        s3 = self.case_studies["S3-MOBILE-VEHICLE"]

        max_steps = 1000

        expected_phase_names_by_step = {
            100: "Véhicule à l'arrêt (départ)",
            300: "Accélération",
            500: (
                "Déplacement à vitesse maximale du "
                "scénario (30.0 km/h)"
            ),
            700: "Ralentissement",
            900: "Véhicule à l'arrêt (arrivée)"
        }

        for step_index, expected_name in (
            expected_phase_names_by_step.items()
        ):

            phase = resolve_active_phase(
                s3, step_index, max_steps
            )

            self.assertEqual(
                phase["phase_name"],
                expected_name
            )

    # Test demandé : événements S4 aux bonnes périodes
    # (deux congestions, 25-40 % et 65-80 %).
    def test_s4_congestion_boundaries(self):

        s4 = self.case_studies[
            "S4-DENSE-URBAN-NETWORK"
        ]

        max_steps = 1000

        phase_before_first = resolve_active_phase(
            s4, 240, max_steps
        )

        phase_during_first = resolve_active_phase(
            s4, 300, max_steps
        )

        phase_between = resolve_active_phase(
            s4, 500, max_steps
        )

        phase_during_second = resolve_active_phase(
            s4, 700, max_steps
        )

        self.assertEqual(
            phase_before_first["shadowing_std_db"],
            4.0
        )

        self.assertEqual(
            phase_during_first["shadowing_std_db"],
            7.0
        )

        self.assertEqual(
            phase_between["shadowing_std_db"],
            4.0
        )

        self.assertEqual(
            phase_during_second["shadowing_std_db"],
            7.0
        )

    # Test demandé : événements S5 aux bonnes périodes
    # (attaque 30-60 %, compromission à 45 %).
    def test_s5_attack_and_compromise_boundaries(self):

        s5 = self.case_studies[
            "S5-CRITICAL-INFRASTRUCTURE-ATTACK"
        ]

        max_steps = 1000

        controller = ScenarioController(
            s5,
            seed=1,
            max_steps=max_steps
        )

        conditions_before = (
            controller.resolve_period_conditions(
                440
            )
        )

        conditions_after = (
            controller.resolve_period_conditions(
                450
            )
        )

        conditions_cleared = (
            controller.resolve_period_conditions(
                600
            )
        )

        self.assertFalse(
            conditions_before[
                "compromise_suspected"
            ]
        )

        self.assertTrue(
            conditions_after["compromise_suspected"]
        )

        self.assertFalse(
            conditions_cleared[
                "compromise_suspected"
            ]
        )

    def test_speed_ramp_interpolation(self):

        phase = {
            "start_fraction": 0.2,
            "end_fraction": 0.4,
            "effective_speed_m_s": (
                "ramp",
                0.0,
                10.0
            )
        }

        max_steps = 100

        speed_at_start = resolve_effective_speed_m_s(
            phase, 20, max_steps
        )

        speed_at_middle = resolve_effective_speed_m_s(
            phase, 30, max_steps
        )

        speed_at_end = resolve_effective_speed_m_s(
            phase, 40, max_steps
        )

        self.assertAlmostEqual(
            speed_at_start,
            0.0,
            places=6
        )

        self.assertAlmostEqual(
            speed_at_middle,
            5.0,
            places=6
        )

        self.assertAlmostEqual(
            speed_at_end,
            10.0,
            places=6
        )


class TestChannelNotBypassed(unittest.TestCase):

    # Le contrôleur ne doit produire QUE des ingrédients
    # (snr_db, speed_m_s) : jamais une corrélation, un
    # Doppler ou un KDR directement.
    def test_controller_output_has_no_channel_outputs(
        self
    ):

        case_studies = build_five_case_studies()

        controller = ScenarioController(
            case_studies[0],
            seed=1,
            max_steps=10
        )

        conditions = (
            controller.resolve_period_conditions(0)
        )

        forbidden_keys = [
            "rho_ab",
            "rho_time",
            "doppler_hz",
            "effective_kdr",
            "temporal_correlation"
        ]

        for forbidden_key in forbidden_keys:

            self.assertNotIn(
                forbidden_key,
                conditions
            )


if __name__ == "__main__":

    unittest.main()
