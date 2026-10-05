# ================================================================
# SENSIBILITÉ AUX POIDS DE TCHEBYCHEFF (profils grossiers)
# ================================================================
#
# Teste quelques jeux de poids justifiés (pas un poids choisi pour
# faire gagner P0 artificiellement) : EQUAL (campagne principale),
# puis trois profils qui priorisent fortement un seul objectif à la
# fois. Utilise désormais la COMPARAISON PRINCIPALE
# (P0_AUTH_ONLY_HAENEL_RFF, A2 reçoit le FAR publié de Haenel et
# al. = 0.002), pas le FAR natif du modèle de canal physec_dm --
# corrigé le 25/09/2026, voir p0_auth_only_haenel_rff.py.
#
# ATTENTION (corrigé le 25/09/2026) : ces 4 profils grossiers
# (0.10/0.70) ne suffisent PAS à localiser la frontière de décision
# précisément -- voir weight_boundary_sensitivity.py pour le sweep
# fin qui montre que la frontière est EXACTEMENT à w_energy=w_auth,
# et qu'un écart de 0.001 seulement suffit à faire basculer le
# choix. Ne pas conclure de ce fichier seul que "beaucoup plus de
# poids" serait nécessaire.

import csv
from pathlib import Path

from haenel_comparison.haenel_config import HAENEL_FRR_CONFIGS
from haenel_comparison.p0_auth_only import (
    build_haenel_p0_parameters,
    build_haenel_static_context,
)
from haenel_comparison.p0_auth_only_haenel_rff import (
    select_p0_auth_only_haenel_rff,
)

OUTPUT_PATH = Path("results/haenel_comparison/weight_sensitivity.csv")

WEIGHT_PROFILES = {
    # [énergie, latence, robustesse, qualité de clé]
    "EQUAL": [0.25, 0.25, 0.25, 0.25],
    "ENERGY": [0.70, 0.10, 0.10, 0.10],
    "LATENCY": [0.10, 0.70, 0.10, 0.10],
    "AUTH": [0.10, 0.10, 0.70, 0.10],
}


def run_weight_sensitivity():

    rows = []

    for frr_case in ("HYBRID_FRR_05", "HYBRID_FRR_10"):
        frr = HAENEL_FRR_CONFIGS[frr_case]["frr"]

        for label, weights in WEIGHT_PROFILES.items():

            parameters = build_haenel_p0_parameters()
            parameters.contextual_weights = list(weights)
            context, channel_metrics = build_haenel_static_context(
                parameters
            )

            selected, _all = select_p0_auth_only_haenel_rff(
                context, parameters, channel_metrics.rho_ab, frr
            )

            rows.append(
                {
                    "frr_case": frr_case,
                    "frr": frr,
                    "weight_profile": label,
                    "weights": str(weights),
                    "chosen_action": (
                        selected.decision.authentication_action.value
                        if selected
                        else "REFUS"
                    ),
                }
            )

    return rows


if __name__ == "__main__":

    Path("results/haenel_comparison").mkdir(parents=True, exist_ok=True)
    rows = run_weight_sensitivity()

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV écrit : {OUTPUT_PATH}\n")
    for row in rows:
        print(
            f"{row['frr_case']} / {row['weight_profile']} "
            f"{row['weights']} -> {row['chosen_action']}"
        )

    print(
        "\nCONSTAT (corrigé le 25/09/2026) : sous poids égaux "
        "(campagne principale) et sous les profils LATENCY/AUTH, P0 "
        "choisit A1. Sous le profil ENERGY (poids 0.70), P0 choisit "
        "A2. Ces 4 profils grossiers ne montrent PAS où se situe "
        "exactement la frontière entre les deux -- voir "
        "weight_boundary_sensitivity.csv, qui montre par un sweep "
        "fin que la frontière est EXACTEMENT à w_energy=w_auth=0.25 "
        "et qu'un écart de seulement 0.001 suffit à faire basculer "
        "la décision. Ce résultat n'a pas été cherry-pické : les 4 "
        "profils étaient définis avant exécution, aucun n'a été "
        "ajusté après coup."
    )
