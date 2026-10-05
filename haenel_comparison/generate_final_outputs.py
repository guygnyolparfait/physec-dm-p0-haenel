# ================================================================
# FIGURE 4 (sécurité) + FIGURE 5 (frontière des poids) + TABLEAUX
# FINAUX (comparaison principale + extension exploratoire séparée)
# ================================================================
#
# CORRECTION 2 (25/09/2026) : Figure 4 utilisait la campagne
# insuffisante (~450 tentatives). Elle utilise maintenant la
# campagne Monte-Carlo dédiée (security_monte_carlo.py, >=100 000
# tentatives/politique, IC95% Clopper-Pearson), en échelle
# logarithmique -- indispensable puisque le FAR de P0 (borne
# théorique) et celui de B5 (publié) diffèrent de ~16 ordres de
# grandeur. La barre P0 est délibérément affichée comme une LIMITE
# DE DÉTECTION (IC95% supérieur), jamais comme "0", pour ne pas
# suggérer une preuve expérimentale de supériorité de sécurité.
#
# CORRECTION (passe finale, 25/09/2026) : Figure 5 remplace les 4
# grosses barres EQUAL/ENERGY/LATENCY/AUTH (qui ne montraient pas où
# se situe la frontière) par la courbe du sweep fin
# (weight_boundary_sensitivity.csv), qui montre que la frontière est
# EXACTEMENT à w_energy=w_auth. Le tableau de synthèse principal
# n'inclut plus P0_COMPLETE (extension hors-périmètre, gestion de
# clé absente chez Haenel et al.) : voir
# p0_complete_extension_table.csv, une table SÉPARÉE.

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from haenel_comparison.haenel_config import HAENEL_FRR_CONFIGS

RESULTS_DIR = Path("results/haenel_comparison")
FIGURES_DIR = RESULTS_DIR / "figures"


def generate_figure_4_security():

    with (RESULTS_DIR / "security_monte_carlo.csv").open(
        encoding="utf-8"
    ) as f:
        rows = {r["policy"]: r for r in csv.DictReader(f)}

    b5_key = next(k for k in rows if k.startswith("B5"))
    p0_key = next(k for k in rows if k.startswith("P0"))
    b5 = rows[b5_key]
    p0 = rows[p0_key]

    b5_far = float(b5["empirical_far"])
    b5_ci_low = float(b5["ci95_low"])
    b5_ci_high = float(b5["ci95_high"])

    p0_detection_limit = float(p0["ci95_high"])  # jamais 0 affiché
    p0_theoretical = float(p0["expected_far"])
    n_attempts = int(b5["n_attempts"])

    fig, ax = plt.subplots(figsize=(7, 5.5))

    # Pas de "caps" sur la barre d'erreur (demande explicite : moins
    # d'artifice visuel) -- une simple ligne verticale fine suffit à
    # montrer l'IC95%.
    ax.bar(
        [0], [b5_far],
        yerr=[[b5_far - b5_ci_low], [b5_ci_high - b5_far]],
        capsize=0, error_kw={"elinewidth": 1.5},
        color="#DD8452", width=0.5,
        label="B5_HAENEL_CALIBRATED : FAR empirique (IC95%)",
    )
    ax.bar(
        [1], [p0_detection_limit],
        color="none", edgecolor="#55A868", hatch="///", width=0.5,
        label="P0 : limite de détection IC95% (0/100 000 mesuré)",
    )
    ax.scatter(
        [1], [p0_theoretical], color="#2E7D32", marker="x", s=80, zorder=5,
        label="P0 : borne théorique du modèle (non mesurable ici)",
    )
    ax.axhline(
        0.002, color="gray", linestyle="--", linewidth=1,
        label="FAR publié Haenel et al. = 0,20%",
    )

    n_attempts_str = f"{n_attempts:,}".replace(",", " ")

    ax.set_yscale("log")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(
        ["B5_HAENEL_CALIBRATED (A2/RFF)", "P0_AUTH_ONLY_HAENEL_RFF (A1)"]
    )
    ax.set_ylabel("FAR (échelle logarithmique)")
    ax.set_title(
        f"Figure 4 — Sécurité : FAR empirique vs théorique\n"
        f"(Monte-Carlo {n_attempts_str} tentatives/politique, IC95% "
        f"Clopper-Pearson)\n"
        f"P0 : illustration du modèle, pas validation expérimentale",
        fontsize=11,
    )
    ax.legend(fontsize=8, loc="center right")
    ax.text(
        1, p0_detection_limit * 1.5,
        "0 accepté sur 100 000 :\nNON une preuve de supériorité\n"
        "(voir texte)",
        ha="center", fontsize=7, color="#2E7D32",
    )
    fig.tight_layout()

    path = FIGURES_DIR / "figure_4_security.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def generate_figure_5_weight_boundary():
    """REMPLACE (25/09/2026) l'ancienne figure à 4 barres grossières
    par la courbe du sweep fin, qui montre où se situe RÉELLEMENT la
    frontière de décision (voir weight_boundary_sensitivity.py)."""

    with (RESULTS_DIR / "weight_boundary_sensitivity.csv").open(
        encoding="utf-8"
    ) as f:
        rows = list(csv.DictReader(f))

    w_energy = [float(r["w_energy"]) for r in rows]
    score_a1 = [float(r["score_A1"]) for r in rows]
    score_a2 = [float(r["score_A2"]) for r in rows]
    actions = [r["selected_action"] for r in rows]

    fig, ax = plt.subplots(figsize=(7.5, 5.5))

    ax.plot(w_energy, score_a1, "o-", color="#C44E52", label="score(A1)")
    ax.plot(w_energy, score_a2, "s-", color="#55A868", label="score(A2)")
    ax.axvline(
        0.25, color="gray", linestyle="--", linewidth=1,
        label="w_energy = w_auth = 0.25 (poids égaux)",
    )

    for x, a1, a2, action in zip(w_energy, score_a1, score_a2, actions):
        y = max(a1, a2)
        ax.annotate(
            action, (x, y), textcoords="offset points", xytext=(0, 8),
            ha="center", fontsize=7,
        )

    ax.set_xlabel("w_energy (avec w_auth = 0.50 - w_energy, "
                  "w_latency = w_qkey = 0.25 fixés)")
    ax.set_ylabel("Score de Tchebycheff (plus bas = meilleur)")
    ax.set_title(
        "Figure 5 — Frontière des poids : score(A1)=w_energy vs "
        "score(A2)=w_auth\n(cas principal FRR=10%, FAR=0.002 publié "
        "-- sweep fin, PAS 4 profils grossiers)"
    )
    ax.legend(fontsize=8)
    fig.tight_layout()

    path = FIGURES_DIR / "figure_5_weight_sensitivity.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def build_master_table():
    """Tableau de synthèse PRINCIPAL : Haenel publié / B5_HAENEL_
    CALIBRATED / P0_AUTH_ONLY_HAENEL_RFF -- les trois éléments
    directement comparables sur l'échelle Haenel et al. P0_COMPLETE
    est délibérément EXCLU d'ici (voir
    build_p0_complete_extension_table, table séparée) : il réactive
    K1a/K1b/K2 avec des coûts qui ne viennent pas de Haenel et al.,
    ce n'est plus une comparaison directe du mécanisme
    d'authentification."""

    rows = []

    # A. Haenel publié
    for case_name, data in HAENEL_FRR_CONFIGS.items():
        rows.append({
            "method": f"A. Haenel et al. (publié) -- {case_name}",
            "energy": f"{data['published_energy_mJ']:.3f} mJ/300s",
            "latency": "N/A (non publié, non comparable)",
            "rauth_or_far": (
                "FAR=0,20% (PUBLISHED_HAENEL pour FRR=10% -- exp. "
                "classification distincte du banc d'essai "
                "énergétique)"
                if case_name == "HYBRID_FRR_10"
                else "N/A (pas de FAR apparié publié pour ce cas)"
                if case_name != "MAC_ONLY" else "N/A"
            ),
            # Section 10B : Haenel et al. ne publie pas de métrique
            # "service rate" identique à la nôtre -- ne jamais
            # attribuer artificiellement "100%".
            "service_pct": "N/A / not separately reported",
            "pct_rff": (
                "100%" if case_name == "RFF_ONLY"
                else "0%" if case_name == "MAC_ONLY"
                else f"{100*(1-data['frr']):.0f}% (attendu)"
            ),
            "pct_mac_direct": (
                "0%" if case_name == "RFF_ONLY"
                else "100%" if case_name == "MAC_ONLY"
                else "N/A (voir pct_fallback -- pas de MAC direct "
                     "hors repli dans ce cas)"
            ),
            "pct_fallback": (
                "N/A" if case_name in ("RFF_ONLY", "MAC_ONLY")
                else f"{100*data['frr']:.0f}% (attendu, inclut la "
                     "1ere authentification complète -- Section "
                     "6.3.3/Fig. 11)"
            ),
            "q_key": "N/A (non géré par Haenel et al.)",
        })

    # Sécurité (Correction 2, 25/09/2026) : campagne Monte-Carlo
    # dédiée (>=100 000 tentatives/politique), remplace les valeurs
    # vagues "N/A (voir Expérience B séparée)" par les vrais
    # chiffres IC95%. Rappel : ces deux FAR ne sont PAS de même
    # nature (KNN publié vs borne cryptographique théorique) --
    # jamais présentés comme directement comparables terme à terme.
    with (RESULTS_DIR / "security_monte_carlo.csv").open(
        encoding="utf-8"
    ) as f:
        security_rows = {r["policy"]: r for r in csv.DictReader(f)}
    security_b5 = next(
        v for k, v in security_rows.items() if k.startswith("B5")
    )
    security_p0 = next(
        v for k, v in security_rows.items() if k.startswith("P0")
    )

    # B. B5_HAENEL_CALIBRATED (30 graines, résumé)
    with (RESULTS_DIR / "summary_statistics_experiment_a.csv").open(
        encoding="utf-8"
    ) as f:
        b5_summary = {r["case"]: r for r in csv.DictReader(f)}

    b5_n_attempts_str = f"{int(security_b5['n_attempts']):,}".replace(
        ",", " "
    )

    for case_name in ("HYBRID_FRR_05", "HYBRID_FRR_10"):
        r = b5_summary[case_name]
        rows.append({
            "method": f"B. B5_HAENEL_CALIBRATED -- {case_name}",
            "energy": (
                f"{float(r['total_energy_mJ_mean']):.3f} +/- "
                f"{float(r['total_energy_mJ_std']):.3f} mJ/300s"
            ),
            "latency": "N/A (non modélisé pour B5)",
            "rauth_or_far": (
                f"FAR={float(security_b5['empirical_far']):.4f} "
                f"(Monte-Carlo {b5_n_attempts_str}, "
                f"IC95%=[{float(security_b5['ci95_low']):.4f}, "
                f"{float(security_b5['ci95_high']):.4f}], publié=0.0020)"
            ),
            "service_pct": "100% (chaque message finit authentifié, "
                           "RFF ou repli -- pas de refus de service "
                           "dans ce protocole)",
            "pct_rff": f"{float(r['n_rff_direct_mean']):.1f}%",
            "pct_mac_direct": "N/A (pas de MAC direct hors repli)",
            "pct_fallback": f"{float(r['n_fallback_mac_mean']):.1f}% "
                            "(inclut la 1ere authentification "
                            "complète, message d'indice 0)",
            "q_key": "N/A",
        })

    # C. P0_AUTH_ONLY_HAENEL_RFF (COMPARAISON PRINCIPALE)
    with (
        RESULTS_DIR / "p0_auth_only_haenel_rff_deterministic.csv"
    ).open(encoding="utf-8") as f:
        p0_rows_csv = {r["case"]: r for r in csv.DictReader(f)}

    p0_n_attempts_str = f"{int(security_p0['n_attempts']):,}".replace(
        ",", " "
    )

    for case_name in ("HYBRID_FRR_05", "HYBRID_FRR_10"):
        r = p0_rows_csv[case_name]
        rows.append({
            "method": (
                f"C. P0_AUTH_ONLY_HAENEL_RFF (comparaison principale, "
                f"A2 reçoit FAR publié Haenel) -- {case_name}"
            ),
            "energy": f"{float(r['total_energy_mJ']):.3f} mJ/300s (déterministe)",
            "latency": "Neutralisée (UNAVAILABLE, voir §2 adapter)",
            "rauth_or_far": (
                f"Rauth=1.0 (choisit A1) ; FAR théorique="
                f"{float(security_p0['expected_far']):.2e} (borne "
                f"crypto idéalisée, PAS mesurée -- 0/"
                f"{p0_n_attempts_str} sur Monte-Carlo, "
                f"IC95% sup.={float(security_p0['ci95_high']):.2e}, "
                f"non comparable au KNN de Haenel et al.)"
            ),
            "service_pct": "100%",
            "pct_rff": f"{r['n_a2']}%",
            "pct_mac_direct": f"{r['n_a1']}%",
            "pct_fallback": "N/A (P0 ne fait pas de repli, il choisit "
                            "une fois pour toutes)",
            "q_key": "1,0 (K0 figé, identique des deux côtés)",
        })

    return rows


def build_p0_complete_extension_table():
    """Table SÉPARÉE (Section 10A) : P0_COMPLETE réactive K1a/K1b/K2
    avec des coûts qui ne viennent PAS de Haenel et al. -- extension
    EXPLORATOIRE, jamais insérée dans le même classement que la
    comparaison principale (build_master_table)."""

    with (RESULTS_DIR / "p0_complete_result.csv").open(
        encoding="utf-8"
    ) as f:
        p0c = next(csv.DictReader(f))

    return [{
        "method": "EXPLORATORY EXTENSION -- P0_COMPLETE "
                  "(K1a/K1b/K2 réactivés)",
        "energy": (
            f"{float(p0c['energy_j_native_scale'])*1000:.3f} mJ "
            "(échelle LoRa/Semtech NATIVE, PAS comparable à Haenel "
            "et al.)"
        ),
        "latency": f"{float(p0c['normalized_latency']):.4f} "
                   "(normalisée, modèle natif)",
        "rauth_or_far": f"Rauth={float(p0c['r_auth']):.6f}",
        "service_pct": (
            "100%" if p0c["refusal_of_service"] == "False" else "0%"
        ),
        "decision": p0c["decision"],
        "q_key": f"{float(p0c['q_key']):.4f}",
        "note": (
            "Hors périmètre de comparaison directe à Haenel et al. "
            "(gestion de clé physique absente de leur article) -- "
            "ne jamais comparer terme à terme avec les lignes A/B/C "
            "du tableau principal."
        ),
    }]


if __name__ == "__main__":

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    fig4 = generate_figure_4_security()
    fig5 = generate_figure_5_weight_boundary()
    print(f"Figures écrites : {fig4}, {fig5}")

    rows = build_master_table()
    table_path = RESULTS_DIR / "master_comparison_table.csv"
    with table_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Tableau principal écrit : {table_path}")
    for row in rows:
        print(f"  {row['method']}")

    extension_rows = build_p0_complete_extension_table()
    extension_path = RESULTS_DIR / "p0_complete_extension_table.csv"
    with extension_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(extension_rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(extension_rows)

    print(f"\nTable d'extension exploratoire écrite (séparée) : "
          f"{extension_path}")
    for row in extension_rows:
        print(f"  {row['method']}")
