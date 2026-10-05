import unittest


from physec_dm.thesis_scenarios import (
    THREE_SCENARIO_CAMPAIGN_ID,
    THREE_SCENARIO_CONFIG_VERSION,
    THREE_SCENARIO_IDS,
    apply_scenario_overrides_for_validation,
    build_exploratory_k2_protocol,
    build_scenario_weights,
    build_three_scenario_configuration,
    build_three_scenario_parameters,
    build_thesis_policy,
    build_thesis_scenarios,
    build_thesis_seeds,
    validate_thesis_scenarios
)


class TestThreeScenarioParameters(unittest.TestCase):

    def test_configuration_version(self):

        self.assertEqual(
            THREE_SCENARIO_CONFIG_VERSION,
            "2.0.0"
        )

    def test_campaign_identifier(self):

        self.assertIn(
            "THREE-SCENARIOS",
            THREE_SCENARIO_CAMPAIGN_ID
        )

    def test_nominal_cryptoperiod(self):

        parameters = (
            build_three_scenario_parameters()
        )

        self.assertEqual(
            parameters.maximum_messages_per_key,
            1000
        )

        self.assertEqual(
            parameters.maximum_key_age_s,
            86400.0
        )

        self.assertEqual(
            parameters.renewal_trigger,
            0.60
        )

    def test_parameters_are_complete(self):

        parameters = (
            build_three_scenario_parameters()
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


class TestK2Protocol(unittest.TestCase):

    def test_k2_protocol_uses_existing_parameters(self):

        parameters = (
            build_three_scenario_parameters()
        )

        protocol = (
            build_exploratory_k2_protocol(
                parameters
            )
        )

        self.assertEqual(
            protocol[
                "ecc_operation_energies_j"
            ],
            [
                parameters.ecc_signature_energy_j
            ]
        )

        self.assertEqual(
            protocol[
                "tx_message_sizes_bytes"
            ],
            [
                parameters.response_bytes
            ]
        )


class TestScenarioWeights(unittest.TestCase):

    def test_three_weight_vectors(self):

        weights = build_scenario_weights()

        self.assertEqual(
            set(weights.keys()),
            set(THREE_SCENARIO_IDS)
        )

    def test_each_weight_vector_sums_to_one(self):

        for weights in (
            build_scenario_weights().values()
        ):

            self.assertAlmostEqual(
                sum(weights),
                1.0
            )

    def test_s2_prioritizes_energy_and_latency(self):

        weights = build_scenario_weights()[
            "S2-RESOURCE-CONSTRAINED"
        ]

        self.assertGreater(
            weights[0] + weights[1],
            weights[2] + weights[3]
        )

    def test_s3_prioritizes_security(self):

        weights = build_scenario_weights()[
            "S3-HIGH-SECURITY-PRESSURE"
        ]

        self.assertGreater(
            weights[2] + weights[3],
            weights[0] + weights[1]
        )


class TestThreeScenarios(unittest.TestCase):

    def setUp(self):

        self.parameters = (
            build_three_scenario_parameters()
        )

        self.scenarios = build_thesis_scenarios(
            parameters=self.parameters,
            max_steps=300
        )

    def test_exactly_three_scenarios(self):

        self.assertEqual(
            len(self.scenarios),
            3
        )

    def test_scenario_order_is_fixed(self):

        self.assertEqual(
            [
                scenario["scenario_id"]
                for scenario in self.scenarios
            ],
            THREE_SCENARIO_IDS
        )

    def test_s1_is_degraded(self):

        s1 = self.scenarios[0]

        self.assertEqual(
            s1["parameter_overrides"][
                "mean_snr_db"
            ],
            -10.0
        )

        self.assertFalse(
            s1["variation_feasible"]
        )

    def test_s2_has_small_usable_energy_margin(self):

        s2 = self.scenarios[1]

        overrides = s2[
            "parameter_overrides"
        ]

        margin = (
            overrides[
                "initial_battery_energy_j"
            ]
            - overrides[
                "minimum_battery_energy_j"
            ]
        )

        self.assertAlmostEqual(
            margin,
            80.0
        )

        self.assertEqual(
            overrides[
                "critical_message_probability"
            ],
            0.60
        )

    def test_s3_has_stronger_attack_pressure(self):

        s1 = self.scenarios[0]
        s3 = self.scenarios[2]

        self.assertEqual(
            s3["parameter_overrides"][
                "mean_snr_db"
            ],
            20.0
        )

        self.assertGreater(
            s3["parameter_overrides"][
                "mallory_attempt_probability"
            ],
            s1["parameter_overrides"][
                "mallory_attempt_probability"
            ]
        )

    def test_each_scenario_has_k2_protocol(self):

        for scenario in self.scenarios:

            self.assertIn(
                "k2_protocol",
                scenario
            )

            self.assertIn(
                "ecc_operation_energies_j",
                scenario["k2_protocol"]
            )

    def test_each_scenario_has_300_steps(self):

        for scenario in self.scenarios:

            self.assertEqual(
                scenario["mission_options"][
                    "max_steps"
                ],
                300
            )

    def test_scenario_parameters_validate(self):

        for scenario in self.scenarios:

            scenario_parameters = (
                apply_scenario_overrides_for_validation(
                    self.parameters,
                    scenario
                )
            )

            errors, warnings = (
                scenario_parameters.validate(
                    require_complete=True
                )
            )

            self.assertEqual(
                errors,
                []
            )

            self.assertEqual(
                warnings,
                []
            )


class TestPolicyAndSeeds(unittest.TestCase):

    def test_one_policy(self):

        policies = build_thesis_policy()

        self.assertEqual(
            len(policies),
            1
        )

        self.assertEqual(
            policies[0]["policy_id"],
            "P0-THESIS-CONTEXTUAL-PILOT"
        )

    def test_thirty_default_seeds(self):

        seeds = build_thesis_seeds()

        self.assertEqual(
            len(seeds),
            30
        )

        self.assertEqual(
            seeds[0],
            2000
        )

        self.assertEqual(
            seeds[-1],
            2029
        )

    def test_seed_count_must_be_positive(self):

        with self.assertRaises(ValueError):

            build_thesis_seeds(
                count=0
            )


class TestCompleteConfiguration(unittest.TestCase):

    def test_configuration_is_valid(self):

        configuration = (
            build_three_scenario_configuration(
                max_steps=50,
                seed_count=3
            )
        )

        self.assertEqual(
            len(
                configuration["scenarios"]
            ),
            3
        )

        self.assertEqual(
            len(
                configuration["seeds"]
            ),
            3
        )

        self.assertTrue(
            configuration[
                "preliminary_results"
            ]
        )

    def test_explicit_validation(self):

        parameters = (
            build_three_scenario_parameters()
        )

        scenarios = build_thesis_scenarios(
            parameters=parameters,
            max_steps=10
        )

        self.assertTrue(
            validate_thesis_scenarios(
                parameters=parameters,
                scenarios=scenarios,
                policies=(
                    build_thesis_policy()
                ),
                seeds=[
                    1,
                    2
                ]
            )
        )


if __name__ == "__main__":

    unittest.main()
