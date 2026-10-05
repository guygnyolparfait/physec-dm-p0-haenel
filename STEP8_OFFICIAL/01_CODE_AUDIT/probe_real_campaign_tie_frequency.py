# Sonde diagnostique (jetable) : sur de VRAIES missions S1-S5
# (build_five_case_studies_v2, poids EQUAL publiés), on
# reconstruit a posteriori -- a partir des memes fonctions
# reelles du Decision Maker -- le score Tchebycheff de chaque
# membre du front de Pareto a CHAQUE periode, avec :
#
#   (a) la formule ACTUELLE (epsilon ajoute au denominateur
#       de toutes les dimensions) ;
#   (b) la formule PROPOSEE (epsilon utilise seulement comme
#       seuil de detection de span degenere -> normalized=0).
#
# On compte :
#   - le nombre de periodes ou le front de Pareto a plus d'un
#     membre (condition necessaire a une egalite) ;
#   - le nombre de periodes ou, sous la formule (a), plusieurs
#       membres tombent dans score_tolerance du meilleur score
#       (egalite/quasi-egalite detectee) ;
#   - parmi celles-ci, le nombre de fois ou le "gagnant" choisi
#       par (a) differe du "gagnant" qu'aurait choisi (b).
#
# N'ecrit rien dans le depot.
import sys

sys.path.insert(0, "/home/parfait/physec_dm")

from physec_dm.case_studies import (
    apply_case_study_overrides,
    build_case_study_base_parameters,
    build_five_case_studies_v2
)

from physec_dm.decision_maker import (
    calculate_pareto_front,
    calculate_ideal_and_nadir_points,
    evaluate_all_decisions,
    run_decision_maker,
    validate_contextual_weights,
    build_tie_break_key
)

from run_five_case_studies import build_scenario_traces, run_single_mission

EQUAL_WEIGHTS = [0.25, 0.25, 0.25, 0.25]
SEEDS = [9500, 9501, 9502]
MAX_STEPS = 1500
EPS = 1e-12
SCORE_TOL = 1e-12


def score_current(objective_vector, weights, ideal, nadir, epsilon):

    weighted = []
    for k in range(len(objective_vector)):
        denom = nadir[k] - ideal[k] + epsilon
        num = objective_vector[k] - ideal[k]
        weighted.append(weights[k] * (num / denom))
    return max(weighted)


def score_proposed(objective_vector, weights, ideal, nadir, epsilon):

    weighted = []
    for k in range(len(objective_vector)):
        span = nadir[k] - ideal[k]
        if abs(span) <= epsilon:
            normalized = 0.0
        else:
            normalized = (objective_vector[k] - ideal[k]) / span
        weighted.append(weights[k] * normalized)
    return max(weighted)


stats = {
    "periods_total": 0,
    "periods_pareto_front_gt1": 0,
    "periods_tie_current": 0,
    "periods_winner_differs": 0,
    "max_score_gap_seen_in_tie": 0.0,
}

diverging_examples = []


def build_probe_policy(scenario_id, seed):

    def probe(
        context,
        parameters,
        rho_ab,
        variation_feasible=None,
        k2_protocol=None,
        contextual_weights=None,
        enforce_far_floor=True
    ):

        result = run_decision_maker(
            context=context,
            parameters=parameters,
            rho_ab=rho_ab,
            variation_feasible=variation_feasible,
            k2_protocol=k2_protocol,
            contextual_weights=contextual_weights,
            enforce_far_floor=enforce_far_floor
        )

        if result.refusal_of_service:
            return result

        stats["periods_total"] += 1

        pareto_front = result.pareto_front

        if len(pareto_front) > 1:

            stats["periods_pareto_front_gt1"] += 1

            weights = result.contextual_weights
            ideal = result.ideal_point
            nadir = result.nadir_point

            scores_current = [
                score_current(e.objective_vector, weights, ideal, nadir, EPS)
                for e in pareto_front
            ]
            scores_proposed = [
                score_proposed(e.objective_vector, weights, ideal, nadir, EPS)
                for e in pareto_front
            ]

            best_current = min(scores_current)
            best_proposed = min(scores_proposed)

            tied_current = [
                e for e, s in zip(pareto_front, scores_current)
                if abs(s - best_current) <= SCORE_TOL
            ]
            tied_proposed = [
                e for e, s in zip(pareto_front, scores_proposed)
                if abs(s - best_proposed) <= SCORE_TOL
            ]

            if len(tied_current) > 1 or len(tied_proposed) > 1:

                stats["periods_tie_current"] += 1

                winner_current = min(tied_current, key=build_tie_break_key)
                winner_proposed = min(tied_proposed, key=build_tie_break_key)

                if (
                    winner_current.decision.get_name()
                    != winner_proposed.decision.get_name()
                ):

                    stats["periods_winner_differs"] += 1

                    if len(diverging_examples) < 5:
                        diverging_examples.append({
                            "scenario": scenario_id,
                            "seed": seed,
                            "n_pareto": len(pareto_front),
                            "n_tied_current": len(tied_current),
                            "n_tied_proposed": len(tied_proposed),
                            "winner_current": winner_current.decision.get_name(),
                            "winner_proposed": winner_proposed.decision.get_name(),
                            "scores_current": scores_current,
                            "scores_proposed": scores_proposed,
                        })

            # amplitude max de l'ecart entre 2 scores non-identiques
            # (diagnostic complementaire, meme hors tolerance stricte)
            sorted_scores = sorted(scores_current)
            if len(sorted_scores) > 1:
                gap = sorted_scores[1] - sorted_scores[0]
                if 0 < gap < 1e-8:
                    stats["max_score_gap_seen_in_tie"] = max(
                        stats["max_score_gap_seen_in_tie"], gap
                    )

        return result

    return probe


def main():

    base_parameters = build_case_study_base_parameters()
    case_studies = build_five_case_studies_v2()

    for case_study in case_studies:

        scenario_id = case_study["scenario_id"]
        scenario_parameters = apply_case_study_overrides(base_parameters, case_study)

        for seed in SEEDS:

            traces = build_scenario_traces(case_study, seed, MAX_STEPS)

            probe_policy = build_probe_policy(scenario_id, seed)

            run_single_mission(
                case_study=case_study,
                scenario_parameters=scenario_parameters,
                policy_id="P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS",
                decision_policy_fn=probe_policy,
                seed=seed,
                max_steps=MAX_STEPS,
                traces=traces
            )

        print(scenario_id, "termine.")

    print()
    print("=" * 70)
    print("RESULTATS SONDE (S1-S5 v2, poids EQUAL, 3 graines/scenario, 1500 pas)")
    print("=" * 70)
    for k, v in stats.items():
        print(k, "=", v)

    print()
    print("Exemples de divergence (max 5) :")
    for ex in diverging_examples:
        print(ex)


if __name__ == "__main__":
    main()
