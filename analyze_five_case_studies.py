# Ce module prépare les fonctions de figure pour les cinq cas
# d'étude dynamiques (physec_dm/case_studies.py). Il ne relance
# aucune mission : il lit uniquement le journal CSV déjà produit
# par run_five_case_studies.py
# (results/five_case_studies_validation/five_case_studies_log.csv
# ou results/five_case_studies/five_case_studies_log.csv pour la
# campagne complète).
#
# Chaque fonction produit UNE figure et l'enregistre en PNG.
# Les scénarios et les phases sont toujours désignés par leur
# nom complet (case_study["scenario_name"] / phase["phase_name"]),
# jamais par leur seul identifiant technique.
import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from physec_dm.key_generation import (
    calculate_reconciliation_yield,
    calculate_required_measurements
)


# Noms complets exigés pour l'affichage (section 6 de la
# demande) : toujours affichés à proximité de l'identifiant
# technique, jamais l'identifiant seul.
SCENARIO_FULL_NAMES = {
    "S1-REMOTE-AGRICULTURAL-SENSOR": (
        "S1 — Capteur agricole isolé"
    ),
    "S2-INDUSTRIAL-CRITICAL-ALARM": (
        "S2 — Alarme critique industrielle"
    ),
    "S3-MOBILE-VEHICLE": (
        "S3 — Objet mobile sur véhicule"
    ),
    "S4-DENSE-URBAN-NETWORK": (
        "S4 — Réseau urbain dense"
    ),
    "S5-CRITICAL-INFRASTRUCTURE-ATTACK": (
        "S5 — Infrastructure critique sous attaque"
    )
}

# Graine unique utilisée comme trajectoire REPRÉSENTATIVE pour
# les figures qui ne peuvent pas être moyennées sur les 30
# graines (événements discrets : chronologie des décisions,
# clé candidate prête, activation). Les figures de moyennes
# (quatre objectifs, comparaison P0/B1) utilisent, elles,
# l'ensemble des graines disponibles dans le journal.
REPRESENTATIVE_SEED = 2000


DECISION_NAMES = [
    "A1-K0", "A1-K1a", "A1-K1b", "A1-K2",
    "A2-K0", "A2-K1a", "A2-K1b", "A2-K2",
    "REFUS"
]


# ================================================================
# 1. CHARGEMENT DU JOURNAL
# ================================================================


def _parse_bool(value):

    return value in ("True", "true", "1", True)


def _parse_optional_float(value):

    if value is None or value == "":

        return None

    return float(value)


def load_log(log_path):

    rows = []

    with open(
        log_path,
        newline="",
        encoding="utf-8"
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        for raw_row in reader:

            rows.append(
                {
                    "scenario_id": (
                        raw_row["scenario_id"]
                    ),
                    "phase_name": (
                        raw_row["phase_name"]
                    ),
                    "policy_id": raw_row["policy_id"],
                    "seed": int(raw_row["seed"]),
                    "step_index": int(
                        raw_row["step_index"]
                    ),
                    "battery_energy_j": float(
                        raw_row["battery_energy_j"]
                    ),
                    "snr_db": float(raw_row["snr_db"]),
                    "effective_speed_m_s": float(
                        raw_row["effective_speed_m_s"]
                    ),
                    "doppler_hz": float(
                        raw_row["doppler_hz"]
                    ),
                    "rho_time": float(
                        raw_row["rho_time"]
                    ),
                    "rho_ab": float(raw_row["rho_ab"]),
                    "effective_kdr": (
                        _parse_optional_float(
                            raw_row["effective_kdr"]
                        )
                    ),
                    "criticality": int(
                        raw_row["criticality"]
                    ),
                    "mallory_attempted": _parse_bool(
                        raw_row["mallory_attempted"]
                    ),
                    "compromise_suspected": (
                        _parse_bool(
                            raw_row[
                                "compromise_suspected"
                            ]
                        )
                    ),
                    "remaining_duty_cycle_airtime_s": (
                        float(
                            raw_row[
                                "remaining_duty_cycle"
                                "_airtime_s"
                            ]
                        )
                    ),
                    "key_age_s": float(
                        raw_row["key_age_s"]
                    ),
                    "messages_with_current_key": int(
                        raw_row[
                            "messages_with_current_key"
                        ]
                    ),
                    "k1a_measurements_collected": int(
                        raw_row[
                            "k1a_measurements_collected"
                        ]
                    ),
                    "k1b_measurements_collected": int(
                        raw_row[
                            "k1b_measurements_collected"
                        ]
                    ),
                    "candidate_key_ready": _parse_bool(
                        raw_row["candidate_key_ready"]
                    ),
                    "candidate_key_action": (
                        raw_row["candidate_key_action"]
                    ),
                    "selected_decision": (
                        raw_row["selected_decision"]
                    ),
                    "energy_objective_j": (
                        _parse_optional_float(
                            raw_row["energy_objective_j"]
                        )
                    ),
                    "latency_objective": (
                        _parse_optional_float(
                            raw_row["latency_objective"]
                        )
                    ),
                    "authentication_robustness": (
                        _parse_optional_float(
                            raw_row[
                                "authentication_"
                                "robustness"
                            ]
                        )
                    ),
                    "key_quality": (
                        _parse_optional_float(
                            raw_row["key_quality"]
                        )
                    ),
                    "admissible_decision_count": int(
                        raw_row[
                            "admissible_decision_count"
                        ]
                    ),
                    "pareto_front_size": int(
                        raw_row["pareto_front_size"]
                    ),
                    "legitimate_message_served": (
                        _parse_bool(
                            raw_row[
                                "legitimate_message_"
                                "served"
                            ]
                        )
                    ),
                    "security_floor_violation": (
                        _parse_bool(
                            raw_row[
                                "security_floor_"
                                "violation"
                            ]
                        )
                    ),
                    "mallory_accepted": _parse_bool(
                        raw_row["mallory_accepted"]
                    )
                }
            )

    return rows


def _filter_rows(
    rows,
    scenario_id,
    policy_id=None,
    seed=None
):

    return [
        row
        for row in rows
        if row["scenario_id"] == scenario_id
        and (
            policy_id is None
            or row["policy_id"] == policy_id
        )
        and (
            seed is None
            or row["seed"] == seed
        )
    ]


def _scenario_display_name(
    case_studies_by_id,
    scenario_id
):

    case_study = case_studies_by_id.get(scenario_id)

    if case_study is None:

        return scenario_id

    return case_study["scenario_name"]


# ================================================================
# 2. FIGURE 1 — CHRONOLOGIE DES PHASES ET DÉCISIONS
# ================================================================


def figure_phase_and_decision_timeline(
    rows,
    scenario_id,
    policy_id,
    seed,
    scenario_name,
    output_path
):

    scenario_rows = _filter_rows(
        rows,
        scenario_id,
        policy_id,
        seed
    )

    scenario_rows.sort(
        key=lambda row: row["step_index"]
    )

    steps = [
        row["step_index"] for row in scenario_rows
    ]

    decision_indices = [
        DECISION_NAMES.index(
            row["selected_decision"]
        )
        if row["selected_decision"] in DECISION_NAMES
        else len(DECISION_NAMES) - 1
        for row in scenario_rows
    ]

    figure, (
        decision_axes,
        phase_axes
    ) = plt.subplots(
        2,
        1,
        figsize=(13.0, 6.0),
        sharex=True,
        height_ratios=[3, 1]
    )

    decision_axes.step(
        steps,
        decision_indices,
        where="post"
    )

    decision_axes.set_yticks(
        range(len(DECISION_NAMES))
    )

    decision_axes.set_yticklabels(
        DECISION_NAMES
    )

    decision_axes.set_ylabel(
        "Décision sélectionnée"
    )

    decision_axes.set_title(
        scenario_name
        + " — chronologie des phases et décisions "
        "(politique "
        + policy_id
        + ", graine "
        + str(seed)
        + ")"
    )

    phase_names_in_order = []

    for row in scenario_rows:

        if (
            len(phase_names_in_order) == 0
            or phase_names_in_order[-1]
            != row["phase_name"]
        ):

            phase_names_in_order.append(
                row["phase_name"]
            )

    unique_phase_names = sorted(
        set(
            row["phase_name"]
            for row in scenario_rows
        ),
        key=phase_names_in_order.index
    )

    phase_indices = [
        unique_phase_names.index(
            row["phase_name"]
        )
        for row in scenario_rows
    ]

    phase_axes.step(
        steps,
        phase_indices,
        where="post",
        color="tab:orange"
    )

    phase_axes.set_yticks(
        range(len(unique_phase_names))
    )

    phase_axes.set_yticklabels(
        unique_phase_names,
        fontsize=8
    )

    phase_axes.set_xlabel("Période")
    phase_axes.set_ylabel("Phase")

    figure.tight_layout()

    figure.savefig(output_path)

    plt.close(figure)


# ================================================================
# 3. FIGURES 2 À 5 — TRAJECTOIRES TEMPORELLES
# ================================================================


def _figure_metric_over_time(
    rows,
    scenario_id,
    policy_id,
    seed,
    scenario_name,
    metric_field,
    y_label,
    title_suffix,
    output_path
):

    scenario_rows = _filter_rows(
        rows,
        scenario_id,
        policy_id,
        seed
    )

    scenario_rows.sort(
        key=lambda row: row["step_index"]
    )

    steps = [
        row["step_index"] for row in scenario_rows
    ]

    values = [
        row[metric_field]
        for row in scenario_rows
    ]

    figure, axes = plt.subplots(
        figsize=(12.0, 4.5)
    )

    axes.plot(
        steps,
        values,
        linewidth=1.0
    )

    axes.set_xlabel("Période")
    axes.set_ylabel(y_label)

    axes.set_title(
        scenario_name
        + " — "
        + title_suffix
        + " (politique "
        + policy_id
        + ", graine "
        + str(seed)
        + ")"
    )

    figure.tight_layout()

    figure.savefig(output_path)

    plt.close(figure)


def figure_energy_over_time(
    rows, scenario_id, policy_id, seed,
    scenario_name, output_path
):

    _figure_metric_over_time(
        rows, scenario_id, policy_id, seed,
        scenario_name,
        metric_field="energy_objective_j",
        y_label="Énergie de la décision (J)",
        title_suffix="énergie au cours du temps",
        output_path=output_path
    )


def figure_latency_over_time(
    rows, scenario_id, policy_id, seed,
    scenario_name, output_path
):

    _figure_metric_over_time(
        rows, scenario_id, policy_id, seed,
        scenario_name,
        metric_field="latency_objective",
        y_label="Latence normalisée",
        title_suffix="latence au cours du temps",
        output_path=output_path
    )


def figure_authentication_robustness_over_time(
    rows, scenario_id, policy_id, seed,
    scenario_name, output_path
):

    _figure_metric_over_time(
        rows, scenario_id, policy_id, seed,
        scenario_name,
        metric_field="authentication_robustness",
        y_label="Robustesse d'authentification",
        title_suffix=(
            "robustesse d'authentification au cours "
            "du temps"
        ),
        output_path=output_path
    )


def figure_key_quality_over_time(
    rows, scenario_id, policy_id, seed,
    scenario_name, output_path
):

    _figure_metric_over_time(
        rows, scenario_id, policy_id, seed,
        scenario_name,
        metric_field="key_quality",
        y_label="Qualité de clé",
        title_suffix="qualité de clé au cours du temps",
        output_path=output_path
    )


# ================================================================
# 4. FIGURE 6 — PROGRESSION K1a / K1b
# ================================================================


def figure_k1_progression(
    rows,
    scenario_id,
    policy_id,
    seed,
    scenario_name,
    output_path
):

    scenario_rows = _filter_rows(
        rows,
        scenario_id,
        policy_id,
        seed
    )

    scenario_rows.sort(
        key=lambda row: row["step_index"]
    )

    steps = [
        row["step_index"] for row in scenario_rows
    ]

    k1a_values = [
        row["k1a_measurements_collected"]
        for row in scenario_rows
    ]

    k1b_values = [
        row["k1b_measurements_collected"]
        for row in scenario_rows
    ]

    figure, axes = plt.subplots(
        figsize=(12.0, 4.5)
    )

    axes.plot(
        steps,
        k1a_values,
        label="K1a (mesures accumulées)",
        linewidth=1.2
    )

    axes.plot(
        steps,
        k1b_values,
        label="K1b (sondages accumulés)",
        linewidth=1.2
    )

    axes.set_xlabel("Période")
    axes.set_ylabel("Mesures / sondages accumulés")

    axes.set_title(
        scenario_name
        + " — progression K1a / K1b (politique "
        + policy_id
        + ", graine "
        + str(seed)
        + ")"
    )

    axes.legend()

    figure.tight_layout()

    figure.savefig(output_path)

    plt.close(figure)


# ================================================================
# 5. FIGURE 7 — ÉVÉNEMENTS DE PRÉPARATION ET D'ACTIVATION
# ================================================================


def figure_preparation_and_activation_events(
    rows,
    scenario_id,
    policy_id,
    seed,
    scenario_name,
    output_path
):

    scenario_rows = _filter_rows(
        rows,
        scenario_id,
        policy_id,
        seed
    )

    scenario_rows.sort(
        key=lambda row: row["step_index"]
    )

    ready_steps = []
    activation_steps = []
    previous_ready = False
    previous_key_age_s = None

    for row in scenario_rows:

        if row["candidate_key_ready"] and not (
            previous_ready
        ):

            ready_steps.append(
                row["step_index"]
            )

        if (
            previous_key_age_s is not None
            and row["key_age_s"] == 0.0
            and previous_key_age_s != 0.0
        ):

            activation_steps.append(
                row["step_index"]
            )

        previous_ready = row["candidate_key_ready"]
        previous_key_age_s = row["key_age_s"]

    figure, axes = plt.subplots(
        figsize=(12.0, 3.0)
    )

    axes.eventplot(
        [ready_steps],
        lineoffsets=[1],
        colors=["tab:blue"],
        label="Clé candidate prête"
    )

    axes.eventplot(
        [activation_steps],
        lineoffsets=[0],
        colors=["tab:red"],
        label="Activation de clé"
    )

    axes.set_yticks([0, 1])
    axes.set_yticklabels(
        ["Activation", "Candidat prêt"]
    )

    axes.set_xlabel("Période")

    axes.set_title(
        scenario_name
        + " — événements de préparation et "
        "d'activation (politique "
        + policy_id
        + ", graine "
        + str(seed)
        + ")"
    )

    figure.tight_layout()

    figure.savefig(output_path)

    plt.close(figure)


# ================================================================
# 6. FIGURE 8 — FRÉQUENCE DES DÉCISIONS
# ================================================================


def figure_decision_frequency(
    rows,
    scenario_id,
    policy_id,
    scenario_name,
    output_path
):

    scenario_rows = _filter_rows(
        rows,
        scenario_id,
        policy_id
    )

    counts = {
        name: 0
        for name in DECISION_NAMES
    }

    for row in scenario_rows:

        decision_name = row["selected_decision"]

        if decision_name not in counts:

            decision_name = "REFUS"

        counts[decision_name] += 1

    total = max(
        sum(
            counts.values()
        ),
        1
    )

    frequencies = [
        counts[name] / total
        for name in DECISION_NAMES
    ]

    figure, axes = plt.subplots(
        figsize=(10.0, 4.5)
    )

    axes.bar(
        DECISION_NAMES,
        frequencies
    )

    axes.set_ylabel("Fréquence de sélection")

    axes.set_title(
        scenario_name
        + " — fréquence des décisions (politique "
        + policy_id
        + ")"
    )

    axes.tick_params(
        axis="x",
        rotation=45
    )

    figure.tight_layout()

    figure.savefig(output_path)

    plt.close(figure)


# ================================================================
# 7. FIGURE 9 — COMPARAISON P0 CONTRE B1
# ================================================================


def figure_p0_vs_b1_comparison(
    rows,
    scenario_id,
    scenario_name,
    output_path
):

    metrics = [
        (
            "energy_objective_j",
            "Énergie moyenne (J)"
        ),
        (
            "latency_objective",
            "Latence normalisée moyenne"
        ),
        (
            "authentication_robustness",
            "Robustesse d'authentification "
            "moyenne"
        ),
        (
            "key_quality",
            "Qualité de clé moyenne"
        )
    ]

    p0_rows = _filter_rows(
        rows,
        scenario_id,
        "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS"
    )

    b1_rows = _filter_rows(
        rows,
        scenario_id,
        "B1-CONVENTIONAL"
    )

    def mean_of(
        source_rows,
        field
    ):

        values = [
            row[field]
            for row in source_rows
            if row[field] is not None
        ]

        if len(values) == 0:

            return 0.0

        return sum(values) / len(values)

    p0_values = [
        mean_of(p0_rows, field)
        for field, _ in metrics
    ]

    b1_values = [
        mean_of(b1_rows, field)
        for field, _ in metrics
    ]

    labels = [
        label for _, label in metrics
    ]

    x_positions = range(
        len(metrics)
    )

    bar_width = 0.35

    figure, axes = plt.subplots(
        figsize=(11.0, 5.0)
    )

    axes.bar(
        [x - bar_width / 2 for x in x_positions],
        p0_values,
        width=bar_width,
        label="P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS"
    )

    axes.bar(
        [x + bar_width / 2 for x in x_positions],
        b1_values,
        width=bar_width,
        label="B1-CONVENTIONAL"
    )

    axes.set_xticks(
        list(x_positions)
    )

    axes.set_xticklabels(
        labels,
        rotation=20,
        ha="right"
    )

    axes.set_title(
        scenario_name
        + " — comparaison P0 contre B1"
    )

    axes.legend()

    figure.tight_layout()

    figure.savefig(output_path)

    plt.close(figure)


# ================================================================
# 8. FIGURE 10 — FRONT DE PARETO À DES PÉRIODES REPRÉSENTATIVES
# ================================================================
#
# Le journal CSV ne conserve pas les vecteurs d'objectifs
# complets de toutes les décisions du front de Pareto (seule
# leur NOMBRE, pareto_front_size, y est journalisé). Cette
# figure prend donc directement des instantanés capturés en
# mémoire (voir tests/test_five_case_studies_integration.py
# pour un exemple de capture), et non le journal CSV, afin de
# ne réinventer aucune donnée.
#
# pareto_snapshots : liste de dicts
# {
#     "step_index": int,
#     "points": [(energy, latency, decision_name), ...],
#     "selected_decision_name": str
# }
def figure_pareto_front_snapshots(
    pareto_snapshots,
    scenario_name,
    output_path
):

    snapshot_count = len(pareto_snapshots)

    figure, axes_list = plt.subplots(
        1,
        max(
            snapshot_count,
            1
        ),
        figsize=(
            4.5 * max(snapshot_count, 1),
            4.5
        )
    )

    if snapshot_count == 1:

        axes_list = [axes_list]

    for axes, snapshot in zip(
        axes_list,
        pareto_snapshots
    ):

        energies = [
            point[0]
            for point in snapshot["points"]
        ]

        latencies = [
            point[1]
            for point in snapshot["points"]
        ]

        axes.scatter(
            energies,
            latencies
        )

        for point in snapshot["points"]:

            energy, latency, decision_name = point

            marker = (
                "o"
                if decision_name
                != snapshot[
                    "selected_decision_name"
                ]
                else "*"
            )

            axes.scatter(
                [energy],
                [latency],
                marker=marker,
                s=(
                    120
                    if marker == "*"
                    else 40
                )
            )

        axes.set_xlabel("Énergie (J)")
        axes.set_ylabel("Latence normalisée")

        axes.set_title(
            "Période "
            + str(snapshot["step_index"])
        )

    figure.suptitle(
        scenario_name
        + " — front de Pareto à des périodes "
        "représentatives"
    )

    figure.tight_layout()

    figure.savefig(output_path)

    plt.close(figure)


# ================================================================
# 9. GÉNÉRATION GROUPÉE (utilitaire optionnel)
# ================================================================


def generate_all_figures_for_scenario(
    rows,
    case_study,
    policy_id,
    seed,
    output_directory
):

    output_path = Path(
        output_directory
    )

    output_path.mkdir(
        parents=True,
        exist_ok=True
    )

    scenario_id = case_study["scenario_id"]
    scenario_name = case_study["scenario_name"]

    figure_phase_and_decision_timeline(
        rows, scenario_id, policy_id, seed,
        scenario_name,
        output_path
        / (scenario_id + "_timeline.png")
    )

    figure_energy_over_time(
        rows, scenario_id, policy_id, seed,
        scenario_name,
        output_path
        / (scenario_id + "_energy.png")
    )

    figure_latency_over_time(
        rows, scenario_id, policy_id, seed,
        scenario_name,
        output_path
        / (scenario_id + "_latency.png")
    )

    figure_authentication_robustness_over_time(
        rows, scenario_id, policy_id, seed,
        scenario_name,
        output_path
        / (scenario_id + "_authentication.png")
    )

    figure_key_quality_over_time(
        rows, scenario_id, policy_id, seed,
        scenario_name,
        output_path
        / (scenario_id + "_key_quality.png")
    )

    figure_k1_progression(
        rows, scenario_id, policy_id, seed,
        scenario_name,
        output_path
        / (scenario_id + "_k1_progression.png")
    )

    figure_preparation_and_activation_events(
        rows, scenario_id, policy_id, seed,
        scenario_name,
        output_path
        / (scenario_id + "_k1_events.png")
    )

    figure_decision_frequency(
        rows, scenario_id, policy_id,
        scenario_name,
        output_path
        / (scenario_id + "_decision_frequency.png")
    )

    figure_p0_vs_b1_comparison(
        rows, scenario_id,
        scenario_name,
        output_path
        / (scenario_id + "_p0_vs_b1.png")
    )


# ================================================================
# 10. OUTILS PARTAGÉS : PHASES, ÉVÉNEMENTS, STATISTIQUES IC 95 %
# ================================================================


def scenario_full_name(scenario_id):

    return SCENARIO_FULL_NAMES.get(
        scenario_id,
        scenario_id
    )


def get_phase_segments_in_steps(
    case_study,
    max_steps
):

    segments = []

    for phase in case_study["phases"]:

        segments.append(
            {
                "phase_name": phase["phase_name"],
                "start_step": round(
                    phase["start_fraction"] * max_steps
                ),
                "end_step": round(
                    phase["end_fraction"] * max_steps
                )
            }
        )

    return segments


def get_scenario_point_events_in_steps(
    case_study,
    max_steps
):

    events = []

    for event in case_study.get(
        "scenario_events",
        []
    ):

        events.append(
            {
                "label": event["event_name"],
                "step": round(
                    event["at_fraction"] * max_steps
                )
            }
        )

    return events


# Moyenne et IC 95 % (approximation normale) d'un champ, à
# chaque step_index, sur l'ensemble des graines disponibles
# dans le journal pour ce scénario/politique.
def compute_step_statistics(
    rows,
    scenario_id,
    policy_id,
    field
):

    scenario_rows = _filter_rows(
        rows,
        scenario_id,
        policy_id
    )

    values_by_step = {}

    for row in scenario_rows:

        value = row[field]

        if value is None:

            continue

        values_by_step.setdefault(
            row["step_index"],
            []
        ).append(value)

    steps = sorted(
        values_by_step.keys()
    )

    means = []
    ci_low = []
    ci_high = []

    for step in steps:

        values = values_by_step[step]

        sample_size = len(values)

        mean = sum(values) / sample_size

        if sample_size > 1:

            variance = sum(
                (value - mean) ** 2
                for value in values
            ) / (sample_size - 1)

            standard_error = math.sqrt(
                variance / sample_size
            )

        else:

            standard_error = 0.0

        margin = 1.96 * standard_error

        means.append(mean)
        ci_low.append(mean - margin)
        ci_high.append(mean + margin)

    return steps, means, ci_low, ci_high


# Événements K1 (clé candidate prête / activation) détectés
# sur UNE SEULE graine représentative (ces événements sont
# discrets et dépendent des tirages aléatoires : ils ne
# peuvent pas être moyennés sur 30 graines sans perdre leur
# sens).
def get_k1_events_from_seed(
    rows,
    scenario_id,
    policy_id,
    seed
):

    scenario_rows = _filter_rows(
        rows,
        scenario_id,
        policy_id,
        seed
    )

    scenario_rows.sort(
        key=lambda row: row["step_index"]
    )

    ready_steps = []
    activation_events = []

    previous_ready = False
    previous_key_age_s = None

    for row in scenario_rows:

        if row["candidate_key_ready"] and not (
            previous_ready
        ):

            ready_steps.append(
                row["step_index"]
            )

        if (
            previous_key_age_s is not None
            and row["key_age_s"] == 0.0
            and previous_key_age_s != 0.0
        ):

            activation_events.append(
                {
                    "step": row["step_index"],
                    "mechanism": (
                        row["selected_decision"]
                    )
                }
            )

        previous_ready = row["candidate_key_ready"]
        previous_key_age_s = row["key_age_s"]

    return ready_steps, activation_events


def _draw_phase_boundaries(
    axes,
    phase_segments
):

    for segment in phase_segments:

        if segment["start_step"] > 0:

            axes.axvline(
                segment["start_step"],
                color="grey",
                linestyle="--",
                linewidth=0.8,
                alpha=0.6
            )


def _label_phase_boundaries(
    axes,
    phase_segments,
    y_position=1.02
):

    for segment in phase_segments:

        midpoint = (
            segment["start_step"]
            + segment["end_step"]
        ) / 2

        axes.text(
            midpoint,
            y_position,
            segment["phase_name"],
            transform=(
                axes.get_xaxis_transform()
            ),
            ha="center",
            va="bottom",
            fontsize=7,
            clip_on=False
        )


# ================================================================
# 11. FIGURE PRINCIPALE À QUATRE OBJECTIFS
# ================================================================
def figure_four_objectives_over_time(
    rows,
    case_study,
    max_steps,
    output_path,
    representative_seed=REPRESENTATIVE_SEED
):

    scenario_id = case_study["scenario_id"]
    scenario_name = scenario_full_name(
        scenario_id
    )

    phase_segments = get_phase_segments_in_steps(
        case_study,
        max_steps
    )

    point_events = (
        get_scenario_point_events_in_steps(
            case_study,
            max_steps
        )
    )

    ready_steps, activation_events = (
        get_k1_events_from_seed(
            rows,
            scenario_id,
            "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS",
            representative_seed
        )
    )

    metrics = [
        (
            "energy_objective_j",
            "Énergie (J)\n(plus faible = meilleur)"
        ),
        (
            "latency_objective",
            "Latence normalisée\n"
            "(plus faible = meilleur)"
        ),
        (
            "authentication_robustness",
            "Robustesse d'authentification\n"
            "(plus élevée = meilleur)"
        ),
        (
            "key_quality",
            "Qualité de clé\n"
            "(plus élevée = meilleur)"
        )
    ]

    figure, axes_list = plt.subplots(
        4,
        1,
        figsize=(14.0, 13.0),
        sharex=True
    )

    seed_count = len(
        set(
            row["seed"]
            for row in rows
            if row["scenario_id"] == scenario_id
        )
    )

    for panel_index, (
        field,
        y_label
    ) in enumerate(metrics):

        axes = axes_list[panel_index]

        for policy_id, color in [
            ("P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS", "tab:blue"),
            ("B1-CONVENTIONAL", "tab:orange")
        ]:

            steps, means, ci_low, ci_high = (
                compute_step_statistics(
                    rows,
                    scenario_id,
                    policy_id,
                    field
                )
            )

            if len(steps) == 0:

                continue

            axes.plot(
                steps,
                means,
                label=policy_id,
                color=color,
                linewidth=1.0
            )

            axes.fill_between(
                steps,
                ci_low,
                ci_high,
                color=color,
                alpha=0.2,
                linewidth=0
            )

        _draw_phase_boundaries(
            axes,
            phase_segments
        )

        for event in point_events:

            axes.axvline(
                event["step"],
                color="purple",
                linestyle=":",
                linewidth=1.2,
                alpha=0.8
            )

        for step in ready_steps:

            axes.axvline(
                step,
                color="tab:green",
                linestyle="-.",
                linewidth=0.8,
                alpha=0.5
            )

        for event in activation_events:

            axes.axvline(
                event["step"],
                color="tab:red",
                linestyle="-",
                linewidth=1.0,
                alpha=0.6
            )

        axes.set_ylabel(
            y_label,
            fontsize=8
        )

        axes.legend(
            fontsize=7,
            loc="upper right"
        )

    top_axes = axes_list[0]

    _label_phase_boundaries(
        top_axes,
        phase_segments
    )

    for event in point_events:

        top_axes.text(
            event["step"],
            1.09,
            event["label"],
            transform=(
                top_axes.get_xaxis_transform()
            ),
            ha="center",
            va="bottom",
            fontsize=7,
            color="purple",
            rotation=90,
            clip_on=False
        )

    axes_list[-1].set_xlabel(
        "Période de simulation"
    )

    figure.suptitle(
        scenario_name
        + " — énergie, latence, authentification et "
        "qualité de clé au cours du temps\n"
        "moyenne sur "
        + str(seed_count)
        + " graines communes P0/B1 (bande = IC 95 %)"
        " — graine "
        + str(representative_seed)
        + " pour les événements K1\n"
        "pointillé gris = changement de phase ; "
        "pointillé violet = événement ; tiret vert = "
        "clé candidate prête ; trait rouge = "
        "activation de clé",
        fontsize=8
    )

    figure.tight_layout(
        rect=[0, 0, 1, 0.90]
    )

    figure.subplots_adjust(
        top=0.82
    )

    figure.savefig(
        output_path,
        dpi=130
    )

    plt.close(figure)


# ================================================================
# 12. CHRONOLOGIE DES DÉCISIONS (P0 ET B1)
# ================================================================
def figure_decision_timeline_by_policy(
    rows,
    case_study,
    max_steps,
    output_path,
    representative_seed=REPRESENTATIVE_SEED
):

    scenario_id = case_study["scenario_id"]
    scenario_name = scenario_full_name(
        scenario_id
    )

    phase_segments = get_phase_segments_in_steps(
        case_study,
        max_steps
    )

    figure, (
        p0_axes,
        b1_axes
    ) = plt.subplots(
        2,
        1,
        figsize=(14.0, 6.0),
        sharex=True
    )

    for axes, policy_id in [
        (p0_axes, "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS"),
        (b1_axes, "B1-CONVENTIONAL")
    ]:

        scenario_rows = _filter_rows(
            rows,
            scenario_id,
            policy_id,
            representative_seed
        )

        scenario_rows.sort(
            key=lambda row: row["step_index"]
        )

        steps = [
            row["step_index"]
            for row in scenario_rows
        ]

        indices = [
            DECISION_NAMES.index(
                row["selected_decision"]
            )
            if row["selected_decision"]
            in DECISION_NAMES
            else len(DECISION_NAMES) - 1
            for row in scenario_rows
        ]

        axes.step(
            steps,
            indices,
            where="post",
            linewidth=1.0
        )

        axes.set_yticks(
            range(len(DECISION_NAMES))
        )

        axes.set_yticklabels(
            DECISION_NAMES,
            fontsize=7
        )

        axes.set_ylabel(
            policy_id,
            fontsize=8
        )

        _draw_phase_boundaries(
            axes,
            phase_segments
        )

    _label_phase_boundaries(
        p0_axes,
        phase_segments
    )

    b1_axes.set_xlabel(
        "Période de simulation (graine "
        + str(representative_seed)
        + ")"
    )

    figure.suptitle(
        scenario_name
        + " — chronologie des décisions "
        "sélectionnées (P0 en haut, B1 en bas)",
        fontsize=10
    )

    figure.tight_layout(
        rect=[0, 0, 1, 0.88]
    )

    figure.savefig(
        output_path,
        dpi=130
    )

    plt.close(figure)


# ================================================================
# 13. PROGRESSION DE LA GÉNÉRATION DE CLÉ
# ================================================================
def derive_required_measurements_curve(
    rows,
    scenario_id,
    policy_id,
    seed,
    parameters
):

    scenario_rows = _filter_rows(
        rows,
        scenario_id,
        policy_id,
        seed
    )

    scenario_rows.sort(
        key=lambda row: row["step_index"]
    )

    steps = []
    required_values = []

    for row in scenario_rows:

        if row["effective_kdr"] is None:

            continue

        reconciliation_yield = (
            calculate_reconciliation_yield(
                effective_kdr=(
                    row["effective_kdr"]
                ),
                kept_measurement_ratio=(
                    parameters
                    .kept_measurement_ratio
                )
            )
        )

        required_measurements = (
            calculate_required_measurements(
                key_length_bits=(
                    parameters.key_length_bits
                ),
                reconciliation_yield=(
                    reconciliation_yield
                ),
                numerical_epsilon=(
                    parameters.key_numerical_epsilon
                )
            )
        )

        steps.append(
            row["step_index"]
        )

        required_values.append(
            required_measurements
        )

    return steps, required_values


def figure_key_generation_progress(
    rows,
    case_study,
    parameters,
    max_steps,
    output_path,
    representative_seed=REPRESENTATIVE_SEED
):

    scenario_id = case_study["scenario_id"]
    scenario_name = scenario_full_name(
        scenario_id
    )

    phase_segments = get_phase_segments_in_steps(
        case_study,
        max_steps
    )

    p0_rows = _filter_rows(
        rows,
        scenario_id,
        "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS",
        representative_seed
    )

    p0_rows.sort(
        key=lambda row: row["step_index"]
    )

    steps = [
        row["step_index"] for row in p0_rows
    ]

    k1a_values = [
        row["k1a_measurements_collected"]
        for row in p0_rows
    ]

    k1b_values = [
        row["k1b_measurements_collected"]
        for row in p0_rows
    ]

    required_steps, required_values = (
        derive_required_measurements_curve(
            rows,
            scenario_id,
            "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS",
            representative_seed,
            parameters
        )
    )

    # Lorsque la PHY est infaisable, reconciliation_yield
    # s'effondre vers key_numerical_epsilon
    # (physec_dm/key_generation.py,
    # calculate_required_measurements), ce qui fait exploser
    # N_required à des valeurs sans signification physique
    # (jusqu'à ~1e10) — un résultat mathématiquement correct
    # de l'équation, mais qui écraserait totalement l'échelle
    # de K1a/K1b sur ce graphique. L'affichage est donc
    # plafonné à un niveau lisible ; la valeur RÉELLE n'est
    # jamais modifiée (voir summary_by_scenario_policy*.csv
    # et le journal complet pour les valeurs exactes).
    display_cap = max(
        max(k1a_values, default=0),
        max(k1b_values, default=0),
        10
    ) * 3

    clipped_count = sum(
        1
        for value in required_values
        if value > display_cap
    )

    required_values_for_display = [
        min(value, display_cap)
        for value in required_values
    ]

    ready_steps, activation_events = (
        get_k1_events_from_seed(
            rows,
            scenario_id,
            "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS",
            representative_seed
        )
    )

    figure, axes = plt.subplots(
        figsize=(14.0, 5.5)
    )

    axes.plot(
        steps,
        k1a_values,
        label="K1a accumulé",
        color="tab:blue",
        linewidth=1.1
    )

    axes.plot(
        steps,
        k1b_values,
        label="K1b accumulé",
        color="tab:orange",
        linewidth=1.1
    )

    axes.plot(
        required_steps,
        required_values_for_display,
        label=(
            "N_required (dérivé de "
            "effective_kdr ; affichage "
            "plafonné à "
            + format(display_cap, ".0f")
            + (
                " — "
                + str(clipped_count)
                + " périodes tronquées, PHY "
                "infaisable)"
                if clipped_count > 0
                else ")"
            )
        ),
        color="black",
        linewidth=0.6,
        linestyle=":"
    )

    ready_label_used = False

    for step in ready_steps:

        axes.axvline(
            step,
            color="tab:green",
            linestyle="-.",
            linewidth=1.0,
            alpha=0.8,
            label=(
                "Clé candidate prête"
                if not ready_label_used
                else None
            )
        )

        ready_label_used = True

    activation_colors = {
        "A1-K1a": "tab:blue",
        "A2-K1a": "tab:blue",
        "A1-K1b": "tab:orange",
        "A2-K1b": "tab:orange",
        "A1-K2": "tab:red",
        "A2-K2": "tab:red"
    }

    labeled_mechanisms = set()

    for event in activation_events:

        mechanism = event["mechanism"]

        color = activation_colors.get(
            mechanism,
            "black"
        )

        label = None

        if mechanism not in labeled_mechanisms:

            label = "Activation (" + mechanism + ")"
            labeled_mechanisms.add(mechanism)

        axes.axvline(
            event["step"],
            color=color,
            linestyle="-",
            linewidth=1.4,
            alpha=0.9,
            label=label
        )

    _draw_phase_boundaries(
        axes,
        phase_segments
    )

    axes.set_xlabel(
        "Période de simulation (graine "
        + str(representative_seed)
        + ")"
    )

    axes.set_ylabel(
        "Mesures accumulées / N_required"
    )

    axes.set_title(
        scenario_name
        + " — progression de la génération de "
        "clé (P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS)\n"
        "préparation → candidat prêt → "
        "admissibilité → activation"
    )

    axes.legend(
        fontsize=7,
        loc="upper left"
    )

    axes.set_ylim(
        0,
        display_cap * 1.1
    )

    figure.tight_layout()

    figure.savefig(
        output_path,
        dpi=130
    )

    plt.close(figure)


# ================================================================
# 14. COMPARAISON DÉTAILLÉE P0 CONTRE B1 (9 MÉTRIQUES)
# ================================================================
def compute_scenario_policy_summary(
    rows,
    scenario_id,
    policy_id
):

    scenario_rows = _filter_rows(
        rows,
        scenario_id,
        policy_id
    )

    def mean_of(field):

        values = [
            row[field]
            for row in scenario_rows
            if row[field] is not None
        ]

        if len(values) == 0:

            return 0.0

        return sum(values) / len(values)

    total = len(scenario_rows)

    served = sum(
        1
        for row in scenario_rows
        if row["legitimate_message_served"]
    )

    refused = total - served

    violations = sum(
        1
        for row in scenario_rows
        if row["security_floor_violation"]
    )

    mallory_attempts = sum(
        1
        for row in scenario_rows
        if row["mallory_attempted"]
    )

    mallory_accepted = sum(
        1
        for row in scenario_rows
        if row["mallory_accepted"]
    )

    far = (
        mallory_accepted / mallory_attempts
        if mallory_attempts > 0
        else 0.0
    )

    seeds = sorted(
        set(
            row["seed"] for row in scenario_rows
        )
    )

    activation_counts = {
        "K1a": 0,
        "K1b": 0,
        "K2": 0
    }

    for seed in seeds:

        seed_rows = sorted(
            [
                row
                for row in scenario_rows
                if row["seed"] == seed
            ],
            key=lambda row: row["step_index"]
        )

        previous_key_age_s = None

        for row in seed_rows:

            if (
                previous_key_age_s is not None
                and row["key_age_s"] == 0.0
                and previous_key_age_s != 0.0
            ):

                mechanism = row[
                    "selected_decision"
                ]

                if "K1a" in mechanism:

                    activation_counts["K1a"] += 1

                elif "K1b" in mechanism:

                    activation_counts["K1b"] += 1

                elif "K2" in mechanism:

                    activation_counts["K2"] += 1

            previous_key_age_s = row["key_age_s"]

    return {
        "energy_mean": mean_of(
            "energy_objective_j"
        ),
        "latency_mean": mean_of(
            "latency_objective"
        ),
        "authentication_mean": mean_of(
            "authentication_robustness"
        ),
        "key_quality_mean": mean_of(
            "key_quality"
        ),
        "service_rate": (
            served / total if total else 0.0
        ),
        "refusal_rate": (
            refused / total if total else 0.0
        ),
        "far": far,
        "violation_rate": (
            violations / total if total else 0.0
        ),
        "activation_counts": activation_counts
    }


def figure_p0_vs_b1_detailed(
    rows,
    case_study,
    output_path
):

    scenario_id = case_study["scenario_id"]
    scenario_name = scenario_full_name(
        scenario_id
    )

    p0_summary = compute_scenario_policy_summary(
        rows,
        scenario_id,
        "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS"
    )

    b1_summary = compute_scenario_policy_summary(
        rows,
        scenario_id,
        "B1-CONVENTIONAL"
    )

    metrics = [
        ("energy_mean", "Énergie moyenne (J)"),
        (
            "latency_mean",
            "Latence normalisée moyenne"
        ),
        (
            "authentication_mean",
            "Robustesse d'authentification"
        ),
        (
            "key_quality_mean",
            "Qualité de clé moyenne"
        ),
        (
            "service_rate",
            "Taux de messages servis"
        ),
        (
            "refusal_rate",
            "Taux de refus légitime"
        ),
        ("far", "FAR (fausse acceptation)"),
        (
            "violation_rate",
            "Taux de violation du plancher"
        )
    ]

    figure, axes_grid = plt.subplots(
        3,
        3,
        figsize=(14.0, 10.0)
    )

    axes_list = axes_grid.flatten()

    for axes, (field, label) in zip(
        axes_list,
        metrics
    ):

        axes.bar(
            ["P0", "B1"],
            [
                p0_summary[field],
                b1_summary[field]
            ],
            color=["tab:blue", "tab:orange"]
        )

        axes.set_title(
            label,
            fontsize=9
        )

    activation_axes = axes_list[8]

    mechanisms = ["K1a", "K1b", "K2"]

    x_positions = range(
        len(mechanisms)
    )

    bar_width = 0.35

    activation_axes.bar(
        [
            x - bar_width / 2
            for x in x_positions
        ],
        [
            p0_summary["activation_counts"][m]
            for m in mechanisms
        ],
        width=bar_width,
        label="P0",
        color="tab:blue"
    )

    activation_axes.bar(
        [
            x + bar_width / 2
            for x in x_positions
        ],
        [
            b1_summary["activation_counts"][m]
            for m in mechanisms
        ],
        width=bar_width,
        label="B1",
        color="tab:orange"
    )

    activation_axes.set_xticks(
        list(x_positions)
    )

    activation_axes.set_xticklabels(
        mechanisms
    )

    activation_axes.set_title(
        "Activations K1a / K1b / K2 "
        "(somme, toutes graines)",
        fontsize=9
    )

    activation_axes.legend(
        fontsize=7
    )

    figure.suptitle(
        scenario_name
        + " — comparaison P0 contre B1",
        fontsize=12
    )

    figure.tight_layout(
        rect=[0, 0, 1, 0.94]
    )

    figure.savefig(
        output_path,
        dpi=130
    )

    plt.close(figure)

    return p0_summary, b1_summary


# ================================================================
# 15. FIGURE GLOBALE COMPLÉMENTAIRE (GAINS RELATIFS)
# ================================================================
def figure_global_summary_p0_vs_b1_gains(
    rows,
    case_studies,
    output_path
):

    metrics = [
        ("energy_mean", "Énergie", False),
        ("latency_mean", "Latence", False),
        (
            "authentication_mean",
            "Authentification",
            True
        ),
        ("key_quality_mean", "Qualité de clé", True),
        ("service_rate", "Taux de service", True)
    ]

    scenario_ids = [
        case_study["scenario_id"]
        for case_study in case_studies
    ]

    gains_table = []

    for scenario_id in scenario_ids:

        p0_summary = (
            compute_scenario_policy_summary(
                rows,
                scenario_id,
                "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS"
            )
        )

        b1_summary = (
            compute_scenario_policy_summary(
                rows,
                scenario_id,
                "B1-CONVENTIONAL"
            )
        )

        row_gains = []

        for field, _, higher_is_better in (
            metrics
        ):

            p0_value = p0_summary[field]
            b1_value = b1_summary[field]

            if b1_value == 0:

                gain_percent = 0.0

            elif higher_is_better:

                gain_percent = (
                    100.0
                    * (p0_value - b1_value)
                    / abs(b1_value)
                )

            else:

                gain_percent = (
                    100.0
                    * (b1_value - p0_value)
                    / abs(b1_value)
                )

            row_gains.append(
                gain_percent
            )

        gains_table.append(
            row_gains
        )

    figure, axes = plt.subplots(
        figsize=(
            12.0,
            1.2 + 0.6 * len(scenario_ids)
        )
    )

    axes.axis("off")

    column_labels = [
        label for _, label, _ in metrics
    ]

    row_labels = [
        scenario_full_name(scenario_id)
        for scenario_id in scenario_ids
    ]

    cell_text = [
        [
            format(value, "+.1f") + " %"
            for value in row
        ]
        for row in gains_table
    ]

    table = axes.table(
        cellText=cell_text,
        rowLabels=row_labels,
        colLabels=column_labels,
        loc="center",
        cellLoc="center"
    )

    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.8)

    axes.set_title(
        "Gains relatifs de P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS par "
        "rapport à B1-CONVENTIONAL (positif = P0 "
        "meilleur)\n(énergie/latence : réduction "
        "relative ; authentification/clé/service : "
        "amélioration relative)",
        fontsize=10
    )

    figure.tight_layout()

    figure.savefig(
        output_path,
        dpi=130
    )

    plt.close(figure)

    return gains_table


# ================================================================
# 16. FRONT DE PARETO — LECTURE D'INSTANTANÉS CAPTURÉS
# ================================================================
#
# Les instantanés (objectifs complets, admissibilité, motifs de
# rejet, front, décision sélectionnée) sont capturés séparément
# par capture_pareto_snapshots.py, car le journal CSV ne
# conserve pas les vecteurs d'objectifs des décisions non
# sélectionnées.
def figure_pareto_front_energy_auth(
    snapshot,
    scenario_name,
    output_path
):

    _figure_pareto_projection(
        snapshot,
        scenario_name,
        x_field="energy",
        y_field="authentication",
        x_label="Énergie (J) — plus faible = meilleur",
        y_label=(
            "Robustesse d'authentification — "
            "plus élevée = meilleur"
        ),
        best_direction_text=(
            "faible énergie + forte authentification"
        ),
        best_direction_xy=(0.05, 0.95),
        # authentication_robustness = 1 - P_FA est borné
        # dans [0, 1] par construction
        # (physec_dm/authentication.py,
        # calculate_a1_robustness/calculate_a2_robustness).
        # Un intervalle fixe évite qu'un écart de quelques
        # 1e-8 entre deux décisions quasi parfaites ne soit
        # dilaté par la notation scientifique à décalage de
        # matplotlib en un axe trompeur (constaté lors de la
        # vérification visuelle de ce script : un écart réel
        # de 6,7e-8 s'affichait comme si l'authentification
        # variait de 1,0 à -6,6).
        y_limits=(0.0, 1.05),
        output_path=output_path
    )


def figure_pareto_front_latency_key(
    snapshot,
    scenario_name,
    output_path
):

    _figure_pareto_projection(
        snapshot,
        scenario_name,
        x_field="latency",
        y_field="key_quality",
        x_label=(
            "Latence normalisée — "
            "plus faible = meilleur"
        ),
        y_label="Qualité de clé — plus élevée = meilleur",
        best_direction_text=(
            "faible latence + forte qualité de clé"
        ),
        best_direction_xy=(0.05, 0.95),
        # key_quality est également borné dans [0, 1]
        # (calculate_k0_quality / calculate_k1_quality /
        # calculate_k2_quality) — même correctif que pour
        # figure_pareto_front_energy_auth.
        y_limits=(0.0, 1.05),
        output_path=output_path
    )


def _figure_pareto_projection(
    snapshot,
    scenario_name,
    x_field,
    y_field,
    x_label,
    y_label,
    best_direction_text,
    best_direction_xy,
    output_path,
    y_limits=None
):

    periods = snapshot["periods"]

    figure, axes_list = plt.subplots(
        1,
        len(periods),
        figsize=(5.5 * len(periods), 5.0)
    )

    if len(periods) == 1:

        axes_list = [axes_list]

    for axes, period in zip(
        axes_list,
        periods
    ):

        for policy_id, marker_shape in [
            ("P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS", "o"),
            ("B1-CONVENTIONAL", "s")
        ]:

            evaluations = period["policies"].get(
                policy_id,
                {}
            ).get("evaluations", [])

            selected_name = period[
                "policies"
            ].get(
                policy_id,
                {}
            ).get(
                "selected_decision_name"
            )

            for evaluation in evaluations:

                x_value = evaluation.get(x_field)
                y_value = evaluation.get(y_field)

                if x_value is None or (
                    y_value is None
                ):

                    continue

                is_selected = (
                    evaluation["decision_name"]
                    == selected_name
                )

                if not evaluation["admissible"]:

                    color = "lightgrey"
                    zorder = 1

                elif evaluation[
                    "on_pareto_front"
                ]:

                    color = (
                        "tab:blue"
                        if policy_id
                        == "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS"
                        else "tab:orange"
                    )
                    zorder = 3

                else:

                    color = "grey"
                    zorder = 2

                axes.scatter(
                    [x_value],
                    [y_value],
                    marker=(
                        "*"
                        if is_selected
                        else marker_shape
                    ),
                    s=(
                        220
                        if is_selected
                        else 60
                    ),
                    color=color,
                    edgecolors="black",
                    linewidths=0.5,
                    zorder=zorder
                )

                label = (
                    evaluation["decision_name"]
                )

                if not evaluation["admissible"]:

                    reasons = evaluation.get(
                        "rejection_reasons",
                        ""
                    )

                    label += (
                        "\n("
                        + reasons.split(";")[0]
                        + ")"
                    )

                axes.annotate(
                    label,
                    (x_value, y_value),
                    fontsize=6,
                    xytext=(3, 3),
                    textcoords="offset points"
                )

        axes.annotate(
            "meilleure direction :\n"
            + best_direction_text,
            xy=best_direction_xy,
            xycoords="axes fraction",
            xytext=best_direction_xy,
            fontsize=7,
            style="italic",
            ha="left" if best_direction_xy[0]
            < 0.5 else "right",
            va="top"
        )

        axes.set_xlabel(
            x_label,
            fontsize=8
        )

        axes.set_ylabel(
            y_label,
            fontsize=8
        )

        if y_limits is not None:

            axes.set_ylim(*y_limits)

        axes.set_title(
            period["label"]
            + " (période "
            + str(period["step_index"])
            + ")",
            fontsize=9
        )

    figure.suptitle(
        scenario_name
        + " — front de Pareto à des périodes "
        "représentatives\n(rond/carré = P0/B1 ; "
        "couleur pleine = front de Pareto ; "
        "gris clair = inadmissible avec motif ; "
        "étoile = décision sélectionnée)",
        fontsize=10
    )

    figure.tight_layout(
        rect=[0, 0, 1, 0.86]
    )

    figure.savefig(
        output_path,
        dpi=130
    )

    plt.close(figure)
