# Tests statistiques de la règle B5_HAENEL_CALIBRATEDe, à faire passer
# AVANT tout calcul d'énergie (Étape 3 demandée explicitement).
#
# Le projet utilise unittest (voir tests/test_decision_maker.py) :
# on suit la même convention plutôt que d'introduire pytest.
#
# Exécution : depuis /home/parfait/physec_dm
#   python3 -m unittest haenel_comparison.tests.test_haenel_b5_statistics -v

import math
import unittest

from haenel_comparison.haenel_b5 import (
    simulate_haenel_reference_messages,
    summarize_haenel_events,
)


def _binomial_tolerance(n, p, n_sigma=4.0):
    """Tolérance statistique raisonnable autour de p, pour n
    tirages Bernoulli(p) : n_sigma écarts-types de la loi
    binomiale. n_sigma=4 laisse une marge large pour éviter un
    test qui échoue par pur hasard (~1 chance sur 16000)."""

    std = math.sqrt(p * (1.0 - p) / n)
    return n_sigma * std


class TestHaenelB5Statistics(unittest.TestCase):

    def test_frr_005_converges_to_5_percent(self):

        n_messages = 100_000
        frr = 0.05

        events = simulate_haenel_reference_messages(
            frr=frr, n_messages=n_messages, seed=12345
        )
        summary = summarize_haenel_events(events)

        observed = summary["observed_fallback_rate"]
        tolerance = _binomial_tolerance(n_messages, frr)

        self.assertLess(
            abs(observed - frr),
            tolerance,
            f"Taux de repli observé {observed:.5f} trop loin de "
            f"FRR={frr} (tolérance +/-{tolerance:.5f}).",
        )

    def test_frr_010_converges_to_10_percent(self):

        n_messages = 100_000
        frr = 0.10

        events = simulate_haenel_reference_messages(
            frr=frr, n_messages=n_messages, seed=54321
        )
        summary = summarize_haenel_events(events)

        observed = summary["observed_fallback_rate"]
        tolerance = _binomial_tolerance(n_messages, frr)

        self.assertLess(
            abs(observed - frr),
            tolerance,
            f"Taux de repli observé {observed:.5f} trop loin de "
            f"FRR={frr} (tolérance +/-{tolerance:.5f}).",
        )

    def test_frr_none_is_mac_only(self):
        """frr=None doit forcer A1 pour 100% des messages (MAC_ONLY)."""

        events = simulate_haenel_reference_messages(
            frr=None, n_messages=1000, seed=1
        )
        summary = summarize_haenel_events(events)

        self.assertEqual(summary["n_fallback_mac"], 1000)
        self.assertEqual(summary["n_rff_direct"], 0)
        self.assertTrue(
            all(event.chosen_auth == "A1" for event in events)
        )

    def test_frr_zero_is_rff_only(self):
        """frr=0.0 doit forcer A2 pour 100% des messages (RFF_ONLY,
        "no fall back to cryptographic authentication")."""

        events = simulate_haenel_reference_messages(
            frr=0.0, n_messages=1000, seed=2
        )
        summary = summarize_haenel_events(events)

        self.assertEqual(summary["n_fallback_mac"], 0)
        self.assertEqual(summary["n_rff_direct"], 1000)
        self.assertTrue(
            all(event.chosen_auth == "A2" for event in events)
        )

    def test_reproducibility_same_seed_same_events(self):
        """Deux exécutions avec la même graine doivent produire
        exactement les mêmes événements (reproductibilité)."""

        events_a = simulate_haenel_reference_messages(
            frr=0.05, n_messages=100, seed=999
        )
        events_b = simulate_haenel_reference_messages(
            frr=0.05, n_messages=100, seed=999
        )

        for event_a, event_b in zip(events_a, events_b):
            self.assertEqual(event_a.u, event_b.u)
            self.assertEqual(
                event_a.rff_rejected, event_b.rff_rejected
            )
            self.assertEqual(
                event_a.chosen_auth, event_b.chosen_auth
            )

    def test_different_seeds_differ(self):
        """Deux graines différentes ne doivent (presque toujours)
        pas produire exactement la même séquence -- garde-fou
        contre une graine ignorée par erreur."""

        events_a = simulate_haenel_reference_messages(
            frr=0.05, n_messages=200, seed=1
        )
        events_b = simulate_haenel_reference_messages(
            frr=0.05, n_messages=200, seed=2
        )

        same_count = sum(
            1
            for event_a, event_b in zip(events_a, events_b)
            if event_a.rff_rejected == event_b.rff_rejected
        )

        self.assertNotEqual(same_count, len(events_a))

    def test_no_nan_or_negative_counts(self):

        for frr in (None, 0.0, 0.05, 0.10):
            events = simulate_haenel_reference_messages(
                frr=frr, n_messages=100, seed=7
            )
            summary = summarize_haenel_events(events)

            self.assertEqual(summary["n_messages"], 100)
            self.assertGreaterEqual(summary["n_fallback_mac"], 0)
            self.assertGreaterEqual(summary["n_rff_direct"], 0)
            self.assertEqual(
                summary["n_fallback_mac"] + summary["n_rff_direct"],
                100,
            )


if __name__ == "__main__":
    unittest.main()
