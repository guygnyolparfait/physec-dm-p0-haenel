# Ce script calcule, à partir du journal détaillé de la
# campagne complète (results/five_case_studies_final/
# five_case_studies_log.csv), les statistiques demandées :
# moyennes et IC 95 %, séparément par scénario, par politique
# et par phase, ainsi qu'une vérification ciblée du duty-cycle
# de S5. Il ne relance aucune mission et ne modifie aucun
# résultat existant.
import csv
import math
from pathlib import Path

from analyze_five_case_studies import (
    SCENARIO_FULL_NAMES,
    compute_scenario_policy_summary,
    get_phase_segments_in_steps,
    load_log,
    scenario_full_name
)

from physec_dm.case_studies import build_five_case_studies


LOG_PATH = Path(
    "results/five_case_studies_final/"
    "five_case_studies_log.csv"
)

OUTPUT_DIRECTORY = Path(
    "results/five_case_studies_final"
)

MAX_STEPS = 1500

METRIC_FIELDS = [
    ("energy_objective_j", "energy"),
    ("latency_objective", "latency"),
    ("authentication_robustness", "authentication"),
    ("key_quality", "key_quality")
]


def mean_and_ci95(values):

    sample_size = len(values)

    if sample_size == 0:

        return 0.0, 0.0, 0.0

    mean = sum(values) / sample_size

    if sample_size > 1:

        variance = sum(
            (value - mean) ** 2
            for value in values
        ) / (sample_size - 1)

        standard_error = math.sqrt(
            variance / sample_size
        )

    else:

        standard_error = 0.0

    margin = 1.96 * standard_error

    return mean, mean - margin, mean + margin


# ================================================================
# 1. RÉSUMÉ PAR SCÉNARIO ET PAR POLITIQUE (déjà présent dans
#    compute_scenario_policy_summary, complété ici par les IC 95 %
#    des quatre objectifs).
# ================================================================


def compute_summary_with_ci(
    rows,
    scenario_id,
    policy_id
):

    summary = compute_scenario_policy_summary(
        rows,
        scenario_id,
        policy_id
    )

    scenario_rows = [
        row
        for row in rows
        if row["scenario_id"] == scenario_id
        and row["policy_id"] == policy_id
    ]

    for field, short_name in METRIC_FIELDS:

        values = [
            row[field]
            for row in scenario_rows
            if row[field] is not None
        ]

        mean, ci_low, ci_high = mean_and_ci95(
            values
        )

        summary[short_name + "_mean"] = mean
        summary[short_name + "_ci95_low"] = ci_low
        summary[short_name + "_ci95_high"] = ci_high

    return summary


def export_summary_by_scenario_policy(
    rows,
    case_studies
):

    fieldnames = [
        "scenario_id",
        "scenario_name",
        "policy_id",
        "energy_mean",
        "energy_ci95_low",
        "energy_ci95_high",
        "latency_mean",
        "latency_ci95_low",
        "latency_ci95_high",
        "authentication_mean",
        "authentication_ci95_low",
        "authentication_ci95_high",
        "key_quality_mean",
        "key_quality_ci95_low",
        "key_quality_ci95_high",
        "service_rate",
        "refusal_rate",
        "far",
        "violation_rate",
        "activations_k1a",
        "activations_k1b",
        "activations_k2"
    ]

    output_rows = []

    for case_study in case_studies:

        scenario_id = case_study["scenario_id"]

        for policy_id in [
            "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS",
            "B1-CONVENTIONAL"
        ]:

            summary = compute_summary_with_ci(
                rows,
                scenario_id,
                policy_id
            )

            output_rows.append(
                {
                    "scenario_id": scenario_id,
                    "scenario_name": (
                        scenario_full_name(
                            scenario_id
                        )
                    ),
                    "policy_id": policy_id,
                    "energy_mean": (
                        summary["energy_mean"]
                    ),
                    "energy_ci95_low": summary[
                        "energy_ci95_low"
                    ],
                    "energy_ci95_high": summary[
                        "energy_ci95_high"
                    ],
                    "latency_mean": summary[
                        "latency_mean"
                    ],
                    "latency_ci95_low": summary[
                        "latency_ci95_low"
                    ],
                    "latency_ci95_high": summary[
                        "latency_ci95_high"
                    ],
                    "authentication_mean": (
                        summary[
                            "authentication_mean"
                        ]
                    ),
                    "authentication_ci95_low": (
                        summary[
                            "authentication_"
                            "ci95_low"
                        ]
                    ),
                    "authentication_ci95_high": (
                        summary[
                            "authentication_"
                            "ci95_high"
                        ]
                    ),
                    "key_quality_mean": summary[
                        "key_quality_mean"
                    ],
                    "key_quality_ci95_low": (
                        summary[
                            "key_quality_ci95_low"
                        ]
                    ),
                    "key_quality_ci95_high": (
                        summary[
                            "key_quality_ci95_high"
                        ]
                    ),
                    "service_rate": summary[
                        "service_rate"
                    ],
                    "refusal_rate": summary[
                        "refusal_rate"
                    ],
                    "far": summary["far"],
                    "violation_rate": summary[
                        "violation_rate"
                    ],
                    "activations_k1a": summary[
                        "activation_counts"
                    ]["K1a"],
                    "activations_k1b": summary[
                        "activation_counts"
                    ]["K1b"],
                    "activations_k2": summary[
                        "activation_counts"
                    ]["K2"]
                }
            )

    output_path = (
        OUTPUT_DIRECTORY
        / "summary_by_scenario_policy.csv"
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(output_rows)

    return output_rows


# ================================================================
# 2. RÉSUMÉ PAR SCÉNARIO, POLITIQUE ET PHASE
# ================================================================


def export_summary_by_phase(
    rows,
    case_studies
):

    fieldnames = [
        "scenario_id",
        "scenario_name",
        "policy_id",
        "phase_name",
        "start_step",
        "end_step",
        "energy_mean",
        "energy_ci95_low",
        "energy_ci95_high",
        "latency_mean",
        "latency_ci95_low",
        "latency_ci95_high",
        "authentication_mean",
        "authentication_ci95_low",
        "authentication_ci95_high",
        "key_quality_mean",
        "key_quality_ci95_low",
        "key_quality_ci95_high",
        "service_rate",
        "refusal_rate",
        "duty_cycle_min_s"
    ]

    output_rows = []

    for case_study in case_studies:

        scenario_id = case_study["scenario_id"]

        phase_segments = (
            get_phase_segments_in_steps(
                case_study,
                MAX_STEPS
            )
        )

        for policy_id in [
            "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS",
            "B1-CONVENTIONAL"
        ]:

            policy_rows = [
                row
                for row in rows
                if row["scenario_id"]
                == scenario_id
                and row["policy_id"]
                == policy_id
            ]

            for segment in phase_segments:

                phase_rows = [
                    row
                    for row in policy_rows
                    if segment["start_step"]
                    <= row["step_index"]
                    < segment["end_step"]
                    or (
                        segment
                        is phase_segments[-1]
                        and row["step_index"]
                        == segment["end_step"]
                    )
                ]

                if len(phase_rows) == 0:

                    continue

                total = len(phase_rows)

                served = sum(
                    1
                    for row in phase_rows
                    if row[
                        "legitimate_message_"
                        "served"
                    ]
                )

                duty_cycle_min = min(
                    row[
                        "remaining_duty_cycle_"
                        "airtime_s"
                    ]
                    for row in phase_rows
                )

                metric_values = {}

                for field, short_name in (
                    METRIC_FIELDS
                ):

                    values = [
                        row[field]
                        for row in phase_rows
                        if row[field] is not None
                    ]

                    mean, ci_low, ci_high = (
                        mean_and_ci95(values)
                    )

                    metric_values[short_name] = (
                        mean,
                        ci_low,
                        ci_high
                    )

                output_rows.append(
                    {
                        "scenario_id": scenario_id,
                        "scenario_name": (
                            scenario_full_name(
                                scenario_id
                            )
                        ),
                        "policy_id": policy_id,
                        "phase_name": segment[
                            "phase_name"
                        ],
                        "start_step": segment[
                            "start_step"
                        ],
                        "end_step": segment[
                            "end_step"
                        ],
                        "energy_mean": (
                            metric_values[
                                "energy"
                            ][0]
                        ),
                        "energy_ci95_low": (
                            metric_values[
                                "energy"
                            ][1]
                        ),
                        "energy_ci95_high": (
                            metric_values[
                                "energy"
                            ][2]
                        ),
                        "latency_mean": (
                            metric_values[
                                "latency"
                            ][0]
                        ),
                        "latency_ci95_low": (
                            metric_values[
                                "latency"
                            ][1]
                        ),
                        "latency_ci95_high": (
                            metric_values[
                                "latency"
                            ][2]
                        ),
                        "authentication_mean": (
                            metric_values[
                                "authentication"
                            ][0]
                        ),
                        "authentication_"
                        "ci95_low": (
                            metric_values[
                                "authentication"
                            ][1]
                        ),
                        "authentication_"
                        "ci95_high": (
                            metric_values[
                                "authentication"
                            ][2]
                        ),
                        "key_quality_mean": (
                            metric_values[
                                "key_quality"
                            ][0]
                        ),
                        "key_quality_ci95_low": (
                            metric_values[
                                "key_quality"
                            ][1]
                        ),
                        "key_quality_ci95_high": (
                            metric_values[
                                "key_quality"
                            ][2]
                        ),
                        "service_rate": (
                            served / total
                        ),
                        "refusal_rate": (
                            1 - served / total
                        ),
                        "duty_cycle_min_s": (
                            duty_cycle_min
                        )
                    }
                )

    output_path = (
        OUTPUT_DIRECTORY
        / "summary_by_scenario_policy_phase.csv"
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(output_rows)

    return output_rows


# ================================================================
# 3. VÉRIFICATION CIBLÉE DU DUTY-CYCLE DE S5
# ================================================================


def export_s5_duty_cycle_check(
    rows
):

    scenario_id = (
        "S5-CRITICAL-INFRASTRUCTURE-ATTACK"
    )

    fieldnames = [
        "policy_id",
        "seed",
        "min_duty_cycle_airtime_s",
        "step_index_of_min",
        "phase_name_of_min",
        "periods_below_1s",
        "periods_below_2s",
        "total_periods",
        "any_negative"
    ]

    case_studies = {
        case_study["scenario_id"]: case_study
        for case_study in build_five_case_studies()
    }

    phase_segments = get_phase_segments_in_steps(
        case_studies[scenario_id],
        MAX_STEPS
    )

    def phase_name_for_step(step_index):

        for segment in phase_segments:

            if (
                segment["start_step"]
                <= step_index
                < segment["end_step"]
            ):

                return segment["phase_name"]

        return phase_segments[-1]["phase_name"]

    output_rows = []

    for policy_id in [
        "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS",
        "B1-CONVENTIONAL"
    ]:

        seeds = sorted(
            set(
                row["seed"]
                for row in rows
                if row["scenario_id"]
                == scenario_id
                and row["policy_id"]
                == policy_id
            )
        )

        for seed in seeds:

            seed_rows = [
                row
                for row in rows
                if row["scenario_id"]
                == scenario_id
                and row["policy_id"]
                == policy_id
                and row["seed"] == seed
            ]

            min_row = min(
                seed_rows,
                key=lambda row: row[
                    "remaining_duty_cycle_"
                    "airtime_s"
                ]
            )

            below_1s = sum(
                1
                for row in seed_rows
                if row[
                    "remaining_duty_cycle_"
                    "airtime_s"
                ]
                < 1.0
            )

            below_2s = sum(
                1
                for row in seed_rows
                if row[
                    "remaining_duty_cycle_"
                    "airtime_s"
                ]
                < 2.0
            )

            any_negative = any(
                row[
                    "remaining_duty_cycle_"
                    "airtime_s"
                ]
                < 0.0
                for row in seed_rows
            )

            output_rows.append(
                {
                    "policy_id": policy_id,
                    "seed": seed,
                    "min_duty_cycle_airtime_s": (
                        min_row[
                            "remaining_duty_"
                            "cycle_airtime_s"
                        ]
                    ),
                    "step_index_of_min": min_row[
                        "step_index"
                    ],
                    "phase_name_of_min": (
                        phase_name_for_step(
                            min_row["step_index"]
                        )
                    ),
                    "periods_below_1s": below_1s,
                    "periods_below_2s": below_2s,
                    "total_periods": len(
                        seed_rows
                    ),
                    "any_negative": any_negative
                }
            )

    output_path = (
        OUTPUT_DIRECTORY
        / "s5_duty_cycle_check.csv"
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(output_rows)

    return output_rows


# ================================================================
# 4. LANCEMENT
# ================================================================


if __name__ == "__main__":

    print(
        "Chargement du journal : "
        + str(LOG_PATH)
    )

    rows = load_log(LOG_PATH)

    print(
        str(len(rows))
        + " lignes chargées."
    )

    case_studies = build_five_case_studies()

    print("")
    print(
        "=== Résumé par scénario et par politique "
        "(moyennes, IC 95 %) ==="
    )

    scenario_policy_rows = (
        export_summary_by_scenario_policy(
            rows,
            case_studies
        )
    )

    for row in scenario_policy_rows:

        print(
            row["scenario_name"]
            + " | "
            + row["policy_id"]
            + " | énergie="
            + format(row["energy_mean"], ".4f")
            + " [IC95 "
            + format(
                row["energy_ci95_low"],
                ".4f"
            )
            + ", "
            + format(
                row["energy_ci95_high"],
                ".4f"
            )
            + "] | latence="
            + format(row["latency_mean"], ".4f")
            + " | auth="
            + format(
                row["authentication_mean"],
                ".6f"
            )
            + " | clé="
            + format(
                row["key_quality_mean"],
                ".4f"
            )
            + " | service="
            + format(
                row["service_rate"] * 100,
                ".2f"
            )
            + "% | FAR="
            + format(row["far"] * 100, ".4f")
            + "% | violations="
            + format(
                row["violation_rate"] * 100,
                ".4f"
            )
            + "% | K1a/K1b/K2 activ.="
            + str(row["activations_k1a"])
            + "/"
            + str(row["activations_k1b"])
            + "/"
            + str(row["activations_k2"])
        )

    print("")
    print(
        "=== Vérification du duty-cycle de S5 ==="
    )

    s5_rows = export_s5_duty_cycle_check(
        rows
    )

    for row in s5_rows:

        print(
            row["policy_id"]
            + " graine "
            + str(row["seed"])
            + " : min="
            + format(
                row["min_duty_cycle_airtime_s"],
                ".4f"
            )
            + "s à l'étape "
            + str(row["step_index_of_min"])
            + " ("
            + row["phase_name_of_min"]
            + "), "
            + str(row["periods_below_1s"])
            + "/"
            + str(row["total_periods"])
            + " périodes < 1s, négatif="
            + str(row["any_negative"])
        )

    print("")
    print(
        "=== Résumé par scénario, politique et "
        "phase (calcul en cours...) ==="
    )

    phase_rows = export_summary_by_phase(
        rows,
        case_studies
    )

    print(
        str(len(phase_rows))
        + " lignes écrites dans "
        "summary_by_scenario_policy_phase.csv"
    )
