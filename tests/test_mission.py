# unittest est l'outil de test fourni avec Python.
import unittest


# patch permet de remplacer temporairement
# les sous-modèles pendant les tests.
from unittest.mock import patch


import numpy as np


from physec_dm.models import (
    AuthenticationAction,
    AuthenticationMetrics,
    ChannelMetrics,
    Decision,
    DecisionEvaluation,
    DecisionMakerResult,
    KeyAction,
    KeyMetrics,
    MissionState
)

from physec_dm.parameters import Parameters

from physec_dm.mission import (
    calculate_key_context_metrics,
    calculate_rate,
    calculate_realized_alice_costs,
    create_initial_mission_state,
    create_mission_context,
    create_next_key_identifier,
    create_random_generator,
    draw_bernoulli,
    draw_observed_snr_db,
    evaluate_mallory,
    get_trace_value,
    run_mission,
    run_mission_step,
    update_duty_cycle_budget,
    update_key_state,
    validate_probability
)


# Cette fonction crée des paramètres complets
# uniquement pour les tests de mission.
def create_test_parameters():

    parameters = Parameters()

    parameters.mean_snr_db = 5.0
    parameters.shadowing_std_db = 0.0

    parameters.critical_message_probability = 0.0
    parameters.mallory_attempt_probability = 0.0

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


def create_state(
    battery_energy_j=28512.0,
    key_age_s=0.0,
    messages_with_current_key=0
):

    return MissionState(
        step_index=0,
        time_s=0.0,
        battery_energy_j=battery_energy_j,
        key_age_s=key_age_s,
        messages_with_current_key=(
            messages_with_current_key
        ),
        current_key_identifier="KEY-001",
        remaining_duty_cycle_airtime_s=10.0
    )


def create_channel_metrics():

    return ChannelMetrics(
        snr_db=5.0,
        snr_linear=3.1622776602,
        doppler_hz=0.0,
        temporal_correlation=1.0,
        noise_correlation=0.75,
        rho_ab=0.70
    )


def create_authentication_metrics(
    action=AuthenticationAction.A1,
    far=0.001,
    frr=0.0,
    total_false_acceptance=0.001
):

    return AuthenticationMetrics(
        authentication_action=action,
        far=far,
        frr=frr,
        mac_forgery_probability=2 ** (-64),
        total_false_acceptance_probability=(
            total_false_acceptance
        ),
        authentication_robustness=(
            1.0 - total_false_acceptance
        ),
        alice_fallback_probability=frr,
        mallory_fallback_probability=(
            1.0 - far
            if action == AuthenticationAction.A2
            else 0.0
        )
    )


def create_key_metrics(
    action=KeyAction.K0,
    renewal_required=False,
    key_expired=False
):

    return KeyMetrics(
        key_action=action,
        raw_kdr=None,
        effective_kdr=None,
        binary_entropy=None,
        reconciliation_yield=None,
        required_measurements=None,
        agreement_feasible=None,
        variation_feasible=None,
        phy_feasible=None,
        key_aging_index=0.2,
        renewal_required=renewal_required,
        key_expired=key_expired,
        key_deadline_s=100.0,
        key_quality=0.8
    )


def create_selected_evaluation(
    authentication_action=AuthenticationAction.A1,
    key_action=KeyAction.K0,
    authentication_metrics=None,
    key_metrics=None
):

    decision = Decision(
        authentication_action,
        key_action
    )

    evaluation = DecisionEvaluation(
        decision
    )

    if authentication_metrics is None:

        authentication_metrics = (
            create_authentication_metrics(
                action=authentication_action
            )
        )

    if key_metrics is None:

        key_metrics = create_key_metrics(
            action=key_action
        )

    evaluation.authentication_metrics = (
        authentication_metrics
    )

    evaluation.key_metrics = key_metrics
    evaluation.admissible = True

    return evaluation


def create_decision_result(
    context,
    selected_evaluation
):

    return DecisionMakerResult(
        context=context,
        all_evaluations=[
            selected_evaluation
        ],
        admissible_evaluations=[
            selected_evaluation
        ],
        pareto_front=[
            selected_evaluation
        ],
        rejection_journal=[],
        contextual_weights=[
            0.25,
            0.25,
            0.25,
            0.25
        ],
        ideal_point=[
            0.0,
            0.0,
            -1.0,
            -1.0
        ],
        nadir_point=[
            1.0,
            1.0,
            0.0,
            0.0
        ],
        selected_evaluation=(
            selected_evaluation
        ),
        refusal_of_service=False,
        fallback_mode_used=None,
        explanation="Décision de test."
    )


class FixedRandomGenerator:

    # Cette classe simple retourne toujours
    # la même valeur pour random().
    def __init__(self, random_value):

        self.random_value = random_value

    def random(self):

        return self.random_value


class TestRandomTools(unittest.TestCase):

    def test_invalid_probability(self):

        with self.assertRaises(ValueError):

            validate_probability(
                1.2,
                "p"
            )

    def test_seed_is_reproducible(self):

        generator_a = create_random_generator(
            123
        )

        generator_b = create_random_generator(
            123
        )

        self.assertEqual(
            generator_a.random(),
            generator_b.random()
        )

    def test_bernoulli_true(self):

        generator = FixedRandomGenerator(
            0.1
        )

        self.assertTrue(
            draw_bernoulli(
                0.2,
                generator
            )
        )

    def test_bernoulli_false(self):

        generator = FixedRandomGenerator(
            0.3
        )

        self.assertFalse(
            draw_bernoulli(
                0.2,
                generator
            )
        )

    def test_deterministic_snr(self):

        parameters = create_test_parameters()

        generator = create_random_generator(
            1
        )

        self.assertEqual(
            draw_observed_snr_db(
                parameters,
                generator
            ),
            5.0
        )


class TestInitialStateAndContext(unittest.TestCase):

    def test_initial_state(self):

        parameters = create_test_parameters()

        state = create_initial_mission_state(
            parameters,
            initial_duty_cycle_airtime_s=10.0
        )

        self.assertEqual(
            state.step_index,
            0
        )

        self.assertEqual(
            state.battery_energy_j,
            parameters.initial_battery_energy_j
        )

        self.assertEqual(
            state.current_key_identifier,
            "KEY-001"
        )

    def test_expired_key_forces_renewal(self):

        state = create_state()

        key_metrics = create_key_metrics(
            renewal_required=False,
            key_expired=True
        )

        context = create_mission_context(
            state=state,
            channel_metrics=create_channel_metrics(),
            criticality=0,
            rff_profile_available=True,
            compromise_suspected=True,
            key_context_metrics=key_metrics
        )

        self.assertTrue(
            context.renewal_required
        )

        self.assertTrue(
            context.key_expired
        )

    def test_key_context_uses_k0(self):

        parameters = create_test_parameters()

        expected_metrics = create_key_metrics()

        with patch(
            "physec_dm.mission.calculate_key_metrics",
            return_value=expected_metrics
        ) as mocked_function:

            returned_metrics = (
                calculate_key_context_metrics(
                    state=create_state(),
                    parameters=parameters,
                    compromise_suspected=False
                )
            )

        self.assertIs(
            returned_metrics,
            expected_metrics
        )

        self.assertEqual(
            mocked_function.call_args.kwargs[
                "key_action"
            ],
            KeyAction.K0
        )


class TestRealizedAliceCosts(unittest.TestCase):

    def test_no_selected_decision_has_zero_cost(self):

        costs = calculate_realized_alice_costs(
            selected_evaluation=None,
            parameters=create_test_parameters(),
            random_generator=FixedRandomGenerator(
                0.0
            )
        )

        self.assertEqual(
            costs["energy_j"],
            0.0
        )

    def test_a1_uses_deterministic_cost(self):

        evaluation = create_selected_evaluation(
            authentication_action=(
                AuthenticationAction.A1
            )
        )

        with patch(
            "physec_dm.mission.calculate_base_energy",
            return_value=1.0
        ):

            with patch(
                "physec_dm.mission."
                "calculate_authentication_costs",
                return_value={
                    "expected_energy_j": 2.0,
                    "worst_case_energy_j": 2.0,
                    "expected_latency_s": 0.1,
                    "worst_case_latency_s": 0.1,
                    "worst_case_airtime_s": 0.4
                }
            ):

                with patch(
                    "physec_dm.mission.calculate_key_costs",
                    return_value={
                        "energy_j": 3.0,
                        "latency_s": 0.0,
                        "airtime_s": 0.2
                    }
                ):

                    costs = (
                        calculate_realized_alice_costs(
                            evaluation,
                            create_test_parameters(),
                            FixedRandomGenerator(
                                0.9
                            )
                        )
                    )

        self.assertEqual(
            costs["energy_j"],
            6.0
        )

        self.assertAlmostEqual(
            costs["airtime_s"],
            0.6
        )

    def test_a2_without_fallback_has_no_auth_energy(self):

        authentication_metrics = (
            create_authentication_metrics(
                action=AuthenticationAction.A2,
                frr=0.05
            )
        )

        evaluation = create_selected_evaluation(
            authentication_action=(
                AuthenticationAction.A2
            ),
            authentication_metrics=(
                authentication_metrics
            )
        )

        with patch(
            "physec_dm.mission.calculate_base_energy",
            return_value=1.0
        ):

            with patch(
                "physec_dm.mission."
                "calculate_authentication_costs",
                return_value={
                    "expected_energy_j": 0.1,
                    "worst_case_energy_j": 2.0,
                    "expected_latency_s": 0.1,
                    "worst_case_latency_s": 4.0,
                    "worst_case_airtime_s": 0.4
                }
            ):

                with patch(
                    "physec_dm.mission.calculate_key_costs",
                    return_value={
                        "energy_j": 3.0,
                        "latency_s": 0.0,
                        "airtime_s": 0.2
                    }
                ):

                    costs = (
                        calculate_realized_alice_costs(
                            evaluation,
                            create_test_parameters(),
                            FixedRandomGenerator(
                                0.9
                            )
                        )
                    )

        self.assertEqual(
            costs["energy_j"],
            4.0
        )

        self.assertEqual(
            costs["airtime_s"],
            0.2
        )

        self.assertFalse(
            costs[
                "alice_fallback_triggered"
            ]
        )

    def test_a2_with_fallback_uses_worst_case(self):

        authentication_metrics = (
            create_authentication_metrics(
                action=AuthenticationAction.A2,
                frr=0.05
            )
        )

        evaluation = create_selected_evaluation(
            authentication_action=(
                AuthenticationAction.A2
            ),
            authentication_metrics=(
                authentication_metrics
            )
        )

        with patch(
            "physec_dm.mission.calculate_base_energy",
            return_value=1.0
        ):

            with patch(
                "physec_dm.mission."
                "calculate_authentication_costs",
                return_value={
                    "expected_energy_j": 0.1,
                    "worst_case_energy_j": 2.0,
                    "expected_latency_s": 0.1,
                    "worst_case_latency_s": 4.0,
                    "worst_case_airtime_s": 0.4
                }
            ):

                with patch(
                    "physec_dm.mission.calculate_key_costs",
                    return_value={
                        "energy_j": 3.0,
                        "latency_s": 0.0,
                        "airtime_s": 0.2
                    }
                ):

                    costs = (
                        calculate_realized_alice_costs(
                            evaluation,
                            create_test_parameters(),
                            FixedRandomGenerator(
                                0.01
                            )
                        )
                    )

        self.assertEqual(
            costs["energy_j"],
            6.0
        )

        self.assertAlmostEqual(
            costs["airtime_s"],
            0.6
        )

        self.assertTrue(
            costs[
                "alice_fallback_triggered"
            ]
        )


class TestMallory(unittest.TestCase):

    def test_no_attack_is_not_accepted(self):

        result = evaluate_mallory(
            selected_evaluation=(
                create_selected_evaluation()
            ),
            real_snr_db=5.0,
            parameters=create_test_parameters(),
            random_generator=(
                FixedRandomGenerator(0.0)
            ),
            mallory_attempted=False
        )

        self.assertFalse(
            result["accepted"]
        )

    def test_mallory_uses_total_false_acceptance(self):

        evaluation = create_selected_evaluation(
            authentication_action=(
                AuthenticationAction.A2
            )
        )

        real_metrics = (
            create_authentication_metrics(
                action=AuthenticationAction.A2,
                far=0.10,
                total_false_acceptance=0.20
            )
        )

        with patch(
            "physec_dm.mission."
            "calculate_authentication_metrics",
            return_value=real_metrics
        ):

            result = evaluate_mallory(
                selected_evaluation=evaluation,
                real_snr_db=5.0,
                parameters=create_test_parameters(),
                random_generator=(
                    FixedRandomGenerator(0.15)
                ),
                mallory_attempted=True
            )

        self.assertTrue(
            result["accepted"]
        )


class TestKeyAndDutyCycleUpdates(unittest.TestCase):

    def test_next_key_identifier(self):

        self.assertEqual(
            create_next_key_identifier(
                "KEY-009"
            ),
            "KEY-010"
        )

    def test_k0_increments_age_and_messages(self):

        updated = update_key_state(
            previous_key_age_s=60.0,
            previous_message_count=2,
            current_key_identifier="KEY-001",
            key_action=KeyAction.K0,
            legitimate_message_served=True,
            message_period_s=60.0
        )

        self.assertEqual(
            updated["key_age_s"],
            120.0
        )

        self.assertEqual(
            updated[
                "messages_with_current_key"
            ],
            3
        )

        self.assertFalse(
            updated["key_renewed"]
        )

    def test_renewal_resets_key(self):

        updated = update_key_state(
            previous_key_age_s=600.0,
            previous_message_count=10,
            current_key_identifier="KEY-001",
            key_action=KeyAction.K2,
            legitimate_message_served=True,
            message_period_s=60.0
        )

        self.assertEqual(
            updated["key_age_s"],
            0.0
        )

        self.assertEqual(
            updated[
                "messages_with_current_key"
            ],
            0
        )

        self.assertEqual(
            updated[
                "current_key_identifier"
            ],
            "KEY-002"
        )

    def test_refusal_only_ages_key(self):

        updated = update_key_state(
            previous_key_age_s=60.0,
            previous_message_count=2,
            current_key_identifier="KEY-001",
            key_action=None,
            legitimate_message_served=False,
            message_period_s=60.0
        )

        self.assertEqual(
            updated["key_age_s"],
            120.0
        )

        self.assertEqual(
            updated[
                "messages_with_current_key"
            ],
            2
        )

    def test_duty_cycle_is_recharged_and_capped(self):

        updated = update_duty_cycle_budget(
            current_airtime_s=5.0,
            used_airtime_s=2.0,
            recharge_airtime_s=4.0,
            maximum_airtime_s=6.0
        )

        self.assertEqual(
            updated,
            6.0
        )


class TestRatesAndTraces(unittest.TestCase):

    def test_zero_denominator_is_undefined(self):

        self.assertIsNone(
            calculate_rate(
                0,
                0
            )
        )

    def test_rate(self):

        self.assertEqual(
            calculate_rate(
                2,
                4
            ),
            0.5
        )

    def test_trace_value(self):

        self.assertEqual(
            get_trace_value(
                [3, 4],
                1,
                "trace"
            ),
            4
        )

    def test_short_trace_is_rejected(self):

        with self.assertRaises(ValueError):

            get_trace_value(
                [3],
                1,
                "trace"
            )


class TestMissionStep(unittest.TestCase):

    def test_step_does_not_debit_alice_for_mallory(self):

        parameters = create_test_parameters()
        state = create_state()

        channel_metrics = create_channel_metrics()

        key_context_metrics = create_key_metrics()

        selected_evaluation = (
            create_selected_evaluation()
        )

        context = create_mission_context(
            state=state,
            channel_metrics=channel_metrics,
            criticality=0,
            rff_profile_available=True,
            compromise_suspected=False,
            key_context_metrics=(
                key_context_metrics
            )
        )

        decision_result = create_decision_result(
            context,
            selected_evaluation
        )

        with patch(
            "physec_dm.mission.calculate_channel_metrics",
            return_value=channel_metrics
        ):

            with patch(
                "physec_dm.mission."
                "calculate_key_context_metrics",
                return_value=key_context_metrics
            ):

                with patch(
                    "physec_dm.mission.run_decision_maker",
                    return_value=decision_result
                ):

                    with patch(
                        "physec_dm.mission."
                        "calculate_realized_alice_costs",
                        return_value={
                            "energy_j": 2.0,
                            "airtime_s": 0.5,
                            "alice_fallback_triggered": False
                        }
                    ):

                        with patch(
                            "physec_dm.mission.evaluate_mallory",
                            return_value={
                                "accepted": True,
                                "authentication_metrics": (
                                    create_authentication_metrics()
                                )
                            }
                        ):

                            with patch(
                                "physec_dm.mission."
                                "calculate_authentication_metrics",
                                return_value=(
                                    create_authentication_metrics()
                                )
                            ):

                                step_result = run_mission_step(
                                    state=state,
                                    parameters=parameters,
                                    random_generator=(
                                        FixedRandomGenerator(0.0)
                                    ),
                                    maximum_duty_cycle_airtime_s=10.0,
                                    duty_cycle_recharge_s=0.0,
                                    observed_snr_db=5.0,
                                    real_snr_db=5.0,
                                    criticality=0,
                                    mallory_attempted=True
                                )

        # L'énergie reste exactement celle d'Alice.
        self.assertEqual(
            step_result.energy_debited_from_alice_j,
            2.0
        )

        self.assertEqual(
            step_result.state_after.false_acceptances,
            1
        )

        self.assertEqual(
            step_result.state_after.battery_energy_j,
            state.battery_energy_j - 2.0
        )

    def test_refusal_counts_legitimate_refusal(self):

        parameters = create_test_parameters()
        state = create_state()

        channel_metrics = create_channel_metrics()
        key_context_metrics = create_key_metrics()

        context = create_mission_context(
            state=state,
            channel_metrics=channel_metrics,
            criticality=0,
            rff_profile_available=True,
            compromise_suspected=False,
            key_context_metrics=key_context_metrics
        )

        refusal_result = DecisionMakerResult(
            context=context,
            all_evaluations=[],
            admissible_evaluations=[],
            pareto_front=[],
            rejection_journal=[],
            contextual_weights=[
                0.25,
                0.25,
                0.25,
                0.25
            ],
            ideal_point=None,
            nadir_point=None,
            selected_evaluation=None,
            refusal_of_service=True,
            fallback_mode_used="refuse",
            explanation="Refus."
        )

        with patch(
            "physec_dm.mission.calculate_channel_metrics",
            return_value=channel_metrics
        ):

            with patch(
                "physec_dm.mission."
                "calculate_key_context_metrics",
                return_value=key_context_metrics
            ):

                with patch(
                    "physec_dm.mission.run_decision_maker",
                    return_value=refusal_result
                ):

                    step_result = run_mission_step(
                        state=state,
                        parameters=parameters,
                        random_generator=(
                            FixedRandomGenerator(0.9)
                        ),
                        maximum_duty_cycle_airtime_s=10.0,
                        duty_cycle_recharge_s=0.0,
                        observed_snr_db=5.0,
                        criticality=0,
                        mallory_attempted=False
                    )

        self.assertFalse(
            step_result.legitimate_message_served
        )

        self.assertEqual(
            step_result.state_after.legitimate_refusals,
            1
        )

        self.assertEqual(
            step_result.energy_debited_from_alice_j,
            0.0
        )


class TestCompleteMission(unittest.TestCase):

    def test_three_step_mission_metrics(self):

        parameters = create_test_parameters()

        states = [
            MissionState(
                step_index=1,
                time_s=60.0,
                battery_energy_j=28510.0,
                key_age_s=60.0,
                messages_with_current_key=1,
                current_key_identifier="KEY-001",
                remaining_duty_cycle_airtime_s=10.0,
                legitimate_messages=1,
                served_messages=1,
                legitimate_refusals=0,
                mallory_attempts=1,
                false_acceptances=0,
                critical_mallory_attempts=0,
                critical_false_acceptances=0,
                security_floor_violations=0
            ),
            MissionState(
                step_index=2,
                time_s=120.0,
                battery_energy_j=28508.0,
                key_age_s=120.0,
                messages_with_current_key=2,
                current_key_identifier="KEY-001",
                remaining_duty_cycle_airtime_s=10.0,
                legitimate_messages=2,
                served_messages=1,
                legitimate_refusals=1,
                mallory_attempts=1,
                false_acceptances=0,
                critical_mallory_attempts=0,
                critical_false_acceptances=0,
                security_floor_violations=0
            ),
            MissionState(
                step_index=3,
                time_s=180.0,
                battery_energy_j=28506.0,
                key_age_s=180.0,
                messages_with_current_key=3,
                current_key_identifier="KEY-001",
                remaining_duty_cycle_airtime_s=10.0,
                legitimate_messages=3,
                served_messages=2,
                legitimate_refusals=1,
                mallory_attempts=2,
                false_acceptances=1,
                critical_mallory_attempts=1,
                critical_false_acceptances=1,
                security_floor_violations=1
            )
        ]

        selected = create_selected_evaluation()

        context = create_mission_context(
            state=create_state(),
            channel_metrics=create_channel_metrics(),
            criticality=0,
            rff_profile_available=True,
            compromise_suspected=False,
            key_context_metrics=create_key_metrics()
        )

        decision_result = create_decision_result(
            context,
            selected
        )

        step_results = []

        for index in range(3):

            step_results.append(
                type(
                    "SimpleStep",
                    (),
                    {
                        "state_after": states[index],
                        "decision_maker_result": decision_result
                    }
                )()
            )

        with patch(
            "physec_dm.mission.run_mission_step",
            side_effect=step_results
        ):

            result = run_mission(
                parameters=parameters,
                seed=123,
                max_steps=3,
                observed_snr_trace=[
                    5.0,
                    5.0,
                    5.0
                ],
                criticality_trace=[
                    0,
                    0,
                    1
                ],
                mallory_trace=[
                    True,
                    False,
                    True
                ]
            )

        self.assertEqual(
            result.lifetime_s,
            180.0
        )

        self.assertEqual(
            result.false_acceptance_rate,
            0.5
        )

        self.assertEqual(
            result.critical_false_acceptance_rate,
            1.0
        )

        self.assertAlmostEqual(
            result.legitimate_refusal_rate,
            1.0 / 3.0
        )

        self.assertEqual(
            result.security_floor_violation_rate,
            0.5
        )

        self.assertEqual(
            result.decision_counts,
            {
                "A1-K0": 3
            }
        )

        self.assertEqual(
            result.stop_reason,
            "maximum_steps"
        )

        self.assertTrue(
            result.censored
        )


if __name__ == "__main__":

    unittest.main()
