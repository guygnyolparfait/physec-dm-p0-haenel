# ================================================================
# HISTORIQUE / SUPERSEDED — première campagne (10 graines), ANCIEN
# nommage "B5-littéral". CONSERVÉ tel quel pour l'historique du
# projet, mais SUPERSEDED par run_haenel_experiment_a.py (30 graines,
# nommage corrigé B5_HAENEL_CALIBRATED) et
# p0_auth_only_haenel_rff.py (comparaison principale, FAR publié
# Haenel) -- ne pas utiliser ce fichier comme référence pour de
# nouvelles conclusions, il n'est plus appelé par run_all_final.sh.
# ================================================================
# EXPÉRIENCE 1 (ANCIENNE VERSION) : B5-LITTÉRAL (calibré Option A)
# vs P0_AUTH_ONLY
# ================================================================
#
# Reproduit d'abord le banc d'essai énergétique de Haenel et al.
# (B5-littéral, Option A), puis fait tourner P0 restreint à K0
# dans exactement le même nombre de messages, pour répondre à :
# "Le Decision Maker multiobjectif apporte-t-il un comportement
# différent de la règle fixe RFF-puis-MAC de Haenel et al. dans
# les mêmes conditions ?"
#
# B5-littéral et P0_AUTH_ONLY ne partagent pas un mécanisme
# aléatoire commun à faire correspondre 1-pour-1 (B5-littéral tire
# un rejet RFF stochastique message par message ; P0 est
# déterministe sur un contexte statique -- voir la note dans
# p0_auth_only.py). Les graines communes servent donc ici
# uniquement à la reproductibilité de B5-littéral lui-même d'une
# exécution à l'autre, pas à un appariement message-par-message
# avec P0.

import csv
from pathlib import Path

from haenel_comparison.energy_option_a import (
    compute_energy_option_a_mJ,
    validate_option_a,
)
from haenel_comparison.haenel_b5 import (
    simulate_haenel_reference_messages,
    summarize_haenel_events,
)
from haenel_comparison.haenel_config import (
    N_MESSAGES,
    PRIMARY_FRR_CASE,
    SECONDARY_FRR_CASE,
    HAENEL_FRR_CONFIGS,
)
from haenel_comparison.p0_auth_only import (
    simulate_p0_auth_only,
    summarize_p0_auth_only_events,
)

OUTPUT_DIR = Path("results/haenel_comparison")

SEEDS = list(range(9800, 9810))   # 10 graines, comme demandé
                                   # à l'Étape 8 (première passe)


def run_b5_literal_over_seeds(case_name, seeds):
    """Fait tourner B5-littéral sur plusieurs graines pour un cas
    FRR donné, et calcule moyenne/écart-type/IC95% de l'énergie
    Option A et du nombre de replis observés."""

    frr = HAENEL_FRR_CONFIGS[case_name]["frr"]

    per_seed_rows = []

    for seed in seeds:

        events = simulate_haenel_reference_messages(
            frr=frr, n_messages=N_MESSAGES, seed=seed
        )
        summary = summarize_haenel_events(events)

        energy_mJ = compute_energy_option_a_mJ(
            n_fallback=summary["n_fallback_mac"],
            n_rff_direct=summary["n_rff_direct"],
        )

        per_seed_rows.append(
            {
                "case": case_name,
                "seed": seed,
                "n_fallback_mac": summary["n_fallback_mac"],
                "n_rff_direct": summary["n_rff_direct"],
                "observed_fallback_rate": (
                    summary["observed_fallback_rate"]
                ),
                "energy_option_a_mJ": energy_mJ,
            }
        )

    return per_seed_rows


def mean_and_std(values):

    n = len(values)
    mean = sum(values) / n

    if n > 1:
        variance = sum((v - mean) ** 2 for v in values) / (n - 1)
        std = variance ** 0.5
    else:
        std = 0.0

    ci95_half_width = (
        1.96 * std / (n ** 0.5) if n > 1 else 0.0
    )

    return mean, std, ci95_half_width


def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Validation Option A (déterministe, replis = FRR * N_MESSAGES)")
    print("=" * 70)
    for row in validate_option_a():
        print(row)

    print()
    print("=" * 70)
    print(
        f"B5-littéral sur {len(SEEDS)} graines "
        f"({PRIMARY_FRR_CASE} et {SECONDARY_FRR_CASE})"
    )
    print("=" * 70)

    all_b5_rows = []

    for case_name in (PRIMARY_FRR_CASE, SECONDARY_FRR_CASE):

        rows = run_b5_literal_over_seeds(case_name, SEEDS)
        all_b5_rows.extend(rows)

        energies = [row["energy_option_a_mJ"] for row in rows]
        mean_e, std_e, ci95_e = mean_and_std(energies)

        published = HAENEL_FRR_CONFIGS[case_name][
            "published_energy_mJ"
        ]

        print(
            f"\n{case_name}: énergie Option A = "
            f"{mean_e:.3f} +/- {ci95_e:.3f} mJ (IC95%), "
            f"écart-type={std_e:.3f} mJ "
            f"(publié Haenel: {published:.3f} mJ)"
        )

    b5_csv_path = OUTPUT_DIR / "b5_option_a_runs.csv"
    with b5_csv_path.open(
        "w", newline="", encoding="utf-8"
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file, fieldnames=list(all_b5_rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(all_b5_rows)
    print(f"\nCSV brut B5-littéral écrit : {b5_csv_path}")

    print()
    print("=" * 70)
    print("P0_AUTH_ONLY (déterministe, contexte statique)")
    print("=" * 70)

    p0_events = simulate_p0_auth_only(n_messages=N_MESSAGES)
    p0_summary = summarize_p0_auth_only_events(p0_events)

    print(p0_summary)

    p0_csv_path = OUTPUT_DIR / "p0_auth_only_runs.csv"
    with p0_csv_path.open(
        "w", newline="", encoding="utf-8"
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "message_index",
                "chosen_auth",
                "energy_j",
                "normalized_latency",
                "authentication_robustness",
                "refusal_of_service",
            ],
        )
        writer.writeheader()
        for event in p0_events:
            writer.writerow(
                {
                    "message_index": event.message_index,
                    "chosen_auth": event.chosen_auth,
                    "energy_j": event.energy_j,
                    "normalized_latency": event.normalized_latency,
                    "authentication_robustness": (
                        event.authentication_robustness
                    ),
                    "refusal_of_service": (
                        event.refusal_of_service
                    ),
                }
            )
    print(f"CSV brut P0_AUTH_ONLY écrit : {p0_csv_path}")

    print()
    print("=" * 70)
    print("CONSTAT IMPORTANT (à interpréter, pas une erreur)")
    print("=" * 70)
    print(
        "P0_AUTH_ONLY choisit A1 (MAC) pour les "
        f"{p0_summary['n_a1']}/{p0_summary['n_messages']} messages, "
        "jamais A2 (RFF), dans ce contexte statique. Vérifié : les "
        "deux décisions A1-K0 et A2-K0 sont ADMISSIBLES (A2 n'est "
        "pas rejetée par le plancher de FAR) ; A2 a même une "
        "énergie légèrement inférieure. Mais A1 a une robustesse "
        "théorique parfaite (FAR quasi nul, borne cryptographique) "
        "tandis que A2 a un FAR RFF non nul (~8x10^-5 avec le "
        "contexte ASSUMED choisi). Sur ce front de Pareto à 2 "
        "points, les deux décisions obtiennent le MÊME pire écart "
        "normalisé pondéré (Tchebycheff) : c'est le bris d'égalité "
        "du modèle -- FAR croissant en premier critère "
        "(build_tie_break_key, decision_maker.py) -- qui tranche "
        "systématiquement en faveur d'A1. Ce n'est pas un défaut : "
        "c'est le modèle qui, à égalité de compromis, privilégie "
        "la sécurité la plus prouvée. Voir HAENEL_COMPARISON_README.md."
    )

    print()
    print("=" * 70)
    print("LIMITE DE COMPARABILITÉ À NE JAMAIS OMETTRE")
    print("=" * 70)
    print(
        "L'énergie de P0_AUTH_ONLY est calculée avec NOTRE modèle "
        "physique (LoRa/Semtech, energy_latency.py), PAS avec le "
        "matériel MSP430/CC110L de Haenel et al. Les ordres de "
        "grandeur en mJ ne sont donc PAS directement comparables "
        "entre P0_AUTH_ONLY et les valeurs publiées par Haenel et "
        "al. (ou B5-littéral Option A, qui EST calibré sur leurs "
        "chiffres). La comparaison valide ici porte sur le "
        "COMPORTEMENT (quelle action est choisie, pourquoi), pas "
        "sur l'énergie absolue en mJ entre les deux politiques."
    )


if __name__ == "__main__":
    main()
