# ================================================================
# FIGURES — EXPÉRIENCE A (ÉNERGIE), UNIQUEMENT APRÈS VALIDATION
# ================================================================
#
# Figure 1 : énergie B5_HAENEL_CALIBRATED (30 graines) vs
#            P0_AUTH_ONLY_HAENEL_RFF (comparaison principale),
#            échelle Haenel commune, pour FRR=5% et FRR=10%.
# Figure 2 : proportion RFF direct vs repli MAC (B5) et A2 vs A1
#            (P0), pour les deux FRR.
# Figure 3 : nombre de replis observés en fonction du FRR.
#
# Figure 4 (sécurité/FAR, Monte-Carlo 100 000 tentatives) est
# générée séparément par generate_final_outputs.py.

import csv
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


def _read_summary_rows():

    with (RESULTS_DIR / "summary_statistics_experiment_a.csv").open(
        encoding="utf-8"
    ) as f:
        return list(csv.DictReader(f))


def _read_p0_rows():

    with (
        RESULTS_DIR / "p0_auth_only_haenel_rff_deterministic.csv"
    ).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def generate_figure_1_energy_comparison(summary_rows, p0_rows):
    """REFONTE (demande explicite : "les figures sont trop
    artificielles", "je ne veux plus voir les segments [caps] sur
    la figure 1", "les courbes ne seraient-elles pas mieux que des
    barres ?"). Remplace le diagramme en barres groupées (avec caps
    d'erreur) par une COURBE qui raconte l'histoire : comment
    l'énergie évolue avec le FRR pour Haenel et al./B5, comparée à
    la décision FIXE de P0 -- qui se confond avec le plafond
    MAC_ONLY, quel que soit le FRR. C'est le contraste central de
    toute la comparaison, il doit être visible d'un coup d'œil, pas
    déduit d'une légende à 3 barres.

    Courbes réelles (jamais un simple habillage) :
    - Haenel et al. publié : RFF_ONLY (FRR=0) -> HYBRID_05 -> HYBRID_10
      -- la vraie relation FRR/énergie du papier.
    - B5_HAENEL_CALIBRATED : mêmes 2 points FRR, moyenne Monte-Carlo
      (30 graines), bande d'incertitude IC95% (PAS des caps
      artificiels -- une bande translucide, plus honnête sur la
      forme réelle de l'incertitude).
    - P0_AUTH_ONLY_HAENEL_RFF : ligne PLATE (P0 ne dépend pas du
      FRR, il choisit toujours A1) -- tracée volontairement au même
      niveau que MAC_ONLY publié, pour montrer que la décision de
      P0 équivaut, en énergie, à ignorer complètement le bénéfice du
      RFF.
    """

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
    b5_mean = [
        float(b5_by_case[c]["total_energy_mJ_mean"]) for c in cases
    ]
    b5_ci_low = [
        float(b5_by_case[c]["total_energy_mJ_ci95_low"]) for c in cases
    ]
    b5_ci_high = [
        float(b5_by_case[c]["total_energy_mJ_ci95_high"]) for c in cases
    ]

    p0_by_case = {row["case"]: row for row in p0_rows}
    p0_energy = [
        float(p0_by_case[c]["total_energy_mJ"]) for c in cases
    ]
    # P0 est déterministe et identique aux deux FRR testés (voir
    # rapport Section 11-12) : une seule valeur, tracée en ligne
    # plate sur toute la plage affichée.
    assert abs(p0_energy[0] - p0_energy[1]) < 1e-6
    p0_flat_value = p0_energy[0]

    x_span = [rff_only_frr, max(frr_values)]

    fig, ax = plt.subplots(figsize=(8, 5.5))

    # -- Courbe Haenel et al. publié (la vraie histoire RFF -> repli) --
    ax.plot(
        published_x, published_y, "-o", color="#4C72B0", linewidth=2,
        markersize=7, label="Haenel et al. (publié)", zorder=3,
    )
    for x_val, y_val in zip(published_x, published_y):
        ax.annotate(
            f"{y_val:.0f} mJ", (x_val, y_val),
            textcoords="offset points", xytext=(0, 10),
            ha="center", fontsize=8.5, color="#4C72B0",
        )

    # -- B5_HAENEL_CALIBRATED : bande IC95% (PAS de caps) --
    ax.fill_between(
        frr_values, b5_ci_low, b5_ci_high, color="#DD8452", alpha=0.25,
        label="B5_HAENEL_CALIBRATED (IC95%, 30 graines)", zorder=1,
    )
    ax.plot(
        frr_values, b5_mean, "s--", color="#DD8452", linewidth=1.5,
        markersize=6, zorder=2,
    )

    # -- P0 : ligne plate, volontairement au niveau de MAC_ONLY --
    ax.plot(
        x_span, [p0_flat_value, p0_flat_value], "-", color="#55A868",
        linewidth=2.5, zorder=3,
        label="P0_AUTH_ONLY_HAENEL_RFF (choix fixe, indépendant du FRR)",
    )
    ax.annotate(
        f"P0 = {p0_flat_value:.0f} mJ  (= plafond MAC_ONLY publié)",
        (rff_only_frr, p0_flat_value), textcoords="offset points",
        xytext=(2, -14), ha="left", fontsize=9, color="#2E7D32",
        fontweight="bold",
    )

    ax.set_xlim(-0.008, 0.115)
    ax.set_ylim(330, 605)
    ax.set_xticks([rff_only_frr] + frr_values)
    ax.set_xticklabels(["0 %\n(RFF seul)", "5 %", "10 %"])
    ax.set_xlabel("FRR simulé (taux de faux rejet du RFF)")
    ax.set_ylabel("Énergie totale sur 300 s (mJ)")
    ax.set_title(
        "Figure 1 — L'histoire énergétique : Haenel et al. profite du\n"
        "RFF quand le FRR baisse ; P0 s'en tient toujours au MAC",
        fontsize=12,
    )
    ax.legend(fontsize=8.5, loc="lower right")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / "figure_1_energy_comparison.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def generate_figure_2_decision_split(summary_rows, p0_rows):
    """Répartition des décisions : B5 (RFF direct vs repli MAC)
    vs P0 (A2 vs A1), pour les deux FRR."""

    cases = [PRIMARY_FRR_CASE, SECONDARY_FRR_CASE]
    labels = ["FRR = 5 %", "FRR = 10 %"]

    b5_by_case = {row["case"]: row for row in summary_rows}
    p0_by_case = {row["case"]: row for row in p0_rows}

    b5_rff = [
        float(b5_by_case[c]["n_rff_direct_mean"]) for c in cases
    ]
    b5_fallback = [
        float(b5_by_case[c]["n_fallback_mac_mean"]) for c in cases
    ]

    p0_a2 = [float(p0_by_case[c]["n_a2"]) for c in cases]
    p0_a1 = [float(p0_by_case[c]["n_a1"]) for c in cases]

    fig, axes = plt.subplots(1, 2, figsize=(10, 5), sharey=True)

    for ax, title, top, bottom, top_label, bottom_label in (
        (axes[0], "B5_HAENEL_CALIBRATED (moyenne/30 graines)",
         b5_rff, b5_fallback, "RFF direct", "Repli MAC"),
        (axes[1], "P0_AUTH_ONLY_HAENEL_RFF (déterministe)",
         p0_a2, p0_a1, "A2 (RFF)", "A1 (MAC)"),
    ):
        ax.bar(labels, top, label=top_label, color="#55A868")
        ax.bar(
            labels, bottom, bottom=top, label=bottom_label,
            color="#C44E52",
        )
        ax.set_title(title)
        ax.legend()

    axes[0].set_ylabel("Nombre de messages (sur 100)")
    fig.suptitle(
        "Figure 2 — Répartition des décisions : B5_HAENEL_CALIBRATED vs "
        "P0_AUTH_ONLY_HAENEL_RFF"
    )
    fig.tight_layout()

    path = FIGURES_DIR / "figure_2_decision_split.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def generate_figure_3_fallback_vs_frr(summary_rows):
    """Nombre de replis MAC observés (B5_HAENEL_CALIBRATED) en fonction du
    FRR configuré, avec barres d'erreur (écart-type, 30 graines)."""

    cases = [PRIMARY_FRR_CASE, SECONDARY_FRR_CASE]
    frr_values = [HAENEL_FRR_CONFIGS[c]["frr"] for c in cases]

    b5_by_case = {row["case"]: row for row in summary_rows}
    fallback_mean = [
        float(b5_by_case[c]["n_fallback_mac_mean"]) for c in cases
    ]
    fallback_std = [
        float(b5_by_case[c]["n_fallback_mac_std"]) for c in cases
    ]

    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    ax.errorbar(
        frr_values, fallback_mean, yerr=fallback_std,
        fmt="o-", capsize=0, elinewidth=1.5, color="#C44E52",
    )
    # Ligne théorique FRR * N_MESSAGES pour référence.
    theoretical = [frr * 100 for frr in frr_values]
    ax.plot(
        frr_values, theoretical, "--", color="gray",
        label="Attendu (FRR × 100 messages)",
    )

    ax.set_xlabel("FRR configuré")
    ax.set_ylabel("Nombre de replis MAC observés (sur 100 messages)")
    ax.set_title(
        "Figure 3 — Replis MAC observés (B5_HAENEL_CALIBRATED)\n"
        "en fonction du FRR (moyenne +/- écart-type, 30 graines)",
        fontsize=12,
    )
    ax.legend()
    fig.tight_layout()

    path = FIGURES_DIR / "figure_3_fallback_vs_frr.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


if __name__ == "__main__":

    summary_rows = _read_summary_rows()
    p0_rows = _read_p0_rows()

    paths = [
        generate_figure_1_energy_comparison(summary_rows, p0_rows),
        generate_figure_2_decision_split(summary_rows, p0_rows),
        generate_figure_3_fallback_vs_frr(summary_rows),
    ]

    print("Figures générées :")
    for path in paths:
        print(f"  {path}")

    print(
        "\nFigure 4 (sécurité/FAR, Monte-Carlo 100 000 tentatives) "
        "est générée séparément par generate_final_outputs.py."
    )
