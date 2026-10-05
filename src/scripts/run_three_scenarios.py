# csv permet d'exporter les métriques détaillées
# utilisées par les figures et le compte rendu.
import csv


# math est utilisé pour l'intervalle de confiance à 95 %.
import math


# Path facilite la création des dossiers.
from pathlib import Path


# statistics fournit la moyenne et l'écart-type.
import statistics


# run_campaign exécute les missions.
from physec_dm.campaign import (
    calculate_decision_frequencies,
    run_campaign,
    write_csv_rows
)


# La configuration contient uniquement
# les trois scénarios retenus pour la proposition.
from physec_dm.thesis_scenarios import (
    build_three_scenario_configuration
)


# ================================================================
# 1. EXTRACTION DES QUATRE OBJECTIFS
# ================================================================


# Cette fonction lit les métriques de la décision
# sélectionnée pendant une période.
#
# Lorsque le Decision Maker refuse le service,
# aucune décision n'est sélectionnée et la fonction
# retourne None.
def extract_selected_step_metrics(
    step_result,
    scenario_id,
    policy_id,
    seed
):

    selected_evaluation = (
        step_result
        .decision_maker_result
        .selected_evaluation
    )

    if selected_evaluation is None:

        return None

    authentication_metrics = (
        selected_evaluation
        .authentication_metrics
    )

    key_metrics = (
        selected_evaluation
        .key_metrics
    )

    cost_metrics = (
        selected_evaluation
        .cost_metrics
    )

    return {
        "scenario_id": scenario_id,
        "policy_id": policy_id,
        "seed": seed,
        "step_index": (
            step_result.state_before.step_index
        ),
        "decision_name": (
            selected_evaluation
            .decision
            .get_name()
        ),

        # Objectif 1 :
        # énergie à minimiser.
        "energy_objective_j": (
            cost_metrics.expected_energy_j
        ),

        # Objectif 2 :
        # latence normalisée à minimiser.
        "normalized_latency_objective": (
            cost_metrics.normalized_latency
        ),

        # Valeurs complémentaires en secondes.
        "authentication_latency_s": (
            cost_metrics.authentication_latency_s
        ),
        "key_latency_s": (
            cost_metrics.key_latency_s
        ),

        # Objectif 3 :
        # robustesse d'authentification à maximiser.
        "authentication_robustness": (
            authentication_metrics
            .authentication_robustness
        ),

        # Objectif 4 :
        # qualité de clé à maximiser.
        "key_quality": (
            key_metrics.key_quality
        ),

        "pareto_front_size": len(
            step_result
            .decision_maker_result
            .pareto_front
        ),

        "criticality": (
            step_result.context.criticality
        ),

        "snr_db": (
            step_result.channel_metrics.snr_db
        )
    }


# Cette fonction crée une ligne
# pour chaque période ayant une décision sélectionnée.
def build_selected_step_rows(
    campaign_result
):

    rows = []

    for mission_result in (
        campaign_result.mission_results
    ):

        scenario_id = (
            mission_result
            .parameters_snapshot
            .get(
                "scenario_id",
                "UNKNOWN"
            )
        )

        for step_result in mission_result.steps:

            row = extract_selected_step_metrics(
                step_result=step_result,
                scenario_id=scenario_id,
                policy_id=(
                    mission_result.policy_id
                ),
                seed=mission_result.seed
            )

            if row is not None:

                rows.append(
                    row
                )

    return rows


# ================================================================
# 2. RÉSUMÉ PAR MISSION
# ================================================================


def safe_mean(
    values
):

    defined_values = [
        float(value)
        for value in values
        if value is not None
    ]

    if len(defined_values) == 0:

        return None

    return statistics.mean(
        defined_values
    )


# Cette fonction calcule une moyenne par mission.
#
# Nous évitons ainsi qu'une mission plus longue
# pèse artificiellement davantage qu'une autre.
def build_per_mission_objective_rows(
    campaign_result
):

    rows = []

    for mission_result in (
        campaign_result.mission_results
    ):

        scenario_id = (
            mission_result
            .parameters_snapshot
            .get(
                "scenario_id",
                "UNKNOWN"
            )
        )

        selected_rows = []

        for step_result in mission_result.steps:

            row = extract_selected_step_metrics(
                step_result=step_result,
                scenario_id=scenario_id,
                policy_id=(
                    mission_result.policy_id
                ),
                seed=mission_result.seed
            )

            if row is not None:

                selected_rows.append(
                    row
                )

        total_steps = len(
            mission_result.steps
        )

        selected_steps = len(
            selected_rows
        )

        selection_rate = None

        if total_steps > 0:

            selection_rate = (
                selected_steps
                / total_steps
            )

        rows.append(
            {
                "scenario_id": scenario_id,
                "policy_id": (
                    mission_result.policy_id
                ),
                "seed": mission_result.seed,
                "total_steps": total_steps,
                "selected_steps": selected_steps,
                "selection_rate": selection_rate,

                "mean_energy_objective_j": safe_mean(
                    [
                        row[
                            "energy_objective_j"
                        ]
                        for row in selected_rows
                    ]
                ),

                "mean_normalized_latency_objective": (
                    safe_mean(
                        [
                            row[
                                "normalized_latency_objective"
                            ]
                            for row in selected_rows
                        ]
                    )
                ),

                "mean_authentication_robustness": (
                    safe_mean(
                        [
                            row[
                                "authentication_robustness"
                            ]
                            for row in selected_rows
                        ]
                    )
                ),

                "mean_key_quality": safe_mean(
                    [
                        row["key_quality"]
                        for row in selected_rows
                    ]
                ),

                "legitimate_refusal_rate": (
                    mission_result
                    .legitimate_refusal_rate
                ),

                "false_acceptance_rate": (
                    mission_result
                    .false_acceptance_rate
                ),

                "security_floor_violation_rate": (
                    mission_result
                    .security_floor_violation_rate
                ),

                "censored": mission_result.censored,
                "stop_reason": (
                    mission_result.stop_reason
                )
            }
        )

    return rows


# ================================================================
# 3. INTERVALLES DE CONFIANCE
# ================================================================


# Cette fonction calcule :
#
# moyenne ± 1,96 * s / sqrt(n)
def summarize_values(
    values
):

    defined_values = [
        float(value)
        for value in values
        if value is not None
    ]

    count = len(
        defined_values
    )

    if count == 0:

        return {
            "count": 0,
            "mean": None,
            "std": None,
            "ci95_low": None,
            "ci95_high": None
        }

    mean_value = statistics.mean(
        defined_values
    )

    if count == 1:

        standard_deviation = 0.0
        ci95_half_width = 0.0

    else:

        standard_deviation = statistics.stdev(
            defined_values
        )

        ci95_half_width = (
            1.96
            * standard_deviation
            / math.sqrt(
                count
            )
        )

    return {
        "count": count,
        "mean": mean_value,
        "std": standard_deviation,
        "ci95_low": (
            mean_value
            - ci95_half_width
        ),
        "ci95_high": (
            mean_value
            + ci95_half_width
        )
    }


# Cette fonction résume les quatre objectifs
# pour chaque scénario.
def build_four_objective_summary_rows(
    per_mission_rows
):

    scenario_ids = []

    for row in per_mission_rows:

        if row["scenario_id"] not in scenario_ids:

            scenario_ids.append(
                row["scenario_id"]
            )

    metric_definitions = [
        (
            "energy_objective_j",
            "mean_energy_objective_j"
        ),
        (
            "normalized_latency_objective",
            "mean_normalized_latency_objective"
        ),
        (
            "authentication_robustness",
            "mean_authentication_robustness"
        ),
        (
            "key_quality",
            "mean_key_quality"
        ),
        (
            "selection_rate",
            "selection_rate"
        ),
        (
            "legitimate_refusal_rate",
            "legitimate_refusal_rate"
        ),
        (
            "false_acceptance_rate",
            "false_acceptance_rate"
        ),
        (
            "security_floor_violation_rate",
            "security_floor_violation_rate"
        )
    ]

    summary_rows = []

    for scenario_id in scenario_ids:

        scenario_rows = [
            row
            for row in per_mission_rows
            if row["scenario_id"] == scenario_id
        ]

        summary_row = {
            "scenario_id": scenario_id,
            "mission_count": len(
                scenario_rows
            )
        }

        for output_name, input_name in (
            metric_definitions
        ):

            summary = summarize_values(
                [
                    row[input_name]
                    for row in scenario_rows
                ]
            )

            for summary_name, value in (
                summary.items()
            ):

                summary_row[
                    output_name
                    + "_"
                    + summary_name
                ] = value

        summary_rows.append(
            summary_row
        )

    return summary_rows


# ================================================================
# 4. FIGURES
# ================================================================


# Cette fonction retourne une valeur d'erreur
# compatible avec matplotlib.
def calculate_error_bar(
    row,
    metric_name
):

    mean_value = row[
        metric_name
        + "_mean"
    ]

    ci95_low = row[
        metric_name
        + "_ci95_low"
    ]

    ci95_high = row[
        metric_name
        + "_ci95_high"
    ]

    if (
        mean_value is None
        or ci95_low is None
        or ci95_high is None
    ):

        return 0.0

    return max(
        mean_value - ci95_low,
        ci95_high - mean_value
    )


# Cette fonction crée une figure
# pour un seul objectif.
def plot_objective(
    summary_rows,
    metric_name,
    title,
    y_label,
    output_path
):

    # L'import reste local afin que les tests
    # non graphiques puissent fonctionner
    # même avant l'installation de matplotlib.
    import matplotlib.pyplot as plt

    scenario_labels = [
        "S1",
        "S2",
        "S3"
    ]

    means = [
        row[
            metric_name
            + "_mean"
        ]
        if row[
            metric_name
            + "_mean"
        ] is not None
        else 0.0
        for row in summary_rows
    ]

    errors = [
        calculate_error_bar(
            row,
            metric_name
        )
        for row in summary_rows
    ]

    figure, axis = plt.subplots(
        figsize=(
            6.4,
            4.2
        )
    )

    axis.bar(
        scenario_labels,
        means,
        yerr=errors,
        capsize=5
    )

    axis.set_title(
        title
    )

    axis.set_xlabel(
        "Scénario"
    )

    axis.set_ylabel(
        y_label
    )

    axis.grid(
        axis="y",
        alpha=0.3
    )

    figure.tight_layout()

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(
        figure
    )

    return output_path


# Cette fonction génère les quatre figures
# correspondant exactement aux quatre objectifs.
def generate_four_objective_figures(
    summary_rows,
    output_directory
):

    output_directory = Path(
        output_directory
    )

    figures_directory = (
        output_directory
        / "figures"
    )

    figure_paths = {
        "energy": plot_objective(
            summary_rows=summary_rows,
            metric_name="energy_objective_j",
            title=(
                "Énergie attendue de la décision sélectionnée"
            ),
            y_label=(
                "Énergie (J) → plus bas = meilleur"
            ),
            output_path=(
                figures_directory
                / "figure_1_energy.png"
            )
        ),

        "latency": plot_objective(
            summary_rows=summary_rows,
            metric_name=(
                "normalized_latency_objective"
            ),
            title=(
                "Objectif de latence normalisée"
            ),
            y_label=(
                "Latence normalisée → plus bas = meilleur"
            ),
            output_path=(
                figures_directory
                / "figure_2_latency.png"
            )
        ),

        "authentication": plot_objective(
            summary_rows=summary_rows,
            metric_name=(
                "authentication_robustness"
            ),
            title=(
                "Robustesse de l'authentification"
            ),
            y_label=(
                "Robustesse → plus haut = meilleur"
            ),
            output_path=(
                figures_directory
                / "figure_3_authentication.png"
            )
        ),

        "key": plot_objective(
            summary_rows=summary_rows,
            metric_name="key_quality",
            title=(
                "Qualité du mécanisme de clé"
            ),
            y_label=(
                "Qualité de clé → plus haut = meilleur"
            ),
            output_path=(
                figures_directory
                / "figure_4_key_quality.png"
            )
        )
    }

    return figure_paths


# Cette figure complémentaire explique
# les décisions réellement sélectionnées.
def generate_decision_frequency_figure(
    campaign_result,
    output_directory
):

    import matplotlib.pyplot as plt

    frequency_rows = calculate_decision_frequencies(
        campaign_result
    )

    scenario_ids = []

    decision_names = []

    for row in frequency_rows:

        if row["scenario_id"] not in scenario_ids:

            scenario_ids.append(
                row["scenario_id"]
            )

        if row["decision_name"] not in decision_names:

            decision_names.append(
                row["decision_name"]
            )

    x_positions = list(
        range(
            len(scenario_ids)
        )
    )

    figure, axis = plt.subplots(
        figsize=(
            8.0,
            4.8
        )
    )

    bottoms = [
        0.0
        for _ in scenario_ids
    ]

    for decision_name in decision_names:

        values = []

        for scenario_id in scenario_ids:

            matching_rows = [
                row
                for row in frequency_rows
                if (
                    row["scenario_id"] == scenario_id
                    and row["decision_name"] == decision_name
                )
            ]

            if len(matching_rows) == 0:

                values.append(
                    0.0
                )

            else:

                frequency = matching_rows[0][
                    "selection_frequency"
                ]

                values.append(
                    0.0
                    if frequency is None
                    else frequency
                )

        axis.bar(
            x_positions,
            values,
            bottom=bottoms,
            label=decision_name
        )

        bottoms = [
            bottoms[index]
            + values[index]
            for index in range(
                len(values)
            )
        ]

    axis.set_xticks(
        x_positions,
        [
            "S1",
            "S2",
            "S3"
        ]
    )

    axis.set_xlabel(
        "Scénario"
    )

    axis.set_ylabel(
        "Fréquence de sélection"
    )

    axis.set_title(
        "Décisions sélectionnées par le Decision Maker"
    )

    axis.set_ylim(
        0.0,
        1.0
    )

    axis.legend(
        bbox_to_anchor=(
            1.02,
            1.0
        ),
        loc="upper left"
    )

    axis.grid(
        axis="y",
        alpha=0.3
    )

    figure.tight_layout()

    output_path = (
        Path(output_directory)
        / "figures"
        / "figure_5_decision_frequencies.png"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(
        figure
    )

    return output_path


# ================================================================
# 5. LANCEMENT
# ================================================================


def run_three_scenario_experiment(
    max_steps=300,
    seed_count=30,
    output_directory=(
        "results/three_scenarios_s2_corrected"
    )
):

    configuration = (
        build_three_scenario_configuration(
            max_steps=max_steps,
            seed_count=seed_count
        )
    )

    output_directory = Path(
        output_directory
    )

    campaign_result = run_campaign(
        base_parameters=(
            configuration["parameters"]
        ),
        campaign_id=(
            configuration["campaign_id"]
        ),
        scenarios=(
            configuration["scenarios"]
        ),
        policies=(
            configuration["policies"]
        ),
        seeds=configuration["seeds"],
        output_directory=output_directory,
        max_steps=max_steps,
        export_results=True
    )

    selected_step_rows = (
        build_selected_step_rows(
            campaign_result
        )
    )

    per_mission_rows = (
        build_per_mission_objective_rows(
            campaign_result
        )
    )

    summary_rows = (
        build_four_objective_summary_rows(
            per_mission_rows
        )
    )

    write_csv_rows(
        output_directory
        / "selected_step_metrics.csv",
        selected_step_rows
    )

    write_csv_rows(
        output_directory
        / "per_mission_objectives.csv",
        per_mission_rows
    )

    write_csv_rows(
        output_directory
        / "four_objective_summary.csv",
        summary_rows
    )

    figure_paths = (
        generate_four_objective_figures(
            summary_rows,
            output_directory
        )
    )

    decision_figure_path = (
        generate_decision_frequency_figure(
            campaign_result,
            output_directory
        )
    )

    return {
        "campaign_result": campaign_result,
        "selected_step_rows": (
            selected_step_rows
        ),
        "per_mission_rows": (
            per_mission_rows
        ),
        "summary_rows": summary_rows,
        "figure_paths": figure_paths,
        "decision_figure_path": (
            decision_figure_path
        )
    }


# Cette fonction affiche un résumé court
# dans le terminal.
def print_summary(
    summary_rows
):

    print()
    print(
        "============================================================"
    )
    print(
        "RÉSULTATS PRÉLIMINAIRES DES TROIS SCÉNARIOS"
    )
    print(
        "============================================================"
    )

    for row in summary_rows:

        print()
        print(
            row["scenario_id"]
        )

        print(
            "Énergie moyenne :",
            row[
                "energy_objective_j_mean"
            ]
        )

        print(
            "Latence normalisée moyenne :",
            row[
                "normalized_latency_objective_mean"
            ]
        )

        print(
            "Robustesse d'authentification moyenne :",
            row[
                "authentication_robustness_mean"
            ]
        )

        print(
            "Qualité de clé moyenne :",
            row[
                "key_quality_mean"
            ]
        )

        print(
            "Taux de sélection :",
            row[
                "selection_rate_mean"
            ]
        )


def main():

    print(
        "Lancement des trois scénarios "
        "de la proposition de thèse."
    )

    print(
        "Ces résultats restent préliminaires "
        "car certains coûts sont exploratoires."
    )

    experiment_result = (
        run_three_scenario_experiment()
    )

    print_summary(
        experiment_result[
            "summary_rows"
        ]
    )

    print()
    print(
        "Résultats enregistrés dans : "
        "results/three_scenarios_s2_corrected"
    )

    return experiment_result


if __name__ == "__main__":

    main()
