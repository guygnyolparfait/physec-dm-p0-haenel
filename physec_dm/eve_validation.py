# Ce module évalue, APRÈS la décision du Decision Maker,
# la marge de secret d'une clé générée par voie physique
# (K1a ou K1b) face à une espionne passive Ève.
#
# Statut : extension scientifique de cette étude, ajoutée
# après discussion avec l'encadrante. Le document de
# modélisation initial plaçait tout modèle explicite du
# canal Alice-Mallory/Ève dans son périmètre exclu ("hors
# périmètre initial", section II.F). Cette extension couvre
# une évaluation PARTIELLE et volontairement modeste : une
# marge de KDR empirique entre Bob et Ève, jamais une preuve
# d'information mutuelle ni un calcul de capacité secrète
# conditionnelle rigoureux (qui exigerait notamment de
# modéliser la fuite de la réconciliation publique et le
# taux de compression réel de l'amplification de
# confidentialité — non couverts ici).
#
# RÈGLE ARCHITECTURALE ABSOLUE :
#
# Aucune fonction de ce module ne doit jamais être appelée
# par physec_dm.decision_maker, ni par la construction du
# Context présenté au Decision Maker
# (physec_dm.mission.create_mission_context). Ève est
# intégrée à CHAQUE simulation (mission.py l'appelle après
# coup, à l'activation d'une clé candidate), mais ses
# observations ne sont jamais transmises au DM : dans la
# réalité, Bob ne connaît ni la position exacte d'Ève, ni
# ses mesures secrètes, ni son KDR instantané.
import math

from scipy.special import j0

from physec_dm.channel import calculate_reciprocity
from physec_dm.key_generation import calculate_raw_kdr


# Cette fonction calcule la corrélation spatiale entre deux
# récepteurs séparés d'une distance donnée, sous l'hypothèse
# de diffusion isotrope de Clarke-Jakes.
#
# La même fonction de Bessel J0 utilisée pour la
# décorrélation TEMPORELLE (channel.calculate_temporal_
# correlation, J0(2*pi*f_d*Delta_t)) s'applique à la
# décorrélation SPATIALE en substituant une distance
# normalisée par la longueur d'onde à la place de f_d*Delta_t :
#
# rho_spatial(d) = J0(2 * pi * d / lambda)
#
# Cette relation n'est pas une nouvelle formule : c'est la
# même construction de Clarke-Jakes déjà citée dans le
# document de modélisation, appliquée à une séparation
# spatiale plutôt qu'à un délai temporel. L'hypothèse de
# diffusion isotrope doit être annoncée explicitement :
# elle peut être optimiste en propagation longue portée à
# trajet direct dominant (cas LoRa fréquent), où la
# décorrélation réelle peut être plus faible qu'attendu.
#
# Statut : dérivé (Clarke-Jakes), sous hypothèse de
# diffusion isotrope.
def calculate_spatial_correlation(
    separation_m,
    carrier_frequency_hz,
    speed_of_light_m_s
):

    if separation_m < 0:

        raise ValueError(
            "La séparation spatiale ne peut pas "
            "être négative."
        )

    if carrier_frequency_hz <= 0:

        raise ValueError(
            "La fréquence porteuse doit être "
            "strictement supérieure à zéro."
        )

    if speed_of_light_m_s <= 0:

        raise ValueError(
            "La vitesse de la lumière doit être "
            "strictement supérieure à zéro."
        )

    wavelength_m = (
        speed_of_light_m_s
        / carrier_frequency_hz
    )

    bessel_argument = (
        2
        * math.pi
        * separation_m
        / wavelength_m
    )

    spatial_correlation = float(
        j0(bessel_argument)
    )

    return spatial_correlation


# Cette fonction applique l'inversion de bits optimale pour
# Ève : une corrélation fortement NÉGATIVE ne doit pas être
# interprétée automatiquement comme une mauvaise observation
# pour elle, car sous quantification par signe, inverser la
# règle de décision (lire 0 à la place de 1 et
# réciproquement) transforme un fort désaccord en fort
# accord. Le pire cas pour la sécurité (le meilleur cas pour
# Ève) est donc :
#
# KDR_eff = min(KDR, 1 - KDR)
#
# Exemple limite : rho=-1 donne KDR=1,0 (désaccord total
# sans inversion), mais KDR_eff=0,0 après inversion — aussi
# dangereux que rho=+1. rho=0 donne KDR=0,5 dans les deux
# cas (aucune information, cas le plus sûr).
#
# Cette correction ne s'applique QU'À ÈVE : le modèle
# nominal d'accord Alice-Bob (key_generation.calculate_raw_kdr,
# sans inversion) reste inchangé, car Alice et Bob suivent
# un protocole de réconciliation fixé à l'avance, sans
# connaître par avance le signe de rho_AB, alors que
# l'évaluation d'Ève est un majorant prudent a posteriori de
# ce qu'une adversaire optimale pourrait obtenir.
def calculate_effective_kdr_with_inversion(
    raw_kdr
):

    if raw_kdr < 0 or raw_kdr > 1:

        raise ValueError(
            "Le KDR brut doit appartenir à [0, 1]."
        )

    return min(
        raw_kdr,
        1 - raw_kdr
    )


# Cette fonction calcule le KDR EFFECTIF d'Ève (après
# inversion de bits optimale) à partir de sa corrélation
# avec le canal Alice-Bob, via la MÊME loi de l'arc-sinus
# que celle utilisée pour le KDR brut d'Alice et Bob
# (key_generation.calculate_raw_kdr). Aucune nouvelle loi
# n'est introduite : Ève est un second récepteur soumis à
# la même physique de quantification par signe, à qui l'on
# accorde en plus le bénéfice de l'inversion (voir
# calculate_effective_kdr_with_inversion).
def calculate_eve_kdr(
    rho_ae
):

    raw_kdr = calculate_raw_kdr(
        rho_ae
    )

    return calculate_effective_kdr_with_inversion(
        raw_kdr
    )


# Cette fonction retient, pour Ève, le MEILLEUR de ses deux
# canaux accessibles (liaison montante via d_BE, liaison
# descendante via d_AE), après inversion de bits sur chacun.
#
# Combiner d'abord les corrélations par un max(rho), puis
# appliquer l'inversion ensuite, serait INCORRECT : après
# inversion, une corrélation fortement négative peut devenir
# plus dangereuse qu'une corrélation positive plus faible en
# valeur absolue (voir calculate_effective_kdr_with_inversion).
# Il faut donc calculer le KDR effectif SÉPARÉMENT pour
# chaque direction, puis retenir le plus petit des deux
# (le plus dangereux pour la sécurité) :
#
# KDR_E* = min(KDR_eff_montante, KDR_eff_descendante)
#
# Statut : politique (choix de combinaison prudent),
# construction de cette étude à partir de deux applications
# de calculate_spatial_correlation et de la loi de
# l'arc-sinus avec inversion.
def calculate_eve_best_channel_kdr(
    distance_be_m,
    distance_ae_m,
    hardware_reciprocity,
    noise_correlation,
    carrier_frequency_hz,
    speed_of_light_m_s
):

    spatial_correlation_be = (
        calculate_spatial_correlation(
            separation_m=distance_be_m,
            carrier_frequency_hz=(
                carrier_frequency_hz
            ),
            speed_of_light_m_s=(
                speed_of_light_m_s
            )
        )
    )

    spatial_correlation_ae = (
        calculate_spatial_correlation(
            separation_m=distance_ae_m,
            carrier_frequency_hz=(
                carrier_frequency_hz
            ),
            speed_of_light_m_s=(
                speed_of_light_m_s
            )
        )
    )

    rho_eve_uplink = calculate_reciprocity(
        hardware_reciprocity=(
            hardware_reciprocity
        ),
        temporal_correlation=(
            spatial_correlation_be
        ),
        noise_correlation=noise_correlation
    )

    rho_eve_downlink = calculate_reciprocity(
        hardware_reciprocity=(
            hardware_reciprocity
        ),
        temporal_correlation=(
            spatial_correlation_ae
        ),
        noise_correlation=noise_correlation
    )

    kdr_eve_uplink = calculate_eve_kdr(
        rho_eve_uplink
    )

    kdr_eve_downlink = calculate_eve_kdr(
        rho_eve_downlink
    )

    # Ève retient son meilleur canal accessible : le KDR
    # effectif le plus faible (le plus dangereux pour la
    # sécurité), jamais le plus favorable à la sécurité.
    best_kdr_eve = min(
        kdr_eve_uplink,
        kdr_eve_downlink
    )

    return {
        "rho_eve_uplink": rho_eve_uplink,
        "rho_eve_downlink": rho_eve_downlink,
        "kdr_eve_uplink": kdr_eve_uplink,
        "kdr_eve_downlink": kdr_eve_downlink,
        "kdr_eve_best": best_kdr_eve
    }


# Cette fonction calcule la marge de secret empirique :
#
# marge = KDR_Eve - KDR_AB
#
# Une marge positive indique qu'Ève se trompe plus souvent
# que Bob en devinant les bits d'Alice ; une marge nulle ou
# négative indique qu'Ève n'est pas moins bien placée que
# Bob, ce qui interdit toute revendication de secret.
def calculate_secrecy_margin(
    kdr_eve,
    kdr_ab
):

    return (
        kdr_eve
        - kdr_ab
    )


# Cette fonction applique le critère de secret
# pré-enregistré (politique, à balayer en sensibilité) :
#
# sécurisée si :
#     KDR_Eve > KDR_AB (condition nécessaire, absolue)
#     ET marge > eve_secrecy_margin_minimum
#
# Statut : politique — exploratoire, jamais présentée comme
# un seuil universel de la littérature.
def evaluate_key_secrecy(
    kdr_eve,
    kdr_ab,
    minimum_margin
):

    if minimum_margin < 0:

        raise ValueError(
            "minimum_margin ne peut pas être négatif."
        )

    # Condition nécessaire absolue : si Ève se trompe au
    # moins aussi peu souvent que Bob, elle dispose d'une
    # observation au moins aussi bonne — aucun secret ne
    # peut être revendiqué, quelle que soit la marge exigée.
    if kdr_eve <= kdr_ab:

        return False

    margin = calculate_secrecy_margin(
        kdr_eve=kdr_eve,
        kdr_ab=kdr_ab
    )

    return margin > minimum_margin


# Cette fonction regroupe tout le calcul de validation
# pour une seule période, à partir des grandeurs déjà
# calculées par le canal Alice-Bob (jamais recalculées
# différemment). Elle est destinée à être appelée par
# physec_dm.mission après une activation de clé K1a/K1b,
# jamais avant ni pendant l'évaluation du Decision Maker.
def evaluate_eve_secrecy_for_period(
    rho_ab,
    noise_correlation,
    parameters,
    distance_be_m=None,
    distance_ae_m=None
):

    # Hypothèse symétrique par défaut (simplification de
    # scénario explicite) : les deux distances valent
    # eve_standoff_distance_m si aucune valeur distincte
    # n'est fournie.
    if distance_be_m is None:

        distance_be_m = (
            parameters.eve_standoff_distance_m
        )

    if distance_ae_m is None:

        distance_ae_m = (
            parameters.eve_standoff_distance_m
        )

    eve_channel = calculate_eve_best_channel_kdr(
        distance_be_m=distance_be_m,
        distance_ae_m=distance_ae_m,
        hardware_reciprocity=(
            parameters.hardware_reciprocity
        ),
        noise_correlation=noise_correlation,
        carrier_frequency_hz=(
            parameters.carrier_frequency_hz
        ),
        speed_of_light_m_s=(
            parameters.speed_of_light_m_s
        )
    )

    kdr_eve = eve_channel["kdr_eve_best"]

    kdr_ab = calculate_raw_kdr(
        rho_ab
    )

    margin = calculate_secrecy_margin(
        kdr_eve=kdr_eve,
        kdr_ab=kdr_ab
    )

    secure = evaluate_key_secrecy(
        kdr_eve=kdr_eve,
        kdr_ab=kdr_ab,
        minimum_margin=(
            parameters.eve_secrecy_margin_minimum
        )
    )

    return {
        "rho_eve_uplink": (
            eve_channel["rho_eve_uplink"]
        ),
        "rho_eve_downlink": (
            eve_channel["rho_eve_downlink"]
        ),
        "kdr_ab": kdr_ab,
        "kdr_eve": kdr_eve,
        "secrecy_margin": margin,
        "secure": secure
    }
