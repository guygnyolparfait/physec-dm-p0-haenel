import unittest

from haenel_comparison.security_monte_carlo import (
    FAR_B5_A2,
    N_ATTEMPTS_TOTAL,
    binomial_ci95_clopper_pearson,
    run_b5_monte_carlo,
    run_p0_monte_carlo,
)


class TestSecurityMonteCarlo(unittest.TestCase):
    """Correction 2 (25/09/2026) : l'ancienne Expérience B n'avait
    que ~450 tentatives Mallory au total, insuffisant pour un FAR de
    0,2%. Ces tests verrouillent le volume minimal demandé et la
    validité statistique de la nouvelle campagne."""

    def test_sample_size_meets_minimum_requirement(self):
        """Au moins 50 000 tentatives exigées, 100 000 visées."""
        self.assertGreaterEqual(N_ATTEMPTS_TOTAL, 50_000)

    def test_clopper_pearson_ci_handles_zero_successes(self):
        """Cas P0 : 0 acceptation ne doit pas produire un IC dégénéré
        ou négatif (piège classique de l'approximation normale)."""
        low, high = binomial_ci95_clopper_pearson(0, 100_000)
        self.assertEqual(low, 0.0)
        self.assertGreater(high, 0.0)
        self.assertLess(high, 0.001)

    def test_clopper_pearson_ci_handles_all_successes(self):
        low, high = binomial_ci95_clopper_pearson(100, 100)
        self.assertLess(low, 1.0)
        self.assertEqual(high, 1.0)

    def test_b5_empirical_far_recovers_published_value(self):
        """Avec 100 000 tirages à FAR=0.002, l'IC95% empirique doit
        contenir la valeur publiée -- sinon la méthode de simulation
        elle-même serait suspecte."""
        result = run_b5_monte_carlo()
        self.assertEqual(result["expected_far"], FAR_B5_A2)
        self.assertTrue(result["expected_far_within_ci95"])
        # Contrôle de plausibilité : ~200 acceptations attendues.
        self.assertGreater(result["n_accepted"], 100)
        self.assertLess(result["n_accepted"], 350)

    def test_b5_ci_width_is_narrow_enough_to_be_informative(self):
        """L'ancienne campagne (455 tentatives) donnait un IC95% de
        ~1.5 points de pourcent de large -- inutilisable pour un FAR
        de 0.2%. La nouvelle campagne doit être largement plus
        précise (au moins un ordre de grandeur)."""
        result = run_b5_monte_carlo()
        width = result["ci95_high"] - result["ci95_low"]
        self.assertLess(width, 0.001)

    def test_p0_far_is_clearly_labeled_as_theoretical_bound(self):
        result = run_p0_monte_carlo()
        self.assertIn("THEORIQUE", result["far_status"])
        self.assertIn("ILLUSTRATION MONTE-CARLO", result["far_status"])
        self.assertIn("PAS VALIDATION EXPERIMENTALE", result["far_status"])

    def test_p0_zero_acceptances_does_not_imply_far_is_actually_zero(self):
        """Garde-fou explicite demandé par l'utilisateur : '0
        acceptation' ne doit jamais être présentable comme une
        preuve. L'IC95% supérieur doit rester strictement positif
        (donc ne JAMAIS conclure FAR=0 avec certitude)."""
        result = run_p0_monte_carlo()
        self.assertEqual(result["n_accepted"], 0)
        self.assertGreater(result["ci95_high"], 0.0)

    def test_b5_and_p0_use_independent_random_streams(self):
        b5 = run_b5_monte_carlo()
        p0 = run_p0_monte_carlo()
        self.assertNotEqual(b5["seed"], p0["seed"])

    def test_reproducibility_same_seed_same_result(self):
        r1 = run_b5_monte_carlo()
        r2 = run_b5_monte_carlo()
        self.assertEqual(r1["n_accepted"], r2["n_accepted"])


if __name__ == "__main__":
    unittest.main()
