# Diff — `tests/test_decision_maker.py`

## 1. Test préexistant corrigé (avec justification complète)

`TestCompleteDecisionMaker.test_integrated_selection_with_mocked_submodels`

### AVANT

```python
        self.assertFalse(
            result.refusal_of_service
        )

        self.assertEqual(
            result.selected_evaluation.decision.get_name(),
            "A2-K0"
        )
```

### APRÈS

```python
        self.assertFalse(
            result.refusal_of_service
        )

        # ----------------------------------------------------
        # STEP8 -- valeur attendue corrigée de "A2-K0" vers
        # "A1-K0", avec justification complète (règle absolue :
        # ne jamais changer un test uniquement pour faire passer
        # la suite).
        #
        # Avec renewal_required=False, seule K0 est admissible
        # (DM-EQ95) : les deux candidats sont donc A1-K0
        # (far=0.001, énergie=2.0, robustesse=0.999) et A2-K0
        # (far=0.01, énergie=1.0, robustesse=0.99), non dominés
        # l'un par l'autre (A1 meilleur en authentification,
        # A2 meilleur en énergie ; latence et qualité de clé
        # identiques -> span nul sur ces deux dimensions).
        #
        # Sous la formule PURE de Tchebycheff (poids égaux),
        # A1 est le pire du front uniquement sur l'énergie
        # (span=1.0) et A2 uniquement sur l'authentification
        # (span=0.009) : les deux scores valent alors
        # EXACTEMENT 0.25, un vrai bris d'égalité qui doit
        # passer par build_tie_break_key (DM-EQ107 :
        # FAR -> énergie -> latence -> nom). A1 a la FAR la plus
        # faible (0.001 < 0.01) et doit donc gagner : "A1-K0".
        #
        # Avant la correction STEP8, l'ancienne formule (epsilon
        # ajouté au dénominateur des quatre dimensions) rompait
        # cette égalité au profit de A2 -- un artefact numérique
        # dépendant du span de chaque objectif, sans lien avec
        # DM-EQ107, démontré et chiffré dans STEP8_OFFICIAL/
        # 01_CODE_AUDIT/STEP8_PARETO_TCHEBYCHEFF_DIAGNOSTIC.md.
        # "A2-K0" était donc la trace d'un bug, pas un
        # comportement validé : ce test devient un test de
        # non-régression pour le comportement corrigé.
        self.assertEqual(
            result.selected_evaluation.decision.get_name(),
            "A1-K0"
        )
```

**Pourquoi ce changement est légitime et pas un contournement** : le test
mocke exactement le scénario A1 (FAR faible, énergie haute) contre A2
(FAR plus haute, énergie basse), reproduisant à l'identique le mécanisme
structurel décrit dans `STEP8_PARETO_TCHEBYCHEFF_DIAGNOSTIC.md`. Le calcul
manuel (détaillé dans le commentaire ajouté) montre que "A2-K0" ne pouvait
sortir que par l'artefact epsilon corrigé ; "A1-K0" est la sortie que
produit le tie-break FAR déjà documenté et déjà codé
(`build_tie_break_key`), une fois qu'il est réellement atteint.

## 2. Tests ajoutés dans `TestTchebycheff` (avant `TestCompleteDecisionMaker`)

Emplacement : juste après `test_tie_break_prefers_lower_energy_after_far`.
Code complet directement dans le fichier (pas reproduit ici en intégralité
pour éviter la duplication) :

1. `test_tie_break_prefers_lower_latency_after_far_and_energy` — niveau
   latence du tie-break, non couvert par un test dédié auparavant.
2. `test_tie_break_final_lexicographic_by_name` — niveau final (nom de
   décision), non couvert par un test dédié auparavant.
3. `test_normalization_zero_span_contributes_zero` — vérifie que deux
   dimensions à span nul contribuent exactement 0 au score (pas de
   division par une quantité quasi nulle).
4. `test_epsilon_does_not_break_genuine_tie` — **test de non-régression
   principal** : reproduit le Cas A du diagnostic (deux décisions à
   égalité structurelle sous poids égaux, spans différents) et vérifie
   `score_wide_span == score_narrow_span == 0.25` exactement. Ce test
   aurait échoué avec l'ancienne formule (écart mesuré : 2,53e-11).
5. `test_structural_tie_reaches_documented_tie_break` — bout en bout via
   `select_from_pareto_front` : confirme que le candidat à FAR/énergie
   favorable (et non celui dont le span est le plus petit) est
   sélectionné.

## Résumé des exécutions

```
AVANT correction : 464 tests, 464 OK, 0 échec
                    (voir 03_TESTS/tests_BEFORE_step8.log)

APRÈS correction : 469 tests (464 existants + 5 nouveaux),
                    1er passage : 468 OK, 1 échec
                    (test_integrated_selection_with_mocked_submodels,
                    analysé et corrigé avec justification ci-dessus)
                    2e passage : 469 OK, 0 échec
                    (voir 03_TESTS/tests_AFTER_step8.log)
```
