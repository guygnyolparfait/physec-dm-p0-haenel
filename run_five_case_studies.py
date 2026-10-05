# Ce script orchestre les cinq cas d'étude dynamiques
# (physec_dm/case_studies.py) sous les deux politiques
# P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS (Decision Maker complet) et B1-CONVENTIONAL
# (baseline), avec des traces aléatoires communes par graine
# (physec_dm/scenario_controller.py), et journalise chaque
# période dans un fichier CSV.
#
# Il ne modifie et ne recalcule AUCUNE équation scientifique :
# il appelle uniquement physec_dm.mission.run_mission (déjà
# validé), étendu de façon rétrocompatible pour recevoir les
# traces du contrôleur de scénario et la politique de décision
# à utiliser.
import csv
import sys
from pathlib import Path

from physec_dm.case_studies import (
    apply_case_study_overrides,
    build_case_study_base_parameters,
    build_five_case_studies,
    select_b2_naive_physec_decision,
    select_b3_hybrid_fixed_decision,
    select_b4_decision_maker_no_far_floor,
    select_baseline_conventional_decision
)

from physec_dm.contextual_policy import (
    resolve_contextual_weights
)

from physec_dm.mission import (
    find_key_metrics_for_action,
    run_mission
)

from physec_dm.models import KeyAction

from physec_dm.scenario_controller import ScenarioController

from physec_dm.thesis_scenarios import build_thesis_seeds


POLICIES = [
    {
        "policy_id": "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS",
        "decision_policy_fn": None
    },
    {
        "policy_id": "B1-CONVENTIONAL",
        "decision_policy_fn": (
            select_baseline_conventional_decision
        )
    },
    {
        "policy_id": "B2-NAIVE-PHYSEC-NO-FLOOR",
        "decision_policy_fn": (
            select_b2_naive_physec_decision
        )
    },
    {
        "policy_id": "B3-HYBRID-FIXED",
        "decision_policy_fn": (
            select_b3_hybrid_fixed_decision
        )
    },
    {
        "policy_id": "B4-DM-NO-FAR-FLOOR",
        "decision_policy_fn": (
            select_b4_decision_maker_no_far_floor
        )
    }
]


LOG_FIELD_NAMES = [
    "scenario_id",
    "phase_name",
    "policy_id",
    "seed",
    "step_index",
    "battery_energy_j",
    "snr_db",
    "effective_speed_m_s",
    "doppler_hz",
    "rho_time",
    "rho_ab",
    "effective_kdr",
    "criticality",
    "mallory_attempted",
    "compromise_suspected",
    "remaining_duty_cycle_airtime_s",
    "key_age_s",
    "messages_with_current_key",
    "k1a_measurements_collected",
    "k1b_measurements_collected",
    "candidate_key_ready",
    "candidate_key_action",
    "selected_decision",
    "energy_objective_j",
    "latency_objective",
    "authentication_robustness",
    "key_quality",
    "admissible_decision_count",
    "pareto_front_size",
    "legitimate_message_served",
    "security_floor_violation",
    "mallory_accepted"
]


# ================================================================
# 1. TRACES D'UN COUPLE (CAS D'ÉTUDE, GRAINE)
# ================================================================
#
# Les mêmes traces (mêmes réalisations aléatoires exogènes) sont
# utilisées pour P0 et B1 : seule la politique de décision
# diffère entre les deux appels de run_mission.
def build_scenario_traces(
    case_study,
    seed,
    max_steps
):

    controller = ScenarioController(
        case_study=case_study,
        seed=seed,
        max_steps=max_steps
    )

    conditions = [
        controller.resolve_period_conditions(step_index)
        for step_index in range(max_steps)
    ]

    return {
        "conditions": conditions,
        "observed_snr_trace": [
            condition["observed_snr_db"]
            for condition in conditions
        ],
        "real_snr_trace": [
            condition["real_snr_db"]
            for condition in conditions
        ],
        "criticality_trace": [
            condition["criticality"]
            for condition in conditions
        ],
        "mallory_trace": [
            condition["mallory_attempted"]
            for condition in conditions
        ],
        "compromise_trace": [
            condition["compromise_suspected"]
            for condition in conditions
        ],
        "speed_trace": [
            condition["effective_speed_m_s"]
            for condition in conditions
        ]
    }


# ================================================================
# 2. EXÉCUTION D'UNE MISSION ET EXTRACTION DU JOURNAL
# ================================================================


def run_single_mission(
    case_study,
    scenario_parameters,
    policy_id,
    decision_policy_fn,
    seed,
    max_steps,
    traces
):

    mission_result = run_mission(
        parameters=scenario_parameters,
        seed=seed,
        policy_id=policy_id,
        max_steps=max_steps,
        # Convention déjà validée dans
        # physec_dm/thesis_scenarios.py
        # (common_mission_options) : 1 % de duty-cycle
        # PAR HEURE, soit 36 s de budget maximal
        # rechargés de 0,6 s par période de 60 s. Sans
        # ces trois arguments explicites, run_mission
        # retombe sur son propre défaut PAR PÉRIODE
        # (derived_period_budget_s = duty_cycle_fraction
        # * message_period_s = 0,6 s), un budget bien
        # trop faible qui bloquerait artificiellement K2
        # et A2 par DUTY_CYCLE_CONSTRAINT — non pas un
        # résultat scientifique, mais un budget mal
        # dimensionné.
        initial_duty_cycle_airtime_s=36.0,
        maximum_duty_cycle_airtime_s=36.0,
        duty_cycle_recharge_s=0.6,
        variation_feasible=(
            case_study["variation_feasible"]
        ),
        k2_protocol=case_study["k2_protocol"],
        observed_snr_trace=(
            traces["observed_snr_trace"]
        ),
        real_snr_trace=traces["real_snr_trace"],
        criticality_trace=(
            traces["criticality_trace"]
        ),
        mallory_trace=traces["mallory_trace"],
        compromise_trace=(
            traces["compromise_trace"]
        ),
        speed_trace=traces["speed_trace"],
        decision_policy_fn=decision_policy_fn,
        contextual_weights_resolver_fn=(
            resolve_contextual_weights
        )
    )

    return mission_result


def extract_log_rows(
    case_study,
    policy_id,
    seed,
    mission_result,
    conditions
):

    rows = []

    for step_result in mission_result.steps:

        step_index = (
            step_result.state_before.step_index
        )

        condition = conditions[step_index]

        decision_maker_result = (
            step_result.decision_maker_result
        )

        selected_evaluation = (
            decision_maker_result.selected_evaluation
        )

        k1a_key_metrics = find_key_metrics_for_action(
            decision_maker_result.all_evaluations,
            KeyAction.K1A
        )

        effective_kdr = (
            k1a_key_metrics.effective_kdr
            if k1a_key_metrics is not None
            else None
        )

        selected_decision_name = (
            selected_evaluation.decision.get_name()
            if selected_evaluation is not None
            else "REFUS"
        )

        objective_vector = (
            selected_evaluation.objective_vector
            if selected_evaluation is not None
            else None
        )

        energy_objective_j = (
            objective_vector[0]
            if objective_vector is not None
            else None
        )

        latency_objective = (
            objective_vector[1]
            if objective_vector is not None
            else None
        )

        authentication_robustness = (
            selected_evaluation
            .authentication_metrics
            .authentication_robustness
            if selected_evaluation is not None
            else None
        )

        key_quality = (
            selected_evaluation.key_metrics.key_quality
            if selected_evaluation is not None
            else None
        )

        security_floor_violation = (
            step_result.state_after
            .security_floor_violations
            > step_result.state_before
            .security_floor_violations
        )

        candidate_key_action_value = (
            step_result.candidate_key_action.value
            if step_result.candidate_key_action
            is not None
            else ""
        )

        rows.append(
            {
                "scenario_id": (
                    case_study["scenario_id"]
                ),
                "phase_name": condition["phase_name"],
                "policy_id": policy_id,
                "seed": seed,
                "step_index": step_index,
                "battery_energy_j": (
                    step_result.state_after
                    .battery_energy_j
                ),
                "snr_db": step_result.context.snr_db,
                "effective_speed_m_s": (
                    condition["effective_speed_m_s"]
                ),
                "doppler_hz": (
                    step_result.channel_metrics
                    .doppler_hz
                ),
                "rho_time": (
                    step_result.channel_metrics
                    .temporal_correlation
                ),
                "rho_ab": (
                    step_result.channel_metrics.rho_ab
                ),
                "effective_kdr": effective_kdr,
                "criticality": (
                    step_result.context.criticality
                ),
                "mallory_attempted": (
                    step_result.mallory_attempted
                ),
                "compromise_suspected": (
                    step_result.context
                    .compromise_suspected
                ),
                "remaining_duty_cycle_airtime_s": (
                    step_result.state_after
                    .remaining_duty_cycle_airtime_s
                ),
                "key_age_s": (
                    step_result.state_after.key_age_s
                ),
                "messages_with_current_key": (
                    step_result.state_after
                    .messages_with_current_key
                ),
                "k1a_measurements_collected": (
                    step_result.k1a_measurements_after
                ),
                "k1b_measurements_collected": (
                    step_result.k1b_measurements_after
                ),
                "candidate_key_ready": (
                    step_result.candidate_key_ready_after
                ),
                "candidate_key_action": (
                    candidate_key_action_value
                ),
                "selected_decision": (
                    selected_decision_name
                ),
                "energy_objective_j": (
                    energy_objective_j
                ),
                "latency_objective": (
                    latency_objective
                ),
                "authentication_robustness": (
                    authentication_robustness
                ),
                "key_quality": key_quality,
                "admissible_decision_count": len(
                    decision_maker_result
                    .admissible_evaluations
                ),
                "pareto_front_size": len(
                    decision_maker_result.pareto_front
                ),
                "legitimate_message_served": (
                    step_result.legitimate_message_served
                ),
                "security_floor_violation": (
                    security_floor_violation
                ),
                "mallory_accepted": (
                    step_result.mallory_accepted
                )
            }
        )

    return rows


# ================================================================
# 3. CAMPAGNE (COURTE, INTERMÉDIAIRE OU COMPLÈTE)
# ================================================================


def run_campaign(
    seeds,
    max_steps,
    output_directory,
    label
):

    output_path = Path(
        output_directory
    )

    output_path.mkdir(
        parents=True,
        exist_ok=True
    )

    print(
        "Lancement de la campagne "
        + label
        + " des cinq cas d'étude."
    )
    print(
        "Les valeurs de cette campagne ne sont pas "
        "encore des résultats scientifiques finaux."
    )

    base_parameters = (
        build_case_study_base_parameters()
    )

    case_studies = build_five_case_studies()

    all_rows = []

    for case_study in case_studies:

        scenario_parameters = (
            apply_case_study_overrides(
                base_parameters,
                case_study
            )
        )

        for seed in seeds:

            traces = build_scenario_traces(
                case_study,
                seed,
                max_steps
            )

            for policy in POLICIES:

                mission_result = run_single_mission(
                    case_study=case_study,
                    scenario_parameters=(
                        scenario_parameters
                    ),
                    policy_id=policy["policy_id"],
                    decision_policy_fn=(
                        policy["decision_policy_fn"]
                    ),
                    seed=seed,
                    max_steps=max_steps,
                    traces=traces
                )

                all_rows.extend(
                    extract_log_rows(
                        case_study=case_study,
                        policy_id=policy["policy_id"],
                        seed=seed,
                        mission_result=mission_result,
                        conditions=(
                            traces["conditions"]
                        )
                    )
                )

    log_path = (
        output_path / "five_case_studies_log.csv"
    )

    with log_path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=LOG_FIELD_NAMES
        )

        writer.writeheader()
        writer.writerows(all_rows)

    print(
        "Journal écrit : "
        + str(log_path)
        + " ("
        + str(len(all_rows))
        + " lignes)."
    )

    return all_rows


if __name__ == "__main__":

    mode = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "short"
    )

    if mode == "short":

        run_campaign(
            seeds=build_thesis_seeds(
                count=1
            ),
            max_steps=200,
            output_directory=(
                "results/five_case_studies_validation"
            ),
            label="COURTE (1 graine, 200 périodes)"
        )

    elif mode == "intermediate":

        run_campaign(
            seeds=build_thesis_seeds(
                count=3
            ),
            max_steps=1500,
            output_directory=(
                "results/five_case_studies_validation"
            ),
            label=(
                "INTERMÉDIAIRE (3 graines, 1500 "
                "périodes)"
            )
        )

    elif mode == "full":

        run_campaign(
            seeds=build_thesis_seeds(
                count=30
            ),
            max_steps=1500,
            output_directory=(
                "results/five_case_studies_final"
            ),
            label=(
                "COMPLÈTE (30 graines, 1500 périodes) — "
                "NE DOIT ÊTRE LANCÉE QU'APRÈS "
                "CONFIRMATION EXPLICITE"
            )
        )

    else:

        raise ValueError(
            "Mode inconnu : "
            + mode
            + " (utiliser 'short', 'intermediate' ou "
            "'full')."
        )
