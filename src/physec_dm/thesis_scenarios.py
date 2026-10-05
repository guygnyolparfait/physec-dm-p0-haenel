# copy permet de créer des copies indépendantes
# des paramètres pendant la validation.
import copy


# La configuration scientifique pilote contient
# les valeurs centrales déjà utilisées dans le projet.
from physec_dm.scientific_config import (
    build_scientific_pilot_parameters
)


# ================================================================
# 1. IDENTITÉ DE L'EXPÉRIENCE
# ================================================================


THREE_SCENARIO_CONFIG_VERSION = "2.0.0"

THREE_SCENARIO_CAMPAIGN_ID = (
    "CAMP-THESIS-THREE-SCENARIOS-K1-PROGRESSIVE-01"
)


# Les identifiants sont figés.
#
# Leur ordre est également l'ordre utilisé
# dans les tableaux et les figures.
THREE_SCENARIO_IDS = [
    "S1-DEGRADED-CHANNEL",
    "S2-RESOURCE-CONSTRAINED",
    "S3-HIGH-SECURITY-PRESSURE"
]


# ================================================================
# 2. PROTOCOLE K2 EXPLORATOIRE
# ================================================================


# Cette fonction décrit un protocole K2 simplifié
# uniquement pour la campagne préliminaire.
#
# Il utilise :
#
# - une opération ECC déjà paramétrée ;
# - un message transmis de la taille de la réponse ;
# - un message reçu de la taille du défi.
#
# IMPORTANT :
#
# Ce dictionnaire ne doit pas être présenté
# comme un protocole K2 définitivement validé.
#
# Il permet seulement de disposer d'un mécanisme
# conventionnel de secours dans le scénario S1,
# lorsque la génération de clé PHY est impossible.
def build_exploratory_k2_protocol(
    parameters
):

    return {
        "protocol_id": "K2-SIMPLIFIED-PILOT",

        "ecc_operation_energies_j": [
            parameters.ecc_signature_energy_j
        ],

        "ecc_operation_times_s": [
            parameters.ecc_signature_time_s
        ],

        "tx_message_sizes_bytes": [
            parameters.response_bytes
        ],

        "rx_message_sizes_bytes": [
            parameters.challenge_bytes
        ]
    }


# ================================================================
# 3. PARAMÈTRES COMMUNS
# ================================================================


# Cette fonction construit les paramètres communs
# aux trois scénarios.
#
# Le profil CENTRAL reste explicitement exploratoire.
#
# La cryptopériode utilise les valeurs nominales
# du modèle (parameters.py).
#
# Une version antérieure raccourcissait volontairement
# la cryptopériode (maximum_messages_per_key=100,
# maximum_key_age_s=6000.0) dans l'intention de rendre
# K1a, K1b et K2 réellement observables pendant une
# expérience de 300 périodes.
#
# L'audit results/three_scenarios_explicit_analysis/
# k1a_k1b_model_consistency_audit.md a démontré que cet
# effet était inverse : raccourcir la cryptopériode
# raccourcit proportionnellement l'échéance de
# renouvellement (key_deadline_s) sans réduire le nombre
# de mesures physiques nécessaires (N_meas, qui dépend
# uniquement du canal), rendant K1a/K1b mathématiquement
# inatteignables (ratio latence/échéance jusqu'à 6199x).
#
# La cryptopériode nominale est donc restaurée ici.
def build_three_scenario_parameters():

    parameters = (
        build_scientific_pilot_parameters(
            cost_profile_id="CENTRAL"
        )
    )

    # Valeur nominale du modèle (parameters.py).
    #
    # Une clé atteint son seuil anticipé
    # après environ 600 messages :
    #
    # 0,60 * 1000 = 600.
    parameters.maximum_messages_per_key = 1000

    # Valeur nominale du modèle (parameters.py).
    #
    # Même logique temporelle :
    #
    # 1440 périodes * 60 s = 86400 s.
    parameters.maximum_key_age_s = 86400.0

    parameters.renewal_trigger = 0.60

    # L'échéance minimale est cohérente
    # avec une période de message.
    parameters.minimum_deadline_s = 60.0

    # Le protocole K2 utilisé est explicitement
    # identifié comme simplifié et exploratoire.
    parameters.k2_protocol_id = (
        "K2-SIMPLIFIED-PILOT"
    )

    parameters.three_scenario_config_version = (
        THREE_SCENARIO_CONFIG_VERSION
    )

    return parameters


# ================================================================
# 4. POIDS CONTEXTUELS APPROXIMÉS
# ================================================================


# Le moteur dynamique complet des poids contextuels
# n'est pas encore implémenté.
#
# Pour ce retour préliminaire, chaque scénario utilise
# un vecteur fixe correspondant à son objectif principal.
#
# L'ordre des poids est :
#
# [énergie, latence, authentification, qualité de clé]
def build_scenario_weights():

    return {
        # S1 privilégie la robustesse de sécurité
        # et la prudence lorsque la PHY est dégradée.
        "S1-DEGRADED-CHANNEL": [
            0.20,
            0.20,
            0.35,
            0.25
        ],

        # S2 privilégie l'énergie et la latence.
        "S2-RESOURCE-CONSTRAINED": [
            0.40,
            0.35,
            0.15,
            0.10
        ],

        # S3 privilégie l'authentification
        # et la qualité de clé.
        "S3-HIGH-SECURITY-PRESSURE": [
            0.10,
            0.10,
            0.40,
            0.40
        ]
    }


# ================================================================
# 5. TROIS SCÉNARIOS DE LA PROPOSITION DE THÈSE
# ================================================================


# Cette fonction construit exactement
# les trois scénarios retenus.
def build_thesis_scenarios(
    parameters=None,
    max_steps=300
):

    if max_steps <= 0:

        raise ValueError(
            "max_steps doit être strictement positif."
        )

    if parameters is None:

        parameters = (
            build_three_scenario_parameters()
        )

    weights = build_scenario_weights()

    k2_protocol = (
        build_exploratory_k2_protocol(
            parameters
        )
    )

    # Réserve nominale de 5 % de la batterie complète.
    nominal_reserve_j = (
        parameters.minimum_battery_energy_j
    )

    # S2 commence 80 J au-dessus
    # de la réserve nominale.
    #
    # Une mission complète de 300 périodes consomme
    # environ 60 J.
    #
    # Les 20 J supplémentaires constituent
    # une marge de sécurité au-delà de cette consommation
    # estimée, afin que la contrainte énergétique
    # reste réellement visible sans épuiser
    # systématiquement la marge disponible.
    #
    # S2 demeure donc un scénario énergétiquement contraint.
    constrained_initial_energy_j = (
        nominal_reserve_j
        + 80.0
    )

    # Parameters exprime la réserve comme une fraction
    # de l'énergie initiale de la simulation.
    #
    # Cette valeur conserve exactement
    # la réserve absolue nominale.
    constrained_reserve_fraction = (
        nominal_reserve_j
        / constrained_initial_energy_j
    )

    common_mission_options = {
        "max_steps": max_steps,
        "rff_profile_available": True,

        # 1 % de 3600 s donne 36 s par heure.
        "initial_duty_cycle_airtime_s": 36.0,
        "maximum_duty_cycle_airtime_s": 36.0,

        # Une période dure 60 s.
        #
        # La recharge correspond donc à :
        #
        # 0,01 * 60 = 0,6 s.
        "duty_cycle_recharge_s": 0.6
    }

    scenarios = [
        {
            "scenario_id": (
                "S1-DEGRADED-CHANNEL"
            ),

            "short_name": (
                "S1 - Canal dégradé"
            ),

            "scientific_question": (
                "Le Decision Maker rejette-t-il "
                "les mécanismes PHY non fiables ?"
            ),

            "expected_behavior": (
                "Réduction de K1a/K1b, utilisation "
                "de mécanismes conventionnels et maintien "
                "du plancher de sécurité."
            ),

            "parameter_overrides": {
                "mean_snr_db": -10.0,
                "shadowing_std_db": 3.0,
                "critical_message_probability": 0.10,
                "mallory_attempt_probability": 0.15,
                "effective_speed_m_s": 0.0,
                "contextual_weights": weights[
                    "S1-DEGRADED-CHANNEL"
                ]
            },

            # La variabilité PHY est explicitement
            # indisponible dans S1.
            "variation_feasible": False,

            "real_snr_bias_db": 0.0,
            "compromise_probability": 0.0,

            "k2_protocol": copy.deepcopy(
                k2_protocol
            ),

            "mission_options": copy.deepcopy(
                common_mission_options
            )
        },

        {
            "scenario_id": (
                "S2-RESOURCE-CONSTRAINED"
            ),

            "short_name": (
                "S2 - Ressources contraintes"
            ),

            "scientific_question": (
                "Le Decision Maker minimise-t-il "
                "l'énergie et la latence tout en "
                "maintenant la sécurité ?"
            ),

            "expected_behavior": (
                "Sélection de décisions moins coûteuses, "
                "réduction de l'énergie et de la latence, "
                "sans violation des contraintes."
            ),

            "parameter_overrides": {
                "mean_snr_db": 5.0,
                "shadowing_std_db": 3.0,

                # Forte proportion de messages critiques.
                "critical_message_probability": 0.60,

                "mallory_attempt_probability": 0.15,
                "effective_speed_m_s": 0.0,

                # Batterie très proche de sa réserve.
                "initial_battery_energy_j": (
                    constrained_initial_energy_j
                ),
                "battery_reserve_fraction": (
                    constrained_reserve_fraction
                ),
                "minimum_battery_energy_j": (
                    nominal_reserve_j
                ),

                "contextual_weights": weights[
                    "S2-RESOURCE-CONSTRAINED"
                ]
            },

            "variation_feasible": True,

            "real_snr_bias_db": 0.0,
            "compromise_probability": 0.0,

            "k2_protocol": copy.deepcopy(
                k2_protocol
            ),

            "mission_options": copy.deepcopy(
                common_mission_options
            )
        },

        {
            "scenario_id": (
                "S3-HIGH-SECURITY-PRESSURE"
            ),

            "short_name": (
                "S3 - Forte pression de sécurité"
            ),

            "scientific_question": (
                "Le Decision Maker maximise-t-il "
                "l'authentification et la qualité de clé "
                "lorsque la PHY est favorable ?"
            ),

            "expected_behavior": (
                "Utilisation accrue de A2, K1a ou K1b, "
                "robustesse d'authentification élevée "
                "et meilleure qualité de clé."
            ),

            "parameter_overrides": {
                "mean_snr_db": 20.0,
                "shadowing_std_db": 3.0,
                "critical_message_probability": 0.30,

                # Pression adverse plus forte.
                "mallory_attempt_probability": 0.30,

                "mallory_separation": 2.0,
                "effective_speed_m_s": 0.0,

                "contextual_weights": weights[
                    "S3-HIGH-SECURITY-PRESSURE"
                ]
            },

            "variation_feasible": True,

            "real_snr_bias_db": 0.0,
            "compromise_probability": 0.0,

            "k2_protocol": copy.deepcopy(
                k2_protocol
            ),

            "mission_options": copy.deepcopy(
                common_mission_options
            )
        }
    ]

    return scenarios


# ================================================================
# 6. POLITIQUE ET GRAINES
# ================================================================


# Une seule politique représente la méthode proposée.
#
# Les poids sont placés dans chaque scénario
# afin d'approximer le comportement contextuel.
def build_thesis_policy():

    return [
        {
            "policy_id": (
                "P0-THESIS-CONTEXTUAL-PILOT"
            ),

            "fallback_mode": "refuse"
        }
    ]


# Trente graines communes permettent
# de produire une moyenne et un intervalle de confiance.
def build_thesis_seeds(
    count=30,
    first_seed=2000
):

    if count <= 0:

        raise ValueError(
            "Le nombre de graines doit être positif."
        )

    if not isinstance(
        first_seed,
        int
    ):

        raise ValueError(
            "La première graine doit être entière."
        )

    return [
        first_seed + index
        for index in range(count)
    ]


# ================================================================
# 7. VALIDATION
# ================================================================


# Cette fonction applique les modifications
# d'un scénario à une copie des paramètres.
#
# Elle est utilisée uniquement pour valider
# les cohérences avant la campagne.
def apply_scenario_overrides_for_validation(
    parameters,
    scenario
):

    scenario_parameters = copy.deepcopy(
        parameters
    )

    for parameter_name, value in (
        scenario["parameter_overrides"].items()
    ):

        if not hasattr(
            scenario_parameters,
            parameter_name
        ):

            raise ValueError(
                "Paramètre de scénario inconnu : "
                + parameter_name
            )

        setattr(
            scenario_parameters,
            parameter_name,
            copy.deepcopy(
                value
            )
        )

    return scenario_parameters


# Cette fonction vérifie que les trois scénarios
# correspondent exactement à la décision prise.
def validate_thesis_scenarios(
    parameters,
    scenarios,
    policies,
    seeds
):

    if len(scenarios) != 3:

        raise ValueError(
            "La campagne doit contenir "
            "exactement trois scénarios."
        )

    scenario_ids = [
        scenario["scenario_id"]
        for scenario in scenarios
    ]

    if scenario_ids != THREE_SCENARIO_IDS:

        raise ValueError(
            "Les trois scénarios ou leur ordre "
            "ne correspondent pas à la configuration figée."
        )

    if len(policies) != 1:

        raise ValueError(
            "Cette campagne préliminaire "
            "utilise exactement une politique."
        )

    if seeds is None or len(seeds) == 0:

        raise ValueError(
            "Au moins une graine est requise."
        )

    if len(set(seeds)) != len(seeds):

        raise ValueError(
            "Les graines doivent être uniques."
        )

    for scenario in scenarios:

        weights = scenario[
            "parameter_overrides"
        ]["contextual_weights"]

        if len(weights) != 4:

            raise ValueError(
                "Chaque scénario doit contenir "
                "quatre poids."
            )

        if any(
            weight < 0
            for weight in weights
        ):

            raise ValueError(
                "Les poids ne peuvent pas être négatifs."
            )

        if abs(
            sum(weights) - 1.0
        ) > parameters.tchebycheff_epsilon:

            raise ValueError(
                "La somme des poids doit être égale à 1."
            )

        scenario_parameters = (
            apply_scenario_overrides_for_validation(
                parameters,
                scenario
            )
        )

        errors, warnings = (
            scenario_parameters.validate(
                require_complete=True
            )
        )

        if len(errors) > 0:

            raise ValueError(
                scenario["scenario_id"]
                + " contient des erreurs : "
                + " | ".join(errors)
            )

        if len(warnings) > 0:

            raise ValueError(
                scenario["scenario_id"]
                + " contient des avertissements : "
                + " | ".join(warnings)
            )

        k2_protocol = scenario[
            "k2_protocol"
        ]

        required_k2_fields = [
            "ecc_operation_energies_j",
            "ecc_operation_times_s",
            "tx_message_sizes_bytes",
            "rx_message_sizes_bytes"
        ]

        for field_name in required_k2_fields:

            if field_name not in k2_protocol:

                raise ValueError(
                    "Champ K2 manquant : "
                    + field_name
                )

    # Vérifications scientifiques propres
    # aux trois scénarios.
    s1 = scenarios[0]
    s2 = scenarios[1]
    s3 = scenarios[2]

    if s1["variation_feasible"] is not False:

        raise ValueError(
            "S1 doit rendre la variabilité PHY indisponible."
        )

    if (
        s2["parameter_overrides"][
            "initial_battery_energy_j"
        ]
        <= s2["parameter_overrides"][
            "minimum_battery_energy_j"
        ]
    ):

        raise ValueError(
            "S2 doit conserver une petite marge "
            "au-dessus de la réserve."
        )

    if (
        s3["parameter_overrides"][
            "mallory_attempt_probability"
        ]
        <= s1["parameter_overrides"][
            "mallory_attempt_probability"
        ]
    ):

        raise ValueError(
            "S3 doit présenter une pression "
            "de sécurité supérieure à S1."
        )

    return True


# ================================================================
# 8. CONFIGURATION COMPLÈTE
# ================================================================


def build_three_scenario_configuration(
    max_steps=300,
    seed_count=30
):

    parameters = (
        build_three_scenario_parameters()
    )

    scenarios = build_thesis_scenarios(
        parameters=parameters,
        max_steps=max_steps
    )

    policies = build_thesis_policy()

    seeds = build_thesis_seeds(
        count=seed_count
    )

    validate_thesis_scenarios(
        parameters=parameters,
        scenarios=scenarios,
        policies=policies,
        seeds=seeds
    )

    return {
        "config_version": (
            THREE_SCENARIO_CONFIG_VERSION
        ),
        "campaign_id": (
            THREE_SCENARIO_CAMPAIGN_ID
        ),
        "preliminary_results": True,
        "parameters": parameters,
        "scenarios": scenarios,
        "policies": policies,
        "seeds": seeds,
        "max_steps": max_steps,
        "output_directory": (
            "results/three_scenarios"
        )
    }
