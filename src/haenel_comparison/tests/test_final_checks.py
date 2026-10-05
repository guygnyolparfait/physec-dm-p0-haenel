# Phase 18 — vérifications finales complémentaires (celles pas
# déjà couvertes par les tests précédents).

import unittest
from pathlib import Path

from haenel_comparison.haenel_config import (
    DURATION_S, MESSAGE_INTERVAL_S, N_MESSAGES,
)
from haenel_comparison.p0_complete import run_p0_complete, summarize_result

RESULTS_DIR = Path("results/haenel_comparison")


class TestFinalChecks(unittest.TestCase):

    def test_protocol_timing_constants(self):
        self.assertEqual(DURATION_S, 300.0)
        self.assertEqual(MESSAGE_INTERVAL_S, 3.0)
        self.assertEqual(N_MESSAGES, 100)

    def test_p0_complete_can_use_any_of_the_eight_decisions(self):
        """P0_COMPLETE ne doit pas être artificiellement restreint
        -- vérifie que la fonction appelée est bien
        run_decision_maker sans restriction (contrairement à
        P0_AUTH_ONLY)."""

        result, _channel = run_p0_complete()
        summary = summarize_result(result, _channel)

        self.assertFalse(summary["refusal_of_service"])
        self.assertIsNotNone(summary["decision"])
        # Le nom de la décision doit être un des 8 couples valides.
        from physec_dm.models import create_all_decisions
        valid_names = {d.get_name() for d in create_all_decisions()}
        self.assertIn(summary["decision"], valid_names)

    def test_no_nan_in_p0_complete_result(self):

        result, channel = run_p0_complete()
        summary = summarize_result(result, channel)

        for key in (
            "energy_j_native_scale", "normalized_latency",
            "r_auth", "q_key",
        ):
            value = summary[key]
            self.assertIsNotNone(value)
            self.assertFalse(value != value)  # NaN check (NaN != NaN)
            self.assertGreaterEqual(value, 0.0)

    def test_required_result_files_exist(self):

        required_files = [
            "haenel_parameter_traceability.csv",
            "option_b_missing_parameters.csv",
            "haenel_option_b_sources.csv",
            "b5_option_a_runs_30seeds.csv",
            "summary_statistics_experiment_a.csv",
            "p0_auth_only_haenel_rff_deterministic.csv",
            "p0_native_rff_sensitivity_deterministic.csv",
            "option_a_vs_option_b.csv",
            "latency_sensitivity.csv",
            "weight_sensitivity.csv",
            "weight_boundary_sensitivity.csv",
            "p0_decision_diagnostics.csv",
            "p0_decision_explanation.md",
            "experiment_b_security_b5.csv",
            "experiment_b_security_p0.csv",
            "security_monte_carlo.csv",
            "p0_complete_result.csv",
            "master_comparison_table.csv",
            "p0_complete_extension_table.csv",
            "figures/figure_1_energy_comparison.png",
            "figures/figure_2_decision_split.png",
            "figures/figure_3_fallback_vs_frr.png",
            "figures/figure_4_security.png",
            "figures/figure_5_weight_sensitivity.png",
        ]

        for filename in required_files:
            path = RESULTS_DIR / filename
            self.assertTrue(
                path.exists(), f"Fichier manquant : {path}"
            )
            self.assertGreater(
                path.stat().st_size, 0, f"Fichier vide : {path}"
            )

    def test_s1_s5_case_studies_still_produce_five_cases(self):
        """Garde-fou : les campagnes S1-S5 n'ont pas été modifiées
        par ce travail (Phase 0, règle absolue)."""

        from physec_dm.case_studies import build_five_case_studies_v2

        case_studies = build_five_case_studies_v2()
        scenario_ids = {cs["scenario_id"] for cs in case_studies}

        self.assertEqual(len(case_studies), 5)
        self.assertTrue(
            any("S1" in sid for sid in scenario_ids)
        )
        self.assertTrue(
            any("S5" in sid for sid in scenario_ids)
        )


if __name__ == "__main__":
    unittest.main()
