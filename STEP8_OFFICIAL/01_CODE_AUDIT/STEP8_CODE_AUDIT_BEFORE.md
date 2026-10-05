# STEP8 — Audit du code réel AVANT modification

Ce document décrit ce qui est **réellement implémenté** dans le workspace,
avec chemin de fichier + nom de fonction + ligne, avant toute correction de
l'étape 8. Aucune de ces descriptions n'est déduite du nom des fichiers :
chaque affirmation renvoie à du code lu intégralement.

Repo racine : `/home/parfait/physec_dm` (pas de dépôt git — le projet n'est
pas versionné, donc la traçabilité des changements est assurée ici par ce
dossier `STEP8_OFFICIAL/` et par les sauvegardes explicites, pas par des
commits).

## 1. Fichier principal du Decision Maker

`physec_dm/decision_maker.py` (36 525 octets, dernière modif. 22 juil. 2026
avant cette session). C'est le seul fichier qui implémente le raisonnement
DM-EQ93 à DM-EQ106 du document de modélisation (`docs/03_EQUATIONS_REFERENCE.md`,
cité en commentaire dans plusieurs modules).

## 2. Fonction qui énumère les décisions

`create_all_decisions()` — `physec_dm/models.py:108`.
Construit les 8 combinaisons `{A1,A2} × {K0,K1a,K1b,K2}`. Appelée par
`evaluate_all_decisions()` (`decision_maker.py:741`), qui boucle dessus une
fois par période.

## 3. Fonction qui vérifie l'admissibilité

Deux étapes, appliquées dans cet ordre par `evaluate_decision()`
(`decision_maker.py:576`) :

1. `apply_reasoning_rules(evaluation, context)` — `decision_maker.py:194`.
   Règles **logiques** (pas d'optimisation) : DM-EQ94 (A2 exige un profil
   RFF disponible), DM-EQ95 (r_t=0 ⇒ K_i=K0, sans exception), DM-EQ96
   (r_t=1 ⇒ K_i≠K0). Une décision rejetée ici n'a pas ses métriques
   calculées (retour anticipé ligne 598-600).

2. `apply_resource_and_security_constraints(evaluation, context, parameters,
   enforce_far_floor=True)` — `decision_maker.py:296`. Contraintes
   physiques/ressources/sécurité DM-EQ97 à DM-EQ102 : faisabilité PHY de
   K1a/K1b, batterie (pire cas), latence d'authentification prudente,
   échéance de clé, duty-cycle, **plancher de FAR** (`enforce_far_floor`
   — désactivé uniquement pour construire B4, jamais pour P0 ni les autres
   baselines, cf. commentaire lignes 288-295).

`evaluation.admissible` (DM-EQ103, ligne 557) = ET logique des trois blocs
+ absence de tout motif de rejet enregistré.

## 4. Fonction qui calcule le front de Pareto

`calculate_pareto_front(admissible_evaluations, tolerance)` —
`decision_maker.py:867`. Énumération exhaustive O(n²) sur au plus 8
décisions admissibles (commentaire ligne 865-866 : "aucune métaheuristique
n'est nécessaire").

## 5. Définition exacte de la dominance

`objective_vector_dominates(objective_vector_a, objective_vector_b,
tolerance)` — `decision_maker.py:784` (DM-EQ104). A domine B ssi :
- `never_worse` : aucune composante de A > composante de B + tolerance ;
- `strictly_better` : au moins une composante de A < composante de B − tolerance.

Les deux conditions sont requises (`return never_worse and strictly_better`,
ligne 830-833).

## 6. Tolérance numérique de dominance

`parameters.dominance_tolerance`. Valeur par défaut dans le constructeur de
`Parameters` (`physec_dm/parameters.py:636`) : `None` ("Statut : à valider").
Valeur **réellement utilisée par les campagnes officielles** :
**`1e-12`**, fixée dans `physec_dm/scientific_config.py:754` et dans
`main.py:130`. `run_decision_maker()` refuse de s'exécuter tant que cette
valeur n'est pas définie (`decision_maker.py:1264-1269`).

## 7. Calcul du point idéal / point nadir

`calculate_ideal_and_nadir_points(pareto_front)` — `decision_maker.py:917`.
Point idéal = min composante par composante **sur le front de Pareto**
(pas sur l'ensemble admissible complet) ; point nadir = max composante par
composante, également sur le front de Pareto. Lève une erreur explicite si
le front est vide (ligne 921-925).

## 8. Normalisation et score de Tchebycheff

`calculate_tchebycheff_score(objective_vector, contextual_weights,
ideal_point, nadir_point, epsilon)` — `decision_maker.py:1036`.

Formule **réellement codée**, ligne 1077-1086 :

```python
denominator = nadir_point[index] - ideal_point[index] + epsilon
normalized_distance = (objective_vector[index] - ideal_point[index]) / denominator
```

c'est-à-dire `epsilon` est ajouté **au dénominateur, sur les quatre
dimensions, systématiquement** — pas seulement en cas de span nul. C'est
exactement la formule que l'audit ChatGPT a signalée sur sa copie. Voir
`STEP8_PARETO_TCHEBYCHEFF_DIAGNOSTIC.md` pour la vérification empirique de
son effet.

`epsilon` utilisé = `parameters.tchebycheff_epsilon` = **`1e-12`**
(`parameters.py:625`, valeur fixe dans le constructeur, jamais `None`).

## 9. Gestion des égalités (bris d'égalité)

`select_from_pareto_front(pareto_front, contextual_weights, epsilon,
score_tolerance)` — `decision_maker.py:1143`.

Politique réellement codée :
1. Calcule `tchebycheff_score` pour chaque membre du front (boucle
   1185-1199) ;
2. `best_score = min(...)` (ligne 1201) ;
3. `tied_evaluations` = tous les membres dont
   `abs(score - best_score) <= score_tolerance` (lignes 1206-1220) ;
4. `selected_evaluation = min(tied_evaluations, key=build_tie_break_key)`
   (ligne 1224).

**Il n'existe dans le code actuel aucune étape intermédiaire de type
"somme pondérée normalisée" entre (3) et (4)** — contrairement à ce que
proposait la section 4 de la demande. Le tie-break passe directement du
score de Tchebycheff au critère lexicographique ci-dessous. Voir section
"Diagnostic tie-break" plus bas pour la décision motivée à ce sujet.

`score_tolerance` : par défaut `None` dans `Parameters.__init__`
(`parameters.py:631`, "Statut : à valider"), fixé à **`1e-12`** dans
`scientific_config.py:753` et `main.py:129` — **le même ordre de grandeur
que `tchebycheff_epsilon`**. C'est ce rapprochement des deux tolérances qui
rend le biais epsilon-au-dénominateur consécutif (section 8) capable de
casser silencieusement une égalité au lieu d'être absorbé par la fenêtre de
tolérance.

## 10. Tie-break final (critère lexicographique)

`build_tie_break_key(evaluation)` — `decision_maker.py:1113`. Ordre
**réellement codé**, confirmé dans le fichier officiel (pas une supposition
d'après une copie) :

```python
return (far, energy, latency, decision_name)
```

soit **FAR croissante → énergie croissante → latence croissante → nom de
décision (ordre lexicographique)** — exactement l'ordre que l'utilisateur
avait vu dans la copie auditée par ChatGPT. **Confirmé identique dans le
code officiel.**

## 11. Manière dont les poids w sont fournis

`physec_dm/contextual_policy.py`, fonction
`resolve_contextual_weights(context, state, parameters, weight_policy=None)`
(ligne 107). Point d'entrée unique déclaré utilisé par les cinq scénarios
(commentaire lignes 103-106). Comportement réel :

- si un `weight_policy` dynamique est fourni : il est appelé et validé
  (branche jamais activée par la campagne principale) ;
- **sinon (cas réellement utilisé par P0)** : repli statique sur
  `parameters.contextual_weights`, validé par `validate_contextual_weights`.

Le fichier documente explicitement (lignes 1-46) que DM-EQ108 à DM-EQ110
(pondération dynamique selon batterie/criticité/vieillissement de clé) sont
**bloquées** : seules des monotonies qualitatives sont spécifiées dans
`docs/03_EQUATIONS_REFERENCE.md`, aucune formule numérique validée
n'existe. Le statut `"P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS"` dans
`scientific_config.py` (`build_policy_catalog`) porte
`"implementation_status": "BLOCKED"` pour cette même raison.

**Conséquence pour l'audit** : la campagne principale P0 utilise donc un
vecteur de poids **statique et unique** :
`w = (0.25, 0.25, 0.25, 0.25)` (`[énergie, latence, authentification, clé]`,
ordre `WEIGHT_ORDER` de `contextual_policy.py:72-77`). C'est précisément ce
vecteur — poids strictement égaux — qui maximise la fréquence du phénomène
décrit dans `STEP8_PARETO_TCHEBYCHEFF_DIAGNOSTIC.md` (tie structurel sur
front à 2 membres).

## 12. Fonction qui applique D_t*

`run_decision_maker(context, parameters, rho_ab, variation_feasible=None,
k2_protocol=None, contextual_weights=None, enforce_far_floor=True)` —
`decision_maker.py:1252`. Pipeline complet, exactement dans cet ordre
(conforme à la Fig./Algorithmes 1-2 de l'article) :

1. `evaluate_all_decisions` → 8 évaluations ;
2. filtrage admissibilité → `admissible_evaluations` ;
3. si vide → `DecisionMakerResult` avec `refusal_of_service=True` (jamais
   de décision fabriquée) ;
4. `calculate_pareto_front` sur les décisions admissibles ;
5. `select_from_pareto_front` → décision retenue + ideal/nadir + poids
   validés ;
6. `DecisionMakerResult` avec `explanation` textuelle.

## 13. Scripts officiels qui lancent S1-S5

- **Campagne actuellement considérée comme référence (celle qui produit
  les chiffres publiés dans l'article)** :
  `run_five_case_studies_v2_adaptive.py`. Utilise
  `build_five_case_studies_v2()` (`physec_dm/case_studies.py`), écrit dans
  `results/five_case_studies_v2_complex_adaptive/` — **jamais** dans
  `results/five_case_studies_final_adaptive/` (obsolète, commentaire
  explicite ligne 18-19 du script). Dépend de `run_five_case_studies.py`
  pour `build_scenario_traces`, `run_single_mission`, `POLICIES`
  (P0/B1/B2/B3/B4).
- Fichier de sortie confirmé : `five_case_studies_v2_log.csv` (924 554 683
  octets, 11 août 2026), `monte_carlo_convergence.json`, `data/`, `figures/`
  dans ce même dossier.
- `run_weight_sensitivity_v2.py` (session précédente, étape 8 de l'ancien
  plan article) : sensibilité aux poids, déjà étendue avec balayage
  continu (Test A), annulation d'un objectif (Test B), cas extrêmes
  (Test C) — cf. section "Chevauchement avec la demande actuelle" plus bas.
- `run_b5_haenel_comparison.py` : baseline B5 (Haenel et al., RFF puis
  MAC), déjà implémentée et exécutée (session précédente).
- `generate_pareto_front_v2.py` : snapshot diagnostic déjà existant du
  front de Pareto réel sur S5 (une période représentative), déjà exécuté.

## 14. Fichiers qui produisent les CSV et figures

- CSV bruts par mission : `run_five_case_studies_v2_adaptive.py` →
  `run_five_case_studies.py::extract_log_rows` /
  `run_five_case_studies_adaptive.py::compute_seed_summary_metrics`.
- Figures S1-S5 (celles intégrées dans l'article) :
  `generate_v2_comparison_figures.py` (wrapper) →
  `generate_four_objective_scenario_figures_v2.py`
  (`figure_four_objectives_comparison_v2`), sortie dans
  `results/five_case_studies_v2_complex_adaptive/figures/`.

## 15. Chevauchement avec la demande actuelle de l'étape 8

Une partie substantielle des sections 8, 9 et 10 de la demande **existe
déjà dans le workspace**, produite lors d'une session antérieure portant
sur la finalisation de l'article (pas la présente étape 8) :

| Demande (section) | Déjà implémenté ? | Fichier |
|---|---|---|
| §8.A/B/C/D — poids EQUAL, extrêmes, ablations, balayage continu T=0..1 sur S5 | **Oui**, mais grille T à 3 points (0,25/0,50/0,75) et non 0,00→1,00 par pas de 0,05 comme demandé ici | `run_weight_sensitivity_v2.py` |
| §9 — snapshot diagnostic du front de Pareto sur S5 | **Oui**, un seul instant représentatif (période 780/1500, graine 2000) | `generate_pareto_front_v2.py` |
| §10 — baseline Haenel et al. (RFF puis MAC) | **Oui**, `select_b5_haenel_rff_then_mac_decision` dans `physec_dm/case_studies.py` (fin de fichier), comparée à P0 sur S1-S5 | `run_b5_haenel_comparison.py` |

Ces résultats restent valables **tant que le Decision Maker n'est pas
modifié** ; si la correction Tchebycheff décrite ci-dessous est retenue,
ils devront être **regénérés** au même titre que la campagne principale,
car ils utilisent tous `run_decision_maker` / `select_from_pareto_front`.
Ceci est pris en compte dans le plan de Phase B.

## 16. Vérification explicite demandée : limites 600 s / 5 s

Le code réel (`parameters.py:608-616` et
`decision_maker.py:436-465`, DM-EQ99) montre sans ambiguïté que :

- `critical_latency_budget_s = 5.0` et `normal_latency_budget_s = 600.0`
  sont deux **constantes de configuration**, sélectionnées par
  `get_authentication_latency_limit(criticality)` (`parameters.py:651`)
  selon la criticité du **message courant** (0 ou 1) ;
- cette limite est comparée, à **chaque période et pour chaque décision
  candidate évaluée séparément**, à
  `cost_metrics.prudent_authentication_latency_s` — une grandeur recalculée
  à neuf à chaque appel de `evaluate_decision`, jamais accumulée ni
  décrémentée entre les périodes ;
- rien dans `Context` (`physec_dm/models.py:161`) ni dans le pipeline de
  mission ne fait persister un "budget de latence restant" d'une période à
  l'autre pour cette contrainte (contrairement au duty-cycle, DM-EQ101, qui
  lui est un **vrai budget cumulé** : `context.remaining_duty_cycle_airtime_s`
  est explicitement décrémenté dans `physec_dm/mission.py`).

**Conclusion confirmée** (deuxième vérification, sur le workspace officiel
et non une copie) : 600 s et 5 s sont des **limites appliquées par
décision/message**, pas un budget cumulé. Aucune modification n'est
apportée à cette interprétation.
