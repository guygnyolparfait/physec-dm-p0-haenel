# unittest est l'outil de test fourni avec Python.
import unittest


# patch permet de remplacer temporairement
# les sous-modèles pendant les tests d'intégration.
from unittest.mock import patch


from physec_dm.models import (
    AuthenticationAction,
    AuthenticationMetrics,
    Context,
    CostMetrics,
    Decision,
    DecisionEvaluation,
    KeyAction,
    KeyMetrics
)

from physec_dm.parameters import Parameters

from physec_dm.decision_maker import (
    add_rejection,
    apply_reasoning_rules,
    apply_resource_and_security_constraints,
    build_objective_vector,
    build_tie_break_key,
    calculate_ideal_and_nadir_points,
    calculate_pareto_front,
    calculate_tchebycheff_score,
    evaluate_decision,
    objective_vector_dominates,
    run_decision_maker,
    select_from_pareto_front,
    validate_contextual_weights
)


# Cette fonction crée des paramètres complets
# uniquement pour les tests.
#
# Aucune de ces valeurs n'est ajoutée
# dans parameters.py.
def create_test_parameters():

    parameters = Parameters()

    parameters.minimum_deadline_s = 1.0
    parameters.security_strength_bits = 128

    parameters.mac_cycles = 32000
    parameters.challenge_response_latency_s = 4.0

    parameters.sensing_energy_j = 0.001
    parameters.application_energy_j = 0.002
    parameters.receive_windows_energy_j = 0.003
    parameters.sleep_energy_j = 0.004

    parameters.raw_bit_count = 128
    parameters.reconciliation_cycles_per_bit = 100
    parameters.privacy_amplification_cycles = 6400
    parameters.reconciliation_message_energy_j = 0.005
    parameters.reconciliation_message_latency_s = 0.5

    parameters.dominance_tolerance = 1e-12
    parameters.score_tolerance = 1e-12
    parameters.contextual_weights = [
        0.25,
        0.25,
        0.25,
        0.25
    ]

    return parameters


# Cette fonction crée un contexte valide.
def create_test_context(
    renewal_required=False,
    rff_profile_available=True,
    criticality=0,
    battery_energy_j=30000.0,
    key_deadline_s=100.0,
    duty_airtime_s=100.0
):

    return Context(
        snr_db=5.0,
        doppler_hz=0.0,
        battery_energy_j=battery_energy_j,
        criticality=criticality,
        key_age_s=100.0,
        messages_with_current_key=2,
        rff_profile_available=(
            rff_profile_available
        ),
        renewal_required=renewal_required,
        key_expired=False,
        compromise_suspected=False,
        key_deadline_s=key_deadline_s,
        remaining_duty_cycle_airtime_s=(
            duty_airtime_s
        )
    )


# Cette fonction crée les métriques
# d'authentification utilisées dans les tests.
def create_authentication_metrics(
    action=AuthenticationAction.A1,
    far=0.001,
    robustness=0.999
):

    return AuthenticationMetrics(
        authentication_action=action,
        far=far,
        frr=0.05 if action == AuthenticationAction.A2 else 0.0,
        mac_forgery_probability=2 ** (-64),
        total_false_acceptance_probability=far,
        authentication_robustness=robustness,
        alice_fallback_probability=(
            0.05
            if action == AuthenticationAction.A2
            else 0.0
        ),
        mallory_fallback_probability=(
            1.0 - far
            if action == AuthenticationAction.A2
            else 0.0
        )
    )


# Cette fonction crée les métriques de clé.
def create_key_metrics(
    action=KeyAction.K0,
    key_quality=0.8,
    agreement_feasible=None,
    variation_feasible=None,
    phy_feasible=None
):

    return KeyMetrics(
        key_action=action,
        raw_kdr=0.20 if action in [KeyAction.K1A, KeyAction.K1B] else None,
        effective_kdr=0.20 if action in [KeyAction.K1A, KeyAction.K1B] else None,
        binary_entropy=0.72 if action in [KeyAction.K1A, KeyAction.K1B] else None,
        reconciliation_yield=0.19 if action in [KeyAction.K1A, KeyAction.K1B] else None,
        required_measurements=10 if action in [KeyAction.K1A, KeyAction.K1B] else None,
        agreement_feasible=agreement_feasible,
        variation_feasible=variation_feasible,
        phy_feasible=phy_feasible,
        key_aging_index=0.2,
        renewal_required=(action != KeyAction.K0),
        key_expired=False,
        key_deadline_s=100.0,
        key_quality=key_quality
    )


# Cette fonction crée les coûts.
def create_cost_metrics(
    expected_energy_j=1.0,
    worst_case_energy_j=1.2,
    normalized_latency=0.2,
    prudent_authentication_latency_s=1.0,
    key_latency_s=0.0,
    airtime_s=1.0
):

    return CostMetrics(
        base_energy_j=0.5,
        authentication_security_energy_j=0.2,
        key_security_energy_j=0.3,
        security_energy_j=0.5,
        total_energy_j=expected_energy_j,
        authentication_latency_s=0.5,
        prudent_authentication_latency_s=(
            prudent_authentication_latency_s
        ),
        key_latency_s=key_latency_s,
        normalized_latency=normalized_latency,
        airtime_s=airtime_s,
        expected_energy_j=expected_energy_j,
        worst_case_energy_j=worst_case_energy_j
    )


# Cette fonction crée une évaluation déjà calculée.
def create_evaluation(
    name_index,
    objective_vector,
    far=0.01,
    energy=1.0,
    latency=0.2
):

    authentication_actions = [
        AuthenticationAction.A1,
        AuthenticationAction.A2
    ]

    key_actions = [
        KeyAction.K0,
        KeyAction.K1A,
        KeyAction.K1B,
        KeyAction.K2
    ]

    decision_index = 0
    selected_decision = None

    for authentication_action in authentication_actions:

        for key_action in key_actions:

            if decision_index == name_index:

                selected_decision = Decision(
                    authentication_action,
                    key_action
                )

            decision_index += 1

    evaluation = DecisionEvaluation(
        selected_decision
    )

    evaluation.authentication_metrics = (
        create_authentication_metrics(
            action=selected_decision.authentication_action,
            far=far,
            robustness=-objective_vector[2]
        )
    )

    evaluation.key_metrics = create_key_metrics(
        action=selected_decision.key_action,
        key_quality=-objective_vector[3]
    )

    evaluation.cost_metrics = create_cost_metrics(
        expected_energy_j=energy,
        normalized_latency=latency
    )

    evaluation.objective_vector = objective_vector
    evaluation.reasoning_rules_ok = True
    evaluation.resource_constraints_ok = True
    evaluation.security_constraint_ok = True
    evaluation.admissible = True

    return evaluation


class TestObjectiveVector(unittest.TestCase):

    def test_objective_vector_signs(self):

        authentication_metrics = (
            create_authentication_metrics(
                robustness=0.90
            )
        )

        key_metrics = create_key_metrics(
            key_quality=0.80
        )

        cost_metrics = create_cost_metrics(
            expected_energy_j=2.0,
            normalized_latency=0.3
        )

        vector = build_objective_vector(
            authentication_metrics,
            key_metrics,
            cost_metrics
        )

        self.assertEqual(
            vector,
            [
                2.0,
                0.3,
                -0.90,
                -0.80
            ]
        )


class TestReasoningRules(unittest.TestCase):

    def test_a2_requires_rff_profile(self):

        decision = Decision(
            AuthenticationAction.A2,
            KeyAction.K0
        )

        evaluation = DecisionEvaluation(
            decision
        )

        context = create_test_context(
            rff_profile_available=False
        )

        self.assertFalse(
            apply_reasoning_rules(
                evaluation,
                context
            )
        )

        self.assertEqual(
            evaluation.rejection_reasons[0].reason_code,
            "RFF_PROFILE_UNAVAILABLE"
        )

    # Retour à la règle stricte (95)-(96), validé avec
    # l'encadrante : K1a n'est plus une décision RETOURNABLE
    # tant que le renouvellement n'est pas requis. Sa
    # collecte progressive reste possible, mais uniquement
    # comme phénomène de mission (physec_dm/mission.py),
    # jamais comme une décision que le Decision Maker
    # pourrait retourner ici.
    def test_no_renewal_forbids_k1a(self):

        decision = Decision(
            AuthenticationAction.A1,
            KeyAction.K1A
        )

        evaluation = DecisionEvaluation(
            decision
        )

        context = create_test_context(
            renewal_required=False
        )

        self.assertFalse(
            apply_reasoning_rules(
                evaluation,
                context
            )
        )

        self.assertEqual(
            evaluation.rejection_reasons[0].reason_code,
            "KEY_RENEWAL_NOT_REQUIRED"
        )

    # K1b suit exactement la même règle stricte que K1a :
    # elle ne progresse plus jamais gratuitement en
    # arrière-plan (voir physec_dm/mission.py, section 7bis).
    def test_no_renewal_forbids_k1b(self):

        decision = Decision(
            AuthenticationAction.A1,
            KeyAction.K1B
        )

        evaluation = DecisionEvaluation(
            decision
        )

        context = create_test_context(
            renewal_required=False
        )

        self.assertFalse(
            apply_reasoning_rules(
                evaluation,
                context
            )
        )

        self.assertEqual(
            evaluation.rejection_reasons[0].reason_code,
            "KEY_RENEWAL_NOT_REQUIRED"
        )

    # K2 n'a pas de phase de préparation : il reste
    # interdit tant que le renouvellement n'est pas requis.
    def test_no_renewal_forbids_k2(self):

        decision = Decision(
            AuthenticationAction.A1,
            KeyAction.K2
        )

        evaluation = DecisionEvaluation(
            decision
        )

        context = create_test_context(
            renewal_required=False
        )

        self.assertFalse(
            apply_reasoning_rules(
                evaluation,
                context
            )
        )

        self.assertEqual(
            evaluation.rejection_reasons[0].reason_code,
            "KEY_RENEWAL_NOT_REQUIRED"
        )

    def test_renewal_forbids_k0(self):

        decision = Decision(
            AuthenticationAction.A1,
            KeyAction.K0
        )

        evaluation = DecisionEvaluation(
            decision
        )

        context = create_test_context(
            renewal_required=True
        )

        self.assertFalse(
            apply_reasoning_rules(
                evaluation,
                context
            )
        )

        self.assertEqual(
            evaluation.rejection_reasons[0].reason_code,
            "KEY_RENEWAL_REQUIRED"
        )

    def test_valid_reasoning(self):

        decision = Decision(
            AuthenticationAction.A1,
            KeyAction.K0
        )

        evaluation = DecisionEvaluation(
            decision
        )

        self.assertTrue(
            apply_reasoning_rules(
                evaluation,
                create_test_context()
            )
        )


class TestConstraints(unittest.TestCase):

    def create_prepared_evaluation(
        self,
        decision,
        authentication_metrics=None,
        key_metrics=None,
        cost_metrics=None
    ):

        evaluation = DecisionEvaluation(
            decision
        )

        evaluation.reasoning_rules_ok = True

        evaluation.authentication_metrics = (
            authentication_metrics
            if authentication_metrics is not None
            else create_authentication_metrics(
                action=decision.authentication_action
            )
        )

        evaluation.key_metrics = (
            key_metrics
            if key_metrics is not None
            else create_key_metrics(
                action=decision.key_action
            )
        )

        evaluation.cost_metrics = (
            cost_metrics
            if cost_metrics is not None
            else create_cost_metrics()
        )

        evaluation.objective_vector = (
            build_objective_vector(
                evaluation.authentication_metrics,
                evaluation.key_metrics,
                evaluation.cost_metrics
            )
        )

        return evaluation

    def test_variation_none_rejects_k1(self):

        decision = Decision(
            AuthenticationAction.A1,
            KeyAction.K1A
        )

        key_metrics = create_key_metrics(
            action=KeyAction.K1A,
            agreement_feasible=True,
            variation_feasible=None,
            phy_feasible=True
        )

        evaluation = self.create_prepared_evaluation(
            decision,
            key_metrics=key_metrics
        )

        apply_resource_and_security_constraints(
            evaluation,
            create_test_context(
                renewal_required=True
            ),
            create_test_parameters()
        )

        codes = [
            rejection.reason_code
            for rejection in evaluation.rejection_reasons
        ]

        self.assertIn(
            "PHY_VARIATION_NOT_VALIDATED",
            codes
        )

    def test_phy_infeasible_rejects_k1(self):

        decision = Decision(
            AuthenticationAction.A1,
            KeyAction.K1B
        )

        key_metrics = create_key_metrics(
            action=KeyAction.K1B,
            agreement_feasible=False,
            variation_feasible=True,
            phy_feasible=False
        )

        evaluation = self.create_prepared_evaluation(
            decision,
            key_metrics=key_metrics
        )

        apply_resource_and_security_constraints(
            evaluation,
            create_test_context(
                renewal_required=True
            ),
            create_test_parameters()
        )

        self.assertEqual(
            evaluation.rejection_reasons[0].reason_code,
            "PHY_AGREEMENT_INFEASIBLE"
        )

    def test_battery_uses_worst_case(self):

        decision = Decision(
            AuthenticationAction.A1,
            KeyAction.K0
        )

        parameters = create_test_parameters()
        parameters.minimum_battery_energy_j = 5.0

        cost_metrics = create_cost_metrics(
            expected_energy_j=1.0,
            worst_case_energy_j=6.0
        )

        evaluation = self.create_prepared_evaluation(
            decision,
            cost_metrics=cost_metrics
        )

        apply_resource_and_security_constraints(
            evaluation,
            create_test_context(
                battery_energy_j=10.0
            ),
            parameters
        )

        codes = [
            rejection.reason_code
            for rejection in evaluation.rejection_reasons
        ]

        self.assertIn(
            "BATTERY_CONSTRAINT",
            codes
        )

    def test_authentication_uses_prudent_latency(self):

        decision = Decision(
            AuthenticationAction.A2,
            KeyAction.K0
        )

        cost_metrics = create_cost_metrics(
            prudent_authentication_latency_s=6.0
        )

        evaluation = self.create_prepared_evaluation(
            decision,
            authentication_metrics=(
                create_authentication_metrics(
                    action=AuthenticationAction.A2
                )
            ),
            cost_metrics=cost_metrics
        )

        apply_resource_and_security_constraints(
            evaluation,
            create_test_context(
                criticality=1
            ),
            create_test_parameters()
        )

        codes = [
            rejection.reason_code
            for rejection in evaluation.rejection_reasons
        ]

        self.assertIn(
            "AUTH_LATENCY_CONSTRAINT",
            codes
        )

    def test_key_deadline_constraint(self):

        decision = Decision(
            AuthenticationAction.A1,
            KeyAction.K2
        )

        cost_metrics = create_cost_metrics(
            key_latency_s=20.0
        )

        evaluation = self.create_prepared_evaluation(
            decision,
            key_metrics=create_key_metrics(
                action=KeyAction.K2
            ),
            cost_metrics=cost_metrics
        )

        apply_resource_and_security_constraints(
            evaluation,
            create_test_context(
                renewal_required=True,
                key_deadline_s=10.0
            ),
            create_test_parameters()
        )

        codes = [
            rejection.reason_code
            for rejection in evaluation.rejection_reasons
        ]

        self.assertIn(
            "KEY_DEADLINE_CONSTRAINT",
            codes
        )

    def test_duty_cycle_constraint(self):

        decision = Decision(
            AuthenticationAction.A1,
            KeyAction.K0
        )

        evaluation = self.create_prepared_evaluation(
            decision,
            cost_metrics=create_cost_metrics(
                airtime_s=3.0
            )
        )

        apply_resource_and_security_constraints(
            evaluation,
            create_test_context(
                duty_airtime_s=2.0
            ),
            create_test_parameters()
        )

        codes = [
            rejection.reason_code
            for rejection in evaluation.rejection_reasons
        ]

        self.assertIn(
            "DUTY_CYCLE_CONSTRAINT",
            codes
        )

    def test_normal_far_limit(self):

        decision = Decision(
            AuthenticationAction.A2,
            KeyAction.K0
        )

        evaluation = self.create_prepared_evaluation(
            decision,
            authentication_metrics=(
                create_authentication_metrics(
                    action=AuthenticationAction.A2,
                    far=0.06
                )
            )
        )

        apply_resource_and_security_constraints(
            evaluation,
            create_test_context(
                criticality=0
            ),
            create_test_parameters()
        )

        codes = [
            rejection.reason_code
            for rejection in evaluation.rejection_reasons
        ]

        self.assertIn(
            "FAR_CONSTRAINT",
            codes
        )

    def test_critical_far_limit(self):

        decision = Decision(
            AuthenticationAction.A2,
            KeyAction.K0
        )

        evaluation = self.create_prepared_evaluation(
            decision,
            authentication_metrics=(
                create_authentication_metrics(
                    action=AuthenticationAction.A2,
                    far=0.02
                )
            )
        )

        apply_resource_and_security_constraints(
            evaluation,
            create_test_context(
                criticality=1
            ),
            create_test_parameters()
        )

        codes = [
            rejection.reason_code
            for rejection in evaluation.rejection_reasons
        ]

        self.assertIn(
            "FAR_CONSTRAINT",
            codes
        )

    def test_valid_decision_is_admissible(self):

        decision = Decision(
            AuthenticationAction.A1,
            KeyAction.K0
        )

        evaluation = self.create_prepared_evaluation(
            decision
        )

        self.assertTrue(
            apply_resource_and_security_constraints(
                evaluation,
                create_test_context(),
                create_test_parameters()
            )
        )


class TestPareto(unittest.TestCase):

    def test_dominance(self):

        vector_a = [
            1.0,
            1.0,
            -0.9,
            -0.8
        ]

        vector_b = [
            2.0,
            1.0,
            -0.8,
            -0.7
        ]

        self.assertTrue(
            objective_vector_dominates(
                vector_a,
                vector_b,
                0.0
            )
        )

    def test_tradeoff_does_not_dominate(self):

        vector_a = [
            1.0,
            2.0,
            -0.9,
            -0.7
        ]

        vector_b = [
            2.0,
            1.0,
            -0.8,
            -0.8
        ]

        self.assertFalse(
            objective_vector_dominates(
                vector_a,
                vector_b,
                0.0
            )
        )

    def test_tolerance_prevents_false_strict_improvement(self):

        vector_a = [
            1.0,
            1.0,
            1.0,
            1.0
        ]

        vector_b = [
            1.0 + 1e-13,
            1.0,
            1.0,
            1.0
        ]

        self.assertFalse(
            objective_vector_dominates(
                vector_a,
                vector_b,
                1e-12
            )
        )

    def test_exact_pareto_front(self):

        best = create_evaluation(
            0,
            [1.0, 1.0, -0.9, -0.9]
        )

        dominated = create_evaluation(
            1,
            [2.0, 2.0, -0.8, -0.8]
        )

        tradeoff = create_evaluation(
            2,
            [0.8, 3.0, -0.7, -0.95]
        )

        front = calculate_pareto_front(
            [
                best,
                dominated,
                tradeoff
            ],
            tolerance=0.0
        )

        self.assertEqual(
            len(front),
            2
        )

        self.assertIn(
            best,
            front
        )

        self.assertIn(
            tradeoff,
            front
        )


class TestTchebycheff(unittest.TestCase):

    def test_ideal_and_nadir(self):

        evaluation_a = create_evaluation(
            0,
            [1.0, 3.0, -0.9, -0.6]
        )

        evaluation_b = create_evaluation(
            1,
            [2.0, 1.0, -0.7, -0.8]
        )

        ideal, nadir = (
            calculate_ideal_and_nadir_points(
                [
                    evaluation_a,
                    evaluation_b
                ]
            )
        )

        self.assertEqual(
            ideal,
            [
                1.0,
                1.0,
                -0.9,
                -0.8
            ]
        )

        self.assertEqual(
            nadir,
            [
                2.0,
                3.0,
                -0.7,
                -0.6
            ]
        )

    def test_weight_count(self):

        with self.assertRaises(ValueError):

            validate_contextual_weights(
                [
                    0.5,
                    0.5
                ],
                1e-12
            )

    def test_negative_weight(self):

        with self.assertRaises(ValueError):

            validate_contextual_weights(
                [
                    0.4,
                    0.4,
                    0.3,
                    -0.1
                ],
                1e-12
            )

    def test_weight_sum(self):

        with self.assertRaises(ValueError):

            validate_contextual_weights(
                [
                    0.2,
                    0.2,
                    0.2,
                    0.2
                ],
                1e-12
            )

    def test_tchebycheff_score(self):

        score = calculate_tchebycheff_score(
            objective_vector=[
                2.0,
                1.0,
                -0.8,
                -0.7
            ],
            contextual_weights=[
                0.25,
                0.25,
                0.25,
                0.25
            ],
            ideal_point=[
                1.0,
                1.0,
                -0.9,
                -0.8
            ],
            nadir_point=[
                3.0,
                2.0,
                -0.7,
                -0.6
            ],
            epsilon=1e-12
        )

        # La plus grande distance pondérée
        # vaut environ 0.125.
        self.assertAlmostEqual(
            score,
            0.125,
            places=10
        )

    def test_tie_break_prefers_lower_far(self):

        evaluation_a = create_evaluation(
            0,
            [1.0, 1.0, -0.9, -0.8],
            far=0.02
        )

        evaluation_b = create_evaluation(
            4,
            [1.0, 1.0, -0.9, -0.8],
            far=0.01
        )

        selected, ideal, nadir, weights = (
            select_from_pareto_front(
                pareto_front=[
                    evaluation_a,
                    evaluation_b
                ],
                contextual_weights=[
                    0.25,
                    0.25,
                    0.25,
                    0.25
                ],
                epsilon=1e-12,
                score_tolerance=1e-12
            )
        )

        self.assertIs(
            selected,
            evaluation_b
        )

    def test_tie_break_prefers_lower_energy_after_far(self):

        evaluation_a = create_evaluation(
            0,
            [1.0, 1.0, -0.9, -0.8],
            far=0.01,
            energy=2.0
        )

        evaluation_b = create_evaluation(
            1,
            [1.0, 1.0, -0.9, -0.8],
            far=0.01,
            energy=1.0
        )

        self.assertLess(
            build_tie_break_key(evaluation_b),
            build_tie_break_key(evaluation_a)
        )

    def test_tie_break_prefers_lower_latency_after_far_and_energy(self):

        evaluation_a = create_evaluation(
            0,
            [1.0, 1.0, -0.9, -0.8],
            far=0.01,
            energy=1.0,
            latency=0.5
        )

        evaluation_b = create_evaluation(
            1,
            [1.0, 1.0, -0.9, -0.8],
            far=0.01,
            energy=1.0,
            latency=0.1
        )

        self.assertLess(
            build_tie_break_key(evaluation_b),
            build_tie_break_key(evaluation_a)
        )

    def test_tie_break_final_lexicographic_by_name(self):

        # Même FAR, même énergie, même latence : seul l'ordre
        # lexicographique du nom de la décision (A1-K0 avant
        # A1-K1a) doit départager.
        evaluation_a = create_evaluation(
            1,
            [1.0, 1.0, -0.9, -0.8],
            far=0.01,
            energy=1.0,
            latency=0.2
        )

        evaluation_b = create_evaluation(
            0,
            [1.0, 1.0, -0.9, -0.8],
            far=0.01,
            energy=1.0,
            latency=0.2
        )

        self.assertLess(
            build_tie_break_key(evaluation_b),
            build_tie_break_key(evaluation_a)
        )

    # --------------------------------------------------------
    # STEP8 -- tests de non-régression pour la correction de
    # calculate_tchebycheff_score (epsilon utilisé comme seuil
    # de span dégénéré, plus comme terme de lissage systématique
    # sur les quatre dimensions). Voir STEP8_OFFICIAL/
    # 01_CODE_AUDIT/STEP8_PARETO_TCHEBYCHEFF_DIAGNOSTIC.md pour
    # la démonstration chiffrée qui motive ces tests.
    # --------------------------------------------------------

    def test_normalization_zero_span_contributes_zero(self):

        # Deux dimensions à span nul (ideal == nadir) : leur
        # contribution doit être exactement 0, jamais une
        # division par une quantité quasi nulle.
        score = calculate_tchebycheff_score(
            objective_vector=[0.2, 0.005, -0.95, -0.92],
            contextual_weights=[0.25, 0.25, 0.25, 0.25],
            ideal_point=[0.2, 0.005, -1.0, -0.98],
            nadir_point=[0.2, 0.005, -0.9, -0.90],
            epsilon=1e-12
        )

        expected = max(
            0.25 * (-0.95 - (-1.0)) / (-0.9 - (-1.0)),
            0.25 * (-0.92 - (-0.98)) / (-0.90 - (-0.98))
        )

        self.assertAlmostEqual(
            score,
            expected,
            places=12
        )

    def test_epsilon_does_not_break_genuine_tie(self):

        # Deux décisions non dominées, chacune "pire" sur une
        # seule dimension de spans différents (0,20 vs 0,005) :
        # sous poids égaux, leur score de Tchebycheff pur vaut
        # exactement 0,25 des deux côtés. Avant STEP8, l'ancienne
        # formule (epsilon ajouté systématiquement au
        # dénominateur) cassait cette égalité en favorisant la
        # dimension au plus petit span -- un artefact sans lien
        # avec la modélisation (DM-EQ107 ne mentionne aucun
        # critère de "span"). Ce test échouerait avec l'ancienne
        # formule et confirme que la correction restaure
        # l'égalité mathématique réelle.
        ideal = [0.10, 0.001, -1.0, -1.0]
        nadir = [0.30, 0.006, -1.0, -1.0]
        weights = [0.25, 0.25, 0.25, 0.25]

        score_wide_span = calculate_tchebycheff_score(
            objective_vector=[0.30, 0.001, -1.0, -1.0],
            contextual_weights=weights,
            ideal_point=ideal,
            nadir_point=nadir,
            epsilon=1e-12
        )

        score_narrow_span = calculate_tchebycheff_score(
            objective_vector=[0.10, 0.006, -1.0, -1.0],
            contextual_weights=weights,
            ideal_point=ideal,
            nadir_point=nadir,
            epsilon=1e-12
        )

        self.assertEqual(
            score_wide_span,
            0.25
        )

        self.assertEqual(
            score_narrow_span,
            0.25
        )

        self.assertEqual(
            score_wide_span,
            score_narrow_span
        )

    def test_structural_tie_reaches_documented_tie_break(self):

        # Bout en bout, via select_from_pareto_front() : sur le
        # front à 2 membres structurellement à égalité décrit
        # ci-dessus, la décision retenue doit être celle que
        # désigne le tie-break documenté (DM-EQ107 : FAR puis
        # énergie), pas celle dont le "pire" objectif a le plus
        # petit span sur le front (biais de l'ancienne formule).
        evaluation_wide_span_low_energy = create_evaluation(
            0,
            [0.30, 0.001, -1.0, -1.0],
            far=0.01,
            energy=0.12,
            latency=0.001
        )

        evaluation_narrow_span_high_energy = create_evaluation(
            1,
            [0.10, 0.006, -1.0, -1.0],
            far=0.01,
            energy=0.30,
            latency=0.006
        )

        (
            selected,
            ideal_point,
            nadir_point,
            validated_weights
        ) = select_from_pareto_front(
            pareto_front=[
                evaluation_wide_span_low_energy,
                evaluation_narrow_span_high_energy
            ],
            contextual_weights=[0.25, 0.25, 0.25, 0.25],
            epsilon=1e-12,
            score_tolerance=1e-12
        )

        self.assertIs(
            selected,
            evaluation_wide_span_low_energy
        )


class TestCompleteDecisionMaker(unittest.TestCase):

    def test_missing_weights_are_rejected(self):

        parameters = create_test_parameters()
        parameters.contextual_weights = None

        with self.assertRaises(ValueError):

            run_decision_maker(
                context=create_test_context(),
                parameters=parameters,
                rho_ab=0.8
            )

    def test_refusal_when_no_decision_is_admissible(self):

        parameters = create_test_parameters()

        # Aucun profil RFF et aucune énergie disponible.
        context = create_test_context(
            rff_profile_available=False,
            battery_energy_j=(
                parameters.minimum_battery_energy_j
            )
        )

        result = run_decision_maker(
            context=context,
            parameters=parameters,
            rho_ab=0.8,
            variation_feasible=True
        )

        self.assertTrue(
            result.refusal_of_service
        )

        self.assertIsNone(
            result.selected_evaluation
        )

    def test_integrated_selection_with_mocked_submodels(self):

        parameters = create_test_parameters()

        context = create_test_context(
            renewal_required=False
        )

        def fake_authentication(
            authentication_action,
            parameters,
            mallory_snr_db=None
        ):

            if (
                authentication_action
                == AuthenticationAction.A1
            ):

                return create_authentication_metrics(
                    action=AuthenticationAction.A1,
                    far=0.001,
                    robustness=0.999
                )

            return create_authentication_metrics(
                action=AuthenticationAction.A2,
                far=0.01,
                robustness=0.99
            )

        def fake_key(
            key_action,
            parameters,
            rho_ab=None,
            key_age_s=0.0,
            messages_with_current_key=0,
            compromise_suspected=False,
            variation_feasible=None,
            collected_measurements=0,
            candidate_ready=False
        ):

            return create_key_metrics(
                action=key_action,
                key_quality=0.8
            )

        def fake_cost(
            decision,
            authentication_metrics,
            key_metrics,
            context,
            parameters,
            k2_protocol=None
        ):

            if (
                decision.authentication_action
                == AuthenticationAction.A1
            ):

                return create_cost_metrics(
                    expected_energy_j=2.0,
                    normalized_latency=0.2
                )

            return create_cost_metrics(
                expected_energy_j=1.0,
                normalized_latency=0.2
            )

        with patch(
            "physec_dm.decision_maker."
            "calculate_authentication_metrics",
            side_effect=fake_authentication
        ):

            with patch(
                "physec_dm.decision_maker."
                "calculate_key_metrics",
                side_effect=fake_key
            ):

                with patch(
                    "physec_dm.decision_maker."
                    "build_cost_metrics",
                    side_effect=fake_cost
                ):

                    result = run_decision_maker(
                        context=context,
                        parameters=parameters,
                        rho_ab=0.8
                    )

        self.assertFalse(
            result.refusal_of_service
        )

        # ----------------------------------------------------
        # STEP8 -- valeur attendue corrigée de "A2-K0" vers
        # "A1-K0", avec justification complète (règle absolue :
        # ne jamais changer un test uniquement pour faire passer
        # la suite).
        #
        # Avec renewal_required=False, seule K0 est admissible
        # (DM-EQ95) : les deux candidats sont donc A1-K0
        # (far=0.001, énergie=2.0, robustesse=0.999) et A2-K0
        # (far=0.01, énergie=1.0, robustesse=0.99), non dominés
        # l'un par l'autre (A1 meilleur en authentification,
        # A2 meilleur en énergie ; latence et qualité de clé
        # identiques -> span nul sur ces deux dimensions).
        #
        # Sous la formule PURE de Tchebycheff (poids égaux),
        # A1 est le pire du front uniquement sur l'énergie
        # (span=1.0) et A2 uniquement sur l'authentification
        # (span=0.009) : les deux scores valent alors
        # EXACTEMENT 0.25, un vrai bris d'égalité qui doit
        # passer par build_tie_break_key (DM-EQ107 :
        # FAR -> énergie -> latence -> nom). A1 a la FAR la plus
        # faible (0.001 < 0.01) et doit donc gagner : "A1-K0".
        #
        # Avant la correction STEP8, l'ancienne formule (epsilon
        # ajouté au dénominateur des quatre dimensions) rompait
        # cette égalité au profit de A2 -- un artefact numérique
        # dépendant du span de chaque objectif, sans lien avec
        # DM-EQ107, démontré et chiffré dans STEP8_OFFICIAL/
        # 01_CODE_AUDIT/STEP8_PARETO_TCHEBYCHEFF_DIAGNOSTIC.md.
        # "A2-K0" était donc la trace d'un bug, pas un
        # comportement validé : ce test devient un test de
        # non-régression pour le comportement corrigé.
        self.assertEqual(
            result.selected_evaluation.decision.get_name(),
            "A1-K0"
        )


if __name__ == "__main__":

    unittest.main()
