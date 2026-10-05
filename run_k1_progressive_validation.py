# Ce script exécute une validation progressive de la
# correction K1a/K1b décrite dans :
# results/three_scenarios_explicit_analysis/
# k1a_k1b_model_consistency_audit.md
#
# Il utilise directement physec_dm.mission.run_mission
# (déjà validé) sur les trois scénarios réels de la thèse
# (thesis_scenarios.py, cryptopériode nominale restaurée),
# à une échelle réduite (peu de graines, peu de périodes),
# afin de vérifier — AVANT toute campagne complète de 90
# missions — que :
#
# - les compteurs K1a/K1b progressent ;
# - aucune activation prématurée ne se produit ;
# - S1 reste PHY-inadmissible pour K1a/K1b ;
# - S2/S3 accumulent des mesures ;
# - le duty-cycle de K1b est respecté.
import csv
import sys
from pathlib import Path

from physec_dm.models import KeyAction

from physec_dm.mission import run_mission

from physec_dm.thesis_scenarios import (
    apply_scenario_overrides_for_validation,
    build_thesis_scenarios,
    build_three_scenario_parameters
)


OUTPUT_DIRECTORY = Path(
    "results/k1_progressive_validation"
)

SCENARIO_ORDER = [
    "S1-DEGRADED-CHANNEL",
    "S2-RESOURCE-CONSTRAINED",
    "S3-HIGH-SECURITY-PRESSURE"
]


# ================================================================
# 1. EXÉCUTION DES MISSIONS ET COLLECTE PAR PÉRIODE
# ================================================================


def run_scenario_missions(
    scenario,
    scenario_parameters,
    seeds,
    max_steps
):

    mission_options = scenario["mission_options"]

    missions = []

    for seed in seeds:

        mission_result = run_mission(
            parameters=scenario_parameters,
            seed=seed,
            policy_id="P0-THESIS-CONTEXTUAL-PILOT",
            max_steps=max_steps,
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

        missions.append(
            {
                "seed": seed,
                "mission_result": mission_result
            }
        )

    return missions


# ================================================================
# 2. EXTRACTION DES LIGNES DE PROGRESSION PAR PÉRIODE
# ================================================================


def extract_progression_rows(
    scenario_id,
    seed,
    mission_result
):

    rows = []

    for step_result in mission_result.steps:

        selected_evaluation = (
            step_result
            .decision_maker_result
            .selected_evaluation
        )

        selected_decision_name = (
            selected_evaluation.decision.get_name()
            if selected_evaluation is not None
            else "REFUS"
        )

        rows.append(
            {
                "scenario_id": scenario_id,
                "seed": seed,
                "step_index": (
                    step_result.state_before.step_index
                ),
                "renewal_required": (
                    step_result.context.renewal_required
                ),
                "legitimate_message_served": (
                    step_result
                    .legitimate_message_served
                ),
                "selected_decision": (
                    selected_decision_name
                ),
                "k1a_measurements_before": (
                    step_result.k1a_measurements_before
                ),
                "k1a_measurements_after": (
                    step_result.k1a_measurements_after
                ),
                "k1b_measurements_before": (
                    step_result.k1b_measurements_before
                ),
                "k1b_measurements_after": (
                    step_result.k1b_measurements_after
                ),
                "candidate_key_ready_before": (
                    step_result
                    .candidate_key_ready_before
                ),
                "candidate_key_ready_after": (
                    step_result
                    .candidate_key_ready_after
                ),
                "candidate_key_action": (
                    step_result.candidate_key_action.value
                    if step_result.candidate_key_action
                    is not None
                    else ""
                ),
                "key_age_s_after": (
                    step_result.state_after.key_age_s
                ),
                "remaining_duty_cycle_airtime_s_after": (
                    step_result.state_after
                    .remaining_duty_cycle_airtime_s
                )
            }
        )

    return rows


# ================================================================
# 3. DÉTECTION DES ÉVÉNEMENTS DE CLÉ CANDIDATE
# ================================================================


def extract_candidate_key_events(
    scenario_id,
    seed,
    mission_result
):

    events = []

    for step_result in mission_result.steps:

        step_index = (
            step_result.state_before.step_index
        )

        # Événement 1 : une clé candidate devient prête.
        if (
            not step_result.candidate_key_ready_before
            and step_result.candidate_key_ready_after
        ):

            events.append(
                {
                    "scenario_id": scenario_id,
                    "seed": seed,
                    "step_index": step_index,
                    "event": "CANDIDATE_READY",
                    "candidate_key_action": (
                        step_result
                        .candidate_key_action.value
                        if step_result
                        .candidate_key_action is not None
                        else ""
                    )
                }
            )

        # Événement 2 : une clé (K1a, K1b ou K2) est activée.
        #
        # Une activation se reconnaît à la remise à zéro de
        # key_age_s alors que la période précédente avait un
        # âge non nul, ou à un changement d'identifiant.
        activated = (
            step_result.state_after.key_age_s == 0.0
            and step_result.state_before.key_age_s != 0.0
        )

        if activated:

            selected_evaluation = (
                step_result
                .decision_maker_result
                .selected_evaluation
            )

            activated_action = (
                selected_evaluation.decision
                .key_action.value
                if selected_evaluation is not None
                else "INCONNU"
            )

            events.append(
                {
                    "scenario_id": scenario_id,
                    "seed": seed,
                    "step_index": step_index,
                    "event": (
                        "KEY_ACTIVATED_"
                        + activated_action.upper()
                    ),
                    "candidate_key_action": (
                        activated_action
                    )
                }
            )

    return events


# ================================================================
# 4. MOTIFS DE REJET DE K1a / K1b
# ================================================================


def extract_rejection_reasons(
    scenario_id,
    seed,
    mission_result
):

    tally = {}

    for step_result in mission_result.steps:

        for evaluation in (
            step_result.decision_maker_result
            .all_evaluations
        ):

            if evaluation.decision.key_action not in (
                KeyAction.K1A,
                KeyAction.K1B
            ):

                continue

            key_action_name = (
                evaluation.decision.key_action.value
            )

            if evaluation.admissible:

                reason_key = (
                    key_action_name,
                    "ADMISSIBLE"
                )

                tally[reason_key] = (
                    tally.get(reason_key, 0) + 1
                )

                continue

            if len(evaluation.rejection_reasons) == 0:

                reason_key = (
                    key_action_name,
                    "AUCUN_MOTIF_ENREGISTRE"
                )

                tally[reason_key] = (
                    tally.get(reason_key, 0) + 1
                )

                continue

            for rejection in (
                evaluation.rejection_reasons
            ):

                reason_key = (
                    key_action_name,
                    rejection.reason_code
                )

                tally[reason_key] = (
                    tally.get(reason_key, 0) + 1
                )

    rows = []

    for (
        key_action_name,
        reason_code
    ), count in sorted(
        tally.items()
    ):

        rows.append(
            {
                "scenario_id": scenario_id,
                "seed": seed,
                "key_action": key_action_name,
                "reason_code": reason_code,
                "occurrence_count": count
            }
        )

    return rows


# ================================================================
# 5. RÉSUMÉ PAR SCÉNARIO
# ================================================================


def summarize_scenario(
    scenario_id,
    scenario_parameters,
    missions,
    progression_rows,
    events_rows
):

    total_k1a_preparations = sum(
        1
        for row in progression_rows
        if row["k1a_measurements_after"]
        > row["k1a_measurements_before"]
    )

    total_k1b_probes = sum(
        1
        for row in progression_rows
        if row["k1b_measurements_after"]
        > row["k1b_measurements_before"]
    )

    candidate_ready_events = sum(
        1
        for event in events_rows
        if event["event"] == "CANDIDATE_READY"
    )

    k1a_activations = sum(
        1
        for event in events_rows
        if event["event"] == "KEY_ACTIVATED_K1A"
    )

    k1b_activations = sum(
        1
        for event in events_rows
        if event["event"] == "KEY_ACTIVATED_K1B"
    )

    duty_cycle_min_remaining = min(
        (
            row[
                "remaining_duty_cycle_airtime_s_after"
            ]
            for row in progression_rows
        ),
        default=None
    )

    duty_cycle_respected = (
        duty_cycle_min_remaining is not None
        and duty_cycle_min_remaining >= 0.0
    )

    final_k1a_collected = max(
        (
            row["k1a_measurements_after"]
            for row in progression_rows
        ),
        default=0
    )

    final_k1b_collected = max(
        (
            row["k1b_measurements_after"]
            for row in progression_rows
        ),
        default=0
    )

    # N_required est estimé au SNR moyen du scénario,
    # avec le même appel que celui utilisé par le Decision
    # Maker (calculate_key_metrics), à titre indicatif :
    # il fluctue légèrement d'une période à l'autre selon
    # le SNR réellement observé.
    from physec_dm.channel import calculate_channel_metrics
    from physec_dm.key_generation import (
        calculate_key_metrics
    )

    reference_channel = calculate_channel_metrics(
        parameters=scenario_parameters,
        snr_db=scenario_parameters.mean_snr_db,
        speed_m_s=0.0
    )

    reference_key_metrics = calculate_key_metrics(
        key_action=KeyAction.K1A,
        parameters=scenario_parameters,
        rho_ab=reference_channel.rho_ab,
        variation_feasible=(
            scenario_parameters.variation_feasible
        )
    )

    required_measurements_reference = (
        reference_key_metrics.required_measurements
    )

    any_deadline_rejection = any(
        True
        for missions_entry in missions
        for step_result in (
            missions_entry["mission_result"].steps
        )
        for evaluation in (
            step_result.decision_maker_result
            .all_evaluations
        )
        if evaluation.decision.key_action
        in (KeyAction.K1A, KeyAction.K1B)
        for rejection in evaluation.rejection_reasons
        if rejection.reason_code
        == "KEY_DEADLINE_CONSTRAINT"
    )

    return {
        "scenario_id": scenario_id,
        "required_measurements_reference": (
            required_measurements_reference
        ),
        "k1a_measurements_collected_final_max": (
            final_k1a_collected
        ),
        "k1a_measurements_remaining_final_min": max(
            required_measurements_reference
            - final_k1a_collected,
            0
        ),
        "k1b_measurements_collected_final_max": (
            final_k1b_collected
        ),
        "k1a_preparation_count": (
            total_k1a_preparations
        ),
        "k1b_probe_count": total_k1b_probes,
        "candidate_ready_events": (
            candidate_ready_events
        ),
        "k1a_activations": k1a_activations,
        "k1b_activations": k1b_activations,
        "duty_cycle_min_remaining_s": (
            duty_cycle_min_remaining
        ),
        "duty_cycle_respected": (
            duty_cycle_respected
        ),
        "deadline_constraint_observed": (
            any_deadline_rejection
        )
    }


# ================================================================
# 6. ÉCRITURE DES FICHIERS
# ================================================================


def write_csv(
    rows,
    field_names,
    output_path
):

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


def write_report(
    summaries,
    seeds,
    max_steps,
    output_path
):

    lines = []

    lines.append(
        "# Rapport de validation progressive K1a / K1b"
    )
    lines.append("")
    lines.append(
        "Validation exécutée avec "
        + str(len(seeds))
        + " graine(s) ("
        + ", ".join(str(seed) for seed in seeds)
        + ") et "
        + str(max_steps)
        + " périodes par mission, sur les trois scénarios "
        "réels de thesis_scenarios.py (cryptopériode "
        "nominale restaurée). Aucun résultat existant de "
        "results/three_scenarios_s2_corrected n'a été "
        "modifié ; cette validation utilise son propre "
        "dossier de sortie."
    )
    lines.append("")

    for summary in summaries:

        lines.append(
            "## "
            + summary["scenario_id"]
        )
        lines.append("")

        lines.append(
            "| Grandeur | Valeur |"
        )
        lines.append(
            "|---|---:|"
        )

        lines.append(
            "| N_required (référence, SNR moyen) | "
            + str(
                summary[
                    "required_measurements_reference"
                ]
            )
            + " |"
        )

        lines.append(
            "| N_collected final (K1a, max observé) | "
            + str(
                summary[
                    "k1a_measurements_collected_final_max"
                ]
            )
            + " |"
        )

        lines.append(
            "| N_remaining final (K1a, estimation) | "
            + str(
                summary[
                    "k1a_measurements_remaining_final_min"
                ]
            )
            + " |"
        )

        lines.append(
            "| N_collected final (K1b, max observé) | "
            + str(
                summary[
                    "k1b_measurements_collected_final_max"
                ]
            )
            + " |"
        )

        lines.append(
            "| Nombre de préparations K1a "
            "(mesures accumulées) | "
            + str(
                summary["k1a_preparation_count"]
            )
            + " |"
        )

        lines.append(
            "| Nombre de sondages K1b émis | "
            + str(
                summary["k1b_probe_count"]
            )
            + " |"
        )

        lines.append(
            "| Nombre de clés candidates prêtes | "
            + str(
                summary["candidate_ready_events"]
            )
            + " |"
        )

        lines.append(
            "| Nombre d'activations K1a | "
            + str(
                summary["k1a_activations"]
            )
            + " |"
        )

        lines.append(
            "| Nombre d'activations K1b | "
            + str(
                summary["k1b_activations"]
            )
            + " |"
        )

        lines.append(
            "| Budget duty-cycle minimal observé (s) | "
            + format(
                summary[
                    "duty_cycle_min_remaining_s"
                ],
                ".4f"
            )
            + " |"
        )

        lines.append(
            "| Duty-cycle respecté "
            "(jamais négatif) | "
            + str(
                summary["duty_cycle_respected"]
            )
            + " |"
        )

        lines.append(
            "| Contrainte d'échéance "
            "(KEY_DEADLINE_CONSTRAINT) observée "
            "au moins une fois | "
            + str(
                summary[
                    "deadline_constraint_observed"
                ]
            )
            + " |"
        )

        lines.append("")

    output_path.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )


# ================================================================
# 7. LANCEMENT
# ================================================================


def run_validation(
    seeds,
    max_steps,
    label
):

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )

    print(
        "Lancement de la campagne "
        + label
        + " de vérification."
    )
    print(
        "Les valeurs provisoires de cette campagne ne "
        "sont pas encore des résultats scientifiques "
        "finaux."
    )

    base_parameters = build_three_scenario_parameters()

    scenarios = build_thesis_scenarios(
        parameters=base_parameters,
        max_steps=max_steps
    )

    all_progression_rows = []
    all_event_rows = []
    all_rejection_rows = []
    all_summaries = []

    for scenario_id in SCENARIO_ORDER:

        scenario = next(
            item
            for item in scenarios
            if item["scenario_id"] == scenario_id
        )

        scenario_parameters = (
            apply_scenario_overrides_for_validation(
                base_parameters,
                scenario
            )
        )

        missions = run_scenario_missions(
            scenario=scenario,
            scenario_parameters=scenario_parameters,
            seeds=seeds,
            max_steps=max_steps
        )

        scenario_progression_rows = []
        scenario_event_rows = []

        for entry in missions:

            scenario_progression_rows.extend(
                extract_progression_rows(
                    scenario_id,
                    entry["seed"],
                    entry["mission_result"]
                )
            )

            scenario_event_rows.extend(
                extract_candidate_key_events(
                    scenario_id,
                    entry["seed"],
                    entry["mission_result"]
                )
            )

            all_rejection_rows.extend(
                extract_rejection_reasons(
                    scenario_id,
                    entry["seed"],
                    entry["mission_result"]
                )
            )

        all_progression_rows.extend(
            scenario_progression_rows
        )

        all_event_rows.extend(
            scenario_event_rows
        )

        all_summaries.append(
            summarize_scenario(
                scenario_id,
                scenario_parameters,
                missions,
                scenario_progression_rows,
                scenario_event_rows
            )
        )

    write_csv(
        all_progression_rows,
        [
            "scenario_id",
            "seed",
            "step_index",
            "renewal_required",
            "legitimate_message_served",
            "selected_decision",
            "k1a_measurements_before",
            "k1a_measurements_after",
            "k1b_measurements_before",
            "k1b_measurements_after",
            "candidate_key_ready_before",
            "candidate_key_ready_after",
            "candidate_key_action",
            "key_age_s_after",
            "remaining_duty_cycle_airtime_s_after"
        ],
        OUTPUT_DIRECTORY / "k1_progression_by_step.csv"
    )

    write_csv(
        all_event_rows,
        [
            "scenario_id",
            "seed",
            "step_index",
            "event",
            "candidate_key_action"
        ],
        OUTPUT_DIRECTORY / "candidate_key_events.csv"
    )

    write_csv(
        all_rejection_rows,
        [
            "scenario_id",
            "seed",
            "key_action",
            "reason_code",
            "occurrence_count"
        ],
        OUTPUT_DIRECTORY / "k1_rejection_reasons.csv"
    )

    write_csv(
        all_summaries,
        [
            "scenario_id",
            "required_measurements_reference",
            "k1a_measurements_collected_final_max",
            "k1a_measurements_remaining_final_min",
            "k1b_measurements_collected_final_max",
            "k1a_preparation_count",
            "k1b_probe_count",
            "candidate_ready_events",
            "k1a_activations",
            "k1b_activations",
            "duty_cycle_min_remaining_s",
            "duty_cycle_respected",
            "deadline_constraint_observed"
        ],
        OUTPUT_DIRECTORY / "k1_validation_summary.csv"
    )

    write_report(
        all_summaries,
        seeds,
        max_steps,
        OUTPUT_DIRECTORY / "k1_progression_report.md"
    )

    return all_summaries


if __name__ == "__main__":

    mode = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "short"
    )

    if mode == "short":

        summaries = run_validation(
            seeds=[2000],
            max_steps=100,
            label="COURTE (1 graine, 100 périodes)"
        )

    elif mode == "intermediate":

        summaries = run_validation(
            seeds=[2000, 2001, 2002],
            max_steps=1500,
            label="INTERMÉDIAIRE (3 graines, 1500 "
            "périodes)"
        )

    else:

        raise ValueError(
            "Mode inconnu : "
            + mode
            + " (utiliser 'short' ou 'intermediate')."
        )

    print("")
    print("Résumé par scénario :")

    for summary in summaries:

        print(
            summary["scenario_id"]
            + " : N_required(réf)="
            + str(
                summary[
                    "required_measurements_reference"
                ]
            )
            + " K1a_collected_max="
            + str(
                summary[
                    "k1a_measurements_collected_final_max"
                ]
            )
            + " K1b_collected_max="
            + str(
                summary[
                    "k1b_measurements_collected_final_max"
                ]
            )
            + " preparations_K1a="
            + str(summary["k1a_preparation_count"])
            + " sondages_K1b="
            + str(summary["k1b_probe_count"])
            + " candidats_prets="
            + str(summary["candidate_ready_events"])
            + " activations_K1a="
            + str(summary["k1a_activations"])
            + " activations_K1b="
            + str(summary["k1b_activations"])
            + " duty_cycle_respecte="
            + str(summary["duty_cycle_respected"])
        )
