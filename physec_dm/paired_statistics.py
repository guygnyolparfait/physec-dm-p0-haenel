# Ce module calcule des comparaisons APPARIÉES entre
# P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS et chaque politique de
# référence (B1 à B4), graine par graine, plutôt que deux
# moyennes indépendantes.
#
# Les mêmes graines communes (Common Random Numbers) sont
# utilisées par toutes les politiques : comparer deux
# moyennes indépendantes gaspille cette conception et
# sous-estime la précision réelle de la comparaison. La
# bonne pratique statistique est de calculer, graine par
# graine :
#
# Delta_r = X_{P0,r} - X_{Bi,r}
#
# puis de calculer la moyenne et l'intervalle de confiance
# à 95 % SUR CES DIFFÉRENCES, pas sur les deux niveaux
# séparément.
from physec_dm.adaptive_monte_carlo import (
    compute_mean_ci95_half_width
)


# Cette fonction calcule, pour une métrique donnée, la
# différence appariée P0 - Bi pour chaque graine commune aux
# deux politiques.
#
# baseline_summaries_by_seed et p0_summaries_by_seed sont des
# dictionnaires {seed: valeur_de_la_métrique}. Seules les
# graines présentes dans les DEUX dictionnaires sont
# utilisées (comparaison strictement appariée).
def compute_paired_differences(
    p0_summaries_by_seed,
    baseline_summaries_by_seed
):

    common_seeds = sorted(
        set(p0_summaries_by_seed)
        & set(baseline_summaries_by_seed)
    )

    if len(common_seeds) == 0:

        raise ValueError(
            "Aucune graine commune entre P0 et la "
            "politique de référence : la comparaison "
            "appariée est impossible."
        )

    differences = []

    for seed in common_seeds:

        p0_value = p0_summaries_by_seed[seed]
        baseline_value = (
            baseline_summaries_by_seed[seed]
        )

        if p0_value is None or baseline_value is None:

            continue

        differences.append(
            p0_value - baseline_value
        )

    return common_seeds, differences


# Cette fonction calcule la statistique appariée complète
# pour une métrique : nombre de graines utilisées, moyenne
# de la différence, demi-largeur de l'IC95 sur la différence,
# et si l'intervalle exclut zéro (différence statistiquement
# distinguable de zéro à 95 %, sous l'approximation normale).
def compute_paired_statistic(
    p0_summaries_by_seed,
    baseline_summaries_by_seed
):

    _, differences = compute_paired_differences(
        p0_summaries_by_seed,
        baseline_summaries_by_seed
    )

    if len(differences) == 0:

        return {
            "sample_size": 0,
            "mean_difference": None,
            "half_width": None,
            "excludes_zero": None
        }

    mean_difference, half_width = (
        compute_mean_ci95_half_width(
            differences
        )
    )

    if half_width == float("inf"):

        excludes_zero = False

    else:

        excludes_zero = (
            abs(mean_difference) > half_width
        )

    return {
        "sample_size": len(differences),
        "mean_difference": mean_difference,
        "half_width": half_width,
        "excludes_zero": excludes_zero
    }


# Cette fonction calcule la statistique appariée pour
# PLUSIEURS métriques à la fois, à partir de résumés par
# graine structurés comme :
#
# summaries_by_seed[seed][metric_name] = valeur
#
# Retourne un dictionnaire {metric_name: statistique}.
def compute_paired_statistics_for_all_metrics(
    p0_summaries_by_seed,
    baseline_summaries_by_seed,
    metric_names
):

    results = {}

    for metric_name in metric_names:

        p0_values_by_seed = {
            seed: summary[metric_name]
            for seed, summary in (
                p0_summaries_by_seed.items()
            )
        }

        baseline_values_by_seed = {
            seed: summary[metric_name]
            for seed, summary in (
                baseline_summaries_by_seed.items()
            )
        }

        results[metric_name] = (
            compute_paired_statistic(
                p0_values_by_seed,
                baseline_values_by_seed
            )
        )

    return results
