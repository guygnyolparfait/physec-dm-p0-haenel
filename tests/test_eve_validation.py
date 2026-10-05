# Ce fichier teste physec_dm/eve_validation.py :
#
# - la corrélation spatiale de Clarke-Jakes ;
# - l'inversion de bits optimale d'Ève
#   (KDR_eff = min(KDR, 1-KDR)) ;
# - la combinaison du meilleur canal accessible à Ève
#   (minimum des KDR effectifs montant/descendant) ;
# - le KDR d'Ève (même loi de l'arc-sinus que Bob, avant
#   inversion) ;
# - la marge de secret et le critère de sécurité.
#
# Rappel architectural testé implicitement : aucune de ces
# fonctions ne doit jamais être importée par
# physec_dm.decision_maker (vérifié séparément dans
# test_decision_maker_never_imports_eve).
import math
import unittest

from physec_dm.eve_validation import (
    calculate_eve_best_channel_kdr,
    calculate_eve_kdr,
    calculate_effective_kdr_with_inversion,
    calculate_secrecy_margin,
    calculate_spatial_correlation,
    evaluate_eve_secrecy_for_period,
    evaluate_key_secrecy
)

from physec_dm.key_generation import calculate_raw_kdr

from physec_dm.parameters import Parameters


CARRIER_FREQUENCY_HZ = 868000000.0
SPEED_OF_LIGHT_M_S = 299792458.0


class TestSpatialCorrelation(unittest.TestCase):

    # À distance nulle, les deux récepteurs sont
    # co-localisés : la corrélation spatiale doit valoir 1
    # (J0(0) = 1).
    def test_zero_distance_gives_full_correlation(self):

        correlation = calculate_spatial_correlation(
            separation_m=0.0,
            carrier_frequency_hz=CARRIER_FREQUENCY_HZ,
            speed_of_light_m_s=SPEED_OF_LIGHT_M_S
        )

        self.assertAlmostEqual(
            correlation,
            1.0,
            places=9
        )

    # La corrélation doit diminuer lorsque la séparation
    # augmente, avant le premier zéro de J0.
    def test_correlation_decreases_with_distance(self):

        near_correlation = calculate_spatial_correlation(
            separation_m=0.01,
            carrier_frequency_hz=CARRIER_FREQUENCY_HZ,
            speed_of_light_m_s=SPEED_OF_LIGHT_M_S
        )

        far_correlation = calculate_spatial_correlation(
            separation_m=0.15,
            carrier_frequency_hz=CARRIER_FREQUENCY_HZ,
            speed_of_light_m_s=SPEED_OF_LIGHT_M_S
        )

        self.assertLess(
            far_correlation,
            near_correlation
        )

    # Une séparation négative n'a pas de sens physique.
    def test_negative_distance_is_rejected(self):

        with self.assertRaises(ValueError):

            calculate_spatial_correlation(
                separation_m=-1.0,
                carrier_frequency_hz=(
                    CARRIER_FREQUENCY_HZ
                ),
                speed_of_light_m_s=(
                    SPEED_OF_LIGHT_M_S
                )
            )


class TestBitInversion(unittest.TestCase):

    # rho=1 (accord parfait) : KDR=0, aucune inversion
    # n'est nécessaire ni bénéfique.
    def test_rho_one_gives_zero_effective_kdr(self):

        raw_kdr = calculate_raw_kdr(1.0)

        self.assertAlmostEqual(
            raw_kdr,
            0.0,
            places=9
        )

        self.assertAlmostEqual(
            calculate_effective_kdr_with_inversion(
                raw_kdr
            ),
            0.0,
            places=9
        )

    # rho=0 (aucune information) : KDR=0,5 dans les deux
    # cas, le point le plus sûr pour la sécurité.
    def test_rho_zero_gives_half_effective_kdr(self):

        raw_kdr = calculate_raw_kdr(0.0)

        self.assertAlmostEqual(
            raw_kdr,
            0.5,
            places=9
        )

        self.assertAlmostEqual(
            calculate_effective_kdr_with_inversion(
                raw_kdr
            ),
            0.5,
            places=9
        )

    # rho=-1 (anti-corrélation parfaite) : KDR brut vaut 1
    # (désaccord total sans inversion), mais après
    # inversion, KDR_eff doit valoir 0 — aussi dangereux
    # que rho=+1. C'est le cas central de la correction
    # demandée : une corrélation négative forte n'est PAS
    # automatiquement sûre.
    def test_rho_minus_one_is_as_dangerous_as_rho_one(self):

        raw_kdr_minus_one = calculate_raw_kdr(-1.0)

        self.assertAlmostEqual(
            raw_kdr_minus_one,
            1.0,
            places=9
        )

        effective_kdr_minus_one = (
            calculate_effective_kdr_with_inversion(
                raw_kdr_minus_one
            )
        )

        effective_kdr_plus_one = (
            calculate_effective_kdr_with_inversion(
                calculate_raw_kdr(1.0)
            )
        )

        self.assertAlmostEqual(
            effective_kdr_minus_one,
            effective_kdr_plus_one,
            places=9
        )

        self.assertAlmostEqual(
            effective_kdr_minus_one,
            0.0,
            places=9
        )

    # calculate_eve_kdr doit appliquer l'inversion (elle
    # diffère donc de key_generation.calculate_raw_kdr dès
    # que rho < 0).
    def test_eve_kdr_applies_inversion_unlike_bob(self):

        rho = -0.8

        bob_style_kdr = calculate_raw_kdr(rho)

        eve_kdr = calculate_eve_kdr(rho)

        self.assertGreater(
            bob_style_kdr,
            0.5
        )

        self.assertAlmostEqual(
            eve_kdr,
            1 - bob_style_kdr,
            places=9
        )

        self.assertLessEqual(
            eve_kdr,
            0.5
        )

    def test_out_of_range_raw_kdr_is_rejected(self):

        with self.assertRaises(ValueError):

            calculate_effective_kdr_with_inversion(1.5)


class TestBestAccessibleChannel(unittest.TestCase):

    # Le KDR effectif retenu doit être le MINIMUM des deux
    # KDR effectifs (montant/descendant) : Ève retient son
    # meilleur canal accessible, jamais le pire.
    def test_best_channel_is_the_minimum_kdr(self):

        result = calculate_eve_best_channel_kdr(
            distance_be_m=0.05,
            distance_ae_m=0.30,
            hardware_reciprocity=0.9582,
            noise_correlation=0.9,
            carrier_frequency_hz=CARRIER_FREQUENCY_HZ,
            speed_of_light_m_s=SPEED_OF_LIGHT_M_S
        )

        self.assertEqual(
            result["kdr_eve_best"],
            min(
                result["kdr_eve_uplink"],
                result["kdr_eve_downlink"]
            )
        )

    # Combiner par max(rho) (signé) AVANT l'inversion serait
    # erroné : le KDR effectif après inversion est une
    # fonction de |rho| (paire), pas de rho. Une liaison à
    # rho faiblement négatif peut donc apparaître "meilleure"
    # au sens max(rho) qu'une liaison à rho fortement
    # négatif, alors que c'est l'inverse une fois l'inversion
    # appliquée. Ce cas est construit avec deux distances
    # réelles (aucune réciprocité matérielle hors domaine) :
    # à d_be=0,16 m, rho_montant ≈ -0,197 ; à d_ae ≈ 0,2105 m
    # (creux de J0), rho_descendant ≈ -0,347. max(rho) signé
    # choisirait à tort la liaison montante (-0,197 > -0,347).
    def test_max_rho_first_would_be_wrong_combination(self):

        result = calculate_eve_best_channel_kdr(
            distance_be_m=0.16,
            distance_ae_m=0.21053285668061625,
            hardware_reciprocity=0.9582,
            noise_correlation=0.9,
            carrier_frequency_hz=CARRIER_FREQUENCY_HZ,
            speed_of_light_m_s=SPEED_OF_LIGHT_M_S
        )

        # Les deux corrélations sont négatives, et le
        # maximum SIGNÉ correspond à la liaison montante.
        self.assertLess(
            result["rho_eve_uplink"],
            0.0
        )

        self.assertLess(
            result["rho_eve_downlink"],
            0.0
        )

        naive_max_rho_picks_uplink = (
            result["rho_eve_uplink"]
            > result["rho_eve_downlink"]
        )

        self.assertTrue(
            naive_max_rho_picks_uplink
        )

        # Mais le canal réellement le plus dangereux (KDR
        # effectif le plus faible) est la liaison
        # descendante : une combinaison par max(rho) signé
        # aurait choisi le mauvais canal et sous-estimé Ève.
        self.assertEqual(
            result["kdr_eve_best"],
            result["kdr_eve_downlink"]
        )

        self.assertLess(
            result["kdr_eve_downlink"],
            result["kdr_eve_uplink"]
        )

    # Plusieurs distances : la corrélation spatiale, donc
    # le KDR d'Ève, doit varier de façon cohérente avec la
    # séparation (aucune distance n'est présentée comme
    # sûre par construction).
    def test_kdr_varies_with_distance(self):

        close_result = calculate_eve_best_channel_kdr(
            distance_be_m=0.01,
            distance_ae_m=0.01,
            hardware_reciprocity=0.9582,
            noise_correlation=0.9,
            carrier_frequency_hz=CARRIER_FREQUENCY_HZ,
            speed_of_light_m_s=SPEED_OF_LIGHT_M_S
        )

        far_result = calculate_eve_best_channel_kdr(
            distance_be_m=1.0,
            distance_ae_m=1.0,
            hardware_reciprocity=0.9582,
            noise_correlation=0.9,
            carrier_frequency_hz=CARRIER_FREQUENCY_HZ,
            speed_of_light_m_s=SPEED_OF_LIGHT_M_S
        )

        self.assertNotAlmostEqual(
            close_result["kdr_eve_best"],
            far_result["kdr_eve_best"],
            places=6
        )


class TestEveKdrAndMargin(unittest.TestCase):

    # Ève doit utiliser exactement la même loi de
    # l'arc-sinus que Bob (key_generation.calculate_raw_kdr).
    def test_eve_kdr_matches_arcsine_law(self):

        kdr_eve = calculate_eve_kdr(0.6)

        self.assertAlmostEqual(
            kdr_eve,
            math.acos(0.6) / math.pi,
            places=12
        )

    def test_secrecy_margin_is_difference(self):

        margin = calculate_secrecy_margin(
            kdr_eve=0.35,
            kdr_ab=0.10
        )

        self.assertAlmostEqual(
            margin,
            0.25,
            places=12
        )

    # Condition nécessaire absolue : si Ève se trompe au
    # plus autant que Bob, aucun secret ne peut être
    # revendiqué, quelle que soit la marge exigée.
    def test_eve_at_least_as_good_as_bob_is_never_secure(self):

        self.assertFalse(
            evaluate_key_secrecy(
                kdr_eve=0.10,
                kdr_ab=0.10,
                minimum_margin=0.0
            )
        )

        self.assertFalse(
            evaluate_key_secrecy(
                kdr_eve=0.05,
                kdr_ab=0.10,
                minimum_margin=0.0
            )
        )

    def test_margin_above_threshold_is_secure(self):

        self.assertTrue(
            evaluate_key_secrecy(
                kdr_eve=0.30,
                kdr_ab=0.10,
                minimum_margin=0.10
            )
        )

    def test_margin_below_threshold_is_not_secure(self):

        self.assertFalse(
            evaluate_key_secrecy(
                kdr_eve=0.15,
                kdr_ab=0.10,
                minimum_margin=0.10
            )
        )

    def test_negative_minimum_margin_is_rejected(self):

        with self.assertRaises(ValueError):

            evaluate_key_secrecy(
                kdr_eve=0.30,
                kdr_ab=0.10,
                minimum_margin=-0.01
            )


class TestFullPeriodEvaluation(unittest.TestCase):

    # Vérifie que la fonction d'orchestration retourne
    # toutes les clés attendues et reste cohérente avec les
    # fonctions élémentaires.
    def test_evaluate_eve_secrecy_for_period_structure(self):

        parameters = Parameters()

        result = evaluate_eve_secrecy_for_period(
            rho_ab=0.9,
            noise_correlation=0.95,
            parameters=parameters
        )

        for expected_key in [
            "rho_eve_uplink",
            "rho_eve_downlink",
            "kdr_ab",
            "kdr_eve",
            "secrecy_margin",
            "secure"
        ]:

            self.assertIn(
                expected_key,
                result
            )

        self.assertAlmostEqual(
            result["secrecy_margin"],
            result["kdr_eve"] - result["kdr_ab"],
            places=12
        )

    # L'hypothèse symétrique par défaut doit utiliser
    # eve_standoff_distance_m pour les deux directions.
    def test_default_symmetric_standoff_is_used(self):

        parameters = Parameters()
        parameters.eve_standoff_distance_m = 0.20

        result_default = (
            evaluate_eve_secrecy_for_period(
                rho_ab=0.9,
                noise_correlation=0.95,
                parameters=parameters
            )
        )

        result_explicit = (
            evaluate_eve_secrecy_for_period(
                rho_ab=0.9,
                noise_correlation=0.95,
                parameters=parameters,
                distance_be_m=0.20,
                distance_ae_m=0.20
            )
        )

        self.assertAlmostEqual(
            result_default["rho_eve_uplink"],
            result_explicit["rho_eve_uplink"],
            places=12
        )

        self.assertAlmostEqual(
            result_default["rho_eve_downlink"],
            result_explicit["rho_eve_downlink"],
            places=12
        )


# Cette classe vérifie la séparation architecturale exigée :
# aucune fonction du Decision Maker ne doit importer
# eve_validation, et le contexte présenté au DM ne doit
# jamais contenir de champ lié à Ève.
class TestArchitecturalSeparationFromDecisionMaker(
    unittest.TestCase
):

    def test_decision_maker_module_does_not_import_eve(self):

        import physec_dm.decision_maker as decision_maker_module

        source_path = decision_maker_module.__file__

        with open(source_path, encoding="utf-8") as source_file:

            source_text = source_file.read()

        self.assertNotIn(
            "eve_validation",
            source_text
        )

    def test_context_construction_does_not_import_eve(self):

        import physec_dm.mission as mission_module

        source_path = mission_module.__file__

        with open(source_path, encoding="utf-8") as source_file:

            source_lines = source_file.readlines()

        # create_mission_context (construction du Context
        # présenté au DM) ne doit contenir aucune référence
        # à Ève dans son corps.
        inside_function = False
        function_lines = []

        for line in source_lines:

            if line.startswith("def create_mission_context"):

                inside_function = True
                continue

            if inside_function:

                if (
                    line.startswith("def ")
                    or line.startswith("# ====")
                ):

                    break

                function_lines.append(line)

        function_source = "".join(function_lines)

        self.assertNotIn(
            "eve",
            function_source.lower()
        )


if __name__ == "__main__":

    unittest.main()
