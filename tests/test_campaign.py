# unittest est l'outil de test fourni avec Python.
import csv
import tempfile
import unittest


from pathlib import Path


from unittest.mock import patch


from physec_dm.models import (
    CampaignResult,
    MissionResult,
    MissionState
)

from physec_dm.parameters import Parameters

from physec_dm.campaign import (
    aggregate_campaign_results,
    apply_parameter_overrides,
    build_mission_summary_rows,
    build_policy_parameters,
    build_scenario_parameters,
    calculate_95_percent_confidence_interval,
    calculate_decision_frequencies,
    calculate_mean,
    calculate_sample_standard_deviation,
    clone_parameters,
    create_common_random_traces,
    export_campaign_results,
    get_mission_scenario_id,
    get_required_identifier,
    group_mission_results,
    prepare_plot_data,
    remove_undefined_values,
    run_campaign,
    summarize_values,
    validate_non_empty_sequence,
    validate_probability,
    write_csv_rows
)


# Cette fonction crée des paramètres
# suffisants pour les tests de campagne.
def create_test_parameters():

    parameters = Parameters()

    parameters.mean_snr_db = 5.0
    parameters.shadowing_std_db = 1.0

    parameters.critical_message_probability = 0.25
    parameters.mallory_attempt_probability = 0.10

    parameters.contextual_weights = [
        0.25,
        0.25,
        0.25,
        0.25
    ]

    parameters.dominance_tolerance = 1e-12
    parameters.score_tolerance = 1e-12

    return parameters


def create_mission_result(
    scenario_id,
    policy_id,
    seed,
    lifetime_s,
    energy_generated,
    energy_served,
    far,
    critical_far,
    refusal_rate,
    violation_rate,
    decision_counts,
    final_battery_energy_j,
    censored
):

    final_state = MissionState(
        step_index=10,
        time_s=lifetime_s,
        battery_energy_j=(
            final_battery_energy_j
        ),
        key_age_s=100.0,
        messages_with_current_key=10,
        current_key_identifier="KEY-001",
        remaining_duty_cycle_airtime_s=1.0
    )

    return MissionResult(
        parameters_snapshot={
            "scenario_id": scenario_id
        },
        seed=seed,
        policy_id=policy_id,
        steps=[],
        lifetime_s=lifetime_s,
        mean_energy_per_generated_message_j=(
            energy_generated
        ),
        mean_energy_per_served_message_j=(
            energy_served
        ),
        false_acceptance_rate=far,
        critical_false_acceptance_rate=(
            critical_far
        ),
        legitimate_refusal_rate=(
            refusal_rate
        ),
        security_floor_violation_rate=(
            violation_rate
        ),
        decision_counts=decision_counts,
        final_state=final_state,
        stop_reason="maximum_steps",
        censored=censored
    )


def create_campaign_result(
    mission_results,
    output_directory="results"
):

    return CampaignResult(
        campaign_id="CAMP-TEST",
        scenario_ids=[
            "S1"
        ],
        policy_ids=[
            "P1",
            "P2"
        ],
        seeds=[
            1,
            2
        ],
        mission_results=mission_results,
        output_directory=output_directory
    )


class TestInputValidation(unittest.TestCase):

    def test_empty_sequence_is_rejected(self):

        with self.assertRaises(ValueError):

            validate_non_empty_sequence(
                [],
                "values"
            )

    def test_missing_identifier_is_rejected(self):

        with self.assertRaises(ValueError):

            get_required_identifier(
                {},
                "scenario_id"
            )

    def test_blank_identifier_is_rejected(self):

        with self.assertRaises(ValueError):

            get_required_identifier(
                {
                    "policy_id": " "
                },
                "policy_id"
            )

    def test_invalid_probability_is_rejected(self):

        with self.assertRaises(ValueError):

            validate_probability(
                1.2,
                "p"
            )


class TestParameterConfigurations(unittest.TestCase):

    def test_clone_is_independent(self):

        original = create_test_parameters()

        cloned = clone_parameters(
            original
        )

        cloned.mean_snr_db = 12.0

        self.assertEqual(
            original.mean_snr_db,
            5.0
        )

    def test_known_override_is_applied(self):

        parameters = create_test_parameters()

        apply_parameter_overrides(
            parameters,
            {
                "mean_snr_db": 8.0
            },
            "test"
        )

        self.assertEqual(
            parameters.mean_snr_db,
            8.0
        )

    def test_unknown_override_is_rejected(self):

        with self.assertRaises(ValueError):

            apply_parameter_overrides(
                create_test_parameters(),
                {
                    "unknown_parameter": 1
                },
                "test"
            )

    def test_scenario_parameters(self):

        parameters = (
            build_scenario_parameters(
                create_test_parameters(),
                {
                    "scenario_id": "S-LOW",
                    "parameter_overrides": {
                        "mean_snr_db": -5.0
                    }
                }
            )
        )

        self.assertEqual(
            parameters.scenario_id,
            "S-LOW"
        )

        self.assertEqual(
            parameters.mean_snr_db,
            -5.0
        )

    def test_policy_override_has_priority(self):

        scenario_parameters = (
            build_scenario_parameters(
                create_test_parameters(),
                {
                    "scenario_id": "S1",
                    "parameter_overrides": {
                        "normal_far_limit": 0.05
                    }
                }
            )
        )

        policy_parameters = (
            build_policy_parameters(
                scenario_parameters,
                {
                    "policy_id": "P-STRICT",
                    "parameter_overrides": {
                        "normal_far_limit": 0.02
                    },
                    "contextual_weights": [
                        0.1,
                        0.2,
                        0.4,
                        0.3
                    ]
                }
            )
        )

        self.assertEqual(
            policy_parameters.normal_far_limit,
            0.02
        )

        self.assertEqual(
            policy_parameters.contextual_weights,
            [
                0.1,
                0.2,
                0.4,
                0.3
            ]
        )


class TestCommonRandomTraces(unittest.TestCase):

    def test_same_seed_is_reproducible(self):

        parameters = create_test_parameters()

        traces_a = create_common_random_traces(
            parameters,
            seed=123,
            max_steps=20
        )

        traces_b = create_common_random_traces(
            parameters,
            seed=123,
            max_steps=20
        )

        self.assertEqual(
            traces_a,
            traces_b
        )

    def test_different_seed_changes_trace(self):

        parameters = create_test_parameters()

        traces_a = create_common_random_traces(
            parameters,
            seed=1,
            max_steps=20
        )

        traces_b = create_common_random_traces(
            parameters,
            seed=2,
            max_steps=20
        )

        self.assertNotEqual(
            traces_a[
                "observed_snr_trace"
            ],
            traces_b[
                "observed_snr_trace"
            ]
        )

    def test_trace_lengths(self):

        traces = create_common_random_traces(
            create_test_parameters(),
            seed=1,
            max_steps=7
        )

        for trace_name in traces:

            self.assertEqual(
                len(traces[trace_name]),
                7
            )

    def test_criticality_is_binary(self):

        traces = create_common_random_traces(
            create_test_parameters(),
            seed=1,
            max_steps=50
        )

        self.assertTrue(
            all(
                value in [
                    0,
                    1
                ]
                for value in traces[
                    "criticality_trace"
                ]
            )
        )

    def test_real_snr_bias(self):

        traces = create_common_random_traces(
            create_test_parameters(),
            seed=1,
            max_steps=5,
            real_snr_bias_db=-2.0
        )

        for observed_value, real_value in zip(
            traces["observed_snr_trace"],
            traces["real_snr_trace"]
        ):

            self.assertAlmostEqual(
                real_value,
                observed_value - 2.0
            )


class TestStatistics(unittest.TestCase):

    def test_remove_none(self):

        self.assertEqual(
            remove_undefined_values(
                [
                    1.0,
                    None,
                    3.0
                ]
            ),
            [
                1.0,
                3.0
            ]
        )

    def test_mean_ignores_none(self):

        self.assertEqual(
            calculate_mean(
                [
                    1.0,
                    None,
                    3.0
                ]
            ),
            2.0
        )

    def test_empty_mean_is_none(self):

        self.assertIsNone(
            calculate_mean(
                [
                    None
                ]
            )
        )

    def test_standard_deviation_needs_two_values(self):

        self.assertIsNone(
            calculate_sample_standard_deviation(
                [
                    1.0
                ]
            )
        )

    def test_confidence_interval_needs_two_values(self):

        self.assertEqual(
            calculate_95_percent_confidence_interval(
                [
                    1.0
                ]
            ),
            (
                None,
                None
            )
        )

    def test_summary_values(self):

        summary = summarize_values(
            [
                1.0,
                3.0
            ],
            "metric"
        )

        self.assertEqual(
            summary["metric_count"],
            2
        )

        self.assertEqual(
            summary["metric_mean"],
            2.0
        )

        self.assertIsNotNone(
            summary["metric_ci95_low"]
        )


class TestAggregation(unittest.TestCase):

    def create_results(self):

        return [
            create_mission_result(
                scenario_id="S1",
                policy_id="P1",
                seed=1,
                lifetime_s=100.0,
                energy_generated=1.0,
                energy_served=1.2,
                far=0.10,
                critical_far=None,
                refusal_rate=0.20,
                violation_rate=0.05,
                decision_counts={
                    "A1-K0": 8,
                    "A2-K0": 2
                },
                final_battery_energy_j=90.0,
                censored=False
            ),
            create_mission_result(
                scenario_id="S1",
                policy_id="P1",
                seed=2,
                lifetime_s=120.0,
                energy_generated=2.0,
                energy_served=2.2,
                far=0.20,
                critical_far=0.25,
                refusal_rate=0.10,
                violation_rate=0.00,
                decision_counts={
                    "A1-K0": 5,
                    "A2-K0": 5
                },
                final_battery_energy_j=80.0,
                censored=True
            ),
            create_mission_result(
                scenario_id="S1",
                policy_id="P2",
                seed=1,
                lifetime_s=90.0,
                energy_generated=3.0,
                energy_served=3.2,
                far=None,
                critical_far=None,
                refusal_rate=0.30,
                violation_rate=0.10,
                decision_counts={
                    "A2-K0": 10
                },
                final_battery_energy_j=70.0,
                censored=True
            )
        ]

    def test_scenario_id_is_read(self):

        result = self.create_results()[0]

        self.assertEqual(
            get_mission_scenario_id(
                result
            ),
            "S1"
        )

    def test_grouping(self):

        campaign_result = (
            create_campaign_result(
                self.create_results()
            )
        )

        grouped = group_mission_results(
            campaign_result
        )

        self.assertEqual(
            len(
                grouped[
                    (
                        "S1",
                        "P1"
                    )
                ]
            ),
            2
        )

    def test_aggregate_mean_and_censoring(self):

        campaign_result = (
            create_campaign_result(
                self.create_results()
            )
        )

        rows = aggregate_campaign_results(
            campaign_result
        )

        p1_row = next(
            row
            for row in rows
            if row["policy_id"] == "P1"
        )

        self.assertEqual(
            p1_row["mission_count"],
            2
        )

        self.assertEqual(
            p1_row["censored_fraction"],
            0.5
        )

        self.assertEqual(
            p1_row[
                "observed_lifetime_s_mean"
            ],
            110.0
        )

        self.assertEqual(
            p1_row[
                "critical_false_acceptance_rate_count"
            ],
            1
        )

    def test_decision_frequencies(self):

        campaign_result = (
            create_campaign_result(
                self.create_results()
            )
        )

        rows = calculate_decision_frequencies(
            campaign_result
        )

        p1_a1 = next(
            row
            for row in rows
            if (
                row["policy_id"] == "P1"
                and row["decision_name"] == "A1-K0"
            )
        )

        self.assertEqual(
            p1_a1["decision_count"],
            13
        )

        self.assertEqual(
            p1_a1["total_selections"],
            20
        )

        self.assertEqual(
            p1_a1["selection_frequency"],
            13 / 20
        )

    def test_plot_data_is_long_format(self):

        campaign_result = (
            create_campaign_result(
                self.create_results()
            )
        )

        plot_rows = prepare_plot_data(
            campaign_result
        )

        self.assertEqual(
            len(plot_rows),
            16
        )

        self.assertIn(
            "metric_name",
            plot_rows[0]
        )


class TestCsvExport(unittest.TestCase):

    def test_write_csv_rows(self):

        with tempfile.TemporaryDirectory() as directory:

            file_path = Path(
                directory
            ) / "test.csv"

            write_csv_rows(
                file_path,
                [
                    {
                        "a": 1,
                        "b": 2
                    }
                ]
            )

            with file_path.open(
                "r",
                encoding="utf-8"
            ) as csv_file:

                rows = list(
                    csv.DictReader(
                        csv_file
                    )
                )

            self.assertEqual(
                rows[0]["a"],
                "1"
            )

    def test_mission_summary_rows(self):

        campaign_result = (
            create_campaign_result(
                [
                    create_mission_result(
                        scenario_id="S1",
                        policy_id="P1",
                        seed=1,
                        lifetime_s=100.0,
                        energy_generated=1.0,
                        energy_served=1.2,
                        far=0.1,
                        critical_far=0.05,
                        refusal_rate=0.2,
                        violation_rate=0.0,
                        decision_counts={
                            "A1-K0": 10
                        },
                        final_battery_energy_j=90.0,
                        censored=False
                    )
                ]
            )
        )

        rows = build_mission_summary_rows(
            campaign_result
        )

        self.assertEqual(
            rows[0]["campaign_id"],
            "CAMP-TEST"
        )

        self.assertEqual(
            rows[0]["scenario_id"],
            "S1"
        )

    def test_all_export_files_are_created(self):

        campaign_result = (
            create_campaign_result(
                [
                    create_mission_result(
                        scenario_id="S1",
                        policy_id="P1",
                        seed=1,
                        lifetime_s=100.0,
                        energy_generated=1.0,
                        energy_served=1.2,
                        far=0.1,
                        critical_far=0.05,
                        refusal_rate=0.2,
                        violation_rate=0.0,
                        decision_counts={
                            "A1-K0": 10
                        },
                        final_battery_energy_j=90.0,
                        censored=False
                    )
                ]
            )
        )

        with tempfile.TemporaryDirectory() as directory:

            exported_paths = (
                export_campaign_results(
                    campaign_result,
                    directory
                )
            )

            for path_text in (
                exported_paths.values()
            ):

                self.assertTrue(
                    Path(path_text).exists()
                )


class TestCompleteCampaign(unittest.TestCase):

    def test_campaign_runs_all_combinations(self):

        parameters = create_test_parameters()

        scenarios = [
            {
                "scenario_id": "S1"
            },
            {
                "scenario_id": "S2"
            }
        ]

        policies = [
            {
                "policy_id": "P1"
            },
            {
                "policy_id": "P2"
            }
        ]

        fake_results = []

        def fake_run_mission(
            parameters,
            seed,
            policy_id,
            **kwargs
        ):

            result = create_mission_result(
                scenario_id=(
                    parameters.scenario_id
                ),
                policy_id=policy_id,
                seed=seed,
                lifetime_s=100.0,
                energy_generated=1.0,
                energy_served=1.0,
                far=0.0,
                critical_far=0.0,
                refusal_rate=0.0,
                violation_rate=0.0,
                decision_counts={
                    "A1-K0": 1
                },
                final_battery_energy_j=90.0,
                censored=False
            )

            fake_results.append(
                (
                    parameters.scenario_id,
                    policy_id,
                    seed
                )
            )

            return result

        with tempfile.TemporaryDirectory() as directory:

            with patch(
                "physec_dm.campaign.run_mission",
                side_effect=fake_run_mission
            ):

                result = run_campaign(
                    base_parameters=parameters,
                    campaign_id="C1",
                    scenarios=scenarios,
                    policies=policies,
                    seeds=[
                        1,
                        2
                    ],
                    output_directory=directory,
                    max_steps=5,
                    export_results=False
                )

        self.assertEqual(
            len(result.mission_results),
            8
        )

        self.assertEqual(
            len(fake_results),
            8
        )

    def test_policies_receive_same_common_traces(self):

        parameters = create_test_parameters()

        received_traces = []

        def fake_run_mission(
            parameters,
            seed,
            policy_id,
            **kwargs
        ):

            received_traces.append(
                {
                    "policy_id": policy_id,
                    "observed": list(
                        kwargs[
                            "observed_snr_trace"
                        ]
                    ),
                    "criticality": list(
                        kwargs[
                            "criticality_trace"
                        ]
                    ),
                    "mallory": list(
                        kwargs[
                            "mallory_trace"
                        ]
                    )
                }
            )

            return create_mission_result(
                scenario_id=(
                    parameters.scenario_id
                ),
                policy_id=policy_id,
                seed=seed,
                lifetime_s=100.0,
                energy_generated=1.0,
                energy_served=1.0,
                far=0.0,
                critical_far=0.0,
                refusal_rate=0.0,
                violation_rate=0.0,
                decision_counts={
                    "A1-K0": 1
                },
                final_battery_energy_j=90.0,
                censored=False
            )

        with tempfile.TemporaryDirectory() as directory:

            with patch(
                "physec_dm.campaign.run_mission",
                side_effect=fake_run_mission
            ):

                run_campaign(
                    base_parameters=parameters,
                    campaign_id="C1",
                    scenarios=[
                        {
                            "scenario_id": "S1"
                        }
                    ],
                    policies=[
                        {
                            "policy_id": "P1"
                        },
                        {
                            "policy_id": "P2"
                        }
                    ],
                    seeds=[
                        123
                    ],
                    output_directory=directory,
                    max_steps=10,
                    export_results=False
                )

        self.assertEqual(
            received_traces[0]["observed"],
            received_traces[1]["observed"]
        )

        self.assertEqual(
            received_traces[0]["criticality"],
            received_traces[1]["criticality"]
        )

        self.assertEqual(
            received_traces[0]["mallory"],
            received_traces[1]["mallory"]
        )

    def test_empty_policies_are_rejected(self):

        with tempfile.TemporaryDirectory() as directory:

            with self.assertRaises(ValueError):

                run_campaign(
                    base_parameters=(
                        create_test_parameters()
                    ),
                    campaign_id="C1",
                    scenarios=[
                        {
                            "scenario_id": "S1"
                        }
                    ],
                    policies=[],
                    seeds=[
                        1
                    ],
                    output_directory=directory
                )


if __name__ == "__main__":

    unittest.main()
