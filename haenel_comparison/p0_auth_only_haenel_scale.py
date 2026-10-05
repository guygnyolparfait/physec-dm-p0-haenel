# ================================================================
# P0_AUTH_ONLY — ÉCHELLE ÉNERGÉTIQUE HAENEL (comparable à B5)
# ================================================================
#
# Variante de p0_auth_only.py où l'énergie et la latence des deux
# candidats (A1-K0, A2-K0) sont fournies par
# haenel_comparison.haenel_energy_adapter au lieu du modèle natif
# LoRa/Semtech (energy_latency.py, jamais modifié). Rauth et Qkey
# restent calculés par le vrai modèle physec_dm.
#
# p0_auth_only.py (échelle LoRa/Semtech native) N'EST PAS
# supprimé : il reste disponible pour montrer, par contraste, que
# le choix de P0 ne dépendait pas de l'échelle d'énergie -- voir
# HAENEL_COMPARISON_README.md, section "Constat".

from dataclasses import dataclass

from physec_dm.decision_maker import (
    calculate_ideal_and_nadir_points,
    calculate_pareto_front,
    calculate_tchebycheff_score,
    evaluate_decision,
    select_from_pareto_front,
    build_tie_break_key,
)
from physec_dm.models import AuthenticationAction, Decision, KeyAction

from haenel_comparison.haenel_config import N_MESSAGES
from haenel_comparison.haenel_energy_adapter import (
    LATENCY_STATUS,
    a1_energy_mJ,
    a2_expected_energy_mJ,
    apply_haenel_energy_scale,
)
from haenel_comparison.p0_auth_only import (
    build_haenel_p0_parameters,
    build_haenel_static_context,
)


@dataclass
class P0HaenelScaleMessageEvent:
    message_index: int
    frr: float
    chosen_auth: str
    energy_mJ: float
    refusal_of_service: bool


def evaluate_candidates_haenel_scale(context, parameters, rho_ab, frr):
    """Évalue A1-K0 et A2-K0 avec le VRAI moteur physec_dm
    (evaluate_decision, donc Rauth/Qkey/admissibilité authentiques),
    puis remplace uniquement énergie et latence par l'échelle
    Haenel et al. (haenel_energy_adapter). Retourne la liste des
    deux DecisionEvaluation modifiées, dans l'ordre [A1, A2]."""

    candidates = [
        (
            Decision(AuthenticationAction.A1, KeyAction.K0),
            a1_energy_mJ(),
        ),
        (
            Decision(AuthenticationAction.A2, KeyAction.K0),
            a2_expected_energy_mJ(frr),
        ),
    ]

    evaluations = []

    for decision, energy_mJ in candidates:

        evaluation = evaluate_decision(
            decision=decision,
            context=context,
            parameters=parameters,
            rho_ab=rho_ab,
            enforce_far_floor=True,
        )

        if evaluation.admissible:
            apply_haenel_energy_scale(evaluation, energy_mJ)

        evaluations.append(evaluation)

    return evaluations


def select_p0_auth_only_haenel_scale(context, parameters, rho_ab, frr):

    all_evaluations = evaluate_candidates_haenel_scale(
        context, parameters, rho_ab, frr
    )

    admissible_evaluations = [
        evaluation
        for evaluation in all_evaluations
        if evaluation.admissible
    ]

    if len(admissible_evaluations) == 0:
        return None, all_evaluations

    pareto_front = calculate_pareto_front(
        admissible_evaluations, parameters.dominance_tolerance
    )

    (selected_evaluation, _ideal, _nadir, _weights) = (
        select_from_pareto_front(
            pareto_front=pareto_front,
            contextual_weights=parameters.contextual_weights,
            epsilon=parameters.tchebycheff_epsilon,
            score_tolerance=parameters.score_tolerance,
        )
    )

    return selected_evaluation, all_evaluations


def simulate_p0_auth_only_haenel_scale(frr, n_messages=N_MESSAGES):
    """P0 est déterministe sur un contexte statique répété : le
    même candidat gagnant est choisi à chaque période pour un FRR
    donné (P0 raisonne en ESPÉRANCE, pas sur un tirage réalisé --
    voir haenel_energy_adapter.a2_expected_energy_mJ). On simule
    quand même les n_messages pour produire un CSV de la même
    forme que B5_HAENEL_CALIBRATED et faciliter la comparaison directe."""

    parameters = build_haenel_p0_parameters()
    context, channel_metrics = build_haenel_static_context(
        parameters
    )

    events = []

    for message_index in range(n_messages):

        selected, _all = select_p0_auth_only_haenel_scale(
            context, parameters, channel_metrics.rho_ab, frr
        )

        if selected is None:
            events.append(
                P0HaenelScaleMessageEvent(
                    message_index=message_index,
                    frr=frr,
                    chosen_auth=None,
                    energy_mJ=None,
                    refusal_of_service=True,
                )
            )
            continue

        events.append(
            P0HaenelScaleMessageEvent(
                message_index=message_index,
                frr=frr,
                chosen_auth=(
                    selected.decision.authentication_action.value
                ),
                energy_mJ=selected.cost_metrics.expected_energy_j,
                refusal_of_service=False,
            )
        )

    return events


def summarize_p0_haenel_scale_events(events):

    n_messages = len(events)
    served = [e for e in events if not e.refusal_of_service]
    n_a1 = sum(1 for e in served if e.chosen_auth == "A1")
    n_a2 = sum(1 for e in served if e.chosen_auth == "A2")
    total_energy_mJ = sum(e.energy_mJ for e in served)

    return {
        "n_messages": n_messages,
        "n_a1": n_a1,
        "n_a2": n_a2,
        "n_refusal_of_service": n_messages - len(served),
        "total_energy_mJ": total_energy_mJ,
        "mean_energy_per_message_mJ": (
            total_energy_mJ / len(served) if served else None
        ),
    }


# ================================================================
# DIAGNOSTIC DÉTAILLÉ PAR CANDIDAT (demandé explicitement)
# ================================================================


def print_detailed_diagnostic(frr, n_periods_to_show=3):
    """Affiche, pour quelques périodes, le détail complet de
    l'évaluation de A1-K0 et A2-K0 : énergie, latence, Rauth, Qkey,
    admissibilité, coordonnées normalisées, appartenance au front
    de Pareto, score de Tchebycheff, clé de tie-break, décision
    finale. Le contexte étant statique, ces valeurs sont
    identiques d'une période à l'autre -- elles sont réaffichées
    n_periods_to_show fois pour rendre explicite que rien ne varie
    dans le temps ici (contrairement à S1-S5)."""

    parameters = build_haenel_p0_parameters()
    context, channel_metrics = build_haenel_static_context(
        parameters
    )

    print(f"\n{'=' * 78}")
    print(f"DIAGNOSTIC DÉTAILLÉ -- FRR = {frr}")
    print(f"{'=' * 78}")
    print(f"(Latence : {LATENCY_STATUS} -- neutralisée à 0.0 pour")
    print("les deux candidats, voir haenel_energy_adapter.py §2)\n")

    for period in range(n_periods_to_show):

        all_evaluations = evaluate_candidates_haenel_scale(
            context, parameters, channel_metrics.rho_ab, frr
        )

        admissible_evaluations = [
            e for e in all_evaluations if e.admissible
        ]

        pareto_front = calculate_pareto_front(
            admissible_evaluations, parameters.dominance_tolerance
        )

        pareto_ids = {id(e) for e in pareto_front}

        ideal_point, nadir_point = (
            calculate_ideal_and_nadir_points(pareto_front)
            if pareto_front
            else (None, None)
        )

        print(f"--- Période {period} ---")

        for evaluation in all_evaluations:

            name = evaluation.decision.get_name()

            print(f"  {name}:")
            print(f"    admissible          = {evaluation.admissible}")

            if not evaluation.admissible:
                for reason in evaluation.rejection_reasons:
                    print(f"    motif de rejet      = {reason}")
                continue

            energy_mJ = evaluation.cost_metrics.expected_energy_j
            latency = evaluation.cost_metrics.normalized_latency
            r_auth = (
                evaluation.authentication_metrics
                .authentication_robustness
            )
            q_key = evaluation.key_metrics.key_quality
            far = evaluation.authentication_metrics.far

            print(f"    energie (mJ)        = {energy_mJ:.5f}")
            print(f"    latence (neutre)    = {latency}")
            print(f"    R_auth              = {r_auth:.8f}")
            print(f"    Q_key               = {q_key:.6f}")
            print(f"    FAR                 = {far:.8f}")
            print(
                f"    sur front de Pareto = "
                f"{id(evaluation) in pareto_ids}"
            )

            if id(evaluation) in pareto_ids and ideal_point:

                score = calculate_tchebycheff_score(
                    objective_vector=evaluation.objective_vector,
                    contextual_weights=parameters.contextual_weights,
                    ideal_point=ideal_point,
                    nadir_point=nadir_point,
                    epsilon=parameters.tchebycheff_epsilon,
                )

                tie_break = build_tie_break_key(evaluation)

                print(
                    f"    vecteur objectif    = "
                    f"{[round(v, 6) for v in evaluation.objective_vector]}"
                )
                print(f"    score Tchebycheff   = {score:.8f}")
                print(f"    clé tie-break       = {tie_break}")

        selected, _ = select_p0_auth_only_haenel_scale(
            context, parameters, channel_metrics.rho_ab, frr
        )
        decision_name = (
            selected.decision.get_name() if selected else "REFUS"
        )
        print(f"  >>> DÉCISION RETENUE : {decision_name}\n")


if __name__ == "__main__":

    for frr in (0.05, 0.10):
        print_detailed_diagnostic(frr, n_periods_to_show=1)

        events = simulate_p0_auth_only_haenel_scale(frr)
        summary = summarize_p0_haenel_scale_events(events)
        print(f"Résumé sur {summary['n_messages']} messages : {summary}\n")
