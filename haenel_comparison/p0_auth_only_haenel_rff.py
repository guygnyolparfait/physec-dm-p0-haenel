# ================================================================
# P0_AUTH_ONLY_HAENEL_RFF — COMPARAISON PRINCIPALE (25/09/2026)
# ================================================================
#
# Question scientifique de la COMPARAISON PRINCIPALE : "que fait
# notre Decision Maker si on lui donne les mécanismes disponibles
# dans l'expérience Haenel, mais qu'on remplace leur règle fixe de
# décision par P0 ?" Cela exige que A2 (RFF) reçoive la MÊME
# PERFORMANCE DE SÉCURITÉ que Haenel et al. publie, pas le FAR
# natif de notre propre modèle de canal physec_dm.
#
# Ce module reprend EXACTEMENT la même énergie/latence/Rauth(A1)/
# Qkey que p0_auth_only_haenel_scale.py (même moteur physec_dm,
# evaluate_decision jamais réimplémenté), et remplace SEULEMENT le
# FAR/Rauth de A2 par la performance publiée de Haenel et al. via
# haenel_energy_adapter.apply_haenel_rff_far_to_a2 (qui réutilise
# les vraies formules de authentication.py, jamais un calcul à la
# main).
#
# CAS PRINCIPAL (le plus propre scientifiquement, voir Section 2A
# de la demande utilisateur) : FRR=10% / FAR=0.002. Haenel et al.,
# Section 6.3.1, associe explicitement ce FRR (arrondi de 10.89%,
# Section 6.2.2) à ce FAR : "This value was chosen as it led to a
# FAR of 0.2% in our live experiment."
#
# CAS SECONDAIRE : FRR=5%. Haenel et al. mesure l'énergie à FRR=5%
# (pour illustrer une amélioration future du RFF) mais NE publie
# PAS de FAR apparié expérimentalement à ce FRR précis. Si ce
# module est appelé avec frr=0.05, le FAR utilisé reste 0.002
# (FAR_RFF_HAENEL) mais DOIT être étiqueté explicitement
# ASSUMED_CONSTANT_FAR_FOR_FRR5_SENSITIVITY dans tout rapport --
# jamais présenté comme une paire FRR=5%/FAR=0.2% mesurée par
# Haenel et al. dans la même expérience (voir
# label_far_status_for_frr ci-dessous).
#
# Le FAR NATIF de physec_dm pour A2 (~8.39e-5, dépendant d'un
# contexte SNR ASSUMED) N'EST PAS supprimé : il reste disponible
# séparément sous le nom P0_NATIVE_RFF_SENSITIVITY dans
# p0_auth_only_haenel_scale.py -- jamais mélangé à la comparaison
# principale de ce fichier.

from dataclasses import dataclass

from physec_dm.decision_maker import (
    calculate_ideal_and_nadir_points,
    calculate_pareto_front,
    calculate_tchebycheff_score,
    select_from_pareto_front,
    build_tie_break_key,
)

from haenel_comparison.haenel_config import N_MESSAGES
from haenel_comparison.haenel_energy_adapter import (
    FAR_RFF_HAENEL,
    LATENCY_STATUS,
    apply_haenel_rff_far_to_a2,
)
from haenel_comparison.p0_auth_only import build_haenel_p0_parameters
from haenel_comparison.p0_auth_only_haenel_scale import (
    evaluate_candidates_haenel_scale,
)

# FRR pour lequel Haenel et al. publie explicitement une paire
# FRR/FAR (Section 6.3.1 x Section 6.2.2) -- voir en-tête du fichier.
FRR_WITH_PUBLISHED_FAR_PAIRING = 0.10


def far_status_for_frr(frr):
    """Statut à afficher/exporter pour le FAR utilisé sur A2, selon
    le FRR demandé -- jamais laissé implicite."""

    if frr == FRR_WITH_PUBLISHED_FAR_PAIRING:
        return (
            "PUBLISHED_HAENEL (Section 6.3.1 x Section 6.2.2 : "
            "FRR=10% choisi car il conduit à FAR=0.2%)"
        )

    return (
        "ASSUMED_CONSTANT_FAR_FOR_FRR5_SENSITIVITY (Haenel et al. "
        "ne publie pas de FAR apparié expérimentalement à ce FRR "
        "précis -- FAR_RFF_HAENEL=0.002 réutilisé par hypothèse de "
        "sensibilité énergétique, PAS une paire mesurée)"
    )


@dataclass
class P0HaenelRffMessageEvent:
    message_index: int
    frr: float
    far_used: float
    far_status: str
    chosen_auth: str
    energy_mJ: float
    refusal_of_service: bool


def evaluate_candidates_haenel_rff(context, parameters, rho_ab, frr, far=FAR_RFF_HAENEL):
    """Comme evaluate_candidates_haenel_scale, mais A2 reçoit en
    plus le FAR publié de Haenel et al. (au lieu du FAR natif du
    modèle de canal physec_dm)."""

    evaluations = evaluate_candidates_haenel_scale(
        context, parameters, rho_ab, frr
    )

    # evaluations = [A1, A2] par construction de la fonction reprise.
    a2_evaluation = evaluations[1]

    if a2_evaluation.admissible:
        apply_haenel_rff_far_to_a2(a2_evaluation, parameters, far=far)

    return evaluations


def select_p0_auth_only_haenel_rff(context, parameters, rho_ab, frr, far=FAR_RFF_HAENEL):

    all_evaluations = evaluate_candidates_haenel_rff(
        context, parameters, rho_ab, frr, far=far
    )

    admissible_evaluations = [
        evaluation for evaluation in all_evaluations if evaluation.admissible
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


def simulate_p0_auth_only_haenel_rff(frr, n_messages=N_MESSAGES, far=FAR_RFF_HAENEL):
    """P0_AUTH_ONLY_HAENEL_RFF est déterministe sur un contexte
    statique répété (même raisonnement que p0_auth_only_haenel_scale) :
    on simule quand même n_messages pour produire un CSV de la même
    forme et faciliter la comparaison directe avec
    B5_HAENEL_CALIBRATED."""

    from haenel_comparison.p0_auth_only import build_haenel_static_context

    parameters = build_haenel_p0_parameters()
    context, channel_metrics = build_haenel_static_context(parameters)

    far_status = far_status_for_frr(frr)

    events = []

    for message_index in range(n_messages):

        selected, _all = select_p0_auth_only_haenel_rff(
            context, parameters, channel_metrics.rho_ab, frr, far=far
        )

        if selected is None:
            events.append(
                P0HaenelRffMessageEvent(
                    message_index=message_index,
                    frr=frr,
                    far_used=far,
                    far_status=far_status,
                    chosen_auth=None,
                    energy_mJ=None,
                    refusal_of_service=True,
                )
            )
            continue

        events.append(
            P0HaenelRffMessageEvent(
                message_index=message_index,
                frr=frr,
                far_used=far,
                far_status=far_status,
                chosen_auth=selected.decision.authentication_action.value,
                energy_mJ=selected.cost_metrics.expected_energy_j,
                refusal_of_service=False,
            )
        )

    return events


def summarize_p0_haenel_rff_events(events):

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
        "far_used": events[0].far_used if events else None,
        "far_status": events[0].far_status if events else None,
    }


def print_detailed_diagnostic(frr, far=FAR_RFF_HAENEL, n_periods_to_show=1):
    """Diagnostic complet, même forme que
    p0_auth_only_haenel_scale.print_detailed_diagnostic, pour la
    comparaison principale (A2 reçoit le FAR publié de Haenel et al.)."""

    from haenel_comparison.p0_auth_only import build_haenel_static_context

    parameters = build_haenel_p0_parameters()
    context, channel_metrics = build_haenel_static_context(parameters)

    print(f"\n{'=' * 78}")
    print(f"DIAGNOSTIC P0_AUTH_ONLY_HAENEL_RFF -- FRR = {frr}, FAR(A2) = {far}")
    print(f"Statut FAR : {far_status_for_frr(frr)}")
    print(f"{'=' * 78}")
    print(f"(Latence : {LATENCY_STATUS} -- neutralisée à 0.0)\n")

    for period in range(n_periods_to_show):

        all_evaluations = evaluate_candidates_haenel_rff(
            context, parameters, channel_metrics.rho_ab, frr, far=far
        )

        admissible_evaluations = [e for e in all_evaluations if e.admissible]

        pareto_front = calculate_pareto_front(
            admissible_evaluations, parameters.dominance_tolerance
        )
        pareto_ids = {id(e) for e in pareto_front}

        ideal_point, nadir_point = (
            calculate_ideal_and_nadir_points(pareto_front)
            if pareto_front else (None, None)
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
            r_auth = evaluation.authentication_metrics.authentication_robustness
            q_key = evaluation.key_metrics.key_quality
            far_value = evaluation.authentication_metrics.far

            print(f"    energie (mJ)        = {energy_mJ:.5f}")
            print(f"    latence (neutre)    = {latency}")
            print(f"    R_auth              = {r_auth:.8f}")
            print(f"    Q_key               = {q_key:.6f}")
            print(f"    FAR                 = {far_value:.8f}")
            print(f"    sur front de Pareto = {id(evaluation) in pareto_ids}")

            if id(evaluation) in pareto_ids and ideal_point:
                score = calculate_tchebycheff_score(
                    objective_vector=evaluation.objective_vector,
                    contextual_weights=parameters.contextual_weights,
                    ideal_point=ideal_point,
                    nadir_point=nadir_point,
                    epsilon=parameters.tchebycheff_epsilon,
                )
                tie_break = build_tie_break_key(evaluation)
                print(f"    score Tchebycheff   = {score:.8f}")
                print(f"    clé tie-break       = {tie_break}")

        selected, _ = select_p0_auth_only_haenel_rff(
            context, parameters, channel_metrics.rho_ab, frr, far=far
        )
        decision_name = selected.decision.get_name() if selected else "REFUS"
        print(f"  >>> DÉCISION RETENUE : {decision_name}\n")


if __name__ == "__main__":

    for frr in (0.10, 0.05):
        print_detailed_diagnostic(frr)
        events = simulate_p0_auth_only_haenel_rff(frr)
        summary = summarize_p0_haenel_rff_events(events)
        print(f"Résumé sur {summary['n_messages']} messages : {summary}\n")
