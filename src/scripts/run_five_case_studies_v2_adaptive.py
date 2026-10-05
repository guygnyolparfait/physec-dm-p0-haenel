# Campagne adaptative de la version COMPLEXIFIÉE de S1-S5, à la
# demande explicite de l'encadrante (complexifier S1-S5 eux-mêmes,
# pas ajouter un scénario à côté). Copie conforme de
# run_five_case_studies_adaptive.py, au jeu de cas d'étude près :
#
# - mêmes cinq politiques, même arrêt Monte-Carlo adaptatif borné,
#   mêmes briques de simulation (build_scenario_traces,
#   run_single_mission, extract_log_rows) — AUCUNE équation
#   scientifique modifiée ou recalculée ici ;
# - utilise build_five_case_studies_v2() (physec_dm/case_studies.py),
#   qui applique deux leviers déjà sourcés (mallory_separation dans
#   la plage validée [0,5 ; 5] du document de modélisation ;
#   cost_profile_id LOW/CENTRAL/HIGH déjà codé et documenté comme
#   test de sensibilité) sans toucher à build_five_case_studies()
#   ni à build_case_study_s1()..s5(), qui restent strictement
#   inchangés.
#
# Sortie écrite dans results/five_case_studies_v2_complex_adaptive/,
# JAMAIS dans results/five_case_studies_final_adaptive/ (les
# données originales, déjà vérifiées, restent intactes).
import csv
import json
import sys
from pathlib import Path

from physec_dm.adaptive_monte_carlo import (
    MAXIMUM_SEED_COUNT,
    MINIMUM_SEED_COUNT,
    SEED_BATCH_SIZE,
    evaluate_convergence,
    should_stop_sampling
)

from physec_dm.case_studies import (
    apply_case_study_overrides,
    build_case_study_base_parameters,
    build_five_case_studies_v2
)

from physec_dm.thesis_scenarios import build_thesis_seeds

from scripts.run_five_case_studies import (
    LOG_FIELD_NAMES,
    POLICIES,
    build_scenario_traces,
    extract_log_rows,
    run_single_mission
)

from scripts.run_five_case_studies_adaptive import (
    compute_seed_summary_metrics
)


def run_adaptive_campaign_v2(
    max_steps,
    output_directory
):

    output_path = Path(output_directory)

    output_path.mkdir(
        parents=True,
        exist_ok=True
    )

    print(
        "Lancement de la campagne adaptative COMPLEXIFIÉE "
        "de S1-S5."
    )
    print(
        "Politiques : "
        + ", ".join(
            policy["policy_id"]
            for policy in POLICIES
        )
    )
    print(
        "Graines : minimum "
        + str(MINIMUM_SEED_COUNT)
        + ", lots de "
        + str(SEED_BATCH_SIZE)
        + ", maximum "
        + str(MAXIMUM_SEED_COUNT)
        + "."
    )

    base_parameters = (
        build_case_study_base_parameters()
    )

    case_studies = build_five_case_studies_v2()

    all_rows = []

    convergence_report = {}

    for case_study in case_studies:

        scenario_id = case_study["scenario_id"]

        print(
            "\nScénario "
            + scenario_id
            + " (d_M="
            + str(case_study["v2_mallory_separation"])
            + ", profil coût="
            + case_study["v2_cost_profile_id"]
            + ") : démarrage de l'échantillonnage adaptatif."
        )

        scenario_parameters = (
            apply_case_study_overrides(
                base_parameters,
                case_study
            )
        )

        summaries_by_policy_seed = {
            policy["policy_id"]: {}
            for policy in POLICIES
        }

        processed_seed_count = 0
        requested_seed_count = MINIMUM_SEED_COUNT

        while True:

            all_seeds = build_thesis_seeds(
                count=requested_seed_count
            )

            new_seeds = all_seeds[
                processed_seed_count:
            ]

            for seed in new_seeds:

                traces = build_scenario_traces(
                    case_study,
                    seed,
                    max_steps
                )

                for policy in POLICIES:

                    mission_result = (
                        run_single_mission(
                            case_study=case_study,
                            scenario_parameters=(
                                scenario_parameters
                            ),
                            policy_id=(
                                policy["policy_id"]
                            ),
                            decision_policy_fn=(
                                policy[
                                    "decision_policy_fn"
                                ]
                            ),
                            seed=seed,
                            max_steps=max_steps,
                            traces=traces
                        )
                    )

                    rows = extract_log_rows(
                        case_study=case_study,
                        policy_id=policy["policy_id"],
                        seed=seed,
                        mission_result=mission_result,
                        conditions=(
                            traces["conditions"]
                        )
                    )

                    all_rows.extend(rows)

                    summaries_by_policy_seed[
                        policy["policy_id"]
                    ][seed] = (
                        compute_seed_summary_metrics(
                            rows
                        )
                    )

            processed_seed_count = len(
                all_seeds
            )

            convergence_by_policy = {}
            all_policies_converged = True

            for policy in POLICIES:

                policy_id = policy["policy_id"]

                seed_summaries = list(
                    summaries_by_policy_seed[
                        policy_id
                    ].values()
                )

                convergence_result = (
                    evaluate_convergence(
                        seed_summaries
                    )
                )

                convergence_by_policy[policy_id] = (
                    convergence_result
                )

                if not convergence_result[
                    "all_converged"
                ]:

                    all_policies_converged = False

            print(
                "  "
                + str(processed_seed_count)
                + " graines traitées ; convergence "
                "atteinte pour toutes les politiques : "
                + str(all_policies_converged)
            )

            if should_stop_sampling(
                seed_count=processed_seed_count,
                all_converged=all_policies_converged
            ):

                break

            requested_seed_count = (
                processed_seed_count
                + SEED_BATCH_SIZE
            )

        convergence_report[scenario_id] = {
            "seed_count": processed_seed_count,
            "all_converged": all_policies_converged,
            "mallory_separation": (
                case_study["v2_mallory_separation"]
            ),
            "cost_profile_id": (
                case_study["v2_cost_profile_id"]
            ),
            "per_policy": convergence_by_policy
        }

    log_path = (
        output_path / "five_case_studies_v2_log.csv"
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
        "\nJournal écrit : "
        + str(log_path)
        + " ("
        + str(len(all_rows))
        + " lignes)."
    )

    convergence_path = (
        output_path / "monte_carlo_convergence.json"
    )

    with convergence_path.open(
        "w",
        encoding="utf-8"
    ) as json_file:

        json.dump(
            convergence_report,
            json_file,
            indent=2,
            default=str
        )

    print(
        "Rapport de convergence écrit : "
        + str(convergence_path)
    )

    return all_rows, convergence_report


if __name__ == "__main__":

    mode = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "full"
    )

    if mode == "full":

        run_adaptive_campaign_v2(
            max_steps=1500,
            output_directory=(
                "results/five_case_studies_v2_complex_adaptive"
            )
        )

    else:

        raise ValueError(
            "Mode inconnu : "
            + mode
            + " (seul 'full' est défini pour ce script)."
        )
