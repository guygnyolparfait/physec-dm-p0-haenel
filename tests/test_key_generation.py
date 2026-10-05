
import math
import unittest

from physec_dm.models import KeyAction
from physec_dm.parameters import Parameters
from physec_dm.key_generation import (
    calculate_agreement_feasibility,
    calculate_analytic_agreement_from_correlation,
    calculate_binary_entropy,
    calculate_effective_kdr,
    calculate_key_aging_index,
    calculate_key_deadline,
    calculate_key_expired,
    calculate_key_metrics,
    calculate_k0_quality,
    calculate_k1_quality,
    calculate_k2_quality,
    calculate_message_utilization,
    calculate_minimum_correlation,
    calculate_phy_feasibility,
    calculate_raw_kdr,
    calculate_reconciliation_yield,
    calculate_remaining_age_time,
    calculate_remaining_message_time,
    calculate_renewal_required,
    calculate_required_measurements,
    calculate_time_utilization
)


class TestRawKdr(unittest.TestCase):

    def test_rho_one_gives_zero_kdr(self):
        self.assertEqual(calculate_raw_kdr(1.0), 0.0)

    def test_rho_zero_gives_half_kdr(self):
        self.assertEqual(calculate_raw_kdr(0.0), 0.5)

    def test_rho_minus_one_gives_one_kdr(self):
        self.assertEqual(calculate_raw_kdr(-1.0), 1.0)

    def test_rho_point_six_is_about_thirty_percent(self):
        self.assertAlmostEqual(
            calculate_raw_kdr(0.60),
            0.2951672353,
            places=10
        )

    def test_invalid_correlation_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_raw_kdr(1.2)


class TestEffectiveKdr(unittest.TestCase):

    def test_analytic_mode_keeps_raw_kdr(self):
        self.assertEqual(
            calculate_effective_kdr(
                raw_kdr=0.25,
                quantization_mode="analytic",
                guard_band_factor=0.30
            ),
            0.25
        )

    def test_calibrated_mode_applies_factor(self):
        self.assertEqual(
            calculate_effective_kdr(
                raw_kdr=0.50,
                quantization_mode="calibrated",
                guard_band_factor=0.30
            ),
            0.15
        )

    def test_unknown_quantization_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_effective_kdr(
                raw_kdr=0.20,
                quantization_mode="unknown",
                guard_band_factor=1.0
            )

    def test_minimum_correlation_matches_policy(self):
        value = calculate_minimum_correlation(0.30)
        self.assertAlmostEqual(
            value,
            math.cos(0.30 * math.pi),
            places=12
        )


class TestEntropyAndYield(unittest.TestCase):

    def test_binary_entropy_at_zero(self):
        self.assertEqual(
            calculate_binary_entropy(0.0),
            0.0
        )

    def test_binary_entropy_at_half(self):
        self.assertEqual(
            calculate_binary_entropy(0.5),
            1.0
        )

    def test_binary_entropy_is_symmetric(self):
        self.assertAlmostEqual(
            calculate_binary_entropy(0.20),
            calculate_binary_entropy(0.80),
            places=12
        )

    def test_yield_at_zero_kdr(self):
        self.assertEqual(
            calculate_reconciliation_yield(
                effective_kdr=0.0,
                kept_measurement_ratio=0.70
            ),
            0.70
        )

    def test_yield_at_half_kdr(self):
        self.assertEqual(
            calculate_reconciliation_yield(
                effective_kdr=0.5,
                kept_measurement_ratio=0.70
            ),
            0.0
        )

    def test_required_measurements_uses_ceiling(self):
        self.assertEqual(
            calculate_required_measurements(
                key_length_bits=128,
                reconciliation_yield=0.25,
                numerical_epsilon=1e-12
            ),
            512
        )

    def test_invalid_epsilon_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_required_measurements(
                key_length_bits=128,
                reconciliation_yield=0.25,
                numerical_epsilon=0.0
            )


class TestFeasibility(unittest.TestCase):

    def test_agreement_is_true_at_boundary(self):
        self.assertTrue(
            calculate_agreement_feasibility(
                effective_kdr=0.30,
                maximum_kdr=0.30
            )
        )

    def test_agreement_is_false_above_boundary(self):
        self.assertFalse(
            calculate_agreement_feasibility(
                effective_kdr=0.31,
                maximum_kdr=0.30
            )
        )

    def test_analytic_correlation_boundary(self):
        minimum_correlation = math.cos(
            math.pi * 0.30
        )

        self.assertTrue(
            calculate_analytic_agreement_from_correlation(
                rho_ab=minimum_correlation,
                minimum_correlation=minimum_correlation
            )
        )

    def test_complete_phy_feasibility(self):
        self.assertTrue(
            calculate_phy_feasibility(
                agreement_feasible=True,
                variation_feasible=True
            )
        )

        self.assertFalse(
            calculate_phy_feasibility(
                agreement_feasible=True,
                variation_feasible=False
            )
        )

    def test_provisional_phy_uses_agreement_only(self):
        self.assertTrue(
            calculate_phy_feasibility(
                agreement_feasible=True,
                variation_feasible=None
            )
        )


class TestCryptoperiod(unittest.TestCase):

    def test_time_utilization(self):
        self.assertEqual(
            calculate_time_utilization(
                key_age_s=50.0,
                maximum_key_age_s=100.0
            ),
            0.5
        )

    def test_message_utilization(self):
        self.assertEqual(
            calculate_message_utilization(
                messages_with_current_key=20,
                maximum_messages_per_key=100
            ),
            0.2
        )

    def test_key_aging_uses_maximum(self):
        self.assertEqual(
            calculate_key_aging_index(
                key_age_s=50.0,
                maximum_key_age_s=100.0,
                messages_with_current_key=80,
                maximum_messages_per_key=100
            ),
            0.8
        )

    def test_renewal_is_triggered_at_boundary(self):
        self.assertTrue(
            calculate_renewal_required(
                key_aging_index=0.60,
                renewal_trigger=0.60
            )
        )

    def test_expiration_by_age(self):
        self.assertTrue(
            calculate_key_expired(
                key_age_s=100.0,
                maximum_key_age_s=100.0,
                messages_with_current_key=0,
                maximum_messages_per_key=100,
                compromise_suspected=False
            )
        )

    def test_expiration_by_message_count(self):
        self.assertTrue(
            calculate_key_expired(
                key_age_s=0.0,
                maximum_key_age_s=100.0,
                messages_with_current_key=100,
                maximum_messages_per_key=100,
                compromise_suspected=False
            )
        )

    def test_expiration_by_compromise(self):
        self.assertTrue(
            calculate_key_expired(
                key_age_s=0.0,
                maximum_key_age_s=100.0,
                messages_with_current_key=0,
                maximum_messages_per_key=100,
                compromise_suspected=True
            )
        )

    def test_remaining_age_time(self):
        self.assertEqual(
            calculate_remaining_age_time(
                key_age_s=40.0,
                maximum_key_age_s=100.0
            ),
            60.0
        )

    def test_remaining_message_time(self):
        self.assertEqual(
            calculate_remaining_message_time(
                messages_with_current_key=90,
                maximum_messages_per_key=100,
                message_period_s=60.0
            ),
            600.0
        )

    def test_deadline_uses_first_limit(self):
        self.assertEqual(
            calculate_key_deadline(
                key_age_s=40.0,
                maximum_key_age_s=100.0,
                messages_with_current_key=90,
                maximum_messages_per_key=100,
                message_period_s=60.0,
                minimum_deadline_s=10.0
            ),
            60.0
        )

    def test_deadline_respects_minimum_floor(self):
        self.assertEqual(
            calculate_key_deadline(
                key_age_s=99.0,
                maximum_key_age_s=100.0,
                messages_with_current_key=99,
                maximum_messages_per_key=100,
                message_period_s=60.0,
                minimum_deadline_s=10.0
            ),
            10.0
        )


class TestKeyQuality(unittest.TestCase):

    def test_k0_quality(self):
        self.assertEqual(
            calculate_k0_quality(0.25),
            0.75
        )

    def test_k1_quality(self):
        expected = 1 - calculate_binary_entropy(0.20)

        self.assertAlmostEqual(
            calculate_k1_quality(0.20),
            expected,
            places=12
        )

    def test_k2_quality(self):
        self.assertEqual(
            calculate_k2_quality(64),
            1 - 2 ** (-64)
        )


class TestKeyMetricsBuilder(unittest.TestCase):

    def create_parameters(self):
        parameters = Parameters()
        parameters.minimum_deadline_s = 10.0
        return parameters

    def test_build_k0_metrics(self):
        parameters = self.create_parameters()

        metrics = calculate_key_metrics(
            key_action=KeyAction.K0,
            parameters=parameters,
            key_age_s=43200.0,
            messages_with_current_key=100,
            compromise_suspected=False
        )

        self.assertEqual(
            metrics.key_action,
            KeyAction.K0
        )

        self.assertEqual(
            metrics.key_aging_index,
            0.5
        )

        self.assertEqual(
            metrics.key_quality,
            0.5
        )

        self.assertIsNone(
            metrics.raw_kdr
        )

    def test_build_k1a_metrics(self):
        parameters = self.create_parameters()

        metrics = calculate_key_metrics(
            key_action=KeyAction.K1A,
            parameters=parameters,
            rho_ab=0.80,
            key_age_s=0.0,
            messages_with_current_key=0,
            variation_feasible=True
        )

        self.assertEqual(
            metrics.key_action,
            KeyAction.K1A
        )

        self.assertTrue(
            metrics.agreement_feasible
        )

        self.assertTrue(
            metrics.phy_feasible
        )

        self.assertGreater(
            metrics.required_measurements,
            0
        )

    def test_build_k1b_metrics(self):
        parameters = self.create_parameters()

        metrics = calculate_key_metrics(
            key_action=KeyAction.K1B,
            parameters=parameters,
            rho_ab=0.80,
            key_age_s=0.0,
            messages_with_current_key=0,
            variation_feasible=True
        )

        self.assertEqual(
            metrics.key_action,
            KeyAction.K1B
        )

        self.assertTrue(
            metrics.phy_feasible
        )

    def test_build_k2_metrics(self):
        parameters = self.create_parameters()
        parameters.security_strength_bits = 128

        metrics = calculate_key_metrics(
            key_action=KeyAction.K2,
            parameters=parameters,
            key_age_s=0.0,
            messages_with_current_key=0
        )

        self.assertEqual(
            metrics.key_action,
            KeyAction.K2
        )

        self.assertEqual(
            metrics.key_quality,
            1 - 2 ** (-128)
        )

        self.assertIsNone(
            metrics.phy_feasible
        )

    def test_k2_requires_security_strength(self):
        parameters = self.create_parameters()

        with self.assertRaises(ValueError):
            calculate_key_metrics(
                key_action=KeyAction.K2,
                parameters=parameters,
                key_age_s=0.0,
                messages_with_current_key=0
            )

    def test_k1_requires_rho_ab(self):
        parameters = self.create_parameters()

        with self.assertRaises(ValueError):
            calculate_key_metrics(
                key_action=KeyAction.K1A,
                parameters=parameters,
                key_age_s=0.0,
                messages_with_current_key=0
            )

    def test_calibrated_builder_applies_factor(self):
        parameters = self.create_parameters()
        parameters.quantization_mode = "calibrated"
        parameters.guard_band_factor = 0.5

        metrics = calculate_key_metrics(
            key_action=KeyAction.K1A,
            parameters=parameters,
            rho_ab=0.0,
            key_age_s=0.0,
            messages_with_current_key=0,
            variation_feasible=True
        )

        self.assertEqual(
            metrics.raw_kdr,
            0.5
        )

        self.assertEqual(
            metrics.effective_kdr,
            0.25
        )


if __name__ == "__main__":
    unittest.main()
