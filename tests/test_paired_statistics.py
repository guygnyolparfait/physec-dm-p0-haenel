# Ce fichier teste physec_dm/paired_statistics.py : les
# comparaisons appariées P0 vs chaque politique de référence,
# graine par graine, exigées à la place de deux moyennes
# indépendantes.
import unittest

from physec_dm.paired_statistics import (
    compute_paired_differences,
    compute_paired_statistic,
    compute_paired_statistics_for_all_metrics
)


class TestPairedDifferences(unittest.TestCase):

    def test_only_common_seeds_are_used(self):

        p0_values = {1: 10.0, 2: 20.0, 3: 30.0}
        baseline_values = {2: 15.0, 3: 25.0, 4: 40.0}

        common_seeds, differences = (
            compute_paired_differences(
                p0_values,
                baseline_values
            )
        )

        self.assertEqual(
            common_seeds,
            [2, 3]
        )

        self.assertEqual(
            differences,
            [5.0, 5.0]
        )

    def test_no_common_seeds_is_rejected(self):

        with self.assertRaises(ValueError):

            compute_paired_differences(
                {1: 10.0},
                {2: 20.0}
            )

    def test_none_values_are_skipped(self):

        p0_values = {1: 10.0, 2: None, 3: 30.0}
        baseline_values = {1: 5.0, 2: 5.0, 3: 25.0}

        _, differences = compute_paired_differences(
            p0_values,
            baseline_values
        )

        self.assertEqual(
            differences,
            [5.0, 5.0]
        )


class TestPairedStatistic(unittest.TestCase):

    # Un gain constant de 5.0 sur toutes les graines doit
    # produire une moyenne de 5.0 avec une demi-largeur
    # nulle, et exclure zéro (différence clairement établie).
    def test_constant_gain_excludes_zero(self):

        p0_values = {
            seed: 10.0 + 5.0
            for seed in range(30)
        }

        baseline_values = {
            seed: 10.0
            for seed in range(30)
        }

        statistic = compute_paired_statistic(
            p0_values,
            baseline_values
        )

        self.assertEqual(
            statistic["sample_size"],
            30
        )

        self.assertAlmostEqual(
            statistic["mean_difference"],
            5.0,
            places=9
        )

        self.assertEqual(
            statistic["half_width"],
            0.0
        )

        self.assertTrue(
            statistic["excludes_zero"]
        )

    # Deux politiques strictement identiques (différence
    # toujours nulle) ne doivent jamais exclure zéro.
    def test_identical_policies_do_not_exclude_zero(self):

        values = {
            seed: float(seed)
            for seed in range(30)
        }

        statistic = compute_paired_statistic(
            values,
            values
        )

        self.assertAlmostEqual(
            statistic["mean_difference"],
            0.0,
            places=9
        )

        self.assertFalse(
            statistic["excludes_zero"]
        )

    def test_single_seed_never_excludes_zero(self):

        statistic = compute_paired_statistic(
            {1: 10.0},
            {1: 5.0}
        )

        self.assertEqual(
            statistic["sample_size"],
            1
        )

        self.assertFalse(
            statistic["excludes_zero"]
        )


class TestPairedStatisticsForAllMetrics(unittest.TestCase):

    def test_returns_one_entry_per_metric(self):

        p0_summaries = {
            1: {"energy": 10.0, "latency": 0.5},
            2: {"energy": 12.0, "latency": 0.4}
        }

        baseline_summaries = {
            1: {"energy": 8.0, "latency": 0.6},
            2: {"energy": 9.0, "latency": 0.55}
        }

        results = (
            compute_paired_statistics_for_all_metrics(
                p0_summaries,
                baseline_summaries,
                metric_names=["energy", "latency"]
            )
        )

        self.assertIn("energy", results)
        self.assertIn("latency", results)

        self.assertEqual(
            results["energy"]["sample_size"],
            2
        )


if __name__ == "__main__":

    unittest.main()
