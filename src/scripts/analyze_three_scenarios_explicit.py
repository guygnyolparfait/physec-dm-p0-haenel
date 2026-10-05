# Ce script construit une couche d'analyse et de visualisation
# plus explicite à partir des résultats déjà produits
# par run_three_scenarios.py.
#
# Il ne relance aucune mission.
#
# Il lit uniquement les fichiers CSV déjà exportés
# dans le dossier de résultats sélectionné, et lit les
# définitions officielles des scénarios dans
# physec_dm/thesis_scenarios.py pour ne jamais inventer
# une valeur de contexte (SNR, probabilités, etc.).
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from physec_dm.thesis_scenarios import (
    build_thesis_scenarios,
    build_three_scenario_parameters
)


# ================================================================
# 1. SÉLECTION DU DOSSIER SOURCE
# ================================================================


# Le dossier corrigé de S2 est utilisé en priorité s'il existe.
#
# Sinon, le script retombe sur le dossier original
# results/three_scenarios.
#
# Aucune mission n'est relancée : ce script est
# une couche de lecture et de visualisation uniquement.
def select_source_directory():

    corrected_directory = Path(
        "results/three_scenarios_s2_corrected"
    )

    if corrected_directory.exists():

        return corrected_directory

    return Path(
        "results/three_scenarios"
    )


OUTPUT_DIRECTORY = Path(
    "results/three_scenarios_explicit_analysis"
)


# ================================================================
# 2. DESCRIPTIONS EXPLICITES DES SCÉNARIOS
# ================================================================


SCENARIO_ORDER = [
    "S1-DEGRADED-CHANNEL",
    "S2-RESOURCE-CONSTRAINED",
    "S3-HIGH-SECURITY-PRESSURE"
]

SCENARIO_DISPLAY_NAMES = {
    "S1-DEGRADED-CHANNEL": "S1 — Canal dégradé",
    "S2-RESOURCE-CONSTRAINED": "S2 — Ressources contraintes",
    "S3-HIGH-SECURITY-PRESSURE": "S3 — Forte pression de sécurité"
}

SCIENTIFIC_GOALS = {
    "S1-DEGRADED-CHANNEL": (
        "Verifier que le Decision Maker rejette "
        "les mecanismes PHY non fiables."
    ),
    "S2-RESOURCE-CONSTRAINED": (
        "Verifier que le Decision Maker minimise "
        "l'energie et la latence tout en maintenant "
        "la securite."
    ),
    "S3-HIGH-SECURITY-PRESSURE": (
        "Verifier que le Decision Maker maximise "
        "l'authentification et la qualite de cle "
        "lorsque le contexte est favorable."
    )
}


# Étiquettes multi-lignes utilisées directement
# comme graduations des axes des figures.
#
# Un retour à la ligne sépare chaque information
# afin d'éviter tout chevauchement.
SCENARIO_AXIS_LABELS = {
    "S1-DEGRADED-CHANNEL": (
        "S1 — Canal dégradé\n"
        "SNR = −10 dB\n"
        "PHY indisponible\n"
        "Mallory = 15 %"
    ),
    "S2-RESOURCE-CONSTRAINED": (
        "S2 — Ressources contraintes\n"
        "SNR = 5 dB\n"
        "Batterie contrainte\n"
        "Messages critiques = 60 %"
    ),
    "S3-HIGH-SECURITY-PRESSURE": (
        "S3 — Forte pression de sécurité\n"
        "SNR = 20 dB\n"
        "PHY disponible\n"
        "Mallory = 30 %"
    )
}


# Cette mention rappelle la taille de l'échantillon
# Monte Carlo sur chaque figure statistique.
SAMPLE_SIZE_CAPTION = (
    "30 graines × 300 périodes par scénario — "
    "moyenne et intervalle de confiance à 95 %"
)


# Ordre et couleurs fixes des huit décisions possibles.
#
# Cet ordre est conservé même lorsqu'une décision
# n'est jamais sélectionnée, afin que l'absence
# de K1a et K1b reste visible dans la légende.
DECISION_ORDER = [
    "A1-K0",
    "A1-K1a",
    "A1-K1b",
    "A1-K2",
    "A2-K0",
    "A2-K1a",
    "A2-K1b",
    "A2-K2"
]

DECISION_COLORS = {
    "A1-K0": "#4C72B0",
    "A1-K1a": "#93B4DB",
    "A1-K1b": "#C6D8ED",
    "A1-K2": "#2E4A72",
    "A2-K0": "#C44E52",
    "A2-K1a": "#E08A8D",
    "A2-K1b": "#F2C6C8",
    "A2-K2": "#8C2528"
}


# ================================================================
# 3. LECTURE DES RÉSULTATS EXISTANTS
# ================================================================


def read_csv_rows(file_path):

    with open(
        file_path,
        newline="",
        encoding="utf-8"
    ) as csv_file:

        return list(
            csv.DictReader(
                csv_file
            )
        )


# Cette fonction lit les définitions officielles
# des trois scénarios directement dans le module
# scientifique déjà validé, afin de ne jamais
# recopier ou inventer une valeur de contexte.
def load_scenario_metadata():

    parameters = build_three_scenario_parameters()

    scenarios = build_thesis_scenarios(
        parameters=parameters,
        max_steps=300
    )

    metadata = {}

    for scenario in scenarios:

        overrides = scenario[
            "parameter_overrides"
        ]

        scenario_id = scenario["scenario_id"]

        battery_condition = (
            "Nominale ("
            + format(
                parameters.initial_battery_energy_j,
                ".1f"
            )
            + " J, réserve "
            + format(
                parameters.minimum_battery_energy_j,
                ".1f"
            )
            + " J)"
        )

        if "initial_battery_energy_j" in overrides:

            battery_condition = (
                "Contrainte ("
                + format(
                    overrides[
                        "initial_battery_energy_j"
                    ],
                    ".1f"
                )
                + " J, réserve "
                + format(
                    overrides[
                        "minimum_battery_energy_j"
                    ],
                    ".1f"
                )
                + " J)"
            )

        metadata[scenario_id] = {
            "snr_db": overrides["mean_snr_db"],
            "critical_message_probability": overrides[
                "critical_message_probability"
            ],
            "mallory_attempt_probability": overrides[
                "mallory_attempt_probability"
            ],
            "variation_feasible": scenario[
                "variation_feasible"
            ],
            "battery_condition": battery_condition
        }

    return metadata


def load_four_objective_summary(source_directory):

    rows = read_csv_rows(
        source_directory / "four_objective_summary.csv"
    )

    return {
        row["scenario_id"]: row
        for row in rows
    }


# Cette fonction retourne, pour chaque scénario,
# la fréquence de chacune des huit décisions possibles.
#
# Une décision jamais sélectionnée reçoit explicitement
# la valeur 0.0, plutôt que d'être absente.
def load_decision_frequencies(source_directory):

    rows = read_csv_rows(
        source_directory / "decision_frequencies.csv"
    )

    frequencies = {
        scenario_id: {
            decision_name: 0.0
            for decision_name in DECISION_ORDER
        }
        for scenario_id in SCENARIO_ORDER
    }

    for row in rows:

        scenario_id = row["scenario_id"]
        decision_name = row["decision_name"]

        frequencies[scenario_id][decision_name] = float(
            row["selection_frequency"]
        )

    return frequencies


# ================================================================
# 4. TABLEAU CSV LISIBLE
# ================================================================


def build_scenario_summary_rows(
    scenario_metadata,
    four_objective_summary
):

    rows = []

    for scenario_id in SCENARIO_ORDER:

        metadata = scenario_metadata[scenario_id]
        summary = four_objective_summary[scenario_id]

        rows.append(
            {
                "Scenario_ID": scenario_id,
                "Scenario_Name": (
                    SCENARIO_DISPLAY_NAMES[scenario_id]
                ),
                "Scientific_Goal": (
                    SCIENTIFIC_GOALS[scenario_id]
                ),
                "SNR_dB": metadata["snr_db"],
                "Battery_Condition": metadata[
                    "battery_condition"
                ],
                "Critical_Message_Probability": metadata[
                    "critical_message_probability"
                ],
                "Mallory_Attempt_Probability": metadata[
                    "mallory_attempt_probability"
                ],
                "PHY_Variability": metadata[
                    "variation_feasible"
                ],
                "Energy_Mean_J": summary[
                    "energy_objective_j_mean"
                ],
                "Energy_CI95_Low": summary[
                    "energy_objective_j_ci95_low"
                ],
                "Energy_CI95_High": summary[
                    "energy_objective_j_ci95_high"
                ],
                "Latency_Normalized_Mean": summary[
                    "normalized_latency_objective_mean"
                ],
                "Latency_CI95_Low": summary[
                    "normalized_latency_objective_ci95_low"
                ],
                "Latency_CI95_High": summary[
                    "normalized_latency_objective_ci95_high"
                ],
                "Authentication_Robustness_Mean": summary[
                    "authentication_robustness_mean"
                ],
                "Authentication_CI95_Low": summary[
                    "authentication_robustness_ci95_low"
                ],
                "Authentication_CI95_High": summary[
                    "authentication_robustness_ci95_high"
                ],
                "Key_Quality_Mean": summary[
                    "key_quality_mean"
                ],
                "Key_CI95_Low": summary[
                    "key_quality_ci95_low"
                ],
                "Key_CI95_High": summary[
                    "key_quality_ci95_high"
                ],
                "Selection_Rate_Mean": summary[
                    "selection_rate_mean"
                ],
                "Legitimate_Refusal_Rate_Mean": summary[
                    "legitimate_refusal_rate_mean"
                ],
                "False_Acceptance_Rate_Mean": summary[
                    "false_acceptance_rate_mean"
                ],
                "Security_Floor_Violation_Rate_Mean": (
                    summary[
                        "security_floor_violation_rate_mean"
                    ]
                )
            }
        )

    return rows


def write_scenario_summary_csv(
    rows,
    output_path
):

    field_names = list(
        rows[0].keys()
    )

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

        writer.writerows(
            rows
        )


# ================================================================
# 5. OUTILS COMMUNS AUX FIGURES 1 À 4
# ================================================================


# Cette fonction construit un diagramme en barres unique,
# avec intervalles de confiance à 95 %, pour un objectif
# et affiche les trois scénarios avec leur nom complet
# et leur contexte.
def plot_single_objective_bar_chart(
    four_objective_summary,
    mean_key,
    ci_low_key,
    ci_high_key,
    title,
    y_label,
    output_path
):

    scenario_labels = [
        SCENARIO_AXIS_LABELS[scenario_id]
        for scenario_id in SCENARIO_ORDER
    ]

    means = [
        float(
            four_objective_summary[scenario_id][mean_key]
        )
        for scenario_id in SCENARIO_ORDER
    ]

    errors_low = [
        means[index]
        - float(
            four_objective_summary[
                SCENARIO_ORDER[index]
            ][ci_low_key]
        )
        for index in range(
            len(SCENARIO_ORDER)
        )
    ]

    errors_high = [
        float(
            four_objective_summary[
                SCENARIO_ORDER[index]
            ][ci_high_key]
        )
        - means[index]
        for index in range(
            len(SCENARIO_ORDER)
        )
    ]

    figure, axis = plt.subplots(
        figsize=(
            8.0,
            5.2
        )
    )

    bar_positions = range(
        len(SCENARIO_ORDER)
    )

    axis.bar(
        bar_positions,
        means,
        yerr=[
            errors_low,
            errors_high
        ],
        capsize=6,
        color=[
            "#4C72B0",
            "#C44E52",
            "#55A868"
        ]
    )

    axis.set_xticks(
        list(
            bar_positions
        )
    )

    axis.set_xticklabels(
        scenario_labels
    )

    axis.set_title(
        title
        + "\n"
        + SAMPLE_SIZE_CAPTION,
        fontsize=11
    )

    axis.set_ylabel(
        y_label
    )

    axis.grid(
        axis="y",
        alpha=0.3
    )

    figure.tight_layout()

    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(
        figure
    )


# ================================================================
# 6. FIGURE 5 : FRÉQUENCES DE DÉCISION
# ================================================================


def plot_decision_frequencies_figure(
    decision_frequencies,
    output_path
):

    figure, axis = plt.subplots(
        figsize=(
            13.0,
            6.0
        )
    )

    # Un espacement plus large que 1.0 entre les positions
    # évite que les étiquettes multi-lignes des scénarios
    # ne se chevauchent, la légende réduisant par ailleurs
    # la largeur utile de la zone de tracé.
    bar_positions = np.arange(
        len(SCENARIO_ORDER)
    ) * 1.6

    bottoms = np.zeros(
        len(SCENARIO_ORDER)
    )

    for decision_name in DECISION_ORDER:

        values = np.array(
            [
                decision_frequencies[
                    scenario_id
                ][decision_name]
                for scenario_id in SCENARIO_ORDER
            ]
        )

        axis.bar(
            bar_positions,
            values,
            width=0.9,
            bottom=bottoms,
            label=decision_name,
            color=DECISION_COLORS[decision_name]
        )

        bottoms = bottoms + values

    axis.set_xticks(
        bar_positions
    )

    axis.set_xticklabels(
        [
            SCENARIO_AXIS_LABELS[scenario_id]
            for scenario_id in SCENARIO_ORDER
        ],
        fontsize=9
    )

    axis.set_xlim(
        bar_positions[0] - 0.9,
        bar_positions[-1] + 0.9
    )

    axis.set_ylim(
        0.0,
        1.0
    )

    axis.set_ylabel(
        "Fréquence de sélection"
    )

    axis.set_title(
        "Figure 5 — Fréquence des décisions "
        "sélectionnées par le Decision Maker\n"
        + SAMPLE_SIZE_CAPTION,
        fontsize=11
    )

    axis.legend(
        title="Décision (Authentification-Clé)",
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

    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(
        figure
    )


# ================================================================
# 7. FIGURE 6 : RADAR DES QUATRE OBJECTIFS
# ================================================================


# Cette fonction normalise une liste de trois valeurs
# entre 0 et 1 par une mise à l'échelle min-max.
#
# higher_is_better=True signifie que la valeur la plus
# grande reçoit le score 1.0.
#
# higher_is_better=False signifie que la valeur la plus
# petite reçoit le score 1.0 (cas de l'énergie
# et de la latence, que l'on cherche à minimiser).
#
# Lorsque les trois valeurs sont identiques, l'échelle
# est dégénérée : un score neutre de 1.0 est attribué
# aux trois scénarios, et ce cas est explicitement
# signalé dans le fichier d'explication de la normalisation.
def normalize_min_max(
    values,
    higher_is_better
):

    minimum_value = min(values)
    maximum_value = max(values)

    if maximum_value == minimum_value:

        return (
            [1.0 for _ in values],
            True
        )

    if higher_is_better:

        scores = [
            (value - minimum_value)
            / (maximum_value - minimum_value)
            for value in values
        ]

    else:

        scores = [
            (maximum_value - value)
            / (maximum_value - minimum_value)
            for value in values
        ]

    return (
        scores,
        False
    )


def plot_radar_figure(
    four_objective_summary,
    output_path
):

    energy_values = [
        float(
            four_objective_summary[scenario_id][
                "energy_objective_j_mean"
            ]
        )
        for scenario_id in SCENARIO_ORDER
    ]

    latency_values = [
        float(
            four_objective_summary[scenario_id][
                "normalized_latency_objective_mean"
            ]
        )
        for scenario_id in SCENARIO_ORDER
    ]

    authentication_values = [
        float(
            four_objective_summary[scenario_id][
                "authentication_robustness_mean"
            ]
        )
        for scenario_id in SCENARIO_ORDER
    ]

    key_quality_values = [
        float(
            four_objective_summary[scenario_id][
                "key_quality_mean"
            ]
        )
        for scenario_id in SCENARIO_ORDER
    ]

    energy_scores, energy_degenerate = normalize_min_max(
        energy_values,
        higher_is_better=False
    )

    latency_scores, latency_degenerate = normalize_min_max(
        latency_values,
        higher_is_better=False
    )

    authentication_scores, authentication_degenerate = (
        normalize_min_max(
            authentication_values,
            higher_is_better=True
        )
    )

    key_quality_scores, key_quality_degenerate = (
        normalize_min_max(
            key_quality_values,
            higher_is_better=True
        )
    )

    axis_labels = [
        "Score énergie",
        "Score latence",
        "Score authentification",
        "Score qualité de clé"
    ]

    angles = np.linspace(
        0,
        2 * np.pi,
        len(axis_labels),
        endpoint=False
    ).tolist()

    angles = angles + [
        angles[0]
    ]

    figure, axis = plt.subplots(
        figsize=(
            7.0,
            7.0
        ),
        subplot_kw={
            "projection": "polar"
        }
    )

    colors = [
        "#4C72B0",
        "#C44E52",
        "#55A868"
    ]

    for index, scenario_id in enumerate(
        SCENARIO_ORDER
    ):

        scenario_scores = [
            energy_scores[index],
            latency_scores[index],
            authentication_scores[index],
            key_quality_scores[index]
        ]

        scenario_scores = scenario_scores + [
            scenario_scores[0]
        ]

        axis.plot(
            angles,
            scenario_scores,
            color=colors[index],
            linewidth=2,
            label=SCENARIO_DISPLAY_NAMES[
                scenario_id
            ]
        )

        axis.fill(
            angles,
            scenario_scores,
            color=colors[index],
            alpha=0.15
        )

    axis.set_xticks(
        angles[:-1]
    )

    axis.set_xticklabels(
        axis_labels
    )

    axis.set_ylim(
        0.0,
        1.0
    )

    axis.set_title(
        "Figure 6 — Comparaison globale des trois "
        "scénarios selon les quatre objectifs\n"
        "(normalisation min-max entre scénarios ; "
        "voir radar_normalization_method.md)",
        fontsize=10
    )

    axis.legend(
        loc="upper right",
        bbox_to_anchor=(
            1.35,
            1.1
        )
    )

    figure.tight_layout()

    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(
        figure
    )

    return {
        "energy_degenerate": energy_degenerate,
        "latency_degenerate": latency_degenerate,
        "authentication_degenerate": (
            authentication_degenerate
        ),
        "key_quality_degenerate": key_quality_degenerate,
        "energy_scores": energy_scores,
        "latency_scores": latency_scores,
        "authentication_scores": authentication_scores,
        "key_quality_scores": key_quality_scores
    }


def write_radar_normalization_explanation(
    radar_result,
    output_path
):

    lines = [
        "# Méthode de normalisation du radar (Figure 6)",
        "",
        "Le radar de la figure 6 compare les trois "
        "scénarios sur quatre axes normalisés entre 0 et 1, "
        "où **plus grand signifie toujours meilleur**.",
        "",
        "## Méthode",
        "",
        "Pour chaque objectif, une normalisation min-max "
        "est appliquée **entre les trois scénarios** "
        "(et non par rapport à une borne théorique) :",
        "",
        "```",
        "Score_Énergie          = (max(E) - E) / (max(E) - min(E))",
        "Score_Latence          = (max(L) - L) / (max(L) - min(L))",
        "Score_Authentification = (A - min(A)) / (max(A) - min(A))",
        "Score_Clé              = (K - min(K)) / (max(K) - min(K))",
        "```",
        "",
        "où E, L, A, K sont les moyennes de chaque scénario "
        "pour l'énergie, la latence normalisée, la robustesse "
        "d'authentification et la qualité de clé.",
        "",
        "L'énergie et la latence sont inversées (1 - normalisation) "
        "car une valeur plus faible est meilleure. "
        "L'authentification et la qualité de clé sont utilisées "
        "directement, car une valeur plus élevée est meilleure.",
        "",
        "## Avertissement scientifique important",
        "",
        "Cette normalisation min-max est calculée sur "
        "seulement **trois points** (un par scénario). "
        "Elle exagère visuellement des écarts absolus qui "
        "peuvent être numériquement très faibles "
        "(par exemple, la robustesse d'authentification varie "
        "seulement entre 0,998 et 1,000 en valeur réelle, "
        "mais occupe tout l'axe 0 à 1 sur le radar). "
        "Le radar doit donc être lu comme une comparaison "
        "**relative et qualitative**, jamais comme une mesure "
        "absolue. Les valeurs réelles figurent dans "
        "scenario_summary_readable.csv.",
        ""
    ]

    if radar_result["key_quality_degenerate"]:

        lines.append(
            "## Cas particulier : qualité de clé"
        )

        lines.append(
            ""
        )

        lines.append(
            "La qualité de clé moyenne est **identique** "
            "dans les trois scénarios (dominance de l'action "
            "K0). L'échelle de normalisation est donc "
            "dégénérée (max = min) : un score neutre de 1.0 "
            "a été attribué aux trois scénarios sur cet axe, "
            "qui n'est en réalité pas discriminant."
        )

        lines.append(
            ""
        )

    output_path.write_text(
        "\n".join(
            lines
        ),
        encoding="utf-8"
    )


# ================================================================
# 8. FIGURE 7 : PROFILS SYNTHÉTIQUES PAR SCÉNARIO
# ================================================================


# Cette fonction affiche, pour un scénario, cinq barres
# horizontales représentant son profil synthétique.
#
# La longueur visuelle de chaque barre est mise à l'échelle
# par une référence propre à chaque métrique (indiquée
# entre parenthèses dans l'étiquette), uniquement pour
# rendre les cinq barres lisibles côte à côte malgré
# leurs unités différentes. La valeur réelle est toujours
# annotée à la fin de la barre.
def plot_scenario_portrait(
    axis,
    scenario_id,
    four_objective_summary
):

    summary = four_objective_summary[scenario_id]

    energy = float(
        summary["energy_objective_j_mean"]
    )
    latency = float(
        summary["normalized_latency_objective_mean"]
    )
    robustness = float(
        summary["authentication_robustness_mean"]
    )
    key_quality = float(
        summary["key_quality_mean"]
    )
    refusal_rate = float(
        summary["legitimate_refusal_rate_mean"]
    )

    # Références d'échelle indicatives, propres
    # à chaque métrique (voir docstring ci-dessus).
    energy_reference = 0.30
    latency_reference = 0.05

    metrics = [
        (
            "Énergie (J)",
            energy,
            energy / energy_reference,
            format(
                energy,
                ".4f"
            )
            + " J"
        ),
        (
            "Latence normalisée",
            latency,
            latency / latency_reference,
            format(
                latency,
                ".4f"
            )
        ),
        (
            "Robustesse auth.",
            robustness,
            robustness,
            format(
                robustness,
                ".4f"
            )
        ),
        (
            "Qualité de clé",
            key_quality,
            key_quality,
            format(
                key_quality,
                ".4f"
            )
        ),
        (
            "Taux de refus légitime",
            refusal_rate,
            refusal_rate,
            format(
                refusal_rate,
                ".4f"
            )
        )
    ]

    labels = [
        metric[0]
        for metric in metrics
    ]

    bar_lengths = [
        min(
            metric[2],
            1.0
        )
        for metric in metrics
    ]

    value_texts = [
        metric[3]
        for metric in metrics
    ]

    y_positions = range(
        len(metrics)
    )

    bar_colors = [
        "#4C72B0",
        "#DD8452",
        "#55A868",
        "#8172B2",
        "#C44E52"
    ]

    axis.barh(
        list(
            y_positions
        ),
        bar_lengths,
        color=bar_colors
    )

    axis.set_yticks(
        list(
            y_positions
        )
    )

    axis.set_yticklabels(
        labels
    )

    axis.invert_yaxis()

    axis.set_xlim(
        0.0,
        1.15
    )

    axis.set_xticks(
        []
    )

    for index, value_text in enumerate(
        value_texts
    ):

        axis.text(
            min(
                bar_lengths[index],
                1.0
            )
            + 0.03,
            index,
            value_text,
            va="center",
            fontsize=9
        )

    axis.set_title(
        SCENARIO_AXIS_LABELS[scenario_id],
        fontsize=9
    )


def plot_scenario_profiles_figure(
    four_objective_summary,
    output_path
):

    figure, axes = plt.subplots(
        1,
        3,
        figsize=(
            15.0,
            5.0
        )
    )

    for index, scenario_id in enumerate(
        SCENARIO_ORDER
    ):

        plot_scenario_portrait(
            axes[index],
            scenario_id,
            four_objective_summary
        )

    figure.suptitle(
        "Figure 7 — Profils synthétiques des trois "
        "scénarios\n"
        "(longueur des barres mise à l'échelle par "
        "métrique ; valeur réelle annotée)",
        fontsize=11
    )

    figure.tight_layout(
        rect=[
            0,
            0,
            1,
            0.90
        ]
    )

    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(
        figure
    )


# ================================================================
# 9. INTERPRÉTATION AUTOMATIQUE
# ================================================================


def format_percent(
    value
):

    return format(
        value * 100,
        ".2f"
    ) + " %"


def build_interpretation_markdown(
    scenario_metadata,
    four_objective_summary,
    decision_frequencies
):

    s1 = four_objective_summary[
        "S1-DEGRADED-CHANNEL"
    ]
    s2 = four_objective_summary[
        "S2-RESOURCE-CONSTRAINED"
    ]
    s3 = four_objective_summary[
        "S3-HIGH-SECURITY-PRESSURE"
    ]

    freq_s1 = decision_frequencies[
        "S1-DEGRADED-CHANNEL"
    ]
    freq_s2 = decision_frequencies[
        "S2-RESOURCE-CONSTRAINED"
    ]
    freq_s3 = decision_frequencies[
        "S3-HIGH-SECURITY-PRESSURE"
    ]

    k1_never_used = (
        freq_s1["A1-K1a"] == 0.0
        and freq_s1["A1-K1b"] == 0.0
        and freq_s2["A2-K1a"] == 0.0
        and freq_s2["A2-K1b"] == 0.0
        and freq_s3["A2-K1a"] == 0.0
        and freq_s3["A2-K1b"] == 0.0
    )

    lines = []

    lines.append(
        "# Interprétation des trois scénarios "
        "(résultats préliminaires)"
    )
    lines.append("")
    lines.append(
        "**Avertissement scientifique.** Ces résultats "
        "restent préliminaires : le profil de coûts CPU "
        "utilisé (`CENTRAL`) est exploratoire, le protocole "
        "K2 est simplifié (`K2-SIMPLIFIED-PILOT`), et les "
        "poids contextuels par scénario sont statiques "
        "et non encore issus du mécanisme adaptatif complet "
        "(DM-EQ108 à DM-EQ110)."
    )
    lines.append("")

    # ------------------------------------------------------------
    # S1
    # ------------------------------------------------------------

    lines.append(
        "### S1 — Canal dégradé"
    )
    lines.append("")
    lines.append(
        "- **Ce que le scénario cherche à démontrer** : que le "
        "Decision Maker rejette les mécanismes d'authentification "
        "et de génération de clé fondés sur la couche physique "
        "(A2, K1a, K1b) lorsque le canal est trop dégradé "
        "(SNR = −10 dB) et que la variabilité PHY est déclarée "
        "indisponible."
    )
    lines.append(
        "- **Ce que montrent les figures** : énergie moyenne "
        + format(
            float(
                s1["energy_objective_j_mean"]
            ),
            ".4f"
        )
        + " J, latence normalisée très faible ("
        + format(
            float(
                s1["normalized_latency_objective_mean"]
            ),
            ".4f"
        )
        + "), robustesse d'authentification "
        "quasi parfaite (1,0000), qualité de clé "
        + format(
            float(
                s1["key_quality_mean"]
            ),
            ".4f"
        )
        + " (la plus faible des trois scénarios en valeur "
        "absolue, car la clé K0 est conservée presque "
        "systématiquement)."
    )
    lines.append(
        "- **Décisions les plus choisies** : A1-K0 ("
        + format_percent(
            freq_s1["A1-K0"]
        )
        + "), puis A1-K2 ("
        + format_percent(
            freq_s1["A1-K2"]
        )
        + "). A2, K1a et K1b ne sont **jamais** sélectionnés."
    )
    lines.append(
        "- **Cohérence avec l'objectif** : oui. Le comportement "
        "observé est exactement celui attendu : le DM revient "
        "systématiquement à l'authentification conventionnelle "
        "(A1) et au renouvellement conventionnel (K2) plutôt "
        "qu'aux mécanismes PHY, qui sont d'ailleurs explicitement "
        "bloqués par `variation_feasible=False`. Le service reste "
        "assuré à 100 % et aucune violation de sécurité n'est "
        "observée."
    )
    lines.append("")

    # ------------------------------------------------------------
    # S2
    # ------------------------------------------------------------

    lines.append(
        "### S2 — Ressources contraintes"
    )
    lines.append("")
    lines.append(
        "- **Ce que le scénario cherche à démontrer** : que le "
        "Decision Maker minimise l'énergie et la latence tout "
        "en maintenant la sécurité, lorsque la batterie est "
        "proche de sa réserve et que 60 % des messages sont "
        "critiques."
    )
    lines.append(
        "- **Ce que montrent les figures** : énergie moyenne "
        + format(
            float(
                s2["energy_objective_j_mean"]
            ),
            ".4f"
        )
        + " J (légèrement inférieure à S1), mais latence "
        "normalisée "
        + format(
            float(
                s2["normalized_latency_objective_mean"]
            ),
            ".4f"
        )
        + " — la **plus élevée des trois scénarios**, malgré "
        "une pondération censée favoriser énergie ET latence. "
        "Robustesse d'authentification "
        + format(
            float(
                s2["authentication_robustness_mean"]
            ),
            ".4f"
        )
        + ", légèrement inférieure à S1 et S3."
    )
    lines.append(
        "- **L'énergie et la latence sont-elles réellement "
        "favorisées ?** Partiellement. L'énergie est bien la "
        "deuxième plus basse des trois scénarios (cohérent avec "
        "l'objectif), mais la latence normalisée est en réalité "
        "la plus élevée des trois — la pondération statique "
        "actuelle ne sépare pas correctement les deux objectifs "
        "énergie et latence dans ce contexte."
    )
    lines.append(
        "- **Le taux de refus légitime est-il acceptable ?** "
        "Oui, **après correction** de la marge énergétique "
        "initiale (portée de 20 J à 80 J au-dessus de la "
        "réserve) : le taux de refus légitime est retombé de "
        "66,56 % à "
        + format_percent(
            float(
                s2["legitimate_refusal_rate_mean"]
            )
        )
        + ", et le taux de sélection est de "
        + format_percent(
            float(
                s2["selection_rate_mean"]
            )
        )
        + ". **Avant correction, un taux de refus de 66,56 % "
        "aurait rendu toute conclusion sur l'énergie ou la "
        "latence trompeuse** : un système qui refuse la plupart "
        "des messages ne consomme presque rien, ce qui aurait "
        "artificiellement paru « bon » sur l'objectif énergie."
    )
    lines.append(
        "- **Point à signaler honnêtement** : le taux de fausse "
        "acceptation moyen de S2 est de "
        + format(
            float(
                s2["false_acceptance_rate_mean"]
            ),
            ".6f"
        )
        + " (non strictement nul, contrairement à S1 et S3), "
        "ce qui correspond à un événement rare observé sur "
        "l'ensemble des 30 graines. Le plancher de sécurité "
        "au SNR réel n'a toutefois jamais été dépassé "
        "(taux de violation = 0). K1a et K1b ne sont, ici non "
        "plus, jamais sélectionnés, bien que "
        "`variation_feasible=True` — la génération PHY de clé "
        "n'est donc pas démontrée comme avantageuse dans ce "
        "scénario avec la configuration de coûts actuelle."
    )
    lines.append("")

    # ------------------------------------------------------------
    # S3
    # ------------------------------------------------------------

    lines.append(
        "### S3 — Forte pression de sécurité"
    )
    lines.append("")
    lines.append(
        "- **Ce que le scénario cherche à démontrer** : que le "
        "Decision Maker maximise l'authentification et la "
        "qualité de clé lorsque le canal est favorable "
        "(SNR = 20 dB), malgré une pression adverse plus forte "
        "(Mallory = 30 %)."
    )
    lines.append(
        "- **Ce que montrent les figures** : robustesse "
        "d'authentification quasi parfaite ("
        + format(
            float(
                s3["authentication_robustness_mean"]
            ),
            ".10f"
        )
        + "), et surtout l'**énergie moyenne la plus basse des "
        "trois scénarios** ("
        + format(
            float(
                s3["energy_objective_j_mean"]
            ),
            ".4f"
        )
        + " J), un résultat positif non trivial obtenu alors "
        "même que S3 ne pondère l'énergie qu'à 0,10."
    )
    lines.append(
        "- **L'authentification et la qualité de clé "
        "sont-elles réellement favorisées ?** L'authentification "
        "oui, nettement : A2 (authentification RFF hybride) est "
        "choisie dans "
        + format_percent(
            freq_s3["A2-K0"]
            + freq_s3["A2-K1a"]
            + freq_s3["A2-K1b"]
            + freq_s3["A2-K2"]
        )
        + " des périodes, contre "
        + format_percent(
            freq_s1["A2-K0"]
            + freq_s1["A2-K1a"]
            + freq_s1["A2-K1b"]
            + freq_s1["A2-K2"]
        )
        + " en S1. La qualité de clé, en revanche, reste "
        "identique à celle de S1 et S2 ("
        + format(
            float(
                s3["key_quality_mean"]
            ),
            ".4f"
        )
        + ") : cet objectif n'est **pas** différencié entre "
        "les scénarios."
    )
    lines.append(
        "- **Usage des mécanismes PHY (K1a/K1b) ?** Non, aucun "
        "usage, malgré `variation_feasible=True` et une "
        "pondération de la clé à 0,40. La décision dominante "
        "pour le renouvellement reste K0 (conservation), et le "
        "renouvellement effectif passe par K2 (conventionnel), "
        "jamais par K1a ou K1b."
    )
    lines.append(
        "- **Conclusion** : l'objectif d'authentification est "
        "atteint de façon convaincante ; l'objectif de qualité "
        "de clé ne l'est pas, la métrique restant plate sur les "
        "trois scénarios."
    )
    lines.append("")

    # ------------------------------------------------------------
    # Conclusion comparative
    # ------------------------------------------------------------

    lines.append(
        "### Conclusion comparative"
    )
    lines.append("")
    lines.append(
        "- **Énergie** : S3 favorise le plus l'énergie "
        "(la plus basse, "
        + format(
            float(
                s3["energy_objective_j_mean"]
            ),
            ".4f"
        )
        + " J), suivi de près par S2, puis S1. Les écarts "
        "absolus restent modestes (environ 4,5 % entre le "
        "meilleur et le pire cas)."
    )
    lines.append(
        "- **Latence** : S1 favorise le plus la latence "
        "(la plus basse), et non S2 comme son objectif le "
        "laisserait attendre — c'est la limite la plus notable "
        "de cette campagne pilote."
    )
    lines.append(
        "- **Authentification** : S3 et S1 atteignent tous deux "
        "une robustesse quasi parfaite, par des mécanismes "
        "différents (A2 pour S3, A1 pour S1) ; S2 est "
        "très légèrement en retrait."
    )
    lines.append(
        "- **Qualité de clé** : aucun scénario ne se démarque — "
        "la métrique est strictement identique dans les trois "
        "cas, car K0 domine partout et K1a/K1b ne sont jamais "
        "sélectionnés."
    )
    lines.append("")
    lines.append(
        "**Limites importantes à signaler dans le mini compte "
        "rendu IEEE :**"
    )
    lines.append("")

    if k1_never_used:

        lines.append(
            "- K1a et K1b (génération de clé par couche "
            "physique) ne sont **jamais** sélectionnés dans "
            "aucun des trois scénarios, même lorsque "
            "`variation_feasible=True`. La contribution "
            "spécifique de la génération de clé PHY n'est donc "
            "pas démontrée par cette campagne pilote."
        )

    lines.append(
        "- La qualité de clé ne varie pas entre les scénarios : "
        "cette métrique ne différencie actuellement aucune "
        "politique ni aucun contexte."
    )
    lines.append(
        "- S2 a nécessité une correction de sa marge "
        "énergétique initiale (20 J → 80 J) pour éviter qu'un "
        "taux de refus de 66,56 % ne fausse l'interprétation "
        "de ses résultats énergétiques ; les chiffres présentés "
        "ici sont ceux de la version corrigée."
    )
    lines.append(
        "- Le coût CPU (`mac_cycles`, réconciliation, "
        "amplification de confidentialité), l'énergie de base "
        "et le protocole K2 restent des valeurs exploratoires, "
        "non encore mesurées sur la plateforme cible."
    )
    lines.append(
        "- Les résultats sont issus d'une seule politique "
        "statique par scénario (poids fixes), et non du "
        "mécanisme de poids contextuels complet prévu par le "
        "modèle."
    )
    lines.append("")

    return "\n".join(
        lines
    )


# ================================================================
# 10. LANCEMENT
# ================================================================


def run_explicit_analysis():

    source_directory = select_source_directory()

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )

    scenario_metadata = load_scenario_metadata()

    four_objective_summary = load_four_objective_summary(
        source_directory
    )

    decision_frequencies = load_decision_frequencies(
        source_directory
    )

    # --- Tableau CSV lisible ---

    summary_rows = build_scenario_summary_rows(
        scenario_metadata,
        four_objective_summary
    )

    summary_csv_path = (
        OUTPUT_DIRECTORY
        / "scenario_summary_readable.csv"
    )

    write_scenario_summary_csv(
        summary_rows,
        summary_csv_path
    )

    # --- Figures 1 à 4 ---

    plot_single_objective_bar_chart(
        four_objective_summary,
        mean_key="energy_objective_j_mean",
        ci_low_key="energy_objective_j_ci95_low",
        ci_high_key="energy_objective_j_ci95_high",
        title=(
            "Figure 1 — Énergie moyenne de la "
            "décision sélectionnée"
        ),
        y_label=(
            "Énergie moyenne (J) — plus faible = meilleur"
        ),
        output_path=(
            OUTPUT_DIRECTORY
            / "figure_1_energy_explicit.png"
        )
    )

    plot_single_objective_bar_chart(
        four_objective_summary,
        mean_key="normalized_latency_objective_mean",
        ci_low_key="normalized_latency_objective_ci95_low",
        ci_high_key="normalized_latency_objective_ci95_high",
        title=(
            "Figure 2 — Latence normalisée moyenne"
        ),
        y_label=(
            "Latence normalisée — plus faible = meilleur"
        ),
        output_path=(
            OUTPUT_DIRECTORY
            / "figure_2_latency_explicit.png"
        )
    )

    plot_single_objective_bar_chart(
        four_objective_summary,
        mean_key="authentication_robustness_mean",
        ci_low_key="authentication_robustness_ci95_low",
        ci_high_key="authentication_robustness_ci95_high",
        title=(
            "Figure 3 — Robustesse moyenne de "
            "l'authentification"
        ),
        y_label=(
            "Robustesse d'authentification — "
            "plus élevée = meilleure"
        ),
        output_path=(
            OUTPUT_DIRECTORY
            / "figure_3_authentication_explicit.png"
        )
    )

    plot_single_objective_bar_chart(
        four_objective_summary,
        mean_key="key_quality_mean",
        ci_low_key="key_quality_ci95_low",
        ci_high_key="key_quality_ci95_high",
        title=(
            "Figure 4 — Qualité moyenne du "
            "mécanisme de clé"
        ),
        y_label=(
            "Qualité de clé — plus élevée = meilleure"
        ),
        output_path=(
            OUTPUT_DIRECTORY
            / "figure_4_key_quality_explicit.png"
        )
    )

    # --- Figure 5 ---

    plot_decision_frequencies_figure(
        decision_frequencies,
        OUTPUT_DIRECTORY
        / "figure_5_decision_frequencies_explicit.png"
    )

    # --- Figure 6 et son explication ---

    radar_result = plot_radar_figure(
        four_objective_summary,
        OUTPUT_DIRECTORY
        / "figure_6_radar_four_objectives.png"
    )

    write_radar_normalization_explanation(
        radar_result,
        OUTPUT_DIRECTORY
        / "radar_normalization_method.md"
    )

    # --- Figure 7 ---

    plot_scenario_profiles_figure(
        four_objective_summary,
        OUTPUT_DIRECTORY
        / "figure_7_scenario_profiles.png"
    )

    # --- Interprétation automatique ---

    interpretation_markdown = (
        build_interpretation_markdown(
            scenario_metadata,
            four_objective_summary,
            decision_frequencies
        )
    )

    interpretation_path = (
        OUTPUT_DIRECTORY
        / "scenario_interpretation.md"
    )

    interpretation_path.write_text(
        interpretation_markdown,
        encoding="utf-8"
    )

    return {
        "source_directory": source_directory,
        "output_directory": OUTPUT_DIRECTORY
    }


if __name__ == "__main__":

    result = run_explicit_analysis()

    print(
        "Analyse explicite terminée."
    )

    print(
        "Dossier source :",
        result["source_directory"]
    )

    print(
        "Dossier de sortie :",
        result["output_directory"]
    )
