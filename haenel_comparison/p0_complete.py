# ================================================================
# PHASE 13 — P0_COMPLETE (EXTENSION / EXPLORATORY SECONDARY
# EXPERIMENT)
# ================================================================
#
# NE PAS CONFONDRE avec la comparaison directe à Haenel et al.
# (Expériences A et B, échelle énergétique calibrée). Ici, le
# Decision Maker complet (A1/A2 x K0/K1a/K1b/K2) tourne SANS
# restriction, en utilisant le VRAI Decision Maker existant
# (run_decision_maker, jamais réécrit), dans le même contexte
# statique inspiré de Haenel et al. Les coûts de K1a/K1b/K2 n'ont
# pas d'équivalent chez Haenel et al. : ils gardent donc leur
# PROPRE modèle physec_dm natif (energy_latency.py, échelle
# LoRa/Semtech) -- PAS l'échelle calibrée Haenel et al., qui ne
# couvre que A1-K0/A2-K0.
#
# Question posée : "Que change l'ajout d'une décision conjointe
# authentification + gestion de clé par rapport à la règle
# RFF->MAC de Haenel et al. ?"

import csv
from pathlib import Path

from physec_dm.decision_maker import run_decision_maker

from haenel_comparison.p0_auth_only import (
    build_haenel_p0_parameters,
    build_haenel_static_context,
)

OUTPUT_PATH = Path("results/haenel_comparison/p0_complete_result.csv")


def run_p0_complete():
    """Fait tourner le Decision Maker COMPLET (8 décisions
    possibles) dans le contexte statique Haenel et al., avec
    renewal_required=True pour donner une chance réelle à K1a/K1b/K2
    d'être pertinents (K0 seul, sans renouvellement requis, serait
    un cas dégénéré où la gestion de clé ne joue aucun rôle)."""

    parameters = build_haenel_p0_parameters()
    context, channel_metrics = build_haenel_static_context(
        parameters, renewal_required=True
    )

    result = run_decision_maker(
        context=context,
        parameters=parameters,
        rho_ab=channel_metrics.rho_ab,
        enforce_far_floor=True,
    )

    return result, channel_metrics


def summarize_result(result, channel_metrics):

    if result.refusal_of_service or result.selected_evaluation is None:
        return {
            "refusal_of_service": True,
            "decision": None,
            "energy_j_native_scale": None,
            "normalized_latency": None,
            "r_auth": None,
            "q_key": None,
            "rho_ab": channel_metrics.rho_ab,
        }

    selected = result.selected_evaluation

    return {
        "refusal_of_service": False,
        "decision": selected.decision.get_name(),
        "energy_j_native_scale": selected.cost_metrics.expected_energy_j,
        "normalized_latency": selected.cost_metrics.normalized_latency,
        "r_auth": selected.authentication_metrics.authentication_robustness,
        "q_key": selected.key_metrics.key_quality,
        "rho_ab": channel_metrics.rho_ab,
        "n_admissible": len(result.admissible_evaluations),
        "n_on_pareto_front": len(result.pareto_front),
    }


if __name__ == "__main__":

    Path("results/haenel_comparison").mkdir(parents=True, exist_ok=True)

    result, channel_metrics = run_p0_complete()
    summary = summarize_result(result, channel_metrics)

    print("P0_COMPLETE -- contexte statique Haenel et al., 8 "
          "décisions possibles, échelle LoRa/Semtech native "
          "(PAS l'échelle Haenel et al.)\n")
    print(summary)
    print(f"\nExplication du Decision Maker : {result.explanation}")

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary.keys()))
        writer.writeheader()
        writer.writerow(summary)

    print(f"\nCSV écrit : {OUTPUT_PATH}")

    print(
        "\nCONSTAT (Phase 13) : comparé à P0_AUTH_ONLY (K0 figé, "
        f"qui choisissait A1), P0_COMPLETE choisit "
        f"{summary['decision']}. "
        + (
            "L'ajout de la gestion de clé conjointe change donc la "
            "décision par rapport à la comparaison directe avec "
            "Haenel et al. -- mais cette comparaison n'est "
            "qu'EXPLORATOIRE : Haenel et al. ne gère aucune clé "
            "physique, donc il n'existe aucune valeur publiée à "
            "laquelle comparer ce résultat."
            if summary["decision"] != "A1-K0"
            else "P0_COMPLETE choisit la même authentification que "
            "P0_AUTH_ONLY (A1) mais peut différer sur l'action de "
            "clé -- résultat à interpréter sans comparaison "
            "possible aux valeurs publiées de Haenel et al., qui ne "
            "couvre pas la gestion de clé physique."
        )
    )
