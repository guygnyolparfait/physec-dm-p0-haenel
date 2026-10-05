# ================================================================
# EXPORT DES DIAGNOSTICS P0_AUTH_ONLY_HAENEL_RFF (CSV + MD)
# ================================================================
#
# Utilise la COMPARAISON PRINCIPALE (A2 reçoit le FAR publié de
# Haenel et al. = 0.002, voir p0_auth_only_haenel_rff.py), corrigée
# le 25/09/2026 -- remplace l'ancienne version qui utilisait le FAR
# natif du modèle de canal physec_dm pour ce document central.

import csv
from pathlib import Path

from physec_dm.decision_maker import (
    build_tie_break_key,
    calculate_ideal_and_nadir_points,
    calculate_pareto_front,
    calculate_tchebycheff_score,
)

from haenel_comparison.haenel_config import HAENEL_FRR_CONFIGS
from haenel_comparison.p0_auth_only import (
    build_haenel_p0_parameters,
    build_haenel_static_context,
)
from haenel_comparison.p0_auth_only_haenel_rff import (
    evaluate_candidates_haenel_rff,
    select_p0_auth_only_haenel_rff,
)

CSV_PATH = Path("results/haenel_comparison/p0_decision_diagnostics.csv")
MD_PATH = Path("results/haenel_comparison/p0_decision_explanation.md")


def collect_diagnostics():

    parameters = build_haenel_p0_parameters()
    context, channel_metrics = build_haenel_static_context(parameters)

    rows = []

    for frr_case in ("HYBRID_FRR_05", "HYBRID_FRR_10"):
        frr = HAENEL_FRR_CONFIGS[frr_case]["frr"]

        all_evaluations = evaluate_candidates_haenel_rff(
            context, parameters, channel_metrics.rho_ab, frr
        )
        admissible = [e for e in all_evaluations if e.admissible]
        pareto_front = calculate_pareto_front(
            admissible, parameters.dominance_tolerance
        )
        pareto_ids = {id(e) for e in pareto_front}
        ideal_point, nadir_point = (
            calculate_ideal_and_nadir_points(pareto_front)
            if pareto_front
            else (None, None)
        )

        selected, _ = select_p0_auth_only_haenel_rff(
            context, parameters, channel_metrics.rho_ab, frr
        )
        decision_name = (
            selected.decision.get_name() if selected else "REFUS"
        )

        for evaluation in all_evaluations:

            row = {
                "frr_case": frr_case,
                "frr": frr,
                "decision": evaluation.decision.get_name(),
                "admissible": evaluation.admissible,
            }

            if evaluation.admissible:
                row["energy_mJ"] = evaluation.cost_metrics.expected_energy_j
                row["latency_neutral"] = (
                    evaluation.cost_metrics.normalized_latency
                )
                row["r_auth"] = (
                    evaluation.authentication_metrics
                    .authentication_robustness
                )
                row["q_key"] = evaluation.key_metrics.key_quality
                row["far"] = evaluation.authentication_metrics.far
                row["on_pareto_front"] = id(evaluation) in pareto_ids

                if id(evaluation) in pareto_ids and ideal_point:
                    score = calculate_tchebycheff_score(
                        objective_vector=evaluation.objective_vector,
                        contextual_weights=parameters.contextual_weights,
                        ideal_point=ideal_point,
                        nadir_point=nadir_point,
                        epsilon=parameters.tchebycheff_epsilon,
                    )
                    row["tchebycheff_score"] = score
                    row["tie_break_key"] = str(
                        build_tie_break_key(evaluation)
                    )
                else:
                    row["tchebycheff_score"] = None
                    row["tie_break_key"] = None
            else:
                row.update({
                    "energy_mJ": None, "latency_neutral": None,
                    "r_auth": None, "q_key": None, "far": None,
                    "on_pareto_front": False,
                    "tchebycheff_score": None, "tie_break_key": None,
                })

            row["final_decision"] = decision_name
            rows.append(row)

    return rows


def write_csv(rows):

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown_explanation(rows):

    a1_row = next(r for r in rows if r["decision"] == "A1-K0"
                  and r["frr_case"] == "HYBRID_FRR_10")
    a2_row = next(r for r in rows if r["decision"] == "A2-K0"
                  and r["frr_case"] == "HYBRID_FRR_10")

    content = f"""# Explication de la décision P0_AUTH_ONLY_HAENEL_RFF (comparaison principale)

## Résultat observé

Pour le cas principal (FRR=10%, A2 reçoit le FAR PUBLIÉ de Haenel
et al. = 0.002 -- voir `p0_auth_only_haenel_rff.py`), avec la
gestion de clé figée à K0, **P0 choisit A1 (MAC cryptographique)**,
pas A2 (RFF), sous poids égaux. Ce même résultat tient aussi pour le
cas de sensibilité FRR=5% (FAR toujours 0.002 par hypothèse
ASSUMED_CONSTANT_FAR_FOR_FRR5_SENSITIVITY, voir
`p0_auth_only_haenel_rff.far_status_for_frr`).

## Les deux candidats sont admissibles

| | A1-K0 (MAC) | A2-K0 (RFF, FAR publié Haenel) |
|---|---|---|
| Admissible | {a1_row['admissible']} | {a2_row['admissible']} |
| Énergie (mJ, échelle Haenel) | {a1_row['energy_mJ']:.5f} | {a2_row['energy_mJ']:.5f} |
| Latence (neutralisée) | {a1_row['latency_neutral']} | {a2_row['latency_neutral']} |
| R_auth | {a1_row['r_auth']:.8f} | {a2_row['r_auth']:.8f} |
| Q_key | {a1_row['q_key']:.6f} | {a2_row['q_key']:.6f} |
| FAR | {a1_row['far']:.8f} | {a2_row['far']:.8f} |
| Sur le front de Pareto | {a1_row['on_pareto_front']} | {a2_row['on_pareto_front']} |
| Score Tchebycheff | {a1_row['tchebycheff_score']:.8f} | {a2_row['tchebycheff_score']:.8f} |
| Clé de tie-break | `{a1_row['tie_break_key']}` | `{a2_row['tie_break_key']}` |

**A2 est nettement moins cher en énergie** ({a2_row['energy_mJ']:.3f} mJ
contre {a1_row['energy_mJ']:.3f} mJ, soit un écart bien plus visible
que sur l'échelle LoRa native), **mais A1 a un FAR bien plus bas**
(borne cryptographique idéalisée, ~{a1_row['far']:.1e}) que A2 (FAR
publié Haenel et al., 0.002).

## Pourquoi le score Tchebycheff est identique pour les deux

C'est une **propriété mathématique générale**, VÉRIFIÉE dans le code
(voir `weight_boundary_sensitivity.py`), pas un artefact de
paramétrage : sur un front de Pareto à exactement 2 points, avec des
poids égaux, chaque candidat est nécessairement au **point idéal**
sur au moins un axe et au **point nadir** sur au moins un autre (sinon
l'un dominerait l'autre et ne serait pas sur le front). Le score de
Tchebycheff prend le MAX des écarts normalisés pondérés : sur l'axe
où un candidat est au nadir, son écart normalisé vaut TOUJOURS 1,0
par construction (la normalisation ramène nadir à 1 et idéal à 0).

Concrètement, dans ce problème réduit à 2 candidats avec latence et
Qkey neutres (identiques) :

    score(A1) = w_energy   (A1 est au nadir sur l'axe énergie)
    score(A2) = w_auth     (A2 est au nadir sur l'axe robustesse)

Sous poids égaux (w_energy = w_auth = 0.25), les deux scores sont
IDENTIQUEMENT 0.25 -- **quelle que soit l'ampleur réelle de l'écart**
sur l'axe où chacun est en tête. C'est pour cela que ni le
changement d'échelle d'énergie, ni la variation du ratio de latence
sur 4 ordres de grandeur (voir réserve méthodologique dans
`latency_sensitivity.py`), ne changent le résultat : la
normalisation absorbe systématiquement la magnitude.

## Pourquoi le tie-break tranche pour A1

Le score étant à égalité stricte, le Decision Maker applique le
bris d'égalité (`build_tie_break_key`, `physec_dm/decision_maker.py`) :
**FAR croissant en premier critère**. A1 a un FAR quasi nul (borne
cryptographique), A2 le FAR publié de Haenel et al. (0.002) --
strictement positif. A1 gagne donc systématiquement le tie-break.

## Ce qui ferait basculer P0 vers A2 -- LA FRONTIÈRE EST FINE

**Corrigé le 25/09/2026** : ne plus dire "il faut donner beaucoup
plus d'importance à l'énergie". Le sweep fin de
`weight_boundary_sensitivity.py` (résultats dans
`weight_boundary_sensitivity.csv`) montre que la frontière est
EXACTEMENT à w_energy = w_auth = 0.25, et qu'un écart de seulement
0.001 (w_energy=0.251 contre w_auth=0.249) suffit à faire basculer
la décision vers A2. Ce n'est pas un résultat qui nécessite un poids
extrême : c'est une frontière immédiatement adjacente au point de
poids égaux.

## Conclusion

Ce n'est ni un bug, ni un résultat arrangé : avec les poids égaux,
A1 et A2 obtiennent une égalité stricte de score, départagée en
faveur d'A1 par le FAR. Cette décision entraîne donc une
consommation d'énergie plus élevée que la stratégie hybride de
Haenel et al. dans ce scénario, mais elle résulte du compromis et de
la règle de départage -- pas de l'inadmissibilité du RFF (les deux
candidats sont admissibles). Une légère modification des préférences
(0.001 sur les poids) peut déplacer la décision vers A2.
"""

    MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    MD_PATH.write_text(content, encoding="utf-8")


if __name__ == "__main__":

    rows = collect_diagnostics()
    write_csv(rows)
    write_markdown_explanation(rows)

    print(f"CSV écrit : {CSV_PATH}")
    print(f"MD écrit : {MD_PATH}")
