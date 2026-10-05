# unittest est l'outil de test fourni avec Python.
import unittest

# math permet de recalculer
# la corrélation minimale attendue.
import math


# On importe la classe Parameters.
from physec_dm.parameters import Parameters


# Cette classe regroupe tous les tests
# concernant parameters.py.
class TestParameters(unittest.TestCase):

    # Cette fonction crée une configuration neuve
    # pour chaque test.
    def create_parameters(self):

        return Parameters()

    # Vérification des valeurs principales.
    def test_nominal_parameter_values(self):

        parameters = self.create_parameters()

        self.assertEqual(
            parameters.carrier_frequency_hz,
            868000000.0
        )

        self.assertEqual(
            parameters.bandwidth_hz,
            125000.0
        )

        self.assertEqual(
            parameters.rff_feature_count,
            3
        )

        self.assertEqual(
            parameters.mac_tag_bytes,
            8
        )

        self.assertEqual(
            parameters.mac_tag_bits,
            64
        )

        self.assertEqual(
            parameters.data_payload_bytes,
            32
        )

        self.assertEqual(
            parameters.message_period_s,
            60.0
        )

    # Vérification des conversions en ampères.
    def test_current_unit_conversions(self):

        parameters = self.create_parameters()

        self.assertEqual(
            parameters.tx_current_a,
            0.029
        )

        self.assertEqual(
            parameters.rx_current_a,
            0.0108
        )

        self.assertEqual(
            parameters.cpu_current_a,
            5.92e-3
        )

    # Vérification de la taille du tag.
    def test_mac_tag_size_consistency(self):

        parameters = self.create_parameters()

        self.assertEqual(
            parameters.mac_tag_bits,
            8 * parameters.mac_tag_bytes
        )

    # Vérification de :
    #
    # rho_min = cos(pi * KDR_max)
    def test_minimum_correlation_is_derived_from_kdr(self):

        parameters = self.create_parameters()

        expected_value = math.cos(
            math.pi * parameters.maximum_kdr
        )

        self.assertTrue(
            math.isclose(
                parameters.minimum_correlation,
                expected_value,
                rel_tol=1e-12,
                abs_tol=1e-12
            )
        )

    # Vérification de la réserve batterie.
    def test_battery_reserve_is_derived(self):

        parameters = self.create_parameters()

        expected_value = (
            parameters.battery_reserve_fraction
            * parameters.initial_battery_energy_j
        )

        self.assertTrue(
            math.isclose(
                parameters.minimum_battery_energy_j,
                expected_value,
                rel_tol=1e-12,
                abs_tol=1e-12
            )
        )

        # Les nombres décimaux peuvent contenir
        # une très petite différence liée au stockage binaire.
        #
        # assertAlmostEqual compare donc les valeurs
        # avec une précision adaptée.
        self.assertAlmostEqual(
            parameters.minimum_battery_energy_j,
            1425.6,
            places=9
        )

    # Limites d'un message normal.
    def test_normal_message_limits(self):

        parameters = self.create_parameters()

        self.assertEqual(
            parameters.get_authentication_latency_limit(0),
            600.0
        )

        self.assertEqual(
            parameters.get_far_limit(0),
            0.05
        )

    # Limites d'un message critique.
    def test_critical_message_limits(self):

        parameters = self.create_parameters()

        self.assertEqual(
            parameters.get_authentication_latency_limit(1),
            5.0
        )

        self.assertEqual(
            parameters.get_far_limit(1),
            0.01
        )

    # Une mauvaise criticité doit être refusée.
    def test_invalid_criticality_is_rejected(self):

        parameters = self.create_parameters()

        with self.assertRaises(ValueError):
            parameters.get_far_limit(2)

        with self.assertRaises(ValueError):
            parameters.get_authentication_latency_limit(
                -1
            )

    # Les paramètres absents doivent être signalés.
    def test_missing_parameters_are_reported(self):

        parameters = self.create_parameters()

        missing_parameters = (
            parameters.get_missing_parameters()
        )

        self.assertIn(
            "challenge_response_latency_s",
            missing_parameters
        )

        self.assertIn(
            "mac_cycles",
            missing_parameters
        )

        self.assertIn(
            "variation_feasible",
            missing_parameters
        )

        self.assertIn(
            "contextual_weights",
            missing_parameters
        )

        self.assertIn(
            "k2_protocol_id",
            missing_parameters
        )

    # Pendant le développement :
    # avertissements, mais aucune erreur.
    def test_development_validation(self):

        parameters = self.create_parameters()

        errors, warnings = parameters.validate(
            require_complete=False
        )

        self.assertEqual(
            errors,
            []
        )

        self.assertGreater(
            len(warnings),
            0
        )

    # Pour une campagne complète :
    # les valeurs manquantes deviennent des erreurs.
    def test_complete_validation_reports_errors(self):

        parameters = self.create_parameters()

        errors, warnings = parameters.validate(
            require_complete=True
        )

        self.assertGreater(
            len(errors),
            0
        )

        self.assertEqual(
            warnings,
            []
        )

    # Une probabilité hors de [0, 1]
    # doit être détectée.
    def test_invalid_probability_is_detected(self):

        parameters = self.create_parameters()

        parameters.target_frr = 1.5

        errors, warnings = parameters.validate()

        self.assertIn(
            "target_frr doit appartenir à [0, 1].",
            errors
        )

    # Un mauvais indice LoRa doit être détecté.
    def test_invalid_coding_rate_index_is_detected(self):

        parameters = self.create_parameters()

        parameters.coding_rate_index = 7

        errors, warnings = parameters.validate()

        self.assertIn(
            "coding_rate_index doit appartenir "
            "à {1, 2, 3, 4}.",
            errors
        )

    # Le mode distance exige le bilan de liaison.
    def test_distance_mode_requires_link_budget_parameters(self):

        parameters = self.create_parameters()

        parameters.snr_mode = "distance"

        errors, warnings = parameters.validate()

        self.assertIn(
            "tx_power_dbm est requis "
            "pour le mode distance.",
            errors
        )

        self.assertIn(
            "reference_path_loss_db est requis "
            "pour le mode distance.",
            errors
        )

        self.assertIn(
            "path_loss_exponent est requis "
            "pour le mode distance.",
            errors
        )

    # Les limites critiques doivent être
    # plus strictes que les limites normales.
    def test_critical_limits_are_stricter(self):

        parameters = self.create_parameters()

        self.assertLessEqual(
            parameters.critical_far_limit,
            parameters.normal_far_limit
        )

        self.assertLessEqual(
            parameters.critical_latency_budget_s,
            parameters.normal_latency_budget_s
        )

    # Vérification de l'export en dictionnaire.
    def test_parameters_can_be_exported_to_dictionary(self):

        parameters = self.create_parameters()

        parameters_dictionary = (
            parameters.to_dictionary()
        )

        self.assertEqual(
            parameters_dictionary[
                "carrier_frequency_hz"
            ],
            868000000.0
        )

        self.assertEqual(
            parameters_dictionary[
                "initial_battery_energy_j"
            ],
            28512.0
        )

        # On modifie uniquement la copie.
        parameters_dictionary[
            "carrier_frequency_hz"
        ] = 1.0

        # La valeur originale ne doit pas changer.
        self.assertEqual(
            parameters.carrier_frequency_hz,
            868000000.0
        )


# Cette condition permet aussi de lancer
# directement ce fichier.
if __name__ == "__main__":

    unittest.main()
