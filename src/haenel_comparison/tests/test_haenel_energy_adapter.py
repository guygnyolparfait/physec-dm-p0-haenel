import unittest

from haenel_comparison.haenel_energy_adapter import (
    E_FALLBACK_EXTRA_MJ,
    E_MAC_PER_MESSAGE_MJ,
    E_RFF_BASE_PER_MESSAGE_MJ,
    LATENCY_STATUS,
    NEUTRAL_LATENCY_VALUE,
    a1_energy_mJ,
    a2_expected_energy_mJ,
    a2_realized_energy_mJ,
)
from haenel_comparison.p0_auth_only_haenel_scale import (
    evaluate_candidates_haenel_scale,
    select_p0_auth_only_haenel_scale,
    simulate_p0_auth_only_haenel_scale,
    summarize_p0_haenel_scale_events,
)
from haenel_comparison.p0_auth_only import (
    build_haenel_p0_parameters,
    build_haenel_static_context,
)


class TestHaenelEnergyAdapter(unittest.TestCase):

    def test_per_message_constants_match_published_over_n_messages(self):
        self.assertAlmostEqual(E_MAC_PER_MESSAGE_MJ * 100, 564.743)
        self.assertAlmostEqual(E_RFF_BASE_PER_MESSAGE_MJ * 100, 355.412)

    def test_a1_energy_is_deterministic(self):
        self.assertEqual(a1_energy_mJ(), E_MAC_PER_MESSAGE_MJ)

    def test_a2_expected_energy_matches_option_a_aggregate(self):
        """L'espérance par message * 100, pour FRR=5% et FRR=10%,
        doit retomber sur les mêmes totaux qu'Option A (passe
        précédente), à l'arrondi flottant près."""

        for frr, published_total in (
            (0.05, 404.790),
            (0.10, 454.076),
        ):
            expected_per_message = a2_expected_energy_mJ(frr)
            self.assertAlmostEqual(
                expected_per_message * 100, published_total, places=1
            )

    def test_a2_expected_energy_requires_frr(self):
        with self.assertRaises(ValueError):
            a2_expected_energy_mJ(None)

    def test_a2_realized_energy_bounds(self):
        no_fallback = a2_realized_energy_mJ(rff_rejected=False)
        with_fallback = a2_realized_energy_mJ(rff_rejected=True)

        self.assertEqual(no_fallback, E_RFF_BASE_PER_MESSAGE_MJ)
        self.assertEqual(
            with_fallback,
            E_RFF_BASE_PER_MESSAGE_MJ + E_FALLBACK_EXTRA_MJ,
        )
        self.assertLess(no_fallback, with_fallback)

    def test_latency_is_neutralized_and_documented(self):
        self.assertEqual(NEUTRAL_LATENCY_VALUE, 0.0)
        self.assertIn("UNAVAILABLE", LATENCY_STATUS)

    def test_both_candidates_get_identical_neutral_latency(self):

        parameters = build_haenel_p0_parameters()
        context, channel_metrics = build_haenel_static_context(
            parameters
        )

        evaluations = evaluate_candidates_haenel_scale(
            context, parameters, channel_metrics.rho_ab, frr=0.05
        )

        for evaluation in evaluations:
            self.assertEqual(
                evaluation.cost_metrics.normalized_latency,
                NEUTRAL_LATENCY_VALUE,
            )

    def test_rauth_and_qkey_untouched_by_adapter(self):
        """Rauth et Qkey doivent rester ceux du vrai modèle
        physec_dm (pas de valeur neutralisée ou recalibrée)."""

        parameters = build_haenel_p0_parameters()
        context, channel_metrics = build_haenel_static_context(
            parameters
        )

        evaluations = evaluate_candidates_haenel_scale(
            context, parameters, channel_metrics.rho_ab, frr=0.05
        )

        a1_eval, a2_eval = evaluations

        # A1 (MAC) doit garder sa robustesse quasi parfaite native.
        self.assertGreater(
            a1_eval.authentication_metrics.authentication_robustness,
            0.999999,
        )
        # A2 (RFF) doit garder un FAR non nul natif (calculé par
        # authentication.py, pas fabriqué ici).
        self.assertGreater(a2_eval.authentication_metrics.far, 0.0)

    def test_energy_values_on_haenel_scale_not_lora_scale(self):
        """L'énergie exposée doit être de l'ordre du mJ Haenel
        (quelques mJ), pas de l'ordre du modèle LoRa natif
        (~200 mJ, voir p0_auth_only.py, échelle différente)."""

        parameters = build_haenel_p0_parameters()
        context, channel_metrics = build_haenel_static_context(
            parameters
        )

        evaluations = evaluate_candidates_haenel_scale(
            context, parameters, channel_metrics.rho_ab, frr=0.05
        )

        for evaluation in evaluations:
            energy = evaluation.cost_metrics.expected_energy_j
            self.assertGreater(energy, 1.0)
            self.assertLess(energy, 20.0)

    def test_p0_decision_persists_across_frr_cases(self):
        """Le résultat (A1 systématiquement retenu) ne doit pas
        dépendre arbitrairement du FRR choisi -- on vérifie que
        c'est bien le cas (résultat à interpréter, pas à forcer)."""

        parameters = build_haenel_p0_parameters()
        context, channel_metrics = build_haenel_static_context(
            parameters
        )

        chosen_actions = set()

        for frr in (0.05, 0.10):
            selected, _all = select_p0_auth_only_haenel_scale(
                context=context,
                parameters=parameters,
                rho_ab=channel_metrics.rho_ab,
                frr=frr,
            )
            self.assertIsNotNone(selected)
            chosen_actions.add(
                selected.decision.authentication_action.value
            )

        # Documente explicitement le résultat observé (voir
        # HAENEL_COMPARISON_README.md) : un seul et même candidat
        # gagne pour les deux FRR testés.
        self.assertEqual(len(chosen_actions), 1)

    def test_simulate_p0_haenel_scale_no_nan(self):

        for frr in (0.05, 0.10):
            events = simulate_p0_auth_only_haenel_scale(
                frr, n_messages=20
            )
            summary = summarize_p0_haenel_scale_events(events)

            self.assertEqual(summary["n_messages"], 20)
            self.assertGreaterEqual(summary["total_energy_mJ"], 0.0)
            self.assertEqual(summary["n_refusal_of_service"], 0)


if __name__ == "__main__":
    unittest.main()
