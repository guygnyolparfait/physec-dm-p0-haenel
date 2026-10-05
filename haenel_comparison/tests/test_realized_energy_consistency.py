# Vérifie qu'une réalisation stochastique message-par-message
# (via haenel_energy_adapter, utilisée par
# run_haenel_experiment_a.py) converge, en espérance sur beaucoup
# de messages, vers les mêmes totaux qu'Option A (calibration
# agrégée directe) -- garde-fou contre le bug déjà corrigé une
# fois (brancher sur chosen_auth au lieu de event.frr avait
# sous-compté l'énergie des messages repliés).

import unittest

from haenel_comparison.haenel_b5 import (
    simulate_haenel_reference_messages,
)
from haenel_comparison.haenel_config import HAENEL_FRR_CONFIGS
from haenel_comparison.haenel_energy_adapter import (
    a1_energy_mJ,
    a2_realized_energy_mJ,
)


def energy_for_event_mJ(event):
    if event.frr is None:
        return a1_energy_mJ()
    return a2_realized_energy_mJ(event.rff_rejected)


class TestRealizedEnergyConsistency(unittest.TestCase):

    def test_large_sample_converges_to_published_per_message_cost(self):
        """Sur un grand nombre de messages (pour lisser le bruit
        stochastique), le coût moyen réalisé par message doit
        converger vers published_energy_mJ / 100."""

        n_messages = 200_000

        for case_name in ("HYBRID_FRR_05", "HYBRID_FRR_10", "RFF_ONLY"):

            frr = HAENEL_FRR_CONFIGS[case_name]["frr"]
            published_per_message = (
                HAENEL_FRR_CONFIGS[case_name]["published_energy_mJ"]
                / 100
            )

            events = simulate_haenel_reference_messages(
                frr=frr, n_messages=n_messages, seed=42
            )

            mean_energy = sum(
                energy_for_event_mJ(e) for e in events
            ) / n_messages

            self.assertAlmostEqual(
                mean_energy, published_per_message, delta=0.02,
                msg=(
                    f"{case_name}: moyenne réalisée {mean_energy:.4f} "
                    f"mJ/message trop loin de la valeur publiée "
                    f"{published_per_message:.4f} mJ/message."
                ),
            )

    def test_mac_only_uses_flat_cost_every_message(self):

        events = simulate_haenel_reference_messages(
            frr=None, n_messages=1000, seed=1
        )
        for event in events:
            self.assertEqual(
                energy_for_event_mJ(event), a1_energy_mJ()
            )

    def test_fallback_message_costs_more_than_direct_rff(self):
        """Un message replié doit coûter STRICTEMENT plus qu'un
        message RFF direct -- c'est précisément le bug déjà
        corrigé qui violait cette propriété (il sous-facturait les
        replis au coût MAC seul, parfois moins cher que RFF seul)."""

        direct_cost = a2_realized_energy_mJ(rff_rejected=False)
        fallback_cost = a2_realized_energy_mJ(rff_rejected=True)

        self.assertGreater(fallback_cost, direct_cost)


if __name__ == "__main__":
    unittest.main()
