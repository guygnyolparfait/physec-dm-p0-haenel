# ================================================================
# OPTION A — MODÈLE ÉNERGÉTIQUE AGRÉGÉ, CALIBRÉ SUR LES RÉSULTATS
# PUBLIÉS PAR HAENEL ET AL. (Table 1, p.15)
# ================================================================
#
# CE QU'EST OPTION A (formulation obligatoire, relecture du
# 25/09/2026) : un modèle énergétique agrégé, calibré directement
# sur les 4 mesures publiées de Haenel et al. Il sert d'ÉCHELLE
# COMMUNE pour comparer les politiques (B5_HAENEL_CALIBRATED,
# P0_AUTH_ONLY) sur les mêmes grandeurs physiques. Son accord avec
# les points de calibration est une VÉRIFICATION DE COHÉRENCE
# (le modèle a bien été résolu correctement), PAS UNE VALIDATION
# INDÉPENDANTE : les paramètres du modèle sont ajustés précisément
# pour reproduire ces points, donc les retrouver est vrai par
# construction. Ne jamais présenter cet accord comme une preuve
# d'exactitude physique.
#
# CE QUE LE PAPIER DIT DU PROTOCOLE (Section 6.3.3, Figure 11) :
# "Due to the first full authentication, the hybrid protocol was a
# little more energy-demanding at the start of the experiment."
# Puis, après ~6 transmissions, l'énergie cumulée du MAC-only et de
# l'hybride devient équivalente, avant que l'hybride ne devienne
# plus avantageux. Le papier NE DONNE AUCUNE valeur numérique isolée
# pour ce coût de démarrage -- impossible de le décomposer
# physiquement à partir de ce qui est publié.
#
# CONSÉQUENCE MÉTHODOLOGIQUE : plutôt que de supposer un coût
# uniforme par repli (RFF_BASE + N_fallback × coût_fixe, qui ignore
# implicitement ce démarrage), le modèle ci-dessous introduit un
# terme EFFECTIF agrégé à deux paramètres, résolu EXACTEMENT sur les
# deux points HYBRID publiés (système 2 équations / 2 inconnues) :
#
#   E_hybrid(FRR) = E_RFF_BASE_MJ
#                 + EFFECTIVE_FIXED_HYBRID_OVERHEAD_MJ
#                 + N_fallback_attendu(FRR) × EFFECTIVE_FALLBACK_COST_MJ
#
# EFFECTIVE_FIXED_HYBRID_OVERHEAD_MJ n'est PAS présenté comme le
# coût physique exact de la première authentification complète : il
# agrège tout ce que le papier ne permet pas de décomposer (la
# première authentification complète, et tout autre effet constant
# sur les 300 s que le modèle ne détaille pas). Statut : CALIBRATED
# / EFFECTIVE, jamais "coût physique exact".
#
# Ce terme fixe ne s'applique QU'aux cas HYBRID (protocole réel
# avec repli possible). RFF_ONLY est un cas LIMITE THÉORIQUE défini
# par le papier lui-même ("no fall back to cryptographic
# authentication") : par construction, aucun repli, donc aucune
# authentification complète de démarrage à amortir -- le terme fixe
# ne lui est jamais appliqué (voir compute_energy_option_a_for_case).
#
# MAC_ONLY n'a pas de structure RFF_BASE + repli du tout (chaque
# message EST déjà une authentification complète) : sa valeur
# publiée est reprise DIRECTEMENT ("published reference used
# directly"), jamais présentée comme prédite/calibrée par la
# formule hybride.

from haenel_comparison.haenel_config import (
    HAENEL_FRR_CONFIGS,
    N_MESSAGES,
)


def calibrate_effective_hybrid_terms_mJ():
    """Résout EXACTEMENT le système 2x2 (2 points HYBRID publiés,
    2 inconnues) pour EFFECTIVE_FIXED_HYBRID_OVERHEAD_MJ (F) et
    EFFECTIVE_FALLBACK_COST_MJ (C) :

        F + N_fallback_05 * C = HYBRID_05_published - RFF_ONLY_published
        F + N_fallback_10 * C = HYBRID_10_published - RFF_ONLY_published

    Contrairement à l'ancienne calibration (une seule inconnue,
    moyenne de deux estimations, résidu non nul de 0.006%-0.01%),
    ce système à deux inconnues reproduit EXACTEMENT (0.00% d'erreur
    par construction) les deux points HYBRID publiés -- voir
    validate_option_a() pour la confirmation chiffrée à l'exécution,
    jamais supposée sans être recalculée.
    """

    e_rff_base = HAENEL_FRR_CONFIGS["RFF_ONLY"]["published_energy_mJ"]

    frr_05 = HAENEL_FRR_CONFIGS["HYBRID_FRR_05"]["frr"]
    frr_10 = HAENEL_FRR_CONFIGS["HYBRID_FRR_10"]["frr"]

    n_fallback_05 = frr_05 * N_MESSAGES
    n_fallback_10 = frr_10 * N_MESSAGES

    surcharge_05 = (
        HAENEL_FRR_CONFIGS["HYBRID_FRR_05"]["published_energy_mJ"]
        - e_rff_base
    )
    surcharge_10 = (
        HAENEL_FRR_CONFIGS["HYBRID_FRR_10"]["published_energy_mJ"]
        - e_rff_base
    )

    # Résolution du système 2x2 par élimination :
    #   surcharge_10 - surcharge_05 = (n_fallback_10 - n_fallback_05) * C
    effective_fallback_cost_mJ = (
        (surcharge_10 - surcharge_05)
        / (n_fallback_10 - n_fallback_05)
    )

    effective_fixed_overhead_mJ = (
        surcharge_05 - n_fallback_05 * effective_fallback_cost_mJ
    )

    detail = {
        "e_rff_base_mJ": e_rff_base,
        "n_fallback_05": n_fallback_05,
        "n_fallback_10": n_fallback_10,
        "surcharge_05_mJ": surcharge_05,
        "surcharge_10_mJ": surcharge_10,
    }

    return effective_fixed_overhead_mJ, effective_fallback_cost_mJ, detail


(
    EFFECTIVE_FIXED_HYBRID_OVERHEAD_MJ,
    EFFECTIVE_FALLBACK_COST_MJ,
    _CALIBRATION_DETAIL,
) = calibrate_effective_hybrid_terms_mJ()

# Alias de compatibilité (nom utilisé par le code existant avant
# cette passe) : pointe maintenant vers le coût par repli du modèle
# à 2 paramètres, jamais recalculé séparément pour éviter toute
# divergence silencieuse entre les deux noms.
E_FALLBACK_CALIBRATED_MJ = EFFECTIVE_FALLBACK_COST_MJ

E_RFF_BASE_MJ = HAENEL_FRR_CONFIGS["RFF_ONLY"]["published_energy_mJ"]


def compute_energy_option_a_mJ(n_fallback, n_rff_direct=None, include_fixed_overhead=True):
    """E_total = E_RFF_BASE + [EFFECTIVE_FIXED_HYBRID_OVERHEAD] +
    N_fallback * EFFECTIVE_FALLBACK_COST.

    include_fixed_overhead=False reproduit le cas limite RFF_ONLY
    (aucun repli possible, donc aucune authentification de démarrage
    à amortir) -- mettre False uniquement pour n_fallback=0.

    n_fallback : nombre de messages effectivement repliés vers le
        MAC dans la réalisation simulée (issu de
        haenel_b5.summarize_haenel_events).
    n_rff_direct : non utilisé par la formule, gardé en paramètre
        pour lisibilité des appels et validations croisées
        (n_fallback + n_rff_direct doit valoir N_MESSAGES).
    """

    if n_rff_direct is not None:

        total = n_fallback + n_rff_direct

        if total != N_MESSAGES:

            raise ValueError(
                "n_fallback + n_rff_direct ("
                + str(total)
                + ") ne correspond pas à N_MESSAGES ("
                + str(N_MESSAGES)
                + ")."
            )

    overhead = (
        EFFECTIVE_FIXED_HYBRID_OVERHEAD_MJ if include_fixed_overhead else 0.0
    )

    return E_RFF_BASE_MJ + overhead + n_fallback * EFFECTIVE_FALLBACK_COST_MJ


def compute_energy_option_a_for_case(case_name):
    """Calcule l'énergie Option A pour un des 4 cas HAENEL_FRR_CONFIGS,
    en utilisant le nombre de replis ATTENDU (frr * N_MESSAGES), pour
    la table de validation (comparaison déterministe, pas une
    réalisation aléatoire particulière).

    RFF_ONLY (frr=0.0) : cas limite théorique du papier ("no fall
    back") -- aucun terme fixe, formule dégénère à E_RFF_BASE_MJ
    exactement (erreur 0.00% par construction, pas une coïncidence).
    MAC_ONLY (frr=None) : hors structure RFF_BASE + repli -- renvoie
    None (voir validate_option_a, "published reference used directly").
    """

    frr = HAENEL_FRR_CONFIGS[case_name]["frr"]

    if frr is None:
        # MAC_ONLY : ne suit pas le modèle RFF_BASE + fallback.
        return None

    expected_n_fallback = frr * N_MESSAGES
    include_fixed_overhead = frr > 0.0  # jamais pour RFF_ONLY

    return compute_energy_option_a_mJ(
        expected_n_fallback, include_fixed_overhead=include_fixed_overhead
    )


def validate_option_a():
    """Tableau de vérification de cohérence (PAS une validation
    indépendante -- voir en-tête du fichier) : configuration,
    énergie publiée, énergie Option A, erreur absolue, erreur
    relative. MAC_ONLY est signalé séparément avec la mention
    explicite "published reference used directly" : sa valeur n'est
    jamais prédite par la formule hybride."""

    rows = []

    for case_name, case_data in HAENEL_FRR_CONFIGS.items():

        published = case_data["published_energy_mJ"]
        simulated = compute_energy_option_a_for_case(case_name)

        if simulated is None:
            rows.append(
                {
                    "case": case_name,
                    "published_mJ": published,
                    "option_a_mJ": published,
                    "absolute_error_mJ": 0.0,
                    "relative_error_pct": 0.0,
                    "note": (
                        "published reference used directly -- "
                        "MAC_ONLY n'a pas de structure RFF_BASE + "
                        "fallback (chaque message est déjà une "
                        "authentification complète) ; ce n'est PAS "
                        "une prédiction du modèle hybride."
                    ),
                }
            )
            continue

        absolute_error = abs(simulated - published)
        relative_error_pct = 100.0 * absolute_error / published

        rows.append(
            {
                "case": case_name,
                "published_mJ": published,
                "option_a_mJ": simulated,
                "absolute_error_mJ": absolute_error,
                "relative_error_pct": relative_error_pct,
                "note": (
                    "cohérence de calibration (2 paramètres résolus "
                    "exactement sur HYBRID_05/HYBRID_10)"
                    if case_name != "RFF_ONLY"
                    else "cas limite théorique, aucun terme fixe appliqué"
                ),
            }
        )

    return rows


if __name__ == "__main__":

    print("Calibration EFFECTIVE_FIXED_HYBRID_OVERHEAD / "
          "EFFECTIVE_FALLBACK_COST (système 2x2 exact) :")
    print(f"  E_RFF_BASE_MJ (RFF_ONLY publié)      = "
          f"{_CALIBRATION_DETAIL['e_rff_base_mJ']:.3f} mJ")
    print(f"  Surcharge HYBRID_05 vs RFF_ONLY       = "
          f"{_CALIBRATION_DETAIL['surcharge_05_mJ']:.3f} mJ "
          f"({_CALIBRATION_DETAIL['n_fallback_05']:.1f} replis attendus)")
    print(f"  Surcharge HYBRID_10 vs RFF_ONLY       = "
          f"{_CALIBRATION_DETAIL['surcharge_10_mJ']:.3f} mJ "
          f"({_CALIBRATION_DETAIL['n_fallback_10']:.1f} replis attendus)")
    print(f"  -> EFFECTIVE_FIXED_HYBRID_OVERHEAD_MJ = "
          f"{EFFECTIVE_FIXED_HYBRID_OVERHEAD_MJ:.4f} mJ")
    print(f"  -> EFFECTIVE_FALLBACK_COST_MJ         = "
          f"{EFFECTIVE_FALLBACK_COST_MJ:.4f} mJ/repli\n")

    print("Table de vérification de cohérence Option A :")
    print(
        f"{'Cas':<16}{'Publié (mJ)':>14}{'Option A (mJ)':>16}"
        f"{'Erreur abs.':>14}{'Erreur rel. %':>16}"
    )
    for row in validate_option_a():
        print(
            f"{row['case']:<16}{row['published_mJ']:>14.3f}"
            f"{row['option_a_mJ']:>16.3f}"
            f"{row['absolute_error_mJ']:>14.4f}"
            f"{row['relative_error_pct']:>15.4f}%   ({row['note']})"
        )
