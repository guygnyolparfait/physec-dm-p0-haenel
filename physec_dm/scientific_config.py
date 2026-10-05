# copy permet de créer des copies indépendantes
# des dictionnaires de configuration.
#
# Une politique ou un scénario ne doit jamais modifier
# silencieusement un autre élément de la campagne.
import copy


# math est utilisé pour recalculer correctement
# la corrélation minimale lorsqu'on modifie KDR_max :
#
# rho_min = cos(pi * KDR_max)
import math


# Parameters contient les paramètres numériques
# utilisés par les modules scientifiques déjà validés.
from physec_dm.parameters import (
    Parameters
)


# ================================================================
# 1. IDENTITÉ DE LA CONFIGURATION
# ================================================================


# Cette version identifie le contenu exact
# de la configuration scientifique.
#
# Elle doit être enregistrée avec les résultats
# afin de garantir la reproductibilité.
SCIENTIFIC_CONFIG_VERSION = "1.0.0"


# Les statuts utilisés dans le registre scientifique.
#
# Ces textes correspondent aux catégories
# déjà définies dans la documentation du projet.
ALLOWED_PARAMETER_STATUSES = [
    "literature",
    "datasheet",
    "derived",
    "calibrated",
    "scenario",
    "policy",
    "to_validate"
]


# ================================================================
# 2. REGISTRE DES PARAMÈTRES
# ================================================================


# Cette fonction crée une fiche simple
# pour un paramètre scientifique.
#
# Un dictionnaire est utilisé volontairement
# afin que le code reste facile à lire.
def create_parameter_record(
    name,
    value,
    unit,
    status,
    source,
    description,
    sensitivity_range,
    validated,
    blocking_for_final
):

    if status not in ALLOWED_PARAMETER_STATUSES:

        raise ValueError(
            "Le statut scientifique "
            + str(status)
            + " n'est pas autorisé."
        )

    return {
        "name": name,
        "value": value,
        "unit": unit,
        "status": status,
        "source": source,
        "description": description,
        "sensitivity_range": sensitivity_range,
        "validated": bool(validated),
        "blocking_for_final": bool(
            blocking_for_final
        )
    }


# Cette fonction construit le registre principal.
#
# Elle distingue :
#
# - les paramètres déjà justifiés ;
# - les choix de scénario ;
# - les paramètres encore ouverts.
#
# Les valeurs encore ouvertes restent explicitement
# marquées "to_validate", même lorsqu'une valeur
# exploratoire est utilisée dans une campagne pilote.
def build_parameter_registry(
    parameters=None
):

    if parameters is None:

        parameters = Parameters()

    records = [
        create_parameter_record(
            name="carrier_frequency_hz",
            value=parameters.carrier_frequency_hz,
            unit="Hz",
            status="scenario",
            source="Modèle nominal EU868",
            description=(
                "Fréquence porteuse utilisée "
                "dans le calcul du Doppler."
            ),
            sensitivity_range=[
                863000000.0,
                870000000.0
            ],
            validated=True,
            blocking_for_final=False
        ),

        create_parameter_record(
            name="hardware_reciprocity",
            value=parameters.hardware_reciprocity,
            unit="sans unité",
            status="calibrated",
            source="Paramètre calibré du dernier modèle",
            description=(
                "Facteur matériel de réciprocité "
                "entre Alice et Bob."
            ),
            sensitivity_range=[
                0.80,
                0.90,
                0.9582,
                0.99
            ],
            validated=True,
            blocking_for_final=False
        ),

        create_parameter_record(
            name="mallory_separation",
            value=parameters.mallory_separation,
            unit="sans unité",
            status="scenario",
            source="Valeur centrale du modèle",
            description=(
                "Séparation RFF normalisée "
                "entre Alice et Mallory."
            ),
            sensitivity_range=[
                0.5,
                1.0,
                2.0,
                3.0,
                5.0
            ],
            validated=True,
            blocking_for_final=False
        ),

        create_parameter_record(
            name="critical_message_probability",
            value=parameters.critical_message_probability,
            unit="probabilité",
            status="scenario",
            source="Scénario nominal du modèle",
            description=(
                "Probabilité qu'un message "
                "soit critique."
            ),
            sensitivity_range=[
                0.05,
                0.10,
                0.20
            ],
            validated=True,
            blocking_for_final=False
        ),

        create_parameter_record(
            name="mallory_attempt_probability",
            value=parameters.mallory_attempt_probability,
            unit="probabilité par période",
            status="scenario",
            source="Scénario nominal du modèle",
            description=(
                "Probabilité d'une tentative "
                "de Mallory pendant une période."
            ),
            sensitivity_range=[
                0.05,
                0.15,
                0.30
            ],
            validated=True,
            blocking_for_final=False
        ),

        create_parameter_record(
            name="snr_quantization_step_db",
            value=getattr(
                parameters,
                "snr_quantization_step_db",
                0.25
            ),
            unit="dB",
            status="scenario",
            source="Tableau X du dernier modèle",
            description=(
                "Résolution de quantification "
                "du SNR simulé."
            ),
            sensitivity_range=[
                0.0,
                0.25,
                0.50,
                1.0
            ],
            validated=True,
            blocking_for_final=False
        ),

        create_parameter_record(
            name="mac_cycles",
            value=parameters.mac_cycles,
            unit="cycles",
            status="to_validate",
            source=(
                "Profilage requis sur "
                "l'implémentation AES-CMAC retenue"
            ),
            description=(
                "Nombre de cycles CPU "
                "pour le calcul du MAC."
            ),
            sensitivity_range=[
                16000,
                32000,
                64000
            ],
            validated=False,
            blocking_for_final=True
        ),

        create_parameter_record(
            name="challenge_response_latency_s",
            value=parameters.challenge_response_latency_s,
            unit="s",
            status="to_validate",
            source=(
                "Décomposition protocolaire "
                "encore à mesurer"
            ),
            description=(
                "Latence complète du défi-réponse."
            ),
            sensitivity_range=[
                2.0,
                4.0,
                8.0
            ],
            validated=False,
            blocking_for_final=True
        ),

        create_parameter_record(
            name="reconciliation_cycles_per_bit",
            value=parameters.reconciliation_cycles_per_bit,
            unit="cycles/bit",
            status="to_validate",
            source=(
                "Profilage BCH requis "
                "sur la plateforme retenue"
            ),
            description=(
                "Coût CPU de la réconciliation."
            ),
            sensitivity_range=[
                50,
                100,
                200
            ],
            validated=False,
            blocking_for_final=True
        ),

        create_parameter_record(
            name="privacy_amplification_cycles",
            value=parameters.privacy_amplification_cycles,
            unit="cycles",
            status="to_validate",
            source=(
                "Profilage SHA-256 requis "
                "sur la plateforme retenue"
            ),
            description=(
                "Coût CPU de l'amplification "
                "de confidentialité."
            ),
            sensitivity_range=[
                3200,
                6400,
                12800
            ],
            validated=False,
            blocking_for_final=True
        ),

        create_parameter_record(
            name="sensing_energy_j",
            value=parameters.sensing_energy_j,
            unit="J",
            status="to_validate",
            source=(
                "Capteur réel non encore fixé"
            ),
            description=(
                "Énergie d'acquisition "
                "de la grandeur physique."
            ),
            sensitivity_range=[
                0.0005,
                0.001,
                0.002
            ],
            validated=False,
            blocking_for_final=True
        ),

        create_parameter_record(
            name="application_energy_j",
            value=parameters.application_energy_j,
            unit="J",
            status="to_validate",
            source=(
                "Firmware applicatif "
                "non encore profilé"
            ),
            description=(
                "Énergie du traitement applicatif."
            ),
            sensitivity_range=[
                0.001,
                0.002,
                0.004
            ],
            validated=False,
            blocking_for_final=True
        ),

        create_parameter_record(
            name="receive_windows_energy_j",
            value=parameters.receive_windows_energy_j,
            unit="J",
            status="to_validate",
            source=(
                "Fenêtres RX exactes "
                "non encore caractérisées"
            ),
            description=(
                "Énergie des fenêtres "
                "de réception LoRaWAN."
            ),
            sensitivity_range=[
                0.0015,
                0.003,
                0.006
            ],
            validated=False,
            blocking_for_final=True
        ),

        create_parameter_record(
            name="sleep_energy_j",
            value=parameters.sleep_energy_j,
            unit="J",
            status="to_validate",
            source=(
                "Durée et mode de veille "
                "à confirmer"
            ),
            description=(
                "Énergie de veille "
                "pendant une période."
            ),
            sensitivity_range=[
                0.002,
                0.004,
                0.008
            ],
            validated=False,
            blocking_for_final=True
        ),

        create_parameter_record(
            name="variation_feasible",
            value=parameters.variation_feasible,
            unit="booléen contrôlé",
            status="to_validate",
            source=(
                "Métrique de variabilité "
                "encore absente"
            ),
            description=(
                "Condition distincte de la corrélation "
                "pour la production d'entropie."
            ),
            sensitivity_range=[
                False,
                True
            ],
            validated=False,
            blocking_for_final=True
        ),

        create_parameter_record(
            name="k2_protocol_id",
            value=parameters.k2_protocol_id,
            unit="identifiant",
            status="to_validate",
            source=(
                "Protocole K2 complet "
                "non encore spécifié"
            ),
            description=(
                "Identifiant de la séquence complète "
                "d'opérations et d'échanges K2."
            ),
            sensitivity_range=None,
            validated=False,
            blocking_for_final=True
        )
    ]

    return records


# Cette fonction vérifie la structure du registre.
def validate_parameter_registry(
    records
):

    if records is None or len(records) == 0:

        raise ValueError(
            "Le registre des paramètres "
            "ne peut pas être vide."
        )

    required_fields = [
        "name",
        "value",
        "unit",
        "status",
        "source",
        "description",
        "sensitivity_range",
        "validated",
        "blocking_for_final"
    ]

    seen_names = set()

    for record in records:

        for field_name in required_fields:

            if field_name not in record:

                raise ValueError(
                    "Le champ "
                    + field_name
                    + " manque dans une fiche."
                )

        if record["name"] in seen_names:

            raise ValueError(
                "Le paramètre "
                + record["name"]
                + " apparaît plusieurs fois."
            )

        seen_names.add(
            record["name"]
        )

        if (
            record["status"]
            not in ALLOWED_PARAMETER_STATUSES
        ):

            raise ValueError(
                "Statut scientifique invalide."
            )

    return True


# Cette fonction retourne les paramètres
# qui empêchent encore une campagne finale
# avec prétention matérielle.
def get_final_blocking_parameters(
    records
):

    validate_parameter_registry(
        records
    )

    return [
        record["name"]
        for record in records
        if (
            record["blocking_for_final"]
            and not record["validated"]
        )
    ]


# Cette fonction construit un bandeau d'avertissement
# textuel, destiné à être écrit en tête de chaque export
# de résultats (CSV, figures, interprétation).
#
# Elle rend get_final_blocking_parameters réellement
# consultée par les scripts de campagne, au lieu de
# rester une métadonnée jamais lue : tant qu'au moins un
# paramètre blocking_for_final=True et validated=False
# est utilisé, aucun résultat énergétique ne doit être
# présenté comme définitif.
def build_blocking_parameters_warning_banner(
    records
):

    blocking_parameter_names = (
        get_final_blocking_parameters(
            records
        )
    )

    if len(blocking_parameter_names) == 0:

        return (
            "Aucun paramètre bloquant restant : "
            "les résultats énergétiques peuvent être "
            "considérés comme définitifs sous les "
            "hypothèses documentées."
        )

    banner_lines = [
        "=" * 70,
        "AVERTISSEMENT : résultats énergétiques exploratoires.",
        (
            "Les paramètres suivants restent "
            "\"à valider\" (mesure matérielle obligatoire "
            "avant tout résultat énergétique définitif) :"
        )
    ]

    for parameter_name in blocking_parameter_names:

        banner_lines.append(
            "  - "
            + parameter_name
        )

    banner_lines.append(
        "Toute comparaison d'énergie doit être lue comme "
        "exploratoire et sensible à ces paramètres, pas "
        "comme une mesure d'autonomie absolue."
    )

    banner_lines.append(
        "=" * 70
    )

    return "\n".join(banner_lines)


# ================================================================
# 3. PROFILS EXPLORATOIRES DES PARAMÈTRES OUVERTS
# ================================================================


# Les profils LOW, CENTRAL et HIGH sont des scénarios
# de sensibilité, pas des constantes de littérature.
#
# LOW utilise environ la moitié des valeurs centrales.
#
# HIGH utilise environ le double des valeurs centrales.
#
# Le but est d'observer si les conclusions changent
# lorsque les coûts encore ouverts sont modifiés.
def build_exploratory_cost_profiles():

    return {
        "LOW": {
            "challenge_response_latency_s": 2.0,
            "mac_cycles": 16000,
            "minimum_deadline_s": 30.0,
            "reconciliation_cycles_per_bit": 50,
            "privacy_amplification_cycles": 3200,
            "reconciliation_message_energy_j": 0.0025,
            "reconciliation_message_latency_s": 0.25,
            "security_strength_bits": 128,
            "sensing_energy_j": 0.0005,
            "application_energy_j": 0.001,
            "receive_windows_energy_j": 0.0015,
            "sleep_energy_j": 0.002
        },

        "CENTRAL": {
            "challenge_response_latency_s": 4.0,
            "mac_cycles": 32000,
            "minimum_deadline_s": 60.0,
            "reconciliation_cycles_per_bit": 100,
            "privacy_amplification_cycles": 6400,
            "reconciliation_message_energy_j": 0.005,
            "reconciliation_message_latency_s": 0.5,
            "security_strength_bits": 128,
            "sensing_energy_j": 0.001,
            "application_energy_j": 0.002,
            "receive_windows_energy_j": 0.003,
            "sleep_energy_j": 0.004
        },

        "HIGH": {
            "challenge_response_latency_s": 8.0,
            "mac_cycles": 64000,
            "minimum_deadline_s": 120.0,
            "reconciliation_cycles_per_bit": 200,
            "privacy_amplification_cycles": 12800,
            "reconciliation_message_energy_j": 0.010,
            "reconciliation_message_latency_s": 1.0,
            "security_strength_bits": 128,
            "sensing_energy_j": 0.002,
            "application_energy_j": 0.004,
            "receive_windows_energy_j": 0.006,
            "sleep_energy_j": 0.008
        }
    }


# Cette fonction applique un profil exploratoire
# à une copie de Parameters.
def apply_exploratory_cost_profile(
    parameters,
    profile_id
):

    profiles = build_exploratory_cost_profiles()

    if profile_id not in profiles:

        raise ValueError(
            "Le profil exploratoire "
            + str(profile_id)
            + " n'existe pas."
        )

    profile = profiles[
        profile_id
    ]

    for parameter_name in profile:

        setattr(
            parameters,
            parameter_name,
            profile[parameter_name]
        )

    # Cette valeur contrôlée permet d'exécuter
    # les scénarios où la variabilité PHY
    # est supposée disponible.
    #
    # Elle reste explicitement exploratoire.
    parameters.variation_feasible = True

    # K2 est exclu de la campagne primaire.
    #
    # Le Decision Maker rejettera son coût
    # si aucun dictionnaire k2_protocol n'est fourni.
    parameters.k2_protocol_id = (
        "K2_EXCLUDED_PRIMARY_CAMPAIGN"
    )

    # Les attributs suivants servent
    # à empêcher toute confusion avec une campagne finale.
    parameters.exploratory_run = True
    parameters.cost_profile_id = profile_id
    parameters.k2_enabled = False

    return parameters


# ================================================================
# 4. PARAMÈTRES DE BASE DE LA CAMPAGNE PILOTE
# ================================================================


# Cette fonction construit les paramètres
# de la campagne scientifique pilote.
#
# Elle reprend le scénario nominal :
#
# p_C = 0,10
# p_M = 0,15
# shadowing = 3 dB
#
# Les paramètres encore ouverts proviennent
# d'un profil de sensibilité clairement identifié.
def build_scientific_pilot_parameters(
    cost_profile_id="CENTRAL"
):

    parameters = Parameters()

    apply_exploratory_cost_profile(
        parameters,
        cost_profile_id
    )

    # Scénario nominal du dernier modèle.
    parameters.shadowing_std_db = 3.0
    parameters.critical_message_probability = 0.10
    parameters.mallory_attempt_probability = 0.15
    parameters.message_period_s = 60.0
    parameters.mallory_separation = 2.0
    parameters.effective_speed_m_s = 0.0

    # Résolution prévue par le dernier modèle.
    #
    # Cet attribut n'existait pas encore
    # dans parameters.py.
    parameters.snr_quantization_step_db = 0.25

    # Tolérances uniquement numériques.
    parameters.score_tolerance = 1e-12
    parameters.dominance_tolerance = 1e-12

    # Politique pilote équilibrée.
    #
    # Elle est statique et ne constitue pas encore
    # la politique contextuelle complète de DM-EQ108
    # à DM-EQ110.
    parameters.contextual_weights = [
        0.25,
        0.25,
        0.25,
        0.25
    ]

    parameters.scientific_config_version = (
        SCIENTIFIC_CONFIG_VERSION
    )

    return parameters


# ================================================================
# 5. SCÉNARIOS DÉTERMINISTES DU CANAL
# ================================================================


# Cette fonction crée le balayage du SNR
# demandé par le protocole :
#
# -20 dB à 30 dB
#
# avec un pas de 0,5 dB ou 1 dB.
#
# Ces scénarios servent à des expériences déterministes,
# pas encore à la mission Monte Carlo.
def build_deterministic_snr_scenarios(
    step_db=1.0,
    variation_feasible=True
):

    if step_db not in [
        0.5,
        1.0
    ]:

        raise ValueError(
            "Le pas SNR doit valoir 0,5 dB ou 1 dB."
        )

    scenarios = []

    current_snr_db = -20.0

    while current_snr_db <= 30.0 + 1e-12:

        scenario_id = (
            "DET-SNR-"
            + format(
                current_snr_db,
                "+05.1f"
            )
            .replace(
                "+",
                "P"
            )
            .replace(
                "-",
                "M"
            )
            .replace(
                ".",
                "_"
            )
        )

        scenarios.append(
            {
                "scenario_id": scenario_id,
                "parameter_overrides": {
                    "mean_snr_db": (
                        current_snr_db
                    ),
                    "shadowing_std_db": 0.0,
                    "critical_message_probability": 0.0,
                    "mallory_attempt_probability": 0.0,
                    "effective_speed_m_s": 0.0
                },
                "variation_feasible": (
                    variation_feasible
                ),
                "real_snr_bias_db": 0.0,
                "compromise_probability": 0.0,
                "mission_options": {
                    "max_steps": 1,
                    "rff_profile_available": True,
                    "initial_duty_cycle_airtime_s": 36.0,
                    "maximum_duty_cycle_airtime_s": 36.0,
                    "duty_cycle_recharge_s": 0.6
                }
            }
        )

        current_snr_db += step_db

    return scenarios


# ================================================================
# 6. SCÉNARIOS MONTE CARLO PILOTES
# ================================================================


# Cette fonction crée huit scénarios pilotes :
#
# quatre niveaux de SNR ;
# deux états contrôlés de variabilité PHY.
#
# La variabilité booléenne est un facteur expérimental.
#
# Elle ne doit pas être présentée comme une métrique
# de variabilité déjà validée.
def build_pilot_monte_carlo_scenarios(
    max_steps=1000
):

    if max_steps <= 0:

        raise ValueError(
            "max_steps doit être strictement positif."
        )

    snr_values_db = [
        -10.0,
        0.0,
        10.0,
        20.0
    ]

    variation_modes = [
        False,
        True
    ]

    scenarios = []

    for snr_db in snr_values_db:

        for variation_feasible in variation_modes:

            variation_text = (
                "PHY-ON"
                if variation_feasible
                else "PHY-OFF"
            )

            scenario_id = (
                "MC-SNR-"
                + str(
                    int(snr_db)
                )
                .replace(
                    "-",
                    "M"
                )
                + "-"
                + variation_text
            )

            scenarios.append(
                {
                    "scenario_id": scenario_id,

                    "parameter_overrides": {
                        "mean_snr_db": snr_db,
                        "shadowing_std_db": 3.0,
                        "critical_message_probability": 0.10,
                        "mallory_attempt_probability": 0.15,
                        "mallory_separation": 2.0,
                        "effective_speed_m_s": 0.0
                    },

                    "variation_feasible": (
                        variation_feasible
                    ),

                    "real_snr_bias_db": 0.0,

                    "compromise_probability": 0.0,

                    "mission_options": {
                        "max_steps": max_steps,
                        "rff_profile_available": True,

                        # 1 % de 3600 s donne 36 s.
                        "initial_duty_cycle_airtime_s": 36.0,
                        "maximum_duty_cycle_airtime_s": 36.0,

                        # En une période de 60 s,
                        # 1 % correspond à 0,6 s de recharge.
                        "duty_cycle_recharge_s": 0.6
                    }
                }
            )

    return scenarios


# ================================================================
# 7. SCÉNARIOS DE SENSIBILITÉ
# ================================================================


# Cette fonction ajoute une base commune
# à chaque scénario de sensibilité.
def create_sensitivity_scenario(
    scenario_id,
    parameter_overrides,
    max_steps=1000,
    variation_feasible=True
):

    return {
        "scenario_id": scenario_id,
        "parameter_overrides": (
            copy.deepcopy(
                parameter_overrides
            )
        ),
        "variation_feasible": (
            variation_feasible
        ),
        "real_snr_bias_db": 0.0,
        "compromise_probability": 0.0,
        "mission_options": {
            "max_steps": max_steps,
            "rff_profile_available": True,
            "initial_duty_cycle_airtime_s": 36.0,
            "maximum_duty_cycle_airtime_s": 36.0,
            "duty_cycle_recharge_s": 0.6
        }
    }


# Cette fonction crée des scénarios
# "un facteur à la fois".
#
# Chaque scénario modifie un seul paramètre
# autour du cas nominal.
def build_one_at_a_time_sensitivity_scenarios(
    max_steps=1000
):

    if max_steps <= 0:

        raise ValueError(
            "max_steps doit être strictement positif."
        )

    scenarios = []

    common_overrides = {
        "mean_snr_db": 5.0,
        "shadowing_std_db": 3.0,
        "critical_message_probability": 0.10,
        "mallory_attempt_probability": 0.15,
        "message_period_s": 60.0
    }

    # Séparation RFF de Mallory.
    for value in [
        0.5,
        1.0,
        2.0,
        3.0,
        5.0
    ]:

        overrides = copy.deepcopy(
            common_overrides
        )

        overrides[
            "mallory_separation"
        ] = value

        scenarios.append(
            create_sensitivity_scenario(
                scenario_id=(
                    "SENS-DM-"
                    + str(value)
                    .replace(
                        ".",
                        "_"
                    )
                ),
                parameter_overrides=overrides,
                max_steps=max_steps
            )
        )

    # Facteur matériel de réciprocité.
    for value in [
        0.80,
        0.90,
        0.9582,
        0.99
    ]:

        overrides = copy.deepcopy(
            common_overrides
        )

        overrides[
            "hardware_reciprocity"
        ] = value

        scenarios.append(
            create_sensitivity_scenario(
                scenario_id=(
                    "SENS-RHOHW-"
                    + str(value)
                    .replace(
                        ".",
                        "_"
                    )
                ),
                parameter_overrides=overrides,
                max_steps=max_steps
            )
        )

    # Seuil anticipé de renouvellement.
    for value in [
        0.40,
        0.60,
        0.80
    ]:

        overrides = copy.deepcopy(
            common_overrides
        )

        overrides[
            "renewal_trigger"
        ] = value

        scenarios.append(
            create_sensitivity_scenario(
                scenario_id=(
                    "SENS-QTRIG-"
                    + str(value)
                    .replace(
                        ".",
                        "_"
                    )
                ),
                parameter_overrides=overrides,
                max_steps=max_steps
            )
        )

    # KDR maximal.
    #
    # minimum_correlation est recalculé
    # pour préserver la cohérence croisée.
    for value in [
        0.20,
        0.30,
        0.40
    ]:

        overrides = copy.deepcopy(
            common_overrides
        )

        overrides[
            "maximum_kdr"
        ] = value

        overrides[
            "minimum_correlation"
        ] = math.cos(
            math.pi * value
        )

        scenarios.append(
            create_sensitivity_scenario(
                scenario_id=(
                    "SENS-KDRMAX-"
                    + str(value)
                    .replace(
                        ".",
                        "_"
                    )
                ),
                parameter_overrides=overrides,
                max_steps=max_steps
            )
        )

    # Pression adverse.
    for value in [
        0.05,
        0.15,
        0.30
    ]:

        overrides = copy.deepcopy(
            common_overrides
        )

        overrides[
            "mallory_attempt_probability"
        ] = value

        scenarios.append(
            create_sensitivity_scenario(
                scenario_id=(
                    "SENS-PM-"
                    + str(value)
                    .replace(
                        ".",
                        "_"
                    )
                ),
                parameter_overrides=overrides,
                max_steps=max_steps
            )
        )

    # Proportion de messages critiques.
    for value in [
        0.05,
        0.10,
        0.20
    ]:

        overrides = copy.deepcopy(
            common_overrides
        )

        overrides[
            "critical_message_probability"
        ] = value

        scenarios.append(
            create_sensitivity_scenario(
                scenario_id=(
                    "SENS-PC-"
                    + str(value)
                    .replace(
                        ".",
                        "_"
                    )
                ),
                parameter_overrides=overrides,
                max_steps=max_steps
            )
        )

    return scenarios


# ================================================================
# 8. POLITIQUES
# ================================================================


# Cette fonction décrit toutes les politiques
# exigées par le protocole scientifique.
#
# Elle distingue les politiques déjà exécutables
# avec le code actuel et celles qui exigent
# encore un moteur de politique dédié.
def build_policy_catalog():

    return [
        {
            "policy_id": "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS",
            "description": (
                "Decision Maker complet avec poids "
                "dépendant du contexte."
            ),
            "implementation_status": "BLOCKED",
            "blocking_reason": (
                "La fonction de poids contextuels "
                "DM-EQ108 à DM-EQ110 "
                "n'est pas encore implémentée."
            )
        },

        {
            "policy_id": "B1-CONVENTIONAL",
            "description": (
                "Authentification et renouvellement "
                "conventionnels."
            ),
            "implementation_status": "BLOCKED",
            "blocking_reason": (
                "Une règle fixe A1 avec K0/K2 "
                "doit être ajoutée."
            )
        },

        {
            "policy_id": "B2-NAIVE-PHYSEC",
            "description": (
                "PhySec naïve dès qu'elle semble "
                "disponible, sans plancher de sécurité."
            ),
            "implementation_status": "BLOCKED",
            "blocking_reason": (
                "Une règle fixe de sélection "
                "A2 et K1 doit être ajoutée."
            )
        },

        {
            "policy_id": "B3-FIXED-HYBRID",
            "description": (
                "Règle hybride fixe "
                "et non adaptative."
            ),
            "implementation_status": "BLOCKED",
            "blocking_reason": (
                "La règle hybride exacte "
                "doit être définie puis implémentée."
            )
        },

        {
            "policy_id": "B4-DM-NO-FAR-FLOOR",
            "description": (
                "Decision Maker sans plancher de FAR."
            ),
            "implementation_status": "EXECUTABLE_PILOT",
            "blocking_reason": None
        },

        {
            "policy_id": "P0-PILOT-BALANCED",
            "description": (
                "DM actuel avec poids statiques égaux."
            ),
            "implementation_status": "EXECUTABLE_PILOT",
            "blocking_reason": None
        }
    ]


# Cette fonction retourne uniquement
# les politiques que campaign.py peut exécuter
# sans modifier les modules validés.
#
# Il ne s'agit pas encore de la comparaison finale B1 à B4.
def build_executable_pilot_policies():

    return [
        {
            "policy_id": "P0-PILOT-BALANCED",
            "contextual_weights": [
                0.25,
                0.25,
                0.25,
                0.25
            ],
            "fallback_mode": "refuse"
        },

        {
            "policy_id": "B4-DM-NO-FAR-FLOOR",
            "contextual_weights": [
                0.25,
                0.25,
                0.25,
                0.25
            ],
            "parameter_overrides": {
                "critical_far_limit": 1.0,
                "normal_far_limit": 1.0
            },
            "fallback_mode": "refuse"
        }
    ]


# ================================================================
# 9. GRAINES MONTE CARLO
# ================================================================


# Cette fonction crée les graines de la campagne pilote.
#
# Trente répétitions constituent seulement
# un point de départ.
#
# La campagne finale devra augmenter N_MC
# jusqu'à stabilisation des intervalles de confiance.
def build_pilot_monte_carlo_seeds(
    count=30,
    first_seed=1000
):

    if count <= 0:

        raise ValueError(
            "Le nombre de graines "
            "doit être strictement positif."
        )

    if not isinstance(
        first_seed,
        int
    ):

        raise ValueError(
            "La première graine doit être un entier."
        )

    return [
        first_seed + index
        for index in range(count)
    ]


# ================================================================
# 10. VALIDATION DE LA CONFIGURATION
# ================================================================


# Cette fonction vérifie l'unicité
# d'un identifiant dans une liste de dictionnaires.
def validate_unique_identifiers(
    configurations,
    identifier_name
):

    identifiers = []

    for configuration in configurations:

        if identifier_name not in configuration:

            raise ValueError(
                identifier_name
                + " manque dans une configuration."
            )

        identifier = configuration[
            identifier_name
        ]

        if identifier in identifiers:

            raise ValueError(
                "Identifiant dupliqué : "
                + str(identifier)
            )

        identifiers.append(
            identifier
        )

    return True


# Cette fonction vérifie les politiques exécutables.
def validate_executable_policies(
    policies,
    epsilon
):

    validate_unique_identifiers(
        policies,
        "policy_id"
    )

    for policy in policies:

        if "contextual_weights" not in policy:

            raise ValueError(
                "La politique "
                + policy["policy_id"]
                + " ne contient pas de poids."
            )

        weights = policy[
            "contextual_weights"
        ]

        if len(weights) != 4:

            raise ValueError(
                "Une politique doit contenir "
                "exactement quatre poids."
            )

        if any(
            weight < 0
            for weight in weights
        ):

            raise ValueError(
                "Les poids ne peuvent pas "
                "être négatifs."
            )

        if abs(
            sum(weights) - 1.0
        ) > epsilon:

            raise ValueError(
                "La somme des poids "
                "doit être égale à 1."
            )

    return True


# Cette fonction vérifie les scénarios.
def validate_scientific_scenarios(
    scenarios
):

    validate_unique_identifiers(
        scenarios,
        "scenario_id"
    )

    for scenario in scenarios:

        if "parameter_overrides" not in scenario:

            raise ValueError(
                "Chaque scénario doit contenir "
                "parameter_overrides."
            )

        if "variation_feasible" not in scenario:

            raise ValueError(
                "Chaque scénario doit déclarer "
                "variation_feasible."
            )

        if "mission_options" not in scenario:

            raise ValueError(
                "Chaque scénario doit contenir "
                "mission_options."
            )

        mission_options = scenario[
            "mission_options"
        ]

        if (
            mission_options[
                "initial_duty_cycle_airtime_s"
            ]
            > mission_options[
                "maximum_duty_cycle_airtime_s"
            ]
        ):

            raise ValueError(
                "Le budget duty-cycle initial "
                "ne peut pas dépasser son maximum."
            )

    return True


# Cette fonction valide toute la configuration pilote.
#
# final_run=False autorise les profils exploratoires.
#
# final_run=True refuse toute valeur encore ouverte.
def validate_scientific_configuration(
    parameters,
    scenarios,
    policies,
    seeds,
    parameter_registry,
    final_run=False
):

    errors, warnings = parameters.validate(
        require_complete=True
    )

    if len(errors) > 0:

        raise ValueError(
            "Parameters contient des erreurs : "
            + " | ".join(errors)
        )

    validate_parameter_registry(
        parameter_registry
    )

    validate_scientific_scenarios(
        scenarios
    )

    validate_executable_policies(
        policies,
        parameters.tchebycheff_epsilon
    )

    if seeds is None or len(seeds) == 0:

        raise ValueError(
            "Au moins une graine est requise."
        )

    if len(set(seeds)) != len(seeds):

        raise ValueError(
            "Les graines doivent être uniques."
        )

    if any(
        not isinstance(seed, int)
        for seed in seeds
    ):

        raise ValueError(
            "Toutes les graines doivent être entières."
        )

    final_blockers = (
        get_final_blocking_parameters(
            parameter_registry
        )
    )

    if final_run and len(final_blockers) > 0:

        raise ValueError(
            "Campagne finale bloquée par : "
            + ", ".join(final_blockers)
        )

    validation_warnings = list(
        warnings
    )

    if len(final_blockers) > 0:

        validation_warnings.append(
            "Campagne exploratoire : "
            + ", ".join(final_blockers)
        )

    return {
        "valid": True,
        "final_run": final_run,
        "final_blockers": final_blockers,
        "warnings": validation_warnings
    }


# ================================================================
# 11. CONFIGURATION PILOTE COMPLÈTE
# ================================================================


# Cette fonction construit un objet simple
# contenant tout ce qui est nécessaire
# à la campagne pilote scientifique.
def build_scientific_pilot_configuration(
    cost_profile_id="CENTRAL",
    max_steps=1000,
    seed_count=30
):

    parameters = (
        build_scientific_pilot_parameters(
            cost_profile_id
        )
    )

    scenarios = (
        build_pilot_monte_carlo_scenarios(
            max_steps=max_steps
        )
    )

    policies = (
        build_executable_pilot_policies()
    )

    seeds = build_pilot_monte_carlo_seeds(
        count=seed_count
    )

    parameter_registry = (
        build_parameter_registry(
            parameters
        )
    )

    validation_result = (
        validate_scientific_configuration(
            parameters=parameters,
            scenarios=scenarios,
            policies=policies,
            seeds=seeds,
            parameter_registry=(
                parameter_registry
            ),
            final_run=False
        )
    )

    return {
        "config_version": (
            SCIENTIFIC_CONFIG_VERSION
        ),
        "campaign_id": (
            "CAMP-SCIENTIFIC-PILOT-01"
        ),
        "exploratory_run": True,
        "parameters": parameters,
        "parameter_registry": (
            parameter_registry
        ),
        "scenarios": scenarios,
        "policies": policies,
        "seeds": seeds,
        "k2_protocol": None,
        "validation": validation_result
    }


# Cette fonction empêche de créer par erreur
# une configuration annoncée comme finale.
#
# Elle sera remplacée seulement après :
#
# - le profilage CPU ;
# - la validation de l'énergie de base ;
# - la définition de la métrique de variabilité ;
# - la définition du protocole K2 ;
# - l'implémentation des politiques B1 à B3 ;
# - l'implémentation des poids contextuels.
def build_final_scientific_configuration():

    parameters = (
        build_scientific_pilot_parameters(
            "CENTRAL"
        )
    )

    registry = build_parameter_registry(
        parameters
    )

    blockers = get_final_blocking_parameters(
        registry
    )

    raise ValueError(
        "La configuration finale n'est pas encore autorisée. "
        "Blocages : "
        + ", ".join(blockers)
    )
