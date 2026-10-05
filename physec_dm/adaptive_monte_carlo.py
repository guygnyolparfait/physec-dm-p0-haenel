# Ce module implémente la règle d'arrêt Monte-Carlo
# adaptative bornée exigée par le protocole (Étape 5) :
#
# "Augmenter N_MC jusqu'à ce que la demi-largeur de
# l'intervalle de confiance à 95% soit inférieure à une
# tolérance epsilon_CI définie pour les métriques
# principales."
#
# Borné par un nombre minimal et un nombre maximal de
# graines, fixés AVANT l'exécution (statut politique) :
# minimum 30 graines, lots supplémentaires de 10, maximum
# 150 graines. Les tolérances par métrique sont également
# pré-enregistrées ci-dessous, avant tout lancement de
# campagne.
#
# Statut : ce module ne recalcule aucune métrique
# scientifique (énergie, latence, robustesse, qualité de
# clé) — il consomme des résumés déjà calculés par
# run_five_case_studies.py et ne fait que décider si la
# campagne doit continuer à accumuler des graines.
import math


MINIMUM_SEED_COUNT = 30

SEED_BATCH_SIZE = 10

MAXIMUM_SEED_COUNT = 150


# Tolérances pré-enregistrées, une fois pour toutes, avant
# le lancement de la campagne complète. Statut : politique
# — à balayer en sensibilité si les conclusions s'avèrent
# fragiles à ce choix.
CONVERGENCE_TOLERANCES = {
    "service_rate": {
        "kind": "absolute",
        "tolerance": 0.01
    },
    "mean_energy_j": {
        "kind": "relative",
        "tolerance": 0.05
    },
    "mean_latency_objective": {
        "kind": "relative",
        "tolerance": 0.05
    },
    "mean_authentication_robustness": {
        "kind": "absolute",
        "tolerance": 0.01
    },
    "mean_key_quality": {
        "kind": "absolute",
        "tolerance": 0.01
    }
}


# Cette fonction calcule la moyenne et la demi-largeur de
# l'intervalle de confiance à 95 % (approximation normale,
# 1,96 * écart-type / racine(n)) d'un échantillon de valeurs
# obtenues une par graine.
#
# Avec moins de deux valeurs, la demi-largeur n'est pas
# définie : elle vaut +infini (jamais convergé), pour éviter
# d'arrêter une campagne sur un échantillon trop petit.
def compute_mean_ci95_half_width(
    values
):

    if len(values) == 0:

        raise ValueError(
            "values ne peut pas être vide."
        )

    sample_size = len(values)

    mean_value = sum(values) / sample_size

    if sample_size < 2:

        return mean_value, math.inf

    squared_deviations = [
        (value - mean_value) ** 2
        for value in values
    ]

    sample_variance = sum(
        squared_deviations
    ) / (sample_size - 1)

    standard_error = math.sqrt(
        sample_variance
        / sample_size
    )

    half_width = 1.96 * standard_error

    return mean_value, half_width


# Cette fonction calcule la demi-largeur de l'intervalle de
# Wilson pour une proportion, adaptée aux événements rares
# (FAR) où l'approximation normale peut être instable ou
# indéfinie (comptes nuls).
def compute_wilson_half_width(
    successes,
    trials,
    z_score=1.96
):

    if trials <= 0:

        return None

    if successes < 0 or successes > trials:

        raise ValueError(
            "successes doit appartenir à [0, trials]."
        )

    proportion = successes / trials

    denominator = 1 + (
        z_score ** 2
    ) / trials

    center = (
        proportion
        + (z_score ** 2) / (2 * trials)
    ) / denominator

    margin = (
        z_score
        * math.sqrt(
            (
                proportion * (1 - proportion)
                + (z_score ** 2) / (4 * trials)
            )
            / trials
        )
        / denominator
    )

    return margin


# Cette fonction vérifie si une métrique a convergé selon
# sa tolérance pré-enregistrée (absolue ou relative).
def check_metric_converged(
    mean_value,
    half_width,
    tolerance_spec
):

    if half_width == math.inf:

        return False

    if tolerance_spec["kind"] == "absolute":

        return half_width <= tolerance_spec[
            "tolerance"
        ]

    if tolerance_spec["kind"] == "relative":

        if mean_value == 0:

            # Une moyenne nulle rend la tolérance
            # relative indéfinie : on retombe sur une
            # exigence absolue stricte (aucune tolérance),
            # jamais sur une convergence automatique.
            return half_width == 0.0

        return (
            half_width
            <= abs(mean_value)
            * tolerance_spec["tolerance"]
        )

    raise ValueError(
        "kind de tolérance inconnu : "
        + str(tolerance_spec["kind"])
    )


# Cette fonction évalue la convergence de toutes les
# métriques principales pour un (scénario, politique) donné,
# à partir des résumés par graine déjà accumulés.
#
# seed_summaries : liste de dictionnaires, un par graine,
# contenant au moins les clés de CONVERGENCE_TOLERANCES.
#
# Retourne un dictionnaire détaillé (moyenne, demi-largeur,
# convergé) par métrique, plus un indicateur global
# "all_converged".
def evaluate_convergence(
    seed_summaries
):

    if len(seed_summaries) == 0:

        raise ValueError(
            "seed_summaries ne peut pas être vide."
        )

    per_metric_results = {}

    for metric_name in CONVERGENCE_TOLERANCES:

        tolerance_spec = CONVERGENCE_TOLERANCES[
            metric_name
        ]

        values = [
            summary[metric_name]
            for summary in seed_summaries
            if summary[metric_name] is not None
        ]

        if len(values) == 0:

            per_metric_results[metric_name] = {
                "mean": None,
                "half_width": math.inf,
                "converged": False,
                "sample_size": 0
            }

            continue

        mean_value, half_width = (
            compute_mean_ci95_half_width(
                values
            )
        )

        converged = check_metric_converged(
            mean_value=mean_value,
            half_width=half_width,
            tolerance_spec=tolerance_spec
        )

        per_metric_results[metric_name] = {
            "mean": mean_value,
            "half_width": half_width,
            "converged": converged,
            "sample_size": len(values)
        }

    all_converged = all(
        per_metric_results[metric_name]["converged"]
        for metric_name in CONVERGENCE_TOLERANCES
    )

    return {
        "per_metric": per_metric_results,
        "all_converged": all_converged
    }


# Cette fonction décide si la campagne doit s'arrêter pour un
# (scénario, politique) donné : soit parce que toutes les
# métriques principales ont convergé, soit parce que le
# nombre maximal de graines a été atteint (borne dure,
# jamais dépassée).
def should_stop_sampling(
    seed_count,
    all_converged
):

    if seed_count >= MAXIMUM_SEED_COUNT:

        return True

    if (
        seed_count >= MINIMUM_SEED_COUNT
        and all_converged
    ):

        return True

    return False
