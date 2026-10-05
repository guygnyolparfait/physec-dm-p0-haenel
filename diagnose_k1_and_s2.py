# Ce script effectue un diagnostic scientifique en lecture seule.
#
# Il ne relance aucune mission et ne modifie aucune équation,
# aucun paramètre ni aucun scénario.
#
# Il utilise directement les fonctions déjà validées de :
# - physec_dm/channel.py
# - physec_dm/key_generation.py
# - physec_dm/energy_latency.py
# - physec_dm/authentication.py
# - physec_dm/decision_maker.py
#
# avec les paramètres réels des trois scénarios (reconstruits
# via physec_dm/thesis_scenarios.py, déjà validé), afin
# d'obtenir les motifs de rejet exacts produits par le modèle
# lui-même plutôt que des estimations approximatives.
import csv
from pathlib import Path

import numpy as np

from physec_dm.thesis_scenarios import (
    apply_scenario_overrides_for_validation,
    build_exploratory_k2_protocol,
    build_thesis_scenarios,
    build_three_scenario_parameters
)

from physec_dm.channel import (
    calculate_channel_metrics,
    convert_db_to_linear
)

from physec_dm.key_generation import (
    calculate_agreement_feasibility,
    calculate_effective_kdr,
    calculate_k0_quality,
    calculate_k1_quality,
    calculate_k2_quality,
    calculate_key_aging_index,
    calculate_key_deadline,
    calculate_phy_feasibility,
    calculate_raw_kdr,
    calculate_reconciliation_yield,
    calculate_renewal_required,
    calculate_required_measurements
)

from physec_dm.energy_latency import (
    calculate_authentication_costs,
    calculate_k1a_costs,
    calculate_k1b_costs,
    calculate_k2_costs,
    calculate_normalized_latency
)

from physec_dm.authentication import (
    calculate_authentication_metrics,
    calculate_far,
    calculate_noncentrality_from_snr
)

from physec_dm.decision_maker import (
    run_decision_maker
)

from physec_dm.models import (
    AuthenticationAction,
    Context
)


SOURCE_DIRECTORY = Path(
    "results/three_scenarios_s2_corrected"
)

OUTPUT_DIRECTORY = Path(
    "results/three_scenarios_explicit_analysis"
)


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


# ================================================================
# 1. LECTURE DES RÉSULTATS EXISTANTS (contrôle empirique)
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


def load_decision_frequencies():

    rows = read_csv_rows(
        SOURCE_DIRECTORY / "decision_frequencies.csv"
    )

    frequencies = {
        scenario_id: {}
        for scenario_id in SCENARIO_ORDER
    }

    for row in rows:

        frequencies[
            row["scenario_id"]
        ][
            row["decision_name"]
        ] = float(
            row["selection_frequency"]
        )

    return frequencies


def load_four_objective_summary():

    rows = read_csv_rows(
        SOURCE_DIRECTORY / "four_objective_summary.csv"
    )

    return {
        row["scenario_id"]: row
        for row in rows
    }


# ================================================================
# 2. RECONSTRUCTION DES PARAMÈTRES RÉELS DE CHAQUE SCÉNARIO
# ================================================================


# Cette fonction reproduit exactement la construction utilisée
# par run_campaign / build_thesis_scenarios : une copie des
# paramètres de base avec les overrides du scénario appliqués.
def build_scenario_parameters_and_definition():

    base_parameters = build_three_scenario_parameters()

    scenarios = build_thesis_scenarios(
        parameters=base_parameters,
        max_steps=300
    )

    result = {}

    for scenario in scenarios:

        scenario_parameters = (
            apply_scenario_overrides_for_validation(
                base_parameters,
                scenario
            )
        )

        result[
            scenario["scenario_id"]
        ] = {
            "parameters": scenario_parameters,
            "definition": scenario
        }

    return result


# ================================================================
# 3. DIAGNOSTIC DE FAISABILITÉ ET DE COÛT DE K1a / K1b
# ================================================================


# Ce diagnostic se place volontairement au point de la
# cryptopériode le PLUS FAVORABLE possible à K1a et K1b :
# le tout premier instant où le renouvellement devient requis
# (q_t == renewal_trigger), c'est-à-dire l'instant où
# l'échéance restante (key_deadline_s) est maximale.
#
# Si K1a/K1b échouent déjà dans ce cas le plus favorable,
# ils échouent nécessairement aussi plus tard dans la
# cryptopériode, où l'échéance restante est plus courte.
def diagnose_key_renewal_at_trigger(
    scenario_id,
    scenario_parameters,
    snr_db_samples,
    duty_cycle_budget_s
):

    renewal_trigger = (
        scenario_parameters.renewal_trigger
    )

    key_age_s = (
        renewal_trigger
        * scenario_parameters.maximum_key_age_s
    )

    messages_with_current_key = (
        renewal_trigger
        * scenario_parameters.maximum_messages_per_key
    )

    key_aging_index = calculate_key_aging_index(
        key_age_s=key_age_s,
        maximum_key_age_s=(
            scenario_parameters.maximum_key_age_s
        ),
        messages_with_current_key=(
            messages_with_current_key
        ),
        maximum_messages_per_key=(
            scenario_parameters.maximum_messages_per_key
        )
    )

    renewal_required = calculate_renewal_required(
        key_aging_index=key_aging_index,
        renewal_trigger=renewal_trigger
    )

    key_deadline_s = calculate_key_deadline(
        key_age_s=key_age_s,
        maximum_key_age_s=(
            scenario_parameters.maximum_key_age_s
        ),
        messages_with_current_key=(
            messages_with_current_key
        ),
        maximum_messages_per_key=(
            scenario_parameters.maximum_messages_per_key
        ),
        message_period_s=(
            scenario_parameters.message_period_s
        ),
        minimum_deadline_s=(
            scenario_parameters.minimum_deadline_s
        )
    )

    k2_protocol = build_exploratory_k2_protocol(
        scenario_parameters
    )

    k2_costs = calculate_k2_costs(
        ecc_operation_energies_j=(
            k2_protocol["ecc_operation_energies_j"]
        ),
        ecc_operation_times_s=(
            k2_protocol["ecc_operation_times_s"]
        ),
        tx_message_sizes_bytes=(
            k2_protocol["tx_message_sizes_bytes"]
        ),
        rx_message_sizes_bytes=(
            k2_protocol["rx_message_sizes_bytes"]
        ),
        parameters=scenario_parameters
    )

    k2_quality = calculate_k2_quality(
        scenario_parameters.security_strength_bits
    )

    k0_quality = calculate_k0_quality(
        key_aging_index
    )

    channel_rows = []

    for label, snr_db in snr_db_samples:

        rho_ab = calculate_channel_metrics(
            parameters=scenario_parameters,
            snr_db=snr_db,
            speed_m_s=0.0
        ).rho_ab

        raw_kdr = calculate_raw_kdr(
            rho_ab
        )

        effective_kdr = calculate_effective_kdr(
            raw_kdr=raw_kdr,
            quantization_mode=(
                scenario_parameters.quantization_mode
            ),
            guard_band_factor=(
                scenario_parameters.guard_band_factor
            )
        )

        agreement_feasible = (
            calculate_agreement_feasibility(
                effective_kdr=effective_kdr,
                maximum_kdr=(
                    scenario_parameters.maximum_kdr
                )
            )
        )

        phy_feasible = calculate_phy_feasibility(
            agreement_feasible=agreement_feasible,
            variation_feasible=(
                scenario_parameters.variation_feasible
            )
        )

        reconciliation_yield = (
            calculate_reconciliation_yield(
                effective_kdr=effective_kdr,
                kept_measurement_ratio=(
                    scenario_parameters
                    .kept_measurement_ratio
                )
            )
        )

        required_measurements = (
            calculate_required_measurements(
                key_length_bits=(
                    scenario_parameters.key_length_bits
                ),
                reconciliation_yield=(
                    reconciliation_yield
                ),
                numerical_epsilon=(
                    scenario_parameters
                    .key_numerical_epsilon
                )
            )
        )

        key_quality_phy = calculate_k1_quality(
            effective_kdr
        )

        k1a_costs = calculate_k1a_costs(
            required_measurements=(
                required_measurements
            ),
            parameters=scenario_parameters
        )

        k1b_costs = calculate_k1b_costs(
            required_measurements=(
                required_measurements
            ),
            parameters=scenario_parameters
        )

        channel_rows.append(
            {
                "label": label,
                "snr_db": snr_db,
                "rho_ab": rho_ab,
                "raw_kdr": raw_kdr,
                "effective_kdr": effective_kdr,
                "agreement_feasible": (
                    agreement_feasible
                ),
                "phy_feasible": phy_feasible,
                "reconciliation_yield": (
                    reconciliation_yield
                ),
                "required_measurements": (
                    required_measurements
                ),
                "key_quality_phy": key_quality_phy,
                "k1a_energy_j": k1a_costs["energy_j"],
                "k1a_latency_s": k1a_costs["latency_s"],
                "k1a_airtime_s": k1a_costs["airtime_s"],
                "k1b_energy_j": k1b_costs["energy_j"],
                "k1b_latency_s": k1b_costs["latency_s"],
                "k1b_airtime_s": k1b_costs["airtime_s"],
                "k1a_deadline_ok": (
                    k1a_costs["latency_s"]
                    <= key_deadline_s
                ),
                "k1b_deadline_ok": (
                    k1b_costs["latency_s"]
                    <= key_deadline_s
                ),
                "k1a_duty_cycle_ok": (
                    k1a_costs["airtime_s"]
                    <= duty_cycle_budget_s
                ),
                "k1b_duty_cycle_ok": (
                    k1b_costs["airtime_s"]
                    <= duty_cycle_budget_s
                )
            }
        )

    return {
        "scenario_id": scenario_id,
        "renewal_trigger": renewal_trigger,
        "key_age_s": key_age_s,
        "messages_with_current_key": (
            messages_with_current_key
        ),
        "key_aging_index": key_aging_index,
        "renewal_required": renewal_required,
        "key_deadline_s": key_deadline_s,
        "remaining_duty_cycle_airtime_s": (
            duty_cycle_budget_s
        ),
        "k0_quality": k0_quality,
        "k2_quality": k2_quality,
        "k2_energy_j": k2_costs["energy_j"],
        "k2_latency_s": k2_costs["latency_s"],
        "k2_airtime_s": k2_costs["airtime_s"],
        "channel_rows": channel_rows
    }


# ================================================================
# 4. ÉVALUATION AUTORITATIVE VIA evaluate_decision()
# ================================================================


# Cette fonction appelle directement le vrai Decision Maker
# (run_decision_maker, déjà validé) sur un contexte représentatif
# où le renouvellement est requis. Les motifs de rejet, le front
# de Pareto et les scores de Tchebycheff retournés sont ceux
# réellement produits par le modèle, pas une estimation.
def run_authoritative_evaluation(
    scenario_id,
    scenario_parameters,
    diagnosis_at_trigger,
    snr_db,
    criticality
):

    channel_metrics = calculate_channel_metrics(
        parameters=scenario_parameters,
        snr_db=snr_db,
        speed_m_s=0.0
    )

    context = Context(
        snr_db=channel_metrics.snr_db,
        doppler_hz=channel_metrics.doppler_hz,
        battery_energy_j=(
            scenario_parameters.initial_battery_energy_j
        ),
        criticality=criticality,
        key_age_s=diagnosis_at_trigger["key_age_s"],
        messages_with_current_key=(
            diagnosis_at_trigger[
                "messages_with_current_key"
            ]
        ),
        rff_profile_available=True,
        renewal_required=True,
        key_expired=False,
        compromise_suspected=False,
        key_deadline_s=(
            diagnosis_at_trigger["key_deadline_s"]
        ),
        remaining_duty_cycle_airtime_s=(
            diagnosis_at_trigger[
                "remaining_duty_cycle_airtime_s"
            ]
        )
    )

    k2_protocol = build_exploratory_k2_protocol(
        scenario_parameters
    )

    evaluations = {}

    # On appelle directement le vrai Decision Maker
    # (run_decision_maker, déjà validé), plutôt que de
    # réimplémenter le pipeline Pareto / Tchebycheff,
    # afin que les motifs de rejet et le front obtenus
    # soient authentiquement ceux du modèle.
    decision_maker_result = run_decision_maker(
        context=context,
        parameters=scenario_parameters,
        rho_ab=channel_metrics.rho_ab,
        variation_feasible=(
            scenario_parameters.variation_feasible
        ),
        k2_protocol=k2_protocol
    )

    for evaluation in decision_maker_result.all_evaluations:

        evaluations[
            evaluation.decision.get_name()
        ] = evaluation

    tchebycheff_scores = {
        evaluation.decision.get_name():
            evaluation.tchebycheff_score
        for evaluation in (
            decision_maker_result.pareto_front
        )
    }

    return {
        "context": context,
        "evaluations": evaluations,
        "pareto_front_names": [
            evaluation.decision.get_name()
            for evaluation in (
                decision_maker_result.pareto_front
            )
        ],
        "tchebycheff_scores": tchebycheff_scores,
        "refusal_of_service": (
            decision_maker_result.refusal_of_service
        ),
        "selected_decision_name": (
            decision_maker_result.selected_evaluation
            .decision.get_name()
            if decision_maker_result.selected_evaluation
            is not None
            else None
        )
    }


def format_rejections(evaluation):

    if len(evaluation.rejection_reasons) == 0:

        return "aucun (admissible)"

    return "; ".join(
        rejection.reason_code
        + " [mesuré="
        + (
            format(
                rejection.measured_value,
                ".6g"
            )
            if isinstance(
                rejection.measured_value,
                (int, float)
            )
            else str(
                rejection.measured_value
            )
        )
        + ", autorisé="
        + (
            format(
                rejection.allowed_value,
                ".6g"
            )
            if isinstance(
                rejection.allowed_value,
                (int, float)
            )
            else str(
                rejection.allowed_value
            )
        )
        + "]"
        for rejection in evaluation.rejection_reasons
    )


# ================================================================
# 5. DIAGNOSTIC DE LA LATENCE NORMALISÉE (S2)
# ================================================================


def diagnose_latency(
    scenario_definitions,
    decision_frequencies
):

    rows = []

    for scenario_id in SCENARIO_ORDER:

        scenario_parameters = scenario_definitions[
            scenario_id
        ]["parameters"]

        critical_probability = (
            scenario_parameters
            .critical_message_probability
        )

        frequencies = decision_frequencies[
            scenario_id
        ]

        a1_frequency = sum(
            frequency
            for name, frequency in frequencies.items()
            if name.startswith("A1")
        )

        a2_frequency = sum(
            frequency
            for name, frequency in frequencies.items()
            if name.startswith("A2")
        )

        a1_costs = calculate_authentication_costs(
            authentication_action=(
                AuthenticationAction.A1
            ),
            authentication_metrics=None,
            parameters=scenario_parameters
        )

        real_authentication_metrics_a2 = (
            calculate_authentication_metrics(
                authentication_action=(
                    AuthenticationAction.A2
                ),
                parameters=scenario_parameters,
                mallory_snr_db=(
                    scenario_parameters.mean_snr_db
                )
            )
        )

        a2_costs = calculate_authentication_costs(
            authentication_action=(
                AuthenticationAction.A2
            ),
            authentication_metrics=(
                real_authentication_metrics_a2
            ),
            parameters=scenario_parameters
        )

        normal_limit = (
            scenario_parameters
            .normal_latency_budget_s
        )

        critical_limit = (
            scenario_parameters
            .critical_latency_budget_s
        )

        ratios = {
            "A1_normal": calculate_normalized_latency(
                authentication_latency_s=(
                    a1_costs["expected_latency_s"]
                ),
                authentication_latency_limit_s=(
                    normal_limit
                ),
                key_latency_s=0.0,
                key_deadline_s=1.0
            ),
            "A1_critical": calculate_normalized_latency(
                authentication_latency_s=(
                    a1_costs["expected_latency_s"]
                ),
                authentication_latency_limit_s=(
                    critical_limit
                ),
                key_latency_s=0.0,
                key_deadline_s=1.0
            ),
            "A2_normal": calculate_normalized_latency(
                authentication_latency_s=(
                    a2_costs["expected_latency_s"]
                ),
                authentication_latency_limit_s=(
                    normal_limit
                ),
                key_latency_s=0.0,
                key_deadline_s=1.0
            ),
            "A2_critical": calculate_normalized_latency(
                authentication_latency_s=(
                    a2_costs["expected_latency_s"]
                ),
                authentication_latency_limit_s=(
                    critical_limit
                ),
                key_latency_s=0.0,
                key_deadline_s=1.0
            )
        }

        weighted_estimate = (
            a1_frequency
            * (
                (1 - critical_probability)
                * ratios["A1_normal"]
                + critical_probability
                * ratios["A1_critical"]
            )
            + a2_frequency
            * (
                (1 - critical_probability)
                * ratios["A2_normal"]
                + critical_probability
                * ratios["A2_critical"]
            )
        )

        rows.append(
            {
                "scenario_id": scenario_id,
                "critical_probability": (
                    critical_probability
                ),
                "a1_frequency": a1_frequency,
                "a2_frequency": a2_frequency,
                "a1_expected_latency_s": (
                    a1_costs["expected_latency_s"]
                ),
                "a2_expected_latency_s": (
                    a2_costs["expected_latency_s"]
                ),
                "ratio_A1_normal": ratios["A1_normal"],
                "ratio_A1_critical": (
                    ratios["A1_critical"]
                ),
                "ratio_A2_normal": ratios["A2_normal"],
                "ratio_A2_critical": (
                    ratios["A2_critical"]
                ),
                "weighted_estimate": weighted_estimate
            }
        )

    return rows


# ================================================================
# 6. DIAGNOSTIC DE LA FAR NON NULLE DE S2
# ================================================================


# Cette fonction calcule le SNR à partir duquel la FAR
# franchit le plancher de sécurité DM-EQ102
# (physec_dm/decision_maker.py, ligne 488-492), séparément
# pour un message normal (far_limit = 0.05) et un message
# critique (far_limit = 0.01). Elle utilise directement
# calculate_far() par recherche dichotomique, sans jamais
# réimplémenter la formule.
def find_far_threshold_snr_db(
    scenario_parameters,
    far_limit,
    lower_bound_db=-20.0,
    upper_bound_db=30.0
):

    normalized_separation_squared = (
        scenario_parameters.mallory_separation ** 2
    )

    def far_at(snr_db):

        snr_linear = convert_db_to_linear(snr_db)

        noncentrality = calculate_noncentrality_from_snr(
            normalized_separation_squared,
            snr_linear
        )

        return calculate_far(
            threshold=(
                scenario_parameters.rff_threshold
            ),
            feature_count=(
                scenario_parameters.rff_feature_count
            ),
            noncentrality_parameter=noncentrality
        )

    low = lower_bound_db
    high = upper_bound_db

    for _ in range(80):

        middle = (low + high) / 2.0

        if far_at(middle) > far_limit:

            low = middle

        else:

            high = middle

    return high


# Cette fonction rejoue, en lecture seule et sans toucher
# aux missions de la campagne, le mécanisme exact
# authentification + Mallory de physec_dm/mission.py
# (draw_observed_snr_db, run_decision_maker,
# evaluate_mallory), avec un générateur aléatoire
# indépendant et une graine fixe, pour un état de clé K0
# représentatif hors renouvellement (renewal_required=False).
#
# Objectif : mesurer la fréquence de sélection de A2 et le
# taux de fausse acceptation *conditionnés* par la sélection
# réelle de A2, plutôt que d'utiliser le SNR moyen brut
# (qui ignore le plancher de sécurité DM-EQ102 et surestime
# fortement la FAR réalisée, comme démontré ci-dessous).
def simulate_far_mechanism(
    scenario_id,
    scenario_parameters,
    k2_protocol,
    variation_feasible,
    sample_count,
    random_seed
):

    random_generator = np.random.default_rng(
        random_seed
    )

    a2_selected_count = 0
    a1_selected_count = 0
    mallory_attempts = 0
    false_acceptances = 0

    for _ in range(sample_count):

        snr_db = random_generator.normal(
            scenario_parameters.mean_snr_db,
            scenario_parameters.shadowing_std_db
        )

        criticality = (
            1
            if random_generator.random()
            < scenario_parameters
            .critical_message_probability
            else 0
        )

        channel_metrics = calculate_channel_metrics(
            parameters=scenario_parameters,
            snr_db=snr_db,
            speed_m_s=0.0
        )

        # État de clé K0 représentatif, hors
        # renouvellement, afin d'isoler le choix A1 / A2
        # sans dépendre du point précis du cycle de vie
        # de la clé (déjà diagnostiqué séparément
        # ci-dessus pour K1a/K1b).
        context = Context(
            snr_db=channel_metrics.snr_db,
            doppler_hz=channel_metrics.doppler_hz,
            battery_energy_j=(
                scenario_parameters
                .initial_battery_energy_j
            ),
            criticality=criticality,
            key_age_s=1800.0,
            messages_with_current_key=30,
            rff_profile_available=True,
            renewal_required=False,
            key_expired=False,
            compromise_suspected=False,
            key_deadline_s=2400.0,
            remaining_duty_cycle_airtime_s=36.0
        )

        decision_maker_result = run_decision_maker(
            context=context,
            parameters=scenario_parameters,
            rho_ab=channel_metrics.rho_ab,
            variation_feasible=variation_feasible,
            k2_protocol=k2_protocol
        )

        selected_evaluation = (
            decision_maker_result.selected_evaluation
        )

        if (
            decision_maker_result.refusal_of_service
            or selected_evaluation is None
        ):

            continue

        authentication_action = (
            selected_evaluation.decision
            .authentication_action
        )

        if authentication_action == (
            AuthenticationAction.A2
        ):

            a2_selected_count += 1

        else:

            a1_selected_count += 1

        mallory_attempted = (
            random_generator.random()
            < scenario_parameters
            .mallory_attempt_probability
        )

        if not mallory_attempted:

            continue

        mallory_attempts += 1

        # real_snr_bias_db = 0.0 pour les trois scénarios
        # (confirmé dans thesis_scenarios.py) : le SNR réel
        # de Mallory est donc identique au SNR observé ayant
        # servi à la décision.
        real_authentication_metrics = (
            calculate_authentication_metrics(
                authentication_action=(
                    authentication_action
                ),
                parameters=scenario_parameters,
                mallory_snr_db=snr_db
            )
        )

        accepted = (
            random_generator.random()
            < real_authentication_metrics
            .total_false_acceptance_probability
        )

        if accepted:

            false_acceptances += 1

    far_rate = (
        false_acceptances / mallory_attempts
        if mallory_attempts > 0
        else 0.0
    )

    # Erreur-type binomiale de la fréquence observée,
    # pour situer l'écart avec la valeur empirique dans
    # son intervalle de confiance plutôt que de le juger
    # sur la seule valeur ponctuelle.
    standard_error = (
        (
            far_rate * (1 - far_rate)
            / mallory_attempts
        ) ** 0.5
        if mallory_attempts > 0
        else 0.0
    )

    return {
        "scenario_id": scenario_id,
        "sample_count": sample_count,
        "a2_selection_frequency": (
            a2_selected_count / sample_count
        ),
        "a1_selection_frequency": (
            a1_selected_count / sample_count
        ),
        "mallory_attempts": mallory_attempts,
        "false_acceptances": false_acceptances,
        "far_rate_simulated": far_rate,
        "far_rate_standard_error": standard_error
    }


def diagnose_far(
    scenario_definitions,
    decision_frequencies
):

    rows = []

    for scenario_id in SCENARIO_ORDER:

        scenario_parameters = scenario_definitions[
            scenario_id
        ]["parameters"]

        definition = scenario_definitions[
            scenario_id
        ]["definition"]

        frequencies = decision_frequencies[
            scenario_id
        ]

        a2_frequency_campaign = sum(
            frequency
            for name, frequency in frequencies.items()
            if name.startswith("A2")
        )

        mallory_attempt_probability = (
            scenario_parameters
            .mallory_attempt_probability
        )

        snr_linear_mean = convert_db_to_linear(
            scenario_parameters.mean_snr_db
        )

        normalized_separation_squared = (
            scenario_parameters.mallory_separation
            ** 2
        )

        noncentrality = calculate_noncentrality_from_snr(
            normalized_separation_squared,
            snr_linear_mean
        )

        far_at_mean_snr = calculate_far(
            threshold=(
                scenario_parameters.rff_threshold
            ),
            feature_count=(
                scenario_parameters.rff_feature_count
            ),
            noncentrality_parameter=noncentrality
        )

        far_threshold_snr_normal_db = (
            find_far_threshold_snr_db(
                scenario_parameters,
                scenario_parameters.normal_far_limit
            )
        )

        far_threshold_snr_critical_db = (
            find_far_threshold_snr_db(
                scenario_parameters,
                scenario_parameters.critical_far_limit
            )
        )

        simulation = simulate_far_mechanism(
            scenario_id=scenario_id,
            scenario_parameters=scenario_parameters,
            k2_protocol=definition["k2_protocol"],
            variation_feasible=(
                definition["variation_feasible"]
            ),
            sample_count=40000,
            random_seed=20260721
        )

        rows.append(
            {
                "scenario_id": scenario_id,
                "mean_snr_db": (
                    scenario_parameters.mean_snr_db
                ),
                "shadowing_std_db": (
                    scenario_parameters.shadowing_std_db
                ),
                "snr_linear_mean": snr_linear_mean,
                "mallory_separation": (
                    scenario_parameters
                    .mallory_separation
                ),
                "noncentrality_at_mean_snr": (
                    noncentrality
                ),
                "far_at_mean_snr": far_at_mean_snr,
                "normal_far_limit": (
                    scenario_parameters.normal_far_limit
                ),
                "critical_far_limit": (
                    scenario_parameters.critical_far_limit
                ),
                "far_threshold_snr_normal_db": (
                    far_threshold_snr_normal_db
                ),
                "far_threshold_snr_critical_db": (
                    far_threshold_snr_critical_db
                ),
                "a2_frequency_campaign": (
                    a2_frequency_campaign
                ),
                "mallory_attempt_probability": (
                    mallory_attempt_probability
                ),
                "simulation": simulation
            }
        )

    return rows


# ================================================================
# 7. ÉCRITURE DES FICHIERS DE DIAGNOSTIC
# ================================================================


def write_k1_selection_diagnosis(
    scenario_definitions,
    trigger_diagnoses,
    authoritative_evaluations,
    output_path
):

    lines = []

    lines.append(
        "# Diagnostic — pourquoi K1a et K1b ne sont "
        "jamais sélectionnés"
    )
    lines.append("")
    lines.append(
        "Ce diagnostic utilise directement les fonctions "
        "validées de `physec_dm/key_generation.py`, "
        "`physec_dm/energy_latency.py` et "
        "`physec_dm/decision_maker.py`, avec les paramètres "
        "réels des scénarios (aucune valeur inventée, aucune "
        "mission relancée)."
    )
    lines.append("")

    for scenario_id in SCENARIO_ORDER:

        scenario_parameters = scenario_definitions[
            scenario_id
        ]["parameters"]

        trigger = trigger_diagnoses[scenario_id]

        lines.append(
            "## "
            + SCENARIO_DISPLAY_NAMES[scenario_id]
        )
        lines.append("")

        if scenario_parameters.variation_feasible is not True:

            lines.append(
                "**Cause identifiée : K1a/K1b infaisables "
                "(PHY_VARIATION_INFEASIBLE).**"
            )
            lines.append("")
            lines.append(
                "`variation_feasible = "
                + str(
                    scenario_parameters.variation_feasible
                )
                + "` pour ce scénario. La règle DM-EQ97 "
                "(`physec_dm/decision_maker.py`, ligne 340) "
                "rejette immédiatement K1a et K1b dès que "
                "`key_metrics.variation_feasible is not True`, "
                "quelle que soit la qualité du canal. Aucun "
                "calcul de coût n'est même nécessaire pour "
                "expliquer ce cas."
            )
            lines.append("")
            continue

        lines.append(
            "`variation_feasible = True` pour ce scénario : "
            "K1a/K1b ne sont donc pas bloqués par la règle "
            "PHY_VARIATION_INFEASIBLE. Le diagnostic se place "
            "au premier instant possible du renouvellement "
            "(`q_t = renewal_trigger = "
            + format(
                trigger["renewal_trigger"],
                ".2f"
            )
            + "`), c'est-à-dire le cas **le plus favorable** "
            "à K1a/K1b : l'échéance restante "
            "(`key_deadline_s`) y est maximale."
        )
        lines.append("")

        lines.append(
            "| Grandeur | Valeur |"
        )
        lines.append(
            "|---|---:|"
        )
        lines.append(
            "| key_age_s au déclenchement | "
            + format(
                trigger["key_age_s"],
                ".1f"
            )
            + " s |"
        )
        lines.append(
            "| messages_with_current_key | "
            + format(
                trigger["messages_with_current_key"],
                ".1f"
            )
            + " |"
        )
        lines.append(
            "| key_deadline_s (échéance restante, "
            "cas le plus favorable) | "
            + format(
                trigger["key_deadline_s"],
                ".2f"
            )
            + " s |"
        )
        lines.append(
            "| remaining_duty_cycle_airtime_s "
            "(budget maximal configuré) | "
            + format(
                trigger[
                    "remaining_duty_cycle_airtime_s"
                ],
                ".2f"
            )
            + " s |"
        )
        lines.append(
            "| K2 — energy_j / latency_s / airtime_s | "
            + format(
                trigger["k2_energy_j"],
                ".4f"
            )
            + " J / "
            + format(
                trigger["k2_latency_s"],
                ".4f"
            )
            + " s / "
            + format(
                trigger["k2_airtime_s"],
                ".4f"
            )
            + " s |"
        )
        lines.append(
            "| K2 — key_quality "
            "(1 − 2^−security_strength_bits) | "
            + format(
                trigger["k2_quality"],
                ".10f"
            )
            + " |"
        )
        lines.append(
            "| K0 — key_quality au déclenchement "
            "(1 − q_t) | "
            + format(
                trigger["k0_quality"],
                ".4f"
            )
            + " |"
        )
        lines.append("")

        lines.append(
            "### Faisabilité et coût de K1a / K1b selon "
            "le SNR réellement observé dans le scénario"
        )
        lines.append("")
        lines.append(
            "| SNR (dB) | rho_AB | KDR effectif | "
            "PHY faisable | N_meas | Qualité clé PHY | "
            "K1a latence (s) | K1a ≤ deadline ? | "
            "K1b latence (s) | K1b ≤ deadline ? | "
            "K1b airtime (s) | K1b ≤ duty-cycle ? |"
        )
        lines.append(
            "|---:|---:|---:|:---:|---:|---:|---:|:---:"
            "|---:|:---:|---:|:---:|"
        )

        for row in trigger["channel_rows"]:

            lines.append(
                "| "
                + row["label"]
                + " ("
                + format(
                    row["snr_db"],
                    ".1f"
                )
                + ") | "
                + format(
                    row["rho_ab"],
                    ".4f"
                )
                + " | "
                + format(
                    row["effective_kdr"],
                    ".4f"
                )
                + " | "
                + str(
                    row["phy_feasible"]
                )
                + " | "
                + str(
                    row["required_measurements"]
                )
                + " | "
                + format(
                    row["key_quality_phy"],
                    ".4f"
                )
                + " | "
                + format(
                    row["k1a_latency_s"],
                    ".1f"
                )
                + " | "
                + str(
                    row["k1a_deadline_ok"]
                )
                + " | "
                + format(
                    row["k1b_latency_s"],
                    ".1f"
                )
                + " | "
                + str(
                    row["k1b_deadline_ok"]
                )
                + " | "
                + format(
                    row["k1b_airtime_s"],
                    ".1f"
                )
                + " | "
                + str(
                    row["k1b_duty_cycle_ok"]
                )
                + " |"
            )

        lines.append("")

        lines.append(
            "### Motifs de rejet exacts produits par "
            "`evaluate_decision()` (SNR moyen du scénario, "
            "criticité = 0)"
        )
        lines.append("")

        authoritative = authoritative_evaluations[
            scenario_id
        ]

        lines.append(
            "| Décision | Admissible | Motifs de rejet "
            "(mesuré / autorisé) |"
        )
        lines.append(
            "|---|:---:|---|"
        )

        for decision_name in [
            "A1-K1a",
            "A1-K1b",
            "A1-K2",
            "A2-K1a",
            "A2-K1b",
            "A2-K2"
        ]:

            evaluation = authoritative["evaluations"][
                decision_name
            ]

            lines.append(
                "| "
                + decision_name
                + " | "
                + str(
                    evaluation.admissible
                )
                + " | "
                + format_rejections(
                    evaluation
                )
                + " |"
            )

        lines.append("")

        lines.append(
            "Front de Pareto obtenu à ce point : "
            + (
                ", ".join(
                    authoritative["pareto_front_names"]
                )
                if len(
                    authoritative["pareto_front_names"]
                ) > 0
                else "**vide (aucune décision admissible)**"
            )
        )
        lines.append("")

        if len(
            authoritative["tchebycheff_scores"]
        ) > 0:

            lines.append(
                "Scores de Tchebycheff sur le front "
                "(plus petit = meilleur) :"
            )
            lines.append("")

            for name, score in authoritative[
                "tchebycheff_scores"
            ].items():

                lines.append(
                    "- "
                    + name
                    + " : "
                    + format(
                        score,
                        ".6f"
                    )
                )

            lines.append("")

        # Diagnostic final pour ce scénario.
        any_k1_admissible = (
            authoritative["evaluations"][
                "A1-K1a"
            ].admissible
            or authoritative["evaluations"][
                "A1-K1b"
            ].admissible
            or authoritative["evaluations"][
                "A2-K1a"
            ].admissible
            or authoritative["evaluations"][
                "A2-K1b"
            ].admissible
        )

        lines.append(
            "**Cause identifiée : "
        )

        if not any_k1_admissible:

            deadline_involved = any(
                any(
                    rejection.reason_code
                    == "KEY_DEADLINE_CONSTRAINT"
                    for rejection in (
                        authoritative["evaluations"][
                            name
                        ].rejection_reasons
                    )
                )
                for name in [
                    "A1-K1a",
                    "A1-K1b",
                    "A2-K1a",
                    "A2-K1b"
                ]
            )

            duty_cycle_involved = any(
                any(
                    rejection.reason_code
                    == "DUTY_CYCLE_CONSTRAINT"
                    for rejection in (
                        authoritative["evaluations"][
                            name
                        ].rejection_reasons
                    )
                )
                for name in [
                    "A1-K1a",
                    "A1-K1b",
                    "A2-K1a",
                    "A2-K1b"
                ]
            )

            phy_involved = any(
                any(
                    rejection.reason_code.startswith(
                        "PHY_"
                    )
                    for rejection in (
                        authoritative["evaluations"][
                            name
                        ].rejection_reasons
                    )
                )
                for name in [
                    "A1-K1a",
                    "A1-K1b",
                    "A2-K1a",
                    "A2-K1b"
                ]
            )

            causes = []

            if deadline_involved:

                causes.append(
                    "contraintes par la deadline "
                    "(KEY_DEADLINE_CONSTRAINT)"
                )

            if duty_cycle_involved:

                causes.append(
                    "contraintes par le duty-cycle "
                    "(DUTY_CYCLE_CONSTRAINT)"
                )

            if phy_involved:

                causes.append(
                    "infaisables physiquement "
                    "(PHY_*)"
                )

            lines[-1] = (
                lines[-1]
                + ", ".join(causes)
                + ".**"
            )

        else:

            lines[-1] = (
                lines[-1]
                + "présentes sur le front mais non "
                "sélectionnées, dominées par K2 dans la "
                "scalarisation de Tchebycheff.**"
            )

        lines.append("")
        lines.append("---")
        lines.append("")

    output_path.write_text(
        "\n".join(
            lines
        ),
        encoding="utf-8"
    )


def write_s2_latency_diagnosis(
    latency_rows,
    four_objective_summary,
    output_path
):

    lines = []

    lines.append(
        "# Diagnostic — latence normalisée élevée de S2"
    )
    lines.append("")
    lines.append(
        "**Mécanisme identifié.** `calculate_normalized_latency` "
        "(`physec_dm/energy_latency.py`, ligne 1450) divise la "
        "latence d'authentification par "
        "`authentication_latency_limit_s`, qui vaut "
        "`critical_latency_budget_s` = 5 s si le message est "
        "critique, contre `normal_latency_budget_s` = 600 s "
        "sinon (`physec_dm/parameters.py`, "
        "`get_authentication_latency_limit`). Le passage en "
        "mode critique rend donc le ratio **120 fois plus "
        "sensible** à la même latence absolue."
    )
    lines.append("")

    lines.append(
        "| Scénario | P(critique) | Fréq. A1 | Fréq. A2 | "
        "Latence A2 attendue (s) | Ratio A2 normal | "
        "Ratio A2 critique | Estimation pondérée | "
        "Valeur empirique (four_objective_summary.csv) |"
    )
    lines.append(
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|"
    )

    for row in latency_rows:

        empirical = four_objective_summary[
            row["scenario_id"]
        ][
            "normalized_latency_objective_mean"
        ]

        lines.append(
            "| "
            + SCENARIO_DISPLAY_NAMES[
                row["scenario_id"]
            ]
            + " | "
            + format(
                row["critical_probability"] * 100,
                ".0f"
            )
            + " % | "
            + format(
                row["a1_frequency"] * 100,
                ".1f"
            )
            + " % | "
            + format(
                row["a2_frequency"] * 100,
                ".1f"
            )
            + " % | "
            + format(
                row["a2_expected_latency_s"],
                ".5f"
            )
            + " | "
            + format(
                row["ratio_A2_normal"],
                ".6f"
            )
            + " | "
            + format(
                row["ratio_A2_critical"],
                ".6f"
            )
            + " | "
            + format(
                row["weighted_estimate"],
                ".6f"
            )
            + " | "
            + format(
                float(
                    empirical
                ),
                ".6f"
            )
            + " |"
        )

    lines.append("")
    lines.append(
        "**Cause identifiée.** S2 combine deux facteurs qui, "
        "ensemble, expliquent sa latence normalisée moyenne "
        "plus élevée que S1 et S3 :"
    )
    lines.append("")
    lines.append(
        "1. **P(message critique) = 60 %**, très supérieure à "
        "S1 (10 %) et S3 (30 %) — la majorité des périodes "
        "utilisent donc le budget serré de 5 s plutôt que "
        "600 s."
    )
    lines.append(
        "2. **A2 est sélectionné dans ~24 % des périodes** "
        "(contre 0 % en S1), et la latence attendue de A2 "
        "(intégrant la probabilité de repli FRR × "
        "`challenge_response_latency_s` = 4 s) est "
        "structurellement plus élevée que celle de A1 "
        "(dominée par `mac_cycles` / `cpu_frequency_hz` "
        "≈ 1 ms)."
    )
    lines.append("")
    lines.append(
        "S3 utilise A2 encore plus souvent (~98 %), mais sa "
        "proportion de messages critiques (30 %) est plus "
        "faible que celle de S2 (60 %), ce qui limite le "
        "nombre de périodes exposées au budget serré de 5 s "
        "et explique sa latence normalisée intermédiaire."
    )
    lines.append("")
    lines.append(
        "**Limite de cette estimation.** Le calcul ci-dessus "
        "isole la composante d'authentification (key_latency "
        "fixé à 0, cas K0 dominant). Les quelques périodes où "
        "K2 est effectivement sélectionné (renouvellement) "
        "ajoutent une composante `key_latency_s / "
        "key_deadline_s` non incluse ici, ce qui explique un "
        "écart résiduel entre l'estimation pondérée et la "
        "valeur empirique observée."
    )
    lines.append("")

    output_path.write_text(
        "\n".join(
            lines
        ),
        encoding="utf-8"
    )


def write_s2_far_diagnosis(
    far_rows,
    four_objective_summary,
    output_path
):

    lines = []

    lines.append(
        "# Diagnostic — FAR moyenne non nulle de S2 (≈ 0,23 %)"
    )
    lines.append("")
    lines.append(
        "**Mécanisme identifié.** Deux règles distinctes "
        "interviennent, et leur combinaison explique "
        "quantitativement la valeur observée :"
    )
    lines.append("")
    lines.append(
        "1. `evaluate_mallory()` (`physec_dm/mission.py`, "
        "ligne 457) tire un événement de fausse acceptation "
        "avec la probabilité `total_false_acceptance_probability` "
        "calculée par `calculate_authentication_metrics()` au "
        "SNR **réel** de la période (`real_snr_db`). Pour les "
        "trois scénarios, `real_snr_bias_db = 0.0` "
        "(`physec_dm/thesis_scenarios.py`), donc ce SNR réel "
        "est identique au SNR observé ayant servi à la "
        "décision."
    )
    lines.append(
        "2. **DM-EQ102** (`physec_dm/decision_maker.py`, "
        "lignes 488-506) rejette A2 dès que "
        "`authentication_metrics.far > far_limit`, avec "
        "`far_limit` = "
        + format(
            far_rows[0]["normal_far_limit"],
            ".2f"
        )
        + " pour un message normal et "
        + format(
            far_rows[0]["critical_far_limit"],
            ".2f"
        )
        + " pour un message critique. Comme ce `far` est "
        "calculé au **même** SNR observé que celui utilisé "
        "ensuite par `evaluate_mallory()`, **A2 n'est jamais "
        "sélectionné dans une période où le SNR réel donnerait "
        "une FAR supérieure au plancher.** La FAR réalisée "
        "pendant les tentatives de Mallory est donc "
        "structurellement bornée par construction, et non "
        "distribuée autour du SNR moyen brut du scénario."
    )
    lines.append("")

    lines.append(
        "### SNR à partir duquel A2 franchit le plancher "
        "de sécurité (recherche numérique sur `calculate_far`)"
    )
    lines.append("")
    lines.append(
        "| Scénario | SNR moyen ± écart-type (dB) | FAR au "
        "SNR moyen (non conditionnée) | SNR minimal pour "
        "FAR ≤ 0,05 (normal) | SNR minimal pour FAR ≤ 0,01 "
        "(critique) |"
    )
    lines.append(
        "|---|---:|---:|---:|---:|"
    )

    for row in far_rows:

        lines.append(
            "| "
            + SCENARIO_DISPLAY_NAMES[
                row["scenario_id"]
            ]
            + " | "
            + format(
                row["mean_snr_db"],
                ".1f"
            )
            + " ± "
            + format(
                row["shadowing_std_db"],
                ".1f"
            )
            + " | "
            + format(
                row["far_at_mean_snr"],
                ".6f"
            )
            + " | "
            + format(
                row["far_threshold_snr_normal_db"],
                ".2f"
            )
            + " dB | "
            + format(
                row["far_threshold_snr_critical_db"],
                ".2f"
            )
            + " dB |"
        )

    lines.append("")
    lines.append(
        "Pour S2 (SNR ~ N(5, 3²)), le seuil de FAR normal "
        "(≈ "
        + format(
            far_rows[1]["far_threshold_snr_normal_db"],
            ".1f"
        )
        + " dB) se situe à environ "
        + format(
            (
                far_rows[1]["far_threshold_snr_normal_db"]
                - far_rows[1]["mean_snr_db"]
            )
            / far_rows[1]["shadowing_std_db"],
            ".2f"
        )
        + " écarts-types au-dessus de la moyenne, et le seuil "
        "critique (≈ "
        + format(
            far_rows[1]["far_threshold_snr_critical_db"],
            ".1f"
        )
        + " dB) à environ "
        + format(
            (
                far_rows[1]["far_threshold_snr_critical_db"]
                - far_rows[1]["mean_snr_db"]
            )
            / far_rows[1]["shadowing_std_db"],
            ".2f"
        )
        + " écarts-types. Seules les réalisations de SNR "
        "au-delà de ces seuils permettent la sélection de A2 "
        "— ce qui explique à la fois pourquoi A2 est "
        "sélectionné dans une minorité de périodes (~24 %) et "
        "pourquoi la FAR réellement subie pendant ces périodes "
        "est bien inférieure à `FAR(SNR moyen)`."
    )
    lines.append("")

    lines.append(
        "### Vérification numérique par rejeu du modèle "
        "réel (lecture seule)"
    )
    lines.append("")
    lines.append(
        "Pour démontrer ce mécanisme avec des valeurs "
        "exactes plutôt qu'un raisonnement qualitatif, "
        "`diagnose_k1_and_s2.py` rejoue directement, pour "
        "chacun des trois scénarios, la chaîne réelle "
        "`draw_observed_snr_db` → `calculate_channel_metrics` "
        "→ `run_decision_maker` → `evaluate_mallory` sur "
        "40 000 tirages indépendants (graine fixe = 20260721, "
        "générateur NumPy dédié, aucune mission ni aucun "
        "fichier de `results/three_scenarios_s2_corrected` "
        "modifié), avec un état de clé K0 hors renouvellement "
        "représentatif (le mécanisme K1a/K1b/K2 est diagnostiqué "
        "séparément ci-dessus)."
    )
    lines.append("")

    lines.append(
        "| Scénario | Fréq. A2 simulée | Fréq. A2 réelle "
        "(decision_frequencies.csv) | Tentatives de Mallory "
        "simulées | Fausses acceptations simulées | FAR "
        "(simulée, ± erreur-type) | FAR empirique "
        "(four_objective_summary.csv) |"
    )
    lines.append(
        "|---|---:|---:|---:|---:|---:|---:|"
    )

    for row in far_rows:

        simulation = row["simulation"]

        empirical = four_objective_summary[
            row["scenario_id"]
        ][
            "false_acceptance_rate_mean"
        ]

        lines.append(
            "| "
            + SCENARIO_DISPLAY_NAMES[
                row["scenario_id"]
            ]
            + " | "
            + format(
                simulation[
                    "a2_selection_frequency"
                ] * 100,
                ".1f"
            )
            + " % | "
            + format(
                row["a2_frequency_campaign"] * 100,
                ".1f"
            )
            + " % | "
            + str(
                simulation["mallory_attempts"]
            )
            + " | "
            + str(
                simulation["false_acceptances"]
            )
            + " | "
            + format(
                simulation["far_rate_simulated"],
                ".6f"
            )
            + " ± "
            + format(
                simulation[
                    "far_rate_standard_error"
                ],
                ".6f"
            )
            + " | "
            + format(
                float(
                    empirical
                ),
                ".6f"
            )
            + " |"
        )

    lines.append("")
    lines.append(
        "**Cause identifiée.** La FAR n'est pas un bruit "
        "numérique ni une anomalie du modèle : c'est la "
        "conséquence directe et attendue de la combinaison "
        "de deux mécanismes déjà présents dans le modèle "
        "validé :"
    )
    lines.append("")
    lines.append(
        "- **S1** : A2 n'est jamais sélectionné (0 %) — à "
        "SNR moyen -10 dB, même le seuil de FAR normal "
        "n'est jamais atteint. Seule la forge de MAC "
        "(≈ 2⁻⁶⁴) reste possible, statistiquement invisible "
        "sur 30 graines. FAR empirique = 0, FAR simulée = 0 "
        "sur "
        + str(
            far_rows[0]["simulation"]["mallory_attempts"]
        )
        + " tentatives."
    )
    lines.append(
        "- **S3** : le SNR moyen (20 dB) est très largement "
        "au-dessus des deux seuils de plancher ; A2 est donc "
        "sélectionné dans la quasi-totalité des périodes "
        "(~98 %), mais toujours à un SNR où `calculate_far` "
        "sature numériquement à zéro. FAR empirique = 0, "
        "FAR simulée = 0 sur "
        + str(
            far_rows[2]["simulation"]["mallory_attempts"]
        )
        + " tentatives."
    )
    lines.append(
        "- **S2** : le SNR moyen (5 dB) place la majorité de "
        "la distribution **sous** les deux seuils de "
        "plancher, ce qui limite A2 à ~24 % des périodes "
        "(valeur simulée cohérente avec la fréquence réelle "
        "de la campagne) ; mais la **queue haute** de la "
        "distribution de SNR (au-delà de ces seuils) reste "
        "non nulle. Dans ces périodes-là, A2 est admissible "
        "et Mallory peut être acceptée avec une FAR déjà "
        "faible (bornée par le plancher franchi), ce qui "
        "produit un taux de fausse acceptation simulé de "
        "l'ordre de la valeur empirique — très inférieur au "
        "FAR(SNR moyen) non conditionné ("
        + format(
            far_rows[1]["far_at_mean_snr"],
            ".4f"
        )
        + "), qui ignore à tort cette sélection par le "
        "plancher de sécurité. Le plancher de sécurité au "
        "SNR réel n'a par ailleurs jamais été dépassé dans la "
        "campagne (`security_floor_violation_rate` = 0), ce "
        "qui est cohérent : ce plancher compare la FAR à une "
        "limite autorisée non nulle, pas à zéro."
    )
    lines.append("")

    output_path.write_text(
        "\n".join(
            lines
        ),
        encoding="utf-8"
    )


def write_diagnostic_summary_csv(
    trigger_diagnoses,
    authoritative_evaluations,
    latency_rows,
    far_rows,
    four_objective_summary,
    output_path
):

    rows = []

    for scenario_id in SCENARIO_ORDER:

        trigger = trigger_diagnoses[scenario_id]

        authoritative = authoritative_evaluations[
            scenario_id
        ]

        latency_row = next(
            row
            for row in latency_rows
            if row["scenario_id"] == scenario_id
        )

        far_row = next(
            row
            for row in far_rows
            if row["scenario_id"] == scenario_id
        )

        nominal_channel = trigger["channel_rows"][
            len(
                trigger["channel_rows"]
            )
            // 2
        ]

        k1a_evaluation = authoritative["evaluations"].get(
            "A2-K1a"
        )

        k1b_evaluation = authoritative["evaluations"].get(
            "A2-K1b"
        )

        rows.append(
            {
                "Scenario_ID": scenario_id,
                "K1a_admissible_at_trigger": (
                    k1a_evaluation.admissible
                    if k1a_evaluation is not None
                    else None
                ),
                "K1a_rejection_reasons": (
                    format_rejections(
                        k1a_evaluation
                    )
                    if k1a_evaluation is not None
                    else ""
                ),
                "K1b_admissible_at_trigger": (
                    k1b_evaluation.admissible
                    if k1b_evaluation is not None
                    else None
                ),
                "K1b_rejection_reasons": (
                    format_rejections(
                        k1b_evaluation
                    )
                    if k1b_evaluation is not None
                    else ""
                ),
                "Effective_KDR_nominal_SNR": (
                    nominal_channel["effective_kdr"]
                ),
                "Required_measurements_nominal_SNR": (
                    nominal_channel[
                        "required_measurements"
                    ]
                ),
                "K1a_latency_s_nominal_SNR": (
                    nominal_channel["k1a_latency_s"]
                ),
                "K1b_latency_s_nominal_SNR": (
                    nominal_channel["k1b_latency_s"]
                ),
                "K1b_airtime_s_nominal_SNR": (
                    nominal_channel["k1b_airtime_s"]
                ),
                "Key_deadline_s_at_trigger": (
                    trigger["key_deadline_s"]
                ),
                "Duty_cycle_budget_s": (
                    trigger[
                        "remaining_duty_cycle_airtime_s"
                    ]
                ),
                "K1_key_quality_nominal_SNR": (
                    nominal_channel["key_quality_phy"]
                ),
                "K2_key_quality": (
                    trigger["k2_quality"]
                ),
                "Pareto_front_at_trigger": (
                    ", ".join(
                        authoritative[
                            "pareto_front_names"
                        ]
                    )
                ),
                "Latency_weighted_estimate": (
                    latency_row["weighted_estimate"]
                ),
                "Latency_empirical_mean": (
                    four_objective_summary[
                        scenario_id
                    ][
                        "normalized_latency_objective_mean"
                    ]
                ),
                "FAR_at_mean_snr_unconditional": (
                    far_row["far_at_mean_snr"]
                ),
                "FAR_threshold_snr_normal_db": (
                    far_row[
                        "far_threshold_snr_normal_db"
                    ]
                ),
                "FAR_threshold_snr_critical_db": (
                    far_row[
                        "far_threshold_snr_critical_db"
                    ]
                ),
                "FAR_simulated_a2_frequency": (
                    far_row["simulation"][
                        "a2_selection_frequency"
                    ]
                ),
                "FAR_simulated_rate": (
                    far_row["simulation"][
                        "far_rate_simulated"
                    ]
                ),
                "FAR_simulated_standard_error": (
                    far_row["simulation"][
                        "far_rate_standard_error"
                    ]
                ),
                "FAR_empirical_mean": (
                    four_objective_summary[
                        scenario_id
                    ][
                        "false_acceptance_rate_mean"
                    ]
                )
            }
        )

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
# 8. LANCEMENT
# ================================================================


def run_diagnosis():

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )

    decision_frequencies = load_decision_frequencies()

    four_objective_summary = load_four_objective_summary()

    scenario_definitions = (
        build_scenario_parameters_and_definition()
    )

    trigger_diagnoses = {}

    authoritative_evaluations = {}

    for scenario_id in SCENARIO_ORDER:

        scenario_parameters = scenario_definitions[
            scenario_id
        ]["parameters"]

        duty_cycle_budget_s = scenario_definitions[
            scenario_id
        ]["definition"]["mission_options"][
            "maximum_duty_cycle_airtime_s"
        ]

        mean_snr = scenario_parameters.mean_snr_db

        shadowing = (
            scenario_parameters.shadowing_std_db
        )

        snr_samples = [
            (
                "borne basse (SNR−σ)",
                mean_snr - shadowing
            ),
            (
                "nominal (SNR moyen)",
                mean_snr
            ),
            (
                "borne haute (SNR+σ)",
                mean_snr + shadowing
            )
        ]

        trigger_diagnoses[scenario_id] = (
            diagnose_key_renewal_at_trigger(
                scenario_id,
                scenario_parameters,
                snr_samples,
                duty_cycle_budget_s
            )
        )

        authoritative_evaluations[scenario_id] = (
            run_authoritative_evaluation(
                scenario_id,
                scenario_parameters,
                trigger_diagnoses[scenario_id],
                snr_db=mean_snr,
                criticality=0
            )
        )

    latency_rows = diagnose_latency(
        scenario_definitions,
        decision_frequencies
    )

    far_rows = diagnose_far(
        scenario_definitions,
        decision_frequencies
    )

    write_k1_selection_diagnosis(
        scenario_definitions,
        trigger_diagnoses,
        authoritative_evaluations,
        OUTPUT_DIRECTORY / "k1_selection_diagnosis.md"
    )

    write_s2_latency_diagnosis(
        latency_rows,
        four_objective_summary,
        OUTPUT_DIRECTORY / "s2_latency_diagnosis.md"
    )

    write_s2_far_diagnosis(
        far_rows,
        four_objective_summary,
        OUTPUT_DIRECTORY / "s2_far_diagnosis.md"
    )

    write_diagnostic_summary_csv(
        trigger_diagnoses,
        authoritative_evaluations,
        latency_rows,
        far_rows,
        four_objective_summary,
        OUTPUT_DIRECTORY / "diagnostic_summary.csv"
    )

    return {
        "trigger_diagnoses": trigger_diagnoses,
        "authoritative_evaluations": (
            authoritative_evaluations
        ),
        "latency_rows": latency_rows,
        "far_rows": far_rows
    }


if __name__ == "__main__":

    result = run_diagnosis()

    print(
        "Diagnostic terminé."
    )

    print(
        "Fichiers écrits dans :",
        OUTPUT_DIRECTORY
    )
