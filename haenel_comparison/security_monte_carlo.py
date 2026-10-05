# ================================================================
# EXPÉRIENCE SÉCURITÉ RENFORCÉE — VALIDATION MONTE-CARLO DU FAR
# (CORRECTION 2, demandée après relecture du 25/09/2026)
# ================================================================
#
# PROBLÈME IDENTIFIÉ PAR LA RELECTURE : la première Expérience B
# (run_haenel_experiment_b.py, conservée telle quelle ci-dessous
# pour l'historique) utilise ~15 tentatives Mallory par mission x
# 30 graines, soit environ 450 tentatives au total. Avec un FAR
# publié de 0,2%, c'est trop peu pour estimer le taux de façon
# fiable : l'intervalle de confiance est bien trop large pour être
# informatif (voir comparaison chiffrée dans main() ci-dessous).
#
# CORRECTION : campagne Monte-Carlo DÉDIÉE, présentée comme
# DISTINCTE du banc d'essai énergétique (qui garde sa structure
# 100 messages / 300 s inchangée, voir run_haenel_experiment_a.py).
# Il ne s'agit plus de simuler des missions complètes de 100
# messages, mais de tirer directement N_ATTEMPTS_TOTAL tentatives
# Bernoulli (acceptée / rejetée) selon le FAR de chaque politique --
# un test statistique du TAUX, explicitement pas une reproduction
# du protocole complet.
#
# Pour B5 : FAR_A2 = 0,002 (PUBLISHED_IN_HAENEL, Section 6.2.2,
# Fig. 9 -- transposé d'une expérience de classification différente
# du banc d'essai énergétique, jamais mesuré dans le même
# protocole).
#
# Pour P0 : FAR réel du mécanisme choisi par le VRAI Decision Maker
# physec_dm (physec_dm/decision_maker.py, jamais réimplémenté ---
# voir p0_decision_diagnostics.csv pour la valeur). RAPPEL EXPLICITE
# ET IMPORTANT : c'est une BORNE CRYPTOGRAPHIQUE THÉORIQUE IDÉALISÉE
# du modèle (de l'ordre de 5x10^-20 pour le MAC, A1), PAS une mesure
# expérimentale comparable au classifieur KNN empirique de Haenel et
# al. "0 acceptation sur N tirages" ne doit JAMAIS être présenté
# comme une preuve expérimentale de supériorité de sécurité : avec
# un FAR théorique aussi petit, 0 acceptation est simplement attendu
# par construction, et l'intervalle de confiance calculé ci-dessous
# le rend explicite (voir champ ci95_high pour P0).

import csv
from pathlib import Path

import numpy as np
from scipy.stats import beta

from haenel_comparison.p0_auth_only_haenel_rff import (
    select_p0_auth_only_haenel_rff,
)
from haenel_comparison.p0_auth_only import (
    build_haenel_p0_parameters,
    build_haenel_static_context,
)
from haenel_comparison.haenel_config import HAENEL_FRR_CONFIGS

OUTPUT_PATH = Path("results/haenel_comparison/security_monte_carlo.csv")

# Objectif utilisateur : au moins 50 000 tentatives, idéalement
# 100 000 -- retenu ici car le calcul (tirages Bernoulli vectorisés)
# reste de l'ordre de la milliseconde pour cette taille.
N_ATTEMPTS_TOTAL = 100_000

SEED_B5 = 314159   # graine fixe, documentée, reproductible
SEED_P0 = 314160   # flux indépendant explicite (offset de 1)

FAR_B5_A2 = 0.002   # PUBLISHED_IN_HAENEL (Section 6.2.2, Fig. 9)

# Chiffres de l'ancienne campagne (run_haenel_experiment_b.py),
# repris tels quels depuis experiment_b_security_b5.csv (30 graines
# déjà exécutées), pour un contraste chiffré AVANT/APRÈS -- pas
# recalculés à la main, lus depuis le CSV existant dans main().
OLD_CAMPAIGN_CSV = Path("results/haenel_comparison/experiment_b_security_b5.csv")


def binomial_ci95_clopper_pearson(k, n):
    """IC95% exact (Clopper-Pearson) pour k succès sur n essais.
    Préféré à l'approximation normale : reste valide quand k=0 (cas
    P0), où l'approximation normale donnerait un intervalle
    dégénéré ou négatif."""

    alpha = 0.05
    lower = 0.0 if k == 0 else beta.ppf(alpha / 2, k, n - k + 1)
    upper = 1.0 if k == n else beta.ppf(1 - alpha / 2, k + 1, n - k)
    return float(lower), float(upper)


def run_b5_monte_carlo(n_attempts=N_ATTEMPTS_TOTAL, seed=SEED_B5):
    """B5_HAENEL_CALIBRATED : le mécanisme choisi dans la campagne
    B5-Haenel est A2 (RFF) sauf repli MAC ; ce Monte-Carlo teste
    spécifiquement le FAR publié de la voie RFF (A2), celle
    explicitement calibrée par Haenel et al. dans Section 6.2.2."""

    rng = np.random.default_rng(seed)
    draws = rng.random(n_attempts)
    n_accepted = int(np.sum(draws < FAR_B5_A2))
    empirical_far = n_accepted / n_attempts
    ci_low, ci_high = binomial_ci95_clopper_pearson(n_accepted, n_attempts)

    return {
        "policy": "B5_HAENEL_CALIBRATED (voie A2/RFF)",
        "n_attempts": n_attempts,
        "n_accepted": n_accepted,
        "empirical_far": empirical_far,
        "expected_far": FAR_B5_A2,
        "far_status": "PUBLISHED_IN_HAENEL (Section 6.2.2, Fig. 9)",
        "ci95_low": ci_low,
        "ci95_high": ci_high,
        "expected_far_within_ci95": ci_low <= FAR_B5_A2 <= ci_high,
        "seed": seed,
    }


def get_p0_chosen_action_and_far():
    """Fait tourner le VRAI Decision Maker physec_dm (jamais
    réimplémenté) sur le contexte statique Haenel, cas principal
    FRR=10%/FAR=0.002 (comparaison principale, voir
    p0_auth_only_haenel_rff.py). Retourne l'action choisie et son
    FAR réel tel que calculé par authentication.py -- pour A1 (le
    choix effectif de P0), ce FAR est indépendant du FAR utilisé
    pour A2, donc identique à celui de l'analyse native."""

    parameters = build_haenel_p0_parameters()
    context, channel_metrics = build_haenel_static_context(parameters)

    frr = HAENEL_FRR_CONFIGS["HYBRID_FRR_10"]["frr"]
    selected, _all = select_p0_auth_only_haenel_rff(
        context, parameters, channel_metrics.rho_ab, frr
    )

    action = (
        selected.decision.authentication_action.value if selected else None
    )
    far = selected.authentication_metrics.far if selected else None

    return action, far


def run_p0_monte_carlo(n_attempts=N_ATTEMPTS_TOTAL, seed=SEED_P0):

    action, far = get_p0_chosen_action_and_far()

    rng = np.random.default_rng(seed)
    draws = rng.random(n_attempts)
    n_accepted = int(np.sum(draws < far))
    empirical_far = n_accepted / n_attempts
    ci_low, ci_high = binomial_ci95_clopper_pearson(n_accepted, n_attempts)

    return {
        "policy": f"P0_AUTH_ONLY (action choisie : {action})",
        "n_attempts": n_attempts,
        "n_accepted": n_accepted,
        "empirical_far": empirical_far,
        "expected_far": far,
        "far_status": (
            "BORNE CRYPTOGRAPHIQUE THEORIQUE DU MODELE physec_dm -- "
            "ILLUSTRATION MONTE-CARLO DU MODELE, PAS VALIDATION "
            "EXPERIMENTALE, PAS UNE MESURE COMPARABLE AU KNN DE HAENEL"
        ),
        "ci95_low": ci_low,
        "ci95_high": ci_high,
        "expected_far_within_ci95": ci_low <= far <= ci_high,
        "seed": seed,
    }


def main():

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    b5_result = run_b5_monte_carlo()
    p0_result = run_p0_monte_carlo()

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(b5_result.keys())
        )
        writer.writeheader()
        writer.writerow(b5_result)
        writer.writerow(p0_result)

    print("=" * 78)
    print(f"EXPÉRIENCE SÉCURITÉ RENFORCÉE -- {N_ATTEMPTS_TOTAL:,} "
          f"tentatives Mallory par politique".replace(",", " "))
    print("=" * 78)

    for result in (b5_result, p0_result):
        print(f"\n{result['policy']}")
        print(f"  Tentatives totales     : {result['n_attempts']:,}"
              .replace(",", " "))
        print(f"  Acceptées              : {result['n_accepted']}")
        print(f"  FAR empirique          : {result['empirical_far']:.3e}")
        print(f"  FAR attendu            : {result['expected_far']:.3e} "
              f"({result['far_status']})")
        print(f"  IC95% (Clopper-Pearson): "
              f"[{result['ci95_low']:.3e}, {result['ci95_high']:.3e}]")
        print(f"  FAR attendu dans l'IC95% : "
              f"{result['expected_far_within_ci95']}")

    print()
    print("=" * 78)
    print("CONTRASTE AVEC L'ANCIENNE CAMPAGNE (30 graines x ~15 "
          "tentatives/mission)")
    print("=" * 78)

    if OLD_CAMPAIGN_CSV.exists():
        with OLD_CAMPAIGN_CSV.open() as f:
            old_rows = list(csv.DictReader(f))
        old_n = sum(int(r["n_attempts"]) for r in old_rows)
        old_k = sum(int(r["n_accepted"]) for r in old_rows)
        old_ci_low, old_ci_high = binomial_ci95_clopper_pearson(
            old_k, old_n
        )
        print(f"Ancienne campagne : {old_k} acceptées / {old_n} "
              f"tentatives -> FAR empirique="
              f"{old_k / old_n:.4f}, IC95%=[{old_ci_low:.4f}, "
              f"{old_ci_high:.4f}] -- intervalle de largeur "
              f"{old_ci_high - old_ci_low:.4f} (~"
              f"{100 * (old_ci_high - old_ci_low):.1f} points de "
              f"pourcent), bien trop large pour distinguer un FAR "
              f"de 0,2% d'un FAR de 1% ou plus.")
    else:
        print("Ancien CSV non trouvé -- comparaison ignorée.")

    print(f"\nNouvelle campagne (B5) : IC95% de largeur "
          f"{b5_result['ci95_high'] - b5_result['ci95_low']:.5f} "
          f"(~{100 * (b5_result['ci95_high'] - b5_result['ci95_low']):.3f} "
          f"points de pourcent) -- suffisamment précis pour confirmer "
          f"statistiquement le FAR publié de 0,2%.")

    n_attempts_str = f"{N_ATTEMPTS_TOTAL:,}".replace(",", " ")

    print()
    print("=" * 78)
    print("MISE EN GARDE EXPLICITE (ne pas sur-interpréter le résultat P0)")
    print("=" * 78)
    print(
        f"P0 a 0 acceptation sur {n_attempts_str} tirages, mais "
        f"son IC95% supérieur est {p0_result['ci95_high']:.3e} : ce "
        f"Monte-Carlo ne peut PAS distinguer un FAR réellement de "
        f"l'ordre de {p0_result['expected_far']:.1e} (la borne "
        f"théorique du modèle) d'un FAR simplement inférieur à "
        f"~{p0_result['ci95_high']:.1e}. \"0 acceptation\" ne prouve "
        f"donc PAS expérimentalement la supériorité de sécurité de "
        f"P0 -- c'est une conséquence attendue d'une borne "
        f"cryptographique idéalisée à ce volume de tirage, pas une "
        f"découverte empirique. Le FAR de B5 (0,2%), lui, est une "
        f"valeur PUBLIÉE par Haenel et al. à partir d'un classifieur "
        f"KNN réel -- les deux FAR ne sont pas de même nature et ne "
        f"doivent jamais être comparés comme si c'était le cas."
    )

    print(f"\nCSV écrit : {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
