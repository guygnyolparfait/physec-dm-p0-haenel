# ================================================================
# EXPÉRIENCE B — SÉCURITÉ / FAR (distincte de l'Expérience A)
# ================================================================
#
# NE PAS CONFONDRE avec l'Expérience A (énergie/FRR, aucun
# attaquant). Ici, on introduit des tentatives de Mallory et on
# compare le nombre d'acceptations à tort entre B5_HAENEL_CALIBRATED et
# P0_AUTH_ONLY.
#
# Le FAR de référence (0,002) vient de l'expérience de
# CLASSIFICATION de Haenel et al. (Section 6.2, calibration KNN,
# Fig. 9), PAS du banc d'essai énergétique (Section 6.3). C'est une
# TRANSPOSITION explicite de cette valeur dans une campagne
# distincte -- jamais présentée comme mesurée dans le même
# protocole que l'énergie.
#
# mallory_attempt_probability est ASSUMED (non publiée par Haenel
# et al. pour ce protocole précis) : documentée, pas fabriquée en
# silence.
#
# CORRECTION 2 (25/09/2026) : cette campagne (30 graines x ~15
# tentatives/mission, ~450 tentatives au total) est CONSERVÉE pour
# montrer le comportement dans une mission complète de 100 messages,
# mais elle est STATISTIQUEMENT INSUFFISANTE pour estimer un FAR de
# 0,2% (intervalle de confiance bien trop large). L'estimation
# statistiquement valide du FAR (>=50 000 tentatives, IC95%
# Clopper-Pearson) est dans security_monte_carlo.py -- se référer à
# CE fichier pour toute conclusion quantitative sur le FAR, pas à
# celui-ci.

import csv
from pathlib import Path

import numpy as np

from haenel_comparison.haenel_b5 import simulate_haenel_reference_messages
from haenel_comparison.haenel_config import HAENEL_FRR_CONFIGS, N_MESSAGES
from haenel_comparison.p0_auth_only_haenel_scale import (
    select_p0_auth_only_haenel_scale,
)
from haenel_comparison.p0_auth_only import (
    build_haenel_p0_parameters,
    build_haenel_static_context,
)

OUTPUT_DIR = Path("results/haenel_comparison")

# ASSUMED (non publié pour ce protocole -- documenté, pas fabriqué
# en silence). Choisi comme ordre de grandeur raisonnable pour un
# capteur IoT sous pression d'attaque modérée, cohérent avec les
# probabilités d'attaque utilisées dans les scénarios S1-S5 du
# projet (0.10 à 0.30 selon le scénario).
MALLORY_ATTEMPT_PROBABILITY = 0.15

FAR_REFERENCE = 0.002   # PUBLISHED_IN_HAENEL (Section 6.2.2, Fig. 9)

# Borne cryptographique idéalisée pour le MAC (A1) -- reprend la
# même forme que le modèle physec_dm natif (1 - 2^-b_MAC), avec
# b_MAC=32 bits (taille de tag Chaskey-12 tronqué courante).
MAC_FORGERY_PROBABILITY = 2 ** -32   # ASSUMED (taille de tag non
                                       # publiée par Haenel et al.)

SEED_COUNT = 30
FIRST_SEED = 9900


def run_b5_security_seed(seed):
    """B5_HAENEL_CALIBRATED : réutilise la même sélection A1/A2 (FRR=5%,
    cas principal) que l'Expérience A, puis tire séparément les
    tentatives d'attaque et leur acceptation."""

    frr = HAENEL_FRR_CONFIGS["HYBRID_FRR_05"]["frr"]
    events = simulate_haenel_reference_messages(
        frr=frr, n_messages=N_MESSAGES, seed=seed
    )

    rng = np.random.default_rng(seed + 500_000)  # flux distinct de
                                                    # celui du FRR

    n_attempts = 0
    n_accepted = 0

    for event in events:

        if rng.uniform(0.0, 1.0) >= MALLORY_ATTEMPT_PROBABILITY:
            continue

        n_attempts += 1

        far_for_this_message = (
            FAR_REFERENCE
            if event.chosen_auth == "A2"
            else MAC_FORGERY_PROBABILITY
        )

        if rng.uniform(0.0, 1.0) < far_for_this_message:
            n_accepted += 1

    return {
        "policy": "B5_HAENEL_CALIBRATED",
        "seed": seed,
        "n_attempts": n_attempts,
        "n_accepted": n_accepted,
        "empirical_far": (
            n_accepted / n_attempts if n_attempts > 0 else None
        ),
    }


def run_p0_security_seed(seed):
    """P0_AUTH_ONLY : dans ce contexte statique, P0 choisit
    toujours A1 (voir Expérience A / p0_decision_explanation.md).
    On tire les MÊMES tentatives d'attaque (graine identique,
    même flux) et on teste l'acceptation avec le FAR RÉEL calculé
    par le modèle physec_dm pour l'action choisie -- pas une
    valeur recopiée de B5."""

    parameters = build_haenel_p0_parameters()
    context, channel_metrics = build_haenel_static_context(parameters)

    frr = HAENEL_FRR_CONFIGS["HYBRID_FRR_05"]["frr"]
    selected, _all = select_p0_auth_only_haenel_scale(
        context, parameters, channel_metrics.rho_ab, frr
    )
    chosen_action = (
        selected.decision.authentication_action.value
        if selected else None
    )
    far_for_chosen_action = (
        selected.authentication_metrics.far if selected else None
    )

    rng = np.random.default_rng(seed + 500_000)  # même flux que B5

    n_attempts = 0
    n_accepted = 0

    for _ in range(N_MESSAGES):

        if rng.uniform(0.0, 1.0) >= MALLORY_ATTEMPT_PROBABILITY:
            continue

        n_attempts += 1

        if rng.uniform(0.0, 1.0) < far_for_chosen_action:
            n_accepted += 1

    return {
        "policy": "P0_AUTH_ONLY",
        "seed": seed,
        "chosen_action": chosen_action,
        "far_used": far_for_chosen_action,
        "n_attempts": n_attempts,
        "n_accepted": n_accepted,
        "empirical_far": (
            n_accepted / n_attempts if n_attempts > 0 else None
        ),
    }


def mean_std(values):
    values = [v for v in values if v is not None]
    if not values:
        return None, None
    n = len(values)
    mean = sum(values) / n
    if n > 1:
        var = sum((v - mean) ** 2 for v in values) / (n - 1)
        std = var ** 0.5
    else:
        std = 0.0
    return mean, std


def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    seeds = list(range(FIRST_SEED, FIRST_SEED + SEED_COUNT))

    b5_rows = [run_b5_security_seed(s) for s in seeds]
    p0_rows = [run_p0_security_seed(s) for s in seeds]

    with (OUTPUT_DIR / "experiment_b_security_b5.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(f, fieldnames=list(b5_rows[0].keys()))
        writer.writeheader()
        writer.writerows(b5_rows)

    with (OUTPUT_DIR / "experiment_b_security_p0.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(f, fieldnames=list(p0_rows[0].keys()))
        writer.writeheader()
        writer.writerows(p0_rows)

    b5_accepted_mean, b5_accepted_std = mean_std(
        [r["n_accepted"] for r in b5_rows]
    )
    p0_accepted_mean, p0_accepted_std = mean_std(
        [r["n_accepted"] for r in p0_rows]
    )
    b5_attempts_mean, _ = mean_std([r["n_attempts"] for r in b5_rows])

    print(f"Expérience B (sécurité/FAR) -- {SEED_COUNT} graines, "
          f"FRR=5%, mallory_attempt_probability="
          f"{MALLORY_ATTEMPT_PROBABILITY} (ASSUMED)\n")
    print(f"Tentatives moyennes/campagne (300s, 100 msg) : "
          f"{b5_attempts_mean:.2f}")
    print(f"B5_HAENEL_CALIBRATED       : acceptées={b5_accepted_mean:.3f} "
          f"+/- {b5_accepted_std:.3f} (FAR utilisé pour A2="
          f"{FAR_REFERENCE}, pour A1={MAC_FORGERY_PROBABILITY:.2e})")
    print(f"P0_AUTH_ONLY      : acceptées={p0_accepted_mean:.3f} "
          f"+/- {p0_accepted_std:.3f} (action choisie="
          f"{p0_rows[0]['chosen_action']}, FAR réel du modèle="
          f"{p0_rows[0]['far_used']:.2e})")

    print(
        "\nCONSTAT : P0_AUTH_ONLY choisit A1 dans ce contexte "
        "(voir Expérience A), dont le FAR est la borne "
        "cryptographique idéalisée du modèle physec_dm -- "
        "quasi nulle. B5_HAENEL_CALIBRATED utilise A2 (RFF) la majorité du "
        "temps (95% à FRR=5%), avec le FAR de référence de Haenel "
        "et al. (0,20%, Section 6.2). P0 accepte donc mécaniquement "
        "moins d'attaques dans cette configuration précise -- "
        "CONSÉQUENCE DIRECTE du choix d'authentification établi en "
        "Expérience A, pas un résultat de sécurité indépendant. "
        "ATTENTION : le FAR réel du modèle physec_dm pour A2 dans "
        "ce contexte ASSUMED (~8x10^-5, voir p0_decision_diagnostics.csv) "
        "n'est PAS calibré pour être identique au FAR_reference de "
        "Haenel et al. (0,002) -- les deux valeurs viennent de deux "
        "modèles de FAR différents (chi-2 non centrée pour "
        "physec_dm, KNN empirique pour Haenel et al.) et ne sont "
        "PAS directement comparables terme à terme."
    )


if __name__ == "__main__":
    main()
