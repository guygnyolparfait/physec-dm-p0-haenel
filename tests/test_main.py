# unittest est l'outil de test fourni avec Python.
import io
import unittest


# redirect_stdout permet de lire
# ce qui a été affiché dans le terminal.
from contextlib import redirect_stdout


# patch permet de remplacer temporairement
# run_campaign pendant les tests.
from unittest.mock import patch


from physec_dm.models import (
    CampaignResult
)


from scripts import main
class SimpleMissionResult:

    # Cette classe minimale suffit
    # pour les tests d'affichage.
    def __init__(self):

        self.policy_id = (
            "P-SMOKE-BALANCED"
        )

        self.parameters_snapshot = {
            "scenario_id": "S-SMOKE"
        }


def create_fake_campaign_result():

    return CampaignResult(
        campaign_id="CAMP-SMOKE-01",
        scenario_ids=[
            "S-SMOKE"
        ],
        policy_ids=[
            "P-SMOKE-BALANCED"
        ],
        seeds=[
            123
        ],
        mission_results=[
            SimpleMissionResult()
        ],
        output_directory="results/smoke"
    )


class TestSmokeParameters(unittest.TestCase):

    def test_all_required_parameters_are_defined(self):

        parameters = (
            main.build_smoke_parameters()
        )

        missing_parameters = (
            parameters.get_missing_parameters()
        )

        self.assertEqual(
            missing_parameters,
            []
        )

    def test_complete_validation_has_no_error(self):

        parameters = (
            main.build_smoke_parameters()
        )

        errors, warnings = parameters.validate(
            require_complete=True
        )

        self.assertEqual(
            errors,
            []
        )

        self.assertEqual(
            warnings,
            []
        )

    def test_smoke_probabilities(self):

        parameters = (
            main.build_smoke_parameters()
        )

        self.assertEqual(
            parameters.critical_message_probability,
            0.20
        )

        self.assertEqual(
            parameters.mallory_attempt_probability,
            0.10
        )


class TestSmokeDefinitions(unittest.TestCase):

    def test_smoke_scenario(self):

        scenarios = (
            main.build_smoke_scenarios()
        )

        self.assertEqual(
            len(scenarios),
            1
        )

        self.assertEqual(
            scenarios[0]["scenario_id"],
            "S-SMOKE"
        )

        self.assertEqual(
            scenarios[0][
                "mission_options"
            ]["max_steps"],
            5
        )

    def test_smoke_policy(self):

        policies = (
            main.build_smoke_policies()
        )

        self.assertEqual(
            len(policies),
            1
        )

        self.assertEqual(
            policies[0]["policy_id"],
            "P-SMOKE-BALANCED"
        )

        self.assertEqual(
            sum(
                policies[0][
                    "contextual_weights"
                ]
            ),
            1.0
        )

    def test_smoke_seed(self):

        self.assertEqual(
            main.build_smoke_seeds(),
            [
                123
            ]
        )


class TestSmokeValidation(unittest.TestCase):

    def test_valid_configuration(self):

        self.assertTrue(
            main.validate_smoke_configuration(
                parameters=(
                    main.build_smoke_parameters()
                ),
                scenarios=(
                    main.build_smoke_scenarios()
                ),
                policies=(
                    main.build_smoke_policies()
                ),
                seeds=(
                    main.build_smoke_seeds()
                )
            )
        )

    def test_empty_scenarios_are_rejected(self):

        with self.assertRaises(ValueError):

            main.validate_smoke_configuration(
                parameters=(
                    main.build_smoke_parameters()
                ),
                scenarios=[],
                policies=(
                    main.build_smoke_policies()
                ),
                seeds=(
                    main.build_smoke_seeds()
                )
            )

    def test_invalid_weights_are_rejected(self):

        policies = (
            main.build_smoke_policies()
        )

        policies[0][
            "contextual_weights"
        ] = [
            0.2,
            0.2,
            0.2,
            0.2
        ]

        with self.assertRaises(ValueError):

            main.validate_smoke_configuration(
                parameters=(
                    main.build_smoke_parameters()
                ),
                scenarios=(
                    main.build_smoke_scenarios()
                ),
                policies=policies,
                seeds=(
                    main.build_smoke_seeds()
                )
            )


class TestSummary(unittest.TestCase):

    def test_format_none(self):

        self.assertEqual(
            main.format_summary_value(
                None
            ),
            "non défini"
        )

    def test_format_float(self):

        self.assertEqual(
            main.format_summary_value(
                1.23456789
            ),
            "1.234568"
        )

    def test_print_summary(self):

        campaign_result = (
            create_fake_campaign_result()
        )

        aggregate_rows = [
            {
                "scenario_id": "S-SMOKE",
                "policy_id": (
                    "P-SMOKE-BALANCED"
                ),
                "observed_lifetime_s_mean": 300.0,
                "energy_per_generated_message_j_mean": 1.0,
                "false_acceptance_rate_mean": None,
                "legitimate_refusal_rate_mean": 0.0,
                "censored_fraction": 1.0
            }
        ]

        output = io.StringIO()

        with patch(
            "scripts.main.aggregate_campaign_results",
            return_value=aggregate_rows
        ):

            with redirect_stdout(
                output
            ):

                main.print_campaign_summary(
                    campaign_result
                )

        printed_text = output.getvalue()

        self.assertIn(
            "CAMP-SMOKE-01",
            printed_text
        )

        self.assertIn(
            "S-SMOKE",
            printed_text
        )

        self.assertIn(
            "non défini",
            printed_text
        )


class TestLaunch(unittest.TestCase):

    def test_run_smoke_campaign_calls_campaign(self):

        fake_result = (
            create_fake_campaign_result()
        )

        with patch(
            "scripts.main.run_campaign",
            return_value=fake_result
        ) as mocked_run_campaign:

            returned_result = (
                main.run_smoke_campaign(
                    output_directory=(
                        "results/test-smoke"
                    )
                )
            )

        self.assertIs(
            returned_result,
            fake_result
        )

        call_arguments = (
            mocked_run_campaign.call_args.kwargs
        )

        self.assertEqual(
            call_arguments["campaign_id"],
            "CAMP-SMOKE-01"
        )

        self.assertEqual(
            call_arguments["max_steps"],
            5
        )

        self.assertTrue(
            call_arguments["export_results"]
        )

    def test_main_returns_campaign_result(self):

        fake_result = (
            create_fake_campaign_result()
        )

        with patch(
            "scripts.main.run_smoke_campaign",
            return_value=fake_result
        ):

            with patch(
                "scripts.main.print_campaign_summary"
            ):

                returned_result = main.main()

        self.assertIs(
            returned_result,
            fake_result
        )


if __name__ == "__main__":

    unittest.main()
