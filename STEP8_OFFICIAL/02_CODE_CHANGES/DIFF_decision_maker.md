# Diff — `physec_dm/decision_maker.py`

Fonction touchée : `calculate_tchebycheff_score` (seule fonction modifiée
dans le fichier). Emplacement avant modification : lignes 1023-1101 du
fichier officiel avant STEP8 (voir extrait exact dans
`STEP8_OFFICIAL/01_CODE_AUDIT/STEP8_CODE_AUDIT_BEFORE.md`, section 8).

## AVANT

```python
# Cette fonction calcule le score
# de Tchebychev pondéré d'une décision.
#
# Dans la modélisation :
#
# score(D) =
#     max_k [
#         w_k
#         * (f_k(D) - f_ideal_k)
#         / (f_nadir_k - f_ideal_k + epsilon)
#     ]
#
# Cette fonction correspond à DM-EQ106.
def calculate_tchebycheff_score(
    objective_vector,
    contextual_weights,
    ideal_point,
    nadir_point,
    epsilon
):

    if epsilon <= 0:

        raise ValueError(
            "L'epsilon de Tchebychev "
            "doit être strictement positif."
        )

    vector_length = len(
        objective_vector
    )

    if (
        len(contextual_weights) != vector_length
        or len(ideal_point) != vector_length
        or len(nadir_point) != vector_length
    ):

        raise ValueError(
            "Les vecteurs de Tchebychev "
            "doivent avoir la même taille."
        )

    weighted_distances = []

    for index in range(
        vector_length
    ):

        numerator = (
            objective_vector[index]
            - ideal_point[index]
        )

        denominator = (
            nadir_point[index]
            - ideal_point[index]
            + epsilon
        )

        normalized_distance = (
            numerator
            / denominator
        )

        weighted_distance = (
            contextual_weights[index]
            * normalized_distance
        )

        weighted_distances.append(
            weighted_distance
        )

    score = max(
        weighted_distances
    )

    return score
```

## APRÈS

```python
# Cette fonction calcule le score
# de Tchebychev pondéré d'une décision.
#
# Dans la modélisation :
#
# score(D) =
#     max_k [
#         w_k
#         * (f_k(D) - f_ideal_k)
#         / (f_nadir_k - f_ideal_k)
#     ]
#
# avec la convention : si (f_nadir_k - f_ideal_k) est
# numériquement nul (à epsilon près), la dimension k est
# neutre (contribution 0) plutôt que divisée.
#
# Cette fonction correspond à DM-EQ106.
#
# ----------------------------------------------------------
# CORRECTION STEP8 (voir STEP8_OFFICIAL/01_CODE_AUDIT/
# STEP8_PARETO_TCHEBYCHEFF_DIAGNOSTIC.md pour la démonstration
# complète, chiffrée sur le code réel, avant cette correction) :
#
# La version précédente ajoutait epsilon au dénominateur sur
# LES QUATRE dimensions, systématiquement, y compris quand le
# span (nadir_k - ideal_k) était normal. Cela introduisait un
# biais dépendant de l'échelle propre à chaque objectif (span
# différent pour l'énergie, la latence, l'authentification, la
# clé), capable de casser une égalité mathématique réelle entre
# deux scores de Tchebycheff -- et donc de contourner
# silencieusement le tie-break documenté (DM-EQ107 :
# FAR -> énergie -> latence -> nom, cf. build_tie_break_key
# ci-dessous). Mesuré sur la campagne principale (poids égaux,
# S1-S5, 3 graines) : ce contournement se produit dans 7249 des
# 22500 périodes testées (~32 %), à chaque fois qu'un front de
# Pareto à deux membres atteint structurellement le même score
# maximal sous poids égaux.
#
# epsilon garde désormais son rôle initial de SEUIL de
# détection d'un span numériquement dégénéré (ideal == nadir
# sur cette dimension pour l'ensemble du front), et non de
# terme de lissage ajouté partout. Quand span == 0, toutes les
# décisions du front partagent la même valeur sur cette
# dimension : le numérateur (f_k(D) - ideal_k) vaut alors aussi
# 0, et la contribution de cette dimension est neutre (0) --
# ce cas donnait déjà 0 avec l'ancienne formule (0 / epsilon
# = 0), la correction ne change donc rien à ce cas précis, elle
# supprime uniquement le biais introduit sur les spans non nuls.
def calculate_tchebycheff_score(
    objective_vector,
    contextual_weights,
    ideal_point,
    nadir_point,
    epsilon
):

    if epsilon <= 0:

        raise ValueError(
            "L'epsilon de Tchebychev "
            "doit être strictement positif."
        )

    vector_length = len(
        objective_vector
    )

    if (
        len(contextual_weights) != vector_length
        or len(ideal_point) != vector_length
        or len(nadir_point) != vector_length
    ):

        raise ValueError(
            "Les vecteurs de Tchebychev "
            "doivent avoir la même taille."
        )

    weighted_distances = []

    for index in range(
        vector_length
    ):

        span = (
            nadir_point[index]
            - ideal_point[index]
        )

        # span numériquement dégénéré : dimension neutre,
        # jamais de division par une quantité quasi nulle.
        if abs(span) <= epsilon:

            normalized_distance = 0.0

        else:

            numerator = (
                objective_vector[index]
                - ideal_point[index]
            )

            normalized_distance = (
                numerator
                / span
            )

        weighted_distance = (
            contextual_weights[index]
            * normalized_distance
        )

        weighted_distances.append(
            weighted_distance
        )

    score = max(
        weighted_distances
    )

    return score
```

## Portée du changement

- Signature de la fonction **inchangée** (mêmes 5 paramètres, même ordre).
- Comportement **inchangé** dans le cas span nul (déjà 0 avant, 0 après).
- Comportement **inchangé** quand deux vecteurs objectifs sont strictement
  identiques (même calcul flottant des deux côtés).
- Comportement **corrigé** uniquement quand un span est non nul et que
  l'ancien biais epsilon-dépendant-du-span aurait déterminé un gagnant à
  la place du tie-break documenté.
- Aucun appelant (`select_from_pareto_front`, `run_decision_maker`) n'a été
  modifié : ils continuent d'appeler `calculate_tchebycheff_score` avec la
  même signature.
