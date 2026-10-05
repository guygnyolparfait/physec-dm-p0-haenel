import math
import unittest


from types import SimpleNamespace


from scripts.run_three_scenarios import (
    build_four_objective_summary_rows,
    build_per_mission_objective_rows,
    calculate_error_bar,
    extract_selected_step_metrics,
    safe_mean,
    summarize_values
)

# Cette classe de test utilise les véritables classes
# de models.py, et non des SimpleNamespace, afin de vérifier
# que run_three_scenarios.py reste compatible avec la structure
# réelle produite par mission.py.
from physec_dm.models import (
    AuthenticationAction,
    AuthenticationMetrics,
    ChannelMetrics,
    Context,
    CostMetrics,
    Decision,
    DecisionEvaluation,
    DecisionMakerResult,
    KeyAction,
    KeyMetrics,
    MissionState,
    MissionStepResult
)


def create_selected_step(
    energy=1.0,
    latency=0.2,
    authentication=0.9,
    key_quality=0.8,
    decision_name="A2-K1a",
    step_index=0
):

    decision = SimpleNamespace(
        get_name=lambda: decision_name
    )

    authentication_metrics = SimpleNamespace(
        authentication_robustness=(
            authentication
        )
    )

    key_metrics = SimpleNamespace(
        key_quality=key_quality
    )

    cost_metrics = SimpleNamespace(
        expected_energy_j=energy,
        normalized_latency=latency,
        authentication_latency_s=0.1,
        key_latency_s=1.0
    )

    selected_evaluation = SimpleNamespace(
        decision=decision,
        authentication_metrics=(
            authentication_metrics
        ),
        key_metrics=key_metrics,
        cost_metrics=cost_metrics
    )

    decision_maker_result = SimpleNamespace(
        selected_evaluation=(
            selected_evaluation
        ),
        pareto_front=[
            selected_evaluation
        ]
    )

    context = SimpleNamespace(
        step_index=step_index,
        criticality=0
    )

    channel_metrics = SimpleNamespace(
        snr_db=5.0
    )

    return SimpleNamespace(
        decision_maker_result=(
            decision_maker_result
        ),
        context=context,
        channel_metrics=channel_metrics,
        state_before=SimpleNamespace(
            step_index=step_index
        ),
        state_after=SimpleNamespace(
            step_index=step_index + 1
        )
    )


def create_refused_step(
    step_index=0
):

    return SimpleNamespace(
        decision_maker_result=SimpleNamespace(
            selected_evaluation=None,
            pareto_front=[]
        ),
        context=SimpleNamespace(
            step_index=step_index,
            criticality=0
        ),
        channel_metrics=SimpleNamespace(
            snr_db=-10.0
        ),
        state_before=SimpleNamespace(
            step_index=step_index
        ),
        state_after=SimpleNamespace(
            step_index=step_index + 1
        )
    )


def create_mission(
    scenario_id,
    seed,
    steps
):

    return SimpleNamespace(
        parameters_snapshot={
            "scenario_id": scenario_id
        },
        policy_id="P0",
        seed=seed,
        steps=steps,
        legitimate_refusal_rate=0.0,
        false_acceptance_rate=0.0,
        security_floor_violation_rate=0.0,
        censored=True,
        stop_reason="max_steps"
    )


class TestStepExtraction(unittest.TestCase):

    def test_selected_step_is_extracted(self):

        row = extract_selected_step_metrics(
            step_result=(
                create_selected_step()
            ),
            scenario_id="S1",
            policy_id="P0",
            seed=1
        )

        self.assertEqual(
            row["decision_name"],
            "A2-K1a"
        )

        self.assertEqual(
            row["energy_objective_j"],
            1.0
        )

        self.assertEqual(
            row["authentication_robustness"],
            0.9
        )

    def test_refused_step_returns_none(self):

        row = extract_selected_step_metrics(
            step_result=(
                create_refused_step()
            ),
            scenario_id="S1",
            policy_id="P0",
            seed=1
        )

        self.assertIsNone(
            row
        )


class TestStatistics(unittest.TestCase):

    def test_safe_mean(self):

        self.assertEqual(
            safe_mean(
                [
                    1.0,
                    None,
                    3.0
                ]
            ),
            2.0
        )

    def test_safe_mean_none(self):

        self.assertIsNone(
            safe_mean(
                [
                    None,
                    None
                ]
            )
        )

    def test_summary_of_two_values(self):

        summary = summarize_values(
            [
                1.0,
                3.0
            ]
        )

        self.assertEqual(
            summary["count"],
            2
        )

        self.assertEqual(
            summary["mean"],
            2.0
        )

        self.assertGreater(
            summary["ci95_high"],
            summary["mean"]
        )

    def test_summary_of_empty_values(self):

        summary = summarize_values(
            [
                None
            ]
        )

        self.assertEqual(
            summary["count"],
            0
        )

        self.assertIsNone(
            summary["mean"]
        )


class TestMissionAndScenarioSummary(unittest.TestCase):

    def test_per_mission_means(self):

        mission = create_mission(
            scenario_id="S1",
            seed=1,
            steps=[
                create_selected_step(
                    energy=1.0
                ),
                create_selected_step(
                    energy=3.0,
                    step_index=1
                )
            ]
        )

        campaign = SimpleNamespace(
            mission_results=[
                mission
            ]
        )

        rows = build_per_mission_objective_rows(
            campaign
        )

        self.assertEqual(
            len(rows),
            1
        )

        self.assertEqual(
            rows[0][
                "mean_energy_objective_j"
            ],
            2.0
        )

        self.assertEqual(
            rows[0]["selection_rate"],
            1.0
        )

    def test_refusal_reduces_selection_rate(self):

        mission = create_mission(
            scenario_id="S1",
            seed=1,
            steps=[
                create_selected_step(),
                create_refused_step(
                    step_index=1
                )
            ]
        )

        campaign = SimpleNamespace(
            mission_results=[
                mission
            ]
        )

        rows = build_per_mission_objective_rows(
            campaign
        )

        self.assertEqual(
            rows[0]["selection_rate"],
            0.5
        )

    def test_four_objective_summary(self):

        per_mission_rows = [
            {
                "scenario_id": "S1",
                "mean_energy_objective_j": 1.0,
                "mean_normalized_latency_objective": 0.2,
                "mean_authentication_robustness": 0.8,
                "mean_key_quality": 0.7,
                "selection_rate": 1.0,
                "legitimate_refusal_rate": 0.0,
                "false_acceptance_rate": 0.0,
                "security_floor_violation_rate": 0.0
            },
            {
                "scenario_id": "S1",
                "mean_energy_objective_j": 3.0,
                "mean_normalized_latency_objective": 0.4,
                "mean_authentication_robustness": 1.0,
                "mean_key_quality": 0.9,
                "selection_rate": 0.8,
                "legitimate_refusal_rate": 0.2,
                "false_acceptance_rate": 0.0,
                "security_floor_violation_rate": 0.0
            }
        ]

        summary_rows = (
            build_four_objective_summary_rows(
                per_mission_rows
            )
        )

        self.assertEqual(
            len(summary_rows),
            1
        )

        self.assertEqual(
            summary_rows[0][
                "energy_objective_j_mean"
            ],
            2.0
        )

        self.assertEqual(
            summary_rows[0][
                "authentication_robustness_mean"
            ],
            0.9
        )

    def test_error_bar(self):

        row = {
            "x_mean": 2.0,
            "x_ci95_low": 1.5,
            "x_ci95_high": 2.7
        }

        self.assertAlmostEqual(
            calculate_error_bar(
                row,
                "x"
            ),
            0.7
        )


class TestIntegrationWithRealModels(unittest.TestCase):

    # Ce test construit un véritable MissionStepResult
    # à partir des classes de models.py, sans SimpleNamespace,
    # afin de détecter tout nom d'attribut incompatible
    # entre run_three_scenarios.py et la structure réelle
    # produite par mission.py.
    def create_real_step_result(self):

        decision = Decision(
            AuthenticationAction.A2,
            KeyAction.K1A
        )

        authentication_metrics = AuthenticationMetrics(
            authentication_action=AuthenticationAction.A2,
            far=0.01,
            frr=0.05,
            mac_forgery_probability=2 ** (-64),
            total_false_acceptance_probability=0.01,
            authentication_robustness=0.95,
            alice_fallback_probability=0.05,
            mallory_fallback_probability=0.99
        )

        key_metrics = KeyMetrics(
            key_action=KeyAction.K1A,
            raw_kdr=0.20,
            effective_kdr=0.20,
            binary_entropy=0.72,
            reconciliation_yield=0.19,
            required_measurements=10,
            agreement_feasible=True,
            variation_feasible=True,
            phy_feasible=True,
            key_aging_index=0.2,
            renewal_required=True,
            key_expired=False,
            key_deadline_s=100.0,
            key_quality=0.85
        )

        cost_metrics = CostMetrics(
            base_energy_j=0.5,
            authentication_security_energy_j=0.1,
            key_security_energy_j=0.2,
            security_energy_j=0.3,
            total_energy_j=0.8,
            authentication_latency_s=0.2,
            prudent_authentication_latency_s=1.0,
            key_latency_s=2.0,
            normalized_latency=0.15,
            airtime_s=0.5,
            expected_energy_j=0.8,
            worst_case_energy_j=1.0
        )

        evaluation = DecisionEvaluation(
            decision
        )

        evaluation.authentication_metrics = (
            authentication_metrics
        )
        evaluation.key_metrics = key_metrics
        evaluation.cost_metrics = cost_metrics
        evaluation.admissible = True

        context = Context(
            snr_db=5.0,
            doppler_hz=0.0,
            battery_energy_j=28000.0,
            criticality=0,
            key_age_s=100.0,
            messages_with_current_key=2,
            rff_profile_available=True,
            renewal_required=True,
            key_expired=False,
            compromise_suspected=False,
            key_deadline_s=100.0,
            remaining_duty_cycle_airtime_s=10.0
        )

        channel_metrics = ChannelMetrics(
            snr_db=5.0,
            snr_linear=3.1622776602,
            doppler_hz=0.0,
            temporal_correlation=1.0,
            noise_correlation=0.75,
            rho_ab=0.70
        )

        decision_maker_result = DecisionMakerResult(
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
                0.8,
                0.15,
                -0.95,
                -0.85
            ],
            nadir_point=[
                0.8,
                0.15,
                -0.95,
                -0.85
            ],
            selected_evaluation=evaluation,
            refusal_of_service=False,
            fallback_mode_used=None,
            explanation="Décision de test intégré."
        )

        state_before = MissionState(
            step_index=3,
            time_s=180.0,
            battery_energy_j=28000.0,
            key_age_s=100.0,
            messages_with_current_key=2,
            current_key_identifier="KEY-001",
            remaining_duty_cycle_airtime_s=10.0
        )

        state_after = MissionState(
            step_index=4,
            time_s=240.0,
            battery_energy_j=27999.2,
            key_age_s=0.0,
            messages_with_current_key=0,
            current_key_identifier="KEY-002",
            remaining_duty_cycle_airtime_s=9.5
        )

        return MissionStepResult(
            state_before=state_before,
            context=context,
            channel_metrics=channel_metrics,
            decision_maker_result=decision_maker_result,
            legitimate_message_served=True,
            mallory_attempted=False,
            mallory_accepted=False,
            energy_debited_from_alice_j=0.8,
            state_after=state_after
        )

    def test_extraction_with_real_model_objects(self):

        step_result = self.create_real_step_result()

        row = extract_selected_step_metrics(
            step_result=step_result,
            scenario_id="S1-DEGRADED-CHANNEL",
            policy_id="P0-THESIS-CONTEXTUAL-PILOT",
            seed=2000
        )

        self.assertEqual(
            row["decision_name"],
            "A2-K1a"
        )

        self.assertEqual(
            row["step_index"],
            3
        )

        self.assertEqual(
            row["energy_objective_j"],
            0.8
        )

        self.assertEqual(
            row["authentication_robustness"],
            0.95
        )

        self.assertEqual(
            row["key_quality"],
            0.85
        )

        self.assertEqual(
            row["criticality"],
            0
        )

        self.assertEqual(
            row["snr_db"],
            5.0
        )


if __name__ == "__main__":

    unittest.main()
