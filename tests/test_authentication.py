# unittest est l'outil de test fourni avec Python.
import unittest


# NumPy est utilisé pour comparer
# les vecteurs et les matrices RFF.
import numpy as np


# On importe les actions d'authentification.
from physec_dm.models import AuthenticationAction


# On importe la configuration centrale.
from physec_dm.parameters import Parameters


# On importe toutes les fonctions
# actuellement définies dans authentication.py.
from physec_dm.authentication import (
    build_a1_metrics,
    build_a2_metrics,
    calculate_a1_robustness,
    calculate_a2_robustness,
    calculate_a2_total_false_acceptance,
    calculate_alice_fallback_probability,
    calculate_authentication_metrics,
    calculate_enrollment_reference,
    calculate_far,
    calculate_frr,
    calculate_isotropic_statistic,
    calculate_mac_forgery_probability,
    calculate_mahalanobis_statistic,
    calculate_mallory_fallback_probability,
    calculate_noise_variance,
    calculate_noncentrality_from_snr,
    calculate_noncentrality_parameter,
    calculate_normalized_separation_squared,
    calculate_rff_threshold,
    create_rff_vector,
    decide_rff,
    generate_rff_observation
)


# Cette classe teste la création du vecteur RFF
# et la phase d'enrôlement.
class TestRffVectorAndEnrollment(unittest.TestCase):

    # Le vecteur doit contenir CFO, DCO et PO
    # dans cet ordre exact.
    def test_create_rff_vector(self):

        rff_vector = create_rff_vector(
            cfo=1.0,
            dco=2.0,
            po=3.0
        )

        expected_vector = np.array(
            [
                1.0,
                2.0,
                3.0
            ]
        )

        self.assertTrue(
            np.array_equal(
                rff_vector,
                expected_vector
            )
        )

    # La référence d'enrôlement
    # doit être la moyenne des observations.
    def test_enrollment_reference(self):

        enrollment_reference = (
            calculate_enrollment_reference(
                [
                    [1.0, 2.0, 3.0],
                    [3.0, 4.0, 5.0]
                ]
            )
        )

        expected_reference = np.array(
            [
                2.0,
                3.0,
                4.0
            ]
        )

        self.assertTrue(
            np.allclose(
                enrollment_reference,
                expected_reference
            )
        )

    # Un enrôlement vide doit être refusé.
    def test_empty_enrollment_is_rejected(self):

        with self.assertRaises(ValueError):

            calculate_enrollment_reference(
                []
            )

    # Avec une covariance nulle,
    # l'observation doit être égale
    # au vecteur réel de l'appareil.
    def test_zero_noise_observation(self):

        random_generator = (
            np.random.default_rng(123)
        )

        device_vector = np.array(
            [
                1.0,
                2.0,
                3.0
            ]
        )

        zero_covariance = np.zeros(
            (
                3,
                3
            )
        )

        observation = generate_rff_observation(
            device_vector=device_vector,
            covariance_matrix=zero_covariance,
            random_generator=random_generator
        )

        self.assertTrue(
            np.allclose(
                observation,
                device_vector
            )
        )


# Cette classe teste les statistiques RFF.
class TestRffStatistics(unittest.TestCase):

    # Une observation identique à la référence
    # doit produire une distance nulle.
    def test_mahalanobis_zero(self):

        statistic = calculate_mahalanobis_statistic(
            observation=[1.0, 2.0, 3.0],
            reference=[1.0, 2.0, 3.0],
            covariance_matrix=np.eye(3)
        )

        self.assertEqual(
            statistic,
            0.0
        )

    # La forme générale et la forme isotrope
    # doivent donner le même résultat
    # lorsque Sigma = sigma² I.
    def test_general_statistic_equals_isotropic(self):

        observation = [
            2.0,
            3.0,
            4.0
        ]

        reference = [
            1.0,
            1.0,
            1.0
        ]

        noise_variance = 2.0

        covariance_matrix = (
            noise_variance
            * np.eye(3)
        )

        general_statistic = (
            calculate_mahalanobis_statistic(
                observation,
                reference,
                covariance_matrix
            )
        )

        isotropic_statistic = (
            calculate_isotropic_statistic(
                observation,
                reference,
                noise_variance
            )
        )

        self.assertAlmostEqual(
            general_statistic,
            isotropic_statistic,
            places=12
        )

    # La valeur exactement égale au seuil
    # doit être acceptée.
    def test_boundary_is_accepted(self):

        self.assertTrue(
            decide_rff(
                statistic=7.0,
                threshold=7.0
            )
        )

    # Une valeur supérieure au seuil
    # doit être rejetée.
    def test_value_above_threshold_is_rejected(self):

        self.assertFalse(
            decide_rff(
                statistic=7.1,
                threshold=7.0
            )
        )

    # Une covariance de mauvaise taille
    # doit être refusée.
    def test_invalid_covariance_is_rejected(self):

        with self.assertRaises(ValueError):

            calculate_mahalanobis_statistic(
                observation=[1.0, 2.0, 3.0],
                reference=[1.0, 2.0, 3.0],
                covariance_matrix=np.eye(2)
            )

    # Ce test vérifie le paramètre
    # de non-centralité général.
    def test_general_noncentrality_parameter(self):

        noncentrality_parameter = (
            calculate_noncentrality_parameter(
                mallory_vector=[
                    2.0,
                    0.0,
                    0.0
                ],
                alice_reference=[
                    0.0,
                    0.0,
                    0.0
                ],
                covariance_matrix=(
                    2.0 * np.eye(3)
                )
            )
        )

        # ||[2,0,0]||² / 2 = 4 / 2 = 2.
        self.assertEqual(
            noncentrality_parameter,
            2.0
        )


# Cette classe teste les probabilités
# et les équations de robustesse.
class TestAuthenticationProbabilities(unittest.TestCase):

    # Pour n_f = 3 et FRR cible = 5 %,
    # le seuil doit être proche de 7.8147279.
    def test_nominal_threshold(self):

        threshold = calculate_rff_threshold(
            feature_count=3,
            target_frr=0.05
        )

        self.assertAlmostEqual(
            threshold,
            7.814727903251179,
            places=12
        )

    # Le seuil nominal doit reproduire
    # une FRR de 5 %.
    def test_frr_matches_target(self):

        threshold = calculate_rff_threshold(
            feature_count=3,
            target_frr=0.05
        )

        frr = calculate_frr(
            threshold=threshold,
            feature_count=3
        )

        self.assertAlmostEqual(
            frr,
            0.05,
            places=12
        )

    # Lorsque lambda = 0,
    # Mallory suit la même distribution qu'Alice.
    #
    # La FAR doit alors être égale à 1 - FRR.
    def test_far_at_zero_noncentrality(self):

        threshold = calculate_rff_threshold(
            feature_count=3,
            target_frr=0.05
        )

        far = calculate_far(
            threshold=threshold,
            feature_count=3,
            noncentrality_parameter=0.0
        )

        self.assertAlmostEqual(
            far,
            0.95,
            places=12
        )

    # La FAR doit diminuer lorsque
    # la séparation de Mallory augmente.
    def test_far_decreases_with_noncentrality(self):

        threshold = calculate_rff_threshold(
            feature_count=3,
            target_frr=0.05
        )

        far_small_separation = calculate_far(
            threshold=threshold,
            feature_count=3,
            noncentrality_parameter=1.0
        )

        far_large_separation = calculate_far(
            threshold=threshold,
            feature_count=3,
            noncentrality_parameter=10.0
        )

        self.assertLess(
            far_large_separation,
            far_small_separation
        )

    # sigma0² = 2 et gamma = 4
    # doivent produire sigma_w² = 0.5.
    def test_noise_variance(self):

        noise_variance = calculate_noise_variance(
            reference_noise_variance=2.0,
            snr_linear=4.0
        )

        self.assertEqual(
            noise_variance,
            0.5
        )

    # Ce test vérifie d_M².
    def test_normalized_separation_squared(self):

        normalized_separation_squared = (
            calculate_normalized_separation_squared(
                mallory_vector=[
                    2.0,
                    0.0,
                    0.0
                ],
                alice_reference=[
                    0.0,
                    0.0,
                    0.0
                ],
                reference_noise_variance=2.0
            )
        )

        self.assertEqual(
            normalized_separation_squared,
            2.0
        )

    # lambda = d_M² * gamma.
    def test_noncentrality_from_snr(self):

        noncentrality_parameter = (
            calculate_noncentrality_from_snr(
                normalized_separation_squared=4.0,
                snr_linear=3.0
            )
        )

        self.assertEqual(
            noncentrality_parameter,
            12.0
        )

    # Le risque idéal de forge
    # pour un tag de 64 bits est 2^-64.
    def test_mac_forgery_probability(self):

        probability = (
            calculate_mac_forgery_probability(
                64
            )
        )

        self.assertEqual(
            probability,
            2 ** (-64)
        )

    # Ce test vérifie la robustesse A1.
    def test_a1_robustness(self):

        robustness = calculate_a1_robustness(
            64
        )

        self.assertEqual(
            robustness,
            1 - 2 ** (-64)
        )

    # Ce test vérifie :
    #
    # 0.02 + (1 - 0.02) * 0.001
    # = 0.02098
    def test_a2_total_false_acceptance(self):

        total_probability = (
            calculate_a2_total_false_acceptance(
                far=0.02,
                mac_forgery_probability=0.001
            )
        )

        self.assertAlmostEqual(
            total_probability,
            0.02098,
            places=12
        )

    # La robustesse est 1 - P_FA.
    def test_a2_robustness(self):

        robustness = calculate_a2_robustness(
            0.02
        )

        self.assertEqual(
            robustness,
            0.98
        )

    # Ce test vérifie les deux probabilités de repli.
    def test_fallback_probabilities(self):

        self.assertEqual(
            calculate_alice_fallback_probability(
                0.05
            ),
            0.05
        )

        self.assertEqual(
            calculate_mallory_fallback_probability(
                0.02
            ),
            0.98
        )


# Cette classe teste la construction
# des objets AuthenticationMetrics.
class TestAuthenticationMetricsConstruction(
    unittest.TestCase
):

    # Test complet de A1.
    def test_a1_metrics(self):

        metrics = build_a1_metrics(
            mac_tag_bits=64
        )

        self.assertEqual(
            metrics.authentication_action,
            AuthenticationAction.A1
        )

        self.assertEqual(
            metrics.frr,
            0.0
        )

        self.assertEqual(
            metrics.far,
            2 ** (-64)
        )

        self.assertEqual(
            metrics.alice_fallback_probability,
            0.0
        )

    # Test complet de A2.
    def test_a2_metrics(self):

        parameters = Parameters()

        metrics = build_a2_metrics(
            feature_count=3,
            threshold=parameters.rff_threshold,
            mallory_separation=2.0,
            mallory_snr_linear=10.0,
            mac_tag_bits=64
        )

        self.assertEqual(
            metrics.authentication_action,
            AuthenticationAction.A2
        )

        self.assertAlmostEqual(
            metrics.frr,
            0.05,
            places=12
        )

        self.assertGreaterEqual(
            metrics.far,
            0.0
        )

        self.assertLessEqual(
            metrics.far,
            1.0
        )

        self.assertGreaterEqual(
            metrics.authentication_robustness,
            0.0
        )

        self.assertLessEqual(
            metrics.authentication_robustness,
            1.0
        )

    # Le dispatcher doit appeler A1.
    def test_dispatcher_a1(self):

        parameters = Parameters()

        metrics = calculate_authentication_metrics(
            authentication_action=(
                AuthenticationAction.A1
            ),
            parameters=parameters
        )

        self.assertEqual(
            metrics.authentication_action,
            AuthenticationAction.A1
        )

    # Le dispatcher doit appeler A2
    # et convertir le SNR fourni.
    def test_dispatcher_a2(self):

        parameters = Parameters()

        metrics = calculate_authentication_metrics(
            authentication_action=(
                AuthenticationAction.A2
            ),
            parameters=parameters,
            mallory_snr_db=10.0
        )

        self.assertEqual(
            metrics.authentication_action,
            AuthenticationAction.A2
        )


# Cette condition permet aussi
# de lancer directement le fichier.
if __name__ == "__main__":

    unittest.main()
