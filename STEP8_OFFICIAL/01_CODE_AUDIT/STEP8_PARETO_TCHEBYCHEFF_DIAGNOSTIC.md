# STEP8 — Diagnostic Pareto / Tchebycheff (epsilon au dénominateur)

Ce document répond point par point à la section 2 de la demande, **avant**
toute modification de `physec_dm/decision_maker.py`. Toutes les valeurs
ci-dessous proviennent de l'exécution réelle du code officiel (pas d'une
copie, pas d'un calcul à la main) — scripts reproductibles dans ce même
dossier :

- `probe_unit_cases_A_to_E.py` → sortie complète dans
  `probe_unit_cases_A_to_E_OUTPUT.txt`
- `probe_real_campaign_tie_frequency.py` → sortie complète dans
  `probe_real_campaign_tie_frequency_OUTPUT.txt`

## A. Formule réellement utilisée

Confirmée dans `STEP8_CODE_AUDIT_BEFORE.md` §8 :
`denominator = nadir_k - ideal_k + epsilon`, appliqué **sur les quatre
dimensions, systématiquement**, avec `epsilon = 1e-12` et
`score_tolerance = 1e-12` (même ordre de grandeur — c'est ce
rapprochement qui rend l'effet visible).

## B/C. Cas unitaires contrôlés

### Cas A — span normal (échelle réaliste énergie/latence)

Deux décisions D1 (pire sur l'énergie, span 0,10) et D2 (pire sur la
latence, span 0,009) construites pour être **exactement égales** sous la
formule pure (sans epsilon) : `score_pur(D1) = score_pur(D2) = 0.25`.

Résultat avec le code réel (`calculate_tchebycheff_score`, epsilon
inclus) :

```
score D1 = 0.2499999999975
score D2 = 0.24999999997222222
écart    = 2.527777986927049e-11
```

Cet écart (2,53e-11) est **25 fois plus grand** que `score_tolerance`
(1e-12). L'égalité mathématique est donc cassée par un artefact
numérique, **hors de la fenêtre de tolérance censée traiter les
égalités**.

### Cas B — ideal == nadir sur une dimension (span nul)

Deux dimensions à span nul (`ideal_k == nadir_k`), deux dimensions
normales. Résultat : `score = 0.14999999999699978`, calculé correctement
sur les deux dimensions non nulles. **Aucune division par zéro** : quand
`span_k = 0`, le numérateur `f_k(D) - ideal_k` vaut nécessairement 0 lui
aussi (puisque tous les membres du front partagent alors la même valeur
sur cette dimension), donc `0 / epsilon = 0` quel que soit `epsilon > 0`.
**Ce cas ne pose donc aucun problème avec la formule actuelle** — la
correction proposée en section 3 de la demande ne change rien à ce cas
précis (elle donne aussi 0), elle est seulement plus explicite.

### Cas C — span très petit, décroissant vers/sous epsilon

| span | score code (avec epsilon) | score pur (sans epsilon) | ratio |
|---|---|---|---|
| 1e-6  | 0,249999750000250 | 0,250000000000250 | 0,9999990 |
| 1e-9  | 0,249750249750118 | 0,249999999868411 | 0,9990010 |
| 1e-12 | 0,125000352114977 | 0,250001408463874 | 0,4999986 |
| 1e-15 | 0,000249550829172 | 0,249800180540660 | 0,0009990 |

Quand le span d'une dimension devient de l'ordre de `epsilon` ou plus
petit, le score codé s'effondre (jusqu'à ×0,001 du score correct à
span=1e-15). C'est un effet plus sévère que le Cas A, mais qui suppose un
span quasi nul non structurel (pas exactement 0) — situation plus rare
en pratique que le Cas A, qui lui s'est révélé **très fréquent** (voir D).

### Cas D — égalité exacte de vecteurs objectifs

Deux vecteurs objectifs strictement identiques (mêmes flottants, bit à
bit) donnent des scores strictement identiques
(`0.18749999999765615 == 0.18749999999765615`). **Attendu et sans
problème** : les deux formules (actuelle et proposée) appliquent alors
exactement les mêmes opérations aux mêmes entrées.

### Cas E — impact direct sur `select_from_pareto_front`

Rejeu du Cas A à travers la vraie fonction `select_from_pareto_front`
(pas seulement `calculate_tchebycheff_score`) : D1 a une énergie de 0,20 J,
D2 une énergie de 0,16 J (D2 devrait gagner le tie-break "énergie" si les
scores étaient vraiment égaux). **Résultat réel : `D_LATENCY_WORST` (D2)
est sélectionné directement par comparaison de score — le tie-break
FAR→énergie→latence→nom n'est jamais atteint**, alors que le résultat
"correct" (score réellement égal) aurait dû passer par ce tie-break.
Dans ce cas précis le résultat coïncide (D2 gagne des deux façons), mais
seulement par coïncidence des chiffres choisis — voir D. pour la mesure
réelle sur données de simulation, où ce n'est pas toujours le cas.

## D. L'epsilon influence-t-il réellement la décision finale ? — Mesure sur une vraie campagne

Sonde exécutée sur **S1 à S5, `build_five_case_studies_v2()`, poids EQUAL
publiés `w=(0,25;0,25;0,25;0,25)`, 3 graines/scénario (9500-9502), 1500
pas** — donc sur le Decision Maker réel, dans les conditions réelles de
la campagne principale, pas un cas synthétique isolé :

```
periods_total              = 22500
periods_pareto_front_gt1   = 8521   (37,9 % des périodes)
periods_tie_current        = 8521   (100 % des fronts à >1 membre produisent
                                       une égalité/quasi-égalité détectée)
periods_winner_differs     = 7249   (85,1 % de ces égalités : le gagnant
                                       choisi par la formule actuelle diffère
                                       de celui qu'aurait choisi la formule
                                       proposée, donc potentiellement du
                                       tie-break FAR→énergie→latence→nom)
max_score_gap_seen_in_tie  = 9,93e-9  (écart maximal observé entre deux
                                       scores "proches" sur le vrai jeu de
                                       données)
```

**Explication structurelle** (pas une coïncidence numérique) : avec des
poids strictement égaux et un front de Pareto à exactement 2 membres, les
deux membres sont par construction non dominés l'un par l'autre — donc
chacun est nécessairement "le pire" du front sur au moins une dimension.
Sur cette dimension, il atteint exactement le point nadir, donc
`normalized_k = (nadir_k - ideal_k) / (nadir_k - ideal_k) = 1` **sous la
formule pure**, et son score pondéré sur cette dimension vaut exactement
`w_k = 0,25`. Si chacun des deux membres n'est "pire" que sur une seule
dimension, les deux scores maximaux valent alors **exactement 0,25**,
sous la formule pure — une égalité structurellement garantie, pas un
hasard de calcul flottant. La formule actuelle (epsilon ajouté au
dénominateur) rompt cette égalité en favorisant systématiquement le
membre dont la dimension "pire" a le plus grand span sur le front — un
critère qui n'a **aucune justification dans la modélisation** (DM-EQ106
et le tie-break DM-EQ107 documentent FAR→énergie→latence→nom, jamais
"span de la dimension la plus défavorable").

**Conclusion factuelle** : ce n'est pas un cas limite rare. Avec le
vecteur de poids réellement utilisé par P0 (poids égaux), la formule
actuelle contourne le tie-break documenté dans l'article dans une
fraction substantielle (~32 % de l'ensemble des périodes de la campagne
principale, soit 7249/22500) des périodes où plusieurs décisions sont
non dominées.

## E. Un test historique dépend-il de ce comportement ?

Vérifié dans `tests/test_decision_maker.py` :

- `test_tchebycheff_score` (ligne 1016) : `assertAlmostEqual(score, 0.125,
  places=10)`, soit une tolérance de 5e-11 — largement supérieure à
  l'écart induit par epsilon dans ce test précis (spans 2 / 1 / 0,2 / 0,2,
  perturbation attendue ≈5e-12). **Ce test reste vrai avec les deux
  formules.**
- `test_tie_break_prefers_lower_far` et
  `test_tie_break_prefers_lower_energy_after_far` (lignes 1054, 1090) :
  utilisent des vecteurs objectifs **strictement identiques** entre les
  deux évaluations comparées (`[1.0, 1.0, -0.9, -0.8]` pour les deux).
  D'après le Cas D ci-dessus, deux vecteurs identiques produisent des
  scores identiques sous les deux formules (ideal=nadir=vecteur commun,
  span nul partout, score=0 des deux côtés) : **ces tests ne dépendent
  pas de l'artefact epsilon** et continueront de passer sans
  modification.

**Aucun test existant n'encode intentionnellement ou accidentellement le
biais epsilon-au-dénominateur.** La suite de tests actuelle (464/464 OK)
ne fait donc pas obstacle à la correction.

## Diagnostic tie-break (section 4 de la demande)

Ordre réellement codé, confirmé sur le fichier officiel (pas une
supposition) : **FAR → énergie → latence → nom**
(`build_tie_break_key`, `decision_maker.py:1113`) — identique à ce que
l'utilisateur avait vu dans la copie auditée par ChatGPT.

La demande propose d'insérer, entre le score de Tchebycheff et ce
tie-break, un critère intermédiaire `U(D) = Σ w_k·normalized_k(D)`
(somme pondérée normalisée). **Analyse avant implémentation** :

- Ce critère intermédiaire est classiquement utilisé (Miettinen 1999,
  déjà cité dans l'article) pour départager des points *faiblement*
  Pareto-optimaux obtenus par scalarisation de Tchebycheff pure — un
  risque réel quand la scalarisation Tchebycheff est utilisée **seule**
  pour filtrer les solutions.
- Ce n'est **pas le cas ici** : le filtrage par dominance stricte
  (`calculate_pareto_front`, DM-EQ105) est appliqué **avant**
  Tchebycheff (DM-EQ106). Tout candidat qui atteint l'étape de bris
  d'égalité est donc déjà un point *strictement* non dominé — le risque
  que la somme pondérée est censée corriger ne s'applique pas à ce
  pipeline.
- Insérer ce critère ajouterait une étape non demandée par la
  modélisation (DM-EQ107 documente uniquement FAR→énergie→latence→nom)
  et ferait dépendre le résultat d'un coefficient de pondération
  supplémentaire non validé par l'encadrante, contrairement à la règle
  déjà appliquée dans `contextual_policy.py` ("ne pas inventer de
  coefficient").

**Recommandation retenue : ne pas ajouter ce critère intermédiaire.**
Une fois la correction de la section suivante appliquée, le tie-break
FAR→énergie→latence→nom déjà documenté dans l'article s'applique
directement aux égalités réelles (au lieu d'être contourné par
l'artefact epsilon) — ce qui restaure exactement le comportement déjà
décrit et publié, sans rien inventer de nouveau.

## Conclusion du diagnostic

**Le diagnostic de ChatGPT est confirmé — et sous-estimé.** Il n'affecte
pas seulement des égalités numériques exactes de coïncidence : il
contourne systématiquement le tie-break documenté dans l'article pour
~32 % des périodes de la campagne principale (poids égaux), à cause
d'une propriété structurelle des fronts de Pareto à 2 membres sous poids
égaux, pas d'un cas limite improbable. La correction proposée en
section 3 de la demande (epsilon utilisé comme seuil de détection de
span dégénéré, pas comme terme de lissage systématique) est
mathématiquement justifiée, standard (Miettinen 1999), et strictement
équivalente à la formule actuelle dans le seul cas où celle-ci était déjà
correcte (span nul, Cas B). Elle est appliquée dans
`STEP8_OFFICIAL/02_CODE_CHANGES/`.
