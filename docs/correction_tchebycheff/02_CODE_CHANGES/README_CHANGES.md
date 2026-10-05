# STEP8 — Fichiers modifiés et justification

Le projet n'est pas versionné par git (`Is a git repository: false`), donc
il n'existe pas de `git diff` natif. Ce dossier reconstruit fidèlement les
changements à partir du texte exact substitué (avant/après), pour chacun
des deux fichiers touchés. Aucun autre fichier du dépôt n'a été modifié en
Phase A.

## Fichiers modifiés

1. `physec_dm/decision_maker.py` — fonction `calculate_tchebycheff_score`
   (voir `DIFF_decision_maker.md`). **Seule fonction touchée dans tout le
   Decision Maker.**
2. `tests/test_decision_maker.py` — 5 tests ajoutés (nouvelle couverture
   demandée en section 5), 1 test préexistant corrigé avec justification
   complète (voir `DIFF_test_decision_maker.md`).

## Justification scientifique de la modification de `decision_maker.py`

Voir `STEP8_OFFICIAL/01_CODE_AUDIT/STEP8_PARETO_TCHEBYCHEFF_DIAGNOSTIC.md`
pour la démonstration complète. Résumé :

- **Avant** : `denominator = nadir_k - ideal_k + epsilon`, appliqué
  systématiquement sur les 4 dimensions. Biais dépendant du span propre à
  chaque objectif, capable de casser une égalité de Tchebycheff
  mathématiquement réelle, et de court-circuiter le tie-break documenté
  (DM-EQ107 : FAR → énergie → latence → nom). Mesuré sur la campagne
  principale réelle (poids égaux, S1-S5, 3 graines, 1500 pas) : ce
  contournement se produit dans **7249 / 22500 périodes (~32 %)**.
- **Après** : `epsilon` redevient un seuil de détection de span
  numériquement dégénéré (`abs(span) <= epsilon → contribution 0`), pas un
  terme de lissage systématique. Comportement strictement identique à
  l'ancien dans le seul cas où celui-ci était déjà correct (span nul).
  Formulation standard (Miettinen 1999, déjà cité dans l'article).

Aucune autre fonction (`objective_vector_dominates`,
`calculate_pareto_front`, `calculate_ideal_and_nadir_points`,
`build_tie_break_key`, `select_from_pareto_front`, `run_decision_maker`,
règles logiques, contraintes ressources/sécurité) n'a été modifiée : elles
ont été auditées (voir `01_CODE_AUDIT/STEP8_CODE_AUDIT_BEFORE.md`) et
jugées conformes à la modélisation, sans défaut identifié.

## Ce qui n'a PAS été changé, et pourquoi

- **Le critère de bris d'égalité intermédiaire** ("somme pondérée
  normalisée U(D)") proposé en section 4 de la demande n'a **pas** été
  ajouté. Justification détaillée dans le diagnostic : ce critère sert
  classiquement à départager des points *faiblement* Pareto-optimaux
  obtenus par scalarisation Tchebycheff seule ; ici le filtrage par
  dominance stricte précède toujours Tchebycheff, donc tout candidat au
  stade du bris d'égalité est déjà strictement non dominé — le problème
  que ce critère est censé résoudre ne se pose pas dans ce pipeline. Le
  tie-break FAR→énergie→latence→nom déjà documenté et déjà codé suffit,
  et c'est précisément lui qu'il fallait laisser s'exprimer.
- **Aucun scénario, coût, seuil, poids ou règle métier n'a été modifié.**
  `parameters.contextual_weights`, `dominance_tolerance`,
  `score_tolerance`, `tchebycheff_epsilon`, `far_limit`,
  `authentication_latency_limit` restent à l'identique.
- **L'interprétation des limites 600 s / 5 s n'a pas été changée** :
  confirmée par re-lecture du code officiel comme limite par
  décision/message (voir audit §16), pas comme budget cumulé.
