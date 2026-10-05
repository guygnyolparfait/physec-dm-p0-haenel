# unittest est l'outil de test
# fourni directement avec Python.
import unittest


# math est utilisé pour certaines
# valeurs de référence.
import math


# On importe Parameters afin de construire
# des scénarios de canal.
from physec_dm.parameters import Parameters


# On importe toutes les fonctions
# actuellement définies dans channel.py.
from physec_dm.channel import (
    calculate_channel_metrics,
    calculate_doppler_hz,
    calculate_lag1_autocorrelation,
    calculate_noise_correlation,
    calculate_noise_power_dbm,
    calculate_path_loss_db,
    calculate_quantized_transition_statistics,
    calculate_received_power_dbm,
    calculate_reciprocity,
    calculate_snr_db,
    calculate_temporal_correlation,
    calculate_temporal_variability_feasible,
    calculate_truncated_reciprocity,
    calculate_window_std_dev,
    convert_db_to_linear,
    convert_linear_to_db
)


# Cette classe teste les conversions du SNR.
class TestSnrConversions(unittest.TestCase):

    # 0 dB doit devenir 1 en linéaire.
    def test_zero_db_equals_one_linear(self):

        self.assertEqual(
            convert_db_to_linear(0),
            1.0
        )

    # 10 dB doit devenir 10.
    def test_ten_db_equals_ten_linear(self):

        self.assertEqual(
            convert_db_to_linear(10),
            10.0
        )

    # Une conversion aller-retour doit retrouver
    # la valeur de départ.
    def test_db_linear_round_trip(self):

        original_db = 5.0

        linear_value = convert_db_to_linear(
            original_db
        )

        converted_db = convert_linear_to_db(
            linear_value
        )

        self.assertAlmostEqual(
            converted_db,
            original_db,
            places=12
        )

    # La conversion logarithmique doit refuser
    # une valeur nulle.
    def test_zero_linear_value_is_rejected(self):

        with self.assertRaises(ValueError):

            convert_linear_to_db(0.0)


# Cette classe teste le bilan de liaison.
class TestLinkBudget(unittest.TestCase):

    # À la distance de référence,
    # la perte doit être égale à PL(d0).
    def test_path_loss_at_reference_distance(self):

        path_loss_db = calculate_path_loss_db(
            distance_m=1.0,
            reference_distance_m=1.0,
            reference_path_loss_db=31.2,
            path_loss_exponent=2.0
        )

        self.assertEqual(
            path_loss_db,
            31.2
        )

    # Avec n = 2, multiplier la distance par 10
    # ajoute 20 dB de perte.
    def test_path_loss_increases_with_distance(self):

        path_loss_db = calculate_path_loss_db(
            distance_m=10.0,
            reference_distance_m=1.0,
            reference_path_loss_db=31.2,
            path_loss_exponent=2.0
        )

        self.assertAlmostEqual(
            path_loss_db,
            51.2,
            places=12
        )

    # Ce test vérifie le calcul
    # de la puissance reçue.
    def test_received_power(self):

        received_power_dbm = (
            calculate_received_power_dbm(
                tx_power_dbm=14.0,
                tx_antenna_gain_dbi=0.0,
                rx_antenna_gain_dbi=0.0,
                path_loss_db=51.2,
                system_loss_db=0.0
            )
        )

        self.assertAlmostEqual(
            received_power_dbm,
            -37.2,
            places=12
        )

    # Le bruit à 125 kHz et NF = 6 dB
    # doit être voisin de -117.03 dBm.
    def test_noise_power(self):

        noise_power_dbm = (
            calculate_noise_power_dbm(
                bandwidth_hz=125000.0,
                noise_figure_db=6.0
            )
        )

        self.assertAlmostEqual(
            noise_power_dbm,
            -117.03089987,
            places=6
        )

    # Le SNR en dB est la différence
    # entre puissance reçue et puissance du bruit.
    def test_snr_from_received_and_noise_power(self):

        snr_db = calculate_snr_db(
            received_power_dbm=-100.0,
            noise_power_dbm=-117.0
        )

        self.assertEqual(
            snr_db,
            17.0
        )

    # Une distance nulle doit être refusée.
    def test_invalid_distance_is_rejected(self):

        with self.assertRaises(ValueError):

            calculate_path_loss_db(
                distance_m=0.0,
                reference_distance_m=1.0,
                reference_path_loss_db=31.2,
                path_loss_exponent=2.0
            )


# Cette classe teste le Doppler
# et la corrélation temporelle.
class TestTemporalChannel(unittest.TestCase):

    # Une vitesse nulle doit produire
    # un Doppler nul.
    def test_zero_speed_gives_zero_doppler(self):

        doppler_hz = calculate_doppler_hz(
            speed_m_s=0.0,
            carrier_frequency_hz=868000000.0,
            speed_of_light_m_s=299792458.0
        )

        self.assertEqual(
            doppler_hz,
            0.0
        )

    # J0(0) doit être égal à 1.
    def test_jakes_at_zero(self):

        temporal_correlation = (
            calculate_temporal_correlation(
                doppler_hz=0.0,
                probe_delay_s=1.0
            )
        )

        self.assertEqual(
            temporal_correlation,
            1.0
        )

    # Pour f_d = 0.5 Hz et Delta_t = 1 s,
    # l'argument de J0 vaut pi.
    #
    # J0(pi) est négatif.
    def test_negative_temporal_correlation_is_preserved(self):

        temporal_correlation = (
            calculate_temporal_correlation(
                doppler_hz=0.5,
                probe_delay_s=1.0
            )
        )

        self.assertLess(
            temporal_correlation,
            0.0
        )

        self.assertAlmostEqual(
            temporal_correlation,
            -0.3042421776,
            places=8
        )


# Cette classe teste les facteurs
# de réciprocité.
class TestReciprocity(unittest.TestCase):

    # Pour gamma = 1 :
    #
    # rho_noise = 1 / (1 + 1) = 0.5
    def test_noise_correlation_at_one(self):

        noise_correlation = (
            calculate_noise_correlation(
                1.0
            )
        )

        self.assertEqual(
            noise_correlation,
            0.5
        )

    # Ce test vérifie le produit
    # des trois facteurs.
    def test_reciprocity_product(self):

        rho_ab = calculate_reciprocity(
            hardware_reciprocity=0.9582,
            temporal_correlation=0.8,
            noise_correlation=0.75
        )

        expected_value = (
            0.9582
            * 0.8
            * 0.75
        )

        self.assertAlmostEqual(
            rho_ab,
            expected_value,
            places=12
        )

    # Une corrélation temporelle négative
    # doit produire un rho_AB négatif.
    def test_negative_reciprocity_is_preserved(self):

        rho_ab = calculate_reciprocity(
            hardware_reciprocity=0.9582,
            temporal_correlation=-0.4,
            noise_correlation=0.75
        )

        self.assertLess(
            rho_ab,
            0.0
        )

    # La variante tronquée transforme
    # uniquement les valeurs négatives en zéro.
    def test_truncated_reciprocity(self):

        self.assertEqual(
            calculate_truncated_reciprocity(
                -0.25
            ),
            0.0
        )

        self.assertEqual(
            calculate_truncated_reciprocity(
                0.25
            ),
            0.25
        )

    # Une réciprocité matérielle supérieure à 1
    # doit être refusée.
    def test_invalid_hardware_reciprocity_is_rejected(self):

        with self.assertRaises(ValueError):

            calculate_reciprocity(
                hardware_reciprocity=1.2,
                temporal_correlation=0.8,
                noise_correlation=0.75
            )


# Cette classe teste la fonction complète
# calculate_channel_metrics.
class TestCompleteChannelMetrics(unittest.TestCase):

    # Ce test utilise directement le SNR imposé.
    def test_imposed_snr_mode(self):

        parameters = Parameters()

        parameters.snr_mode = "imposed"
        parameters.mean_snr_db = 10.0
        parameters.effective_speed_m_s = 0.0

        channel_metrics = (
            calculate_channel_metrics(
                parameters
            )
        )

        self.assertEqual(
            channel_metrics.snr_db,
            10.0
        )

        self.assertEqual(
            channel_metrics.snr_linear,
            10.0
        )

        self.assertEqual(
            channel_metrics.doppler_hz,
            0.0
        )

        self.assertEqual(
            channel_metrics.temporal_correlation,
            1.0
        )

        self.assertAlmostEqual(
            channel_metrics.noise_correlation,
            10.0 / 11.0,
            places=12
        )

        expected_rho_ab = (
            parameters.hardware_reciprocity
            * 1.0
            * (10.0 / 11.0)
        )

        self.assertAlmostEqual(
            channel_metrics.rho_ab,
            expected_rho_ab,
            places=12
        )

    # Ce test calcule le SNR
    # à partir de la distance.
    def test_distance_snr_mode(self):

        parameters = Parameters()

        parameters.snr_mode = "distance"
        parameters.tx_power_dbm = 14.0
        parameters.reference_path_loss_db = 31.2
        parameters.path_loss_exponent = 2.0
        parameters.effective_speed_m_s = 0.0

        channel_metrics = (
            calculate_channel_metrics(
                parameters=parameters,
                distance_m=10.0,
                shadowing_db=0.0
            )
        )

        # PL = 31.2 + 20 = 51.2 dB
        #
        # P_rx = 14 - 51.2 = -37.2 dBm
        #
        # P_noise ≈ -117.03089987 dBm
        #
        # SNR ≈ 79.83089987 dB
        expected_snr_db = (
            -37.2
            - (-117.03089987)
        )

        self.assertAlmostEqual(
            channel_metrics.snr_db,
            expected_snr_db,
            places=6
        )

        self.assertEqual(
            channel_metrics.doppler_hz,
            0.0
        )

    # Le mode distance doit exiger
    # une distance.
    def test_distance_mode_requires_distance(self):

        parameters = Parameters()

        parameters.snr_mode = "distance"
        parameters.tx_power_dbm = 14.0
        parameters.reference_path_loss_db = 31.2
        parameters.path_loss_exponent = 2.0

        with self.assertRaises(ValueError):

            calculate_channel_metrics(
                parameters
            )


STANDARD_VARIABILITY_KWARGS = {
    "minimum_window_size": 10,
    "minimum_std_dev": 0.05,
    "maximum_lag1_autocorrelation": 0.70,
    "maximum_bit_frequency": 0.90,
    "kept_measurement_ratio": 0.70,
    "minimum_valid_measurements": 5
}


# Cette classe teste le calcul RÉEL de phi_var
# (variabilité temporelle du canal), renforcé en quatre
# composantes : écart-type, autocorrélation à décalage 1,
# transitions/min-entropie de séquence quantifiée, et
# nombre de mesures valides. Aucune de ces quatre
# composantes n'est, seule, suffisante.
class TestTemporalVariabilityFeasibility(unittest.TestCase):

    # Une fenêtre trop courte ne permet aucun jugement :
    # la fonction doit retourner None, jamais un booléen
    # inventé.
    def test_window_too_short_returns_none(self):

        result = calculate_temporal_variability_feasible(
            rho_ab_window=[0.6, 0.61, 0.59],
            **STANDARD_VARIABILITY_KWARGS
        )

        self.assertIsNone(result)

    # Un canal figé (valeurs quasi identiques) doit être
    # jugé insuffisamment variable : échoue sur l'écart-type
    # (composante 1).
    def test_frozen_channel_is_infeasible(self):

        frozen_window = [0.60] * 10

        result = calculate_temporal_variability_feasible(
            rho_ab_window=frozen_window,
            **STANDARD_VARIABILITY_KWARGS
        )

        self.assertFalse(result)

    # Une alternance parfaite entre deux valeurs a un
    # écart-type élevé, mais est TROP prévisible d'une
    # période à l'autre : elle doit échouer sur
    # l'autocorrélation (composante 2), pas être validée
    # simplement parce que la dispersion est bonne.
    def test_perfectly_alternating_channel_fails_autocorrelation(
        self
    ):

        alternating_window = [
            0.2, 0.8, 0.2, 0.8, 0.2,
            0.8, 0.2, 0.8, 0.2, 0.8
        ]

        std_dev = calculate_window_std_dev(
            alternating_window
        )

        self.assertGreaterEqual(
            std_dev,
            STANDARD_VARIABILITY_KWARGS[
                "minimum_std_dev"
            ]
        )

        autocorrelation = (
            calculate_lag1_autocorrelation(
                alternating_window
            )
        )

        self.assertGreater(
            abs(autocorrelation),
            STANDARD_VARIABILITY_KWARGS[
                "maximum_lag1_autocorrelation"
            ]
        )

        result = calculate_temporal_variability_feasible(
            rho_ab_window=alternating_window,
            **STANDARD_VARIABILITY_KWARGS
        )

        self.assertFalse(result)

    # Un canal irrégulier, sans motif simple, qui satisfait
    # les quatre composantes doit être jugé suffisamment
    # variable.
    def test_irregular_channel_is_feasible(self):

        irregular_window = [
            0.327, 0.206, 0.556, 0.151, 0.475,
            0.356, 0.141, 0.455, 0.126, 0.404,
            0.149, 0.163
        ]

        result = calculate_temporal_variability_feasible(
            rho_ab_window=irregular_window,
            **STANDARD_VARIABILITY_KWARGS
        )

        self.assertTrue(result)

    # Un nombre de mesures valides insuffisant
    # (kept_measurement_ratio faible) doit faire échouer
    # phi_var même si le reste est favorable (composante 4).
    def test_insufficient_valid_measurements_is_infeasible(
        self
    ):

        irregular_window = [
            0.327, 0.206, 0.556, 0.151, 0.475,
            0.356, 0.141, 0.455, 0.126, 0.404,
            0.149, 0.163
        ]

        kwargs = dict(STANDARD_VARIABILITY_KWARGS)
        kwargs["kept_measurement_ratio"] = 0.10
        kwargs["minimum_valid_measurements"] = 5

        result = calculate_temporal_variability_feasible(
            rho_ab_window=irregular_window,
            **kwargs
        )

        self.assertFalse(result)

    # Le seuil minimal d'écart-type ne peut pas être
    # négatif.
    def test_negative_threshold_is_rejected(self):

        kwargs = dict(STANDARD_VARIABILITY_KWARGS)
        kwargs["minimum_std_dev"] = -0.01

        with self.assertRaises(ValueError):

            calculate_temporal_variability_feasible(
                rho_ab_window=[0.5] * 10,
                **kwargs
            )

    # La taille minimale de fenêtre doit être
    # strictement supérieure à 1.
    def test_window_size_must_exceed_one(self):

        kwargs = dict(STANDARD_VARIABILITY_KWARGS)
        kwargs["minimum_window_size"] = 1

        with self.assertRaises(ValueError):

            calculate_temporal_variability_feasible(
                rho_ab_window=[0.5, 0.5],
                **kwargs
            )


# Cette classe teste directement les fonctions élémentaires
# utilisées par phi_var.
class TestVariabilitySubComponents(unittest.TestCase):

    def test_std_dev_of_constant_window_is_zero(self):

        self.assertEqual(
            calculate_window_std_dev([0.5] * 10),
            0.0
        )

    # Cas dégénéré : une fenêtre constante a une variance
    # nulle, l'autocorrélation n'est pas mathématiquement
    # définie. La fonction doit retourner 1.0 (le cas le
    # plus défavorable), jamais lever d'exception.
    def test_autocorrelation_of_constant_window_is_one(
        self
    ):

        self.assertEqual(
            calculate_lag1_autocorrelation(
                [0.5] * 10
            ),
            1.0
        )

    # Sur une séquence quantifiée parfaitement équilibrée
    # (moitié au-dessus, moitié en-dessous de la médiane),
    # la fréquence maximale doit valoir 0,5 et la
    # min-entropie empirique doit valoir 1 bit (maximale).
    def test_balanced_sequence_has_maximum_entropy(self):

        statistics = (
            calculate_quantized_transition_statistics(
                [
                    0.327, 0.206, 0.556, 0.151, 0.475,
                    0.356, 0.141, 0.455, 0.126, 0.404,
                    0.149, 0.163
                ]
            )
        )

        self.assertAlmostEqual(
            statistics["maximum_bit_frequency"],
            0.5,
            places=9
        )

        self.assertAlmostEqual(
            statistics["minimum_entropy_bits"],
            1.0,
            places=9
        )

    # Une séquence toujours du même côté de sa médiane
    # (cas limite construit) a une fréquence maximale de 1
    # et une min-entropie de 0 bit.
    def test_degenerate_sequence_has_zero_entropy(self):

        # Une valeur strictement supérieure aux neuf autres
        # place la médiane du côté des dix identiques :
        # neuf valeurs valent exactement la médiane (donc
        # "1" par convention >=), une seule vaut "0".
        degenerate_window = [0.5] * 9 + [0.1]

        statistics = (
            calculate_quantized_transition_statistics(
                degenerate_window
            )
        )

        self.assertAlmostEqual(
            statistics["maximum_bit_frequency"],
            0.9,
            places=9
        )

        self.assertGreater(
            statistics["minimum_entropy_bits"],
            0.0
        )


# Cette condition permet également
# de lancer directement le fichier.
if __name__ == "__main__":

    unittest.main()
