# Ce fichier teste les politiques de référence B2, B3 et B4
# (physec_dm/case_studies.py), exigées par le protocole de
# simulation (Étape 4) pour permettre une validation complète
# du Decision Maker :
#
# - B2 : PhySec naïve, ordre de préférence fixe, sans plancher
#   de FAR ;
# - B3 : règle hybride fixe non adaptative, sans recherche de
#   repli, plancher de FAR appliqué ;
# - B4 : Decision Maker complet (identique à P0), sans plancher
#   de FAR, pour isoler l'effet de cette seule contrainte.
#
# Toutes réutilisent evaluate_decision/run_decision_maker de
# decision_maker.py : aucune ne recrée d'équation scientifique.
import unittest

from physec_dm.models import Context, KeyAction

from physec_dm.parameters import Parameters

from physec_dm.decision_maker import run_decision_maker

from physec_dm.case_studies import (
    build_b2_policy_definition,
    build_b3_policy_definition,
    build_b4_policy_definition,
    select_b2_naive_physec_decision,
    select_b3_hybrid_fixed_decision,
    select_b4_decision_maker_no_far_floor
)


def create_test_parameters(
    mallory_separation=2.0
):

    parameters = Parameters()

    parameters.minimum_deadline_s = 1.0
    parameters.security_strength_bits = 128

    parameters.mac_cycles = 32000
    parameters.challenge_response_latency_s = 4.0

    parameters.sensing_energy_j = 0.001
    parameters.application_energy_j = 0.002
    parameters.receive_windows_energy_j = 0.003
    parameters.sleep_energy_j = 0.004

    parameters.reconciliation_cycles_per_bit = 100
    parameters.privacy_amplification_cycles = 6400
    parameters.reconciliation_message_energy_j = 0.005
    parameters.reconciliation_message_latency_s = 0.5

    parameters.key_length_bits = 8

    parameters.dominance_tolerance = 1e-12
    parameters.score_tolerance = 1e-12
    parameters.contextual_weights = [
        0.25,
        0.25,
        0.25,
        0.25
    ]

    parameters.mallory_separation = mallory_separation

    return parameters


def create_test_context(
    renewal_required=False,
    key_deadline_s=100000.0,
    remaining_duty_cycle_airtime_s=1000.0
):

    return Context(
        snr_db=20.0,
        doppler_hz=0.0,
        battery_energy_j=28512.0,
        criticality=0,
        key_age_s=0.0,
        messages_with_current_key=0,
        rff_profile_available=True,
        renewal_required=renewal_required,
        key_expired=False,
        compromise_suspected=False,
        key_deadline_s=key_deadline_s,
        remaining_duty_cycle_airtime_s=(
            remaining_duty_cycle_airtime_s
        )
    )


class TestPolicyDefinitions(unittest.TestCase):

    def test_policy_ids_are_distinct(self):

        policy_ids = {
            build_b2_policy_definition()["policy_id"],
            build_b3_policy_definition()["policy_id"],
            build_b4_policy_definition()["policy_id"]
        }

        self.assertEqual(
            len(policy_ids),
            3
        )


class TestB2NaivePhysec(unittest.TestCase):

    # Avec une séparation Mallory très faible, la FAR de A2
    # dépasse largement le plancher de sécurité normal. B2
    # doit malgré tout accepter la décision (pas de plancher),
    # là où le DM complet avec plancher la rejetterait.
    def test_b2_ignores_far_floor(self):

        parameters = create_test_parameters(
            mallory_separation=0.05
        )

        context = create_test_context(
            renewal_required=False
        )

        result_with_floor = run_decision_maker(
            context=context,
            parameters=parameters,
            rho_ab=0.95,
            variation_feasible=True
        )

        result_b2 = select_b2_naive_physec_decision(
            context=context,
            parameters=parameters,
            rho_ab=0.95,
            variation_feasible=True
        )

        # Le DM normal (avec plancher) doit être bloqué par
        # la FAR sur au moins une décision A2 ; B2 ne doit
        # jamais être bloquée par ce motif.
        far_rejections_with_floor = [
            rejection
            for rejection in (
                result_with_floor.rejection_journal
            )
            if rejection.reason_code == "FAR_CONSTRAINT"
        ]

        far_rejections_b2 = [
            rejection
            for rejection in (
                result_b2.rejection_journal
            )
            if rejection.reason_code == "FAR_CONSTRAINT"
        ]

        self.assertGreater(
            len(far_rejections_with_floor),
            0
        )

        self.assertEqual(
            len(far_rejections_b2),
            0
        )

        self.assertFalse(
            result_b2.refusal_of_service
        )

    # Hors renouvellement, l'ordre de préférence de B2 place
    # (A2,K0) avant (A1,K0) : si A2 est admissible, elle doit
    # être choisie.
    def test_b2_prefers_a2_when_admissible(self):

        parameters = create_test_parameters()

        context = create_test_context(
            renewal_required=False
        )

        result = select_b2_naive_physec_decision(
            context=context,
            parameters=parameters,
            rho_ab=0.95,
            variation_feasible=True
        )

        self.assertFalse(
            result.refusal_of_service
        )

        self.assertEqual(
            result.selected_evaluation
            .decision.authentication_action.value,
            "A2"
        )

    def test_b2_refuses_when_nothing_admissible(self):

        parameters = create_test_parameters()

        # Budget de duty-cycle nul : aucune décision
        # n'engageant le moindre temps d'antenne n'est
        # possible, y compris K0/A1 si sa contribution au
        # temps d'antenne (pire cas) est strictement positive.
        #
        # Plus robuste : batterie au minimum, ce qui bloque
        # toute décision par la contrainte énergétique.
        parameters.minimum_battery_energy_j = 28512.0

        context = create_test_context(
            renewal_required=False
        )

        result = select_b2_naive_physec_decision(
            context=context,
            parameters=parameters,
            rho_ab=0.95,
            variation_feasible=True
        )

        self.assertTrue(
            result.refusal_of_service
        )

        self.assertIsNone(
            result.selected_evaluation
        )


class TestB3HybridFixed(unittest.TestCase):

    # B3 respecte le plancher de FAR (contrairement à B2/B4) :
    # avec une séparation Mallory très faible, B3 doit refuser
    # le service plutôt que d'accepter une FAR excessive.
    def test_b3_enforces_far_floor(self):

        parameters = create_test_parameters(
            mallory_separation=0.05
        )

        context = create_test_context(
            renewal_required=False
        )

        result = select_b3_hybrid_fixed_decision(
            context=context,
            parameters=parameters,
            rho_ab=0.95,
            variation_feasible=True
        )

        self.assertTrue(
            result.refusal_of_service
        )

    # B3 n'a AUCUNE recherche de repli : si sa décision fixe
    # (A2,K1a) n'est pas admissible pendant un renouvellement
    # (ici, faisabilité PHY explicitement fausse), elle refuse
    # le service même si (A1,K2), par exemple, serait
    # admissible.
    def test_b3_never_falls_back_to_alternative(self):

        parameters = create_test_parameters()

        context = create_test_context(
            renewal_required=True
        )

        result_b3 = select_b3_hybrid_fixed_decision(
            context=context,
            parameters=parameters,
            rho_ab=0.95,
            # variation_feasible=False interdit K1a/K1b
            # (PHY_VARIATION_INFEASIBLE) : la règle fixe de
            # B3 n'a alors aucun repli.
            variation_feasible=False
        )

        self.assertTrue(
            result_b3.refusal_of_service
        )

        # Le DM complet (P0), lui, retomberait sur K2 ou une
        # autre décision admissible : la comparaison illustre
        # bien l'absence de recherche de repli de B3.
        result_p0 = run_decision_maker(
            context=context,
            parameters=parameters,
            rho_ab=0.95,
            variation_feasible=False,
            k2_protocol={
                "ecc_operation_energies_j": [0.019],
                "ecc_operation_times_s": [0.218],
                "tx_message_sizes_bytes": [32],
                "rx_message_sizes_bytes": [32]
            }
        )

        self.assertFalse(
            result_p0.refusal_of_service
        )

    def test_b3_selects_k1a_when_renewal_required_and_feasible(
        self
    ):

        parameters = create_test_parameters()

        context = create_test_context(
            renewal_required=True
        )

        result = select_b3_hybrid_fixed_decision(
            context=context,
            parameters=parameters,
            rho_ab=0.95,
            variation_feasible=True
        )

        self.assertFalse(
            result.refusal_of_service
        )

        self.assertEqual(
            result.selected_evaluation
            .decision.key_action,
            KeyAction.K1A
        )


class TestB4NoFarFloor(unittest.TestCase):

    # Avec une séparation Mallory très faible, les décisions
    # A2 dépassent le plancher de FAR sous P0 (elles restent
    # dans le journal de rejet, même si A1 permet à P0 de ne
    # pas refuser totalement le service). Sous B4, aucune
    # décision n'est jamais rejetée pour ce motif, et A2 doit
    # redevenir admissible.
    def test_b4_accepts_what_p0_rejects_only_for_far(self):

        parameters = create_test_parameters(
            mallory_separation=0.05
        )

        context = create_test_context(
            renewal_required=False
        )

        result_p0 = run_decision_maker(
            context=context,
            parameters=parameters,
            rho_ab=0.95,
            variation_feasible=True
        )

        result_b4 = select_b4_decision_maker_no_far_floor(
            context=context,
            parameters=parameters,
            rho_ab=0.95,
            variation_feasible=True
        )

        far_rejections_p0 = [
            rejection
            for rejection in result_p0.rejection_journal
            if rejection.reason_code == "FAR_CONSTRAINT"
        ]

        far_rejections_b4 = [
            rejection
            for rejection in result_b4.rejection_journal
            if rejection.reason_code == "FAR_CONSTRAINT"
        ]

        self.assertGreater(
            len(far_rejections_p0),
            0
        )

        self.assertEqual(
            len(far_rejections_b4),
            0
        )

        a2_admissible_under_p0 = any(
            evaluation.decision.authentication_action
            .value == "A2"
            for evaluation in (
                result_p0.admissible_evaluations
            )
        )

        a2_admissible_under_b4 = any(
            evaluation.decision.authentication_action
            .value == "A2"
            for evaluation in (
                result_b4.admissible_evaluations
            )
        )

        self.assertFalse(
            a2_admissible_under_p0
        )

        self.assertTrue(
            a2_admissible_under_b4
        )

    # Sans le motif FAR, B4 doit retrouver exactement le même
    # ensemble admissible que P0 (même front de Pareto).
    def test_b4_matches_p0_when_far_is_not_binding(self):

        parameters = create_test_parameters(
            mallory_separation=2.0
        )

        context = create_test_context(
            renewal_required=False
        )

        result_p0 = run_decision_maker(
            context=context,
            parameters=parameters,
            rho_ab=0.95,
            variation_feasible=True
        )

        result_b4 = select_b4_decision_maker_no_far_floor(
            context=context,
            parameters=parameters,
            rho_ab=0.95,
            variation_feasible=True
        )

        self.assertEqual(
            len(result_p0.admissible_evaluations),
            len(result_b4.admissible_evaluations)
        )

        self.assertEqual(
            result_p0.selected_evaluation
            .decision.get_name(),
            result_b4.selected_evaluation
            .decision.get_name()
        )


if __name__ == "__main__":

    unittest.main()
