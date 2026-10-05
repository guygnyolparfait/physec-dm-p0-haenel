# Ce module remplace les anciens scénarios principalement
# numériques (physec_dm/thesis_scenarios.py) par cinq véritables
# cas d'étude dynamiques, comparables à l'exemple de l'auto-école
# donné par l'encadrante : chaque cas d'étude est une histoire
# complète (système, environnement, mission, question
# scientifique, phases, critères de réussite), pas seulement un
# vecteur de paramètres.
#
# Ce module NE MODIFIE AUCUNE ÉQUATION SCIENTIFIQUE. Il réutilise
# exclusivement des briques déjà validées :
#
# - physec_dm.thesis_scenarios.build_three_scenario_parameters()
#   pour la cryptopériode nominale déjà restaurée et le profil de
#   coût CENTRAL déjà validé ;
# - physec_dm.thesis_scenarios.build_exploratory_k2_protocol()
#   pour le protocole K2 déjà validé ;
# - physec_dm.contextual_policy.resolve_contextual_weights()
#   comme UNIQUE source des poids contextuels (aucun scénario ne
#   fixe ses propres poids à la main) ;
# - physec_dm.channel.calculate_channel_metrics() (via
#   scenario_controller.py) pour tout calcul de corrélation, de
#   Doppler et de KDR — jamais recalculé ici.
#
# Chaque cas d'étude est un dictionnaire, jamais une simple liste
# de parameter_overrides : la structure narrative (description,
# question scientifique, phases, critères) est une partie du
# contrat scientifique de ce cas d'étude, au même titre que ses
# valeurs numériques.
import copy

from physec_dm.models import (
    AuthenticationAction,
    Decision,
    DecisionMakerResult,
    KeyAction
)

from physec_dm.decision_maker import (
    evaluate_decision,
    run_decision_maker
)

from physec_dm.thesis_scenarios import (
    build_exploratory_k2_protocol,
    build_three_scenario_parameters
)


CASE_STUDY_CONFIG_VERSION = "1.0.0"

CASE_STUDY_CAMPAIGN_ID = (
    "CAMP-THESIS-FIVE-CASE-STUDIES-01"
)

CASE_STUDY_IDS = [
    "S1-REMOTE-AGRICULTURAL-SENSOR",
    "S2-INDUSTRIAL-CRITICAL-ALARM",
    "S3-MOBILE-VEHICLE",
    "S4-DENSE-URBAN-NETWORK",
    "S5-CRITICAL-INFRASTRUCTURE-ATTACK"
]

POLICY_IDS = [
    "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS",
    "B1-CONVENTIONAL",
    "B2-NAIVE-PHYSEC-NO-FLOOR",
    "B3-HYBRID-FIXED",
    "B4-DM-NO-FAR-FLOOR"
]


# ================================================================
# 1. BASE COMMUNE (paramètres déjà validés, jamais recalculés ici)
# ================================================================


def build_case_study_base_parameters():

    return build_three_scenario_parameters()


# Applique les overrides d'un cas d'étude à une copie
# indépendante des paramètres de base — même mécanisme que
# thesis_scenarios.apply_scenario_overrides_for_validation,
# reproduit ici pour ne pas coupler case_studies.py à
# l'existence de scénarios "thèse" appelés en parallèle.
def apply_case_study_overrides(
    base_parameters,
    case_study
):

    scenario_parameters = copy.deepcopy(
        base_parameters
    )

    for parameter_name, value in (
        case_study["parameter_overrides"].items()
    ):

        if not hasattr(
            scenario_parameters,
            parameter_name
        ):

            raise ValueError(
                "Paramètre de cas d'étude inconnu : "
                + parameter_name
            )

        setattr(
            scenario_parameters,
            parameter_name,
            copy.deepcopy(value)
        )

    return scenario_parameters


# ================================================================
# 2. CAS D'ÉTUDE S1 — CAPTEUR AGRICOLE ISOLÉ
# ================================================================


def build_case_study_s1():

    return {
        "scenario_id": "S1-REMOTE-AGRICULTURAL-SENSOR",

        "scenario_name": (
            "Capteur agricole isolé"
        ),

        "case_study_description": (
            "Un capteur LoRa fixe mesure l'humidité du sol "
            "dans une zone rurale isolée. Il est alimenté "
            "par une petite batterie difficile ou coûteuse "
            "à remplacer (accès physique limité). Les "
            "messages sont majoritairement des relevés "
            "périodiques non critiques. La pression "
            "d'attaque est faible à modérée : un "
            "attaquant occasionnel pourrait tenter "
            "d'usurper le capteur, mais aucune menace "
            "ciblée et soutenue n'est supposée."
        ),

        "system_under_test": (
            "Nœud LoRa fixe (Alice), authentification "
            "conventionnelle (A1) ou par empreinte "
            "radiofréquence (A2), gestion de clé K0/K1a/"
            "K1b/K2 arbitrée par le Decision Maker."
        ),

        "environment_description": (
            "Zone rurale dégagée, peu d'obstacles, canal "
            "radio globalement stable avec des "
            "fluctuations naturelles modérées (shadowing "
            "faible). Nœud fixe : aucune mobilité."
        ),

        "mission_description": (
            "Mission longue durée (surveillance continue "
            "de l'humidité du sol) sur une seule phase "
            "stable, sans événement brusque, afin "
            "d'observer le comportement du Decision Maker "
            "en régime permanent, où l'économie d'énergie "
            "est l'enjeu dominant."
        ),

        "scientific_question": (
            "Le Decision Maker réduit-il l'énergie "
            "consommée tout en maintenant une "
            "authentification et une gestion de clé "
            "acceptables, dans un contexte où rien "
            "n'impose explicitement l'économie d'énergie "
            "si ce n'est le contexte lui-même (batterie "
            "limitée, faible criticité) ?"
        ),

        "phases": [
            {
                "phase_name": (
                    "Fonctionnement stable "
                    "(mesures périodiques d'humidité)"
                ),
                "start_fraction": 0.0,
                "end_fraction": 1.0,
                "mean_snr_db": 8.0,
                "shadowing_std_db": 2.0,
                "effective_speed_m_s": 0.0,
                "critical_message_probability": 0.05,
                "mallory_attempt_probability": 0.10,
                "criticality_forced": None,
                "compromise_suspected_forced": False
            }
        ],

        # variation_feasible=True : la faisabilité PHY
        # réelle des K1a/K1b doit être déterminée par
        # calculate_agreement_feasibility /
        # calculate_phy_feasibility à partir du KDR
        # effectif calculé par channel.py et
        # key_generation.py — jamais imposée à False.
        "variation_feasible": True,

        "parameters_held_constant": [
            "mean_snr_db (8.0 dB) et shadowing_std_db "
            "(2.0 dB) sur toute la mission — canal stable",
            "effective_speed_m_s = 0.0 — nœud fixe",
            "cryptopériode nominale "
            "(maximum_messages_per_key=1000, "
            "maximum_key_age_s=86400.0)",
            "profil de coût CENTRAL "
            "(build_scientific_pilot_parameters)"
        ],

        "parameters_allowed_to_change": [
            "battery_energy_j (décroît naturellement "
            "avec la consommation réelle débitée par "
            "mission.py)",
            "key_age_s, messages_with_current_key, "
            "k1a/k1b_measurements_collected "
            "(progression naturelle de l'état)"
        ],

        "success_criteria": [
            "Énergie moyenne par message servi "
            "significativement inférieure à celle d'une "
            "politique n'utilisant jamais K1a/K1b/A1 "
            "seul (comparaison avec B1-CONVENTIONAL).",
            "Service maintenu (taux de refus légitime "
            "faible).",
            "FAR empirique sous le plancher de sécurité "
            "configuré (aucune violation).",
            "Progression non nulle de "
            "k1a_measurements_collected lorsque la PHY "
            "est faisable (démontre que la correction "
            "progressive K1a/K1b reste active)."
        ],

        "validity_limits": [
            "Scénario mono-phase : ne permet pas "
            "d'observer une réaction à un changement "
            "brutal de contexte (voir S2/S3/S4/S5 pour "
            "cela).",
            "La faisabilité PHY effective de K1a/K1b à "
            "8 dB dépend du KDR réellement calculé ; "
            "elle n'est pas garantie et doit être lue "
            "dans les résultats, pas supposée."
        ],

        "k2_protocol": None,

        "parameter_overrides": {
            "mean_snr_db": 8.0,
            "shadowing_std_db": 2.0,
            "critical_message_probability": 0.05,
            "mallory_attempt_probability": 0.10,
            "effective_speed_m_s": 0.0
        }
    }


# ================================================================
# 3. CAS D'ÉTUDE S2 — ALARME CRITIQUE INDUSTRIELLE
# ================================================================


def build_case_study_s2():

    return {
        "scenario_id": "S2-INDUSTRIAL-CRITICAL-ALARM",

        "scenario_name": (
            "Alarme critique industrielle"
        ),

        "case_study_description": (
            "Un capteur industriel (par exemple, "
            "surveillance de pression ou de température "
            "sur une ligne de production) fonctionne "
            "normalement, avec un trafic majoritairement "
            "non critique. Une alarme critique survient "
            "ensuite : un message urgent doit être "
            "authentifié et acheminé rapidement, avant "
            "que le système ne revienne progressivement à "
            "un fonctionnement normal."
        ),

        "system_under_test": (
            "Nœud LoRa fixe en environnement industriel, "
            "même chaîne de décision qu'en S1 (A1/A2, "
            "K0/K1a/K1b/K2)."
        ),

        "environment_description": (
            "Environnement industriel : shadowing plus "
            "marqué qu'en zone rurale (structures "
            "métalliques, machines), pression d'attaque "
            "modérée."
        ),

        "mission_description": (
            "Trois phases : fonctionnement normal, "
            "alarme critique maintenue, récupération "
            "progressive."
        ),

        "scientific_question": (
            "Le Decision Maker change-t-il rapidement de "
            "décision pour minimiser la latence pendant "
            "l'alarme, sans jamais violer les contraintes "
            "de sécurité (plancher de FAR, échéance de "
            "clé) ?"
        ),

        "phases": [
            {
                "phase_name": "Fonctionnement normal",
                "start_fraction": 0.0,
                "end_fraction": 0.40,
                "mean_snr_db": 6.0,
                "shadowing_std_db": 3.0,
                "effective_speed_m_s": 0.0,
                "critical_message_probability": 0.05,
                "mallory_attempt_probability": 0.15,
                "criticality_forced": None,
                "compromise_suspected_forced": False
            },
            {
                "phase_name": (
                    "Alarme critique "
                    "(apparition et maintien)"
                ),
                "start_fraction": 0.40,
                "end_fraction": 0.50,
                "mean_snr_db": 6.0,
                "shadowing_std_db": 3.0,
                "effective_speed_m_s": 0.0,
                "critical_message_probability": 1.0,
                "mallory_attempt_probability": 0.15,
                # Criticité forcée à 1 : chaque période de
                # cette phase transporte un message urgent
                # dont le budget de latence critique
                # s'applique (parameters.
                # critical_latency_budget_s /
                # critical_far_limit).
                "criticality_forced": 1,
                "compromise_suspected_forced": False
            },
            {
                "phase_name": "Récupération progressive",
                "start_fraction": 0.50,
                "end_fraction": 1.0,
                "mean_snr_db": 6.0,
                "shadowing_std_db": 3.0,
                "effective_speed_m_s": 0.0,
                "critical_message_probability": 0.05,
                "mallory_attempt_probability": 0.15,
                "criticality_forced": None,
                "compromise_suspected_forced": False
            }
        ],

        "variation_feasible": True,

        "parameters_held_constant": [
            "mean_snr_db (6.0 dB) et shadowing_std_db "
            "(3.0 dB) — l'alarme ne change pas la "
            "qualité du canal, seulement la criticité "
            "et le budget de latence associé",
            "effective_speed_m_s = 0.0 — nœud fixe",
            "cryptopériode nominale, profil de coût "
            "CENTRAL"
        ],

        "parameters_allowed_to_change": [
            "criticality (forcée à 1 pendant l'alarme, "
            "tirée aléatoirement sinon)",
            "battery_energy_j, key_age_s, "
            "messages_with_current_key, compteurs K1"
        ],

        "success_criteria": [
            "Messages de la phase d'alarme servis avant "
            "l'échéance (authentication_latency_s "
            "<= critical_latency_budget_s pour la "
            "décision sélectionnée).",
            "Taux de refus légitime faible pendant "
            "l'urgence.",
            "Aucune violation du plancher de sécurité "
            "(security_floor_violation) pendant "
            "l'alarme, où le plancher critique "
            "(critical_far_limit) est plus strict."
        ],

        "validity_limits": [
            "Le déclenchement de l'alarme est un "
            "changement de CONTEXTE (criticité forcée), "
            "pas un changement du canal radio lui-même : "
            "ce scénario isole donc l'effet de la "
            "criticité sur la décision, indépendamment "
            "de toute dégradation PHY (voir S3/S4 pour "
            "cet aspect)."
        ],

        "k2_protocol": None,

        "parameter_overrides": {
            "mean_snr_db": 6.0,
            "shadowing_std_db": 3.0,
            "critical_message_probability": 0.05,
            "mallory_attempt_probability": 0.15,
            "effective_speed_m_s": 0.0
        }
    }


# ================================================================
# 4. CAS D'ÉTUDE S3 — OBJET MOBILE SUR VÉHICULE
# ================================================================
#
# Le profil de vitesse a été choisi après vérification numérique
# directe avec physec_dm.channel.calculate_channel_metrics
# (aucune équation modifiée) :
#
#   v=0    km/h  rho_time=1.000   rho_ab=0.871  KDR_eff=0.163
#          (agreement_feasible=True)
#   v=0.2  km/h  rho_time=0.760   rho_ab=0.663  KDR_eff=0.270
#          (agreement_feasible=True)
#   v=0.5  km/h  rho_time=-0.062  rho_ab=-0.054 KDR_eff=0.517
#          (agreement_feasible=False)
#   v>=1   km/h  KDR_eff proche de 0.5 (agreement_feasible=False)
#
# Avec probe_delay_s=1.0 s (paramètre nominal du projet) et une
# porteuse à 868 MHz, l'argument de la fonction de Bessel J0
# franchit son premier zéro dès quelques dixièmes de km/h : le
# modèle prédit donc une décorrélation quasi immédiate dès que
# le véhicule roule, bien avant d'atteindre une vitesse routière.
# Ce n'est pas un artefact du scénario : c'est une conséquence
# directe et vérifiable des équations CH-EQ existantes. Le
# profil ci-dessous (véhicule de maintenance, vitesse maximale
# 30 km/h) est choisi pour rester réaliste tout en manifestant
# cet effet, documenté explicitement dans validity_limits.
def build_case_study_s3():

    max_speed_kmh = 30.0
    max_speed_m_s = max_speed_kmh / 3.6

    return {
        "scenario_id": "S3-MOBILE-VEHICLE",

        "scenario_name": (
            "Objet mobile sur véhicule de maintenance"
        ),

        "case_study_description": (
            "Un capteur est installé sur un véhicule de "
            "maintenance qui effectue une tournée : "
            "arrêt initial, accélération, déplacement à "
            "vitesse constante, ralentissement, arrêt "
            "final. L'objectif est d'observer comment la "
            "mobilité affecte la réciprocité du canal "
            "(donc la faisabilité de K1a/K1b), et comment "
            "le Decision Maker s'adapte."
        ),

        "system_under_test": (
            "Nœud LoRa embarqué sur véhicule, même chaîne "
            "de décision qu'en S1/S2."
        ),

        "environment_description": (
            "Trajet routier local (site industriel ou "
            "rural), SNR moyen modéré, vitesse maximale "
            "de "
            + str(max_speed_kmh)
            + " km/h (véhicule de maintenance, pas "
            "autoroutier)."
        ),

        "mission_description": (
            "Cinq phases : arrêt, accélération, vitesse "
            "maximale du scénario, ralentissement, arrêt."
        ),

        "scientific_question": (
            "Le Decision Maker adapte-t-il "
            "l'authentification et les mécanismes K1 "
            "lorsque la mobilité modifie la réciprocité "
            "du canal (rho_AB), telle que réellement "
            "calculée par channel.py ?"
        ),

        "phases": [
            {
                "phase_name": "Véhicule à l'arrêt (départ)",
                "start_fraction": 0.0,
                "end_fraction": 0.20,
                "mean_snr_db": 10.0,
                "shadowing_std_db": 2.0,
                "effective_speed_m_s": 0.0,
                "critical_message_probability": 0.05,
                "mallory_attempt_probability": 0.10,
                "criticality_forced": None,
                "compromise_suspected_forced": False
            },
            {
                "phase_name": "Accélération",
                "start_fraction": 0.20,
                "end_fraction": 0.40,
                "mean_snr_db": 10.0,
                "shadowing_std_db": 2.0,
                # Rampe linéaire 0 -> vitesse maximale,
                # interpolée période par période par
                # scenario_controller.py.
                "effective_speed_m_s": (
                    "ramp",
                    0.0,
                    max_speed_m_s
                ),
                "critical_message_probability": 0.05,
                "mallory_attempt_probability": 0.10,
                "criticality_forced": None,
                "compromise_suspected_forced": False
            },
            {
                "phase_name": (
                    "Déplacement à vitesse maximale du "
                    "scénario ("
                    + str(max_speed_kmh)
                    + " km/h)"
                ),
                "start_fraction": 0.40,
                "end_fraction": 0.60,
                "mean_snr_db": 9.0,
                "shadowing_std_db": 2.5,
                "effective_speed_m_s": max_speed_m_s,
                "critical_message_probability": 0.05,
                "mallory_attempt_probability": 0.10,
                "criticality_forced": None,
                "compromise_suspected_forced": False
            },
            {
                "phase_name": "Ralentissement",
                "start_fraction": 0.60,
                "end_fraction": 0.80,
                "mean_snr_db": 10.0,
                "shadowing_std_db": 2.0,
                "effective_speed_m_s": (
                    "ramp",
                    max_speed_m_s,
                    0.0
                ),
                "critical_message_probability": 0.05,
                "mallory_attempt_probability": 0.10,
                "criticality_forced": None,
                "compromise_suspected_forced": False
            },
            {
                "phase_name": "Véhicule à l'arrêt (arrivée)",
                "start_fraction": 0.80,
                "end_fraction": 1.0,
                "mean_snr_db": 10.0,
                "shadowing_std_db": 2.0,
                "effective_speed_m_s": 0.0,
                "critical_message_probability": 0.05,
                "mallory_attempt_probability": 0.10,
                "criticality_forced": None,
                "compromise_suspected_forced": False
            }
        ],

        "variation_feasible": True,

        "parameters_held_constant": [
            "critical_message_probability (0.05) et "
            "mallory_attempt_probability (0.10) sur "
            "toute la mission",
            "cryptopériode nominale, profil de coût "
            "CENTRAL"
        ],

        "parameters_allowed_to_change": [
            "effective_speed_m_s (0 -> "
            + str(max_speed_kmh)
            + " km/h -> 0, par rampes linéaires)",
            "mean_snr_db, shadowing_std_db (légèrement "
            "réduits en phase de vitesse maximale, "
            "cohérent avec un trajet en extérieur "
            "dégagé)",
            "doppler_hz, rho_time, rho_ab, KDR effectif "
            "(conséquences calculées, pas fixées)"
        ],

        "success_criteria": [
            "Décisions différentes observées entre les "
            "phases immobiles et les phases mobiles "
            "(le choix du Decision Maker suit la "
            "faisabilité PHY réelle).",
            "Progression de k1a/k1b_measurements_collected "
            "pendant les phases à l'arrêt, lorsque la "
            "PHY est faisable.",
            "Repli sur A1/A2 + K0/K2 pendant les phases "
            "mobiles si K1a/K1b deviennent PHY-infaisables "
            "(observé, pas imposé)."
        ],

        "validity_limits": [
            "Avec probe_delay_s=1.0 s et une porteuse à "
            "868 MHz, le modèle prédit une "
            "décorrélation quasi immédiate dès que "
            "v > 0 (voir calcul en tête de fonction) : "
            "K1a/K1b sont donc attendues PHY-infaisables "
            "pendant les quatre phases non nulles, et "
            "seules les phases à l'arrêt (0 % à 20 % "
            "et 80 % à 100 %) permettent une "
            "progression K1. Ce résultat n'est pas "
            "imposé par le scénario : il découle du "
            "calcul réel de rho_time/rho_AB et doit être "
            "vérifié, pas supposé, dans les résultats."
        ],

        "k2_protocol": None,

        "parameter_overrides": {
            "mean_snr_db": 10.0,
            "shadowing_std_db": 2.0,
            "critical_message_probability": 0.05,
            "mallory_attempt_probability": 0.10,
            "effective_speed_m_s": 0.0
        }
    }


# ================================================================
# 5. CAS D'ÉTUDE S4 — RÉSEAU URBAIN DENSE
# ================================================================


def build_case_study_s4():

    return {
        "scenario_id": "S4-DENSE-URBAN-NETWORK",

        "scenario_name": (
            "Réseau urbain dense"
        ),

        "case_study_description": (
            "Un objet communique dans une zone urbaine "
            "dense (bâtiments, multi-trajets, "
            "interférences). Le scénario alterne des "
            "périodes de charge radio normale et des "
            "périodes de congestion, où le canal devient "
            "plus difficile et où les sondages dédiés "
            "K1b deviennent relativement plus coûteux."
        ),

        "system_under_test": (
            "Nœud LoRa fixe en environnement urbain, "
            "même chaîne de décision qu'en S1/S2/S3."
        ),

        "environment_description": (
            "Zone urbaine : SNR moyen plus faible "
            "qu'en zone rurale, shadowing important, "
            "aggravé pendant les congestions. La charge "
            "radio de fond est représentée par un "
            "shadowing accru et une pression d'attaque "
            "opportuniste plus élevée pendant la "
            "congestion — PAS par une consommation "
            "directe du budget de duty-cycle "
            "d'Alice par du trafic tiers, notion absente "
            "du modèle validé (voir validity_limits)."
        ),

        "mission_description": (
            "Cinq phases : charge normale, congestion, "
            "retour normal, deuxième congestion, retour "
            "normal."
        ),

        "scientific_question": (
            "Le Decision Maker privilégie-t-il K1a "
            "(opportuniste, sans coût radio "
            "incrémental) et limite-t-il K1b (sondages "
            "dédiés, coût radio réel) lorsque le canal "
            "devient plus difficile pendant la "
            "congestion ?"
        ),

        "phases": [
            {
                "phase_name": "Charge normale",
                "start_fraction": 0.0,
                "end_fraction": 0.25,
                "mean_snr_db": 3.0,
                "shadowing_std_db": 4.0,
                "effective_speed_m_s": 0.0,
                "critical_message_probability": 0.05,
                "mallory_attempt_probability": 0.20,
                "criticality_forced": None,
                "compromise_suspected_forced": False
            },
            {
                "phase_name": "Congestion (1)",
                "start_fraction": 0.25,
                "end_fraction": 0.40,
                "mean_snr_db": 3.0,
                "shadowing_std_db": 7.0,
                "effective_speed_m_s": 0.0,
                "critical_message_probability": 0.05,
                "mallory_attempt_probability": 0.30,
                "criticality_forced": None,
                "compromise_suspected_forced": False
            },
            {
                "phase_name": "Retour normal (1)",
                "start_fraction": 0.40,
                "end_fraction": 0.65,
                "mean_snr_db": 3.0,
                "shadowing_std_db": 4.0,
                "effective_speed_m_s": 0.0,
                "critical_message_probability": 0.05,
                "mallory_attempt_probability": 0.20,
                "criticality_forced": None,
                "compromise_suspected_forced": False
            },
            {
                "phase_name": "Congestion (2)",
                "start_fraction": 0.65,
                "end_fraction": 0.80,
                "mean_snr_db": 3.0,
                "shadowing_std_db": 7.0,
                "effective_speed_m_s": 0.0,
                "critical_message_probability": 0.05,
                "mallory_attempt_probability": 0.30,
                "criticality_forced": None,
                "compromise_suspected_forced": False
            },
            {
                "phase_name": "Retour normal (2)",
                "start_fraction": 0.80,
                "end_fraction": 1.0,
                "mean_snr_db": 3.0,
                "shadowing_std_db": 4.0,
                "effective_speed_m_s": 0.0,
                "critical_message_probability": 0.05,
                "mallory_attempt_probability": 0.20,
                "criticality_forced": None,
                "compromise_suspected_forced": False
            }
        ],

        "variation_feasible": True,

        "parameters_held_constant": [
            "mean_snr_db (3.0 dB) — seule la variabilité "
            "(shadowing_std_db) augmente pendant la "
            "congestion, pas le SNR moyen",
            "effective_speed_m_s = 0.0 — nœud fixe",
            "cryptopériode nominale, profil de coût "
            "CENTRAL"
        ],

        "parameters_allowed_to_change": [
            "shadowing_std_db (4.0 dB en charge normale, "
            "7.0 dB en congestion)",
            "mallory_attempt_probability (0.20 en charge "
            "normale, 0.30 en congestion — pression "
            "opportuniste accrue par la densité)"
        ],

        "success_criteria": [
            "Le budget de duty-cycle n'est jamais "
            "dépassé (remaining_duty_cycle_airtime_s "
            ">= 0 à chaque période, contrainte déjà "
            "garantie par DM-EQ101).",
            "Les sondages K1b (k1b_measurements_collected) "
            "progressent moins vite, en proportion, "
            "pendant la congestion qu'en charge normale "
            "(le canal plus difficile réduit la fenêtre "
            "où variation_feasible/agreement_feasible "
            "restent vrais).",
            "Le service reste globalement assuré "
            "(taux de refus légitime limité) malgré la "
            "dégradation."
        ],

        "validity_limits": [
            "Le modèle validé ne représente pas "
            "explicitement une consommation du budget "
            "de duty-cycle d'Alice par du trafic tiers "
            "(les autres émetteurs de la zone dense ne "
            "sont pas simulés individuellement) : la "
            "congestion est donc représentée uniquement "
            "par des mécanismes déjà validés (shadowing, "
            "probabilité d'attaque), pas par une nouvelle "
            "équation de partage de canal."
        ],

        "k2_protocol": None,

        "parameter_overrides": {
            "mean_snr_db": 3.0,
            "shadowing_std_db": 4.0,
            "critical_message_probability": 0.05,
            "mallory_attempt_probability": 0.20,
            "effective_speed_m_s": 0.0
        }
    }


# ================================================================
# 6. CAS D'ÉTUDE S5 — INFRASTRUCTURE CRITIQUE SOUS ATTAQUE
# ================================================================


def build_case_study_s5():

    return {
        "scenario_id": (
            "S5-CRITICAL-INFRASTRUCTURE-ATTACK"
        ),

        "scenario_name": (
            "Infrastructure critique sous attaque"
        ),

        "case_study_description": (
            "Un objet surveille une infrastructure "
            "sensible (par exemple, un poste électrique "
            "ou une station de pompage). Le trafic est "
            "normal, puis la pression d'attaque augmente "
            "fortement ; une suspicion de compromission "
            "de clé survient en cours d'attaque. Le "
            "système doit réagir puis revenir "
            "progressivement à la normale."
        ),

        "system_under_test": (
            "Nœud LoRa fixe protégeant une "
            "infrastructure sensible, même chaîne de "
            "décision qu'en S1/S2/S3/S4."
        ),

        "environment_description": (
            "Lien radio de bonne qualité (infrastructure "
            "protégée, installation soignée), pression "
            "d'attaque variable dans le temps."
        ),

        "mission_description": (
            "Quatre segments temporels : fonctionnement "
            "normal, attaque renforcée (avec un "
            "événement de suspicion de compromission au "
            "milieu de cette phase), réaction et retour "
            "progressif à la normale."
        ),

        "scientific_question": (
            "Le Decision Maker renforce-t-il "
            "l'authentification et renouvelle-t-il la "
            "clé avant expiration ou compromission, tout "
            "en maintenant une énergie et une latence "
            "acceptables ?"
        ),

        "phases": [
            {
                "phase_name": "Fonctionnement normal",
                "start_fraction": 0.0,
                "end_fraction": 0.30,
                "mean_snr_db": 12.0,
                "shadowing_std_db": 2.0,
                "effective_speed_m_s": 0.0,
                "critical_message_probability": 0.10,
                "mallory_attempt_probability": 0.10,
                "criticality_forced": None,
                "compromise_suspected_forced": False
            },
            {
                "phase_name": (
                    "Attaque renforcée "
                    "(avec suspicion de compromission "
                    "à mi-phase)"
                ),
                "start_fraction": 0.30,
                "end_fraction": 0.60,
                "mean_snr_db": 12.0,
                "shadowing_std_db": 2.0,
                "effective_speed_m_s": 0.0,
                "critical_message_probability": 0.10,
                "mallory_attempt_probability": 0.50,
                "criticality_forced": None,
                # La suspicion de compromission est un
                # événement ponctuel à 45 % de la
                # mission (soit le milieu de cette
                # phase, qui couvre 30 % à 60 %) : traité
                # comme un événement de scénario, pas
                # comme un attribut de phase uniforme
                # (voir scenario_events ci-dessous).
                "compromise_suspected_forced": False
            },
            {
                "phase_name": (
                    "Réaction et retour progressif "
                    "à la normale"
                ),
                "start_fraction": 0.60,
                "end_fraction": 1.0,
                "mean_snr_db": 12.0,
                "shadowing_std_db": 2.0,
                "effective_speed_m_s": 0.0,
                "critical_message_probability": 0.10,
                "mallory_attempt_probability": 0.15,
                "criticality_forced": None,
                "compromise_suspected_forced": False
            }
        ],

        # Événements ponctuels du scénario, distincts des
        # phases : ils s'appliquent à une fraction précise
        # de la mission plutôt qu'à un intervalle.
        "scenario_events": [
            {
                "event_name": (
                    "COMPROMISE_SUSPECTED"
                ),
                "at_fraction": 0.45,
                "effect": "compromise_suspected",
                # La suspicion reste active jusqu'au
                # début de la phase de réaction (60 %),
                # où elle est levée (retour progressif à
                # la normale).
                "clears_at_fraction": 0.60
            }
        ],

        "variation_feasible": True,

        "parameters_held_constant": [
            "mean_snr_db (12.0 dB) et shadowing_std_db "
            "(2.0 dB) — seule la pression d'attaque "
            "varie, pas la qualité du canal",
            "effective_speed_m_s = 0.0 — nœud fixe",
            "cryptopériode nominale, profil de coût "
            "CENTRAL"
        ],

        "parameters_allowed_to_change": [
            "mallory_attempt_probability (0.10 -> 0.50 "
            "-> 0.15)",
            "compromise_suspected (False -> True à "
            "45 % -> False à 60 %)"
        ],

        "success_criteria": [
            "FAR empirique sous le plancher critique "
            "pendant toute l'attaque.",
            "Aucune violation du plancher de sécurité "
            "(security_floor_violation).",
            "Un renouvellement de clé (K1a, K1b ou K2) "
            "est observé en temps utile après "
            "l'événement de compromission suspectée "
            "(key_expired impose renewal_required=True "
            "dès que compromise_suspected=True, cf. "
            "key_generation.calculate_key_expired)."
        ],

        "validity_limits": [
            "L'événement de compromission est modélisé "
            "via compromise_suspected=True, qui force "
            "key_expired=True (mécanisme déjà validé de "
            "key_generation.py) : ce scénario n'invente "
            "aucun nouveau mécanisme de compromission, "
            "il active un signal déjà prévu par le "
            "modèle."
        ],

        "k2_protocol": None,

        "parameter_overrides": {
            "mean_snr_db": 12.0,
            "shadowing_std_db": 2.0,
            "critical_message_probability": 0.10,
            "mallory_attempt_probability": 0.10,
            "effective_speed_m_s": 0.0
        }
    }


# ================================================================
# 7. CONSTRUCTION DE L'ENSEMBLE DES CINQ CAS D'ÉTUDE
# ================================================================


def build_five_case_studies():

    base_parameters = build_case_study_base_parameters()

    builders = [
        build_case_study_s1,
        build_case_study_s2,
        build_case_study_s3,
        build_case_study_s4,
        build_case_study_s5
    ]

    case_studies = []

    for builder in builders:

        case_study = builder()

        case_study["k2_protocol"] = (
            build_exploratory_k2_protocol(
                base_parameters
            )
        )

        case_studies.append(case_study)

    return case_studies


# ================================================================
# 7bis. CAS D'ÉTUDE SUPPLÉMENTAIRE S6 — COLLECTE PAR DRONE
# ================================================================
#
# Ce sixième cas d'étude est ADDITIF : il ne modifie ni
# CASE_STUDY_IDS, ni build_five_case_studies(), ni aucun des cinq
# cas d'étude S1-S5 déjà simulés et vérifiés. Il répond à la
# demande d'un scénario plus réaliste et comparable à la
# littérature (Ardizzon et al. 2024 ; Kawoya & Wang 2025) : un
# capteur fixe visité périodiquement par un drone collecteur.
#
# CE QUI N'EST PAS SIMULÉ, pour rester honnête : la position du
# drone, sa trajectoire ou l'énergie qu'il dépense à voler. Seul
# l'effet sur le canal radio du capteur (Alice) est reproduit :
# une connexion de bonne qualité, mais brève et très mobile,
# alternant avec de longues périodes sans lien exploitable quand
# le drone est hors de portée. Le Decision Maker (P0) ne pilote
# pas le drone ; il décide uniquement de l'authentification et de
# la gestion de clé du capteur, exactement comme dans S1-S5.
CASE_STUDY_S6_ID = "S6-UAV-ASSISTED-COLLECTION"


def build_case_study_s6():

    return {
        "scenario_id": CASE_STUDY_S6_ID,

        "scenario_name": (
            "Collecte de données par drone"
        ),

        "case_study_description": (
            "Un capteur LoRa fixe (même contexte physique "
            "que S1) est visité périodiquement par un "
            "drone qui vient récupérer ses données "
            "— agriculture de précision ou inspection "
            "d'infrastructure. La majeure partie du temps, "
            "le drone est hors de portée et le lien radio "
            "est très dégradé. Lors de chaque passage, le "
            "lien redevient bon mais très bref et "
            "fortement mobile (grande vitesse relative "
            "entre le drone et le capteur), ce qui crée "
            "une fenêtre de collecte sous pression."
        ),

        "system_under_test": (
            "Nœud LoRa fixe (Alice), même chaîne de "
            "décision qu'en S1-S5. Le drone n'est pas un "
            "agent piloté par le Decision Maker : il "
            "n'est représenté que par son effet sur le "
            "canal radio d'Alice (qualité, mobilité "
            "relative)."
        ),

        "environment_description": (
            "Zone rurale ou industrielle dégagée, comme "
            "S1. Contrairement à S1, le lien alterne "
            "entre deux régimes très différents : absence "
            "quasi totale de lien exploitable (drone "
            "loin) et lien de bonne qualité mais très "
            "instable (drone proche, survol rapide)."
        ),

        "mission_description": (
            "Trois cycles complets silence/passage : le "
            "drone effectue trois tournées de collecte "
            "au cours de la mission. Chaque passage est "
            "court par rapport au silence qui l'entoure, "
            "conformément au problème réel de fenêtre de "
            "connectivité courte identifié par Kawoya & "
            "Wang (2025) et Ardizzon et al. (2024)."
        ),

        "scientific_question": (
            "Le Decision Maker sait-il gérer une "
            "connectivité qui apparaît et disparaît "
            "brutalement, plus extrême que la mobilité "
            "progressive de S3, sans dégrader le service "
            "ni la sécurité pendant les fenêtres de "
            "passage ?"
        ),

        "phases": [
            {
                "phase_name": "Silence 1 (drone hors de portée)",
                "start_fraction": 0.00,
                "end_fraction": 0.20,
                "mean_snr_db": 0.0,
                "shadowing_std_db": 6.0,
                "effective_speed_m_s": 0.0,
                "critical_message_probability": 0.05,
                "mallory_attempt_probability": 0.10,
                "criticality_forced": None,
                "compromise_suspected_forced": False
            },
            {
                "phase_name": "Passage du drone 1 (fenêtre de collecte)",
                "start_fraction": 0.20,
                "end_fraction": 0.31,
                "mean_snr_db": 11.0,
                "shadowing_std_db": 1.5,
                "effective_speed_m_s": 12.0,
                "critical_message_probability": 0.30,
                "mallory_attempt_probability": 0.20,
                "criticality_forced": None,
                "compromise_suspected_forced": False
            },
            {
                "phase_name": "Silence 2 (drone hors de portée)",
                "start_fraction": 0.31,
                "end_fraction": 0.53,
                "mean_snr_db": 0.0,
                "shadowing_std_db": 6.0,
                "effective_speed_m_s": 0.0,
                "critical_message_probability": 0.05,
                "mallory_attempt_probability": 0.10,
                "criticality_forced": None,
                "compromise_suspected_forced": False
            },
            {
                "phase_name": "Passage du drone 2 (fenêtre de collecte)",
                "start_fraction": 0.53,
                "end_fraction": 0.64,
                "mean_snr_db": 11.0,
                "shadowing_std_db": 1.5,
                "effective_speed_m_s": 12.0,
                "critical_message_probability": 0.30,
                "mallory_attempt_probability": 0.20,
                "criticality_forced": None,
                "compromise_suspected_forced": False
            },
            {
                "phase_name": "Silence 3 (drone hors de portée)",
                "start_fraction": 0.64,
                "end_fraction": 0.89,
                "mean_snr_db": 0.0,
                "shadowing_std_db": 6.0,
                "effective_speed_m_s": 0.0,
                "critical_message_probability": 0.05,
                "mallory_attempt_probability": 0.10,
                "criticality_forced": None,
                "compromise_suspected_forced": False
            },
            {
                "phase_name": "Passage du drone 3 (fenêtre de collecte)",
                "start_fraction": 0.89,
                "end_fraction": 1.00,
                "mean_snr_db": 11.0,
                "shadowing_std_db": 1.5,
                "effective_speed_m_s": 12.0,
                "critical_message_probability": 0.30,
                "mallory_attempt_probability": 0.20,
                "criticality_forced": None,
                "compromise_suspected_forced": False
            }
        ],

        "variation_feasible": True,

        "parameters_held_constant": [
            "profil de coût CENTRAL, cryptopériode "
            "nominale — comme S1-S5"
        ],

        "parameters_allowed_to_change": [
            "mean_snr_db (0.0 dB en silence -> 11.0 dB "
            "en passage)",
            "shadowing_std_db (6.0 dB en silence -> "
            "1.5 dB en passage)",
            "effective_speed_m_s (0.0 -> 12.0 m/s en "
            "passage, ordre de grandeur d'un survol de "
            "collecte, cf. Ardizzon et al. 2024 ; "
            "Kawoya & Wang 2025 — ni l'un ni l'autre ne "
            "publie de vitesse de croisière exacte "
            "reprise ici telle quelle)",
            "critical_message_probability (0.05 -> 0.30 "
            "en passage)",
            "mallory_attempt_probability (0.10 -> 0.20 "
            "en passage, cohérent avec la fenêtre de "
            "vulnérabilité identifiée par Ardizzon et "
            "al. 2024)"
        ],

        "success_criteria": [
            "Service et sécurité maintenus pendant les "
            "trois fenêtres de passage malgré la brièveté "
            "et l'instabilité du lien.",
            "Comportement du Decision Maker différent "
            "entre silence et passage (observé, pas "
            "imposé)."
        ],

        "validity_limits": [
            "Ce scénario NE simule PAS la position, la "
            "trajectoire ni l'énergie de déplacement du "
            "drone : seul l'effet sur le canal d'Alice "
            "est reproduit (voir note en tête de "
            "section). Toute comparaison à la "
            "littérature drone se limite donc au contexte "
            "radio et à la menace, jamais à l'énergie de "
            "vol.",
            "Comme en S3, le modèle prédit qu'une "
            "vitesse relative non nulle "
            "(effective_speed_m_s=12.0 pendant les "
            "passages) décorrèle le canal très "
            "rapidement avec probe_delay_s=1.0 s à "
            "868 MHz : K1a/K1b sont donc probablement "
            "PHY-infaisables pendant les passages. Ce "
            "n'est pas imposé par le scénario, mais un "
            "résultat à vérifier dans les données, "
            "exactement comme en S3.",
            "Les valeurs de SNR/shadowing des deux "
            "régimes (silence/passage) sont construites "
            "pour représenter \"drone absent\" vs \"drone "
            "proche\", pas mesurées depuis un article "
            "précis : à présenter comme telles."
        ],

        "k2_protocol": None,

        "parameter_overrides": {
            "mean_snr_db": 0.0,
            "shadowing_std_db": 6.0,
            "critical_message_probability": 0.05,
            "mallory_attempt_probability": 0.10,
            "effective_speed_m_s": 0.0
        }
    }


def build_case_study_s6_only():

    base_parameters = build_case_study_base_parameters()

    case_study = build_case_study_s6()

    case_study["k2_protocol"] = (
        build_exploratory_k2_protocol(
            base_parameters
        )
    )

    return [case_study]


# ================================================================
# 7ter. VERSION COMPLEXIFIÉE DE S1-S5 (à la demande explicite de
# l'encadrante : complexifier S1-S5 eux-mêmes, pas ajouter un
# sixième cas d'étude à côté)
# ================================================================
#
# Deux leviers sont utilisés, tous deux déjà présents et validés
# ailleurs dans le dépôt — AUCUNE valeur n'est inventée ici :
#
# - mallory_separation (d_M) : le document de modélisation
#   (docs/modelisation/modelisation_parametres_modifies.tex,
#   ligne ~1520) fixe explicitement 2,0 comme "valeur centrale
#   conservée pour le balayage normalisé [0,5 ; 5] ; aucun auteur
#   ne fixe une valeur universelle", et rend obligatoire une
#   analyse de sensibilité sur ce paramètre (jamais faite jusqu'ici
#   dans la campagne S1-S5). Les valeurs utilisées ci-dessous
#   restent strictement dans cette plage déjà validée.
#
# - cost_profile_id (LOW/CENTRAL/HIGH) : profils déjà codés dans
#   physec_dm/scientific_config.py
#   (build_exploratory_cost_profiles), documentés dans leur propre
#   commentaire comme "des scénarios de sensibilité, pas des
#   constantes de littérature" (LOW ~= moitié de CENTRAL, HIGH ~=
#   double de CENTRAL). Utilisés ici tels quels, sans modification,
#   et présentés dans l'article comme des variantes de sensibilité
#   au coût matériel, jamais comme du matériel réel documenté.
#
# Un troisième levier envisagé (real_snr_bias_db, biais de
# calibration) a été explicitement écarté : aucune source, ni dans
# le document de modélisation ni dans le code, ne le justifie.
#
# Ces fonctions sont ADDITIVES : build_case_study_s1() à
# build_case_study_s5() et build_five_case_studies() restent
# strictement inchangés et continuent de produire exactement les
# mêmes cas d'étude qu'avant (résultats déjà vérifiés préservés).
from physec_dm.scientific_config import (
    build_exploratory_cost_profiles
)


SCENARIO_V2_MALLORY_SEPARATION = {
    "S1-REMOTE-AGRICULTURAL-SENSOR": 4.0,
    "S2-INDUSTRIAL-CRITICAL-ALARM": 2.0,
    "S3-MOBILE-VEHICLE": 2.0,
    "S4-DENSE-URBAN-NETWORK": 1.0,
    "S5-CRITICAL-INFRASTRUCTURE-ATTACK": 0.5
}

SCENARIO_V2_COST_PROFILE = {
    "S1-REMOTE-AGRICULTURAL-SENSOR": "LOW",
    "S2-INDUSTRIAL-CRITICAL-ALARM": "HIGH",
    "S3-MOBILE-VEHICLE": "CENTRAL",
    "S4-DENSE-URBAN-NETWORK": "CENTRAL",
    "S5-CRITICAL-INFRASTRUCTURE-ATTACK": "HIGH"
}


def apply_v2_complexity_overrides(case_study):

    scenario_id = case_study["scenario_id"]

    complex_case_study = copy.deepcopy(case_study)

    overrides = complex_case_study["parameter_overrides"]

    overrides["mallory_separation"] = (
        SCENARIO_V2_MALLORY_SEPARATION[scenario_id]
    )

    cost_profile_id = SCENARIO_V2_COST_PROFILE[scenario_id]

    cost_profile_values = build_exploratory_cost_profiles()[
        cost_profile_id
    ]

    for parameter_name, value in cost_profile_values.items():

        overrides[parameter_name] = value

    complex_case_study["v2_cost_profile_id"] = cost_profile_id

    complex_case_study["v2_mallory_separation"] = (
        SCENARIO_V2_MALLORY_SEPARATION[scenario_id]
    )

    return complex_case_study


def build_five_case_studies_v2():

    base_parameters = build_case_study_base_parameters()

    builders = [
        build_case_study_s1,
        build_case_study_s2,
        build_case_study_s3,
        build_case_study_s4,
        build_case_study_s5
    ]

    case_studies = []

    for builder in builders:

        case_study = apply_v2_complexity_overrides(
            builder()
        )

        case_study["k2_protocol"] = (
            build_exploratory_k2_protocol(
                base_parameters
            )
        )

        case_studies.append(case_study)

    return case_studies


# ================================================================
# 8. BASELINE B1-CONVENTIONAL
# ================================================================
#
# La baseline n'est pas un sixième cas d'étude : c'est une
# POLITIQUE alternative, comparée au Decision Maker P0 dans les
# cinq mêmes cas d'étude, avec les mêmes traces aléatoires
# communes (voir scenario_controller.py, section 5 du protocole).
def build_baseline_policy_definition():

    return {
        "policy_id": "B1-CONVENTIONAL",
        "description": (
            "Authentification et renouvellement "
            "conventionnels : A1 systématique, K0 tant "
            "que la clé reste valide, K2 lorsqu'un "
            "renouvellement est requis. N'utilise jamais "
            "K1a, K1b ni A2."
        )
    }


# Cette fonction implémente la politique B1-CONVENTIONAL.
#
# Elle NE crée PAS un second Decision Maker : elle réutilise
# evaluate_decision() de physec_dm/decision_maker.py — les mêmes
# règles logiques (DM-EQ94 à DM-EQ96), les mêmes contraintes
# (DM-EQ97 à DM-EQ102) et le même vecteur d'objectifs
# (DM-EQ93) que P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS. Seule la SÉLECTION diffère :
# B1 ne considère jamais que deux candidats fixes (A1-K0,
# A1-K2), choisis par une règle déterministe simple plutôt que
# par le front de Pareto et la scalarisation de Tchebycheff
# (DM-EQ103 à DM-EQ106), qui restent réservés à P0.
#
# Signature compatible avec run_decision_maker (mêmes arguments,
# retourne un DecisionMakerResult) afin de pouvoir être branchée
# telle quelle via mission.run_mission_step(...,
# decision_policy_fn=select_baseline_conventional_decision).
def select_baseline_conventional_decision(
    context,
    parameters,
    rho_ab,
    variation_feasible=None,
    k2_protocol=None,
    contextual_weights=None
):

    # B1-CONVENTIONAL n'arbitre jamais par Tchebycheff : le
    # paramètre contextual_weights n'est accepté que pour
    # partager la même signature d'appel que
    # run_decision_maker (voir mission.run_mission_step,
    # decision_policy_fn) et n'est jamais utilisé.
    del contextual_weights

    # Même règle que DM-EQ95/DM-EQ96 : K0 tant que le
    # renouvellement n'est pas requis, K2 dès qu'il l'est.
    if context.renewal_required:

        candidate_key_action = KeyAction.K2

    else:

        candidate_key_action = KeyAction.K0

    decision = Decision(
        AuthenticationAction.A1,
        candidate_key_action
    )

    evaluation = evaluate_decision(
        decision=decision,
        context=context,
        parameters=parameters,
        rho_ab=rho_ab,
        variation_feasible=variation_feasible,
        k2_protocol=k2_protocol
    )

    if evaluation.admissible:

        selected_evaluation = evaluation
        refusal_of_service = False
        fallback_mode_used = None

        explanation = (
            "B1-CONVENTIONAL : "
            + decision.get_name()
            + " est admissible et sélectionnée "
            "(règle fixe, sans Pareto ni Tchebycheff)."
        )

    else:

        selected_evaluation = None
        refusal_of_service = True
        fallback_mode_used = "B1-CONVENTIONAL"

        explanation = (
            "B1-CONVENTIONAL : "
            + decision.get_name()
            + " n'est pas admissible ; la politique "
            "n'essaie aucune alternative (A2, K1a et "
            "K1b sont exclus par construction)."
        )

    return DecisionMakerResult(
        context=context,
        all_evaluations=[evaluation],
        admissible_evaluations=(
            [evaluation]
            if evaluation.admissible
            else []
        ),
        pareto_front=(
            [evaluation]
            if evaluation.admissible
            else []
        ),
        rejection_journal=list(
            evaluation.rejection_reasons
        ),
        contextual_weights=None,
        ideal_point=None,
        nadir_point=None,
        selected_evaluation=selected_evaluation,
        refusal_of_service=refusal_of_service,
        fallback_mode_used=fallback_mode_used,
        explanation=explanation
    )


# ================================================================
# B2 : PHYSEC NAÏVE, SANS PLANCHER DE FAR
# ================================================================
#
# Politique de référence exigée par le protocole (Étape 4) pour
# isoler l'effet du plancher de sécurité DM-EQ102 combiné à une
# règle naïve : contrairement à P0, B2 n'évalue pas les huit
# décisions par Pareto/Tchebycheff. Elle essaie, dans un ORDRE DE
# PRÉFÉRENCE FIXE privilégiant la couche physique, la première
# décision qui se révèle admissible — sans jamais imposer le
# plancher de FAR (DM-EQ102). Les règles de raisonnement
# (DM-EQ94 à DM-EQ96) et les contraintes physiques/de ressources
# (DM-EQ97 à DM-EQ101) restent, elles, pleinement appliquées.


def build_b2_policy_definition():

    return {
        "policy_id": "B2-NAIVE-PHYSEC-NO-FLOOR",
        "description": (
            "PhySec naïve : essaie, dans un ordre de "
            "préférence fixe privilégiant A2 et K1a/K1b "
            "dès qu'ils semblent admissibles, sans "
            "imposer le plancher de FAR (DM-EQ102). "
            "Sert à isoler l'effet du plancher de "
            "sécurité combiné à l'absence d'arbitrage "
            "Pareto/Tchebycheff."
        )
    }


def _build_b2_preference_order(renewal_required):

    if renewal_required:

        return [
            Decision(
                AuthenticationAction.A2,
                KeyAction.K1A
            ),
            Decision(
                AuthenticationAction.A2,
                KeyAction.K1B
            ),
            Decision(
                AuthenticationAction.A1,
                KeyAction.K1A
            ),
            Decision(
                AuthenticationAction.A1,
                KeyAction.K1B
            ),
            Decision(
                AuthenticationAction.A2,
                KeyAction.K2
            ),
            Decision(
                AuthenticationAction.A1,
                KeyAction.K2
            )
        ]

    return [
        Decision(
            AuthenticationAction.A2,
            KeyAction.K0
        ),
        Decision(
            AuthenticationAction.A1,
            KeyAction.K0
        )
    ]


def select_b2_naive_physec_decision(
    context,
    parameters,
    rho_ab,
    variation_feasible=None,
    k2_protocol=None,
    contextual_weights=None
):

    del contextual_weights

    preference_order = _build_b2_preference_order(
        context.renewal_required
    )

    all_evaluations = []
    selected_evaluation = None

    for decision in preference_order:

        evaluation = evaluate_decision(
            decision=decision,
            context=context,
            parameters=parameters,
            rho_ab=rho_ab,
            variation_feasible=variation_feasible,
            k2_protocol=k2_protocol,
            enforce_far_floor=False
        )

        all_evaluations.append(
            evaluation
        )

        if (
            selected_evaluation is None
            and evaluation.admissible
        ):

            selected_evaluation = evaluation

    rejection_journal = []

    for evaluation in all_evaluations:

        rejection_journal.extend(
            evaluation.rejection_reasons
        )

    if selected_evaluation is not None:

        refusal_of_service = False
        fallback_mode_used = None

        explanation = (
            "B2-NAIVE-PHYSEC-NO-FLOOR : "
            + selected_evaluation.decision.get_name()
            + " est la première décision admissible de "
            "l'ordre de préférence fixe (sans plancher "
            "de FAR)."
        )

    else:

        refusal_of_service = True
        fallback_mode_used = "B2-NAIVE-PHYSEC-NO-FLOOR"

        explanation = (
            "B2-NAIVE-PHYSEC-NO-FLOOR : aucune décision "
            "de l'ordre de préférence fixe n'est "
            "admissible."
        )

    return DecisionMakerResult(
        context=context,
        all_evaluations=all_evaluations,
        admissible_evaluations=[
            evaluation
            for evaluation in all_evaluations
            if evaluation.admissible
        ],
        pareto_front=(
            [selected_evaluation]
            if selected_evaluation is not None
            else []
        ),
        rejection_journal=rejection_journal,
        contextual_weights=None,
        ideal_point=None,
        nadir_point=None,
        selected_evaluation=selected_evaluation,
        refusal_of_service=refusal_of_service,
        fallback_mode_used=fallback_mode_used,
        explanation=explanation
    )


# ================================================================
# B3 : RÈGLE HYBRIDE FIXE NON ADAPTATIVE
# ================================================================
#
# Politique de référence exigée par le protocole (Étape 4) :
# une SEULE règle fixe (A2 systématique ; K1a dès qu'un
# renouvellement est requis, K0 sinon), jamais réévaluée ni
# comparée à une alternative. Contrairement à B2 (qui essaie
# plusieurs décisions dans un ordre de préférence jusqu'à en
# trouver une admissible), B3 n'a aucune recherche de repli :
# si l'unique décision fixe n'est pas admissible, la mission
# refuse le service. Le plancher de FAR (DM-EQ102) reste
# pleinement appliqué, contrairement à B2 et B4.


def build_b3_policy_definition():

    return {
        "policy_id": "B3-HYBRID-FIXED",
        "description": (
            "Règle hybride fixe, non adaptative : "
            "authentification A2 systématique ; gestion "
            "de clé K1a dès qu'un renouvellement est "
            "requis, K0 sinon. Aucune recherche de repli "
            "vers une autre décision ; le plancher de FAR "
            "reste appliqué."
        )
    }


def select_b3_hybrid_fixed_decision(
    context,
    parameters,
    rho_ab,
    variation_feasible=None,
    k2_protocol=None,
    contextual_weights=None
):

    del contextual_weights

    if context.renewal_required:

        candidate_key_action = KeyAction.K1A

    else:

        candidate_key_action = KeyAction.K0

    decision = Decision(
        AuthenticationAction.A2,
        candidate_key_action
    )

    evaluation = evaluate_decision(
        decision=decision,
        context=context,
        parameters=parameters,
        rho_ab=rho_ab,
        variation_feasible=variation_feasible,
        k2_protocol=k2_protocol
    )

    if evaluation.admissible:

        selected_evaluation = evaluation
        refusal_of_service = False
        fallback_mode_used = None

        explanation = (
            "B3-HYBRID-FIXED : "
            + decision.get_name()
            + " est admissible et retenue (règle fixe, "
            "aucune recherche de repli)."
        )

    else:

        selected_evaluation = None
        refusal_of_service = True
        fallback_mode_used = "B3-HYBRID-FIXED"

        explanation = (
            "B3-HYBRID-FIXED : "
            + decision.get_name()
            + " n'est pas admissible ; la politique "
            "n'essaie aucune alternative (règle fixe "
            "non adaptative, par construction)."
        )

    return DecisionMakerResult(
        context=context,
        all_evaluations=[evaluation],
        admissible_evaluations=(
            [evaluation]
            if evaluation.admissible
            else []
        ),
        pareto_front=(
            [evaluation]
            if evaluation.admissible
            else []
        ),
        rejection_journal=list(
            evaluation.rejection_reasons
        ),
        contextual_weights=None,
        ideal_point=None,
        nadir_point=None,
        selected_evaluation=selected_evaluation,
        refusal_of_service=refusal_of_service,
        fallback_mode_used=fallback_mode_used,
        explanation=explanation
    )


# ================================================================
# B4 : DECISION MAKER COMPLET, SANS PLANCHER DE FAR
# ================================================================
#
# Politique de référence exigée par le protocole (Étape 4) pour
# isoler l'effet PROPRE du plancher de sécurité DM-EQ102 :
# B4 réutilise EXACTEMENT le même Decision Maker que P0 (front
# de Pareto exact, scalarisation de Tchebycheff, mêmes poids
# égaux de référence), avec la SEULE différence que le plancher
# de FAR n'est pas imposé. Toute différence entre P0 et B4 est
# donc attribuable à cette seule contrainte, et à rien d'autre.


def build_b4_policy_definition():

    return {
        "policy_id": "B4-DM-NO-FAR-FLOOR",
        "description": (
            "Decision Maker complet (Pareto exact + "
            "Tchebycheff, mêmes poids égaux que P0), "
            "sans le plancher de FAR (DM-EQ102). Isole "
            "l'effet propre de cette contrainte de "
            "sécurité sur les quatre objectifs."
        )
    }


def select_b4_decision_maker_no_far_floor(
    context,
    parameters,
    rho_ab,
    variation_feasible=None,
    k2_protocol=None,
    contextual_weights=None
):

    return run_decision_maker(
        context=context,
        parameters=parameters,
        rho_ab=rho_ab,
        variation_feasible=variation_feasible,
        k2_protocol=k2_protocol,
        contextual_weights=contextual_weights,
        enforce_far_floor=False
    )


# ================================================================
# B5 : REPLI RFF-PUIS-MAC (FAÇON HAENEL ET AL. 2021)
# ================================================================
#
# Baseline publiée ajoutée à la demande explicite de
# l'encadrant en réunion, pour comparer P0 à une stratégie de
# la littérature plutôt qu'uniquement à des ablations internes
# (B1-B4). Haenel et al. [Sensors 2021] décrivent une
# architecture cross-layer : l'empreinte radiofréquence (RFF)
# est vérifiée en premier ; le repli cryptographique (MAC)
# n'est déclenché que lorsque ce test rejette le message
# courant. C'est une règle fixe, message par message, qui ne
# considère ni l'état de la batterie ni la gestion de clé
# physique -- Haenel et al. ne traitent pas la génération de
# clé, seule l'authentification est adaptative dans leur
# architecture.
#
# B5 reproduit cette logique dans les limites du cadre de
# décision existant :
#   - authentification : A2 (RFF) essayée en premier ; repli
#     vers A1 (MAC) uniquement si A2 n'est pas admissible
#     (le plancher de FAR DM-EQ102 reste appliqué, contrairement
#     à B2, car c'est précisément ce plancher qui joue ici le
#     rôle du "rejet du test RFF" chez Haenel et al.) ;
#   - gestion de clé : conventionnelle uniquement (K0 si aucun
#     renouvellement n'est requis, K2 sinon), sans génération
#     physique de clé (K1a/K1b), pour rester fidèle au périmètre
#     de l'architecture de Haenel et al., qui ne couvre pas la
#     gestion de clé.
#
# Cette politique n'est PAS une reproduction bit-à-bit de
# Haenel et al. (le modèle de coût, le canal et le matériel
# restent ceux de cette étude) : c'est une transposition de
# leur RÈGLE DE DÉCISION dans notre cadre de simulation, dans
# le seul but de comparer un mécanisme de bascule publié à P0
# sur les mêmes scénarios et les mêmes métriques.


def build_b5_policy_definition():

    return {
        "policy_id": "B5-HAENEL-RFF-THEN-MAC",
        "description": (
            "Repli RFF-puis-MAC façon Haenel et al. 2021 : "
            "authentification A2 essayée en premier, repli "
            "vers A1 uniquement si A2 n'est pas admissible "
            "(plancher de FAR appliqué). Gestion de clé "
            "conventionnelle uniquement (K0/K2), sans "
            "génération physique de clé, pour rester fidèle "
            "au périmètre de l'architecture publiée."
        )
    }


def select_b5_haenel_rff_then_mac_decision(
    context,
    parameters,
    rho_ab,
    variation_feasible=None,
    k2_protocol=None,
    contextual_weights=None
):

    del contextual_weights

    if context.renewal_required:

        conventional_key_action = KeyAction.K2

    else:

        conventional_key_action = KeyAction.K0

    preference_order = [
        Decision(
            AuthenticationAction.A2,
            conventional_key_action
        ),
        Decision(
            AuthenticationAction.A1,
            conventional_key_action
        )
    ]

    all_evaluations = []
    selected_evaluation = None

    for decision in preference_order:

        evaluation = evaluate_decision(
            decision=decision,
            context=context,
            parameters=parameters,
            rho_ab=rho_ab,
            variation_feasible=variation_feasible,
            k2_protocol=k2_protocol,
            enforce_far_floor=True
        )

        all_evaluations.append(
            evaluation
        )

        if (
            selected_evaluation is None
            and evaluation.admissible
        ):

            selected_evaluation = evaluation

    rejection_journal = []

    for evaluation in all_evaluations:

        rejection_journal.extend(
            evaluation.rejection_reasons
        )

    if selected_evaluation is not None:

        refusal_of_service = False
        fallback_mode_used = (
            None
            if selected_evaluation.decision.authentication_action
            == AuthenticationAction.A2
            else "B5-HAENEL-RFF-THEN-MAC (repli MAC après rejet RFF)"
        )

        explanation = (
            "B5-HAENEL-RFF-THEN-MAC : "
            + selected_evaluation.decision.get_name()
            + " retenue (RFF essayée en premier, repli MAC "
            "uniquement si le RFF est rejeté)."
        )

    else:

        refusal_of_service = True
        fallback_mode_used = "B5-HAENEL-RFF-THEN-MAC"

        explanation = (
            "B5-HAENEL-RFF-THEN-MAC : ni le RFF ni le repli "
            "MAC ne sont admissibles."
        )

    return DecisionMakerResult(
        context=context,
        all_evaluations=all_evaluations,
        admissible_evaluations=[
            evaluation
            for evaluation in all_evaluations
            if evaluation.admissible
        ],
        pareto_front=(
            [selected_evaluation]
            if selected_evaluation is not None
            else []
        ),
        rejection_journal=rejection_journal,
        contextual_weights=None,
        ideal_point=None,
        nadir_point=None,
        selected_evaluation=selected_evaluation,
        refusal_of_service=refusal_of_service,
        fallback_mode_used=fallback_mode_used,
        explanation=explanation
    )
