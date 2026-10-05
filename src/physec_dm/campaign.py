# On importe copy pour créer une copie indépendante
# des paramètres avant chaque scénario et chaque politique.
#
# Cela évite qu'une simulation modifie silencieusement
# les paramètres d'une autre simulation.
import copy


# csv permet d'exporter les résultats
# dans des fichiers lisibles par Excel, LibreOffice
# ou un programme Python.
import csv


# math est utilisé pour :
# - la racine carrée ;
# - le calcul des intervalles de confiance.
import math


# Path facilite la création des dossiers
# et la manipulation des chemins de fichiers.
from pathlib import Path


# statistics fournit une moyenne et un écart-type
# simples, sans ajouter une nouvelle dépendance.
import statistics


# NumPy est utilisé uniquement pour produire
# les traces aléatoires communes aux politiques.
import numpy as np


# CampaignResult regroupe toutes les missions
# d'une campagne.
from physec_dm.models import (
    CampaignResult
)


# run_mission exécute une mission complète
# pour un scénario, une politique et une graine.
from physec_dm.mission import (
    run_mission
)


# ================================================================
# 1. VALIDATION DES ENTRÉES
# ================================================================


# Cette fonction vérifie qu'une liste existe
# et qu'elle contient au moins un élément.
def validate_non_empty_sequence(
    values,
    sequence_name
):

    if values is None or len(values) == 0:

        raise ValueError(
            sequence_name
            + " doit contenir au moins un élément."
        )

    return values


# Cette fonction lit un identifiant obligatoire
# dans un dictionnaire.
def get_required_identifier(
    configuration,
    identifier_name
):

    if not isinstance(
        configuration,
        dict
    ):

        raise ValueError(
            "Chaque configuration doit être un dictionnaire."
        )

    if identifier_name not in configuration:

        raise ValueError(
            identifier_name
            + " est obligatoire."
        )

    identifier = configuration[
        identifier_name
    ]

    if (
        not isinstance(identifier, str)
        or identifier.strip() == ""
    ):

        raise ValueError(
            identifier_name
            + " doit être un texte non vide."
        )

    return identifier


# Cette fonction vérifie une probabilité.
def validate_probability(
    probability,
    probability_name
):

    if probability < 0 or probability > 1:

        raise ValueError(
            probability_name
            + " doit appartenir à [0, 1]."
        )

    return float(
        probability
    )


# ================================================================
# 2. COPIE ET MODIFICATION DES PARAMÈTRES
# ================================================================


# Cette fonction crée une copie indépendante
# de l'objet Parameters.
def clone_parameters(
    parameters
):

    return copy.deepcopy(
        parameters
    )


# Cette fonction applique une liste de modifications
# à un objet Parameters.
#
# Les modifications sont données sous la forme :
#
# {
#     "mean_snr_db": 5.0,
#     "shadowing_std_db": 3.0
# }
#
# Une faute dans le nom d'un paramètre est refusée.
# Le programme ne crée donc pas silencieusement
# un nouveau paramètre inconnu.
def apply_parameter_overrides(
    parameters,
    overrides,
    configuration_name
):

    if overrides is None:

        return parameters

    if not isinstance(
        overrides,
        dict
    ):

        raise ValueError(
            configuration_name
            + " doit être un dictionnaire."
        )

    for parameter_name in overrides:

        if not hasattr(
            parameters,
            parameter_name
        ):

            raise ValueError(
                "Le paramètre "
                + parameter_name
                + " n'existe pas dans Parameters."
            )

        setattr(
            parameters,
            parameter_name,
            overrides[parameter_name]
        )

    return parameters


# Cette fonction construit les paramètres
# d'un scénario.
def build_scenario_parameters(
    base_parameters,
    scenario
):

    scenario_id = get_required_identifier(
        scenario,
        "scenario_id"
    )

    scenario_parameters = clone_parameters(
        base_parameters
    )

    apply_parameter_overrides(
        parameters=scenario_parameters,
        overrides=scenario.get(
            "parameter_overrides"
        ),
        configuration_name=(
            "parameter_overrides du scénario "
            + scenario_id
        )
    )

    # L'identifiant est ajouté aux paramètres.
    #
    # La méthode to_dictionary de Parameters
    # le conservera ensuite dans parameters_snapshot.
    scenario_parameters.scenario_id = (
        scenario_id
    )

    return scenario_parameters


# Cette fonction applique une politique
# à la copie des paramètres du scénario.
def build_policy_parameters(
    scenario_parameters,
    policy
):

    policy_id = get_required_identifier(
        policy,
        "policy_id"
    )

    policy_parameters = clone_parameters(
        scenario_parameters
    )

    apply_parameter_overrides(
        parameters=policy_parameters,
        overrides=policy.get(
            "parameter_overrides"
        ),
        configuration_name=(
            "parameter_overrides de la politique "
            + policy_id
        )
    )

    # Les poids peuvent être donnés directement
    # dans la politique pour faciliter la lecture.
    if "contextual_weights" in policy:

        policy_parameters.contextual_weights = (
            list(
                policy[
                    "contextual_weights"
                ]
            )
        )

    # Le mode de secours peut également
    # être propre à une politique.
    if "fallback_mode" in policy:

        policy_parameters.fallback_mode = (
            policy[
                "fallback_mode"
            ]
        )

    policy_parameters.policy_id = (
        policy_id
    )

    return policy_parameters


# ================================================================
# 3. TRACES ALÉATOIRES COMMUNES
# ================================================================


# Cette fonction crée une trace commune
# pour toutes les politiques comparées
# dans un même scénario et avec une même graine.
#
# Cette technique est appelée :
#
# Common Random Numbers.
#
# Elle permet de comparer les politiques
# avec exactement :
# - les mêmes SNR ;
# - les mêmes criticités ;
# - les mêmes tentatives de Mallory ;
# - les mêmes suspicions de compromission.
def create_common_random_traces(
    parameters,
    seed,
    max_steps,
    real_snr_bias_db=0.0,
    compromise_probability=0.0
):

    if max_steps <= 0:

        raise ValueError(
            "max_steps doit être strictement positif."
        )

    if parameters.mean_snr_db is None:

        raise ValueError(
            "mean_snr_db doit être défini."
        )

    if parameters.shadowing_std_db is None:

        raise ValueError(
            "shadowing_std_db doit être défini."
        )

    if parameters.shadowing_std_db < 0:

        raise ValueError(
            "shadowing_std_db ne peut pas être négatif."
        )

    critical_probability = (
        validate_probability(
            parameters.critical_message_probability,
            "critical_message_probability"
        )
    )

    mallory_probability = (
        validate_probability(
            parameters.mallory_attempt_probability,
            "mallory_attempt_probability"
        )
    )

    compromise_probability = (
        validate_probability(
            compromise_probability,
            "compromise_probability"
        )
    )

    random_generator = np.random.default_rng(
        seed
    )

    observed_snr_array = (
        random_generator.normal(
            loc=parameters.mean_snr_db,
            scale=parameters.shadowing_std_db,
            size=max_steps
        )
    )

    # Le biais permet plus tard d'étudier
    # une différence entre le SNR observé
    # et le SNR réel.
    real_snr_array = (
        observed_snr_array
        + real_snr_bias_db
    )

    criticality_array = (
        random_generator.random(
            max_steps
        )
        < critical_probability
    )

    mallory_array = (
        random_generator.random(
            max_steps
        )
        < mallory_probability
    )

    compromise_array = (
        random_generator.random(
            max_steps
        )
        < compromise_probability
    )

    # Les tableaux NumPy sont convertis
    # en listes Python simples.
    return {
        "observed_snr_trace": [
            float(value)
            for value in observed_snr_array
        ],
        "real_snr_trace": [
            float(value)
            for value in real_snr_array
        ],
        "criticality_trace": [
            1 if value else 0
            for value in criticality_array
        ],
        "mallory_trace": [
            bool(value)
            for value in mallory_array
        ],
        "compromise_trace": [
            bool(value)
            for value in compromise_array
        ]
    }


# ================================================================
# 4. EXÉCUTION D'UNE CAMPAGNE
# ================================================================


# Cette fonction lit une option de mission
# dans le dictionnaire d'un scénario.
def get_mission_option(
    scenario,
    option_name,
    default_value
):

    mission_options = scenario.get(
        "mission_options",
        {}
    )

    if not isinstance(
        mission_options,
        dict
    ):

        raise ValueError(
            "mission_options doit être un dictionnaire."
        )

    return mission_options.get(
        option_name,
        default_value
    )


# Cette fonction exécute toutes les missions
# d'une campagne.
#
# L'ordre des boucles est important :
#
# scénario
#     graine
#         création d'une trace commune
#         politique 1
#         politique 2
#         ...
#
# Ainsi, toutes les politiques d'une même paire
# scénario-graine utilisent exactement la même trace.
def run_campaign(
    base_parameters,
    campaign_id,
    scenarios,
    policies,
    seeds,
    output_directory,
    max_steps=1000,
    max_duration_s=None,
    variation_feasible=None,
    k2_protocol=None,
    compromise_probability=0.0,
    export_results=True
):

    if (
        not isinstance(campaign_id, str)
        or campaign_id.strip() == ""
    ):

        raise ValueError(
            "campaign_id doit être un texte non vide."
        )

    validate_non_empty_sequence(
        scenarios,
        "scenarios"
    )

    validate_non_empty_sequence(
        policies,
        "policies"
    )

    validate_non_empty_sequence(
        seeds,
        "seeds"
    )

    if max_steps <= 0:

        raise ValueError(
            "max_steps doit être strictement positif."
        )

    output_directory = Path(
        output_directory
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    scenario_ids = []
    policy_ids = []

    for scenario in scenarios:

        scenario_ids.append(
            get_required_identifier(
                scenario,
                "scenario_id"
            )
        )

    for policy in policies:

        policy_ids.append(
            get_required_identifier(
                policy,
                "policy_id"
            )
        )

    mission_results = []

    for scenario in scenarios:

        scenario_id = get_required_identifier(
            scenario,
            "scenario_id"
        )

        scenario_parameters = (
            build_scenario_parameters(
                base_parameters,
                scenario
            )
        )

        scenario_max_steps = get_mission_option(
            scenario,
            "max_steps",
            max_steps
        )

        scenario_max_duration_s = (
            get_mission_option(
                scenario,
                "max_duration_s",
                max_duration_s
            )
        )

        initial_duty_cycle_airtime_s = (
            get_mission_option(
                scenario,
                "initial_duty_cycle_airtime_s",
                None
            )
        )

        maximum_duty_cycle_airtime_s = (
            get_mission_option(
                scenario,
                "maximum_duty_cycle_airtime_s",
                None
            )
        )

        duty_cycle_recharge_s = (
            get_mission_option(
                scenario,
                "duty_cycle_recharge_s",
                None
            )
        )

        rff_profile_available = (
            get_mission_option(
                scenario,
                "rff_profile_available",
                True
            )
        )

        real_snr_bias_db = scenario.get(
            "real_snr_bias_db",
            0.0
        )

        scenario_variation_feasible = (
            scenario.get(
                "variation_feasible",
                variation_feasible
            )
        )

        scenario_k2_protocol = scenario.get(
            "k2_protocol",
            k2_protocol
        )

        scenario_compromise_probability = (
            scenario.get(
                "compromise_probability",
                compromise_probability
            )
        )

        for seed in seeds:

            # Une seule trace est créée ici,
            # avant la boucle des politiques.
            common_traces = (
                create_common_random_traces(
                    parameters=scenario_parameters,
                    seed=seed,
                    max_steps=scenario_max_steps,
                    real_snr_bias_db=(
                        real_snr_bias_db
                    ),
                    compromise_probability=(
                        scenario_compromise_probability
                    )
                )
            )

            for policy in policies:

                policy_id = (
                    get_required_identifier(
                        policy,
                        "policy_id"
                    )
                )

                policy_parameters = (
                    build_policy_parameters(
                        scenario_parameters,
                        policy
                    )
                )

                mission_result = run_mission(
                    parameters=policy_parameters,
                    seed=seed,
                    policy_id=policy_id,
                    max_steps=scenario_max_steps,
                    max_duration_s=(
                        scenario_max_duration_s
                    ),
                    initial_duty_cycle_airtime_s=(
                        initial_duty_cycle_airtime_s
                    ),
                    maximum_duty_cycle_airtime_s=(
                        maximum_duty_cycle_airtime_s
                    ),
                    duty_cycle_recharge_s=(
                        duty_cycle_recharge_s
                    ),
                    rff_profile_available=(
                        rff_profile_available
                    ),
                    variation_feasible=(
                        scenario_variation_feasible
                    ),
                    k2_protocol=(
                        scenario_k2_protocol
                    ),
                    observed_snr_trace=(
                        common_traces[
                            "observed_snr_trace"
                        ]
                    ),
                    real_snr_trace=(
                        common_traces[
                            "real_snr_trace"
                        ]
                    ),
                    criticality_trace=(
                        common_traces[
                            "criticality_trace"
                        ]
                    ),
                    mallory_trace=(
                        common_traces[
                            "mallory_trace"
                        ]
                    ),
                    compromise_trace=(
                        common_traces[
                            "compromise_trace"
                        ]
                    )
                )

                mission_results.append(
                    mission_result
                )

    campaign_result = CampaignResult(
        campaign_id=campaign_id,
        scenario_ids=scenario_ids,
        policy_ids=policy_ids,
        seeds=list(seeds),
        mission_results=mission_results,
        output_directory=str(
            output_directory
        )
    )

    if export_results:

        export_campaign_results(
            campaign_result,
            output_directory
        )

    return campaign_result


# ================================================================
# 5. OUTILS STATISTIQUES
# ================================================================


# Cette fonction retire les valeurs None.
#
# None signifie qu'un taux n'était pas défini,
# par exemple lorsqu'aucune attaque n'a eu lieu.
def remove_undefined_values(
    values
):

    return [
        float(value)
        for value in values
        if value is not None
    ]


# Cette fonction calcule une moyenne.
#
# Elle retourne None lorsqu'aucune valeur
# n'est disponible.
def calculate_mean(
    values
):

    defined_values = (
        remove_undefined_values(
            values
        )
    )

    if len(defined_values) == 0:

        return None

    return statistics.mean(
        defined_values
    )


# Cette fonction calcule l'écart-type
# d'un échantillon.
#
# Une seule répétition ne permet pas
# d'estimer un écart-type.
def calculate_sample_standard_deviation(
    values
):

    defined_values = (
        remove_undefined_values(
            values
        )
    )

    if len(defined_values) < 2:

        return None

    return statistics.stdev(
        defined_values
    )


# Cette fonction calcule un intervalle de confiance
# approximatif à 95 % :
#
# moyenne ± 1.96 * écart-type / sqrt(n)
#
# Cet intervalle utilise l'approximation normale.
#
# Pour une seule répétition,
# l'intervalle ne peut pas être estimé.
def calculate_95_percent_confidence_interval(
    values
):

    defined_values = (
        remove_undefined_values(
            values
        )
    )

    if len(defined_values) < 2:

        return (
            None,
            None
        )

    mean_value = statistics.mean(
        defined_values
    )

    standard_deviation = statistics.stdev(
        defined_values
    )

    margin = (
        1.96
        * standard_deviation
        / math.sqrt(
            len(defined_values)
        )
    )

    return (
        mean_value - margin,
        mean_value + margin
    )


# Cette fonction regroupe les statistiques
# d'une seule métrique.
def summarize_values(
    values,
    prefix
):

    defined_values = (
        remove_undefined_values(
            values
        )
    )

    mean_value = calculate_mean(
        defined_values
    )

    standard_deviation = (
        calculate_sample_standard_deviation(
            defined_values
        )
    )

    (
        confidence_low,
        confidence_high
    ) = calculate_95_percent_confidence_interval(
        defined_values
    )

    return {
        prefix + "_count": len(
            defined_values
        ),
        prefix + "_mean": mean_value,
        prefix + "_std": standard_deviation,
        prefix + "_ci95_low": confidence_low,
        prefix + "_ci95_high": confidence_high
    }


# ================================================================
# 6. AGRÉGATION DES RÉSULTATS
# ================================================================


# Cette fonction retrouve l'identifiant du scénario
# dans la copie des paramètres de la mission.
def get_mission_scenario_id(
    mission_result
):

    parameters_snapshot = (
        mission_result.parameters_snapshot
    )

    if "scenario_id" not in parameters_snapshot:

        raise ValueError(
            "scenario_id manque dans parameters_snapshot."
        )

    return parameters_snapshot[
        "scenario_id"
    ]


# Cette fonction regroupe les missions
# par scénario et par politique.
def group_mission_results(
    campaign_result
):

    grouped_results = {}

    for mission_result in (
        campaign_result.mission_results
    ):

        scenario_id = get_mission_scenario_id(
            mission_result
        )

        policy_id = mission_result.policy_id

        group_key = (
            scenario_id,
            policy_id
        )

        if group_key not in grouped_results:

            grouped_results[
                group_key
            ] = []

        grouped_results[
            group_key
        ].append(
            mission_result
        )

    return grouped_results


# Cette fonction produit une ligne agrégée
# pour chaque couple scénario-politique.
#
# La durée est appelée "observed_lifetime"
# car une mission censurée n'est pas une durée de vie
# complètement observée.
#
# Le code ne prétend donc pas réaliser
# une analyse de survie de Kaplan-Meier.
def aggregate_campaign_results(
    campaign_result
):

    grouped_results = group_mission_results(
        campaign_result
    )

    aggregate_rows = []

    for group_key in sorted(
        grouped_results
    ):

        scenario_id = group_key[0]
        policy_id = group_key[1]

        mission_results = grouped_results[
            group_key
        ]

        mission_count = len(
            mission_results
        )

        censored_count = sum(
            1
            for result in mission_results
            if result.censored
        )

        aggregate_row = {
            "scenario_id": scenario_id,
            "policy_id": policy_id,
            "mission_count": mission_count,
            "censored_count": censored_count,
            "censored_fraction": (
                censored_count
                / mission_count
            )
        }

        metric_definitions = [
            (
                "observed_lifetime_s",
                [
                    result.lifetime_s
                    for result in mission_results
                ]
            ),
            (
                "energy_per_generated_message_j",
                [
                    result.mean_energy_per_generated_message_j
                    for result in mission_results
                ]
            ),
            (
                "energy_per_served_message_j",
                [
                    result.mean_energy_per_served_message_j
                    for result in mission_results
                ]
            ),
            (
                "false_acceptance_rate",
                [
                    result.false_acceptance_rate
                    for result in mission_results
                ]
            ),
            (
                "critical_false_acceptance_rate",
                [
                    result.critical_false_acceptance_rate
                    for result in mission_results
                ]
            ),
            (
                "legitimate_refusal_rate",
                [
                    result.legitimate_refusal_rate
                    for result in mission_results
                ]
            ),
            (
                "security_floor_violation_rate",
                [
                    result.security_floor_violation_rate
                    for result in mission_results
                ]
            ),
            (
                "final_battery_energy_j",
                [
                    result.final_state.battery_energy_j
                    for result in mission_results
                ]
            )
        ]

        for metric_name, values in metric_definitions:

            aggregate_row.update(
                summarize_values(
                    values,
                    metric_name
                )
            )

        aggregate_rows.append(
            aggregate_row
        )

    return aggregate_rows


# Cette fonction calcule la fréquence de sélection
# de chaque décision.
def calculate_decision_frequencies(
    campaign_result
):

    grouped_results = group_mission_results(
        campaign_result
    )

    frequency_rows = []

    for group_key in sorted(
        grouped_results
    ):

        scenario_id = group_key[0]
        policy_id = group_key[1]

        decision_totals = {}

        for mission_result in grouped_results[
            group_key
        ]:

            for decision_name in (
                mission_result.decision_counts
            ):

                decision_totals[
                    decision_name
                ] = (
                    decision_totals.get(
                        decision_name,
                        0
                    )
                    + mission_result.decision_counts[
                        decision_name
                    ]
                )

        total_selections = sum(
            decision_totals.values()
        )

        for decision_name in sorted(
            decision_totals
        ):

            decision_count = (
                decision_totals[
                    decision_name
                ]
            )

            if total_selections == 0:

                frequency = None

            else:

                frequency = (
                    decision_count
                    / total_selections
                )

            frequency_rows.append(
                {
                    "scenario_id": scenario_id,
                    "policy_id": policy_id,
                    "decision_name": decision_name,
                    "decision_count": decision_count,
                    "total_selections": (
                        total_selections
                    ),
                    "selection_frequency": (
                        frequency
                    )
                }
            )

    return frequency_rows


# Cette fonction transforme les résultats agrégés
# en format long, pratique pour les graphiques.
def prepare_plot_data(
    campaign_result
):

    aggregate_rows = aggregate_campaign_results(
        campaign_result
    )

    plot_rows = []

    metric_names = [
        "observed_lifetime_s",
        "energy_per_generated_message_j",
        "energy_per_served_message_j",
        "false_acceptance_rate",
        "critical_false_acceptance_rate",
        "legitimate_refusal_rate",
        "security_floor_violation_rate",
        "final_battery_energy_j"
    ]

    for aggregate_row in aggregate_rows:

        for metric_name in metric_names:

            plot_rows.append(
                {
                    "scenario_id": (
                        aggregate_row[
                            "scenario_id"
                        ]
                    ),
                    "policy_id": (
                        aggregate_row[
                            "policy_id"
                        ]
                    ),
                    "metric_name": metric_name,
                    "count": aggregate_row[
                        metric_name
                        + "_count"
                    ],
                    "mean": aggregate_row[
                        metric_name
                        + "_mean"
                    ],
                    "std": aggregate_row[
                        metric_name
                        + "_std"
                    ],
                    "ci95_low": aggregate_row[
                        metric_name
                        + "_ci95_low"
                    ],
                    "ci95_high": aggregate_row[
                        metric_name
                        + "_ci95_high"
                    ]
                }
            )

    return plot_rows


# ================================================================
# 7. EXPORT CSV
# ================================================================


# Cette fonction écrit une liste de dictionnaires
# dans un fichier CSV.
def write_csv_rows(
    file_path,
    rows
):

    file_path = Path(
        file_path
    )

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if len(rows) == 0:

        # Un fichier vide est tout de même créé
        # pour rendre l'export explicite.
        file_path.write_text(
            "",
            encoding="utf-8"
        )

        return file_path

    field_names = list(
        rows[0].keys()
    )

    with file_path.open(
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

    return file_path


# Cette fonction crée une ligne
# pour chaque mission.
def build_mission_summary_rows(
    campaign_result
):

    rows = []

    for mission_result in (
        campaign_result.mission_results
    ):

        rows.append(
            {
                "campaign_id": (
                    campaign_result.campaign_id
                ),
                "scenario_id": (
                    get_mission_scenario_id(
                        mission_result
                    )
                ),
                "policy_id": (
                    mission_result.policy_id
                ),
                "seed": mission_result.seed,
                "lifetime_s": (
                    mission_result.lifetime_s
                ),
                "mean_energy_per_generated_message_j": (
                    mission_result
                    .mean_energy_per_generated_message_j
                ),
                "mean_energy_per_served_message_j": (
                    mission_result
                    .mean_energy_per_served_message_j
                ),
                "false_acceptance_rate": (
                    mission_result
                    .false_acceptance_rate
                ),
                "critical_false_acceptance_rate": (
                    mission_result
                    .critical_false_acceptance_rate
                ),
                "legitimate_refusal_rate": (
                    mission_result
                    .legitimate_refusal_rate
                ),
                "security_floor_violation_rate": (
                    mission_result
                    .security_floor_violation_rate
                ),
                "final_battery_energy_j": (
                    mission_result
                    .final_state
                    .battery_energy_j
                ),
                "stop_reason": (
                    mission_result.stop_reason
                ),
                "censored": (
                    mission_result.censored
                )
            }
        )

    return rows


# Cette fonction exporte les principaux résultats.
def export_campaign_results(
    campaign_result,
    output_directory=None
):

    if output_directory is None:

        output_directory = (
            campaign_result.output_directory
        )

    output_directory = Path(
        output_directory
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    mission_summary_path = write_csv_rows(
        output_directory
        / "mission_summary.csv",
        build_mission_summary_rows(
            campaign_result
        )
    )

    aggregate_summary_path = write_csv_rows(
        output_directory
        / "aggregate_summary.csv",
        aggregate_campaign_results(
            campaign_result
        )
    )

    decision_frequencies_path = (
        write_csv_rows(
            output_directory
            / "decision_frequencies.csv",
            calculate_decision_frequencies(
                campaign_result
            )
        )
    )

    plot_data_path = write_csv_rows(
        output_directory
        / "plot_data.csv",
        prepare_plot_data(
            campaign_result
        )
    )

    return {
        "mission_summary": str(
            mission_summary_path
        ),
        "aggregate_summary": str(
            aggregate_summary_path
        ),
        "decision_frequencies": str(
            decision_frequencies_path
        ),
        "plot_data": str(
            plot_data_path
        )
    }
