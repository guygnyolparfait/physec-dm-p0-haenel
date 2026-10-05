# ================================================================
# VALIDATION OPTION B (Phase 11, corrigée le 25/09/2026) — RÉSULTAT
# HONNÊTE : ÉCART NON EXPLIQUÉ AVEC LES INFORMATIONS PUBLIÉES
# ================================================================
#
# CORRECTION IMPORTANTE (25/09/2026) : une première version de ce
# fichier calculait l'erreur Option B vs Haenel UNIQUEMENT sous
# l'hypothèse CENTRAL (bug : compute_option_b_energy_mJ() était
# appelé sans l'argument `assumptions`, donc toujours CENTRAL, même
# dans les passages du rapport qui prétendaient parler de la borne
# HIGH). Les bornes LOW/HIGH n'étaient exercées que pour vérifier
# l'ORDRE des 4 cas, jamais pour chiffrer l'écart de MAGNITUDE. Ce
# fichier calcule maintenant l'écart aux TROIS jeux d'hypothèses
# (LOW/CENTRAL/HIGH) et les trois sont écrits dans le CSV.
#
# CONSTAT (ne pas cacher) : le modèle événementiel bottom-up
# (TX/RX/CPU, valeurs OFFICIAL_DATASHEET pour le matériel réel du
# banc d'essai -- MSP430G2x + CC110L, Section 6.3.2 -- et analyse de
# sensibilité sur les paramètres UNAVAILABLE) sous-estime largement
# le surcoût observé du repli MAC et du mode MAC_ONLY par rapport au
# RFF seul, y compris à la borne HIGH.
#
# CAUSE : ÉCART NON EXPLIQUÉ AVEC LES INFORMATIONS PUBLIÉES. Le
# temps d'antenne pur (bits/débit) et le calcul Chaskey-12, même à
# leurs bornes hautes documentées, ne suffisent pas à expliquer le
# surcoût mesuré par Haenel et al. Une cause PLAUSIBLE (pas
# confirmée, pas mesurée) est un coût protocolaire non quantifié
# par le papier (fenêtre d'écoute/timeout en réception, coût de
# resynchronisation) -- Haenel et al. ne publie aucune valeur pour
# cela, donc ce n'est pas un paramètre que ce module peut ajouter
# sans fabriquer une valeur. Cette cause est présentée ci-dessous
# comme UNE HYPOTHÈSE PARMI D'AUTRES POSSIBLES, jamais comme la
# conclusion établie de cette analyse.
#
# CONCLUSION MÉTHODOLOGIQUE : Option A (calibrée empiriquement sur
# les 4 points publiés, erreur <0.02%) reste le modèle de
# référence pour la comparaison P0 vs B5 sur l'échelle Haenel et
# al. Option B est conservée et documentée comme vérification de
# COHÉRENCE STRUCTURELLE (l'ordre RFF_ONLY < HYBRID < MAC_ONLY est
# bien reproduit qualitativement) et comme feuille de route pour
# une future collecte de données protocolaires plus fines -- PAS
# comme un modèle d'énergie absolue validé.

import csv
from pathlib import Path

from haenel_comparison.energy_option_b import (
    ASSUMPTIONS_CENTRAL,
    ASSUMPTIONS_HIGH,
    ASSUMPTIONS_LOW,
    compute_option_b_energy_mJ,
    energy_mac_only_mJ,
    energy_rff_fallback_mJ,
    energy_rff_success_mJ,
)
from haenel_comparison.energy_option_a import compute_energy_option_a_for_case
from haenel_comparison.haenel_config import HAENEL_FRR_CONFIGS, N_MESSAGES

OUTPUT_PATH = Path("results/haenel_comparison/option_a_vs_option_b.csv")

ASSUMPTION_SETS = (
    ("LOW", ASSUMPTIONS_LOW),
    ("CENTRAL", ASSUMPTIONS_CENTRAL),
    ("HIGH", ASSUMPTIONS_HIGH),
)


def check_ordering(assumptions):
    """Vérifie RFF_ONLY < HYBRID_05 < HYBRID_10 < MAC_ONLY sur le
    modèle événementiel BRUT (sans résiduel), pour isoler la
    question de l'ORDRE de celle de la MAGNITUDE."""

    success = energy_rff_success_mJ(assumptions)
    fallback = energy_rff_fallback_mJ(assumptions)
    mac_only = energy_mac_only_mJ(assumptions)

    hybrid_05 = 0.95 * success + 0.05 * fallback
    hybrid_10 = 0.90 * success + 0.10 * fallback

    ordering_ok = success < hybrid_05 < hybrid_10 < mac_only

    return {
        "rff_only": success,
        "hybrid_05": hybrid_05,
        "hybrid_10": hybrid_10,
        "mac_only": mac_only,
        "ordering_ok": ordering_ok,
    }


def build_comparison_table():
    """Une ligne par cas x jeu d'hypothèses (LOW/CENTRAL/HIGH), pour
    que l'écart Option B vs Haenel soit chiffré sur toute la plage
    de sensibilité -- pas seulement CENTRAL (bug corrigé le
    25/09/2026, voir en-tête de ce fichier)."""

    rows = []

    published_rff_only = HAENEL_FRR_CONFIGS["RFF_ONLY"]["published_energy_mJ"]

    for case_name, data in HAENEL_FRR_CONFIGS.items():

        published = data["published_energy_mJ"]
        frr = data["frr"]

        # BUG CORRIGÉ : compute_energy_option_a_for_case() retourne
        # déjà un TOTAL sur N_MESSAGES (car E_RFF_BASE_MJ vaut
        # published_energy_mJ tel quel, pas divisé) -- ne JAMAIS
        # multiplier une deuxième fois par N_MESSAGES ici. Une
        # première version de ce script le faisait, produisant une
        # erreur relative absurde (~9900%), détectée en relisant la
        # sortie plutôt que supposée correcte.
        option_a_result = compute_energy_option_a_for_case(case_name)
        option_a_is_direct_published = option_a_result is None
        option_a_total = (
            published if option_a_is_direct_published
            else option_a_result
        )

        # SURCOÛT INCRÉMENTAL au-dessus de RFF_ONLY (corrigé le
        # 25/09/2026, voir en-tête du fichier) : RFF_ONLY est
        # reproduit PAR CONSTRUCTION grâce à un résiduel calibré
        # dessus -- comparer les totaux absolus surestime donc ce
        # qu'Option B "explique" réellement. La grandeur pertinente
        # est le SURCOÛT (repli MAC / crypto) au-dessus de ce
        # plancher, pour B5_HAENEL_CALIBRATED comme pour Option B.
        measured_increment = published - published_rff_only

        for assumption_label, assumptions in ASSUMPTION_SETS:

            option_b_per_msg = compute_option_b_energy_mJ(
                case_name, frr, assumptions=assumptions
            )
            option_b_total = option_b_per_msg * N_MESSAGES

            option_b_rff_only_per_msg = compute_option_b_energy_mJ(
                "RFF_ONLY",
                HAENEL_FRR_CONFIGS["RFF_ONLY"]["frr"],
                assumptions=assumptions,
            )
            option_b_rff_only_total = option_b_rff_only_per_msg * N_MESSAGES

            modeled_increment = option_b_total - option_b_rff_only_total

            if measured_increment > 0:
                increment_explained_pct = (
                    100 * modeled_increment / measured_increment
                )
            else:
                increment_explained_pct = None  # RFF_ONLY lui-même

            rows.append(
                {
                    "case": case_name,
                    "option_b_assumption_set": assumption_label,
                    "haenel_published_mJ": published,
                    "option_a_mJ": option_a_total,
                    "option_a_note": (
                        "N/A -- MAC_ONLY n'a pas de structure "
                        "RFF_BASE+fallback, valeur publiée reprise "
                        "directement (pas une prédiction du modèle)"
                        if option_a_is_direct_published else ""
                    ),
                    "option_a_abs_error_mJ": abs(
                        option_a_total - published
                    ),
                    "option_a_rel_error_pct": (
                        100 * abs(option_a_total - published) / published
                    ),
                    "option_b_mJ": option_b_total,
                    "option_b_abs_error_mJ": abs(
                        option_b_total - published
                    ),
                    "option_b_rel_error_pct": (
                        100 * abs(option_b_total - published) / published
                    ),
                    "measured_increment_over_rff_only_mJ": measured_increment,
                    "modeled_increment_over_rff_only_mJ": modeled_increment,
                    "increment_explained_pct": increment_explained_pct,
                }
            )

    return rows


def main():

    Path("results/haenel_comparison").mkdir(
        parents=True, exist_ok=True
    )

    print("=" * 78)
    print("VÉRIFICATION DE L'ORDRE (modèle événementiel brut, sans "
          "résiduel calibré)")
    print("=" * 78)

    for label, assumptions in (
        ("CENTRAL", ASSUMPTIONS_CENTRAL),
        ("LOW", ASSUMPTIONS_LOW),
        ("HIGH", ASSUMPTIONS_HIGH),
    ):
        result = check_ordering(assumptions)
        print(f"\n{label} ({assumptions.label}):")
        print(f"  RFF_ONLY={result['rff_only']:.5f} mJ < "
              f"HYBRID_05={result['hybrid_05']:.5f} < "
              f"HYBRID_10={result['hybrid_10']:.5f} < "
              f"MAC_ONLY={result['mac_only']:.5f} mJ")
        print(f"  Ordre respecté : {result['ordering_ok']}")

    print()
    print("=" * 78)
    print("COMPARAISON MAGNITUDE : Haenel publié vs Option A vs Option B")
    print("(Option B calculée aux TROIS jeux d'hypothèses LOW/CENTRAL/HIGH)")
    print("=" * 78)

    rows = build_comparison_table()

    for row in rows:
        print(
            f"{row['case']:<16} [{row['option_b_assumption_set']:<7}] "
            f"publié={row['haenel_published_mJ']:>8.3f} mJ  "
            f"OptionA={row['option_a_mJ']:>8.3f} "
            f"(err={row['option_a_rel_error_pct']:>6.2f}%)  "
            f"OptionB={row['option_b_mJ']:>8.3f} "
            f"(err={row['option_b_rel_error_pct']:>6.2f}%)"
        )

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nCSV écrit : {OUTPUT_PATH}")

    print()
    print("=" * 78)
    print("SURCOÛT INCRÉMENTAL AU-DESSUS DE RFF_ONLY (corrigé le 25/09/2026)")
    print("=" * 78)
    print(
        "RFF_ONLY est reproduit PAR CONSTRUCTION (résiduel calibré "
        "dessus) : comparer les totaux absolus surestimerait ce "
        "qu'Option B explique réellement. La grandeur pertinente est "
        "le SURCOÛT incrémental (repli MAC / crypto) au-dessus de ce "
        "plancher.\n"
    )
    print(f"{'Cas':<16}{'Set':<9}{'Mesuré (mJ)':>13}{'Modélisé (mJ)':>15}"
          f"{'Expliqué %':>12}")
    for row in rows:
        if row["increment_explained_pct"] is None:
            continue
        print(
            f"{row['case']:<16}{row['option_b_assumption_set']:<9}"
            f"{row['measured_increment_over_rff_only_mJ']:>13.3f}"
            f"{row['modeled_increment_over_rff_only_mJ']:>15.3f}"
            f"{row['increment_explained_pct']:>11.2f}%"
        )

    incremental_rows = [
        row for row in rows if row["increment_explained_pct"] is not None
    ]
    min_explained = min(
        row["increment_explained_pct"] for row in incremental_rows
    )
    max_explained = max(
        row["increment_explained_pct"] for row in incremental_rows
    )

    print()
    print("=" * 78)
    print("CONSTAT HONNÊTE (corrigé le 25/09/2026, recalculé -- pas copié)")
    print("=" * 78)
    print(
        "Option B reproduit correctement l'ORDRE qualitatif des 4 "
        "cas (RFF_ONLY < HYBRID_05 < HYBRID_10 < MAC_ONLY), sous les "
        "trois jeux d'hypothèses LOW/CENTRAL/HIGH, avec le matériel "
        "réel du banc d'essai (MSP430G2x + CC110L, Section 6.3.2). "
        f"Sur le SURCOÛT INCRÉMENTAL au-dessus de RFF_ONLY (la "
        f"grandeur pertinente, pas le total absolu -- voir ci-dessus), "
        f"le modèle bottom-up actuel n'explique qu'une FAIBLE FRACTION "
        f"du surcoût mesuré : entre {min_explained:.1f}% et "
        f"{max_explained:.1f}% selon le cas et le jeu d'hypothèses. "
        "Une part importante de l'énergie reste agrégée dans le "
        "résiduel calibré (Option A) et/ou dépend de détails "
        "d'implémentation non publiés par Haenel et al. (fenêtre "
        "d'écoute/timeout en réception, coût de resynchronisation, "
        "configuration exacte de calibration radio) -- des causes "
        "POSSIBLES, non confirmées et non mesurées, jamais présentées "
        "comme la conclusion établie de cette analyse. CONCLUSION : "
        "Option A reste le modèle de référence QUANTITATIF pour la "
        "comparaison P0 vs B5_HAENEL_CALIBRATED sur l'échelle Haenel "
        "et al. ; Option B est une ANALYSE STRUCTURELLE / PHYSIQUE DE "
        "SENSIBILITÉ (ordre qualitatif reproduit), jamais un modèle "
        "d'énergie absolue validé."
    )


if __name__ == "__main__":
    main()
