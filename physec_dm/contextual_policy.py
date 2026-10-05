# ================================================================
# DIAGNOSTIC PRÉALABLE — DM-EQ108 À DM-EQ110
# ================================================================
#
# Avant d'écrire ce module, le projet a été inspecté pour savoir
# si une formule numérique validée existe pour les poids
# contextuels du Decision Maker. Constat, avec citations exactes :
#
# 1. docs/03_EQUATIONS_REFERENCE.md, section "DM-EQ107" :
#
#    "Le fichier de modélisation interdit de coder des
#    coefficients numériques arbitraires avant validation par
#    l'encadrante. La documentation ne doit donc pas inventer une
#    formule [...] sans table de politique validée."
#
# 2. docs/03_EQUATIONS_REFERENCE.md, section "DM-EQ108 à DM-EQ110" :
#
#    "Les équations DM-EQ108 à DM-EQ110 décrivent des monotonies,
#    pas des coefficients numériques."
#
#    - DM-EQ108 : B_t↓ ⇒ w_E↑ (monotonie, forme non spécifiée)
#    - DM-EQ109 : criticité=1 ⇒ w_auth↑, w_L↑ (monotonie, forme
#      non spécifiée, "la redistribution nécessaire [...] doit
#      être définie par la table de politique validée")
#    - DM-EQ110 : q_t↑ ⇒ w_key↑ (monotonie, forme non spécifiée)
#
# 3. docs/03_EQUATIONS_REFERENCE.md, tableau récapitulatif :
#
#    "DM-EQ107–110 | poids et monotonies | politique à valider |
#    compute_contextual_weights()"
#
# 4. physec_dm/scientific_config.py, build_policy_catalog() :
#
#    policy_id "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS" —
#    "implementation_status": "BLOCKED",
#    "blocking_reason": "La fonction de poids contextuels
#    DM-EQ108 à DM-EQ110 n'est pas encore implémentée."
#
# CONCLUSION : aucune formule numérique validée n'existe dans ce
# projet pour transformer un contexte (batterie, criticité,
# vieillissement de clé) en un vecteur de poids concret. Seules
# des propriétés de MONOTONIE qualitative sont spécifiées.
#
# Conformément à l'instruction explicite reçue ("si les équations
# DM-EQ108 à DM-EQ110 sont absentes ou ambiguës, n'invente pas de
# formule"), ce module N'INVENTE AUCUN COEFFICIENT.
#
# resolve_contextual_weights() ci-dessous :
# - offre le point d'entrée UNIQUE utilisé par les cinq scénarios
#   (aucun scénario ne fixe ses propres poids à la main) ;
# - accepte un paramètre optionnel weight_policy : si
#   l'encadrante fournit un jour une table de politique validée
#   (une fonction context -> poids), elle peut être branchée ici
#   sans changer aucun appelant ;
# - en son absence (cas actuel), retourne explicitement le
#   vecteur STATIQUE déjà validé et déjà utilisé ailleurs dans le
#   projet (parameters.contextual_weights, cf.
#   scientific_config.py), en le signalant clairement comme un
#   repli statique et non comme une politique contextuelle
#   dynamique ;
# - expose séparément des fonctions de VALIDATION
#   (check_battery_monotonicity, check_criticality_monotonicity,
#   check_key_aging_monotonicity) qui pourront vérifier une
#   future politique dynamique dès qu'elle sera fournie et
#   validée — ces fonctions ne inventent aucun coefficient, elles
#   ne font que comparer deux résultats déjà produits par
#   weight_policy.
from physec_dm.decision_maker import validate_contextual_weights


# Ordre officiel des poids (DM-EQ107, section "Ordre des poids").
WEIGHT_ORDER = (
    "energy",
    "latency",
    "authentication",
    "key"
)


CONTEXTUAL_POLICY_STATUS = {
    "dm_eq108_110_dynamic_formula": "BLOCKED",
    "blocking_reason": (
        "DM-EQ108 à DM-EQ110 ne définissent que des "
        "monotonies qualitatives (batterie, criticité, "
        "vieillissement de la clé), jamais une forme "
        "fonctionnelle ni des coefficients numériques. "
        "docs/03_EQUATIONS_REFERENCE.md et "
        "physec_dm/scientific_config.py "
        "(build_policy_catalog, policy_id "
        "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS) marquent explicitement cette "
        "politique comme non implémentée, en attente de "
        "validation par l'encadrante."
    ),
    "fallback_used": (
        "parameters.contextual_weights (vecteur statique "
        "déjà validé et déjà utilisé par "
        "physec_dm/scientific_config.py et "
        "physec_dm/thesis_scenarios.py)."
    )
}


# Cette fonction est le point d'entrée UNIQUE utilisé par les
# cinq scénarios pour obtenir les poids contextuels du Decision
# Maker. Aucun scénario ne doit fixer ses propres poids à la
# main : ils passent tous par cette fonction.
def resolve_contextual_weights(
    context,
    state,
    parameters,
    weight_policy=None
):

    if weight_policy is not None:

        # Point d'extension pour une future table de
        # politique validée (context, state, parameters)
        # -> [w_E, w_L, w_auth, w_key]. Cette branche
        # n'invente rien : elle délègue entièrement au
        # paramètre fourni par l'appelant.
        candidate_weights = weight_policy(
            context,
            state,
            parameters
        )

        return validate_contextual_weights(
            candidate_weights,
            parameters.tchebycheff_epsilon
        )

    # Repli statique explicite : DM-EQ108 à DM-EQ110 restent
    # bloquées (voir CONTEXTUAL_POLICY_STATUS). Le même
    # vecteur statique déjà validé ailleurs dans le projet
    # est utilisé pour les cinq scénarios, garantissant que
    # le même Decision Maker (mêmes équations, même
    # politique) fonctionne partout.
    if parameters.contextual_weights is None:

        raise ValueError(
            "parameters.contextual_weights doit être "
            "défini : aucune politique contextuelle "
            "dynamique n'est disponible "
            "(DM-EQ108 à DM-EQ110 non implémentées, "
            "voir CONTEXTUAL_POLICY_STATUS)."
        )

    return validate_contextual_weights(
        parameters.contextual_weights,
        parameters.tchebycheff_epsilon
    )


# ================================================================
# VALIDATION DES MONOTONIES (DM-EQ108 À DM-EQ110)
# ================================================================
#
# Ces trois fonctions ne calculent aucun poids : elles comparent
# deux résultats déjà produits par une politique (statique ou,
# un jour, dynamique) et vérifient que l'ordre attendu par
# DM-EQ108/109/110 est respecté. Elles permettent de tester une
# future politique dynamique sans qu'aucun coefficient ne soit
# inventé ici.


# DM-EQ108 : B_t↓ ⇒ w_E↑ (à contexte identique par ailleurs).
def check_battery_monotonicity(
    weights_low_battery,
    weights_high_battery
):

    energy_index = WEIGHT_ORDER.index("energy")

    return (
        weights_low_battery[energy_index]
        >= weights_high_battery[energy_index]
    )


# DM-EQ109 : criticité=1 ⇒ w_auth↑ et w_L↑
# (à contexte identique par ailleurs).
def check_criticality_monotonicity(
    weights_critical,
    weights_normal
):

    latency_index = WEIGHT_ORDER.index("latency")
    authentication_index = WEIGHT_ORDER.index(
        "authentication"
    )

    return (
        weights_critical[authentication_index]
        >= weights_normal[authentication_index]
        and weights_critical[latency_index]
        >= weights_normal[latency_index]
    )


# DM-EQ110 : q_t↑ ⇒ w_key↑ (à contexte identique par ailleurs).
def check_key_aging_monotonicity(
    weights_aged_key,
    weights_fresh_key
):

    key_index = WEIGHT_ORDER.index("key")

    return (
        weights_aged_key[key_index]
        >= weights_fresh_key[key_index]
    )
