# ================================================================
# SENSIBILITÉ DE LA DÉCISION P0 AU RATIO DE LATENCE A2/A1
# ================================================================
#
# Haenel et al. ne publie aucune latence par message comparable à
# notre normalized_latency (voir haenel_energy_adapter.py, §2 --
# LATENCY_STATUS = UNAVAILABLE). Plutôt que d'inventer une valeur,
# on fait varier le ratio L_A2/L_A1 sur une plage documentée et on
# cherche la frontière de décision. A2 reçoit le FAR publié de
# Haenel et al. (0.002), cohérent avec la comparaison principale
# (corrigé le 25/09/2026, voir p0_auth_only_haenel_rff.py).
#
# MISE EN GARDE MÉTHODOLOGIQUE (ajoutée le 25/09/2026, relecture) :
# avec seulement deux candidats et une normalisation idéal/nadir
# (voir weight_boundary_sensitivity.py pour la preuve mathématique
# complète), l'écart normalisé sur un axe où un candidat est au
# nadir vaut TOUJOURS exactement 1.0, quelle que soit l'AMPLEUR
# réelle de l'écart physique. Le fait que P0 reste sur A1 pour
# plusieurs ordres de grandeur de ratio de latence est donc en
# partie un EFFET STRUCTUREL de cette normalisation et des poids
# choisis, PAS la preuve que la latence physique réelle n'aurait
# aucun effet sur un système à plus de deux candidats ou avec une
# autre méthode de scalarisation. Cette expérience illustre le
# comportement de la scalarisation dans CE problème réduit à deux
# candidats ; elle ne constitue pas une validation physique de la
# latence.

import csv
from pathlib import Path

from physec_dm.decision_maker import (
    calculate_pareto_front,
    select_from_pareto_front,
)
from physec_dm.models import AuthenticationAction, Decision, KeyAction
from physec_dm.decision_maker import evaluate_decision

from haenel_comparison.haenel_config import HAENEL_FRR_CONFIGS
from haenel_comparison.haenel_energy_adapter import (
    FAR_RFF_HAENEL,
    a1_energy_mJ,
    a2_expected_energy_mJ,
    apply_haenel_rff_far_to_a2,
)
from haenel_comparison.p0_auth_only import (
    build_haenel_p0_parameters,
    build_haenel_static_context,
)

OUTPUT_PATH = Path("results/haenel_comparison/latency_sensitivity.csv")

# Grille de ratios L_A2/L_A1 testée, en fixant L_A1 = 1.0 (unité
# arbitraire cohérente, puisque seule la VALEUR RELATIVE compte
# pour Pareto/Tchebycheff -- pas une vraie mesure de Haenel et al.).
LATENCY_RATIO_GRID = [
    0.01, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 50.0, 100.0
]

L_A1_REFERENCE = 1.0


def select_with_latency_ratio(context, parameters, rho_ab, frr, latency_ratio):
    """Comme select_p0_auth_only_haenel_scale, mais avec une
    latence EXPLICITEMENT non neutre : L(A1)=1.0, L(A2)=ratio."""

    candidates = [
        (Decision(AuthenticationAction.A1, KeyAction.K0),
         a1_energy_mJ(), L_A1_REFERENCE),
        (Decision(AuthenticationAction.A2, KeyAction.K0),
         a2_expected_energy_mJ(frr), latency_ratio * L_A1_REFERENCE),
    ]

    evaluations = []
    for decision, energy_mJ, latency in candidates:
        evaluation = evaluate_decision(
            decision=decision, context=context, parameters=parameters,
            rho_ab=rho_ab, enforce_far_floor=True,
        )
        if evaluation.admissible:
            if decision.authentication_action == AuthenticationAction.A2:
                apply_haenel_rff_far_to_a2(
                    evaluation, parameters, far=FAR_RFF_HAENEL
                )
            evaluation.cost_metrics.expected_energy_j = energy_mJ
            evaluation.cost_metrics.normalized_latency = latency
            evaluation.objective_vector = [
                energy_mJ, latency,
                -evaluation.authentication_metrics.authentication_robustness,
                -evaluation.key_metrics.key_quality,
            ]
        evaluations.append(evaluation)

    admissible = [e for e in evaluations if e.admissible]
    if not admissible:
        return None

    pareto_front = calculate_pareto_front(
        admissible, parameters.dominance_tolerance
    )
    selected, _i, _n, _w = select_from_pareto_front(
        pareto_front=pareto_front,
        contextual_weights=parameters.contextual_weights,
        epsilon=parameters.tchebycheff_epsilon,
        score_tolerance=parameters.score_tolerance,
    )
    return selected


def run_sensitivity():

    parameters = build_haenel_p0_parameters()
    context, channel_metrics = build_haenel_static_context(parameters)

    rows = []

    for frr_case in ("HYBRID_FRR_05", "HYBRID_FRR_10"):
        frr = HAENEL_FRR_CONFIGS[frr_case]["frr"]

        for ratio in LATENCY_RATIO_GRID:
            selected = select_with_latency_ratio(
                context, parameters, channel_metrics.rho_ab, frr, ratio
            )
            rows.append({
                "frr_case": frr_case,
                "frr": frr,
                "latency_ratio_A2_over_A1": ratio,
                "chosen_action": (
                    selected.decision.authentication_action.value
                    if selected else "REFUS"
                ),
            })

    return rows


def find_decision_boundary(rows, frr_case):

    case_rows = sorted(
        (r for r in rows if r["frr_case"] == frr_case),
        key=lambda r: r["latency_ratio_A2_over_A1"],
    )
    actions = [r["chosen_action"] for r in case_rows]

    if len(set(actions)) == 1:
        return None  # pas de changement observé sur la grille testée

    for i in range(1, len(case_rows)):
        if case_rows[i]["chosen_action"] != case_rows[i - 1]["chosen_action"]:
            return (
                case_rows[i - 1]["latency_ratio_A2_over_A1"],
                case_rows[i]["latency_ratio_A2_over_A1"],
            )
    return None


if __name__ == "__main__":

    Path("results/haenel_comparison").mkdir(parents=True, exist_ok=True)
    rows = run_sensitivity()

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV écrit : {OUTPUT_PATH}\n")

    for frr_case in ("HYBRID_FRR_05", "HYBRID_FRR_10"):
        case_rows = [r for r in rows if r["frr_case"] == frr_case]
        actions = set(r["chosen_action"] for r in case_rows)
        print(f"{frr_case}: actions observées sur la grille = {actions}")

        boundary = find_decision_boundary(rows, frr_case)
        if boundary:
            print(f"  Frontière de décision trouvée entre ratio="
                  f"{boundary[0]} et ratio={boundary[1]}")
        else:
            print(
                "  AUCUN changement de décision observé sur la plage "
                f"testée ({min(LATENCY_RATIO_GRID)} à "
                f"{max(LATENCY_RATIO_GRID)}). RÉSERVE MÉTHODOLOGIQUE "
                "(voir en-tête du fichier) : avec seulement deux "
                "candidats, l'écart normalisé sur l'axe latence "
                "reste borné par la normalisation idéal/nadir -- ce "
                "résultat illustre le comportement de la "
                "scalarisation dans ce problème réduit, ce n'est PAS "
                "une preuve que la latence physique n'a aucun effet "
                "en général."
        )
