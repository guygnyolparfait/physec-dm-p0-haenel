# ================================================================
# CONFIGURATION CENTRALISÉE — BANC D'ESSAI DE RÉFÉRENCE HAENEL
# ================================================================
#
# Source unique : Haenel, A.; Haddad, Y.; Laurent, M.; Zhang, Z.
# "Practical Cross-Layer Radio Frequency-Based Authentication
# Scheme for Internet of Things." Sensors 2021, 21, 4034.
#
# Toute valeur numérique utilisée ailleurs dans ce module DOIT
# venir de ce fichier. Ne jamais recopier un chiffre "en dur"
# dans un autre script de haenel_comparison/.
#
# Chaque paramètre est étiqueté par un statut :
#   PUBLISHED  : valeur numérique donnée explicitement par
#                Haenel et al. dans le papier (section citée).
#   DERIVED    : calcul simple et non ambigu à partir d'une
#                valeur PUBLISHED (ex. n_messages = duration/interval).
#   CALIBRATED : valeur que NOUS choisissons en l'ajustant sur
#                des résultats PUBLISHED (ex. coût moyen d'un
#                fallback déduit des 4 énergies publiées).
#   ASSUMED    : hypothèse de modélisation nécessaire pour faire
#                tourner NOTRE Decision Maker (qui a besoin d'un
#                contexte que Haenel et al. ne fournit pas dans
#                les mêmes unités, p.ex. un SNR en dB). Documentée
#                explicitement, jamais présentée comme publiée.
#   UNAVAILABLE: donnée que Haenel et al. NE PUBLIE PAS et que
#                nous ne fabriquons pas. Marquée
#                "NON FOURNI PAR HAENEL — À MODÉLISER / À SOURCER".

EVALUATION_TYPE = (
    "simulation calibrated from Haenel et al. (Sensors 2021) "
    "published experimental measurements — this is NOT a "
    "physical reproduction of their MSP430/CC110L hardware "
    "testbed."
)

# ----------------------------------------------------------------
# 1. PROTOCOLE TEMPOREL DU BANC D'ESSAI ÉNERGÉTIQUE (Section 6.3.2)
# ----------------------------------------------------------------

DURATION_S = 300.0                 # PUBLISHED — Table 1, p.15 ("Time")
MESSAGE_INTERVAL_S = 3.0           # PUBLISHED — Section 6.3.2, p.14
                                    #   ("SNs transmit ... every 3 s")
N_MESSAGES = int(DURATION_S / MESSAGE_INTERVAL_S)   # DERIVED = 100

# ----------------------------------------------------------------
# 2. CALIBRATION RFF (Section 6.2.2, Fig. 9, p.13)
# ----------------------------------------------------------------

FAR_REFERENCE = 0.0020             # PUBLISHED — "FAR = 0.20%"
FRR_REFERENCE = 0.1089             # PUBLISHED — "FRR = 10.89%"
DECISION_THRESHOLD_REFERENCE = 0.9  # PUBLISHED — "threshold > 0.9"
KNN_K = 10                         # PUBLISHED — "K set to 10"
TRAINING_MESSAGES = 500            # PUBLISHED — "first 500 valid messages"
EVALUATION_MESSAGES = 2000         # PUBLISHED — "for 2000 messages"
N_ANCHORS = 3                      # PUBLISHED — "three RF anchors"
FEATURES_PER_MESSAGE = 3           # PUBLISHED — "three RSSI values"

# Ces paramètres de classification (KNN, ancres, RSSI) appartiennent
# à l'EXPÉRIENCE DE PRÉCISION de Haenel et al. (Section 6.2), pas au
# banc d'essai énergétique (Section 6.3). Ils sont documentés ici
# pour traçabilité mais NE SONT PAS utilisés par les simulations
# énergétiques de ce module — voir HAENEL_COMPARISON_README.md.

# ----------------------------------------------------------------
# 3. CAS SIMULÉS DANS LE BANC D'ESSAI ÉNERGÉTIQUE (Section 6.3.1/6.3.3)
# ----------------------------------------------------------------
#
# IMPORTANT (à documenter dans toute analyse) : le banc d'essai
# énergétique de Haenel et al. NE MET PAS en scène d'attaquant.
# Le FRR y simule un REJET À TORT DU MESSAGE LÉGITIME par le test
# RFF (fausse alerte sur Alice elle-même), pas une acceptation de
# Mallory. Citation exacte (Section 6.3.1) : "the GW simulates the
# RFF ... (simulated FRR of 10%, 5%; and 0% for the simulated
# RFF-only)". Le FAR (sécurité face à un attaquant) n'intervient
# pas dans CE banc d'essai précis — il vient de l'expérience de
# précision (Section 6.2). Notre reproduction respecte cette
# distinction : mallory_attempt_probability = 0.0 dans ce scénario.

HAENEL_FRR_CONFIGS = {
    "MAC_ONLY": {
        "frr": None,   # pas de RFF du tout : chaque message est
                        # authentifié par MAC directement (PUBLISHED,
                        # Section 6.3.1)
        "published_energy_mJ": 564.743,   # PUBLISHED — Table 1
    },
    "HYBRID_FRR_10": {
        "frr": 0.10,                       # PUBLISHED — Section 6.3.1
        "published_energy_mJ": 454.076,   # PUBLISHED — Table 1
    },
    "HYBRID_FRR_05": {
        "frr": 0.05,                       # PUBLISHED — Section 6.3.1
        "published_energy_mJ": 404.790,   # PUBLISHED — Table 1
    },
    "RFF_ONLY": {
        "frr": 0.0,                        # PUBLISHED — Section 6.3.1
                                            # ("no fall back to
                                            # cryptographic authentication")
        "published_energy_mJ": 355.412,   # PUBLISHED — Table 1
    },
}

# Cas principal demandé explicitement par l'utilisateur.
PRIMARY_FRR_CASE = "HYBRID_FRR_05"
SECONDARY_FRR_CASE = "HYBRID_FRR_10"

# ----------------------------------------------------------------
# 4. MATÉRIEL HAENEL — DOCUMENTÉ, JAMAIS PRÉTENDU REPRODUIT
# ----------------------------------------------------------------

HAENEL_HARDWARE_DOCUMENTATION = {
    "microcontroller_energy_testbed": (
        "Texas Instruments MSP430G2x (Section 6.3.2 : \"we used the "
        "Texas Instrument ultra-low-power microcontroller MSP430G2x "
        "and the sub-1 GHz RF transceiver CC110L\"). Puce exacte non "
        "précisée par le papier ; le kit nommé (MSP-EXP430G2ET) est "
        "livré par défaut avec un MSP430G2553 (DERIVED, voir "
        "haenel_option_b_sources.py)."
    ),                                                              # PUBLISHED
    "microcontroller_other_testbed": (
        "MSP430FR5994 -- utilisé ailleurs dans le papier (nœud "
        "aéroporté/drone), PAS le microcontrôleur du banc d'essai "
        "énergétique de Section 6.3.2. Ne doit jamais servir de "
        "référence CPU pour la reconstruction énergétique "
        "(erreur corrigée le 25/09/2026, voir WORK_LOG.md)."
    ),                                                              # PUBLISHED
    "radio_transceiver": "CC110L, 868-870 MHz ISM band",           # PUBLISHED
    "energy_measurement_tool": "EnergyTrace (Texas Instruments), "
                                "via MSP-EXP430G2ET + Code "
                                "Composer Studio (Section 6.3.2)",  # PUBLISHED
    "deep_sleep_used_in_energy_testbed": (
        "NON. Section 6.3.2 : \"This also prevented the nodes from "
        "using the 'deep-sleep' mode of the modules between two "
        "transmissions.\" energy_option_b.py ne modélise donc aucun "
        "courant LPM/deep-sleep."
    ),                                                              # PUBLISHED
    "cryptographic_primitive": "Chaskey-12 keyed-hash MAC "
                                "(ISO/IEC standardized variant)",   # PUBLISHED
    "battery_profile": "3 V, 2400 mAh (two AA batteries)",         # PUBLISHED
    "note": "Toutes ces informations décrivent LE MATÉRIEL RÉEL "
            "utilisé par Haenel et al. Notre travail reste une "
            "SIMULATION : nous ne possédons ni ne mesurons ce "
            "matériel.",
}

# ----------------------------------------------------------------
# 5. TABLE DE TRAÇABILITÉ DES PARAMÈTRES (exportée en CSV)
# ----------------------------------------------------------------
#
# Une ligne par paramètre utilisé quelque part dans ce module.
# Alimentée manuellement ici (source unique), puis simplement
# sérialisée par haenel_parameter_traceability.py.

PARAMETER_TRACEABILITY = [
    {
        "parameter": "duration_s",
        "value": DURATION_S,
        "unit": "s",
        "source": "Haenel et al. 2021",
        "paper_page_or_section": "Table 1, p.15",
        "status": "PUBLISHED_HAENEL",
        "used_in": "haenel_b5.py, run_haenel_experiment_a.py",
        "comment": "Durée du banc d'essai énergétique.",
    },
    {
        "parameter": "message_interval_s",
        "value": MESSAGE_INTERVAL_S,
        "unit": "s",
        "source": "Haenel et al. 2021",
        "paper_page_or_section": "Section 6.3.2, p.14",
        "status": "PUBLISHED_HAENEL",
        "used_in": "haenel_config.py (dérive n_messages)",
        "comment": "\"transmit a data packet every 3 s\".",
    },
    {
        "parameter": "n_messages",
        "value": N_MESSAGES,
        "unit": "messages",
        "source": "duration_s / message_interval_s",
        "paper_page_or_section": "dérivé",
        "status": "DERIVED_FROM_HAENEL",
        "used_in": "tout le module haenel_comparison",
        "comment": "300 / 3 = 100.",
    },
    {
        "parameter": "FAR_reference / FAR_RFF_HAENEL",
        "value": FAR_REFERENCE,
        "unit": "ratio",
        "source": "Haenel et al. 2021",
        "paper_page_or_section": "Fig. 9 / Section 6.2.2, p.13 ; "
                                  "apparié au FRR=10% du banc "
                                  "d'essai énergétique, Section "
                                  "6.3.1 : \"This value was chosen "
                                  "as it led to a FAR of 0.2% in "
                                  "our live experiment\"",
        "status": "PUBLISHED_HAENEL",
        "used_in": "run_haenel_experiment_b.py, security_monte_carlo.py, "
                   "p0_auth_only_haenel_rff.py (comparaison principale)",
        "comment": "Issu de l'expérience de précision (KNN, Section "
                   "6.2), transposé dans une campagne séparée pour "
                   "le FRR=10% (documenté PUBLISHED_HAENEL pour ce "
                   "cas précis) ; réutilisé par hypothèse pour la "
                   "sensibilité FRR=5% (voir "
                   "ASSUMED_CONSTANT_FAR_FOR_FRR5_SENSITIVITY dans "
                   "p0_auth_only_haenel_rff.py).",
    },
    {
        "parameter": "FRR_reference (classification, Section 6.2.2)",
        "value": FRR_REFERENCE,
        "unit": "ratio",
        "source": "Haenel et al. 2021",
        "paper_page_or_section": "Fig. 9 / Section 6.2.2, p.13",
        "status": "PUBLISHED_HAENEL",
        "used_in": "documentation / traçabilité uniquement",
        "comment": "10.89% -- arrondi à 10% pour le banc d'essai "
                   "énergétique simulé (Section 6.3.1). Distinct du "
                   "\"frr\" simulé dans HAENEL_FRR_CONFIGS.",
    },
    {
        "parameter": "energy_MAC_ONLY_mJ",
        "value": HAENEL_FRR_CONFIGS["MAC_ONLY"]["published_energy_mJ"],
        "unit": "mJ",
        "source": "Haenel et al. 2021",
        "paper_page_or_section": "Table 1, p.15",
        "status": "PUBLISHED_HAENEL",
        "used_in": "energy_option_a.py (published reference used "
                   "directly, jamais prédit)",
        "comment": "Mesure EnergyTrace, 300 s.",
    },
    {
        "parameter": "energy_HYBRID_FRR_10_mJ",
        "value": HAENEL_FRR_CONFIGS["HYBRID_FRR_10"]["published_energy_mJ"],
        "unit": "mJ",
        "source": "Haenel et al. 2021",
        "paper_page_or_section": "Table 1, p.15",
        "status": "PUBLISHED_HAENEL",
        "used_in": "energy_option_a.py (calibration EFFECTIVE)",
        "comment": "Cas principal (Section 2A) : FRR=10%, apparié à "
                   "FAR=0.2%.",
    },
    {
        "parameter": "energy_HYBRID_FRR_05_mJ",
        "value": HAENEL_FRR_CONFIGS["HYBRID_FRR_05"]["published_energy_mJ"],
        "unit": "mJ",
        "source": "Haenel et al. 2021",
        "paper_page_or_section": "Table 1, p.15",
        "status": "PUBLISHED_HAENEL",
        "used_in": "energy_option_a.py (calibration EFFECTIVE)",
        "comment": "Cas secondaire (sensibilité énergétique), sans "
                   "FAR apparié expérimentalement.",
    },
    {
        "parameter": "energy_RFF_ONLY_mJ",
        "value": HAENEL_FRR_CONFIGS["RFF_ONLY"]["published_energy_mJ"],
        "unit": "mJ",
        "source": "Haenel et al. 2021",
        "paper_page_or_section": "Table 1, p.15",
        "status": "PUBLISHED_HAENEL",
        "used_in": "energy_option_a.py (base RFF, cas limite "
                   "théorique \"no fall back\")",
        "comment": "",
    },
    {
        "parameter": "EFFECTIVE_FIXED_HYBRID_OVERHEAD_MJ",
        "value": None,   # calculé dynamiquement par energy_option_a.py
        "unit": "mJ",
        "source": "résolution exacte d'un système 2x2 (2 points "
                   "HYBRID publiés, 2 inconnues) -- voir "
                   "energy_option_a.calibrate_effective_hybrid_terms_mJ",
        "paper_page_or_section": "calculé, voir energy_option_a.py",
        "status": "CALIBRATED_EFFECTIVE",
        "used_in": "energy_option_a.py, haenel_energy_adapter.py, "
                   "run_haenel_experiment_a.py",
        "comment": "Agrège tout ce que le papier ne permet pas de "
                   "décomposer (notamment la première "
                   "authentification complète, Section 6.3.3/Fig. "
                   "11) -- PAS le coût physique exact de cette "
                   "authentification. ~0.092 mJ (négligeable en "
                   "magnitude, mais nommé explicitement pour la "
                   "rigueur méthodologique).",
    },
    {
        "parameter": "EFFECTIVE_FALLBACK_COST_MJ",
        "value": None,   # calculé dynamiquement par energy_option_a.py
        "unit": "mJ/repli",
        "source": "même système 2x2 que ci-dessus",
        "paper_page_or_section": "calculé, voir energy_option_a.py",
        "status": "CALIBRATED_EFFECTIVE",
        "used_in": "energy_option_a.py, haenel_energy_adapter.py",
        "comment": "Coût agrégé EFFECTIF d'un repli MAC (~9.86 "
                   "mJ/repli), PAS une mesure universelle du coût "
                   "d'un MAC isolé.",
    },
    {
        "parameter": "context_snr_db (pour faire tourner P0)",
        "value": "voir HAENEL_P0_CONTEXT_SNR_DB ci-dessous",
        "unit": "dB",
        "source": "Haenel et al. ne rapporte aucun SNR en dB pour "
                   "le banc d'essai énergétique (seulement des "
                   "distances en mètres, 8-25 m)",
        "paper_page_or_section": "NON FOURNI PAR HAENEL",
        "status": "ASSUMED",
        "used_in": "p0_auth_only.py (contexte statique de P0)",
        "comment": "Nécessaire pour que notre modèle FAR NATIF "
                   "(chi-2 non centrée) calcule une admissibilité "
                   "de A2 dans l'analyse SECONDAIRE "
                   "P0_NATIVE_RFF_SENSITIVITY uniquement -- la "
                   "COMPARAISON PRINCIPALE (p0_auth_only_haenel_rff.py) "
                   "n'en dépend PAS pour le FAR de A2, qui reçoit "
                   "directement FAR_RFF_HAENEL=0.002 publié.",
    },
    {
        "parameter": "TX/RX current, CPU active current "
                     "(MSP430G2x/CC110L)",
        "value": "voir haenel_option_b_sources.csv",
        "unit": "mA / µA/MHz",
        "source": "Datasheets TI officiels (CC110L SWRS109C, "
                   "MSP430G2553 SLAS735J, MSP430G2231-EP SLAS862) -- "
                   "PAS publié par Haenel et al. lui-même (seules "
                   "les puissances mean/min/max GLOBALES du système "
                   "sont données, Table 1)",
        "paper_page_or_section": "NON FOURNI PAR HAENEL -- sourcé "
                                  "séparément (voir "
                                  "haenel_option_b_sources.csv)",
        "status": "OFFICIAL_DATASHEET",
        "used_in": "energy_option_b.py (Option B, modèle "
                   "événementiel)",
        "comment": "RÉSOLU cette session (25/09/2026) : n'est plus "
                   "UNAVAILABLE. Corrigé après relecture -- une "
                   "première version sourçait par erreur le "
                   "MSP430FR5994 (mauvais composant, utilisé "
                   "ailleurs dans le papier pour le nœud drone) au "
                   "lieu du MSP430G2x du banc d'essai énergétique "
                   "(Section 6.3.2).",
    },
    {
        "parameter": "CC110L state transition time (calib_transition_s)",
        "value": "75.1 (LOW) / 799 (CENTRAL) / 1598 (HIGH) µs",
        "unit": "µs",
        "source": "CC110L SWRS109C, Table 5-11",
        "paper_page_or_section": "Section 5.19.6.1, p.43",
        "status": "ASSUMED_STATE_TRANSITION",
        "used_in": "energy_option_b.py",
        "comment": "Corrigé (25/09/2026) : remplace un temps de "
                   "réveil depuis le DEEP-SLEEP (240 µs) incohérent "
                   "avec l'exclusion explicite du deep-sleep par "
                   "Haenel et al. pour ce banc d'essai. Utilise "
                   "maintenant les temps de transition depuis IDLE.",
    },
    {
        "parameter": "Chaskey(-12) cost on MSP430 16-bit "
                     "(cycles/octet)",
        "value": "10 (LOW) / 20 (CENTRAL) / 40 (HIGH), ASSUMED_MAPPING",
        "unit": "cycles/octet",
        "source": "Mouha et al. 2015 (eprint 2015/1182) donne les "
                   "chiffres ARM Cortex-M (9.8/7.0 cycles/octet) et "
                   "un ratio relatif \"+30% sur MSP430\" -- PAS de "
                   "valeur absolue MSP430. Un article dédié "
                   "(Lee & Seo, IEEE) existe mais était inaccessible "
                   "cette session (accès payant).",
        "paper_page_or_section": "NON FOURNI PAR HAENEL -- voir "
                                  "haenel_option_b_sources.csv pour "
                                  "le détail des deux sources "
                                  "consultées",
        "status": "EXTERNAL_SCIENTIFIC_SOURCE",
        "used_in": "energy_option_b.py",
        "comment": "Recherché activement le 25/09/2026 (WebSearch/"
                   "WebFetch) -- le chiffre ABSOLU MSP430 reste "
                   "UNAVAILABLE malgré la recherche ; la plage "
                   "utilisée est une extrapolation raisonnée, jamais "
                   "présentée comme mesurée.",
    },
]

# ----------------------------------------------------------------
# 6. CONTEXTE STATIQUE POUR FAIRE TOURNER P0 (ASSUMED, documenté)
# ----------------------------------------------------------------
#
# Haenel et al. ne fournit pas de SNR en dB pour le banc d'essai
# énergétique : leurs nœuds sont positionnés par DISTANCE (8, 9,
# 12 m pour les légitimes). Notre Decision Maker P0 a besoin d'un
# contexte radio (SNR, séparation Alice/Mallory) pour calculer un
# FAR et une robustesse — grandeurs que Haenel et al. n'exprime
# jamais dans ces unités. Nous choisissons donc un contexte
# ASSUMED, documenté ici, cohérent avec le FAR très faible qu'ils
# rapportent (0,20 %) : un canal favorable où A2 est typiquement
# admissible. Ce n'est PAS une tentative de reproduire leurs 8-25 m
# en dB — c'est un pont de modélisation explicite entre leur
# calibration et notre modèle de canal.
HAENEL_P0_CONTEXT_SNR_DB = 10.0        # ASSUMED
HAENEL_P0_CONTEXT_SHADOWING_STD_DB = 1.0  # ASSUMED (canal stable,
                                            # nœuds fixes -- Section 6.1)
HAENEL_P0_CONTEXT_SPEED_M_S = 0.0      # PUBLISHED (implicite) — la
                                        # SN légitime "stays at a
                                        # fixed location" (Section 6.1)

# Pas d'attaquant dans ce banc d'essai précis (voir note Section 3
# ci-dessus) : mallory_attempt_probability = 0.0.
HAENEL_P0_MALLORY_ATTEMPT_PROBABILITY = 0.0   # PUBLISHED (dérivé de
                                                # la méthodologie
                                                # Section 6.3.1)
