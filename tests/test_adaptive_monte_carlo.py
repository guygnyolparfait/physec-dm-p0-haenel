# Ce fichier teste physec_dm/adaptive_monte_carlo.py :
# la règle d'arrêt Monte-Carlo adaptative bornée exigée par
# le protocole (Étape 5).
import math
import unittest

from physec_dm.adaptive_monte_carlo import (
    CONVERGENCE_TOLERANCES,
    MAXIMUM_SEED_COUNT,
    MINIMUM_SEED_COUNT,
    SEED_BATCH_SIZE,
    check_metric_converged,
    compute_mean_ci95_half_width,
    compute_wilson_half_width,
    evaluate_convergence,
    should_stop_sampling
)


class TestMeanCi95HalfWidth(unittest.TestCase):

    def test_single_value_gives_infinite_half_width(self):

        mean_value, half_width = (
            compute_mean_ci95_half_width([5.0])
        )

        self.assertEqual(mean_value, 5.0)
        self.assertEqual(half_width, math.inf)

    def test_constant_values_give_zero_half_width(self):

        mean_value, half_width = (
            compute_mean_ci95_half_width(
                [2.0] * 30
            )
        )

        self.assertEqual(mean_value, 2.0)
        self.assertEqual(half_width, 0.0)

    def test_half_width_shrinks_with_more_samples(self):

        small_sample = [1.0, 2.0, 3.0, 4.0, 5.0]
        large_sample = small_sample * 20

        _, half_width_small = (
            compute_mean_ci95_half_width(small_sample)
        )

        _, half_width_large = (
            compute_mean_ci95_half_width(large_sample)
        )

        self.assertLess(
            half_width_large,
            half_width_small
        )

    def test_empty_values_is_rejected(self):

        with self.assertRaises(ValueError):

            compute_mean_ci95_half_width([])


class TestWilsonHalfWidth(unittest.TestCase):

    # Un compte nul doit rester défini (contrairement à
    # l'approximation normale, instable pour un événement
    # rare).
    def test_zero_successes_is_well_defined(self):

        half_width = compute_wilson_half_width(
            successes=0,
            trials=1000
        )

        self.assertIsNotNone(half_width)
        self.assertGreater(half_width, 0.0)

    def test_zero_trials_returns_none(self):

        self.assertIsNone(
            compute_wilson_half_width(
                successes=0,
                trials=0
            )
        )

    def test_successes_greater_than_trials_is_rejected(self):

        with self.assertRaises(ValueError):

            compute_wilson_half_width(
                successes=10,
                trials=5
            )

    def test_half_width_shrinks_with_more_trials(self):

        half_width_small = compute_wilson_half_width(
            successes=5,
            trials=100
        )

        half_width_large = compute_wilson_half_width(
            successes=50,
            trials=1000
        )

        self.assertLess(
            half_width_large,
            half_width_small
        )


class TestMetricConvergence(unittest.TestCase):

    def test_infinite_half_width_never_converges(self):

        self.assertFalse(
            check_metric_converged(
                mean_value=0.5,
                half_width=math.inf,
                tolerance_spec={
                    "kind": "absolute",
                    "tolerance": 0.01
                }
            )
        )

    def test_absolute_tolerance(self):

        self.assertTrue(
            check_metric_converged(
                mean_value=0.5,
                half_width=0.005,
                tolerance_spec={
                    "kind": "absolute",
                    "tolerance": 0.01
                }
            )
        )

        self.assertFalse(
            check_metric_converged(
                mean_value=0.5,
                half_width=0.02,
                tolerance_spec={
                    "kind": "absolute",
                    "tolerance": 0.01
                }
            )
        )

    def test_relative_tolerance(self):

        self.assertTrue(
            check_metric_converged(
                mean_value=10.0,
                half_width=0.4,
                tolerance_spec={
                    "kind": "relative",
                    "tolerance": 0.05
                }
            )
        )

        self.assertFalse(
            check_metric_converged(
                mean_value=10.0,
                half_width=0.6,
                tolerance_spec={
                    "kind": "relative",
                    "tolerance": 0.05
                }
            )
        )

    def test_zero_mean_relative_tolerance_requires_zero_width(
        self
    ):

        self.assertTrue(
            check_metric_converged(
                mean_value=0.0,
                half_width=0.0,
                tolerance_spec={
                    "kind": "relative",
                    "tolerance": 0.05
                }
            )
        )

        self.assertFalse(
            check_metric_converged(
                mean_value=0.0,
                half_width=0.001,
                tolerance_spec={
                    "kind": "relative",
                    "tolerance": 0.05
                }
            )
        )

    def test_unknown_kind_is_rejected(self):

        with self.assertRaises(ValueError):

            check_metric_converged(
                mean_value=1.0,
                half_width=0.1,
                tolerance_spec={
                    "kind": "unknown",
                    "tolerance": 0.1
                }
            )


class TestEvaluateConvergence(unittest.TestCase):

    def _build_converged_summaries(self, count=30):

        return [
            {
                "service_rate": 0.95,
                "mean_energy_j": 0.02,
                "mean_latency_objective": 0.10,
                "mean_authentication_robustness": 0.999,
                "mean_key_quality": 0.90
            }
            for _ in range(count)
        ]

    def test_all_metrics_present_in_result(self):

        summaries = self._build_converged_summaries()

        result = evaluate_convergence(summaries)

        for metric_name in CONVERGENCE_TOLERANCES:

            self.assertIn(
                metric_name,
                result["per_metric"]
            )

    def test_constant_summaries_all_converge(self):

        summaries = self._build_converged_summaries()

        result = evaluate_convergence(summaries)

        self.assertTrue(
            result["all_converged"]
        )

    def test_single_seed_never_converges(self):

        summaries = self._build_converged_summaries(
            count=1
        )

        result = evaluate_convergence(summaries)

        self.assertFalse(
            result["all_converged"]
        )

    def test_missing_metric_values_are_ignored(self):

        summaries = self._build_converged_summaries(
            count=30
        )

        summaries[0]["mean_key_quality"] = None

        result = evaluate_convergence(summaries)

        self.assertEqual(
            result["per_metric"][
                "mean_key_quality"
            ]["sample_size"],
            29
        )

    def test_empty_summaries_is_rejected(self):

        with self.assertRaises(ValueError):

            evaluate_convergence([])


class TestShouldStopSampling(unittest.TestCase):

    def test_stops_at_maximum_regardless_of_convergence(
        self
    ):

        self.assertTrue(
            should_stop_sampling(
                seed_count=MAXIMUM_SEED_COUNT,
                all_converged=False
            )
        )

    def test_does_not_stop_before_minimum_even_if_converged(
        self
    ):

        self.assertFalse(
            should_stop_sampling(
                seed_count=MINIMUM_SEED_COUNT - 1,
                all_converged=True
            )
        )

    def test_stops_at_minimum_if_converged(self):

        self.assertTrue(
            should_stop_sampling(
                seed_count=MINIMUM_SEED_COUNT,
                all_converged=True
            )
        )

    def test_continues_past_minimum_if_not_converged(self):

        self.assertFalse(
            should_stop_sampling(
                seed_count=MINIMUM_SEED_COUNT
                + SEED_BATCH_SIZE,
                all_converged=False
            )
        )


if __name__ == "__main__":

    unittest.main()
