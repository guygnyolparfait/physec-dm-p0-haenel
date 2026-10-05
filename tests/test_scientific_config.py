# unittest est l'outil de test fourni avec Python.
import math
import unittest


from physec_dm.scientific_config import (
    ALLOWED_PARAMETER_STATUSES,
    SCIENTIFIC_CONFIG_VERSION,
    apply_exploratory_cost_profile,
    build_deterministic_snr_scenarios,
    build_executable_pilot_policies,
    build_exploratory_cost_profiles,
    build_final_scientific_configuration,
    build_one_at_a_time_sensitivity_scenarios,
    build_parameter_registry,
    build_pilot_monte_carlo_scenarios,
    build_pilot_monte_carlo_seeds,
    build_policy_catalog,
    build_scientific_pilot_configuration,
    build_scientific_pilot_parameters,
    create_parameter_record,
    create_sensitivity_scenario,
    get_final_blocking_parameters,
    validate_executable_policies,
    validate_parameter_registry,
    validate_scientific_configuration,
    validate_scientific_scenarios,
    validate_unique_identifiers
)

from physec_dm.parameters import (
    Parameters
)


class TestParameterRecords(unittest.TestCase):

    def test_record_contains_all_fields(self):

        record = create_parameter_record(
            name="x",
            value=1.0,
            unit="J",
            status="scenario",
            source="test",
            description="description",
            sensitivity_range=[
                0.5,
                1.0
            ],
            validated=True,
            blocking_for_final=False
        )

        expected_fields = {
            "name",
            "value",
            "unit",
            "status",
            "source",
            "description",
            "sensitivity_range",
            "validated",
            "blocking_for_final"
        }

        self.assertEqual(
            set(record.keys()),
            expected_fields
        )

    def test_invalid_status_is_rejected(self):

        with self.assertRaises(ValueError):

            create_parameter_record(
                name="x",
                value=1.0,
                unit="J",
                status="invented",
                source="test",
                description="description",
                sensitivity_range=None,
                validated=False,
                blocking_for_final=True
            )

    def test_registry_is_valid(self):

        registry = build_parameter_registry()

        self.assertTrue(
            validate_parameter_registry(
                registry
            )
        )

    def test_registry_names_are_unique(self):

        registry = build_parameter_registry()

        names = [
            record["name"]
            for record in registry
        ]

        self.assertEqual(
            len(names),
            len(set(names))
        )

    def test_open_parameters_are_blocking(self):

        registry = build_parameter_registry()

        blockers = get_final_blocking_parameters(
            registry
        )

        self.assertIn(
            "mac_cycles",
            blockers
        )

        self.assertIn(
            "variation_feasible",
            blockers
        )

        self.assertIn(
            "k2_protocol_id",
            blockers
        )

    def test_allowed_statuses_include_to_validate(self):

        self.assertIn(
            "to_validate",
            ALLOWED_PARAMETER_STATUSES
        )


class TestExploratoryProfiles(unittest.TestCase):

    def test_three_profiles_exist(self):

        profiles = build_exploratory_cost_profiles()

        self.assertEqual(
            set(profiles.keys()),
            {
                "LOW",
                "CENTRAL",
                "HIGH"
            }
        )

    def test_profile_order(self):

        profiles = build_exploratory_cost_profiles()

        self.assertLess(
            profiles["LOW"]["mac_cycles"],
            profiles["CENTRAL"]["mac_cycles"]
        )

        self.assertLess(
            profiles["CENTRAL"]["mac_cycles"],
            profiles["HIGH"]["mac_cycles"]
        )

    def test_central_profile_is_applied(self):

        parameters = Parameters()

        apply_exploratory_cost_profile(
            parameters,
            "CENTRAL"
        )

        self.assertEqual(
            parameters.mac_cycles,
            32000
        )

        self.assertEqual(
            parameters.minimum_deadline_s,
            60.0
        )

        self.assertTrue(
            parameters.exploratory_run
        )

        self.assertFalse(
            parameters.k2_enabled
        )

    def test_unknown_profile_is_rejected(self):

        with self.assertRaises(ValueError):

            apply_exploratory_cost_profile(
                Parameters(),
                "UNKNOWN"
            )


class TestScientificPilotParameters(unittest.TestCase):

    def test_nominal_mission_probabilities(self):

        parameters = (
            build_scientific_pilot_parameters()
        )

        self.assertEqual(
            parameters.critical_message_probability,
            0.10
        )

        self.assertEqual(
            parameters.mallory_attempt_probability,
            0.15
        )

        self.assertEqual(
            parameters.shadowing_std_db,
            3.0
        )

    def test_snr_quantization_is_present(self):

        parameters = (
            build_scientific_pilot_parameters()
        )

        self.assertEqual(
            parameters.snr_quantization_step_db,
            0.25
        )

    def test_complete_parameter_validation_passes(self):

        parameters = (
            build_scientific_pilot_parameters()
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

    def test_config_version_is_recorded(self):

        parameters = (
            build_scientific_pilot_parameters()
        )

        self.assertEqual(
            parameters.scientific_config_version,
            SCIENTIFIC_CONFIG_VERSION
        )


class TestDeterministicScenarios(unittest.TestCase):

    def test_one_db_step_creates_51_scenarios(self):

        scenarios = (
            build_deterministic_snr_scenarios(
                step_db=1.0
            )
        )

        self.assertEqual(
            len(scenarios),
            51
        )

        self.assertEqual(
            scenarios[0][
                "parameter_overrides"
            ]["mean_snr_db"],
            -20.0
        )

        self.assertEqual(
            scenarios[-1][
                "parameter_overrides"
            ]["mean_snr_db"],
            30.0
        )

    def test_half_db_step_creates_101_scenarios(self):

        scenarios = (
            build_deterministic_snr_scenarios(
                step_db=0.5
            )
        )

        self.assertEqual(
            len(scenarios),
            101
        )

    def test_invalid_snr_step_is_rejected(self):

        with self.assertRaises(ValueError):

            build_deterministic_snr_scenarios(
                step_db=2.0
            )


class TestPilotMonteCarloScenarios(unittest.TestCase):

    def test_eight_pilot_scenarios(self):

        scenarios = (
            build_pilot_monte_carlo_scenarios()
        )

        self.assertEqual(
            len(scenarios),
            8
        )

    def test_nominal_shadowing_and_probabilities(self):

        scenarios = (
            build_pilot_monte_carlo_scenarios()
        )

        for scenario in scenarios:

            overrides = scenario[
                "parameter_overrides"
            ]

            self.assertEqual(
                overrides["shadowing_std_db"],
                3.0
            )

            self.assertEqual(
                overrides[
                    "critical_message_probability"
                ],
                0.10
            )

            self.assertEqual(
                overrides[
                    "mallory_attempt_probability"
                ],
                0.15
            )

    def test_duty_cycle_budget_is_hourly(self):

        scenario = (
            build_pilot_monte_carlo_scenarios()[0]
        )

        mission_options = scenario[
            "mission_options"
        ]

        self.assertEqual(
            mission_options[
                "maximum_duty_cycle_airtime_s"
            ],
            36.0
        )

        self.assertEqual(
            mission_options[
                "duty_cycle_recharge_s"
            ],
            0.6
        )

    def test_both_variation_modes_are_present(self):

        scenarios = (
            build_pilot_monte_carlo_scenarios()
        )

        modes = {
            scenario["variation_feasible"]
            for scenario in scenarios
        }

        self.assertEqual(
            modes,
            {
                False,
                True
            }
        )


class TestSensitivityScenarios(unittest.TestCase):

    def test_sensitivity_scenarios_are_unique(self):

        scenarios = (
            build_one_at_a_time_sensitivity_scenarios()
        )

        self.assertTrue(
            validate_unique_identifiers(
                scenarios,
                "scenario_id"
            )
        )

    def test_kdr_sensitivity_recomputes_correlation(self):

        scenarios = (
            build_one_at_a_time_sensitivity_scenarios()
        )

        kdr_scenarios = [
            scenario
            for scenario in scenarios
            if scenario[
                "scenario_id"
            ].startswith(
                "SENS-KDRMAX"
            )
        ]

        for scenario in kdr_scenarios:

            overrides = scenario[
                "parameter_overrides"
            ]

            expected_rho = math.cos(
                math.pi
                * overrides[
                    "maximum_kdr"
                ]
            )

            self.assertAlmostEqual(
                overrides[
                    "minimum_correlation"
                ],
                expected_rho
            )

    def test_sensitivity_base_is_independent(self):

        source_overrides = {
            "mean_snr_db": 5.0
        }

        scenario = create_sensitivity_scenario(
            scenario_id="S1",
            parameter_overrides=(
                source_overrides
            )
        )

        source_overrides[
            "mean_snr_db"
        ] = 99.0

        self.assertEqual(
            scenario[
                "parameter_overrides"
            ]["mean_snr_db"],
            5.0
        )


class TestPolicies(unittest.TestCase):

    def test_policy_catalog_contains_required_baselines(self):

        policy_ids = {
            policy["policy_id"]
            for policy in build_policy_catalog()
        }

        self.assertIn(
            "B1-CONVENTIONAL",
            policy_ids
        )

        self.assertIn(
            "B2-NAIVE-PHYSEC",
            policy_ids
        )

        self.assertIn(
            "B3-FIXED-HYBRID",
            policy_ids
        )

        self.assertIn(
            "B4-DM-NO-FAR-FLOOR",
            policy_ids
        )

    def test_blocked_policies_are_explicit(self):

        catalog = build_policy_catalog()

        b1 = next(
            policy
            for policy in catalog
            if policy["policy_id"] == "B1-CONVENTIONAL"
        )

        self.assertEqual(
            b1["implementation_status"],
            "BLOCKED"
        )

        self.assertIsNotNone(
            b1["blocking_reason"]
        )

    def test_two_pilot_policies_are_executable(self):

        policies = (
            build_executable_pilot_policies()
        )

        self.assertEqual(
            len(policies),
            2
        )

        self.assertTrue(
            validate_executable_policies(
                policies,
                1e-12
            )
        )

    def test_b4_removes_far_floor(self):

        policies = (
            build_executable_pilot_policies()
        )

        b4 = next(
            policy
            for policy in policies
            if policy["policy_id"]
            == "B4-DM-NO-FAR-FLOOR"
        )

        self.assertEqual(
            b4[
                "parameter_overrides"
            ]["critical_far_limit"],
            1.0
        )

        self.assertEqual(
            b4[
                "parameter_overrides"
            ]["normal_far_limit"],
            1.0
        )


class TestSeeds(unittest.TestCase):

    def test_default_seed_count(self):

        seeds = build_pilot_monte_carlo_seeds()

        self.assertEqual(
            len(seeds),
            30
        )

        self.assertEqual(
            seeds[0],
            1000
        )

        self.assertEqual(
            seeds[-1],
            1029
        )

    def test_seed_count_must_be_positive(self):

        with self.assertRaises(ValueError):

            build_pilot_monte_carlo_seeds(
                count=0
            )


class TestCompleteConfiguration(unittest.TestCase):

    def test_pilot_configuration_is_valid(self):

        configuration = (
            build_scientific_pilot_configuration(
                max_steps=100,
                seed_count=3
            )
        )

        self.assertTrue(
            configuration[
                "validation"
            ]["valid"]
        )

        self.assertTrue(
            configuration[
                "exploratory_run"
            ]
        )

        self.assertEqual(
            len(
                configuration[
                    "scenarios"
                ]
            ),
            8
        )

        self.assertEqual(
            len(
                configuration[
                    "policies"
                ]
            ),
            2
        )

        self.assertEqual(
            len(
                configuration[
                    "seeds"
                ]
            ),
            3
        )

    def test_pilot_validation_reports_blockers(self):

        configuration = (
            build_scientific_pilot_configuration(
                max_steps=10,
                seed_count=2
            )
        )

        blockers = configuration[
            "validation"
        ]["final_blockers"]

        self.assertIn(
            "mac_cycles",
            blockers
        )

        self.assertIn(
            "k2_protocol_id",
            blockers
        )

    def test_final_run_is_blocked(self):

        configuration = (
            build_scientific_pilot_configuration(
                max_steps=10,
                seed_count=2
            )
        )

        with self.assertRaises(ValueError):

            validate_scientific_configuration(
                parameters=(
                    configuration[
                        "parameters"
                    ]
                ),
                scenarios=(
                    configuration[
                        "scenarios"
                    ]
                ),
                policies=(
                    configuration[
                        "policies"
                    ]
                ),
                seeds=(
                    configuration[
                        "seeds"
                    ]
                ),
                parameter_registry=(
                    configuration[
                        "parameter_registry"
                    ]
                ),
                final_run=True
            )

    def test_final_builder_refuses(self):

        with self.assertRaises(ValueError):

            build_final_scientific_configuration()


if __name__ == "__main__":

    unittest.main()
