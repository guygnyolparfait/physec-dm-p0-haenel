# Ce script effectue, en lecture seule, le diagnostic
# demandé sur :
# 1. l'activation de K1a en S3 (recharge-t-on le coût
#    d'une clé candidate déjà prête ?) ;
# 2. l'absence totale de sondages K1b (k1b_measurements_
#    collected=0 dans tous les scénarios).
#
# Il rejoue une mission réelle (S3, graine 2000, 1500
# périodes, via physec_dm.mission.run_mission, déjà
# validé) et EXTRAIT directement les DecisionMakerResult
# déjà calculés à chaque période — aucune ré-évaluation
# approximative, aucune valeur inventée.
#
# Aucun fichier de résultat existant n'est modifié.
# Aucune campagne complète n'est lancée.
import csv
from pathlib import Path

from physec_dm.models import AuthenticationAction, KeyAction

from physec_dm.mission import run_mission

from physec_dm.thesis_scenarios import (
    apply_scenario_overrides_for_validation,
    build_thesis_scenarios,
    build_three_scenario_parameters
)


OUTPUT_DIRECTORY = Path(
    "results/k1_progressive_validation"
)


def get_scenario(scenarios, scenario_id):

    return next(
        scenario
        for scenario in scenarios
        if scenario["scenario_id"] == scenario_id
    )


def format_rejections(evaluation):

    if len(evaluation.rejection_reasons) == 0:

        return ""

    return "; ".join(
        rejection.reason_code
        + " [mesuré="
        + (
            format(rejection.measured_value, ".6g")
            if isinstance(
                rejection.measured_value,
                (int, float)
            )
            else str(rejection.measured_value)
        )
        + ", autorisé="
        + (
            format(rejection.allowed_value, ".6g")
            if isinstance(
                rejection.allowed_value,
                (int, float)
            )
            else str(rejection.allowed_value)
        )
        + "]"
        for rejection in evaluation.rejection_reasons
    )


def k1_stage_label(
    key_action,
    collected,
    required,
    ready
):

    if key_action not in (KeyAction.K1A, KeyAction.K1B):

        return ""

    if ready:

        return (
            (
                "K1a"
                if key_action == KeyAction.K1A
                else "K1b"
            )
            + "_CANDIDATE_READY"
        )

    if collected is not None and collected > 0:

        return (
            (
                "K1a"
                if key_action == KeyAction.K1A
                else "K1b"
            )
            + "_PREPARATION"
        )

    return (
        (
            "K1a"
            if key_action == KeyAction.K1A
            else "K1b"
        )
        + "_PREPARATION"
    )


def extract_decision_rows(
    moment_label,
    step_result
):

    decision_maker_result = (
        step_result.decision_maker_result
    )

    state_before = step_result.state_before

    selected_evaluation = (
        decision_maker_result.selected_evaluation
    )

    pareto_names = set(
        evaluation.decision.get_name()
        for evaluation in (
            decision_maker_result.pareto_front
        )
    )

    rows = []

    for evaluation in (
        decision_maker_result.all_evaluations
    ):

        decision_name = (
            evaluation.decision.get_name()
        )

        key_action = evaluation.decision.key_action

        objective_vector = (
            evaluation.objective_vector
            if evaluation.objective_vector is not None
            else [None, None, None, None]
        )

        stage_label = ""

        if key_action == KeyAction.K1A:

            k1a_is_ready_candidate = (
                state_before.candidate_key_ready
                and state_before.candidate_key_action
                == KeyAction.K1A
            )

            stage_label = k1_stage_label(
                key_action,
                state_before.k1a_measurements_collected,
                (
                    evaluation.key_metrics
                    .required_measurements
                    if evaluation.key_metrics is not None
                    else None
                ),
                k1a_is_ready_candidate
            )

        rows.append(
            {
                "moment": moment_label,
                "step_index": (
                    step_result.state_before.step_index
                ),
                "k1_stage": stage_label,
                "decision_name": decision_name,
                "admissible": evaluation.admissible,
                "rejection_reasons": format_rejections(
                    evaluation
                ),
                "expected_energy_j": (
                    evaluation.cost_metrics
                    .expected_energy_j
                    if evaluation.cost_metrics is not None
                    else None
                ),
                "key_latency_s": (
                    evaluation.cost_metrics.key_latency_s
                    if evaluation.cost_metrics is not None
                    else None
                ),
                "normalized_latency": (
                    evaluation.cost_metrics
                    .normalized_latency
                    if evaluation.cost_metrics is not None
                    else None
                ),
                "authentication_robustness": (
                    evaluation.authentication_metrics
                    .authentication_robustness
                    if evaluation.authentication_metrics
                    is not None
                    else None
                ),
                "key_quality": (
                    evaluation.key_metrics.key_quality
                    if evaluation.key_metrics is not None
                    else None
                ),
                "objective_energy": objective_vector[0],
                "objective_latency": objective_vector[1],
                "objective_auth": objective_vector[2],
                "objective_key": objective_vector[3],
                "on_pareto_front": (
                    decision_name in pareto_names
                ),
                "tchebycheff_score": (
                    evaluation.tchebycheff_score
                ),
                "selected": (
                    selected_evaluation is not None
                    and selected_evaluation.decision
                    .get_name() == decision_name
                ),
                "required_measurements": (
                    evaluation.key_metrics
                    .required_measurements
                    if evaluation.key_metrics is not None
                    else None
                ),
                "collected_measurements": (
                    evaluation.key_metrics
                    .collected_measurements
                    if evaluation.key_metrics is not None
                    else None
                ),
                "remaining_measurements": (
                    evaluation.key_metrics
                    .remaining_measurements
                    if evaluation.key_metrics is not None
                    else None
                )
            }
        )

    return rows


def run_k1a_activation_diagnosis():

    base_parameters = build_three_scenario_parameters()

    scenarios = build_thesis_scenarios(
        parameters=base_parameters,
        max_steps=1500
    )

    scenario = get_scenario(
        scenarios,
        "S3-HIGH-SECURITY-PRESSURE"
    )

    parameters = apply_scenario_overrides_for_validation(
        base_parameters,
        scenario
    )

    mission_options = scenario["mission_options"]

    mission_result = run_mission(
        parameters=parameters,
        seed=2000,
        policy_id="P0-THESIS-CONTEXTUAL-PILOT",
        max_steps=1500,
        initial_duty_cycle_airtime_s=(
            mission_options[
                "initial_duty_cycle_airtime_s"
            ]
        ),
        maximum_duty_cycle_airtime_s=(
            mission_options[
                "maximum_duty_cycle_airtime_s"
            ]
        ),
        duty_cycle_recharge_s=(
            mission_options["duty_cycle_recharge_s"]
        ),
        rff_profile_available=(
            mission_options["rff_profile_available"]
        ),
        variation_feasible=(
            scenario["variation_feasible"]
        ),
        k2_protocol=scenario["k2_protocol"]
    )

    candidate_ready_step = None
    renewal_required_step = None

    for step_result in mission_result.steps:

        if (
            candidate_ready_step is None
            and step_result.candidate_key_ready_after
            and not (
                step_result.candidate_key_ready_before
            )
        ):

            candidate_ready_step = step_result

        if (
            renewal_required_step is None
            and step_result.context.renewal_required
        ):

            renewal_required_step = step_result

        if (
            candidate_ready_step is not None
            and renewal_required_step is not None
        ):

            break

    rows = []

    if candidate_ready_step is not None:

        rows.extend(
            extract_decision_rows(
                "CANDIDATE_READY",
                candidate_ready_step
            )
        )

    if renewal_required_step is not None:

        rows.extend(
            extract_decision_rows(
                "RENEWAL_REQUIRED",
                renewal_required_step
            )
        )

    return {
        "rows": rows,
        "candidate_ready_step": candidate_ready_step,
        "renewal_required_step": renewal_required_step,
        "mission_result": mission_result
    }


def write_csv(rows, output_path):

    field_names = list(rows[0].keys())

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=field_names
        )

        writer.writeheader()
        writer.writerows(rows)


# ================================================================
# DIAGNOSTIC K1b : la préparation doit-elle gagner Tchebycheff
# face à K0/K2 à chaque période pour progresser ?
# ================================================================


def run_k1b_diagnosis():

    base_parameters = build_three_scenario_parameters()

    scenarios = build_thesis_scenarios(
        parameters=base_parameters,
        max_steps=1500
    )

    report_rows = []

    for scenario_id in [
        "S2-RESOURCE-CONSTRAINED",
        "S3-HIGH-SECURITY-PRESSURE"
    ]:

        scenario = get_scenario(scenarios, scenario_id)

        parameters = (
            apply_scenario_overrides_for_validation(
                base_parameters,
                scenario
            )
        )

        mission_options = scenario["mission_options"]

        mission_result = run_mission(
            parameters=parameters,
            seed=2000,
            policy_id="P0-THESIS-CONTEXTUAL-PILOT",
            max_steps=50,
            initial_duty_cycle_airtime_s=(
                mission_options[
                    "initial_duty_cycle_airtime_s"
                ]
            ),
            maximum_duty_cycle_airtime_s=(
                mission_options[
                    "maximum_duty_cycle_airtime_s"
                ]
            ),
            duty_cycle_recharge_s=(
                mission_options[
                    "duty_cycle_recharge_s"
                ]
            ),
            rff_profile_available=(
                mission_options[
                    "rff_profile_available"
                ]
            ),
            variation_feasible=(
                scenario["variation_feasible"]
            ),
            k2_protocol=scenario["k2_protocol"]
        )

        for step_result in mission_result.steps[:10]:

            all_evaluations = (
                step_result.decision_maker_result
                .all_evaluations
            )

            k0_evaluation = next(
                (
                    evaluation
                    for evaluation in all_evaluations
                    if evaluation.decision.key_action
                    == KeyAction.K0
                    and evaluation.decision
                    .authentication_action
                    == AuthenticationAction.A1
                ),
                None
            )

            k1b_evaluation = next(
                (
                    evaluation
                    for evaluation in all_evaluations
                    if evaluation.decision.key_action
                    == KeyAction.K1B
                    and evaluation.decision
                    .authentication_action
                    == AuthenticationAction.A1
                ),
                None
            )

            if (
                k0_evaluation is None
                or k1b_evaluation is None
            ):

                continue

            report_rows.append(
                {
                    "scenario_id": scenario_id,
                    "step_index": (
                        step_result.state_before
                        .step_index
                    ),
                    "k1b_admissible": (
                        k1b_evaluation.admissible
                    ),
                    "k1b_rejections": format_rejections(
                        k1b_evaluation
                    ),
                    "k1b_energy_objective": (
                        k1b_evaluation.objective_vector[0]
                        if k1b_evaluation
                        .objective_vector is not None
                        else None
                    ),
                    "k0_energy_objective": (
                        k0_evaluation.objective_vector[0]
                        if k0_evaluation
                        .objective_vector is not None
                        else None
                    ),
                    "k1b_key_objective": (
                        k1b_evaluation.objective_vector[3]
                        if k1b_evaluation
                        .objective_vector is not None
                        else None
                    ),
                    "k0_key_objective": (
                        k0_evaluation.objective_vector[3]
                        if k0_evaluation
                        .objective_vector is not None
                        else None
                    ),
                    "k1b_on_pareto_front": (
                        k1b_evaluation in (
                            step_result
                            .decision_maker_result
                            .pareto_front
                        )
                    ),
                    "k1b_tchebycheff_score": (
                        k1b_evaluation.tchebycheff_score
                    ),
                    "k0_tchebycheff_score": (
                        k0_evaluation.tchebycheff_score
                    ),
                    "selected": (
                        step_result
                        .decision_maker_result
                        .selected_evaluation
                        .decision.get_name()
                        if step_result
                        .decision_maker_result
                        .selected_evaluation is not None
                        else "REFUS"
                    )
                }
            )

        return report_rows

    return report_rows


if __name__ == "__main__":

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )

    print(
        "=== Diagnostic activation K1a (S3, graine 2000, "
        "1500 périodes) ==="
    )

    activation_diagnosis = (
        run_k1a_activation_diagnosis()
    )

    if len(activation_diagnosis["rows"]) > 0:

        write_csv(
            activation_diagnosis["rows"],
            OUTPUT_DIRECTORY
            / "k1a_activation_decision_audit.csv"
        )

        print(
            "Fichier écrit : "
            + str(
                OUTPUT_DIRECTORY
                / "k1a_activation_decision_audit.csv"
            )
        )

    if activation_diagnosis["candidate_ready_step"]:

        step = activation_diagnosis[
            "candidate_ready_step"
        ]

        print(
            "Instant CANDIDATE_READY : étape "
            + str(step.state_before.step_index)
            + " — décision sélectionnée : "
            + (
                step.decision_maker_result
                .selected_evaluation.decision
                .get_name()
                if step.decision_maker_result
                .selected_evaluation is not None
                else "REFUS"
            )
        )

    if activation_diagnosis["renewal_required_step"]:

        step = activation_diagnosis[
            "renewal_required_step"
        ]

        print(
            "Instant RENEWAL_REQUIRED : étape "
            + str(step.state_before.step_index)
            + " — décision sélectionnée : "
            + (
                step.decision_maker_result
                .selected_evaluation.decision
                .get_name()
                if step.decision_maker_result
                .selected_evaluation is not None
                else "REFUS"
            )
        )

        selected_evaluation = (
            step.decision_maker_result
            .selected_evaluation
        )

        k1a_evaluation = next(
            (
                evaluation
                for evaluation in (
                    step.decision_maker_result
                    .all_evaluations
                )
                if evaluation.decision.key_action
                == KeyAction.K1A
            ),
            None
        )

        if k1a_evaluation is not None:

            print(
                "  K1a à cet instant : admissible="
                + str(k1a_evaluation.admissible)
                + " required="
                + str(
                    k1a_evaluation.key_metrics
                    .required_measurements
                )
                + " collected="
                + str(
                    k1a_evaluation.key_metrics
                    .collected_measurements
                )
                + " remaining="
                + str(
                    k1a_evaluation.key_metrics
                    .remaining_measurements
                )
                + " key_latency_s="
                + format(
                    k1a_evaluation.cost_metrics
                    .key_latency_s,
                    ".4f"
                )
                + " key_quality="
                + format(
                    k1a_evaluation.key_metrics
                    .key_quality,
                    ".4f"
                )
                + " tchebycheff="
                + (
                    format(
                        k1a_evaluation.tchebycheff_score,
                        ".6f"
                    )
                    if k1a_evaluation.tchebycheff_score
                    is not None
                    else "None (hors front)"
                )
            )

    print("")
    print(
        "=== Diagnostic K1b (S2/S3, graine 2000, "
        "50 premières périodes) ==="
    )

    k1b_rows = run_k1b_diagnosis()

    for row in k1b_rows[:10]:

        print(row)
