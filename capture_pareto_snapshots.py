# Ce script capture, pour chacun des cinq cas d'étude, les
# évaluations COMPLÈTES des huit décisions (admissibilité,
# motifs de rejet, objectifs, front de Pareto, décision
# sélectionnée) à trois périodes représentatives (avant /
# pendant / après l'événement principal du scénario), pour
# P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS et B1-CONVENTIONAL.
#
# Le journal CSV de run_five_case_studies.py ne conserve pas
# les vecteurs d'objectifs des décisions NON sélectionnées ;
# cette information ne peut donc être obtenue qu'en conservant
# les objets DecisionMakerResult produits par une mission déjà
# exécutée. Ce script réutilise directement
# physec_dm.mission.run_mission (déjà validé) et les fonctions
# d'assemblage de run_five_case_studies.py — il ne recalcule et
# ne modifie AUCUNE équation, AUCUN scénario et AUCUN poids.
#
# Une seule graine (la première graine commune, 2000) est
# utilisée : ces instantanés servent à illustrer le mécanisme
# de décision à des instants précis, pas à produire une
# statistique — les statistiques (moyennes, IC 95 %) utilisent
# déjà les 30 graines complètes via le journal CSV.
import json
from pathlib import Path

from physec_dm.case_studies import (
    apply_case_study_overrides,
    build_case_study_base_parameters,
    build_five_case_studies,
    select_baseline_conventional_decision
)

from run_five_case_studies import (
    build_scenario_traces,
    run_single_mission
)


REPRESENTATIVE_SEED = 2000
MAX_STEPS = 1500

OUTPUT_PATH = Path(
    "results/five_case_studies_final/"
    "pareto_snapshots.json"
)

POLICIES = [
    ("P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS", None),
    (
        "B1-CONVENTIONAL",
        select_baseline_conventional_decision
    )
]

# Périodes représentatives (fractions de max_steps),
# choisies à partir des phases/événements réels de chaque
# scénario (physec_dm/case_studies.py) : avant / pendant /
# après l'événement principal.
REPRESENTATIVE_PERIODS = {
    "S1-REMOTE-AGRICULTURAL-SENSOR": [
        (0.10, "Régime établi (début)"),
        (0.50, "Régime établi (milieu)"),
        (0.90, "Régime établi (fin)")
    ],
    "S2-INDUSTRIAL-CRITICAL-ALARM": [
        (0.35, "Avant l'alarme"),
        (0.45, "Pendant l'alarme"),
        (0.75, "Après retour à la normale")
    ],
    "S3-MOBILE-VEHICLE": [
        (0.10, "Véhicule à l'arrêt (avant)"),
        (0.50, "Vitesse maximale du scénario"),
        (0.90, "Véhicule à l'arrêt (après)")
    ],
    "S4-DENSE-URBAN-NETWORK": [
        (0.15, "Avant la congestion"),
        (0.32, "Pendant la congestion (1)"),
        (0.50, "Après retour à la normale")
    ],
    "S5-CRITICAL-INFRASTRUCTURE-ATTACK": [
        (0.15, "Avant l'attaque"),
        (0.45, "Pendant l'attaque (compromission)"),
        (0.80, "Après réaction/retour à la normale")
    ]
}


def format_rejections(evaluation):

    if len(evaluation.rejection_reasons) == 0:

        return ""

    return "; ".join(
        rejection.reason_code
        for rejection in evaluation.rejection_reasons
    )


def extract_period_snapshot(
    step_result,
    label
):

    decision_maker_result = (
        step_result.decision_maker_result
    )

    pareto_names = set(
        evaluation.decision.get_name()
        for evaluation in (
            decision_maker_result.pareto_front
        )
    )

    selected_evaluation = (
        decision_maker_result.selected_evaluation
    )

    evaluations = []

    for evaluation in (
        decision_maker_result.all_evaluations
    ):

        objective_vector = (
            evaluation.objective_vector
        )

        evaluations.append(
            {
                "decision_name": (
                    evaluation.decision.get_name()
                ),
                "admissible": evaluation.admissible,
                "rejection_reasons": (
                    format_rejections(evaluation)
                ),
                "energy": (
                    objective_vector[0]
                    if objective_vector is not None
                    else None
                ),
                "latency": (
                    objective_vector[1]
                    if objective_vector is not None
                    else None
                ),
                "authentication": (
                    evaluation.authentication_metrics
                    .authentication_robustness
                    if evaluation
                    .authentication_metrics
                    is not None
                    else None
                ),
                "key_quality": (
                    evaluation.key_metrics.key_quality
                    if evaluation.key_metrics
                    is not None
                    else None
                ),
                "on_pareto_front": (
                    evaluation.decision.get_name()
                    in pareto_names
                )
            }
        )

    return {
        "step_index": (
            step_result.state_before.step_index
        ),
        "label": label,
        "policies": {
            "__CURRENT__": {
                "evaluations": evaluations,
                "selected_decision_name": (
                    selected_evaluation.decision
                    .get_name()
                    if selected_evaluation
                    is not None
                    else None
                )
            }
        }
    }


def capture_scenario_snapshots(case_study):

    base_parameters = (
        build_case_study_base_parameters()
    )

    scenario_parameters = (
        apply_case_study_overrides(
            base_parameters,
            case_study
        )
    )

    traces = build_scenario_traces(
        case_study,
        seed=REPRESENTATIVE_SEED,
        max_steps=MAX_STEPS
    )

    target_steps = [
        (
            round(fraction * MAX_STEPS),
            label
        )
        for fraction, label in (
            REPRESENTATIVE_PERIODS[
                case_study["scenario_id"]
            ]
        )
    ]

    periods = [
        {
            "step_index": step_index,
            "label": label,
            "policies": {}
        }
        for step_index, label in target_steps
    ]

    for policy_id, decision_fn in POLICIES:

        mission_result = run_single_mission(
            case_study=case_study,
            scenario_parameters=(
                scenario_parameters
            ),
            policy_id=policy_id,
            decision_policy_fn=decision_fn,
            seed=REPRESENTATIVE_SEED,
            max_steps=MAX_STEPS,
            traces=traces
        )

        steps_by_index = {
            step_result.state_before.step_index:
                step_result
            for step_result in mission_result.steps
        }

        for period in periods:

            step_result = steps_by_index.get(
                period["step_index"]
            )

            if step_result is None:

                continue

            snapshot = extract_period_snapshot(
                step_result,
                period["label"]
            )

            period["policies"][policy_id] = (
                snapshot["policies"]["__CURRENT__"]
            )

    return {"periods": periods}


def capture_all_snapshots():

    case_studies = build_five_case_studies()

    all_snapshots = {}

    for case_study in case_studies:

        print(
            "Capture des instantanés Pareto pour "
            + case_study["scenario_id"]
            + "..."
        )

        all_snapshots[
            case_study["scenario_id"]
        ] = capture_scenario_snapshots(
            case_study
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8"
    ) as json_file:

        json.dump(
            all_snapshots,
            json_file,
            indent=2
        )

    print(
        "Instantanés écrits : "
        + str(OUTPUT_PATH)
    )

    return all_snapshots


if __name__ == "__main__":

    capture_all_snapshots()
