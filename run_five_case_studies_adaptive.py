# Ce script orchestre la campagne COMPLÈTE (Jour 2) des cinq
# cas d'étude dynamiques, avec :
#
# - cinq politiques : P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS,
#   B1-CONVENTIONAL, B2-NAIVE-PHYSEC-NO-FLOOR,
#   B3-HYBRID-FIXED, B4-DM-NO-FAR-FLOOR ;
# - un arrêt Monte-Carlo ADAPTATIF BORNÉ par scénario
#   (physec_dm/adaptive_monte_carlo.py) : minimum 30 graines,
#   lots de 10, maximum 150, tolérances pré-enregistrées ;
# - les mêmes graines communes à toutes les politiques d'un
#   même scénario (Common Random Numbers).
#
# Il ne modifie et ne recalcule AUCUNE équation scientifique :
# il réutilise exclusivement build_scenario_traces,
# run_single_mission et extract_log_rows de
# run_five_case_studies.py.
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
    build_five_case_studies
)

from physec_dm.thesis_scenarios import build_thesis_seeds

from run_five_case_studies import (
    LOG_FIELD_NAMES,
    POLICIES,
    build_scenario_traces,
    extract_log_rows,
    run_single_mission
)


# ================================================================
# 1. RÉSUMÉ PAR GRAINE (métriques principales du protocole)
# ================================================================
def compute_seed_summary_metrics(
    rows
):

    served_rows = [
        row
        for row in rows
        if row["legitimate_message_served"]
    ]

    service_rate = len(served_rows) / len(rows)

    def mean_of(field_name):

        values = [
            row[field_name]
            for row in rows
            if row[field_name] is not None
        ]

        if len(values) == 0:

            return None

        return sum(values) / len(values)

    mallory_attempts = [
        row
        for row in rows
        if row["mallory_attempted"]
    ]

    mallory_accepted = [
        row
        for row in mallory_attempts
        if row["mallory_accepted"]
    ]

    return {
        "service_rate": service_rate,
        "mean_energy_j": mean_of(
            "energy_objective_j"
        ),
        "mean_latency_objective": mean_of(
            "latency_objective"
        ),
        "mean_authentication_robustness": mean_of(
            "authentication_robustness"
        ),
        "mean_key_quality": mean_of(
            "key_quality"
        ),
        "far_accepted_count": len(
            mallory_accepted
        ),
        "mallory_attempts_count": len(
            mallory_attempts
        )
    }


# ================================================================
# 2. CAMPAGNE ADAPTATIVE, SCÉNARIO PAR SCÉNARIO
# ================================================================
def run_adaptive_campaign(
    max_steps,
    output_directory
):

    output_path = Path(output_directory)

    output_path.mkdir(
        parents=True,
        exist_ok=True
    )

    print(
        "Lancement de la campagne COMPLÈTE adaptative "
        "des cinq cas d'étude (Jour 2)."
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

    case_studies = build_five_case_studies()

    all_rows = []

    convergence_report = {}

    for case_study in case_studies:

        scenario_id = case_study["scenario_id"]

        print(
            "\nScénario "
            + scenario_id
            + " : démarrage de l'échantillonnage "
            "adaptatif."
        )

        scenario_parameters = (
            apply_case_study_overrides(
                base_parameters,
                case_study
            )
        )

        # summaries_by_policy_seed[policy_id][seed] = résumé
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

            # Convergence évaluée séparément pour chaque
            # politique : le scénario ne s'arrête que
            # lorsque TOUTES les politiques ont convergé
            # (ou que le maximum de graines est atteint).
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
            "per_policy": convergence_by_policy
        }

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

        run_adaptive_campaign(
            max_steps=1500,
            output_directory=(
                "results/five_case_studies_final_adaptive"
            )
        )

    else:

        raise ValueError(
            "Mode inconnu : "
            + mode
            + " (seul 'full' est défini pour ce script)."
        )
