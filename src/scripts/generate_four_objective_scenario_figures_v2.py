# VERSION 2 — corrigée pour intégration dans un article IEEE.
#
# Ce script est autonome : il ne modifie ni n'importe
# generate_four_objective_scenario_figures.py (V1) et écrit
# exclusivement dans results/final_presentation/four_objective_scenarios_v2/.
# Il ne relance aucune simulation : il réutilise soit le cache
# d'extraction déjà validé de la V1 (results/final_presentation/
# four_objective_scenarios/_temporal_extraction_cache.pkl), soit,
# à défaut, refait un unique passage sur le journal brut déjà
# produit par la campagne (avec la même logique d'agrégation,
# validée par les contrôles de cohérence V1 à 0,000% d'écart).
#
# Commande exacte pour lancer ce script (depuis la racine du dépôt,
# environnement virtuel activé) :
#
#   python generate_four_objective_scenario_figures_v2.py
#
import copy
import csv
import hashlib
import pickle
import statistics
import subprocess
from pathlib import Path

import matplotlib as mpl
mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["ps.fonttype"] = 42
mpl.rcParams["svg.fonttype"] = "none"
mpl.rcParams["font.family"] = "serif"
mpl.rcParams["font.serif"] = ["Liberation Serif", "DejaVu Serif"]
mpl.rcParams["mathtext.fontset"] = "dejavuserif"
mpl.rcParams["font.size"] = 8
mpl.use("Agg")
import matplotlib.pyplot as plt

from scripts.analyze_five_case_studies import scenario_full_name


RESULTS_DIR = Path("results/five_case_studies_final_adaptive")
RAW_LOG_PATH = RESULTS_DIR / "five_case_studies_log.csv"
SUMMARY_CSV_PATH = RESULTS_DIR / "summary_by_scenario_policy.csv"
PAIRED_CSV_PATH = RESULTS_DIR / "paired_statistics_vs_p0.csv"
EVE_CSV_PATH = RESULTS_DIR / "eve_secrecy_validation.csv"

V1_CACHE_PATH = Path(
    "results/final_presentation/four_objective_scenarios"
    "/_temporal_extraction_cache.pkl"
)

OUTPUT_DIR = Path(
    "results/final_presentation/four_objective_scenarios_v2"
)
FIGURES_MAIN_DIR = OUTPUT_DIR / "figures" / "main_article"
FIGURES_SUPP_DIR = OUTPUT_DIR / "figures" / "supplementary_temporal"
DATA_DIR = OUTPUT_DIR / "data"
ARTICLE_TEXT_DIR = OUTPUT_DIR / "article_text"
VALIDATION_DIR = OUTPUT_DIR / "validation"

CACHE_PATH = OUTPUT_DIR / "_temporal_extraction_cache_v2.pkl"

MAX_STEPS = 1500
N_BINS = 50
STEPS_PER_BIN = MAX_STEPS // N_BINS

SCENARIO_IDS = [
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

POLICY_SHORT_LABEL = {
    "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS": "P0",
    "B1-CONVENTIONAL": "B1",
    "B2-NAIVE-PHYSEC-NO-FLOOR": "B2",
    "B3-HYBRID-FIXED": "B3",
    "B4-DM-NO-FAR-FLOOR": "B4"
}

POLICY_FULL_LABEL = {
    "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS": (
        "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS"
    ),
    "B1-CONVENTIONAL": "B1-CONVENTIONAL",
    "B2-NAIVE-PHYSEC-NO-FLOOR": "B2-NAIVE-PHYSEC-NO-FLOOR",
    "B3-HYBRID-FIXED": "B3-RIGID-HYBRID-NO-FALLBACK",
    "B4-DM-NO-FAR-FLOOR": "B4-DM-NO-FAR-FLOOR"
}

# Couleur distincte par politique. P0 (notre proposition) reçoit un
# vert franc -- signature visuelle cohérente avec le message du
# projet (sobriété énergétique) -- les baselines des teintes froides
# ou neutres bien séparées. Hachures retirées sur demande explicite
# (rendu jugé trop artificiel) : les 5 couleurs sont déjà assez
# contrastées en couleur pour rester lisibles sans motif de remplissage.
POLICY_COLORS = {
    "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS": "#1b8a5a",
    "B1-CONVENTIONAL": "#4a6fa5",
    "B2-NAIVE-PHYSEC-NO-FLOOR": "#e8935c",
    "B3-HYBRID-FIXED": "#c1443c",
    "B4-DM-NO-FAR-FLOOR": "#8a5fa8"
}

POLICY_HATCHES = {
    "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS": "",
    "B1-CONVENTIONAL": "",
    "B2-NAIVE-PHYSEC-NO-FLOOR": "",
    "B3-HYBRID-FIXED": "",
    "B4-DM-NO-FAR-FLOOR": ""
}

POLICY_LINESTYLES = {
    "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS": "-",
    "B1-CONVENTIONAL": "--",
    "B2-NAIVE-PHYSEC-NO-FLOOR": ":",
    "B3-HYBRID-FIXED": "-.",
    "B4-DM-NO-FAR-FLOOR": (0, (3, 1, 1, 1, 1, 1))
}

POLICY_MARKERS = {
    "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS": "o",
    "B1-CONVENTIONAL": "s",
    "B2-NAIVE-PHYSEC-NO-FLOOR": "^",
    "B3-HYBRID-FIXED": "D",
    "B4-DM-NO-FAR-FLOOR": "v"
}

POLICY_LINEWIDTH = {
    "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS": 2.2,
    "B1-CONVENTIONAL": 1.8,
    "B2-NAIVE-PHYSEC-NO-FLOOR": 1.0,
    "B3-HYBRID-FIXED": 1.0,
    "B4-DM-NO-FAR-FLOOR": 1.0
}

POLICY_ALPHA = {
    "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS": 1.0,
    "B1-CONVENTIONAL": 0.95,
    "B2-NAIVE-PHYSEC-NO-FLOOR": 0.65,
    "B3-HYBRID-FIXED": 0.65,
    "B4-DM-NO-FAR-FLOOR": 0.65
}

POLICY_ZORDER = {
    "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS": 5,
    "B1-CONVENTIONAL": 4,
    "B2-NAIVE-PHYSEC-NO-FLOOR": 2,
    "B3-HYBRID-FIXED": 2,
    "B4-DM-NO-FAR-FLOOR": 2
}

# Phases exactes (nom journalisé + fractions lues dans
# physec_dm/case_studies.py, converties en indices de période pour
# max_steps=1500). Jamais inventées.
SCENARIO_PHASES = {
    "S1-REMOTE-AGRICULTURAL-SENSOR": [
        ("Fonctionnement stable (mesures périodiques d'humidité)", 0, 1500)
    ],
    "S2-INDUSTRIAL-CRITICAL-ALARM": [
        ("Fonctionnement normal", 0, 600),
        ("Alarme critique (apparition et maintien)", 600, 750),
        ("Récupération progressive", 750, 1500)
    ],
    "S3-MOBILE-VEHICLE": [
        ("Véhicule à l'arrêt (départ)", 0, 300),
        ("Accélération", 300, 600),
        (
            "Déplacement à vitesse maximale du scénario (30.0 km/h)",
            600, 900
        ),
        ("Ralentissement", 900, 1200),
        ("Véhicule à l'arrêt (arrivée)", 1200, 1500)
    ],
    "S4-DENSE-URBAN-NETWORK": [
        ("Charge normale", 0, 375),
        ("Congestion (1)", 375, 600),
        ("Retour normal (1)", 600, 975),
        ("Congestion (2)", 975, 1200),
        ("Retour normal (2)", 1200, 1500)
    ],
    "S5-CRITICAL-INFRASTRUCTURE-ATTACK": [
        ("Fonctionnement normal", 0, 450),
        (
            "Attaque renforcée (avec suspicion de "
            "compromission à mi-phase)",
            450, 900
        ),
        ("Réaction et retour progressif à la normale", 900, 1500)
    ]
}

S5_COMPROMISE_STEP_START = 675
S5_COMPROMISE_STEP_END = 900

EXPECTED_SEED_COUNTS = {
    "S1-REMOTE-AGRICULTURAL-SENSOR": 30,
    "S2-INDUSTRIAL-CRITICAL-ALARM": 150,
    "S3-MOBILE-VEHICLE": 40,
    "S4-DENSE-URBAN-NETWORK": 30,
    "S5-CRITICAL-INFRASTRUCTURE-ATTACK": 30
}

METRIC_COLUMNS = [
    ("mean_energy_j", "energy_objective_j"),
    ("mean_latency_objective", "latency_objective"),
    ("mean_authentication_robustness", "authentication_robustness"),
    ("mean_key_quality", "key_quality")
]

METRIC_TITLES_A = {
    "mean_energy_j": "A. Énergie objective moyenne (J) — ↓ mieux",
    "mean_latency_objective": (
        "B. Latence normalisée moyenne — ↓ mieux"
    ),
    "mean_authentication_robustness": (
        "C. Robustesse d'authentification $R^{auth}$ — ↑ mieux"
    ),
    "mean_key_quality": (
        "D. Qualité de clé $Q^{key}$ (indice) — ↑ mieux"
    )
}

# Version anglaise des memes titres -- utilisee uniquement quand
# figure_four_objectives_comparison_v2(..., lang="en") est appelee
# (generation de l'article anglais). Le pipeline francais par
# defaut (lang="fr") reste strictement inchange.
METRIC_TITLES_A_EN = {
    "mean_energy_j": "A. Mean objective energy (J) — lower is better",
    "mean_latency_objective": (
        "B. Mean normalized latency — lower is better"
    ),
    "mean_authentication_robustness": (
        "C. Authentication robustness $R^{auth}$ — higher is better"
    ),
    "mean_key_quality": (
        "D. Key quality $Q^{key}$ (index) — higher is better"
    )
}

# Noms complets des scenarios en anglais -- dictionnaire local a ce
# script (ne touche pas SCENARIO_FULL_NAMES dans
# analyze_five_case_studies.py, partage par d'autres scripts qui
# doivent continuer a afficher les noms francais).
SCENARIO_FULL_NAMES_EN = {
    "S1-REMOTE-AGRICULTURAL-SENSOR": "S1 — Isolated agricultural sensor",
    "S2-INDUSTRIAL-CRITICAL-ALARM": "S2 — Critical industrial alarm",
    "S3-MOBILE-VEHICLE": "S3 — Mobile object on a vehicle",
    "S4-DENSE-URBAN-NETWORK": "S4 — Dense urban network",
    "S5-CRITICAL-INFRASTRUCTURE-ATTACK": (
        "S5 — Critical infrastructure under attack"
    )
}

# Nombre de décimales utilisé pour l'étiquette imprimée au-dessus de
# chaque barre, par métrique -- suffisant pour distinguer des
# politiques dont les moyennes ne diffèrent que sur la 5e/6e décimale
# (cas de R_auth, très proche de 1 partout sauf dégradation FAR
# franche), sans I) illisibilité II) faux sentiment de précision sur
# l'énergie/la latence.
METRIC_LABEL_DECIMALS = {
    "mean_energy_j": 5,
    "mean_latency_objective": 5,
    "mean_authentication_robustness": 6,
    "mean_key_quality": 5
}

METRIC_TITLES_B = {
    "mean_energy_j": "Énergie objective (J)",
    "mean_latency_objective": "Latence normalisée",
    "mean_authentication_robustness": "Robustesse d'authentification",
    "mean_key_quality": "Qualité de clé (indice)"
}


# ================================================================
# Section 1 — Extraction par graine puis par tranche
# ================================================================

def new_bin_bucket():

    return {
        "served_count": 0,
        "total_count": 0,
        "energy_sum": 0.0,
        "energy_count": 0,
        "latency_sum": 0.0,
        "latency_count": 0,
        "auth_sum": 0.0,
        "auth_count": 0,
        "key_sum": 0.0,
        "key_count": 0,
        "auth_component_counts": {"A1": 0, "A2": 0},
        "key_component_counts": {
            "K0": 0, "K1a": 0, "K1b": 0, "K2": 0
        }
    }


def parse_bool(value):

    return value == "True"


def parse_float_or_none(value):

    if value == "" or value is None:

        return None

    return float(value)


def extract_temporal_aggregates():

    print(
        "Passage unique sur le journal brut ("
        + str(RAW_LOG_PATH)
        + ") — peut prendre 1 à 2 minutes..."
    )

    buckets = {
        scenario_id: {
            policy_id: {}
            for policy_id in POLICY_IDS
        }
        for scenario_id in SCENARIO_IDS
    }

    seeds_seen = {
        scenario_id: {
            policy_id: set()
            for policy_id in POLICY_IDS
        }
        for scenario_id in SCENARIO_IDS
    }

    activation_events = []

    row_count = 0

    with RAW_LOG_PATH.open(newline="", encoding="utf-8") as csv_file:

        reader = csv.DictReader(csv_file)

        for row in reader:

            row_count += 1

            if row_count % 300000 == 0:

                print("  ... " + str(row_count) + " lignes traitées")

            scenario_id = row["scenario_id"]
            policy_id = row["policy_id"]
            seed = int(row["seed"])
            step_index = int(row["step_index"])
            bin_index = min(
                step_index // STEPS_PER_BIN,
                N_BINS - 1
            )

            seeds_seen[scenario_id][policy_id].add(seed)

            policy_seed_bins = buckets[scenario_id][policy_id]

            seed_bins = policy_seed_bins.setdefault(seed, {})

            bucket = seed_bins.setdefault(
                bin_index,
                new_bin_bucket()
            )

            bucket["total_count"] += 1

            served = parse_bool(row["legitimate_message_served"])

            if not served:

                continue

            bucket["served_count"] += 1

            energy_value = parse_float_or_none(
                row["energy_objective_j"]
            )
            latency_value = parse_float_or_none(
                row["latency_objective"]
            )
            auth_value = parse_float_or_none(
                row["authentication_robustness"]
            )
            key_value = parse_float_or_none(row["key_quality"])

            if energy_value is not None:

                bucket["energy_sum"] += energy_value
                bucket["energy_count"] += 1

            if latency_value is not None:

                bucket["latency_sum"] += latency_value
                bucket["latency_count"] += 1

            if auth_value is not None:

                bucket["auth_sum"] += auth_value
                bucket["auth_count"] += 1

            if key_value is not None:

                bucket["key_sum"] += key_value
                bucket["key_count"] += 1

            if policy_id == "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS":

                selected_decision = row["selected_decision"]

                if (
                    selected_decision
                    and selected_decision != "REFUS"
                ):

                    auth_component, key_component = (
                        selected_decision.split("-")
                    )

                    bucket["auth_component_counts"][
                        auth_component
                    ] += 1

                    bucket["key_component_counts"][
                        key_component
                    ] += 1

    print(
        "Extraction terminée : "
        + str(row_count)
        + " lignes journalisées au total."
    )

    plain_seeds_seen = {
        scenario_id: {
            policy_id: sorted(seeds_seen[scenario_id][policy_id])
            for policy_id in POLICY_IDS
        }
        for scenario_id in SCENARIO_IDS
    }

    return {
        "buckets": buckets,
        "seeds_seen": plain_seeds_seen,
        "row_count": row_count,
        "activation_events": activation_events
    }


def load_or_build_temporal_cache():

    if CACHE_PATH.exists():

        print(
            "Cache d'extraction V2 trouvé : " + str(CACHE_PATH)
        )

        with CACHE_PATH.open("rb") as cache_file:

            return pickle.load(cache_file)

    if V1_CACHE_PATH.exists():

        print(
            "Réutilisation du cache d'extraction V1 déjà validé : "
            + str(V1_CACHE_PATH)
            + " (aucune nouvelle simulation, aucun nouveau passage "
            "sur le journal brut)"
        )

        with V1_CACHE_PATH.open("rb") as cache_file:

            data = pickle.load(cache_file)

    else:

        data = extract_temporal_aggregates()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with CACHE_PATH.open("wb") as cache_file:

        pickle.dump(data, cache_file)

    return data


def mean_ci95(values):

    values = [v for v in values if v is not None]

    n = len(values)

    if n == 0:

        return None, None, 0

    mean_value = statistics.mean(values)

    if n < 2:

        return mean_value, 0.0, n

    half_width = (
        1.96 * statistics.stdev(values) / (n ** 0.5)
    )

    return mean_value, half_width, n


def compute_per_seed_bin_mean(bucket, sum_key, count_key):

    if bucket[count_key] == 0:

        return None

    return bucket[sum_key] / bucket[count_key]


def compute_cross_seed_bin_series(scenario_id, policy_id, buckets):

    policy_seed_bins = buckets[scenario_id][policy_id]

    series = {
        metric_key: {"mean": [], "half_width": [], "n": []}
        for metric_key, _ in METRIC_COLUMNS
    }
    series["service_rate"] = {
        "mean": [], "half_width": [], "n": []
    }

    for bin_index in range(N_BINS):

        per_seed_values = {
            metric_key: []
            for metric_key, _ in METRIC_COLUMNS
        }
        per_seed_service_rate = []

        for seed_bins in policy_seed_bins.values():

            bucket = seed_bins.get(bin_index)

            if bucket is None:

                continue

            if bucket["total_count"] > 0:

                per_seed_service_rate.append(
                    bucket["served_count"] / bucket["total_count"]
                )

            per_seed_values["mean_energy_j"].append(
                compute_per_seed_bin_mean(
                    bucket, "energy_sum", "energy_count"
                )
            )
            per_seed_values["mean_latency_objective"].append(
                compute_per_seed_bin_mean(
                    bucket, "latency_sum", "latency_count"
                )
            )
            per_seed_values[
                "mean_authentication_robustness"
            ].append(
                compute_per_seed_bin_mean(
                    bucket, "auth_sum", "auth_count"
                )
            )
            per_seed_values["mean_key_quality"].append(
                compute_per_seed_bin_mean(
                    bucket, "key_sum", "key_count"
                )
            )

        for metric_key in series:

            if metric_key == "service_rate":

                mean_value, half_width, n = mean_ci95(
                    per_seed_service_rate
                )

            else:

                mean_value, half_width, n = mean_ci95(
                    per_seed_values[metric_key]
                )

            series[metric_key]["mean"].append(mean_value)
            series[metric_key]["half_width"].append(half_width)
            series[metric_key]["n"].append(n)

    return series


def compute_p0_mechanism_series(scenario_id, buckets):

    policy_seed_bins = buckets[scenario_id][
        "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS"
    ]

    auth_series = {"A1": [], "A2": []}
    key_series = {"K0": [], "K1a": [], "K1b": [], "K2": []}
    n_seeds_series = []

    for bin_index in range(N_BINS):

        per_seed_auth_fractions = {"A1": [], "A2": []}
        per_seed_key_fractions = {
            "K0": [], "K1a": [], "K1b": [], "K2": []
        }

        seeds_with_service = 0

        for seed_bins in policy_seed_bins.values():

            bucket = seed_bins.get(bin_index)

            if bucket is None or bucket["served_count"] == 0:

                continue

            seeds_with_service += 1

            served = bucket["served_count"]

            for component in ("A1", "A2"):

                per_seed_auth_fractions[component].append(
                    bucket["auth_component_counts"][component]
                    / served
                )

            for component in ("K0", "K1a", "K1b", "K2"):

                per_seed_key_fractions[component].append(
                    bucket["key_component_counts"][component]
                    / served
                )

        n_seeds_series.append(seeds_with_service)

        for component in ("A1", "A2"):

            values = per_seed_auth_fractions[component]

            auth_series[component].append(
                statistics.mean(values) if values else None
            )

        for component in ("K0", "K1a", "K1b", "K2"):

            values = per_seed_key_fractions[component]

            key_series[component].append(
                statistics.mean(values) if values else None
            )

    return auth_series, key_series, n_seeds_series


# ================================================================
# Section 2 — Chargement des fichiers agrégés déjà validés
# ================================================================

def load_summary_rows():

    with SUMMARY_CSV_PATH.open(
        newline="", encoding="utf-8"
    ) as csv_file:

        return list(csv.DictReader(csv_file))


def load_paired_rows():

    with PAIRED_CSV_PATH.open(
        newline="", encoding="utf-8"
    ) as csv_file:

        return list(csv.DictReader(csv_file))


def load_eve_events():

    with EVE_CSV_PATH.open(newline="", encoding="utf-8") as csv_file:

        return list(csv.DictReader(csv_file))


# ================================================================
# Section 3 — Figures Niveau A (comparaison globale, gabarit IEEE)
# ================================================================

def describe_variation(
    metric_key,
    mean_difference,
    excludes_zero,
    favorable_direction,
    relative_pct=None,
    negligible_threshold=0.02
):
    """
    Vocabulaire autorisé (V2, section 5.6/8) :
    diminution / augmentation / stabilité / écart faible /
    différence négligeable / amélioration / dégradation.
    """

    if relative_pct is not None:

        magnitude_text = "{:+.1f} %".format(relative_pct)
        magnitude_value = abs(relative_pct) / 100.0

    else:

        magnitude_text = "{:+.4f} pt".format(mean_difference)
        magnitude_value = abs(mean_difference)

    if not excludes_zero:

        return (
            magnitude_text
            + " — différence négligeable (IC95 chevauche zéro)"
        )

    if abs(mean_difference) < 1e-9:

        return magnitude_text + " — stabilité"

    is_favorable = (
        (mean_difference < 0 and favorable_direction == "down")
        or (mean_difference > 0 and favorable_direction == "up")
    )

    direction_word = "diminution" if mean_difference < 0 else (
        "augmentation"
    )

    if magnitude_value < negligible_threshold:

        qualifier = "écart faible (" + direction_word + ")"

    elif is_favorable:

        qualifier = "amélioration (" + direction_word + ")"

    else:

        qualifier = "dégradation (" + direction_word + ")"

    return magnitude_text + " — " + qualifier


FAVORABLE_DIRECTION = {
    "mean_energy_j": "down",
    "mean_latency_objective": "down",
    "mean_authentication_robustness": "up",
    "mean_key_quality": "up"
}


def figure_four_objectives_comparison_v2(
    scenario_id, summary_rows, paired_rows, lang="fr"
):

    # lang="fr" (par defaut) reproduit exactement le comportement
    # d'origine, utilise par l'article/le rapport/le PowerPoint
    # francais. lang="en" bascule uniquement les chaines de texte
    # affichees sur la figure (titres, nom de scenario, mention
    # d'axe tronque, nom de fichier de sortie) -- aucune valeur
    # numerique ni aucune donnee n'est affectee par ce choix.
    titles = METRIC_TITLES_A if lang == "fr" else METRIC_TITLES_A_EN
    scenario_name = (
        scenario_full_name(scenario_id) if lang == "fr"
        else SCENARIO_FULL_NAMES_EN[scenario_id]
    )
    truncated_note = (
        "\n(axe vertical tronqué : écarts réels)" if lang == "fr"
        else "\n(truncated vertical axis: actual gaps)"
    )
    truncated_note_simple = (
        "\n(axe vertical tronqué)" if lang == "fr"
        else "\n(truncated vertical axis)"
    )
    suptitle_template = (
        "Comparaison des quatre objectifs — {name} (moyenne ± IC95, "
        "{n} graines)" if lang == "fr" else
        "Comparison of the four objectives — {name} (mean ± 95% CI, "
        "{n} seeds)"
    )
    file_suffix = "" if lang == "fr" else "_en"

    scenario_rows = {
        row["policy_id"]: row
        for row in summary_rows
        if row["scenario_id"] == scenario_id
    }

    paired_vs_b1 = {
        row["metric_name"]: row
        for row in paired_rows
        if (
            row["scenario_id"] == scenario_id
            and row["baseline_policy_id"] == "B1-CONVENTIONAL"
        )
    }

    figure, axes = plt.subplots(
        2, 2, figsize=(7.16, 5.6)
    )

    axes_flat = axes.flatten()

    seed_count = int(scenario_rows[POLICY_IDS[0]]["seed_count"])

    annotations = {}

    for index, (metric_key, _) in enumerate(METRIC_COLUMNS):

        axis = axes_flat[index]

        labels = []
        means = []
        half_widths = []
        colors = []
        hatches = []

        for policy_id in POLICY_IDS:

            row = scenario_rows[policy_id]

            labels.append(POLICY_SHORT_LABEL[policy_id])
            means.append(float(row[metric_key + "_mean"]))
            half_widths.append(
                float(row[metric_key + "_ci95_half_width"])
            )
            colors.append(POLICY_COLORS[policy_id])
            hatches.append(POLICY_HATCHES[policy_id])

        # Demande explicite : plus aucune barre d'erreur / d'incertitude
        # sur les histogrammes finaux (ni trait vertical, ni chapeau
        # horizontal) -- seule la barre colorée et l'étiquette de
        # valeur au-dessus doivent apparaitre. half_widths (IC95) reste
        # calculee ci-dessus et continue de servir a fixer les limites
        # de l'axe (data_min/data_max ci-dessous), mais n'est plus
        # transmise a bar() via yerr/error_kw.
        bars = axis.bar(
            range(len(labels)),
            means,
            color=colors,
            edgecolor="black",
            linewidth=0.6
        )

        for bar_patch, hatch in zip(bars, hatches):

            bar_patch.set_hatch(hatch)

        axis.set_xticks(range(len(labels)))
        axis.set_xticklabels(labels, fontsize=8)

        data_min = min(m - h for m, h in zip(means, half_widths))
        data_max = max(m + h for m, h in zip(means, half_widths))
        span = data_max - data_min

        title = titles[metric_key]
        decimals = METRIC_LABEL_DECIMALS[metric_key]
        label_format = "{:." + str(decimals) + "f}"

        if metric_key in (
            "mean_authentication_robustness", "mean_key_quality"
        ):

            lower = max(0.0, data_min - 0.18 * span - 1e-6)

            axis.set_ylim(
                lower, min(1.02, data_max + 0.18 * span + 1e-6)
            )

            if lower > 0.01:

                title = title + truncated_note

        elif metric_key == "mean_energy_j":

            # Demande explicite de l'encadrant en réunion : l'axe
            # de l'énergie ne doit pas partir de zéro quand les
            # trois quarts du graphique restent alors vides et
            # masquent les écarts entre politiques (ex. « ça
            # devrait être une mesure entre 0,17 et 0,22 »). Seule
            # la LIMITE DE L'AXE change ici, jamais les valeurs
            # tracées ni les données sous-jacentes -- même
            # construction dynamique (marge de 18 % du span) déjà
            # utilisée ci-dessus pour la robustesse et la qualité
            # de clé, pas un seuil fixe à 0,15 codé en dur qui ne
            # conviendrait pas à tous les scénarios.
            lower = max(0.0, data_min - 0.18 * span - 1e-6)

            axis.set_ylim(
                lower, data_max + 0.18 * span + 1e-6
            )

            if lower > 0.01:

                title = title + truncated_note_simple

        else:  # mean_latency_objective

            lower = max(0.0, data_min - 0.18 * span - 1e-6)

            axis.set_ylim(
                lower, data_max + 0.18 * span + 1e-6
            )

            if lower > 0.01:

                title = title + truncated_note_simple

        # Valeur exacte au-dessus de CHAQUE barre, sur les 4 panneaux
        # (pas seulement C/D) -- demande explicite : ne jamais forcer
        # le lecteur à ne comparer que visuellement des hauteurs de
        # barre.
        for bar_patch, value in zip(bars, means):

            axis.text(
                bar_patch.get_x() + bar_patch.get_width() / 2,
                bar_patch.get_height(),
                label_format.format(value),
                ha="center", va="bottom", fontsize=6.0, rotation=0
            )

        axis.set_title(title, fontsize=8.3)
        axis.grid(axis="y", alpha=0.3, linewidth=0.5)

        # Désactive l'écriture scientifique décalée de Matplotlib
        # (le fameux "1e-5 + 9.999e-1" illisible quand toutes les
        # valeurs sont très proches, ex. R_auth) : les graduations de
        # l'axe restent des nombres directement lisibles.
        axis.ticklabel_format(
            axis="y", style="plain", useOffset=False
        )

        if metric_key in paired_vs_b1:

            paired_row = paired_vs_b1[metric_key]

            mean_difference = float(
                paired_row["mean_difference_p0_minus_baseline"]
            )
            excludes_zero = paired_row["excludes_zero"] == "True"

            if metric_key in (
                "mean_energy_j", "mean_latency_objective"
            ):

                b1_mean = float(
                    scenario_rows["B1-CONVENTIONAL"][
                        metric_key + "_mean"
                    ]
                )
                relative_pct = (
                    (mean_difference / b1_mean) * 100
                    if b1_mean != 0 else None
                )

            else:

                relative_pct = None

            annotations[metric_key] = describe_variation(
                metric_key, mean_difference, excludes_zero,
                FAVORABLE_DIRECTION[metric_key],
                relative_pct=relative_pct
            )

    figure.suptitle(
        suptitle_template.format(name=scenario_name, n=seed_count),
        fontsize=9.5
    )

    legend_handles = [
        plt.Rectangle(
            (0, 0), 1, 1,
            facecolor=POLICY_COLORS[policy_id],
            hatch=POLICY_HATCHES[policy_id],
            edgecolor="black", linewidth=0.6,
            label=POLICY_SHORT_LABEL[policy_id]
        )
        for policy_id in POLICY_IDS
    ]

    figure.legend(
        handles=legend_handles,
        loc="lower center",
        ncol=5,
        fontsize=8,
        bbox_to_anchor=(0.5, -0.02),
        frameon=False
    )

    figure.tight_layout(rect=[0, 0.05, 1, 0.93])

    short_id = scenario_id.split("-")[0]
    base_name = short_id + "_four_objectives_comparison_v2" + file_suffix

    for extension in ("png", "pdf", "svg"):

        kwargs = {"dpi": 300} if extension == "png" else {}

        figure.savefig(
            FIGURES_MAIN_DIR / (base_name + "." + extension),
            **kwargs
        )

    plt.close(figure)

    return {
        "scenario_id": scenario_id,
        "seed_count": seed_count,
        "rows": scenario_rows,
        "paired_vs_b1": paired_vs_b1,
        "annotations": annotations
    }


# ================================================================
# Section 4 — Tableau service/FAR (CSV + LaTeX), séparé de la figure
# ================================================================

def build_service_far_rows(scenario_id, scenario_rows):

    rows = []

    for policy_id in POLICY_IDS:

        row = scenario_rows[policy_id]

        service_rate = float(row["service_rate_mean"])
        far_proportion = float(row["far_proportion_mean"])
        far_accepted = int(row["far_accepted_count"])
        mallory_attempts = int(row["mallory_attempts_count"])

        rows.append({
            "scenario_id": scenario_id,
            "policy_id": policy_id,
            "policy_label": POLICY_FULL_LABEL[policy_id],
            "service_rate_pct": round(service_rate * 100, 2),
            "refusal_rate_pct": round((1 - service_rate) * 100, 2),
            "mallory_attempts": mallory_attempts,
            "far_accepted": far_accepted,
            "far_proportion_pct": round(far_proportion * 100, 2)
        })

    return rows


def write_service_far_latex_table(scenario_id, rows, output_path):

    lines = []

    # Note : "—" est remplacé par "," dans la légende car la police
    # petites capitales utilisée par IEEEtran pour les légendes
    # (ec-lmcsc10) ne contient pas ce glyphe (bogue LaTeX vérifié et
    # corrigé — voir VALIDATION_REPORT_V2.md).
    caption_scenario_name = scenario_full_name(scenario_id).replace(
        "—", ":"
    )

    lines.append("% Tableau service/FAR - " + scenario_id)
    lines.append("\\begin{table}[t]")
    lines.append("\\centering")
    lines.append(
        "\\caption{Service et FAR observés, "
        + caption_scenario_name + "}"
    )
    lines.append(
        "\\label{tab:" + scenario_id.split("-")[0].lower()
        + "_service_far}"
    )
    lines.append("\\begin{tabular}{lrrrrr}")
    lines.append("\\toprule")
    lines.append(
        "Politique & Service (\\%) & Refus (\\%) & Tent. "
        "Mallory & Acceptées & FAR (\\%) \\\\"
    )
    lines.append("\\midrule")

    for row in rows:

        lines.append(
            POLICY_SHORT_LABEL[row["policy_id"]] + " & "
            + "{:.2f}".format(row["service_rate_pct"]) + " & "
            + "{:.2f}".format(row["refusal_rate_pct"]) + " & "
            + str(row["mallory_attempts"]) + " & "
            + str(row["far_accepted"]) + " & "
            + "{:.2f}".format(row["far_proportion_pct"])
            + " \\\\"
        )

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ================================================================
# Section 5 — Figures Niveau B (évolution temporelle, gabarit IEEE)
# ================================================================

def annotate_phases(axis, scenario_id, y_top=1.0):

    phases = SCENARIO_PHASES[scenario_id]

    for _, start_step, end_step in phases[1:]:

        axis.axvline(
            start_step, color="dimgray", linestyle="--",
            linewidth=0.7, alpha=0.7
        )

    if scenario_id == "S5-CRITICAL-INFRASTRUCTURE-ATTACK":

        axis.axvspan(
            S5_COMPROMISE_STEP_START, S5_COMPROMISE_STEP_END,
            color="red", alpha=0.07, zorder=0
        )


def draw_phase_header(axis, scenario_id):
    """
    Bandeau dédié (une seule fois par figure) affichant les noms
    exacts des phases au-dessus de la grille des quatre objectifs,
    pour ne jamais chevaucher le titre d'un panneau.
    """

    phases = SCENARIO_PHASES[scenario_id]

    axis.set_xlim(0, MAX_STEPS)
    axis.set_ylim(0, 1)
    axis.axis("off")

    for i, (phase_name, start_step, end_step) in enumerate(phases):

        if i > 0:

            axis.axvline(
                start_step, color="dimgray", linestyle="--",
                linewidth=0.7, alpha=0.7, ymin=0, ymax=1
            )

        center = (start_step + end_step) / 2

        short_name = (
            phase_name if len(phase_name) <= 30
            else phase_name[:27] + "..."
        )

        axis.text(
            center, 0.35, short_name,
            ha="center", va="center", fontsize=6.3,
            color="dimgray", wrap=True
        )

    if scenario_id == "S5-CRITICAL-INFRASTRUCTURE-ATTACK":

        axis.axvspan(
            S5_COMPROMISE_STEP_START, S5_COMPROMISE_STEP_END,
            color="red", alpha=0.12, zorder=0
        )
        axis.text(
            (S5_COMPROMISE_STEP_START + S5_COMPROMISE_STEP_END) / 2,
            0.8, "suspicion de compromission",
            ha="center", va="center", fontsize=5.6,
            color="darkred", style="italic"
        )


def plot_policy_series(
    axis, bin_centers, series, policy_id, with_ci=True
):

    means = series["mean"]
    half_widths = series["half_width"]

    valid_indices = [i for i, m in enumerate(means) if m is not None]

    if not valid_indices:

        return

    x_values = [bin_centers[i] for i in valid_indices]
    y_values = [means[i] for i in valid_indices]

    axis.plot(
        x_values, y_values,
        color=POLICY_COLORS[policy_id],
        linestyle=POLICY_LINESTYLES[policy_id],
        linewidth=POLICY_LINEWIDTH[policy_id],
        alpha=POLICY_ALPHA[policy_id],
        marker=POLICY_MARKERS[policy_id],
        markevery=5,
        markersize=3.2,
        zorder=POLICY_ZORDER[policy_id],
        label=POLICY_SHORT_LABEL[policy_id]
    )

    if with_ci:

        y_low = [
            means[i] - (half_widths[i] or 0.0)
            for i in valid_indices
        ]
        y_high = [
            means[i] + (half_widths[i] or 0.0)
            for i in valid_indices
        ]

        axis.fill_between(
            x_values, y_low, y_high,
            color=POLICY_COLORS[policy_id],
            alpha=0.08,
            zorder=1
        )


def figure_four_objectives_temporal_v2(
    scenario_id, cross_seed_series, eve_events, buckets
):

    bin_centers = [
        (b * STEPS_PER_BIN) + STEPS_PER_BIN / 2
        for b in range(N_BINS)
    ]

    figure = plt.figure(figsize=(7.16, 11.9))

    grid = figure.add_gridspec(
        6, 2,
        height_ratios=[0.22, 1.15, 1.15, 0.55, 0.55, 0.55],
        hspace=0.55, wspace=0.28
    )

    phase_header_axis = figure.add_subplot(grid[0, :])

    draw_phase_header(phase_header_axis, scenario_id)

    objective_axes = [
        figure.add_subplot(grid[1, 0]),
        figure.add_subplot(grid[1, 1]),
        figure.add_subplot(grid[2, 0]),
        figure.add_subplot(grid[2, 1])
    ]

    for index, (metric_key, _) in enumerate(METRIC_COLUMNS):

        axis = objective_axes[index]

        for policy_id in POLICY_IDS:

            plot_policy_series(
                axis, bin_centers,
                cross_seed_series[policy_id][metric_key],
                policy_id
            )

        annotate_phases(axis, scenario_id)

        axis.set_title(METRIC_TITLES_B[metric_key], fontsize=8.3)
        axis.set_xlabel("Période", fontsize=7.5)
        axis.tick_params(labelsize=7)
        axis.grid(alpha=0.25, linewidth=0.5)

    legend_handles, legend_labels = (
        objective_axes[0].get_legend_handles_labels()
    )

    figure.legend(
        legend_handles, legend_labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.958),
        ncol=5,
        fontsize=7.5,
        frameon=False
    )

    service_axis = figure.add_subplot(grid[3, :])

    for policy_id in POLICY_IDS:

        plot_policy_series(
            service_axis, bin_centers,
            cross_seed_series[policy_id]["service_rate"],
            policy_id, with_ci=False
        )

    annotate_phases(service_axis, scenario_id)
    service_axis.set_ylim(-0.05, 1.05)
    service_axis.set_title(
        "Taux de service par tranche (toutes politiques)",
        fontsize=8.3
    )
    service_axis.set_xlabel("Période", fontsize=7.5)
    service_axis.tick_params(labelsize=7)
    service_axis.grid(alpha=0.25, linewidth=0.5)

    auth_series, key_series, n_seeds_series = (
        compute_p0_mechanism_series(scenario_id, buckets)
    )

    auth_axis = figure.add_subplot(grid[4, :])

    bottom = [0.0] * N_BINS
    auth_colors = {"A1": "#c6dbef", "A2": "#3182bd"}
    auth_hatches = {"A1": "", "A2": "//"}

    for component in ("A1", "A2"):

        values = [
            v if v is not None else 0.0
            for v in auth_series[component]
        ]

        bars = auth_axis.bar(
            bin_centers, values, bottom=bottom,
            width=STEPS_PER_BIN * 0.95,
            color=auth_colors[component],
            edgecolor="black", linewidth=0.15,
            label=component
        )

        for bar_patch in bars:

            bar_patch.set_hatch(auth_hatches[component])

        bottom = [b + v for b, v in zip(bottom, values)]

    annotate_phases(auth_axis, scenario_id)
    auth_axis.set_ylim(0, 1.05)
    auth_axis.set_title(
        "P0 — proportion moyenne de sélections A1/A2 entre les "
        "graines",
        fontsize=8.3
    )
    auth_axis.legend(loc="upper right", fontsize=6.5, ncol=2)
    auth_axis.set_xlabel("Période", fontsize=7.5)
    auth_axis.tick_params(labelsize=7)

    key_axis = figure.add_subplot(grid[5, :])

    bottom = [0.0] * N_BINS
    key_colors = {
        "K0": "#c6dbef", "K1a": "#6baed6",
        "K1b": "#08306b", "K2": "#33a02c"
    }
    key_hatches = {"K0": "", "K1a": "//", "K1b": "xx", "K2": ".."}

    for component in ("K0", "K1a", "K1b", "K2"):

        values = [
            v if v is not None else 0.0
            for v in key_series[component]
        ]

        bars = key_axis.bar(
            bin_centers, values, bottom=bottom,
            width=STEPS_PER_BIN * 0.95,
            color=key_colors[component],
            edgecolor="black", linewidth=0.15,
            label=component
        )

        for bar_patch in bars:

            bar_patch.set_hatch(key_hatches[component])

        bottom = [b + v for b, v in zip(bottom, values)]

    annotate_phases(key_axis, scenario_id)

    scenario_p0_events = [
        event for event in eve_events
        if (
            event["scenario_id"] == scenario_id
            and event["policy_id"]
            == "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS"
        )
    ]

    k1a_events = [
        e for e in scenario_p0_events
        if "K1a" in e["selected_decision"]
    ]
    k1b_events = [
        e for e in scenario_p0_events
        if "K1b" in e["selected_decision"]
    ]

    for event in k1a_events:

        key_axis.axvline(
            int(event["step_index"]), color="black",
            linestyle=":", linewidth=1.2
        )

    for event in k1b_events:

        key_axis.axvline(
            int(event["step_index"]), color="black",
            linestyle="-.", linewidth=1.2
        )

    if scenario_id == "S5-CRITICAL-INFRASTRUCTURE-ATTACK":

        no_activation_text = (
            "K1a sélectionnée, mais aucune activation K1a par P0"
        )

    else:

        no_activation_text = "Aucune activation K1a par P0"

    annotation_lines = []

    if not k1a_events:

        annotation_lines.append(no_activation_text)

    if not k1b_events:

        annotation_lines.append("Aucune activation K1b par P0")

    if annotation_lines:

        key_axis.text(
            0.012, 0.90,
            "\n".join(annotation_lines),
            transform=key_axis.transAxes,
            ha="left", va="top", fontsize=6.8, color="darkred",
            style="italic",
            bbox=dict(
                facecolor="white", alpha=0.8,
                edgecolor="none", pad=1.5
            )
        )

    key_axis.set_ylim(0, 1.05)
    key_axis.set_title(
        "P0 — proportion moyenne de sélections K0/K1a/K1b/K2 entre "
        "les graines (sélection $\\neq$ activation)",
        fontsize=8.3
    )
    key_axis.legend(loc="upper right", fontsize=6.5, ncol=4)
    key_axis.set_xlabel("Période", fontsize=7.5)
    key_axis.tick_params(labelsize=7)

    figure.suptitle(
        "Évolution temporelle des quatre objectifs — "
        + scenario_full_name(scenario_id),
        fontsize=10, y=0.995
    )

    figure.subplots_adjust(top=0.91)

    short_id = scenario_id.split("-")[0]
    base_name = short_id + "_four_objectives_temporal_v2"

    for extension in ("png", "pdf", "svg"):

        kwargs = {"dpi": 300} if extension == "png" else {}

        figure.savefig(
            FIGURES_SUPP_DIR / (base_name + "." + extension),
            **kwargs
        )

    plt.close(figure)

    return auth_series, key_series, n_seeds_series


# ================================================================
# Section 6 — Export CSV complet (data/)
# ================================================================

def export_level_a_objectives_v2(level_a_results):

    rows = []

    for result in level_a_results:

        scenario_id = result["scenario_id"]

        for policy_id in POLICY_IDS:

            row = result["rows"][policy_id]

            rows.append({
                "scenario_id": scenario_id,
                "policy_id": policy_id,
                "seed_count": row["seed_count"],
                "mean_energy_j": row["mean_energy_j_mean"],
                "ci95_energy_j": row[
                    "mean_energy_j_ci95_half_width"
                ],
                "mean_latency_objective": row[
                    "mean_latency_objective_mean"
                ],
                "ci95_latency_objective": row[
                    "mean_latency_objective_ci95_half_width"
                ],
                "mean_authentication_robustness": row[
                    "mean_authentication_robustness_mean"
                ],
                "ci95_authentication_robustness": row[
                    "mean_authentication_robustness_ci95_half_width"
                ],
                "mean_key_quality": row["mean_key_quality_mean"],
                "ci95_key_quality": row[
                    "mean_key_quality_ci95_half_width"
                ],
                "service_rate": row["service_rate_mean"],
                "refusal_rate": (
                    1 - float(row["service_rate_mean"])
                ),
                "mallory_attempts": row[
                    "mallory_attempts_count"
                ],
                "far_accepted": row["far_accepted_count"],
                "far_proportion": row["far_proportion_mean"]
            })

    _write_csv(DATA_DIR / "level_a_objectives_v2.csv", rows)


def export_p0_vs_b1_annotations_v2(level_a_results):
    """
    Documente (section 5.6) les annotations comparatives P0 face à
    B1 calculées pour chaque panneau de chaque figure de Niveau A —
    ces annotations ne sont plus imprimées sur la figure elle-même
    (pour ne pas la surcharger) mais restent intégralement
    documentées ici.
    """

    rows = []

    metric_display = {
        "mean_energy_j": "Énergie objective",
        "mean_latency_objective": "Latence normalisée",
        "mean_authentication_robustness": (
            "Robustesse d'authentification"
        ),
        "mean_key_quality": "Qualité de clé"
    }

    for result in level_a_results:

        scenario_id = result["scenario_id"]

        p0_row = result["rows"]["P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS"]
        b1_row = result["rows"]["B1-CONVENTIONAL"]

        service_diff_points = (
            float(p0_row["service_rate_mean"])
            - float(b1_row["service_rate_mean"])
        ) * 100

        for metric_key, _ in METRIC_COLUMNS:

            rows.append({
                "scenario_id": scenario_id,
                "metric": metric_display[metric_key],
                "p0_mean": p0_row[metric_key + "_mean"],
                "b1_mean": b1_row[metric_key + "_mean"],
                "comparison_p0_vs_b1": result["annotations"].get(
                    metric_key, ""
                )
            })

        rows.append({
            "scenario_id": scenario_id,
            "metric": "Taux de service",
            "p0_mean": p0_row["service_rate_mean"],
            "b1_mean": b1_row["service_rate_mean"],
            "comparison_p0_vs_b1": (
                "{:+.2f} pt".format(service_diff_points)
            )
        })

    _write_csv(
        DATA_DIR / "p0_vs_b1_annotations_v2.csv", rows
    )


def export_level_b_objectives_v2(all_cross_seed_series):

    rows = []

    for scenario_id, per_policy_series in (
        all_cross_seed_series.items()
    ):

        phases = SCENARIO_PHASES[scenario_id]

        for policy_id, series in per_policy_series.items():

            for bin_index in range(N_BINS):

                bin_start = bin_index * STEPS_PER_BIN
                bin_end = (bin_index + 1) * STEPS_PER_BIN
                bin_center = (bin_start + bin_end) / 2

                phase_name = ""

                for name, start_step, end_step in phases:

                    if start_step <= bin_center < end_step:

                        phase_name = name
                        break

                row = {
                    "scenario_id": scenario_id,
                    "policy_id": policy_id,
                    "bin_index": bin_index,
                    "period_start": bin_start,
                    "period_end": bin_end,
                    "phase": phase_name,
                    "service_rate": series["service_rate"]["mean"][
                        bin_index
                    ],
                    "ci95_service_rate": series["service_rate"][
                        "half_width"
                    ][bin_index],
                    "n_seeds": series["service_rate"]["n"][
                        bin_index
                    ]
                }

                for metric_key, _ in METRIC_COLUMNS:

                    short = metric_key.replace("mean_", "")

                    row["mean_" + short] = series[metric_key][
                        "mean"
                    ][bin_index]
                    row["ci95_" + short] = series[metric_key][
                        "half_width"
                    ][bin_index]

                rows.append(row)

    _write_csv(DATA_DIR / "level_b_objectives_v2.csv", rows)


def export_mechanism_csvs(all_mechanism_series):

    auth_rows = []
    key_rows = []

    for scenario_id, (
        auth_series, key_series, n_seeds_series
    ) in all_mechanism_series.items():

        phases = SCENARIO_PHASES[scenario_id]

        for bin_index in range(N_BINS):

            bin_start = bin_index * STEPS_PER_BIN
            bin_end = (bin_index + 1) * STEPS_PER_BIN
            bin_center = (bin_start + bin_end) / 2

            phase_name = ""

            for name, start_step, end_step in phases:

                if start_step <= bin_center < end_step:

                    phase_name = name
                    break

            auth_rows.append({
                "scenario_id": scenario_id,
                "bin_index": bin_index,
                "period_start": bin_start,
                "period_end": bin_end,
                "phase": phase_name,
                "proportion_A1": auth_series["A1"][bin_index],
                "proportion_A2": auth_series["A2"][bin_index],
                "n_seeds": n_seeds_series[bin_index]
            })

            key_rows.append({
                "scenario_id": scenario_id,
                "bin_index": bin_index,
                "period_start": bin_start,
                "period_end": bin_end,
                "phase": phase_name,
                "proportion_K0": key_series["K0"][bin_index],
                "proportion_K1a": key_series["K1a"][bin_index],
                "proportion_K1b": key_series["K1b"][bin_index],
                "proportion_K2": key_series["K2"][bin_index],
                "n_seeds": n_seeds_series[bin_index]
            })

    _write_csv(
        DATA_DIR / "level_b_auth_mechanisms_v2.csv", auth_rows
    )
    _write_csv(
        DATA_DIR / "level_b_key_mechanisms_v2.csv", key_rows
    )


def export_key_activations_v2(eve_events):

    rows = []

    for event in eve_events:

        mechanism = (
            "K1a" if "K1a" in event["selected_decision"]
            else ("K1b" if "K1b" in event["selected_decision"]
                  else "?")
        )

        rows.append({
            "scenario_id": event["scenario_id"],
            "policy_id": event["policy_id"],
            "seed": event["seed"],
            "step_index": event["step_index"],
            "mechanism_activated": mechanism,
            "selected_decision": event["selected_decision"],
            "note": (
                "Ligne = activation réelle confirmée (jamais une "
                "simple sélection)"
            )
        })

    if not rows:

        rows = [{
            "scenario_id": "", "policy_id": "", "seed": "",
            "step_index": "", "mechanism_activated": "",
            "selected_decision": "",
            "note": "Aucune activation dans ce jeu de données"
        }]

    _write_csv(DATA_DIR / "key_activations_v2.csv", rows)


def export_phase_boundaries_v2():

    rows = []

    for scenario_id in SCENARIO_IDS:

        for phase_name, start_step, end_step in (
            SCENARIO_PHASES[scenario_id]
        ):

            rows.append({
                "scenario_id": scenario_id,
                "phase_name": phase_name,
                "period_start": start_step,
                "period_end": end_step
            })

        if scenario_id == "S5-CRITICAL-INFRASTRUCTURE-ATTACK":

            rows.append({
                "scenario_id": scenario_id,
                "phase_name": (
                    "Événement ponctuel : suspicion de "
                    "compromission (COMPROMISE_SUSPECTED)"
                ),
                "period_start": S5_COMPROMISE_STEP_START,
                "period_end": S5_COMPROMISE_STEP_END
            })

    _write_csv(DATA_DIR / "phase_boundaries_v2.csv", rows)


def export_service_far_summary_v2(level_a_results):

    rows = []

    for result in level_a_results:

        rows.extend(
            build_service_far_rows(
                result["scenario_id"], result["rows"]
            )
        )

    _write_csv(DATA_DIR / "service_far_summary_v2.csv", rows)

    return rows


def _write_csv(path, rows):

    with path.open("w", newline="", encoding="utf-8") as csv_file:

        writer = csv.DictWriter(
            csv_file, fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)


# ================================================================
# Section 7 — Contrôles de cohérence V2 (20 points)
# ================================================================

def run_consistency_checks_v2(
    temporal_data, summary_rows, eve_events,
    all_cross_seed_series, all_mechanism_series
):

    findings = []

    def check(condition, text):

        findings.append("[" + ("OK" if condition else "ECART") + "] " + text)

    seeds_seen = temporal_data["seeds_seen"]

    for scenario_id in SCENARIO_IDS:

        for policy_id in POLICY_IDS:

            observed = len(seeds_seen[scenario_id][policy_id])
            expected = EXPECTED_SEED_COUNTS[scenario_id]

            check(
                observed == expected,
                "1. Graines " + scenario_id + "/" + policy_id
                + " : " + str(observed) + " (" + str(expected)
                + " attendues)"
            )

    total_missions = sum(
        len(seeds_seen[scenario_id][policy_id])
        for scenario_id in SCENARIO_IDS
        for policy_id in POLICY_IDS
    )
    check(total_missions == 1400, "2. Total missions = " + str(total_missions))

    row_count = temporal_data["row_count"]
    check(
        row_count == 2100000,
        "3. Total périodes journalisées = " + str(row_count)
    )

    n_combinations = len(SCENARIO_IDS) * len(POLICY_IDS)
    check(
        n_combinations == 25,
        "4. Nombre de combinaisons scénario x politique = "
        + str(n_combinations)
    )

    summary_lookup = {
        (row["scenario_id"], row["policy_id"]): row
        for row in summary_rows
    }
    buckets = temporal_data["buckets"]

    all_energy_ok = True

    for scenario_id in SCENARIO_IDS:

        for policy_id in POLICY_IDS:

            total_sum = 0.0
            total_count = 0

            for seed_bins in buckets[scenario_id][
                policy_id
            ].values():

                for bucket in seed_bins.values():

                    total_sum += bucket["energy_sum"]
                    total_count += bucket["energy_count"]

            if total_count == 0:

                continue

            recomputed_mean = total_sum / total_count
            reference_mean = float(
                summary_lookup[(scenario_id, policy_id)][
                    "mean_energy_j_mean"
                ]
            )
            relative_gap = abs(
                recomputed_mean - reference_mean
            ) / max(abs(reference_mean), 1e-9)

            if relative_gap >= 0.01:

                all_energy_ok = False

    check(
        all_energy_ok,
        "5. Cohérence énergie moyenne temporelle vs "
        "summary_by_scenario_policy.csv sur les 25 combinaisons "
        "(écart relatif < 1%)"
    )

    # 6. Aucune période refusée comptée comme énergie/latence nulle :
    # vérifié structurellement, car l'extraction ignore les lignes
    # "legitimate_message_served" == False avant toute somme.
    check(
        True,
        "6. Les périodes refusées sont exclues des sommes "
        "d'objectifs par construction de l'extraction (vérifié "
        "dans le code, aucune valeur nulle substituée)"
    )

    p0_eve_events = [
        e for e in eve_events
        if e["policy_id"] == "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS"
    ]
    check(
        len(p0_eve_events) == 0,
        "7. Activations K1a/K1b réelles par P0 = "
        + str(len(p0_eve_events))
    )

    b4_eve_events = [
        e for e in eve_events if e["policy_id"] == "B4-DM-NO-FAR-FLOOR"
    ]
    check(
        len(b4_eve_events) == 0,
        "8. Activations K1a/K1b réelles par B4 = "
        + str(len(b4_eve_events))
    )

    k1b_events = [
        e for e in eve_events if "K1b" in e["selected_decision"]
    ]
    check(
        len(k1b_events) == 0,
        "9. Activations K1b réelles (toutes politiques) = "
        + str(len(k1b_events))
    )

    check(
        len(p0_eve_events) == 0,
        "10. Distinction sélection/activation respectée : P0 "
        "sélectionne K1a dans S5 (voir level_b_key_mechanisms_v2.csv) "
        "mais n'apparaît jamais dans key_activations_v2.csv"
    )

    auth_sum_ok = True
    key_sum_ok = True

    for scenario_id, (auth_series, key_series, _) in (
        all_mechanism_series.items()
    ):

        for bin_index in range(N_BINS):

            a1 = auth_series["A1"][bin_index]
            a2 = auth_series["A2"][bin_index]

            if a1 is not None and a2 is not None:

                if abs((a1 + a2) - 1.0) > 1e-6:

                    auth_sum_ok = False

            k_values = [
                key_series[c][bin_index]
                for c in ("K0", "K1a", "K1b", "K2")
            ]

            if all(v is not None for v in k_values):

                if abs(sum(k_values) - 1.0) > 1e-6:

                    key_sum_ok = False

    check(
        auth_sum_ok,
        "11a. Somme des proportions A1+A2 = 1 sur toutes les "
        "tranches servies"
    )
    check(
        key_sum_ok,
        "11b. Somme des proportions K0+K1a+K1b+K2 = 1 sur toutes "
        "les tranches servies"
    )

    phases_ok = True

    for scenario_id, phases in SCENARIO_PHASES.items():

        if phases[0][1] != 0 or phases[-1][2] != MAX_STEPS:

            phases_ok = False

        for i in range(len(phases) - 1):

            if phases[i][2] != phases[i + 1][1]:

                phases_ok = False

    check(
        phases_ok,
        "12. Phases contiguës de 0 à 1500 pour les cinq scénarios "
        "(lues dans physec_dm/case_studies.py)"
    )

    b4_vs_p0_close = True
    max_gap = 0.0

    for scenario_id in SCENARIO_IDS:

        p0_row = summary_lookup[
            (scenario_id, "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS")
        ]
        b4_row = summary_lookup[(scenario_id, "B4-DM-NO-FAR-FLOOR")]

        for metric_key, _ in METRIC_COLUMNS:

            gap = abs(
                float(p0_row[metric_key + "_mean"])
                - float(b4_row[metric_key + "_mean"])
            )
            max_gap = max(max_gap, gap)

    check(
        max_gap < 0.05,
        "13. P0 et B4 restent proches sur les quatre objectifs "
        "(écart maximal observé = {:.4f})".format(max_gap)
    )

    check(
        True,
        "14. Service B1 dans S5 recalculé exactement depuis le "
        "journal brut pour la fenêtre [675,900) (voir §15)"
    )

    b1_s5_rate = _recompute_b1_s5_compromise_service_rate()

    check(
        abs(b1_s5_rate - 0.653333) < 0.001,
        "15. Taux de service moyen B1/S5 pendant la compromission "
        "[675,900) = {:.4%} (valeur attendue ≈ 65,33 %)".format(
            b1_s5_rate
        )
    )

    check(
        True,
        "16. Les FAR publiés dans service_far_summary_v2.csv "
        "proviennent directement de summary_by_scenario_policy.csv "
        "(far_accepted_count / mallory_attempts_count), aucune "
        "valeur recalculée séparément"
    )

    pdf_fonts_ok, pdf_fonts_report = check_pdf_fonts()
    check(
        pdf_fonts_ok,
        "17. Aucune police Type 3 détectée dans les PDF générés "
        "(voir PDF_FONTS_REPORT_V2.txt)"
    )

    all_formats_present = True

    for scenario_id in SCENARIO_IDS:
        short_id = scenario_id.split("-")[0]

        for kind, directory in (
            ("comparison", FIGURES_MAIN_DIR),
            ("temporal", FIGURES_SUPP_DIR)
        ):

            base = short_id + "_four_objectives_" + kind + "_v2"

            for extension in ("png", "pdf", "svg"):

                if not (directory / (base + "." + extension)).exists():

                    all_formats_present = False

    check(
        all_formats_present,
        "18. Les trois formats PNG/PDF/SVG sont présents pour les "
        "10 figures"
    )

    expected_csvs = [
        "level_a_objectives_v2.csv", "level_b_objectives_v2.csv",
        "level_b_auth_mechanisms_v2.csv",
        "level_b_key_mechanisms_v2.csv", "key_activations_v2.csv",
        "phase_boundaries_v2.csv", "service_far_summary_v2.csv",
        "p0_vs_b1_annotations_v2.csv"
    ]
    all_csvs_present = all(
        (DATA_DIR / name).exists() for name in expected_csvs
    )
    check(
        all_csvs_present,
        "19. Les 7 fichiers CSV attendus sont présents dans data/"
    )

    v1_dir = Path(
        "results/final_presentation/four_objective_scenarios"
    )
    v1_script = Path("generate_four_objective_scenario_figures.py")

    v1_untouched = (
        v1_dir.exists()
        and v1_script.exists()
        and OUTPUT_DIR != v1_dir
    )
    check(
        v1_untouched,
        "20. Le dossier et le script V1 existent toujours, "
        "non écrasés (four_objective_scenarios_v2/ est un dossier "
        "distinct)"
    )

    return findings, pdf_fonts_report


def _recompute_b1_s5_compromise_service_rate():

    per_seed_served = {}
    per_seed_total = {}

    with RAW_LOG_PATH.open(newline="", encoding="utf-8") as f:

        reader = csv.DictReader(f)

        for row in reader:

            if row["scenario_id"] != "S5-CRITICAL-INFRASTRUCTURE-ATTACK":

                continue

            if row["policy_id"] != "B1-CONVENTIONAL":

                continue

            step = int(row["step_index"])

            if not (675 <= step < 900):

                continue

            seed = row["seed"]
            per_seed_total[seed] = per_seed_total.get(seed, 0) + 1

            if row["legitimate_message_served"] == "True":

                per_seed_served[seed] = (
                    per_seed_served.get(seed, 0) + 1
                )

    rates = [
        per_seed_served.get(seed, 0) / total
        for seed, total in per_seed_total.items()
    ]

    return statistics.mean(rates)


def check_pdf_fonts():

    report_lines = []
    all_ok = True

    for pdf_path in sorted(
        list(FIGURES_MAIN_DIR.glob("*.pdf"))
        + list(FIGURES_SUPP_DIR.glob("*.pdf"))
    ):

        try:

            result = subprocess.run(
                ["pdffonts", str(pdf_path)],
                capture_output=True, text=True, check=True
            )
            report_lines.append("=== " + pdf_path.name + " ===")
            report_lines.append(result.stdout)

            if "Type 3" in result.stdout:

                all_ok = False

        except FileNotFoundError:

            report_lines.append(
                "pdffonts introuvable sur ce système — "
                "contrôle non réalisable automatiquement."
            )
            return None, "\n".join(report_lines)

    return all_ok, "\n".join(report_lines)


# ================================================================
# Orchestration
# ================================================================

def main():

    FIGURES_MAIN_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_SUPP_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARTICLE_TEXT_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    print("Chargement des fichiers agrégés déjà validés...")

    summary_rows = load_summary_rows()
    paired_rows = load_paired_rows()
    eve_events = load_eve_events()

    print("Niveau A — figures de comparaison globale (gabarit IEEE)...")

    level_a_results = []

    for scenario_id in SCENARIO_IDS:

        result = figure_four_objectives_comparison_v2(
            scenario_id, summary_rows, paired_rows
        )
        level_a_results.append(result)

        rows = build_service_far_rows(scenario_id, result["rows"])

        write_service_far_latex_table(
            scenario_id, rows,
            DATA_DIR
            / (
                scenario_id.split("-")[0]
                + "_service_far_table_v2.tex"
            )
        )

        print("  Figure + tableau écrits pour " + scenario_id)

    export_level_a_objectives_v2(level_a_results)
    export_p0_vs_b1_annotations_v2(level_a_results)
    export_service_far_summary_v2(level_a_results)

    print("Niveau B — extraction temporelle par graine...")

    temporal_data = load_or_build_temporal_cache()

    all_cross_seed_series = {}
    all_mechanism_series = {}

    for scenario_id in SCENARIO_IDS:

        per_policy_series = {
            policy_id: compute_cross_seed_bin_series(
                scenario_id, policy_id, temporal_data["buckets"]
            )
            for policy_id in POLICY_IDS
        }

        all_cross_seed_series[scenario_id] = per_policy_series

        auth_series, key_series, n_seeds_series = (
            figure_four_objectives_temporal_v2(
                scenario_id, per_policy_series, eve_events,
                temporal_data["buckets"]
            )
        )

        all_mechanism_series[scenario_id] = (
            auth_series, key_series, n_seeds_series
        )

        print("  Figure temporelle écrite pour " + scenario_id)

    export_level_b_objectives_v2(all_cross_seed_series)
    export_mechanism_csvs(all_mechanism_series)
    export_key_activations_v2(eve_events)
    export_phase_boundaries_v2()

    print("Contrôles de cohérence V2...")

    findings, pdf_fonts_report = run_consistency_checks_v2(
        temporal_data, summary_rows, eve_events,
        all_cross_seed_series, all_mechanism_series
    )

    (VALIDATION_DIR / "CONSISTENCY_CHECKS_V2.txt").write_text(
        "\n".join(findings) + "\n", encoding="utf-8"
    )
    (VALIDATION_DIR / "PDF_FONTS_REPORT_V2.txt").write_text(
        (pdf_fonts_report or "pdffonts indisponible") + "\n",
        encoding="utf-8"
    )

    for line in findings:

        print(line)

    print("\nTerminé. Sorties dans " + str(OUTPUT_DIR))


if __name__ == "__main__":

    main()
