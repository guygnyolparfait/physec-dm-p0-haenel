# ================================================================
# P0_AUTH_ONLY — notre Decision Maker, restreint à K=K0, dans le
# même contexte statique que le banc d'essai Haenel et al.
# ================================================================
#
# EXPÉRIENCE 1 (voir HAENEL_COMPARISON_README.md) : "Le Decision
# Maker multiobjectif apporte-t-il un comportement différent de la
# règle fixe RFF-puis-MAC de Haenel et al., dans les mêmes
# conditions ?" -- gestion de clé volontairement figée à K0 des
# deux côtés (Haenel et al. ne gère pas de clé physique).
#
# On réutilise directement les VRAIES fonctions du Decision Maker
# (evaluate_decision, calculate_pareto_front, select_from_pareto_front)
# -- on ne réimplémente jamais la logique de sélection. On
# restreint seulement l'ENSEMBLE DES CANDIDATS à {A1-K0, A2-K0}
# avant de la leur soumettre, exactement comme
# select_b5_haenel_rff_then_mac_decision restreint déjà ses
# propres candidats dans case_studies.py.
#
# NUANCE IMPORTANTE À NE JAMAIS PERDRE DE VUE (documentée aussi
# dans le README) : notre modèle n'a pas de notion de "rejet
# stochastique du message légitime" comme le FRR de Haenel et al.
# Le rejet de A2 chez nous est un test d'ADMISSIBILITÉ déterministe
# (FAR <= plancher de sécurité) combiné à un ARBITRAGE
# multiobjectif -- pas un tirage aléatoire sur l'utilisateur
# légitime. P0 est donc, par construction, déterministe pour un
# contexte fixe répété période après période, là où B5_HAENEL_CALIBRATED
# est stochastique par construction. C'est un résultat à
# interpréter, pas une erreur à corriger.

from dataclasses import dataclass

from physec_dm.case_studies import build_case_study_base_parameters
from physec_dm.channel import calculate_channel_metrics
from physec_dm.decision_maker import (
    calculate_pareto_front,
    evaluate_decision,
    select_from_pareto_front,
)
from physec_dm.models import (
    AuthenticationAction,
    Context,
    Decision,
    KeyAction,
)

from haenel_comparison.haenel_config import (
    HAENEL_P0_CONTEXT_SHADOWING_STD_DB,
    HAENEL_P0_CONTEXT_SNR_DB,
    HAENEL_P0_CONTEXT_SPEED_M_S,
    N_MESSAGES,
)


@dataclass
class P0AuthOnlyMessageEvent:
    message_index: int
    chosen_auth: str            # "A1" ou "A2"
    energy_j: float
    normalized_latency: float
    authentication_robustness: float
    refusal_of_service: bool


def build_haenel_p0_parameters():
    """Paramètres de base du projet (mêmes modèles physiques que
    S1-S5), sans aucune modification des campagnes existantes --
    on part d'une COPIE (build_case_study_base_parameters()
    retourne déjà un nouvel objet à chaque appel)."""

    parameters = build_case_study_base_parameters()

    # Le protocole de Haenel et al. transmet un message toutes les
    # 3 s (PUBLISHED, Section 6.3.2), pas toutes les 60 s comme la
    # valeur par défaut du projet.
    parameters.message_period_s = 3.0

    return parameters


def build_haenel_static_context(parameters, renewal_required=False):
    """Construit le contexte statique unique du banc d'essai
    Haenel et al. : nœud fixe, pas de criticité, pas de suspicion
    de compromission, pas d'attaquant (voir note Section 3 dans
    haenel_config.py). Le même contexte est réutilisé pour les
    100 messages -- Haenel et al. ne décrit aucune variation de
    canal pendant le banc d'essai énergétique (Section 6.3.2)."""

    channel_metrics = calculate_channel_metrics(
        parameters=parameters,
        snr_db=HAENEL_P0_CONTEXT_SNR_DB,
        speed_m_s=HAENEL_P0_CONTEXT_SPEED_M_S,
        shadowing_db=HAENEL_P0_CONTEXT_SHADOWING_STD_DB,
    )

    context = Context(
        snr_db=HAENEL_P0_CONTEXT_SNR_DB,
        doppler_hz=0.0,
        battery_energy_j=1.0e6,   # très grande : ne doit jamais
                                   # binder dans ce banc d'essai
                                   # de 300 s (voir README).
        criticality=0,
        key_age_s=0.0,
        messages_with_current_key=0,
        rff_profile_available=True,
        renewal_required=renewal_required,
        key_expired=False,
        compromise_suspected=False,
        key_deadline_s=parameters.message_period_s * 1000.0,
        remaining_duty_cycle_airtime_s=1.0e6,
    )

    return context, channel_metrics


def select_p0_auth_only_decision(context, parameters, rho_ab):
    """Restreint les candidats de P0 à {A1-K0, A2-K0} (gestion de
    clé figée), puis applique la VRAIE logique de sélection du
    Decision Maker (Pareto + Tchebycheff pondéré, mêmes poids que
    la campagne principale) sur ces deux seuls candidats."""

    candidate_decisions = [
        Decision(AuthenticationAction.A1, KeyAction.K0),
        Decision(AuthenticationAction.A2, KeyAction.K0),
    ]

    all_evaluations = [
        evaluate_decision(
            decision=decision,
            context=context,
            parameters=parameters,
            rho_ab=rho_ab,
            enforce_far_floor=True,
        )
        for decision in candidate_decisions
    ]

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


def simulate_p0_auth_only(n_messages=N_MESSAGES):
    """Fait tourner P0 (restreint à K0) sur n_messages répétitions
    du contexte statique Haenel et al. Retourne la liste des
    P0AuthOnlyMessageEvent, un par message -- même format d'esprit
    que haenel_b5.simulate_haenel_reference_messages, pour
    faciliter la comparaison directe."""

    parameters = build_haenel_p0_parameters()
    context, channel_metrics = build_haenel_static_context(
        parameters
    )

    events = []

    for message_index in range(n_messages):

        selected_evaluation, _all = select_p0_auth_only_decision(
            context=context,
            parameters=parameters,
            rho_ab=channel_metrics.rho_ab,
        )

        if selected_evaluation is None:
            events.append(
                P0AuthOnlyMessageEvent(
                    message_index=message_index,
                    chosen_auth=None,
                    energy_j=None,
                    normalized_latency=None,
                    authentication_robustness=None,
                    refusal_of_service=True,
                )
            )
            continue

        events.append(
            P0AuthOnlyMessageEvent(
                message_index=message_index,
                chosen_auth=(
                    selected_evaluation.decision
                    .authentication_action.value
                ),
                energy_j=(
                    selected_evaluation.cost_metrics
                    .expected_energy_j
                ),
                normalized_latency=(
                    selected_evaluation.cost_metrics
                    .normalized_latency
                ),
                authentication_robustness=(
                    selected_evaluation.authentication_metrics
                    .authentication_robustness
                ),
                refusal_of_service=False,
            )
        )

    return events


def summarize_p0_auth_only_events(events):

    n_messages = len(events)
    served_events = [
        event for event in events if not event.refusal_of_service
    ]

    n_a1 = sum(
        1 for event in served_events if event.chosen_auth == "A1"
    )
    n_a2 = sum(
        1 for event in served_events if event.chosen_auth == "A2"
    )
    n_refusal = n_messages - len(served_events)

    total_energy_j = sum(
        event.energy_j for event in served_events
    )

    return {
        "n_messages": n_messages,
        "n_a1": n_a1,
        "n_a2": n_a2,
        "n_refusal_of_service": n_refusal,
        "total_energy_j": total_energy_j,
        "total_energy_mJ": total_energy_j * 1000.0,
        "mean_energy_per_message_mJ": (
            (total_energy_j * 1000.0) / len(served_events)
            if served_events
            else None
        ),
    }


if __name__ == "__main__":

    events = simulate_p0_auth_only()
    summary = summarize_p0_auth_only_events(events)

    print("P0_AUTH_ONLY sur le contexte statique Haenel et al. "
          f"({summary['n_messages']} messages) :")
    print(f"  A1 (MAC)  : {summary['n_a1']}")
    print(f"  A2 (RFF)  : {summary['n_a2']}")
    print(f"  Refus     : {summary['n_refusal_of_service']}")
    print(
        f"  Énergie totale : {summary['total_energy_mJ']:.3f} mJ "
        f"sur 300 s"
    )
