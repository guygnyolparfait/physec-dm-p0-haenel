# Comparaison P0 vs Haenel et al. (Sensors 2021) — README reproductible

**Statut : TERMINÉ.** Toutes les phases sont implémentées et testées
(546 tests, tous verts). Ce document explique ce qui est fait,
comment le relancer, et référence le détail complet dans
`Compte_Rendu_Final_Haenel_vs_P0.md`.

## 1. Objectif scientifique

Transposer le banc d'essai énergétique publié par Haenel, Haddad,
Laurent et Zhang, *"Practical Cross-Layer Radio Frequency-Based
Authentication Scheme for Internet of Things"*, Sensors 2021, 21(12),
4034, puis substituer leur règle fixe de basculement par notre
Decision Maker P0, en lui donnant la MÊME performance de sécurité
qu'ils publient pour l'empreinte radio (RFF).

## 2. Ce que Haenel et al. a réellement expérimenté

- Un banc d'essai matériel réel (MSP430G2x + CC110L, Section 6.3.2),
  mesuré avec EnergyTrace, sur 300 s, un message toutes les 3 s
  (100 messages).
- Quatre configurations mesurées : MAC seul, hybride avec FRR
  simulé à 10 % et à 5 %, RFF seul (Table 1, p.15).
- Le FRR simulé dans ce banc d'essai précis représente un **rejet
  à tort du message légitime** par le test RFF (pas une acceptation
  d'un attaquant) — citation exacte (Section 6.3.1) : *"the GW
  simulates the RFF ... (simulated FRR of 10%, 5%; and 0% for the
  simulated RFF-only)"*.
- Le FAR (sécurité face à un attaquant) vient d'une expérience
  **différente** (Section 6.2.2, classification KNN), mais le papier
  relie explicitement le FRR=10% du banc d'essai énergétique au
  FAR=0,2% de cette expérience (Section 6.3.1 : *"This value was
  chosen as it led to a FAR of 0.2% in our live experiment"*).
- **Première authentification complète** (Section 6.3.3, Fig. 11) :
  *"Due to the first full authentication, the hybrid protocol was a
  little more energy-demanding at the start of the experiment."*
  Aucune valeur numérique isolée n'est publiée pour ce coût de
  démarrage.
- **Deep-sleep explicitement exclu** entre deux transmissions dans
  ce banc d'essai (rythme trop rapide, 3 s) : *"This also prevented
  the nodes from using the 'deep-sleep' mode of the modules between
  two transmissions."*

## 3. Ce que nous transposons, et comment

- `haenel_config.py` centralise toutes les valeurs, avec un statut
  explicite : PUBLISHED_HAENEL / DERIVED_FROM_HAENEL /
  CALIBRATED_EFFECTIVE / OFFICIAL_DATASHEET /
  EXTERNAL_SCIENTIFIC_SOURCE / ASSUMED / ASSUMED_STATE_TRANSITION /
  UNAVAILABLE.
- `haenel_b5.py` transpose, de façon **calibrée** (pas littérale),
  la règle de Haenel et al. par un tirage stochastique
  `u ~ Uniform(0,1)`, rejet RFF si `u < FRR` — nommé
  **B5_HAENEL_CALIBRATED**, **distinct** du B5 déjà présent dans
  `physec_dm/case_studies.py` (`select_b5_haenel_rff_then_mac_decision`),
  qui répond à une question différente (voir `__init__.py`).
- `energy_option_a.py` calibre un modèle à DEUX paramètres nommés
  (`EFFECTIVE_FIXED_HYBRID_OVERHEAD_MJ`, `EFFECTIVE_FALLBACK_COST_MJ`),
  résolu EXACTEMENT sur les deux points HYBRID publiés (système 2x2).
  C'est une calibration, pas une validation indépendante : son
  accord avec les points de calibration est vrai par construction.
- `p0_auth_only.py` fait tourner notre **vrai** Decision Maker
  (mêmes fonctions `evaluate_decision`, `calculate_pareto_front`,
  `select_from_pareto_front` que la campagne principale — jamais
  réimplémentées), restreint à `K = K0` des deux côtés (Haenel et
  al. ne gère pas de clé physique), sur un contexte statique.
- `p0_auth_only_haenel_rff.py` : **comparaison principale**, A2
  reçoit le FAR PUBLIÉ de Haenel et al. (0,002), via
  `haenel_energy_adapter.apply_haenel_rff_far_to_a2` (réutilise les
  vraies formules `authentication.calculate_a2_total_false_acceptance`
  / `calculate_a2_robustness`).
- `p0_auth_only_haenel_scale.py` : analyse **secondaire**
  P0_NATIVE_RFF_SENSITIVITY, A2 reçoit le FAR NATIF du modèle de
  canal physec_dm (~8,39×10⁻⁵, contexte SNR ASSUMED) — répond à une
  question différente, jamais mélangée à la comparaison principale.

## 4. Ce que nous NE reproduisons PAS

- Le matériel MSP430G2x/CC110L, ni la mesure EnergyTrace elle-même
  (Option A est une calibration agrégée ; Option B, ci-dessous,
  reconstruit certaines grandeurs à partir de datasheets officiels,
  sans jamais prétendre mesurer le matériel réel).
- La classification RFF par KNN (Section 6.2) — hors du périmètre
  du banc d'essai énergétique.
- La configuration exacte de calibration radio (registres CC110L
  MCSM0/TEST0/FSCAL3) et le coût réel de Chaskey-12 sur MSP430 :
  non publiés, traités par analyse de sensibilité (Option B).

## 5. Option A vs Option B — deux rôles différents

**Option A** (`energy_option_a.py`) est le modèle de RÉFÉRENCE
QUANTITATIF : calibré sur les 4 valeurs publiées, il reproduit ces
valeurs EXACTEMENT (0,00% d'écart), par construction. C'est
l'échelle énergétique utilisée pour B5_HAENEL_CALIBRATED et P0.

**Option B** (`energy_option_b.py`) est une ANALYSE STRUCTURELLE :
reconstruction bottom-up (TX/RX/CPU) sur le matériel réel
(MSP430G2x + CC110L, datasheets officiels). Elle reproduit
correctement l'ORDRE qualitatif des 4 configurations, mais
n'explique qu'une FAIBLE FRACTION (0,19% à 14,45% selon le cas et
le jeu d'hypothèses LOW/CENTRAL/HIGH) du SURCOÛT INCRÉMENTAL réel
au-dessus de RFF_ONLY (voir `option_a_vs_option_b.csv`, colonnes
`measured_increment_over_rff_only_mJ` / `modeled_increment_over_rff_only_mJ`
/ `increment_explained_pct`). Ce n'est jamais présenté comme un
modèle d'énergie absolue validé.

## 6. Comparaison principale — résultat vérifié pas à pas

Voir `p0_auth_only_haenel_rff.print_detailed_diagnostic` (exécutable
via `python3 -m haenel_comparison.p0_auth_only_haenel_rff`) et
`results/haenel_comparison/p0_decision_explanation.md` pour
l'explication complète :

- A1-K0 et A2-K0 sont **tous les deux admissibles**.
- A2 est nettement moins cher en énergie (454,08 mJ contre 564,74 mJ
  pour A1 à FRR=10%), mais A1 a un FAR bien plus bas (borne
  cryptographique idéalisée) que A2 (FAR publié Haenel et al.,
  0,002).
- Malgré cet écart, les deux candidats obtiennent EXACTEMENT le même
  score de Tchebycheff (0,25) sous poids égaux. Raison mathématique,
  vérifiée dans le code (`weight_boundary_sensitivity.py`) : sur un
  front de Pareto à exactement 2 points avec latence et Qkey
  neutres, `score(A1) = w_energy` et `score(A2) = w_auth` --
  identiques sous poids égaux.
- Le score étant à égalité stricte, le bris d'égalité tranche
  (`build_tie_break_key`, FAR croissant en premier critère) : A1
  gagne systématiquement.
- **La frontière de décision est EXACTEMENT à w_energy=w_auth** : un
  écart de seulement 0,001 (0,251 contre 0,249) fait basculer P0
  vers A2. Ce n'est pas "beaucoup plus" de poids qu'il faudrait
  donner à l'énergie.

## 7. Hypothèses (ASSUMED) — analyse secondaire uniquement

Ces hypothèses concernent UNIQUEMENT P0_NATIVE_RFF_SENSITIVITY
(secondaire) ; la comparaison principale (Section 6) utilise
directement le FAR publié par Haenel et al., sans ce contexte.

| Paramètre | Valeur | Pourquoi |
|---|---|---|
| SNR contexte P0 | 10 dB | Haenel et al. ne publie pas de SNR en dB (seulement des distances 8-25 m) |
| Shadowing | 1 dB | Canal stable, nœuds fixes (Section 6.1) |
| Vitesse | 0 m/s | "stays at a fixed location" (Section 6.1) |
| Probabilité d'attaque Mallory (Expérience A) | 0,0 | Le banc d'essai énergétique (Section 6.3) ne met en scène aucun attaquant |

## 8. Commandes (reproductibilité complète)

```bash
cd /home/parfait/physec_dm

# Tout le pipeline en une commande (11 étapes, ~30s) :
bash haenel_comparison/run_all_final.sh

# Ou étape par étape :
python3 -m unittest discover -s tests                       # 469 tests historiques (S1-S5, jamais modifiés)
python3 -m unittest discover -s haenel_comparison/tests -v  # 48 tests haenel_comparison

python3 -m haenel_comparison.haenel_parameter_traceability
python3 -m haenel_comparison.haenel_option_b_sources
python3 -m haenel_comparison.energy_option_a                # calibration Option A
python3 -m haenel_comparison.run_haenel_experiment_a         # B5 (30 graines) + P0 (RFF + native)
python3 -m haenel_comparison.p0_auth_only_haenel_rff         # diagnostic comparaison principale
python3 -m haenel_comparison.export_p0_diagnostics           # CSV + MD explicatif
python3 -m haenel_comparison.latency_sensitivity
python3 -m haenel_comparison.weight_sensitivity              # 4 profils grossiers
python3 -m haenel_comparison.weight_boundary_sensitivity     # sweep fin de la frontière
python3 -m haenel_comparison.run_haenel_experiment_b         # sécurité, campagne historique 30 graines
python3 -m haenel_comparison.security_monte_carlo            # sécurité renforcée, 100 000 tentatives
python3 -m haenel_comparison.energy_option_b                 # modèle événementiel MSP430G2x/CC110L
python3 -m haenel_comparison.validate_option_b                # surcoût incrémental expliqué
python3 -m haenel_comparison.p0_complete                     # extension exploratoire K1a/K1b/K2
python3 -m haenel_comparison.generate_figures_experiment_a   # Figures 1-3
python3 -m haenel_comparison.generate_final_outputs          # Figures 4-5 + tableaux
```

**Environnement** : Python 3.12, venv à `/home/parfait/physec_dm/.venv`
(numpy, scipy, matplotlib).

## 9. Résultats produits (résumé)

- `results/haenel_comparison/*.csv` : voir `FINAL_MANIFEST.txt` pour
  la liste complète et le rôle de chaque fichier.
- `results/haenel_comparison/figures/figure_1..5.png`.
- `results/haenel_comparison/p0_decision_explanation.md` : preuve
  pas à pas du résultat principal.
- `Compte_Rendu_Final_Haenel_vs_P0.md` : rapport scientifique complet
  (22 sections), y compris le détail de toutes les corrections
  apportées après relecture.

## 10. Fichiers principaux du module

| Fichier | Rôle |
|---|---|
| `haenel_config.py` | Configuration centrale, traçabilité des paramètres |
| `haenel_b5.py` | B5_HAENEL_CALIBRATED (transposition stochastique) |
| `energy_option_a.py` | Modèle énergétique agrégé (référence quantitative) |
| `energy_option_b.py` | Modèle événementiel bottom-up (analyse structurelle) |
| `haenel_energy_adapter.py` | Échelle énergétique commune B5/P0 + FAR publié pour A2 |
| `p0_auth_only_haenel_rff.py` | **Comparaison principale** |
| `p0_auth_only_haenel_scale.py` | Analyse secondaire (FAR natif) |
| `p0_complete.py` | Extension exploratoire (K1a/K1b/K2) |
| `weight_boundary_sensitivity.py` | Sweep fin de la frontière des poids |
| `security_monte_carlo.py` | Campagne sécurité renforcée (100 000 tentatives) |
| `run_all_final.sh` | Relance tout le pipeline en une commande |

Voir `FINAL_MANIFEST.txt` pour la liste exhaustive de tous les
fichiers (code, tests, résultats, figures, rapports).
