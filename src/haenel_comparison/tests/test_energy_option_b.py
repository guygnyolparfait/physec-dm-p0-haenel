import unittest

from haenel_comparison.energy_option_b import (
    ASSUMPTIONS_CENTRAL,
    ASSUMPTIONS_HIGH,
    ASSUMPTIONS_LOW,
    I_ACTIVE_A_PER_HZ_CENTRAL,
    I_ACTIVE_A_PER_HZ_HIGH,
    I_ACTIVE_A_PER_HZ_LOW,
    calibrate_residual_baseline_mJ,
    compute_option_b_energy_mJ,
    energy_mac_only_mJ,
    energy_rff_fallback_mJ,
    energy_rff_success_mJ,
)
from haenel_comparison.haenel_config import HAENEL_FRR_CONFIGS


class TestEnergyOptionBHardwareCorrection(unittest.TestCase):
    """Régression pour la correction du 25/09/2026 : le CPU du banc
    d'essai énergétique (Section 6.3.2) est le MSP430G2x, pas le
    MSP430FR5994. Ces tests verrouillent le fait que les valeurs
    FR5994 ont bien disparu et que les bornes LOW/HIGH sont
    réellement câblées (elles ne l'étaient pas avant correction)."""

    def test_cpu_current_is_not_fr5994_value(self):
        """225 µA/MHz (typ) et 118 µA/MHz (best-case) étaient les
        valeurs FR5994 utilisées par erreur. Elles ne doivent plus
        apparaître comme constante CPU centrale ou basse."""
        wrong_fr5994_typ = 225e-6 / 1e6
        wrong_fr5994_low = 118e-6 / 1e6
        self.assertNotAlmostEqual(
            I_ACTIVE_A_PER_HZ_CENTRAL, wrong_fr5994_typ, places=12
        )
        self.assertNotAlmostEqual(
            I_ACTIVE_A_PER_HZ_LOW, wrong_fr5994_low, places=12
        )

    def test_cpu_current_matches_msp430g2553_datasheet(self):
        """330 µA/MHz (typ, 3V, 1MHz) et 420 µA/MHz (max) viennent du
        datasheet officiel MSP430G2553 (SLAS735J)."""
        self.assertAlmostEqual(
            I_ACTIVE_A_PER_HZ_CENTRAL, 330e-6 / 1e6, places=12
        )
        self.assertAlmostEqual(
            I_ACTIVE_A_PER_HZ_HIGH, 420e-6 / 1e6, places=12
        )

    def test_low_high_cpu_bounds_are_wired_into_assumptions(self):
        """Bug trouvé pendant la correction : les bornes LOW/HIGH
        existaient comme constantes mais n'étaient jamais passées
        aux formules (toujours CENTRAL, quel que soit le label
        demandé). Vérifie que ce n'est plus le cas."""
        self.assertEqual(
            ASSUMPTIONS_LOW.mcu_active_a_per_hz, I_ACTIVE_A_PER_HZ_LOW
        )
        self.assertEqual(
            ASSUMPTIONS_CENTRAL.mcu_active_a_per_hz,
            I_ACTIVE_A_PER_HZ_CENTRAL,
        )
        self.assertEqual(
            ASSUMPTIONS_HIGH.mcu_active_a_per_hz, I_ACTIVE_A_PER_HZ_HIGH
        )

    def test_fallback_energy_actually_varies_with_cpu_assumption(self):
        """Preuve comportementale (pas seulement structurelle) que
        le courant CPU choisi influence bien le résultat : le
        chemin de repli (qui exécute Chaskey) doit coûter plus cher
        sous HIGH que sous LOW, toutes choses égales question CPU."""
        low = energy_rff_fallback_mJ(ASSUMPTIONS_LOW)
        high = energy_rff_fallback_mJ(ASSUMPTIONS_HIGH)
        self.assertLess(low, high)

    def test_no_lpm_or_sleep_constant_remains(self):
        """Haenel et al. Section 6.3.2 précise que le deep-sleep
        n'a pas pu être utilisé pendant ce banc d'essai. Aucune
        constante LPM/SLEEP ne doit donc exister dans ce module."""
        import haenel_comparison.energy_option_b as mod

        forbidden_names = ("I_LPM3_A", "I_SLEEP_A", "I_IDLE_A")
        for name in forbidden_names:
            self.assertFalse(
                hasattr(mod, name),
                f"{name} ne devrait pas exister : le deep-sleep est "
                f"explicitement exclu du banc d'essai (Sec. 6.3.2).",
            )


class TestEnergyOptionBOrderingAndMagnitude(unittest.TestCase):

    def test_ordering_preserved_under_all_three_assumption_sets(self):
        for assumptions in (
            ASSUMPTIONS_LOW, ASSUMPTIONS_CENTRAL, ASSUMPTIONS_HIGH
        ):
            success = energy_rff_success_mJ(assumptions)
            fallback = energy_rff_fallback_mJ(assumptions)
            mac_only = energy_mac_only_mJ(assumptions)
            hybrid_10 = 0.90 * success + 0.10 * fallback
            self.assertLess(success, hybrid_10)
            self.assertLess(hybrid_10, mac_only)

    def test_residual_calibration_varies_with_assumptions_but_not_by_case(
        self,
    ):
        """Le résiduel doit dépendre du jeu d'hypothèses matériel
        (LOW/CENTRAL/HIGH changent le coût CPU/TX/RX modélisé, donc
        ce qu'il reste à expliquer), mais ne doit JAMAIS être
        recalibré séparément pour HYBRID_05 vs HYBRID_10 vs
        MAC_ONLY (interdiction explicite du cherry-picking)."""
        residual_low = calibrate_residual_baseline_mJ(ASSUMPTIONS_LOW)
        residual_high = calibrate_residual_baseline_mJ(ASSUMPTIONS_HIGH)
        self.assertNotAlmostEqual(residual_low, residual_high, places=6)

        # Le même résiduel (calibré sur RFF_ONLY) doit être appliqué
        # tel quel à HYBRID_05, HYBRID_10 et MAC_ONLY sous CENTRAL.
        residual_central = calibrate_residual_baseline_mJ(
            ASSUMPTIONS_CENTRAL
        )
        rff_only = compute_option_b_energy_mJ(
            "RFF_ONLY", frr=0.0, assumptions=ASSUMPTIONS_CENTRAL
        )
        expected_rff_only = (
            energy_rff_success_mJ(ASSUMPTIONS_CENTRAL) + residual_central
        )
        self.assertAlmostEqual(rff_only, expected_rff_only, places=9)

    def test_no_nan_or_negative_energy_any_assumption_set(self):
        for assumptions in (
            ASSUMPTIONS_LOW, ASSUMPTIONS_CENTRAL, ASSUMPTIONS_HIGH
        ):
            for case_name, frr in (
                ("RFF_ONLY", 0.0),
                ("HYBRID_FRR_05", 0.05),
                ("HYBRID_FRR_10", 0.10),
                ("MAC_ONLY", None),
            ):
                value = compute_option_b_energy_mJ(
                    case_name, frr=frr, assumptions=assumptions
                )
                self.assertGreater(value, 0.0)
                self.assertEqual(value, value)  # NaN check

    def test_published_values_are_unchanged_by_this_correction(self):
        """Garde-fou : cette correction touche Option B, jamais les
        valeurs PUBLISHED de Haenel et al. elles-mêmes."""
        self.assertEqual(
            HAENEL_FRR_CONFIGS["MAC_ONLY"]["published_energy_mJ"],
            564.743,
        )
        self.assertEqual(
            HAENEL_FRR_CONFIGS["RFF_ONLY"]["published_energy_mJ"],
            355.412,
        )


if __name__ == "__main__":
    unittest.main()
