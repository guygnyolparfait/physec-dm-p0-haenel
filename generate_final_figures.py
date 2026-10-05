# Ce script génère l'ensemble des figures demandées pour la
# campagne complète des cinq cas d'étude, à partir du journal
# déjà produit (results/five_case_studies_final/
# five_case_studies_log.csv) et des instantanés Pareto déjà
# capturés (results/five_case_studies_final/
# pareto_snapshots.json). Il ne relance aucune mission.
import json
from pathlib import Path

from analyze_five_case_studies import (
    figure_decision_timeline_by_policy,
    figure_four_objectives_over_time,
    figure_global_summary_p0_vs_b1_gains,
    figure_key_generation_progress,
    figure_p0_vs_b1_detailed,
    figure_pareto_front_energy_auth,
    figure_pareto_front_latency_key,
    load_log,
    scenario_full_name
)

from physec_dm.case_studies import (
    apply_case_study_overrides,
    build_case_study_base_parameters,
    build_five_case_studies
)


LOG_PATH = Path(
    "results/five_case_studies_final/"
    "five_case_studies_log.csv"
)

SNAPSHOTS_PATH = Path(
    "results/five_case_studies_final/"
    "pareto_snapshots.json"
)

FIGURES_DIRECTORY = Path(
    "results/five_case_studies_final/figures"
)

MAX_STEPS = 1500


def main():

    FIGURES_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )

    print("Chargement du journal...")

    rows = load_log(LOG_PATH)

    print(
        str(len(rows))
        + " lignes chargées."
    )

    with SNAPSHOTS_PATH.open(
        encoding="utf-8"
    ) as json_file:

        pareto_snapshots = json.load(
            json_file
        )

    case_studies = build_five_case_studies()

    base_parameters = (
        build_case_study_base_parameters()
    )

    for case_study in case_studies:

        scenario_id = case_study["scenario_id"]

        scenario_parameters = (
            apply_case_study_overrides(
                base_parameters,
                case_study
            )
        )

        print(
            "Figures pour "
            + scenario_full_name(scenario_id)
            + "..."
        )

        figure_four_objectives_over_time(
            rows,
            case_study,
            MAX_STEPS,
            FIGURES_DIRECTORY
            / (
                scenario_id
                + "_four_objectives_over_time.png"
            )
        )

        figure_decision_timeline_by_policy(
            rows,
            case_study,
            MAX_STEPS,
            FIGURES_DIRECTORY
            / (
                scenario_id
                + "_decision_timeline.png"
            )
        )

        figure_key_generation_progress(
            rows,
            case_study,
            scenario_parameters,
            MAX_STEPS,
            FIGURES_DIRECTORY
            / (
                scenario_id
                + "_key_generation_progress.png"
            )
        )

        figure_p0_vs_b1_detailed(
            rows,
            case_study,
            FIGURES_DIRECTORY
            / (scenario_id + "_P0_vs_B1.png")
        )

        snapshot = pareto_snapshots.get(
            scenario_id
        )

        if snapshot is not None:

            figure_pareto_front_energy_auth(
                snapshot,
                scenario_full_name(scenario_id),
                FIGURES_DIRECTORY
                / (
                    scenario_id
                    + "_pareto_energy_"
                    "authentication.png"
                )
            )

            figure_pareto_front_latency_key(
                snapshot,
                scenario_full_name(scenario_id),
                FIGURES_DIRECTORY
                / (
                    scenario_id
                    + "_pareto_latency_key.png"
                )
            )

    print(
        "Figure globale complémentaire "
        "(gains P0 vs B1)..."
    )

    figure_global_summary_p0_vs_b1_gains(
        rows,
        case_studies,
        FIGURES_DIRECTORY
        / "global_p0_vs_b1_relative_gains.png"
    )

    print(
        "Toutes les figures ont été écrites dans "
        + str(FIGURES_DIRECTORY)
    )


if __name__ == "__main__":

    main()
