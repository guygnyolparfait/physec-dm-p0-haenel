# ================================================================
# ADAPTATEUR ÉNERGÉTIQUE COMMUN — EXPÉRIENCE 1 (ÉNERGIE HAENEL)
# ================================================================
#
# Objectif : donner à B5_HAENEL_CALIBRATED ET à P0_AUTH_ONLY la
# MÊME échelle énergétique -- celle mesurée par Haenel et al. sur
# leur propre banc d'essai (300 s / 100 messages, MSP430/CC110L) --
# pour que la comparaison porte sur le COMPORTEMENT (quelle
# décision est choisie) et non sur deux échelles physiques
# incomparables (voir le constat de la passe précédente : notre
# modèle LoRa/Semtech, energy_latency.py, et le matériel de
# Haenel et al. n'ont pas la même échelle absolue en mJ).
#
# CE MODULE NE TOUCHE JAMAIS energy_latency.py NI LES CAMPAGNES
# S1-S5. Il ne s'applique qu'aux évaluations construites pour ce
# banc d'essai précis (voir p0_auth_only.py).
#
# CE QUI EST RECALIBRÉ ICI : uniquement l'ÉNERGIE et la LATENCE
# (cette dernière neutralisée, voir §2 ci-dessous -- Haenel et al.
# ne publie aucune latence comparable). La robustesse
# d'authentification (Rauth) et la qualité de clé (Qkey) restent
# calculées par le VRAI modèle physec_dm (authentication.py,
# key_generation.py) : ce ne sont pas des grandeurs que Haenel et
# al. mesure, donc rien à recalibrer dessus pour l'instant.
#
# ================================================================
# 1. ÉNERGIE (PUBLISHED / DERIVED / CALIBRATED -- jamais fabriqué)
# ================================================================

from haenel_comparison.energy_option_a import (
    EFFECTIVE_FALLBACK_COST_MJ,
    EFFECTIVE_FIXED_HYBRID_OVERHEAD_MJ,
)
from haenel_comparison.haenel_config import HAENEL_FRR_CONFIGS, N_MESSAGES

# PUBLISHED (Table 1, p.15) / DERIVED (divisé par N_MESSAGES=100).
E_MAC_PER_MESSAGE_MJ = (
    HAENEL_FRR_CONFIGS["MAC_ONLY"]["published_energy_mJ"] / N_MESSAGES
)  # = 5.64743 mJ/message

E_RFF_BASE_PER_MESSAGE_MJ = (
    HAENEL_FRR_CONFIGS["RFF_ONLY"]["published_energy_mJ"] / N_MESSAGES
)  # = 3.55412 mJ/message

# CALIBRATED_EFFECTIVE -- réutilise EXACTEMENT la calibration à 2
# paramètres d'energy_option_a.py (système résolu exactement sur
# les 2 points HYBRID publiés), jamais recalculée séparément pour
# éviter toute divergence silencieuse entre les deux modules.
E_FALLBACK_EXTRA_MJ = EFFECTIVE_FALLBACK_COST_MJ  # ~9.86 mJ/repli

# AVERTISSEMENT EXPLICITE : ces valeurs sont une calibration
# SPÉCIFIQUE à ce banc d'essai (300 s, 100 messages, matériel
# MSP430/CC110L de Haenel et al.). Elles ne doivent JAMAIS être
# réutilisées comme des constantes universelles de coût
# énergétique ailleurs dans le projet (S1-S5 gardent leur propre
# modèle LoRa/Semtech, energy_latency.py, inchangé).


def a1_energy_mJ():
    """A1 (MAC direct, pas de tentative RFF) : coût déterministe,
    identique pour B5_HAENEL_CALIBRATED et pour P0_AUTH_ONLY."""

    return E_MAC_PER_MESSAGE_MJ


def initial_full_auth_overhead_mJ():
    """Surcoût EFFECTIF (CALIBRATED_EFFECTIVE, PAS un coût physique
    exact) attribué par convention au PREMIER message d'une
    campagne hybride, représentant l'authentification complète de
    démarrage documentée par Haenel et al. (Section 6.3.3, Fig. 11 :
    "Due to the first full authentication, the hybrid protocol was
    a little more energy-demanding at the start of the experiment").
    Le papier ne publie aucune valeur isolée pour ce coût : ce
    module réutilise EFFECTIVE_FIXED_HYBRID_OVERHEAD_MJ
    (energy_option_a.py), résolu par calibration agrégée sur les
    2 points HYBRID publiés, jamais une valeur physique mesurée
    séparément. Convention explicite (voir run_haenel_experiment_a.py) :
    ce surcoût est ajouté UNE SEULE FOIS, sur le message d'indice 0
    d'une campagne HYBRID, jamais sur RFF_ONLY (cas limite théorique
    "no fall back" du papier) ni sur MAC_ONLY (déjà une
    authentification complète à chaque message par définition)."""

    return EFFECTIVE_FIXED_HYBRID_OVERHEAD_MJ


def a2_realized_energy_mJ(rff_rejected):
    """Coût RÉALISÉ d'un message traité par A2, une fois le
    tirage stochastique FRR connu -- utilisé pour
    B5_HAENEL_CALIBRATED (qui suit le protocole message par
    message) et pour calculer l'énergie totale réellement
    consommée sur une réalisation donnée de P0 (a posteriori, pour
    le CSV détaillé). N'inclut PAS le surcoût de première
    authentification (voir initial_full_auth_overhead_mJ, ajouté
    séparément par l'appelant sur le message d'indice 0)."""

    extra = E_FALLBACK_EXTRA_MJ if rff_rejected else 0.0
    return E_RFF_BASE_PER_MESSAGE_MJ + extra


def a2_expected_energy_mJ(frr):
    """Coût ATTENDU d'un message traité par A2, AVANT de savoir
    si le tirage FRR va rejeter ce message précis --
    E[énergie | choisir A2] = E_RFF_BASE
                             + EFFECTIVE_FIXED_HYBRID_OVERHEAD / N_MESSAGES
                             + FRR * E_FALLBACK_EXTRA.

    Le terme EFFECTIVE_FIXED_HYBRID_OVERHEAD / N_MESSAGES amortit,
    sur l'espérance PAR MESSAGE, le surcoût de première
    authentification complète du protocole hybride (voir
    initial_full_auth_overhead_mJ) : P0 évalue une décision
    répétée sur un contexte statique, pas un message précis, donc
    la part attendue de ce coût ponctuel est répartie sur
    l'ensemble de la campagne -- convention explicite, documentée,
    jamais un coût physique par message mesuré séparément.

    C'est cette espérance, et non un tirage réalisé, qui doit être
    fournie au Decision Maker P0 : P0 décide AVANT que l'issue du
    test RFF soit connue, exactement comme le champ
    cost_metrics.expected_energy_j (déjà utilisé partout ailleurs
    dans physec_dm.decision_maker) représente déjà une espérance,
    jamais une réalisation. Ce module ne fait que recalibrer cette
    espérance sur l'échelle Haenel et al. au lieu du modèle
    LoRa/Semtech -- la logique "on évalue une espérance avant
    décision" n'est pas nouvelle, elle est reprise telle quelle."""

    if frr is None:
        raise ValueError(
            "frr=None correspond à MAC_ONLY : utiliser "
            "a1_energy_mJ(), pas a2_expected_energy_mJ()."
        )

    amortized_fixed_overhead = (
        EFFECTIVE_FIXED_HYBRID_OVERHEAD_MJ / N_MESSAGES
    )

    return (
        E_RFF_BASE_PER_MESSAGE_MJ
        + amortized_fixed_overhead
        + frr * E_FALLBACK_EXTRA_MJ
    )


# ================================================================
# 2. LATENCE -- NON FOURNIE PAR HAENEL, JAMAIS INVENTÉE
# ================================================================
#
# Haenel et al. ne publie aucune latence par message comparable à
# notre normalized_latency (ils rapportent une énergie et une
# durée totale de 300 s, pas un budget de délai par message ni de
# décomposition temporelle par opération). Statut explicite :

LATENCY_STATUS = "UNAVAILABLE / NOT DIRECTLY COMPARABLE"

# Décision méthodologique explicite (documentée, pas silencieuse) :
# comme le Decision Maker a besoin d'une valeur de latence pour
# construire son vecteur objectif à 4 composantes (on ne modifie
# pas la structure du Decision Maker), on fixe la MÊME valeur
# neutre pour A1 et A2. Sur un axe où les deux candidats sont
# strictement égaux, la normalisation idéal/nadir donne 0 pour les
# deux (cf. res:eq:normalisation du rapport : "0 si
# |nadir-idéal| <= epsilon") -- cet axe ne pèse alors JAMAIS dans
# l'arbitrage de Tchebycheff. C'est une neutralisation
# méthodologique explicite, PAS une estimation de la vraie latence
# du protocole de Haenel et al.
NEUTRAL_LATENCY_VALUE = 0.0


# ================================================================
# 3. APPLICATION À UNE DecisionEvaluation DÉJÀ CALCULÉE
# ================================================================


def apply_haenel_energy_scale(evaluation, energy_mJ):
    """Remplace UNIQUEMENT l'énergie (par la valeur calibrée
    Haenel et al., en mJ) et la latence (neutralisée, voir §2)
    d'une DecisionEvaluation déjà produite par
    physec_dm.decision_maker.evaluate_decision. La robustesse
    d'authentification et la qualité de clé, déjà calculées par
    le vrai modèle physec_dm, ne sont PAS touchées.

    ATTENTION D'UNITÉ, LOCALE À CE MODULE : à partir d'ici,
    evaluation.cost_metrics.expected_energy_j contient en réalité
    une valeur en MILLIJOULES (mJ), pas en joules comme partout
    ailleurs dans physec_dm. Ce choix est délibéré (rester sur
    l'échelle native des chiffres publiés par Haenel et al.,
    éviter une conversion qui n'ajoute aucune information) et sans
    conséquence sur l'arbitrage : Pareto et Tchebycheff sont
    invariants à un changement d'échelle monotone identique
    appliqué aux deux candidats. Ce module ne doit JAMAIS être
    utilisé en dehors de haenel_comparison/."""

    evaluation.cost_metrics.expected_energy_j = energy_mJ
    evaluation.cost_metrics.normalized_latency = (
        NEUTRAL_LATENCY_VALUE
    )

    evaluation.objective_vector = [
        energy_mJ,
        NEUTRAL_LATENCY_VALUE,
        -evaluation.authentication_metrics.authentication_robustness,
        -evaluation.key_metrics.key_quality,
    ]

    return evaluation


# ================================================================
# 4. FAR DE A2 -- DONNER À P0 LA MÊME PERFORMANCE RFF QUE HAENEL
#    (comparaison principale, demandée après relecture du 25/09/2026)
# ================================================================
#
# La comparaison principale doit répondre à : "que fait notre
# Decision Maker si on lui donne les mécanismes disponibles dans
# l'expérience Haenel, mais qu'on remplace leur règle fixe de
# décision par P0 ?" Cela suppose que A2 (RFF) reçoive la même
# PERFORMANCE DE SÉCURITÉ que celle publiée par Haenel et al., pas
# le FAR natif de notre propre modèle de canal physec_dm (~8.39e-5,
# qui dépend d'un contexte SNR ASSUMED -- voir
# P0_NATIVE_RFF_SENSITIVITY dans p0_auth_only_haenel_scale.py, qui
# reste disponible séparément, jamais mélangée à la comparaison
# principale).

from physec_dm.authentication import (
    calculate_a2_robustness,
    calculate_a2_total_false_acceptance,
    calculate_mac_forgery_probability,
)

# PUBLISHED_HAENEL (Section 6.3.1 : "This value was chosen as it
# led to a FAR of 0.2% in our live experiment", en lien avec le
# FRR=10% simulé dans le banc d'essai énergétique -- lui-même issu
# de l'arrondi du FRR=10.89% mesuré dans l'expérience de
# classification, Section 6.2.2). Haenel et al. ne publie pas de
# FAR apparié spécifiquement au FRR=5% (voir Section 6.2.2 : seule
# la paire FRR=10.89%/FAR=0.20% est rapportée).
FAR_RFF_HAENEL = 0.002


def apply_haenel_rff_far_to_a2(evaluation, parameters, far=FAR_RFF_HAENEL):
    """Remplace le FAR (et donc R_auth) de l'évaluation A2 par la
    performance PUBLIÉE de Haenel et al., en réutilisant les VRAIES
    formules du modèle physec_dm (authentication.py,
    calculate_a2_total_false_acceptance / calculate_a2_robustness)
    -- jamais un remplacement à la main du type "1 - far", qui
    ignorerait le terme résiduel de forge MAC déjà présent dans le
    modèle. Doit être appelée APRÈS apply_haenel_energy_scale
    (l'ordre ne change rien au résultat, les deux ne touchent pas
    aux mêmes champs, mais la convention du code est de recalibrer
    l'énergie puis la sécurité)."""

    mac_forgery_probability = calculate_mac_forgery_probability(
        parameters.mac_tag_bits
    )

    total_false_acceptance = calculate_a2_total_false_acceptance(
        far, mac_forgery_probability
    )

    authentication_robustness = calculate_a2_robustness(
        total_false_acceptance
    )

    evaluation.authentication_metrics.far = far
    evaluation.authentication_metrics.total_false_acceptance_probability = (
        total_false_acceptance
    )
    evaluation.authentication_metrics.authentication_robustness = (
        authentication_robustness
    )

    evaluation.objective_vector = [
        evaluation.cost_metrics.expected_energy_j,
        evaluation.cost_metrics.normalized_latency,
        -authentication_robustness,
        -evaluation.key_metrics.key_quality,
    ]

    return evaluation
