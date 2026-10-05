# unittest est l'outil de test fourni directement avec Python.
import unittest


# On importe toutes les structures actuellement définies
# dans models.py afin de vérifier leur comportement.
from physec_dm.models import (
    AuthenticationAction,
    AuthenticationMetrics,
    CampaignResult,
    ChannelMetrics,
    Context,
    CostMetrics,
    DecisionEvaluation,
    DecisionMakerResult,
    KeyAction,
    KeyMetrics,
    MissionResult,
    MissionState,
    MissionStepResult,
    RejectionRecord,
    create_all_decisions
)


# Cette classe teste l'espace des huit décisions.
class TestDecisionModel(unittest.TestCase):

    # Le produit de 2 actions d'authentification
    # par 4 actions de clé doit produire 8 décisions.
    def test_number_of_decisions(self):

        decisions = create_all_decisions()

        self.assertEqual(
            len(decisions),
            8
        )

    # Ce test vérifie les noms et l'ordre exacts.
    def test_decision_names(self):

        decisions = create_all_decisions()

        decision_names = []

        for decision in decisions:
            decision_names.append(
                decision.get_name()
            )

        expected_names = [
            "A1-K0",
            "A1-K1a",
            "A1-K1b",
            "A1-K2",
            "A2-K0",
            "A2-K1a",
            "A2-K1b",
            "A2-K2"
        ]

        self.assertEqual(
            decision_names,
            expected_names
        )


# Cette classe teste le contexte du Decision Maker.
class TestContextModel(unittest.TestCase):

    # Cette fonction crée un contexte valide
    # réutilisé dans plusieurs tests.
    def create_test_context(self):

        return Context(
            snr_db=5.0,
            doppler_hz=0.2,
            battery_energy_j=28000.0,
            criticality=1,
            key_age_s=3600.0,
            messages_with_current_key=120,
            rff_profile_available=True,
            renewal_required=False,
            key_expired=False,
            compromise_suspected=False,
            key_deadline_s=50000.0,
            remaining_duty_cycle_airtime_s=10.0
        )

    # Vérification des valeurs numériques.
    def test_context_numeric_values(self):

        context = self.create_test_context()

        self.assertEqual(context.snr_db, 5.0)
        self.assertEqual(context.doppler_hz, 0.2)
        self.assertEqual(
            context.battery_energy_j,
            28000.0
        )
        self.assertEqual(context.criticality, 1)
        self.assertEqual(context.key_age_s, 3600.0)
        self.assertEqual(
            context.messages_with_current_key,
            120
        )
        self.assertEqual(
            context.key_deadline_s,
            50000.0
        )
        self.assertEqual(
            context.remaining_duty_cycle_airtime_s,
            10.0
        )

    # Vérification des valeurs booléennes.
    def test_context_boolean_values(self):

        context = self.create_test_context()

        self.assertTrue(
            context.rff_profile_available
        )
        self.assertFalse(
            context.renewal_required
        )
        self.assertFalse(
            context.key_expired
        )
        self.assertFalse(
            context.compromise_suspected
        )

    # La criticité doit valoir 0 ou 1.
    def test_invalid_criticality(self):

        with self.assertRaises(ValueError):

            Context(
                snr_db=5.0,
                doppler_hz=0.2,
                battery_energy_j=28000.0,
                criticality=2,
                key_age_s=3600.0,
                messages_with_current_key=120,
                rff_profile_available=True,
                renewal_required=False,
                key_expired=False,
                compromise_suspected=False,
                key_deadline_s=50000.0,
                remaining_duty_cycle_airtime_s=10.0
            )

    # L'énergie de batterie ne peut pas être négative.
    def test_negative_battery_energy(self):

        with self.assertRaises(ValueError):

            Context(
                snr_db=5.0,
                doppler_hz=0.2,
                battery_energy_j=-100.0,
                criticality=0,
                key_age_s=3600.0,
                messages_with_current_key=120,
                rff_profile_available=True,
                renewal_required=False,
                key_expired=False,
                compromise_suspected=False,
                key_deadline_s=50000.0,
                remaining_duty_cycle_airtime_s=10.0
            )

    # L'échéance doit être supérieure à zéro.
    def test_invalid_key_deadline(self):

        with self.assertRaises(ValueError):

            Context(
                snr_db=5.0,
                doppler_hz=0.2,
                battery_energy_j=28000.0,
                criticality=0,
                key_age_s=3600.0,
                messages_with_current_key=120,
                rff_profile_available=True,
                renewal_required=False,
                key_expired=False,
                compromise_suspected=False,
                key_deadline_s=0.0,
                remaining_duty_cycle_airtime_s=10.0
            )


# Cette classe teste le stockage
# des métriques du canal.
class TestChannelMetrics(unittest.TestCase):

    def create_test_channel_metrics(self):

        return ChannelMetrics(
            snr_db=5.0,
            snr_linear=3.1622776602,
            doppler_hz=0.2,
            temporal_correlation=0.80,
            noise_correlation=0.75,
            rho_ab=0.60
        )

    def test_channel_metrics_values(self):

        channel_metrics = (
            self.create_test_channel_metrics()
        )

        self.assertEqual(
            channel_metrics.snr_db,
            5.0
        )
        self.assertEqual(
            channel_metrics.snr_linear,
            3.1622776602
        )
        self.assertEqual(
            channel_metrics.doppler_hz,
            0.2
        )
        self.assertEqual(
            channel_metrics.temporal_correlation,
            0.80
        )
        self.assertEqual(
            channel_metrics.noise_correlation,
            0.75
        )
        self.assertEqual(
            channel_metrics.rho_ab,
            0.60
        )

    # Le modèle nominal doit conserver
    # les corrélations négatives.
    def test_negative_correlation_is_preserved(self):

        channel_metrics = ChannelMetrics(
            snr_db=5.0,
            snr_linear=3.1622776602,
            doppler_hz=1.5,
            temporal_correlation=-0.40,
            noise_correlation=0.75,
            rho_ab=-0.28746
        )

        self.assertEqual(
            channel_metrics.temporal_correlation,
            -0.40
        )
        self.assertEqual(
            channel_metrics.rho_ab,
            -0.28746
        )


# Cette classe teste les métriques d'authentification.
class TestAuthenticationMetrics(unittest.TestCase):

    def create_test_authentication_metrics(self):

        return AuthenticationMetrics(
            authentication_action=AuthenticationAction.A2,
            far=0.02,
            frr=0.05,
            mac_forgery_probability=0.000001,
            total_false_acceptance_probability=0.020001,
            authentication_robustness=0.979999,
            alice_fallback_probability=0.05,
            mallory_fallback_probability=0.98
        )

    def test_authentication_metrics_values(self):

        authentication_metrics = (
            self.create_test_authentication_metrics()
        )

        self.assertEqual(
            authentication_metrics.authentication_action,
            AuthenticationAction.A2
        )
        self.assertEqual(
            authentication_metrics.far,
            0.02
        )
        self.assertEqual(
            authentication_metrics.frr,
            0.05
        )
        self.assertEqual(
            authentication_metrics.mac_forgery_probability,
            0.000001
        )
        self.assertEqual(
            authentication_metrics.total_false_acceptance_probability,
            0.020001
        )
        self.assertEqual(
            authentication_metrics.authentication_robustness,
            0.979999
        )
        self.assertEqual(
            authentication_metrics.alice_fallback_probability,
            0.05
        )
        self.assertEqual(
            authentication_metrics.mallory_fallback_probability,
            0.98
        )

    # La FAR RFF et la probabilité totale
    # de fausse acceptation doivent rester distinctes.
    def test_far_and_total_false_acceptance_are_distinct(self):

        authentication_metrics = (
            self.create_test_authentication_metrics()
        )

        self.assertNotEqual(
            authentication_metrics.far,
            authentication_metrics.total_false_acceptance_probability
        )


# Cette classe teste les métriques de gestion de clé.
class TestKeyMetrics(unittest.TestCase):

    def create_test_key_metrics(self):

        return KeyMetrics(
            key_action=KeyAction.K1A,
            raw_kdr=0.20,
            effective_kdr=0.20,
            binary_entropy=0.7219,
            reconciliation_yield=0.19467,
            required_measurements=658,
            agreement_feasible=True,
            variation_feasible=True,
            phy_feasible=True,
            key_aging_index=0.65,
            renewal_required=True,
            key_expired=False,
            key_deadline_s=20000.0,
            key_quality=0.2781
        )

    def test_key_metrics_numeric_values(self):

        key_metrics = self.create_test_key_metrics()

        self.assertEqual(
            key_metrics.key_action,
            KeyAction.K1A
        )
        self.assertEqual(
            key_metrics.raw_kdr,
            0.20
        )
        self.assertEqual(
            key_metrics.effective_kdr,
            0.20
        )
        self.assertEqual(
            key_metrics.binary_entropy,
            0.7219
        )
        self.assertEqual(
            key_metrics.reconciliation_yield,
            0.19467
        )
        self.assertEqual(
            key_metrics.required_measurements,
            658
        )
        self.assertEqual(
            key_metrics.key_aging_index,
            0.65
        )
        self.assertEqual(
            key_metrics.key_deadline_s,
            20000.0
        )
        self.assertEqual(
            key_metrics.key_quality,
            0.2781
        )

    def test_key_metrics_boolean_values(self):

        key_metrics = self.create_test_key_metrics()

        self.assertTrue(
            key_metrics.agreement_feasible
        )
        self.assertTrue(
            key_metrics.variation_feasible
        )
        self.assertTrue(
            key_metrics.phy_feasible
        )
        self.assertTrue(
            key_metrics.renewal_required
        )
        self.assertFalse(
            key_metrics.key_expired
        )


# Cette classe teste les coûts d'une décision.
class TestCostMetrics(unittest.TestCase):

    def test_cost_metrics_values(self):

        cost_metrics = CostMetrics(
            base_energy_j=0.20,
            authentication_security_energy_j=0.02,
            key_security_energy_j=0.03,
            security_energy_j=0.05,
            total_energy_j=0.25,
            authentication_latency_s=0.10,
            prudent_authentication_latency_s=1.00,
            key_latency_s=20.0,
            normalized_latency=0.40,
            airtime_s=1.50,
            expected_energy_j=0.24,
            worst_case_energy_j=0.30
        )

        self.assertEqual(
            cost_metrics.base_energy_j,
            0.20
        )
        self.assertEqual(
            cost_metrics.security_energy_j,
            0.05
        )
        self.assertEqual(
            cost_metrics.total_energy_j,
            0.25
        )
        self.assertEqual(
            cost_metrics.prudent_authentication_latency_s,
            1.00
        )
        self.assertEqual(
            cost_metrics.normalized_latency,
            0.40
        )
        self.assertEqual(
            cost_metrics.worst_case_energy_j,
            0.30
        )


# Cette classe teste l'enregistrement
# d'un motif de rejet.
class TestRejectionRecord(unittest.TestCase):

    def test_rejection_record_values(self):

        # L'indice 4 correspond à A2-K0
        # dans l'ordre officiel des décisions.
        decision = create_all_decisions()[4]

        rejection = RejectionRecord(
            decision=decision,
            stage="security",
            reason_code="FAR_TOO_HIGH",
            explanation="La FAR dépasse la limite.",
            measured_value=0.08,
            allowed_value=0.05
        )

        self.assertEqual(
            rejection.decision.get_name(),
            "A2-K0"
        )
        self.assertEqual(
            rejection.stage,
            "security"
        )
        self.assertEqual(
            rejection.reason_code,
            "FAR_TOO_HIGH"
        )
        self.assertEqual(
            rejection.measured_value,
            0.08
        )
        self.assertEqual(
            rejection.allowed_value,
            0.05
        )


# Cette classe teste l'évaluation
# d'une décision candidate.
class TestDecisionEvaluation(unittest.TestCase):

    def test_decision_evaluation_defaults(self):

        decision = create_all_decisions()[0]

        evaluation = DecisionEvaluation(
            decision
        )

        self.assertEqual(
            evaluation.decision.get_name(),
            "A1-K0"
        )
        self.assertIsNone(
            evaluation.authentication_metrics
        )
        self.assertIsNone(
            evaluation.key_metrics
        )
        self.assertIsNone(
            evaluation.cost_metrics
        )
        self.assertFalse(
            evaluation.admissible
        )
        self.assertEqual(
            evaluation.rejection_reasons,
            []
        )
        self.assertFalse(
            evaluation.pareto_optimal
        )
        self.assertIsNone(
            evaluation.tchebycheff_score
        )

    def test_add_rejection_to_decision_evaluation(self):

        decision = create_all_decisions()[7]

        evaluation = DecisionEvaluation(
            decision
        )

        rejection = RejectionRecord(
            decision=decision,
            stage="resource",
            reason_code="BATTERY_TOO_LOW",
            explanation="La batterie est insuffisante."
        )

        # On place volontairement la décision
        # dans l'état admissible avant d'ajouter le rejet.
        evaluation.admissible = True

        evaluation.add_rejection(
            rejection
        )

        self.assertEqual(
            len(evaluation.rejection_reasons),
            1
        )
        self.assertFalse(
            evaluation.admissible
        )


# Cette classe teste le résultat global
# du Decision Maker.
class TestDecisionMakerResult(unittest.TestCase):

    def test_decision_maker_result_values(self):

        context = Context(
            snr_db=5.0,
            doppler_hz=0.2,
            battery_energy_j=28000.0,
            criticality=0,
            key_age_s=100.0,
            messages_with_current_key=2,
            rff_profile_available=True,
            renewal_required=False,
            key_expired=False,
            compromise_suspected=False,
            key_deadline_s=50000.0,
            remaining_duty_cycle_airtime_s=10.0
        )

        evaluation = DecisionEvaluation(
            create_all_decisions()[0]
        )

        result = DecisionMakerResult(
            context=context,
            all_evaluations=[evaluation],
            admissible_evaluations=[evaluation],
            pareto_front=[evaluation],
            rejection_journal=[],
            contextual_weights=[
                0.25,
                0.25,
                0.25,
                0.25
            ],
            ideal_point=[
                0.1,
                0.2,
                -0.9,
                -0.8
            ],
            nadir_point=[
                0.3,
                0.5,
                -0.7,
                -0.6
            ],
            selected_evaluation=evaluation,
            refusal_of_service=False,
            fallback_mode_used=None,
            explanation="A1-K0 a été choisie."
        )

        self.assertFalse(
            result.refusal_of_service
        )
        self.assertEqual(
            result.selected_evaluation.decision.get_name(),
            "A1-K0"
        )
        self.assertEqual(
            result.contextual_weights,
            [
                0.25,
                0.25,
                0.25,
                0.25
            ]
        )


# Cette classe teste l'état de la mission.
class TestMissionState(unittest.TestCase):

    def create_test_state(self):

        return MissionState(
            step_index=3,
            time_s=180.0,
            battery_energy_j=28000.0,
            key_age_s=180.0,
            messages_with_current_key=3,
            current_key_identifier="KEY-001",
            remaining_duty_cycle_airtime_s=20.0
        )

    def test_mission_state_values(self):

        state = self.create_test_state()

        self.assertEqual(
            state.step_index,
            3
        )
        self.assertEqual(
            state.time_s,
            180.0
        )
        self.assertEqual(
            state.battery_energy_j,
            28000.0
        )
        self.assertEqual(
            state.current_key_identifier,
            "KEY-001"
        )
        self.assertEqual(
            state.legitimate_messages,
            0
        )
        self.assertEqual(
            state.mallory_attempts,
            0
        )

    def test_negative_mission_battery_is_rejected(self):

        with self.assertRaises(ValueError):

            MissionState(
                step_index=0,
                time_s=0.0,
                battery_energy_j=-1.0,
                key_age_s=0.0,
                messages_with_current_key=0,
                current_key_identifier="KEY-001",
                remaining_duty_cycle_airtime_s=10.0
            )


# Cette classe teste le résultat
# d'une période de mission.
class TestMissionStepResult(unittest.TestCase):

    # Cette fonction prépare les objets nécessaires
    # à la création d'un résultat de période.
    def create_basic_objects(self):

        state_before = MissionState(
            step_index=0,
            time_s=0.0,
            battery_energy_j=28512.0,
            key_age_s=0.0,
            messages_with_current_key=0,
            current_key_identifier="KEY-001",
            remaining_duty_cycle_airtime_s=10.0
        )

        state_after = MissionState(
            step_index=1,
            time_s=60.0,
            battery_energy_j=28511.8,
            key_age_s=60.0,
            messages_with_current_key=1,
            current_key_identifier="KEY-001",
            remaining_duty_cycle_airtime_s=9.0
        )

        context = Context(
            snr_db=5.0,
            doppler_hz=0.2,
            battery_energy_j=28512.0,
            criticality=0,
            key_age_s=0.0,
            messages_with_current_key=0,
            rff_profile_available=True,
            renewal_required=False,
            key_expired=False,
            compromise_suspected=False,
            key_deadline_s=60000.0,
            remaining_duty_cycle_airtime_s=10.0
        )

        channel_metrics = ChannelMetrics(
            snr_db=5.0,
            snr_linear=3.1622776602,
            doppler_hz=0.2,
            temporal_correlation=0.8,
            noise_correlation=0.75,
            rho_ab=0.6
        )

        evaluation = DecisionEvaluation(
            create_all_decisions()[0]
        )

        decision_result = DecisionMakerResult(
            context=context,
            all_evaluations=[evaluation],
            admissible_evaluations=[evaluation],
            pareto_front=[evaluation],
            rejection_journal=[],
            contextual_weights=[
                0.25,
                0.25,
                0.25,
                0.25
            ],
            ideal_point=[
                0.1,
                0.2,
                -0.9,
                -0.8
            ],
            nadir_point=[
                0.3,
                0.5,
                -0.7,
                -0.6
            ],
            selected_evaluation=evaluation,
            refusal_of_service=False,
            fallback_mode_used=None,
            explanation="Décision valide."
        )

        return (
            state_before,
            state_after,
            context,
            channel_metrics,
            decision_result
        )

    def test_mission_step_result_values(self):

        (
            state_before,
            state_after,
            context,
            channel_metrics,
            decision_result
        ) = self.create_basic_objects()

        step_result = MissionStepResult(
            state_before=state_before,
            context=context,
            channel_metrics=channel_metrics,
            decision_maker_result=decision_result,
            legitimate_message_served=True,
            mallory_attempted=False,
            mallory_accepted=False,
            energy_debited_from_alice_j=0.2,
            state_after=state_after
        )

        self.assertTrue(
            step_result.legitimate_message_served
        )
        self.assertFalse(
            step_result.mallory_attempted
        )
        self.assertEqual(
            step_result.energy_debited_from_alice_j,
            0.2
        )
        self.assertEqual(
            step_result.state_after.step_index,
            1
        )

    def test_negative_debited_energy_is_rejected(self):

        (
            state_before,
            state_after,
            context,
            channel_metrics,
            decision_result
        ) = self.create_basic_objects()

        with self.assertRaises(ValueError):

            MissionStepResult(
                state_before=state_before,
                context=context,
                channel_metrics=channel_metrics,
                decision_maker_result=decision_result,
                legitimate_message_served=True,
                mallory_attempted=False,
                mallory_accepted=False,
                energy_debited_from_alice_j=-0.2,
                state_after=state_after
            )


# Cette classe teste le résultat complet
# d'une mission.
class TestMissionResult(unittest.TestCase):

    def test_mission_result_values(self):

        final_state = MissionState(
            step_index=10,
            time_s=600.0,
            battery_energy_j=28000.0,
            key_age_s=600.0,
            messages_with_current_key=10,
            current_key_identifier="KEY-001",
            remaining_duty_cycle_airtime_s=5.0
        )

        mission_result = MissionResult(
            parameters_snapshot={
                "mean_snr_db": 5.0
            },
            seed=123,
            policy_id="P0",
            steps=[],
            lifetime_s=600.0,
            mean_energy_per_generated_message_j=0.2,
            mean_energy_per_served_message_j=0.21,
            false_acceptance_rate=0.01,
            critical_false_acceptance_rate=0.005,
            legitimate_refusal_rate=0.02,
            security_floor_violation_rate=0.0,
            decision_counts={
                "A1-K0": 10
            },
            final_state=final_state,
            stop_reason="maximum_steps",
            censored=True
        )

        self.assertEqual(
            mission_result.seed,
            123
        )
        self.assertEqual(
            mission_result.policy_id,
            "P0"
        )
        self.assertEqual(
            mission_result.lifetime_s,
            600.0
        )
        self.assertEqual(
            mission_result.decision_counts,
            {
                "A1-K0": 10
            }
        )
        self.assertTrue(
            mission_result.censored
        )


# Cette classe teste le résultat
# d'une campagne de simulation.
class TestCampaignResult(unittest.TestCase):

    def test_campaign_result_values(self):

        campaign_result = CampaignResult(
            campaign_id="CAMP-01",
            scenario_ids=[
                "nominal"
            ],
            policy_ids=[
                "P0",
                "B1"
            ],
            seeds=[
                1,
                2,
                3
            ],
            mission_results=[],
            output_directory="results/"
        )

        self.assertEqual(
            campaign_result.campaign_id,
            "CAMP-01"
        )
        self.assertEqual(
            campaign_result.scenario_ids,
            [
                "nominal"
            ]
        )
        self.assertEqual(
            campaign_result.policy_ids,
            [
                "P0",
                "B1"
            ]
        )
        self.assertEqual(
            campaign_result.seeds,
            [
                1,
                2,
                3
            ]
        )
        self.assertEqual(
            campaign_result.output_directory,
            "results/"
        )


# Cette condition permet aussi de lancer
# ce fichier de test directement.
if __name__ == "__main__":

    unittest.main()
