# Guide complet du travail

Ce dépôt contient le code complet du travail, ordonné selon les étapes de réalisation. Tous les résultats qu'il contient proviennent de la **campagne corrigée** : le calcul de Tchebycheff a été corrigé, et la campagne a été régénérée sur cette base.

Dépôt : `https://github.com/guygnyolparfait/physec-dm-p0-haenel`
Article : `docs/article/paper_en.tex` et `paper_fr.tex`

---

## 0. La question et les trois volets

Un capteur LoRa doit choisir, à chaque message, une méthode d'authentification (empreinte radio RFF ou code MAC cryptographique) et une méthode de gestion de clé. Un arbitre multiobjectif, **P0**, fait ce choix :

1. il filtre les options admissibles ;
2. il construit le front de Pareto des options admissibles ;
3. il sélectionne une option par scalarisation de Tchebycheff, sous un plancher explicite de fausse acceptation (FAR).

| Volet | Question | Où |
|---|---|---|
| A. Le modèle | Comment P0 décide, et comment l'environnement est simulé | `src/physec_dm/` |
| B. Les scénarios S1 à S5 | Comportement de P0 dans cinq contextes, face à quatre politiques de référence | `run_five_case_studies*.py`, `src/scripts/analyze_five_case_studies.py`, `generate_v2_comparison_figures*.py`, `results/five_case_studies_v2_complex_adaptive/` |
| C. La comparaison avec Haenel et al. | Comparaison de P0 avec le schéma hybride publié (Sensors, 2021), sur la même échelle d'énergie et avec le même FAR publié | `src/haenel_comparison/`, `results/haenel_comparison/` |

L'article rapporte les volets B et C, et il s'appuie sur le volet A.

---

## 1. Ordre du travail

### Étape 1 — Le modèle (`src/physec_dm/`)

- `models.py` : structures de données (décisions, observations, résultats).
- `authentication.py` : robustesse d'authentification, FAR, probabilité de forgerie MAC (`2**-mac_tag_bits`), composition du FAR total.
- `key_generation.py` : génération de clé physique, états K0, K1a, K1b, K2.
- `energy_latency.py` : énergie et latence par action, selon les profils LOW, CENTRAL et HIGH.
- `channel.py` : canal radio simulé (ombrage log-normal, Clarke-Jakes, facteur matériel).
- `decision_maker.py` : arbitre P0 (admissibilité, front de Pareto, scalarisation de Tchebycheff, bris d'égalité).
- `eve_validation.py` : évaluation exploratoire de la marge de secret face à une espionne.
- `case_studies.py`, `thesis_scenarios.py`, `scenario_controller.py`, `mission.py` : définition et déroulement des scénarios S1 à S5.
- `campaign.py`, `adaptive_monte_carlo.py`, `paired_statistics.py` : campagne Monte-Carlo, arrêt adaptatif borné entre 30 et 150 graines, statistiques appariées.
- `contextual_policy.py`, `parameters.py`, `scientific_config.py` : politiques et paramètres.

La documentation de référence se trouve dans `docs/` : architecture, diagrammes UML et organigramme, équations, protocoles de simulation et de validation, guide des résultats et audit des paramètres.

### Étape 2 — Correction du calcul de Tchebycheff

Une constante numérique était ajoutée à chaque dénominateur de normalisation, y compris non dégénéré. Cela décalait les scores d'environ 2,5 × 10⁻¹¹, valeur supérieure à la tolérance de détection des égalités, et contournait le départage par FAR dans environ un tiers des périodes à poids égaux.

- Correction : `src/physec_dm/decision_maker.py`, fonction `calculate_tchebycheff_score`. La constante ne sert plus qu'à détecter un écart numériquement nul.
- Documentation de la correction : `docs/correction_tchebycheff/01_CODE_AUDIT/` (diagnostic), `02_CODE_CHANGES/` (changement de code), `03_TESTS/` (tests de non-régression, dans `tests/test_decision_maker.py`).

### Étape 3 — Campagne des scénarios S1 à S5 (corrigée)

Les scénarios sont définis dans `src/physec_dm/case_studies.py` :

- **S1, capteur agricole isolé** : nœud fixe, une phase, RSB moyen 8 dB, probabilité d'attaque 0,10.
- **S2, alarme critique industrielle** : nœud fixe, trois phases (normale, alarme avec criticité forcée, récupération), RSB 6 dB, probabilité d'attaque 0,15.
- **S3, objet mobile sur véhicule** : cinq phases (arrêt, accélération, vitesse jusqu'à 30 km/h, ralentissement, arrêt), RSB 9 à 10 dB, probabilité d'attaque 0,10.
- **S4, réseau urbain dense** : cinq phases alternant charge normale et congestion, RSB 3 dB, probabilité d'attaque 0,20 à 0,30.
- **S5, infrastructure critique sous attaque** : phase normale, phase de compromission (probabilité d'attaque jusqu'à 0,50), récupération ; RSB 12 dB.

Les politiques comparées à P0 :

- **B1-CONVENTIONAL** : toujours la cryptographie ;
- **B2-NAIVE-PHYSEC-NO-FLOOR** : préférence fixe pour la couche physique, sans plancher de FAR ;
- **B3-HYBRID-FIXED** : règle hybride fixe avec plancher de FAR, sans recherche de repli ;
- **B4-DM-NO-FAR-FLOOR** : P0 sans plancher de FAR, pour isoler l'effet de ce plancher.

Lancement de la campagne :

```bash
PYTHONPATH=src python -m scripts.run_five_case_studies_v2_adaptive
```

Le journal brut est écrit dans `results/five_case_studies_v2_complex_adaptive/`. Les résumés sont dans `data/` et les figures dans `figures/` :

- `data/summary_by_scenario_policy_v2.csv` : moyennes et intervalles par scénario et politique ;
- `data/paired_statistics_vs_p0_v2.csv` : différences appariées avec P0 ;
- `monte_carlo_convergence.json` : nombre de graines et état de convergence par scénario ;
- `figures/` : quatre objectifs par scénario, en français (`_v2.*`) et en anglais (`_v2_en.*`).

Le script `run_five_case_studies_v2_adaptive.py` importe des fonctions de `src/scripts/run_five_case_studies.py`, `src/scripts/run_five_case_studies_adaptive.py`, `src/scripts/analyze_five_case_studies.py` et `src/scripts/generate_four_objective_scenario_figures_v2.py`. Ces modules sont des bibliothèques pour la campagne corrigée : leur exécution directe peut écrire dans les dossiers de la campagne antérieure, il ne faut donc **pas** les lancer seuls.

### Étape 4 — Comparaison avec Haenel et al. (`src/haenel_comparison/`)

Le script `src/haenel_comparison/run_all_final.sh` enchaîne les étapes :

1. **Traçabilité des paramètres** : statut de chaque valeur (PUBLISHED_HAENEL, DERIVED_FROM_HAENEL, CALIBRATED_EFFECTIVE, OFFICIAL_DATASHEET, EXTERNAL_SCIENTIFIC_SOURCE, ASSUMED, ASSUMED_STATE_TRANSITION, UNAVAILABLE).
2. **Option A, calibration énergétique** (`energy_option_a.py`) : un système linéaire 2×2 reproduit exactement les quatre valeurs publiées.
3. **Expérience A, énergie et FRR** (`run_haenel_experiment_a.py`) : 30 graines, FRR 5 % et 10 %.
4. **Diagnostic de P0** (`p0_auth_only_haenel_rff.py`) : comparaison principale, avec le FAR publié de 0,002.
5. **Campagne de sécurité** (`security_monte_carlo.py`) : 100 000 tirages par politique, intervalles de Clopper-Pearson.
6. **Frontière des poids** (`weight_boundary_sensitivity.py`) : balayage de 11 couples de poids. La décision bascule exactement à w_énergie = w_auth = 0,25.
7. **Option B, modèle événementiel** (`energy_option_b.py`, `validate_option_b.py`) : le surcoût incrémental au-dessus de RFF seul est expliqué à 0,19 % – 14,45 % selon les hypothèses.
8. **Figures** : `generate_figures_experiment_a.py` et `generate_final_outputs.py` (français) ; `generate_article_figures_en.py` (anglais).

Résultat principal : à poids égaux, P0 choisit le MAC (564,743 mJ) plutôt que le RFF (454,076 mJ publié à FRR=10 %), soit +24,4 % d'énergie. Cette décision est une égalité exacte de scalarisation, départagée par le FAR.

### Étape 5 — Rédaction de l'article

- `docs/article/paper_fr.tex` et `paper_en.tex`, avec leurs PDF.
- Figures : `figure_1_energy_comparison*.png`, `figure_2_decision_split*.png`, `figure_4_security*.png`, `figure_5_weight_sensitivity*.png` (français et anglais), `figure_s2_four_objectives*.pdf` et `figure_s4_four_objectives*.pdf` (scénarios S2 et S4, campagne corrigée), `flowchart_dm*.pdf` (schéma du modèle).
- Le lien vers ce dépôt figure dans la section « Implémentation » de chaque version.

Structure : Résumé (pourcentages et références), Introduction (contexte, contributions en puces), État de l'art et positionnement, Contexte, Méthodologie (dont la correction de la scalarisation), Résultats et discussion (courbes, cas où P0 fait mieux, limites), Conclusion, Implémentation.

---

## 2. Installation

Python 3.12 recommandé.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py"                    # 469 tests
PYTHONPATH=src python -m unittest discover -s src/haenel_comparison/tests -p "test_*.py"  # 76 tests
```

Total : 545 tests, tous verts.

## 4. Reproduction

```bash
bash src/haenel_comparison/run_all_final.sh                   # comparaison avec Haenel et al.
PYTHONPATH=src python -m haenel_comparison.generate_article_figures_en   # figures anglaises de l'article
PYTHONPATH=src python -m scripts.run_five_case_studies_v2_adaptive               # campagne S1 à S5 (journal brut, long)
PYTHONPATH=src python -m scripts.generate_v2_comparison_figures                  # résumés et figures S1 à S5 (FR)
PYTHONPATH=src python -m scripts.generate_v2_comparison_figures_en               # figures S1 à S5 (EN)
```

Les résumés déjà calculés suffisent pour vérifier les chiffres de l'article sans relancer la campagne.

## 5. Données brutes

Le journal brut de la campagne corrigée (878 Mo) dépasse les limites de GitHub. Il est fourni compressé dans la version « données brutes » du dépôt, sous le nom `results_five_case_studies_v2_complex_adaptive_five_case_studies_v2_log.csv.gz`. Pour le restaurer :

```bash
gunzip -k results_five_case_studies_v2_complex_adaptive_five_case_studies_v2_log.csv.gz
mv results_five_case_studies_v2_complex_adaptive_five_case_studies_v2_log.csv results/five_case_studies_v2_complex_adaptive/
```

## 6. Hypothèses et limites

Les valeurs énergétiques sont calibrées, et les paramètres CPU attendent une mesure matérielle. Leur variation (profils LOW à HIGH) fait varier l'énergie moyenne d'environ 8 %. Le canal est simulé. Les poids de P0 sont égaux par construction. La campagne S5 n'a pas atteint la précision préenregistrée à sa limite de 150 graines. L'analyse à deux candidats de l'expérience A est un cas réduit. Le détail figure dans la section Limites de l'article.

## 7. Statut

Dépôt privé pendant la préparation de l'article. Il sera rendu public à la fin du travail. Pour donner accès à l'encadrante avant publication, il faut l'inviter comme collaboratrice (Settings → Collaborators), car un lien privé ne suffit pas.
