# ================================================================
# FIGURES EN ANGLAIS POUR L'ARTICLE ANGLAIS (Haenel et al.)
# ================================================================
#
# Produit les quatre figures de l'article en anglais (Figures 1, 2,
# 4 et 5), à partir des mêmes fichiers de résultats que les figures
# françaises (generate_figures_experiment_a.py, generate_final_outputs.py).
# Seuls les libellés changent : aucune valeur n'est recalculée.
#
# Usage (depuis la racine du dépôt) :
#     python -m haenel_comparison.generate_article_figures_en

import csv
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from haenel_comparison.haenel_config import (
    HAENEL_FRR_CONFIGS,
    PRIMARY_FRR_CASE,
    SECONDARY_FRR_CASE,
)

RESULTS_DIR = Path("results/haenel_comparison")
FIGURES_DIR = RESULTS_DIR / "figures"
ARTICLE_DIR = Path("haenel_comparison/article")


def _read_csv(name):
    with (RESULTS_DIR / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def figure_1(summary_rows, p0_rows):
    cases = [PRIMARY_FRR_CASE, SECONDARY_FRR_CASE]
    frr_values = [HAENEL_FRR_CONFIGS[c]["frr"] for c in cases]
    rff_only_frr = HAENEL_FRR_CONFIGS["RFF_ONLY"]["frr"]
    rff_only_energy = HAENEL_FRR_CONFIGS["RFF_ONLY"]["published_energy_mJ"]
    mac_only_energy = HAENEL_FRR_CONFIGS["MAC_ONLY"]["published_energy_mJ"]

    published_x = [rff_only_frr] + frr_values
    published_y = [rff_only_energy] + [
        HAENEL_FRR_CONFIGS[c]["published_energy_mJ"] for c in cases
    ]

    b5_by_case = {row["case"]: row for row in summary_rows}
    b5_mean = [float(b5_by_case[c]["total_energy_mJ_mean"]) for c in cases]
    b5_ci_low = [float(b5_by_case[c]["total_energy_mJ_ci95_low"]) for c in cases]
    b5_ci_high = [float(b5_by_case[c]["total_energy_mJ_ci95_high"]) for c in cases]

    p0_by_case = {row["case"]: row for row in p0_rows}
    p0_energy = [float(p0_by_case[c]["total_energy_mJ"]) for c in cases]
    assert abs(p0_energy[0] - p0_energy[1]) < 1e-6
    p0_flat_value = p0_energy[0]
    x_span = [rff_only_frr, max(frr_values)]

    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.plot(
        published_x, published_y, "-o", color="#4C72B0", linewidth=2,
        markersize=7, label="Haenel et al. (published)", zorder=3,
    )
    for x_val, y_val in zip(published_x, published_y):
        ax.annotate(
            f"{y_val:.0f} mJ", (x_val, y_val), textcoords="offset points",
            xytext=(0, 10), ha="center", fontsize=8.5, color="#4C72B0",
        )
    ax.fill_between(
        frr_values, b5_ci_low, b5_ci_high, color="#DD8452", alpha=0.25,
        label="B5_HAENEL_CALIBRATED (95% CI, 30 seeds)", zorder=1,
    )
    ax.plot(
        frr_values, b5_mean, "s--", color="#DD8452", linewidth=1.5,
        markersize=6, zorder=2,
    )
    ax.plot(
        x_span, [p0_flat_value, p0_flat_value], "-", color="#55A868",
        linewidth=2.5, zorder=3,
        label="P0_AUTH_ONLY_HAENEL_RFF (fixed choice, independent of FRR)",
    )
    ax.annotate(
        f"P0 = {p0_flat_value:.0f} mJ  (= published MAC_ONLY ceiling)",
        (rff_only_frr, p0_flat_value), textcoords="offset points",
        xytext=(2, -14), ha="left", fontsize=9, color="#2E7D32",
        fontweight="bold",
    )
    ax.set_xlim(-0.008, 0.115)
    ax.set_ylim(330, 605)
    ax.set_xticks([rff_only_frr] + frr_values)
    ax.set_xticklabels(["0 %\n(RFF only)", "5 %", "10 %"])
    ax.set_xlabel("Simulated FRR (RFF false rejection rate)")
    ax.set_ylabel("Total energy over 300 s (mJ)")
    ax.set_title(
        "Figure 1 — Energy comparison: Haenel et al. gains from RFF as FRR "
        "decreases;\nP0 keeps the MAC path",
        fontsize=12,
    )
    ax.legend(fontsize=8.5, loc="lower right")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    path = FIGURES_DIR / "figure_1_energy_comparison_en.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def figure_2(summary_rows, p0_rows):
    cases = [PRIMARY_FRR_CASE, SECONDARY_FRR_CASE]
    labels = ["FRR = 5 %", "FRR = 10 %"]
    b5_by_case = {row["case"]: row for row in summary_rows}
    p0_by_case = {row["case"]: row for row in p0_rows}
    b5_rff = [float(b5_by_case[c]["n_rff_direct_mean"]) for c in cases]
    b5_fallback = [float(b5_by_case[c]["n_fallback_mac_mean"]) for c in cases]
    p0_a2 = [float(p0_by_case[c]["n_a2"]) for c in cases]
    p0_a1 = [float(p0_by_case[c]["n_a1"]) for c in cases]

    fig, axes = plt.subplots(1, 2, figsize=(10, 5), sharey=True)
    for ax, title, top, bottom, top_label, bottom_label in (
        (axes[0], "B5_HAENEL_CALIBRATED (mean over 30 seeds)",
         b5_rff, b5_fallback, "RFF direct", "MAC fallback"),
        (axes[1], "P0_AUTH_ONLY_HAENEL_RFF (deterministic)",
         p0_a2, p0_a1, "A2 (RFF)", "A1 (MAC)"),
    ):
        ax.bar(labels, top, label=top_label, color="#55A868")
        ax.bar(labels, bottom, bottom=top, label=bottom_label,
               color="#C44E52")
        ax.set_title(title)
        ax.legend()
    axes[0].set_ylabel("Number of messages (out of 100)")
    fig.suptitle(
        "Figure 2 — Decision split: B5_HAENEL_CALIBRATED vs "
        "P0_AUTH_ONLY_HAENEL_RFF"
    )
    fig.tight_layout()
    path = FIGURES_DIR / "figure_2_decision_split_en.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def figure_4(security_rows):
    rows = {r["policy"]: r for r in security_rows}
    b5 = rows[next(k for k in rows if k.startswith("B5"))]
    p0 = rows[next(k for k in rows if k.startswith("P0"))]

    b5_far = float(b5["empirical_far"])
    b5_ci_low = float(b5["ci95_low"])
    b5_ci_high = float(b5["ci95_high"])
    p0_detection_limit = float(p0["ci95_high"])
    p0_theoretical = float(p0["expected_far"])
    n_attempts = f"{int(b5['n_attempts']):,}".replace(",", " ")

    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.bar(
        [0], [b5_far],
        yerr=[[b5_far - b5_ci_low], [b5_ci_high - b5_far]],
        capsize=0, error_kw={"elinewidth": 1.5},
        color="#DD8452", width=0.5,
        label="B5_HAENEL_CALIBRATED: empirical FAR (95% CI)",
    )
    ax.bar(
        [1], [p0_detection_limit],
        color="none", edgecolor="#55A868", hatch="///", width=0.5,
        label="P0: detection limit, 95% CI (0 of 100 000 observed)",
    )
    ax.scatter(
        [1], [p0_theoretical], color="#2E7D32", marker="x", s=80, zorder=5,
        label="P0: theoretical bound of the model (not measurable here)",
    )
    ax.axhline(
        0.002, color="gray", linestyle="--", linewidth=1,
        label="Published FAR of Haenel et al. = 0.20%",
    )
    ax.set_yscale("log")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(
        ["B5_HAENEL_CALIBRATED (A2/RFF)", "P0_AUTH_ONLY_HAENEL_RFF (A1)"]
    )
    ax.set_ylabel("FAR (logarithmic scale)")
    ax.set_title(
        f"Figure 4 — Security: empirical vs theoretical FAR\n"
        f"(Monte Carlo, {n_attempts} attempts per policy, Clopper-Pearson "
        f"95% CI)\nP0: model illustration, not experimental validation",
        fontsize=11,
    )
    ax.legend(fontsize=8, loc="center right")
    ax.text(
        1, p0_detection_limit * 1.5,
        "0 accepted out of 100 000:\nNOT a proof of superiority\n(see text)",
        ha="center", fontsize=7, color="#2E7D32",
    )
    fig.tight_layout()
    path = FIGURES_DIR / "figure_4_security_en.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def figure_5(boundary_rows):
    w_energy = [float(r["w_energy"]) for r in boundary_rows]
    score_a1 = [float(r["score_A1"]) for r in boundary_rows]
    score_a2 = [float(r["score_A2"]) for r in boundary_rows]
    actions = [r["selected_action"] for r in boundary_rows]

    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    ax.plot(w_energy, score_a1, "o-", color="#C44E52", label="score(A1, MAC)")
    ax.plot(w_energy, score_a2, "s-", color="#55A868", label="score(A2, RFF)")
    ax.axvline(
        0.25, color="gray", linestyle="--", linewidth=1,
        label="w_energy = w_auth = 0.25 (equal weights)",
    )
    for x, a1, a2, action in zip(w_energy, score_a1, score_a2, actions):
        ax.annotate(
            action, (x, max(a1, a2)), textcoords="offset points",
            xytext=(0, 8), ha="center", fontsize=7,
        )
    ax.set_xlabel("w_energy (with w_auth = 0.50 - w_energy, "
                  "w_latency = w_qkey = 0.25 fixed)")
    ax.set_ylabel("Tchebycheff score (lower is better)")
    ax.set_title(
        "Figure 5 — Weight boundary: score(A1) = w_energy vs score(A2) = "
        "w_auth\n(main case FRR=10%, published FAR=0.002; fine sweep of "
        "11 points)"
    )
    ax.legend(fontsize=8)
    fig.tight_layout()
    path = FIGURES_DIR / "figure_5_weight_sensitivity_en.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    summary_rows = _read_csv("summary_statistics_experiment_a.csv")
    p0_rows = _read_csv("p0_auth_only_haenel_rff_deterministic.csv")
    security_rows = _read_csv("security_monte_carlo.csv")
    boundary_rows = _read_csv("weight_boundary_sensitivity.csv")

    paths = [
        figure_1(summary_rows, p0_rows),
        figure_2(summary_rows, p0_rows),
        figure_4(security_rows),
        figure_5(boundary_rows),
    ]
    if ARTICLE_DIR.exists():
        for p in paths:
            shutil.copy2(p, ARTICLE_DIR / p.name)
    for p in paths:
        print(p)


if __name__ == "__main__":
    main()
