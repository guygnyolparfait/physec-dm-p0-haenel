
# On importe la bibliothèque math de Python.
#
# Elle fournit :
# - acos pour calculer l'arc-cosinus ;
# - cos et pi pour relier le KDR au seuil de corrélation ;
# - log2 pour calculer l'entropie binaire ;
# - ceil pour arrondir le nombre de mesures vers le haut.
import math


# On importe les actions de clé et la structure
# qui conservera tous les résultats calculés.
from physec_dm.models import (
    KeyAction,
    KeyMetrics
)


# Cette fonction calcule le KDR brut
# à partir de la corrélation entre Alice et Bob.
#
# Dans la modélisation :
#
# KDR_brut = arccos(rho_AB) / pi
#
# Cette relation est exacte sous les hypothèses :
# - observations conjointement gaussiennes ;
# - quantification binaire par signe ;
# - seuil de quantification nul ou médian.
def calculate_raw_kdr(rho_ab):

    # Une corrélation doit appartenir à [-1, 1].
    if rho_ab < -1 or rho_ab > 1:

        raise ValueError(
            "La corrélation rho_AB doit appartenir à [-1, 1]."
        )

    raw_kdr = (
        math.acos(rho_ab)
        / math.pi
    )

    return raw_kdr


# Cette fonction calcule le KDR réellement utilisé
# par le modèle selon le mode de quantification.
#
# Deux modes sont prévus :
#
# "analytic"
#     le KDR utilisé est exactement le KDR brut ;
#
# "calibrated"
#     une approximation multiplicative représente
#     provisoirement l'effet du quantificateur réel
#     et de la bande de garde.
#
# La forme multiplicative est un surrogate exploratoire.
# Elle ne doit pas être présentée comme une loi universelle.
def calculate_effective_kdr(
    raw_kdr,
    quantization_mode,
    guard_band_factor
):

    # Le KDR brut est une probabilité de désaccord.
    if raw_kdr < 0 or raw_kdr > 1:

        raise ValueError(
            "Le KDR brut doit appartenir à [0, 1]."
        )

    # Dans le mode analytique,
    # aucune calibration supplémentaire n'est appliquée.
    if quantization_mode == "analytic":

        return raw_kdr

    # Dans le mode calibré,
    # on utilise le facteur multiplicatif provisoire.
    if quantization_mode == "calibrated":

        if guard_band_factor <= 0:

            raise ValueError(
                "Le facteur de bande de garde doit être "
                "strictement positif."
            )

        effective_kdr = (
            guard_band_factor
            * raw_kdr
        )

        # Un KDR est une probabilité.
        # On le maintient donc dans l'intervalle [0, 1].
        effective_kdr = min(
            1.0,
            max(
                0.0,
                effective_kdr
            )
        )

        return effective_kdr

    # Toute autre chaîne correspond à un mode inconnu.
    raise ValueError(
        "Le mode de quantification doit valoir "
        "'analytic' ou 'calibrated'."
    )


# Cette fonction calcule le seuil de corrélation
# correspondant à un KDR maximal.
#
# En inversant :
#
# KDR = arccos(rho) / pi
#
# on obtient :
#
# rho_min = cos(pi * KDR_max)
def calculate_minimum_correlation(
    maximum_kdr
):

    if maximum_kdr < 0 or maximum_kdr > 1:

        raise ValueError(
            "Le KDR maximal doit appartenir à [0, 1]."
        )

    minimum_correlation = math.cos(
        math.pi
        * maximum_kdr
    )

    return minimum_correlation


# Cette fonction calcule l'entropie binaire :
#
# h2(p) =
#     -p * log2(p)
#     -(1-p) * log2(1-p)
#
# La convention utilisée est :
#
# 0 * log2(0) = 0
def calculate_binary_entropy(
    probability
):

    if probability < 0 or probability > 1:

        raise ValueError(
            "La probabilité doit appartenir à [0, 1]."
        )

    # Aux deux extrémités,
    # l'entropie est exactement nulle.
    if probability == 0 or probability == 1:

        return 0.0

    binary_entropy = (
        -probability
        * math.log2(probability)
        -(1 - probability)
        * math.log2(1 - probability)
    )

    return binary_entropy


# Cette fonction calcule le rendement
# après réconciliation et amplification :
#
# y_rec =
#     eta_keep
#     * [1 - h2(KDR)]
#
# Cette quantité est un surrogate de rendement.
# Elle ne constitue pas une capacité secrète complète
# vis-à-vis de Mallory.
def calculate_reconciliation_yield(
    effective_kdr,
    kept_measurement_ratio
):

    if effective_kdr < 0 or effective_kdr > 1:

        raise ValueError(
            "Le KDR effectif doit appartenir à [0, 1]."
        )

    if (
        kept_measurement_ratio <= 0
        or kept_measurement_ratio > 1
    ):

        raise ValueError(
            "La proportion de mesures conservées doit "
            "appartenir à ]0, 1]."
        )

    binary_entropy = calculate_binary_entropy(
        effective_kdr
    )

    reconciliation_yield = (
        kept_measurement_ratio
        * (1 - binary_entropy)
    )

    return reconciliation_yield


# Cette fonction calcule le nombre de mesures
# nécessaire pour produire une clé :
#
# N_meas =
#     ceil(
#         key_length
#         / max(y_rec, epsilon)
#     )
#
# epsilon sert uniquement à éviter
# une division numérique par zéro.
def calculate_required_measurements(
    key_length_bits,
    reconciliation_yield,
    numerical_epsilon
):

    if key_length_bits <= 0:

        raise ValueError(
            "La longueur de clé doit être "
            "strictement positive."
        )

    if reconciliation_yield < 0:

        raise ValueError(
            "Le rendement ne peut pas être négatif."
        )

    if numerical_epsilon <= 0:

        raise ValueError(
            "La protection numérique doit être "
            "strictement positive."
        )

    protected_yield = max(
        reconciliation_yield,
        numerical_epsilon
    )

    required_measurements = math.ceil(
        key_length_bits
        / protected_yield
    )

    return required_measurements


# Cette fonction calcule le reliquat de mesures
# encore nécessaires pour terminer la collecte
# d'une clé candidate K1a ou K1b.
#
# Dans la modélisation :
#
# N_remaining =
#     max(
#         N_required
#         - N_collected,
#         0
#     )
#
# collected_measurements peut dépasser
# required_measurements si les conditions du canal
# se sont améliorées entre deux périodes : le reliquat
# est alors nul, jamais négatif.
def calculate_remaining_measurements(
    required_measurements,
    collected_measurements
):

    if required_measurements < 0:

        raise ValueError(
            "required_measurements ne peut pas "
            "être négatif."
        )

    if collected_measurements < 0:

        raise ValueError(
            "collected_measurements ne peut pas "
            "être négatif."
        )

    remaining_measurements = max(
        required_measurements
        - collected_measurements,
        0
    )

    return remaining_measurements


# Cette fonction vérifie la faisabilité minimale
# de l'accord à partir du KDR.
#
# La condition générale est :
#
# agreement_feasible =
#     effective_kdr <= maximum_kdr
#
# Cette forme reste valable dans les modes
# analytique et calibré.
def calculate_agreement_feasibility(
    effective_kdr,
    maximum_kdr
):

    if effective_kdr < 0 or effective_kdr > 1:

        raise ValueError(
            "Le KDR effectif doit appartenir à [0, 1]."
        )

    if maximum_kdr < 0 or maximum_kdr > 1:

        raise ValueError(
            "Le KDR maximal doit appartenir à [0, 1]."
        )

    agreement_feasible = (
        effective_kdr
        <= maximum_kdr
    )

    return agreement_feasible


# Cette fonction exprime la même condition
# directement avec la corrélation.
#
# Elle ne doit être utilisée que dans le mode analytique :
#
# agreement_feasible =
#     rho_AB >= rho_min
def calculate_analytic_agreement_from_correlation(
    rho_ab,
    minimum_correlation
):

    if rho_ab < -1 or rho_ab > 1:

        raise ValueError(
            "La corrélation rho_AB doit appartenir à [-1, 1]."
        )

    if minimum_correlation < -1 or minimum_correlation > 1:

        raise ValueError(
            "Le seuil de corrélation doit appartenir à [-1, 1]."
        )

    agreement_feasible = (
        rho_ab
        >= minimum_correlation
    )

    return agreement_feasible


# Cette fonction combine :
# - la faisabilité d'accord ;
# - la faisabilité de variabilité.
#
# Dans la modélisation complète :
#
# phi_PHY =
#     phi_agree * phi_var
#
# Lorsque variation_feasible vaut None,
# la métrique de variabilité n'est pas encore validée.
#
# Dans ce cas, on retourne provisoirement
# la faisabilité d'accord seulement.
#
# Le résultat ne doit alors pas être interprété
# comme une preuve complète de sécurité informationnelle.
def calculate_phy_feasibility(
    agreement_feasible,
    variation_feasible
):

    if not isinstance(
        agreement_feasible,
        bool
    ):

        raise ValueError(
            "agreement_feasible doit être booléen."
        )

    # None signifie que seule
    # la faisabilité d'accord est actuellement disponible.
    if variation_feasible is None:

        return agreement_feasible

    if not isinstance(
        variation_feasible,
        bool
    ):

        raise ValueError(
            "variation_feasible doit être booléen ou None."
        )

    phy_feasible = (
        agreement_feasible
        and variation_feasible
    )

    return phy_feasible


# Cette fonction calcule le taux d'utilisation temporelle :
#
# u_time =
#     min(
#         1,
#         key_age / maximum_key_age
#     )
def calculate_time_utilization(
    key_age_s,
    maximum_key_age_s
):

    if key_age_s < 0:

        raise ValueError(
            "L'âge de clé ne peut pas être négatif."
        )

    if maximum_key_age_s <= 0:

        raise ValueError(
            "L'âge maximal doit être strictement positif."
        )

    time_utilization = min(
        1.0,
        key_age_s
        / maximum_key_age_s
    )

    return time_utilization


# Cette fonction calcule le taux d'utilisation
# lié au nombre de messages :
#
# u_msg =
#     min(
#         1,
#         messages_with_current_key
#         / maximum_messages_per_key
#     )
def calculate_message_utilization(
    messages_with_current_key,
    maximum_messages_per_key
):

    if messages_with_current_key < 0:

        raise ValueError(
            "Le nombre de messages ne peut pas être négatif."
        )

    if maximum_messages_per_key <= 0:

        raise ValueError(
            "Le nombre maximal de messages doit être "
            "strictement positif."
        )

    message_utilization = min(
        1.0,
        messages_with_current_key
        / maximum_messages_per_key
    )

    return message_utilization


# Cette fonction calcule l'indice de vieillissement :
#
# q_t =
#     max(
#         u_time,
#         u_msg
#     )
#
# La règle est conservative :
# la limite la plus proche domine.
def calculate_key_aging_index(
    key_age_s,
    maximum_key_age_s,
    messages_with_current_key,
    maximum_messages_per_key
):

    time_utilization = calculate_time_utilization(
        key_age_s,
        maximum_key_age_s
    )

    message_utilization = calculate_message_utilization(
        messages_with_current_key,
        maximum_messages_per_key
    )

    key_aging_index = max(
        time_utilization,
        message_utilization
    )

    return key_aging_index


# Cette fonction indique si le renouvellement
# anticipé doit être demandé :
#
# renewal_required =
#     key_aging_index >= renewal_trigger
def calculate_renewal_required(
    key_aging_index,
    renewal_trigger
):

    if key_aging_index < 0 or key_aging_index > 1:

        raise ValueError(
            "L'indice de vieillissement doit "
            "appartenir à [0, 1]."
        )

    if renewal_trigger < 0 or renewal_trigger > 1:

        raise ValueError(
            "Le seuil de renouvellement doit "
            "appartenir à [0, 1]."
        )

    renewal_required = (
        key_aging_index
        >= renewal_trigger
    )

    return renewal_required


# Cette fonction détecte l'expiration dure de la clé.
#
# La clé est expirée si :
# - son âge atteint la limite ;
# - son nombre de messages atteint la limite ;
# - une compromission est suspectée.
def calculate_key_expired(
    key_age_s,
    maximum_key_age_s,
    messages_with_current_key,
    maximum_messages_per_key,
    compromise_suspected
):

    if key_age_s < 0:

        raise ValueError(
            "L'âge de clé ne peut pas être négatif."
        )

    if maximum_key_age_s <= 0:

        raise ValueError(
            "L'âge maximal doit être strictement positif."
        )

    if messages_with_current_key < 0:

        raise ValueError(
            "Le nombre de messages ne peut pas être négatif."
        )

    if maximum_messages_per_key <= 0:

        raise ValueError(
            "Le nombre maximal de messages doit être "
            "strictement positif."
        )

    if not isinstance(
        compromise_suspected,
        bool
    ):

        raise ValueError(
            "compromise_suspected doit être booléen."
        )

    key_expired = (
        key_age_s
        >= maximum_key_age_s
        or messages_with_current_key
        >= maximum_messages_per_key
        or compromise_suspected
    )

    return key_expired


# Cette fonction calcule le temps restant
# avant la limite d'âge :
#
# T_age =
#     max(
#         maximum_key_age - key_age,
#         0
#     )
def calculate_remaining_age_time(
    key_age_s,
    maximum_key_age_s
):

    if key_age_s < 0:

        raise ValueError(
            "L'âge de clé ne peut pas être négatif."
        )

    if maximum_key_age_s <= 0:

        raise ValueError(
            "L'âge maximal doit être strictement positif."
        )

    remaining_age_time_s = max(
        maximum_key_age_s
        - key_age_s,
        0.0
    )

    return remaining_age_time_s


# Cette fonction calcule le temps restant
# avant la limite de messages :
#
# T_msg =
#     max(
#         maximum_messages
#         - current_messages,
#         0
#     )
#     * message_period
#
# Cette relation suppose un trafic périodique
# ou une période moyenne explicitement assumée.
def calculate_remaining_message_time(
    messages_with_current_key,
    maximum_messages_per_key,
    message_period_s
):

    if messages_with_current_key < 0:

        raise ValueError(
            "Le nombre de messages ne peut pas être négatif."
        )

    if maximum_messages_per_key <= 0:

        raise ValueError(
            "Le nombre maximal de messages doit être "
            "strictement positif."
        )

    if message_period_s <= 0:

        raise ValueError(
            "La période des messages doit être "
            "strictement positive."
        )

    remaining_message_count = max(
        maximum_messages_per_key
        - messages_with_current_key,
        0
    )

    remaining_message_time_s = (
        remaining_message_count
        * message_period_s
    )

    return remaining_message_time_s


# Cette fonction calcule l'échéance disponible
# avant la première limite de cryptopériode :
#
# T_deadline =
#     max(
#         T_min,
#         min(
#             T_age,
#             T_msg
#         )
#     )
def calculate_key_deadline(
    key_age_s,
    maximum_key_age_s,
    messages_with_current_key,
    maximum_messages_per_key,
    message_period_s,
    minimum_deadline_s
):

    if minimum_deadline_s is None:

        raise ValueError(
            "minimum_deadline_s doit être défini."
        )

    if minimum_deadline_s <= 0:

        raise ValueError(
            "L'échéance minimale doit être "
            "strictement positive."
        )

    remaining_age_time_s = (
        calculate_remaining_age_time(
            key_age_s,
            maximum_key_age_s
        )
    )

    remaining_message_time_s = (
        calculate_remaining_message_time(
            messages_with_current_key,
            maximum_messages_per_key,
            message_period_s
        )
    )

    first_limit_time_s = min(
        remaining_age_time_s,
        remaining_message_time_s
    )

    key_deadline_s = max(
        minimum_deadline_s,
        first_limit_time_s
    )

    return key_deadline_s


# Cette fonction calcule l'indice de qualité de K0 :
#
# Q_key(K0) =
#     1 - q_t
#
# Cet indice représente la fraîcheur
# de la clé conservée.
def calculate_k0_quality(
    key_aging_index
):

    if key_aging_index < 0 or key_aging_index > 1:

        raise ValueError(
            "L'indice de vieillissement doit "
            "appartenir à [0, 1]."
        )

    key_quality = (
        1
        - key_aging_index
    )

    return key_quality


# Cette fonction calcule l'indice de qualité
# de K1a et K1b :
#
# Q_key(K1) =
#     1 - h2(KDR)
#
# Cet indice mesure la qualité théorique
# de l'accord entre Alice et Bob.
def calculate_k1_quality(
    effective_kdr
):

    binary_entropy = calculate_binary_entropy(
        effective_kdr
    )

    key_quality = (
        1
        - binary_entropy
    )

    return key_quality


# Cette fonction calcule l'indice de qualité de K2 :
#
# Q_key(K2) =
#     1 - 2 ** (-security_strength_bits)
#
# Il s'agit d'une borne cryptographique idéalisée,
# et non d'une probabilité universelle
# de non-compromission.
def calculate_k2_quality(
    security_strength_bits
):

    if security_strength_bits is None:

        raise ValueError(
            "security_strength_bits doit être défini "
            "pour calculer la qualité de K2."
        )

    if security_strength_bits <= 0:

        raise ValueError(
            "Le niveau de sécurité doit être "
            "strictement positif."
        )

    key_quality = (
        1
        - 2 ** (
            -security_strength_bits
        )
    )

    return key_quality


# Cette fonction regroupe tous les calculs
# d'une action de gestion de clé
# dans un objet KeyMetrics.
def calculate_key_metrics(
    key_action,
    parameters,
    rho_ab=None,
    key_age_s=0.0,
    messages_with_current_key=0,
    compromise_suspected=False,
    variation_feasible=None,
    collected_measurements=0,
    candidate_ready=False
):

    # On calcule d'abord les informations
    # de cryptopériode communes aux quatre actions.
    key_aging_index = (
        calculate_key_aging_index(
            key_age_s=key_age_s,
            maximum_key_age_s=(
                parameters.maximum_key_age_s
            ),
            messages_with_current_key=(
                messages_with_current_key
            ),
            maximum_messages_per_key=(
                parameters.maximum_messages_per_key
            )
        )
    )

    renewal_required = (
        calculate_renewal_required(
            key_aging_index=(
                key_aging_index
            ),
            renewal_trigger=(
                parameters.renewal_trigger
            )
        )
    )

    key_expired = calculate_key_expired(
        key_age_s=key_age_s,
        maximum_key_age_s=(
            parameters.maximum_key_age_s
        ),
        messages_with_current_key=(
            messages_with_current_key
        ),
        maximum_messages_per_key=(
            parameters.maximum_messages_per_key
        ),
        compromise_suspected=(
            compromise_suspected
        )
    )

    key_deadline_s = calculate_key_deadline(
        key_age_s=key_age_s,
        maximum_key_age_s=(
            parameters.maximum_key_age_s
        ),
        messages_with_current_key=(
            messages_with_current_key
        ),
        maximum_messages_per_key=(
            parameters.maximum_messages_per_key
        ),
        message_period_s=(
            parameters.message_period_s
        ),
        minimum_deadline_s=(
            parameters.minimum_deadline_s
        )
    )

    # ------------------------------------------------------------
    # ACTION K0 : CONSERVER LA CLÉ
    # ------------------------------------------------------------

    if key_action == KeyAction.K0:

        key_quality = calculate_k0_quality(
            key_aging_index
        )

        return KeyMetrics(
            key_action=key_action,
            raw_kdr=None,
            effective_kdr=None,
            binary_entropy=None,
            reconciliation_yield=None,
            required_measurements=None,
            agreement_feasible=None,
            variation_feasible=None,
            phy_feasible=None,
            key_aging_index=(
                key_aging_index
            ),
            renewal_required=(
                renewal_required
            ),
            key_expired=(
                key_expired
            ),
            key_deadline_s=(
                key_deadline_s
            ),
            key_quality=(
                key_quality
            )
        )

    # ------------------------------------------------------------
    # ACTIONS K1a ET K1b : GÉNÉRATION PHY
    # ------------------------------------------------------------

    if (
        key_action == KeyAction.K1A
        or key_action == KeyAction.K1B
    ):

        # La corrélation du canal est obligatoire
        # pour calculer le KDR.
        if rho_ab is None:

            raise ValueError(
                "rho_ab doit être défini "
                "pour K1a et K1b."
            )

        raw_kdr = calculate_raw_kdr(
            rho_ab
        )

        effective_kdr = calculate_effective_kdr(
            raw_kdr=raw_kdr,
            quantization_mode=(
                parameters.quantization_mode
            ),
            guard_band_factor=(
                parameters.guard_band_factor
            )
        )

        binary_entropy = calculate_binary_entropy(
            effective_kdr
        )

        reconciliation_yield = (
            calculate_reconciliation_yield(
                effective_kdr=(
                    effective_kdr
                ),
                kept_measurement_ratio=(
                    parameters.kept_measurement_ratio
                )
            )
        )

        required_measurements = (
            calculate_required_measurements(
                key_length_bits=(
                    parameters.key_length_bits
                ),
                reconciliation_yield=(
                    reconciliation_yield
                ),
                numerical_epsilon=(
                    parameters.key_numerical_epsilon
                )
            )
        )

        agreement_feasible = (
            calculate_agreement_feasibility(
                effective_kdr=(
                    effective_kdr
                ),
                maximum_kdr=(
                    parameters.maximum_kdr
                )
            )
        )

        # Une valeur transmise directement
        # a priorité sur la valeur des paramètres.
        if variation_feasible is None:

            variation_feasible = (
                parameters.variation_feasible
            )

        phy_feasible = calculate_phy_feasibility(
            agreement_feasible=(
                agreement_feasible
            ),
            variation_feasible=(
                variation_feasible
            )
        )

        key_quality = calculate_k1_quality(
            effective_kdr
        )

        # collected_measurements peut être omis (valeur
        # par défaut 0), ce qui redonne exactement
        # l'ancien comportement (reliquat = required).
        if collected_measurements is None:

            collected_measurements = 0

        # candidate_ready=True signifie qu'une clé candidate
        # a déjà accumulé toutes les mesures nécessaires lors
        # d'une période antérieure. required_measurements
        # est recalculé à CHAQUE période à partir du canal
        # courant (il peut donc légèrement varier d'une
        # période à l'autre) : comparer un collected figé à
        # un required fraîchement recalculé referacturerait
        # une partie de la collecte déjà réalisée dès que le
        # canal se dégrade légèrement après que la clé est
        # devenue prête (démontré dans
        # results/k1_progressive_validation/
        # k1a_activation_decision_audit.csv — remaining=18
        # au lieu de 0 pour une clé pourtant déjà prête).
        #
        # Une fois prête, le reliquat est donc fixé à 0 sans
        # nouvelle comparaison : la collecte déjà réalisée
        # n'est jamais facturée une seconde fois.
        if candidate_ready:

            remaining_measurements = 0

        else:

            remaining_measurements = (
                calculate_remaining_measurements(
                    required_measurements=(
                        required_measurements
                    ),
                    collected_measurements=(
                        collected_measurements
                    )
                )
            )

        return KeyMetrics(
            key_action=key_action,
            raw_kdr=raw_kdr,
            effective_kdr=(
                effective_kdr
            ),
            binary_entropy=(
                binary_entropy
            ),
            reconciliation_yield=(
                reconciliation_yield
            ),
            required_measurements=(
                required_measurements
            ),
            agreement_feasible=(
                agreement_feasible
            ),
            variation_feasible=(
                variation_feasible
            ),
            phy_feasible=(
                phy_feasible
            ),
            key_aging_index=(
                key_aging_index
            ),
            renewal_required=(
                renewal_required
            ),
            key_expired=(
                key_expired
            ),
            key_deadline_s=(
                key_deadline_s
            ),
            key_quality=(
                key_quality
            ),
            collected_measurements=(
                collected_measurements
            ),
            remaining_measurements=(
                remaining_measurements
            )
        )

    # ------------------------------------------------------------
    # ACTION K2 : RENOUVELLEMENT CONVENTIONNEL
    # ------------------------------------------------------------

    if key_action == KeyAction.K2:

        key_quality = calculate_k2_quality(
            parameters.security_strength_bits
        )

        # K2 ne dépend pas du KDR
        # ni de la faisabilité PHY.
        return KeyMetrics(
            key_action=key_action,
            raw_kdr=None,
            effective_kdr=None,
            binary_entropy=None,
            reconciliation_yield=None,
            required_measurements=None,
            agreement_feasible=None,
            variation_feasible=None,
            phy_feasible=None,
            key_aging_index=(
                key_aging_index
            ),
            renewal_required=(
                renewal_required
            ),
            key_expired=(
                key_expired
            ),
            key_deadline_s=(
                key_deadline_s
            ),
            key_quality=(
                key_quality
            )
        )

    # Toute autre action est inconnue.
    raise ValueError(
        "L'action de clé doit être K0, K1a, K1b ou K2."
    )
