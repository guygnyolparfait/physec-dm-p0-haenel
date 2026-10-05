import unittest

from haenel_comparison.energy_option_a import (
    E_RFF_BASE_MJ,
    compute_energy_option_a_for_case,
    validate_option_a,
)
from haenel_comparison.haenel_config import HAENEL_FRR_CONFIGS


class TestEnergyOptionA(unittest.TestCase):

    def test_reproduces_published_values_within_one_percent(self):
        """Option A doit reproduire les valeurs publiées à moins
        de 1% d'erreur relative pour les cas HYBRID et RFF_ONLY
        (MAC_ONLY est un cas à part, voir test dédié)."""

        for row in validate_option_a():
            if row["option_a_mJ"] is None:
                continue
            self.assertLess(
                row["relative_error_pct"],
                1.0,
                f"{row['case']}: erreur relative "
                f"{row['relative_error_pct']:.3f}% >= 1%.",
            )

    def test_mac_only_not_forced_into_the_model(self):
        """MAC_ONLY ne doit jamais recevoir de valeur Option A
        fabriquée -- la fonction doit renvoyer None."""

        self.assertIsNone(
            compute_energy_option_a_for_case("MAC_ONLY")
        )

    def test_energy_ordering_matches_published_ordering(self):
        """RFF_ONLY < HYBRID_FRR_05 < HYBRID_FRR_10 < MAC_ONLY,
        aussi bien sur les valeurs publiées que sur Option A."""

        published = {
            name: data["published_energy_mJ"]
            for name, data in HAENEL_FRR_CONFIGS.items()
        }

        self.assertLess(
            published["RFF_ONLY"], published["HYBRID_FRR_05"]
        )
        self.assertLess(
            published["HYBRID_FRR_05"], published["HYBRID_FRR_10"]
        )
        self.assertLess(
            published["HYBRID_FRR_10"], published["MAC_ONLY"]
        )

        option_a_05 = compute_energy_option_a_for_case(
            "HYBRID_FRR_05"
        )
        option_a_10 = compute_energy_option_a_for_case(
            "HYBRID_FRR_10"
        )

        self.assertLess(E_RFF_BASE_MJ, option_a_05)
        self.assertLess(option_a_05, option_a_10)
        self.assertLess(option_a_10, published["MAC_ONLY"])

    def test_no_nan_or_negative_energy(self):

        for case_name in HAENEL_FRR_CONFIGS:
            value = compute_energy_option_a_for_case(case_name)
            if value is None:
                continue
            self.assertGreater(value, 0.0)


if __name__ == "__main__":
    unittest.main()
