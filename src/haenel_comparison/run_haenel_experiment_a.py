# ================================================================
# EXPÉRIENCE A — ÉNERGIE HAENEL (30 graines, FRR=5% et FRR=10%)
# ================================================================
#
# Uniquement des messages légitimes, aucun attaquant (voir
# haenel_config.py, note Section 3). B5_HAENEL_CALIBRATED (transposition
# calibrée du mécanisme de Haenel et al., PAS une "reproduction
# littérale/exacte" -- voir __init__.py et WORK_LOG.md, correction
# du 25/09/2026) est stochastique (30 réalisations) ; P0_AUTH_ONLY
# est déterministe sur un contexte statique (une seule valeur,
# répétée pour lisibilité dans le tableau plutôt que "simulée" 30
# fois pour de faux).
#
# PREMIÈRE AUTHENTIFICATION COMPLÈTE (Haenel et al., Section 6.3.3,
# Fig. 11) : "Due to the first full authentication, the hybrid
# protocol was a little more energy-demanding at the start of the
# experiment." Convention retenue ici, documentée explicitement
# (voir haenel_energy_adapter.initial_full_auth_overhead_mJ) :
# EFFECTIVE_FIXED_HYBRID_OVERHEAD_MJ (calibré, PAS un coût physique
# exact) est ajouté UNE SEULE FOIS, au message d'indice 0, pour les
# cas HYBRID uniquement (jamais RFF_ONLY, cas limite théorique "no
# fall back" du papier ; jamais MAC_ONLY, où chaque message est déjà
# une authentification complète par définition).

import csv
import statistics
from pathlib import Path

from haenel_comparison.haenel_b5 import (
    simulate_haenel_reference_messages,
    summarize_haenel_events,
)
from haenel_comparison.haenel_config import (
    HAENEL_FRR_CONFIGS,
    N_MESSAGES,
    PRIMARY_FRR_CASE,
    SECONDARY_FRR_CASE,
)
from haenel_comparison.haenel_energy_adapter import (
    a2_realized_energy_mJ,
    a1_energy_mJ,
    initial_full_auth_overhead_mJ,
)
from haenel_comparison.p0_auth_only_haenel_scale import (
    simulate_p0_auth_only_haenel_scale,
    summarize_p0_haenel_scale_events,
)
from haenel_comparison.p0_auth_only_haenel_rff import (
    simulate_p0_auth_only_haenel_rff,
    summarize_p0_haenel_rff_events,
)

OUTPUT_DIR = Path("results/haenel_comparison")

SEED_COUNT = 30
FIRST_SEED = 9800


def energy_for_event_mJ(event):
    """Énergie réalisée d'un message B5_HAENEL_CALIBRATED, sur
    l'échelle Haenel et al. (haenel_energy_adapter), cohérente avec
    Option A en espérance (voir tests/test_energy_option_a.py).

    ATTENTION (bug corrigé) : il ne faut JAMAIS brancher sur
    event.chosen_auth ici. Dans le protocole hybride de Haenel et
    al., le RFF est TOUJOURS tenté en premier (Section 4.5) -- un
    message "replié" (chosen_auth == "A1") a donc payé le coût de
    base RFF ET le surcoût du challenge-response MAC, pas
    uniquement le coût MAC seul. Seul le cas MAC_ONLY (frr=None,
    aucune tentative RFF du tout, Section 6.3.1) utilise
    a1_energy_mJ() en direct.

    Le surcoût de première authentification complète (message
    d'indice 0, cas HYBRID uniquement) est ajouté par l'appelant
    (run_b5_seed), pas ici -- cette fonction reste le coût par
    message "en régime établi"."""

    if event.frr is None:
        return a1_energy_mJ()
    return a2_realized_energy_mJ(event.rff_rejected)


def run_b5_seed(case_name, seed):

    frr = HAENEL_FRR_CONFIGS[case_name]["frr"]
    events = simulate_haenel_reference_messages(
        frr=frr, n_messages=N_MESSAGES, seed=seed
    )
    summary = summarize_haenel_events(events)

    total_energy_mJ = sum(energy_for_event_mJ(e) for e in events)

    # Convention explicite (voir en-tête du fichier) : le surcoût de
    # première authentification complète est ajouté UNE SEULE FOIS,
    # sur la campagne entière, pour les cas HYBRID uniquement (frr
    # strictement positif). RFF_ONLY (frr=0.0) et MAC_ONLY (frr=None)
    # n'en reçoivent jamais.
    initial_full_auth_applied = frr is not None and frr > 0.0
    if initial_full_auth_applied:
        total_energy_mJ += initial_full_auth_overhead_mJ()

    return {
        "case": case_name,
        "seed": seed,
        "n_rff_direct": summary["n_rff_direct"],
        "n_fallback_mac": summary["n_fallback_mac"],
        "observed_fallback_rate": summary["observed_fallback_rate"],
        "service_rate": 1.0,   # Haenel et al. : chaque message
                                 # finit toujours authentifié, par
                                 # RFF ou par repli MAC -- pas de
                                 # notion de refus de service dans
                                 # ce protocole.
        "initial_full_auth_overhead_mJ_applied": (
            initial_full_auth_overhead_mJ()
            if initial_full_auth_applied else 0.0
        ),
        "total_energy_mJ": total_energy_mJ,
        "mean_energy_per_message_mJ": total_energy_mJ / N_MESSAGES,
    }


def mean_std_ci95(values):

    n = len(values)
    mean = statistics.mean(values)
    std = statistics.stdev(values) if n > 1 else 0.0
    ci95_half_width = 1.96 * std / (n ** 0.5) if n > 1 else 0.0

    return {
        "mean": mean,
        "std": std,
        "ci95_low": mean - ci95_half_width,
        "ci95_high": mean + ci95_half_width,
    }


METRICS_TO_SUMMARIZE = [
    "n_rff_direct",
    "n_fallback_mac",
    "observed_fallback_rate",
    "total_energy_mJ",
    "mean_energy_per_message_mJ",
]


def run_experiment_a():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    seeds = list(range(FIRST_SEED, FIRST_SEED + SEED_COUNT))

    all_b5_rows = []
    summary_rows = []

    for case_name in (PRIMARY_FRR_CASE, SECONDARY_FRR_CASE):

        case_rows = [
            run_b5_seed(case_name, seed) for seed in seeds
        ]
        all_b5_rows.extend(case_rows)

        stats_for_case = {"case": case_name, "n_seeds": len(seeds)}

        for metric in METRICS_TO_SUMMARIZE:
            values = [row[metric] for row in case_rows]
            stats = mean_std_ci95(values)
            for stat_name, stat_value in stats.items():
                stats_for_case[f"{metric}_{stat_name}"] = stat_value

        summary_rows.append(stats_for_case)

    # ------------------------------------------------------------
    # P0_AUTH_ONLY_HAENEL_RFF (COMPARAISON PRINCIPALE, 25/09/2026) :
    # A2 reçoit le FAR publié de Haenel et al. (0.002) -- voir
    # p0_auth_only_haenel_rff.py. Déterministe -- une seule ligne
    # par FRR, explicitement étiquetée comme telle.
    # ------------------------------------------------------------

    p0_rff_rows = []

    for case_name in (PRIMARY_FRR_CASE, SECONDARY_FRR_CASE):

        frr = HAENEL_FRR_CONFIGS[case_name]["frr"]
        events = simulate_p0_auth_only_haenel_rff(
            frr, n_messages=N_MESSAGES
        )
        summary = summarize_p0_haenel_rff_events(events)

        p0_rff_rows.append(
            {
                "case": case_name,
                "frr": frr,
                "deterministic": True,
                "n_a1": summary["n_a1"],
                "n_a2": summary["n_a2"],
                "total_energy_mJ": summary["total_energy_mJ"],
                "mean_energy_per_message_mJ": (
                    summary["mean_energy_per_message_mJ"]
                ),
                "far_used": summary["far_used"],
                "far_status": summary["far_status"],
            }
        )

    # ------------------------------------------------------------
    # P0_NATIVE_RFF_SENSITIVITY (SECONDAIRE, 25/09/2026) : A2 reçoit
    # le FAR NATIF du modèle de canal physec_dm (~8.39e-5, contexte
    # SNR ASSUMED) -- répond à "que ferait P0 avec son propre modèle
    # statistique RFF ?", JAMAIS mélangée à la comparaison principale
    # ci-dessus. Voir p0_auth_only_haenel_scale.py.
    # ------------------------------------------------------------

    p0_native_rows = []

    for case_name in (PRIMARY_FRR_CASE, SECONDARY_FRR_CASE):

        frr = HAENEL_FRR_CONFIGS[case_name]["frr"]
        events = simulate_p0_auth_only_haenel_scale(
            frr, n_messages=N_MESSAGES
        )
        summary = summarize_p0_haenel_scale_events(events)

        p0_native_rows.append(
            {
                "case": case_name,
                "frr": frr,
                "deterministic": True,
                "n_a1": summary["n_a1"],
                "n_a2": summary["n_a2"],
                "total_energy_mJ": summary["total_energy_mJ"],
                "mean_energy_per_message_mJ": (
                    summary["mean_energy_per_message_mJ"]
                ),
            }
        )

    # ------------------------------------------------------------
    # Export CSV
    # ------------------------------------------------------------

    b5_raw_path = OUTPUT_DIR / "b5_option_a_runs_30seeds.csv"
    with b5_raw_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_b5_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_b5_rows)

    summary_path = OUTPUT_DIR / "summary_statistics_experiment_a.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    p0_rff_path = OUTPUT_DIR / "p0_auth_only_haenel_rff_deterministic.csv"
    with p0_rff_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(p0_rff_rows[0].keys()))
        writer.writeheader()
        writer.writerows(p0_rff_rows)

    p0_native_path = (
        OUTPUT_DIR / "p0_native_rff_sensitivity_deterministic.csv"
    )
    with p0_native_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(p0_native_rows[0].keys()))
        writer.writeheader()
        writer.writerows(p0_native_rows)

    return all_b5_rows, summary_rows, p0_rff_rows, p0_native_rows, {
        "b5_raw": b5_raw_path,
        "summary": summary_path,
        "p0_rff": p0_rff_path,
        "p0_native": p0_native_path,
    }


if __name__ == "__main__":

    _all_b5, summary_rows, p0_rff_rows, p0_native_rows, paths = (
        run_experiment_a()
    )

    print(f"Expérience A -- {SEED_COUNT} graines, "
          f"{PRIMARY_FRR_CASE} et {SECONDARY_FRR_CASE}\n")

    for row in summary_rows:
        print(f"--- {row['case']} (n={row['n_seeds']}) ---")
        print(
            f"  énergie totale/300s : "
            f"{row['total_energy_mJ_mean']:.3f} mJ "
            f"(sigma={row['total_energy_mJ_std']:.3f}, "
            f"IC95%=[{row['total_energy_mJ_ci95_low']:.3f}, "
            f"{row['total_energy_mJ_ci95_high']:.3f}])"
        )
        print(
            f"  énergie/message      : "
            f"{row['mean_energy_per_message_mJ_mean']:.4f} mJ "
            f"(sigma={row['mean_energy_per_message_mJ_std']:.4f})"
        )
        print(
            f"  n RFF direct         : "
            f"{row['n_rff_direct_mean']:.2f} "
            f"(sigma={row['n_rff_direct_std']:.2f})"
        )
        print(
            f"  n fallback MAC       : "
            f"{row['n_fallback_mac_mean']:.2f} "
            f"(sigma={row['n_fallback_mac_std']:.2f})"
        )
        print(
            f"  taux repli observé   : "
            f"{row['observed_fallback_rate_mean']:.4f} "
            f"(sigma={row['observed_fallback_rate_std']:.4f})\n"
        )

    print("--- P0_AUTH_ONLY_HAENEL_RFF (COMPARAISON PRINCIPALE, "
          "FAR(A2) publié Haenel) ---")
    for row in p0_rff_rows:
        print(
            f"  {row['case']} (FRR={row['frr']}, FAR={row['far_used']}): "
            f"A1={row['n_a1']}, A2={row['n_a2']}, "
            f"énergie totale={row['total_energy_mJ']:.3f} mJ"
        )

    print("--- P0_NATIVE_RFF_SENSITIVITY (SECONDAIRE, FAR natif "
          "physec_dm) ---")
    for row in p0_native_rows:
        print(
            f"  {row['case']} (FRR={row['frr']}): "
            f"A1={row['n_a1']}, A2={row['n_a2']}, "
            f"énergie totale={row['total_energy_mJ']:.3f} mJ"
        )

    print(f"\nCSV écrits :")
    for name, path in paths.items():
        print(f"  {name}: {path}")
