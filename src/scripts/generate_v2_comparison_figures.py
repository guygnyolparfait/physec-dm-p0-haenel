# Génère les 5 figures de comparaison des quatre objectifs pour la
# version COMPLEXIFIÉE de S1-S5, dans le même style visuel que les
# figures V2 originales : réutilise telle quelle la fonction
# figure_four_objectives_comparison_v2, sans dupliquer sa logique
# de tracé.
#
# Ce script ne relance aucune simulation : il lit uniquement
# results/five_case_studies_v2_complex_adaptive/five_case_studies_v2_log.csv,
# déjà produit par run_five_case_studies_v2_adaptive.py. Il calcule
# moyenne et IC95 par graine puis entre graines (jamais sur les
# lignes brutes), exactement la même règle statistique que pour la
# campagne originale.
import csv
import statistics
from collections import defaultdict
from pathlib import Path

from scripts.generate_four_objective_scenario_figures_v2 import (
    METRIC_COLUMNS,
    POLICY_IDS,
    figure_four_objectives_comparison_v2
)

from scripts import analyze_five_case_studies
from scripts import generate_four_objective_scenario_figures_v2 as v2_module


V2_LOG_PATH = Path(
    "results/five_case_studies_v2_complex_adaptive"
    "/five_case_studies_v2_log.csv"
)

SCENARIO_IDS = [
    "S1-REMOTE-AGRICULTURAL-SENSOR",
    "S2-INDUSTRIAL-CRITICAL-ALARM",
    "S3-MOBILE-VEHICLE",
    "S4-DENSE-URBAN-NETWORK",
    "S5-CRITICAL-INFRASTRUCTURE-ATTACK"
]

OUTPUT_DIR = Path(
    "results/five_case_studies_v2_complex_adaptive/figures"
)
DATA_DIR = Path(
    "results/five_case_studies_v2_complex_adaptive/data"
)


def compute_seed_summary(rows):

    served_rows = [
        row
        for row in rows
        if row["legitimate_message_served"] == "True"
    ]

    service_rate = len(served_rows) / len(rows)

    def mean_of(field_name):

        values = [
            float(row[field_name])
            for row in served_rows
            if row[field_name] not in (None, "", "None")
        ]

        return sum(values) / len(values) if values else None

    mallory_attempts = [
        row for row in rows if row["mallory_attempted"] == "True"
    ]

    mallory_accepted = [
        row for row in mallory_attempts
        if row["mallory_accepted"] == "True"
    ]

    return {
        "service_rate": service_rate,
        "mean_energy_j": mean_of("energy_objective_j"),
        "mean_latency_objective": mean_of("latency_objective"),
        "mean_authentication_robustness": mean_of(
            "authentication_robustness"
        ),
        "mean_key_quality": mean_of("key_quality"),
        "far_accepted_count": len(mallory_accepted),
        "mallory_attempts_count": len(mallory_attempts)
    }


def confidence_interval_95(values):

    n = len(values)
    mean_value = statistics.mean(values)

    if n < 2:

        return mean_value, 0.0

    standard_error = statistics.stdev(values) / (n ** 0.5)

    return mean_value, 1.96 * standard_error


def main(lang="fr"):

    # lang="fr" (par defaut) reproduit exactement le comportement
    # d'origine (article/rapport/PowerPoint francais). lang="en" ne
    # change que le texte affiche sur les figures (voir
    # figure_four_objectives_comparison_v2) ; les memes lignes du
    # meme journal brut sont relues et agregees de la meme maniere.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    v2_module.FIGURES_MAIN_DIR = OUTPUT_DIR

    rows_by_scenario_policy_seed = defaultdict(
        lambda: defaultdict(list)
    )

    with V2_LOG_PATH.open(encoding="utf-8") as csv_file:

        reader = csv.DictReader(csv_file)

        for row in reader:

            key = (row["scenario_id"], row["policy_id"])
            rows_by_scenario_policy_seed[key][
                row["seed"]
            ].append(row)

    all_summary_rows = []
    all_paired_rows = []
    text_summary_lines = []

    for scenario_id in SCENARIO_IDS:

        seed_summaries_by_policy = {}

        for policy_id in POLICY_IDS:

            rows_by_seed = rows_by_scenario_policy_seed[
                (scenario_id, policy_id)
            ]

            seed_summaries_by_policy[policy_id] = {
                seed: compute_seed_summary(rows)
                for seed, rows in rows_by_seed.items()
            }

        seed_count = len(
            seed_summaries_by_policy[POLICY_IDS[0]]
        )

        summary_rows = []

        for policy_id in POLICY_IDS:

            seed_summaries = list(
                seed_summaries_by_policy[policy_id].values()
            )

            row = {
                "scenario_id": scenario_id,
                "policy_id": policy_id,
                "seed_count": str(seed_count)
            }

            for metric_key, _ in METRIC_COLUMNS:

                values = [
                    s[metric_key]
                    for s in seed_summaries
                    if s[metric_key] is not None
                ]

                mean_value, half_width = (
                    confidence_interval_95(values)
                    if values else (None, None)
                )

                row[metric_key + "_mean"] = str(mean_value)
                row[metric_key + "_ci95_half_width"] = str(
                    half_width
                )

            service_values = [
                s["service_rate"] for s in seed_summaries
            ]
            service_mean, service_half_width = (
                confidence_interval_95(service_values)
            )
            row["service_rate_mean"] = str(service_mean)
            row["service_rate_ci95_half_width"] = str(
                service_half_width
            )

            far_accepted_total = sum(
                s["far_accepted_count"]
                for s in seed_summaries
            )
            mallory_attempts_total = sum(
                s["mallory_attempts_count"]
                for s in seed_summaries
            )
            far_proportions = [
                (
                    s["far_accepted_count"]
                    / s["mallory_attempts_count"]
                )
                if s["mallory_attempts_count"] > 0 else 0.0
                for s in seed_summaries
            ]
            far_mean, far_half_width = (
                confidence_interval_95(far_proportions)
            )
            row["far_accepted_count"] = str(
                far_accepted_total
            )
            row["mallory_attempts_count"] = str(
                mallory_attempts_total
            )
            row["far_proportion_mean"] = str(far_mean)
            row["far_proportion_ci95_half_width"] = str(
                far_half_width
            )

            summary_rows.append(row)
            all_summary_rows.append(row)

        p0_seed_summaries = seed_summaries_by_policy[
            POLICY_IDS[0]
        ]
        b1_seed_summaries = seed_summaries_by_policy[
            "B1-CONVENTIONAL"
        ]

        common_seeds = sorted(
            set(p0_seed_summaries.keys())
            & set(b1_seed_summaries.keys())
        )

        paired_rows = []

        for metric_key, _ in METRIC_COLUMNS:

            differences = [
                p0_seed_summaries[seed][metric_key]
                - b1_seed_summaries[seed][metric_key]
                for seed in common_seeds
                if p0_seed_summaries[seed][metric_key]
                is not None
                and b1_seed_summaries[seed][metric_key]
                is not None
            ]

            mean_difference, half_width = (
                confidence_interval_95(differences)
            )

            lower_bound = mean_difference - half_width
            upper_bound = mean_difference + half_width
            excludes_zero = (
                lower_bound > 0.0 or upper_bound < 0.0
            )

            paired_row = {
                "scenario_id": scenario_id,
                "baseline_policy_id": "B1-CONVENTIONAL",
                "metric_name": metric_key,
                "mean_difference_p0_minus_baseline": str(
                    mean_difference
                ),
                "excludes_zero": str(excludes_zero)
            }

            paired_rows.append(paired_row)
            all_paired_rows.append(paired_row)

        analyze_five_case_studies.SCENARIO_FULL_NAMES[
            scenario_id
        ] = analyze_five_case_studies.scenario_full_name(
            scenario_id
        )

        result = figure_four_objectives_comparison_v2(
            scenario_id, summary_rows, paired_rows, lang=lang
        )

        text_summary_lines.append(
            "=== " + scenario_id
            + " (n=" + str(seed_count) + " graines) ==="
        )

        for metric_key, description in (
            result["annotations"].items()
        ):

            text_summary_lines.append(
                "  " + metric_key + " -> " + description
            )

        for policy_id in POLICY_IDS:

            row = next(
                r for r in summary_rows
                if r["policy_id"] == policy_id
            )

            text_summary_lines.append(
                "  "
                + policy_id
                + " service="
                + row["service_rate_mean"][:6]
                + " energy="
                + row["mean_energy_j_mean"][:8]
                + " latency="
                + row["mean_latency_objective_mean"][:8]
                + " robust="
                + row["mean_authentication_robustness_mean"][
                    :8
                ]
                + " keyq="
                + row["mean_key_quality_mean"][:8]
                + " far="
                + row["far_proportion_mean"][:8]
            )

    with (DATA_DIR / "summary_by_scenario_policy_v2.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f, fieldnames=list(all_summary_rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(all_summary_rows)

    with (DATA_DIR / "paired_statistics_vs_p0_v2.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f, fieldnames=list(all_paired_rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(all_paired_rows)

    summary_text = "\n".join(text_summary_lines)

    print(summary_text)

    (DATA_DIR / "text_summary_v2.txt").write_text(
        summary_text, encoding="utf-8"
    )


if __name__ == "__main__":

    main()
