# NumPy permet de manipuler simplement :
# - les vecteurs RFF ;
# - les matrices de covariance ;
# - les moyennes ;
# - les produits matriciels.
import numpy as np


# chi2 représente la loi du Khi-deux centrale.
#
# Elle est utilisée pour modéliser la statistique RFF
# lorsque le message provient réellement d'Alice.
#
# ncx2 représente la loi du Khi-deux non centrale.
#
# Elle est utilisée lorsque le message provient de Mallory.
from scipy.stats import chi2, ncx2


# On importe les actions d'authentification
# et la structure qui conservera les résultats.
from physec_dm.models import (
    AuthenticationAction,
    AuthenticationMetrics
)


# On importe la fonction déjà validée dans channel.py.
#
# Elle permet de convertir le SNR de Mallory
# des décibels vers sa forme linéaire.
from physec_dm.channel import convert_db_to_linear


# Cette fonction construit le vecteur RFF d'un appareil.
#
# Dans la modélisation, le vecteur est :
#
# f_X = [CFO_X, DCO_X, PO_X]
#
# avec :
#
# CFO
#     décalage de fréquence porteuse ;
#
# DCO
#     décalage de composante continue ;
#
# PO
#     décalage de phase.
#
# Cette fonction correspond à AU-EQ23.
def create_rff_vector(cfo, dco, po):

    # np.array regroupe les trois valeurs
    # dans un seul vecteur numérique.
    #
    # dtype=float force l'utilisation
    # de nombres décimaux.
    rff_vector = np.array(
        [
            cfo,
            dco,
            po
        ],
        dtype=float
    )

    return rff_vector


# Cette fonction simule une observation RFF bruitée.
#
# Dans la modélisation :
#
# f_observed,t = f_X + w_t
#
# avec :
#
# w_t ~ N(0, Sigma_w)
#
# Cette fonction correspond à AU-EQ24.
def generate_rff_observation(
    device_vector,
    covariance_matrix,
    random_generator
):

    # On transforme les entrées en tableaux NumPy.
    device_vector = np.array(
        device_vector,
        dtype=float
    )

    covariance_matrix = np.array(
        covariance_matrix,
        dtype=float
    )

    # Le vecteur RFF doit être un vecteur simple
    # et non une matrice.
    if device_vector.ndim != 1:

        raise ValueError(
            "Le vecteur RFF doit avoir une seule dimension."
        )

    # Pour un vecteur de taille n,
    # la covariance doit avoir la taille n × n.
    expected_shape = (
        len(device_vector),
        len(device_vector)
    )

    if covariance_matrix.shape != expected_shape:

        raise ValueError(
            "La matrice de covariance doit être carrée "
            "et compatible avec le vecteur RFF."
        )

    # multivariate_normal tire une observation
    # suivant une loi normale multivariée.
    #
    # La moyenne est le vecteur réel de l'appareil.
    #
    # La covariance représente le bruit de mesure.
    observation = random_generator.multivariate_normal(
        mean=device_vector,
        cov=covariance_matrix
    )

    return observation


# Cette fonction calcule la référence RFF d'Alice
# pendant la phase d'enrôlement.
#
# Dans la modélisation :
#
# f_A,ref =
#     (1 / N_enr)
#     * somme des observations d'Alice
#
# Cette fonction correspond à AU-EQ25.
def calculate_enrollment_reference(
    enrollment_samples
):

    # On transforme les échantillons
    # en matrice NumPy.
    enrollment_samples = np.array(
        enrollment_samples,
        dtype=float
    )

    # La matrice doit contenir :
    # - une ligne par observation ;
    # - une colonne par attribut RFF.
    if (
        enrollment_samples.ndim != 2
        or enrollment_samples.shape[0] == 0
    ):

        raise ValueError(
            "Les échantillons d'enrôlement doivent "
            "former une matrice non vide."
        )

    # axis=0 signifie que l'on calcule
    # la moyenne de chaque colonne.
    #
    # On obtient donc :
    # - la moyenne CFO ;
    # - la moyenne DCO ;
    # - la moyenne PO.
    enrollment_reference = np.mean(
        enrollment_samples,
        axis=0
    )

    return enrollment_reference


# Cette fonction calcule la statistique
# de distance de Mahalanobis.
#
# Dans la modélisation :
#
# T_t =
#     (f_observed - f_A,ref)^T
#     * Sigma_w^(-1)
#     * (f_observed - f_A,ref)
#
# Cette fonction correspond à AU-EQ26.
def calculate_mahalanobis_statistic(
    observation,
    reference,
    covariance_matrix
):

    # On convertit les entrées en tableaux NumPy.
    observation = np.array(
        observation,
        dtype=float
    )

    reference = np.array(
        reference,
        dtype=float
    )

    covariance_matrix = np.array(
        covariance_matrix,
        dtype=float
    )

    # L'observation et la référence
    # doivent avoir la même taille.
    if observation.shape != reference.shape:

        raise ValueError(
            "L'observation et la référence doivent "
            "avoir la même dimension."
        )

    # Les deux entrées doivent être des vecteurs.
    if observation.ndim != 1:

        raise ValueError(
            "L'observation et la référence "
            "doivent être des vecteurs."
        )

    # La covariance doit avoir une ligne
    # et une colonne pour chaque attribut RFF.
    expected_shape = (
        len(observation),
        len(observation)
    )

    if covariance_matrix.shape != expected_shape:

        raise ValueError(
            "La matrice de covariance doit être carrée "
            "et compatible avec le vecteur RFF."
        )

    # On calcule l'écart entre l'observation
    # et la référence d'Alice.
    difference = (
        observation
        - reference
    )

    # La modélisation utilise Sigma_w^(-1).
    #
    # np.linalg.inv calcule l'inverse
    # de la matrice de covariance.
    try:

        inverse_covariance = np.linalg.inv(
            covariance_matrix
        )

    # Une covariance non inversible
    # ne permet pas de calculer Mahalanobis.
    except np.linalg.LinAlgError:

        raise ValueError(
            "La matrice de covariance doit être inversible."
        )

    # On applique la formule :
    #
    # difference^T
    # * inverse_covariance
    # * difference
    statistic = (
        difference.T
        .dot(inverse_covariance)
        .dot(difference)
    )

    # float transforme le résultat NumPy
    # en nombre Python simple.
    return float(statistic)


# Cette fonction applique la règle de décision RFF.
#
# Dans la modélisation :
#
# T_t <= theta
#     l'émetteur est accepté comme Alice ;
#
# T_t > theta
#     l'émetteur est rejeté
#     et le défi-réponse est déclenché.
#
# Cette fonction correspond à AU-EQ27.
def decide_rff(
    statistic,
    threshold
):

    # Une distance ne peut pas être négative.
    if statistic < 0:

        raise ValueError(
            "La statistique RFF ne peut pas être négative."
        )

    # Le seuil doit également être positif ou nul.
    if threshold < 0:

        raise ValueError(
            "Le seuil RFF ne peut pas être négatif."
        )

    # L'égalité est acceptée conformément
    # à la règle T_t <= theta.
    accepted_as_alice = (
        statistic <= threshold
    )

    return accepted_as_alice


# Cette fonction calcule la forme simplifiée
# de la statistique lorsque :
#
# Sigma_w = sigma_w² * I
#
# Dans ce cas :
#
# T_t =
#     ||f_observed - f_A,ref||²
#     / sigma_w²
#
# Cette fonction correspond à AU-EQ28.
def calculate_isotropic_statistic(
    observation,
    reference,
    noise_variance
):

    # La variance doit être strictement positive,
    # car elle se trouve au dénominateur.
    if noise_variance <= 0:

        raise ValueError(
            "La variance du bruit doit être "
            "strictement positive."
        )

    observation = np.array(
        observation,
        dtype=float
    )

    reference = np.array(
        reference,
        dtype=float
    )

    if observation.shape != reference.shape:

        raise ValueError(
            "L'observation et la référence doivent "
            "avoir la même dimension."
        )

    # On calcule le vecteur de différence.
    difference = (
        observation
        - reference
    )

    # np.sum(difference ** 2) calcule
    # le carré de la norme euclidienne.
    squared_distance = float(
        np.sum(
            difference ** 2
        )
    )

    statistic = (
        squared_distance
        / noise_variance
    )

    return statistic


# Cette fonction calcule le paramètre
# de non-centralité général de Mallory.
#
# Dans la modélisation :
#
# lambda_M =
#     (f_M - f_A,ref)^T
#     * Sigma_w^(-1)
#     * (f_M - f_A,ref)
#
# Cette fonction correspond à AU-EQ31.
def calculate_noncentrality_parameter(
    mallory_vector,
    alice_reference,
    covariance_matrix
):

    # La formule est mathématiquement identique
    # à une distance de Mahalanobis.
    noncentrality_parameter = (
        calculate_mahalanobis_statistic(
            observation=mallory_vector,
            reference=alice_reference,
            covariance_matrix=covariance_matrix
        )
    )

    return noncentrality_parameter


# Cette fonction calcule le taux de faux rejet.
#
# Dans la modélisation :
#
# FRR(theta) =
#     1 - F_chi2_n_f(theta)
#
# Cette fonction correspond à AU-EQ32.
def calculate_frr(
    threshold,
    feature_count
):

    if threshold < 0:

        raise ValueError(
            "Le seuil RFF ne peut pas être négatif."
        )

    if feature_count <= 0:

        raise ValueError(
            "Le nombre d'attributs RFF doit être "
            "strictement positif."
        )

    # chi2.cdf retourne :
    #
    # P(T <= threshold)
    #
    # sous l'hypothèse Alice.
    frr = (
        1
        - chi2.cdf(
            threshold,
            df=feature_count
        )
    )

    return float(frr)


# Cette fonction calcule le taux de fausse acceptation.
#
# Dans la modélisation :
#
# FAR(theta, lambda_M) =
#     F_chi2_non_centrale(theta)
#
# Cette fonction correspond à AU-EQ33.
def calculate_far(
    threshold,
    feature_count,
    noncentrality_parameter
):

    if threshold < 0:

        raise ValueError(
            "Le seuil RFF ne peut pas être négatif."
        )

    if feature_count <= 0:

        raise ValueError(
            "Le nombre d'attributs RFF doit être "
            "strictement positif."
        )

    if noncentrality_parameter < 0:

        raise ValueError(
            "Le paramètre de non-centralité "
            "ne peut pas être négatif."
        )

    # ncx2.cdf calcule la probabilité
    # que la statistique de Mallory soit
    # inférieure ou égale au seuil.
    far = ncx2.cdf(
        threshold,
        df=feature_count,
        nc=noncentrality_parameter
    )

    return float(far)


# Cette fonction relie la variance du bruit RFF
# au SNR de Mallory.
#
# Dans la modélisation :
#
# sigma_w²(gamma_M) =
#     sigma_0² / gamma_M
#
# Cette fonction correspond à AU-EQ34.
def calculate_noise_variance(
    reference_noise_variance,
    snr_linear
):

    if reference_noise_variance <= 0:

        raise ValueError(
            "La variance de référence doit être "
            "strictement positive."
        )

    # Le SNR doit être strictement positif,
    # car il se trouve au dénominateur.
    if snr_linear <= 0:

        raise ValueError(
            "Le SNR linéaire doit être "
            "strictement positif."
        )

    noise_variance = (
        reference_noise_variance
        / snr_linear
    )

    return noise_variance


# Cette fonction calcule la séparation normalisée
# entre Mallory et Alice.
#
# Dans la modélisation :
#
# d_M² =
#     ||f_M - f_A,ref||²
#     / sigma_0²
#
# Cette fonction correspond à AU-EQ35.
def calculate_normalized_separation_squared(
    mallory_vector,
    alice_reference,
    reference_noise_variance
):

    if reference_noise_variance <= 0:

        raise ValueError(
            "La variance de référence doit être "
            "strictement positive."
        )

    mallory_vector = np.array(
        mallory_vector,
        dtype=float
    )

    alice_reference = np.array(
        alice_reference,
        dtype=float
    )

    if mallory_vector.shape != alice_reference.shape:

        raise ValueError(
            "Les vecteurs d'Alice et Mallory doivent "
            "avoir la même dimension."
        )

    difference = (
        mallory_vector
        - alice_reference
    )

    squared_distance = float(
        np.sum(
            difference ** 2
        )
    )

    normalized_separation_squared = (
        squared_distance
        / reference_noise_variance
    )

    return normalized_separation_squared


# Cette fonction calcule la forme simplifiée
# du paramètre de non-centralité.
#
# Dans la modélisation :
#
# lambda_M =
#     d_M² * gamma_M
#
# Cette fonction correspond à AU-EQ36.
def calculate_noncentrality_from_snr(
    normalized_separation_squared,
    snr_linear
):

    if normalized_separation_squared < 0:

        raise ValueError(
            "La séparation normalisée "
            "ne peut pas être négative."
        )

    # Le SNR peut être nul dans un cas limite.
    if snr_linear < 0:

        raise ValueError(
            "Le SNR linéaire ne peut pas être négatif."
        )

    noncentrality_parameter = (
        normalized_separation_squared
        * snr_linear
    )

    return noncentrality_parameter


# Cette fonction calcule le seuil RFF
# correspondant à une FRR cible.
#
# Dans la modélisation :
#
# theta =
#     F_chi2_inverse(
#         1 - target_frr
#     )
#
# Cette fonction correspond à AU-EQ37.
def calculate_rff_threshold(
    feature_count,
    target_frr
):

    if feature_count <= 0:

        raise ValueError(
            "Le nombre d'attributs RFF doit être "
            "strictement positif."
        )

    # La FRR cible doit être comprise
    # strictement entre zéro et un.
    if target_frr <= 0 or target_frr >= 1:

        raise ValueError(
            "La FRR cible doit appartenir à ]0, 1[."
        )

    threshold = chi2.ppf(
        1 - target_frr,
        df=feature_count
    )

    return float(threshold)


# Cette fonction calcule la probabilité idéale
# de falsification d'un tag MAC.
#
# Dans la modélisation :
#
# p_forge =
#     2 ** (-b_MAC)
#
# Cette fonction correspond à AU-EQ38.
def calculate_mac_forgery_probability(
    mac_tag_bits
):

    if mac_tag_bits <= 0:

        raise ValueError(
            "La taille du tag MAC doit être "
            "strictement positive."
        )

    mac_forgery_probability = (
        2 ** (-mac_tag_bits)
    )

    return mac_forgery_probability


# Cette fonction calcule la robustesse
# de l'action conventionnelle A1.
#
# Dans la modélisation :
#
# R_auth(A1) =
#     1 - 2 ** (-b_MAC)
#
# Cette fonction correspond à AU-EQ39.
def calculate_a1_robustness(
    mac_tag_bits
):

    mac_forgery_probability = (
        calculate_mac_forgery_probability(
            mac_tag_bits
        )
    )

    authentication_robustness = (
        1
        - mac_forgery_probability
    )

    return authentication_robustness


# Cette fonction calcule la probabilité totale
# de fausse acceptation de l'action A2.
#
# Dans la modélisation :
#
# P_FA(A2) =
#     FAR
#     + (1 - FAR) * p_forge
#
# Cette fonction correspond à AU-EQ40.
def calculate_a2_total_false_acceptance(
    far,
    mac_forgery_probability
):

    if far < 0 or far > 1:

        raise ValueError(
            "La FAR doit appartenir à [0, 1]."
        )

    if (
        mac_forgery_probability < 0
        or mac_forgery_probability > 1
    ):

        raise ValueError(
            "La probabilité de forge doit "
            "appartenir à [0, 1]."
        )

    total_false_acceptance_probability = (
        far
        + (1 - far)
        * mac_forgery_probability
    )

    return total_false_acceptance_probability


# Cette fonction calcule la robustesse
# complète de l'action A2.
#
# Dans la modélisation :
#
# R_auth(A2) =
#     1 - P_FA(A2)
#
# Cette fonction correspond à AU-EQ41.
def calculate_a2_robustness(
    total_false_acceptance_probability
):

    if (
        total_false_acceptance_probability < 0
        or total_false_acceptance_probability > 1
    ):

        raise ValueError(
            "La probabilité totale de fausse acceptation "
            "doit appartenir à [0, 1]."
        )

    authentication_robustness = (
        1
        - total_false_acceptance_probability
    )

    return authentication_robustness


# Cette fonction retourne la probabilité
# de déclencher le repli pour Alice.
#
# Dans la modélisation :
#
# p_fb(A) = FRR
#
# Cette fonction correspond à AU-EQ42.
def calculate_alice_fallback_probability(
    frr
):

    if frr < 0 or frr > 1:

        raise ValueError(
            "La FRR doit appartenir à [0, 1]."
        )

    return frr


# Cette fonction retourne la probabilité
# de déclencher le repli pour Mallory.
#
# Dans la modélisation :
#
# p_fb(M) = 1 - FAR
#
# Cette fonction correspond à AU-EQ43.
#
# Cette probabilité sert à l'analyse de sécurité.
# Elle ne doit pas débiter l'énergie d'Alice.
def calculate_mallory_fallback_probability(
    far
):

    if far < 0 or far > 1:

        raise ValueError(
            "La FAR doit appartenir à [0, 1]."
        )

    mallory_fallback_probability = (
        1
        - far
    )

    return mallory_fallback_probability


# Cette fonction construit toutes les métriques
# de l'action conventionnelle A1.
def build_a1_metrics(
    mac_tag_bits
):

    # Pour A1, la probabilité d'attaque réussie
    # correspond directement à la forge du MAC.
    mac_forgery_probability = (
        calculate_mac_forgery_probability(
            mac_tag_bits
        )
    )

    authentication_robustness = (
        calculate_a1_robustness(
            mac_tag_bits
        )
    )

    # A1 ne possède pas de test RFF.
    #
    # On utilise donc :
    # - FRR = 0 ;
    # - aucun repli ;
    # - FAR = risque de falsification du MAC.
    authentication_metrics = AuthenticationMetrics(
        authentication_action=AuthenticationAction.A1,
        far=mac_forgery_probability,
        frr=0.0,
        mac_forgery_probability=(
            mac_forgery_probability
        ),
        total_false_acceptance_probability=(
            mac_forgery_probability
        ),
        authentication_robustness=(
            authentication_robustness
        ),
        alice_fallback_probability=0.0,
        mallory_fallback_probability=0.0
    )

    return authentication_metrics


# Cette fonction construit toutes les métriques
# de l'action hybride A2.
def build_a2_metrics(
    feature_count,
    threshold,
    mallory_separation,
    mallory_snr_linear,
    mac_tag_bits
):

    # parameters.py contient d_M.
    #
    # L'équation simplifiée utilise d_M².
    normalized_separation_squared = (
        mallory_separation ** 2
    )

    noncentrality_parameter = (
        calculate_noncentrality_from_snr(
            normalized_separation_squared,
            mallory_snr_linear
        )
    )

    # FAR contre Mallory.
    far = calculate_far(
        threshold=threshold,
        feature_count=feature_count,
        noncentrality_parameter=(
            noncentrality_parameter
        )
    )

    # FRR pour Alice.
    frr = calculate_frr(
        threshold=threshold,
        feature_count=feature_count
    )

    # Risque de falsification du MAC
    # pendant le défi-réponse.
    mac_forgery_probability = (
        calculate_mac_forgery_probability(
            mac_tag_bits
        )
    )

    total_false_acceptance_probability = (
        calculate_a2_total_false_acceptance(
            far,
            mac_forgery_probability
        )
    )

    authentication_robustness = (
        calculate_a2_robustness(
            total_false_acceptance_probability
        )
    )

    alice_fallback_probability = (
        calculate_alice_fallback_probability(
            frr
        )
    )

    mallory_fallback_probability = (
        calculate_mallory_fallback_probability(
            far
        )
    )

    authentication_metrics = AuthenticationMetrics(
        authentication_action=AuthenticationAction.A2,
        far=far,
        frr=frr,
        mac_forgery_probability=(
            mac_forgery_probability
        ),
        total_false_acceptance_probability=(
            total_false_acceptance_probability
        ),
        authentication_robustness=(
            authentication_robustness
        ),
        alice_fallback_probability=(
            alice_fallback_probability
        ),
        mallory_fallback_probability=(
            mallory_fallback_probability
        )
    )

    return authentication_metrics


# Cette fonction choisit automatiquement
# le calcul correspondant à A1 ou A2.
#
# Elle sera appelée plus tard
# par le Decision Maker.
def calculate_authentication_metrics(
    authentication_action,
    parameters,
    mallory_snr_db=None
):

    # Cas A1 : authentification conventionnelle.
    if authentication_action == AuthenticationAction.A1:

        return build_a1_metrics(
            parameters.mac_tag_bits
        )

    # Cas A2 : RFF suivie éventuellement
    # du défi-réponse.
    if authentication_action == AuthenticationAction.A2:

        # Si aucun SNR spécifique de Mallory
        # n'est fourni, on utilise le SNR moyen
        # du scénario.
        if mallory_snr_db is None:

            mallory_snr_db = (
                parameters.mean_snr_db
            )

        if mallory_snr_db is None:

            raise ValueError(
                "Le SNR de Mallory doit être défini "
                "pour calculer les métriques de A2."
            )

        mallory_snr_linear = (
            convert_db_to_linear(
                mallory_snr_db
            )
        )

        return build_a2_metrics(
            feature_count=(
                parameters.rff_feature_count
            ),
            threshold=(
                parameters.rff_threshold
            ),
            mallory_separation=(
                parameters.mallory_separation
            ),
            mallory_snr_linear=(
                mallory_snr_linear
            ),
            mac_tag_bits=(
                parameters.mac_tag_bits
            )
        )

    # Toute autre action est interdite.
    raise ValueError(
        "L'action d'authentification doit être A1 ou A2."
    )
