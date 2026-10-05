# Compte-rendu final — Comparaison Decision Maker P0 vs Haenel et al. (Sensors 2021)

*Rédigé de façon autonome. Version scientifique finale (25/09/2026), corrigée après deux relectures. Chaque chiffre cité est retrouvable dans un CSV du dossier `results/haenel_comparison/`.*

## 0. Corrections apportées au fil des relectures

**Passe V2 (deux corrections) :**
1. Le microcontrôleur d'Option B (MSP430FR5994, erroné) a été remplacé par le MSP430G2x réellement utilisé par le banc d'essai énergétique de Haenel et al. (Section 6.3.2).
2. La campagne de sécurité (~450 tentatives) a été remplacée par une campagne Monte-Carlo à 100 000 tentatives/politique.

**Passe finale (cette version) :**
3. La transposition stochastique n'est plus appelée "B5-littéral" (elle ne modélise pas explicitement la première authentification complète décrite par Haenel et al., Fig. 11) : renommée **B5_HAENEL_CALIBRATED**.
4. La comparaison principale donne maintenant à A2 (RFF) la performance PUBLIÉE de Haenel et al. (FAR=0.002), pas le FAR natif de notre modèle de canal — voir Section 10. L'ancienne analyse (FAR natif) est conservée séparément sous le nom **P0_NATIVE_RFF_SENSITIVITY**.
5. La frontière des poids a été vérifiée mathématiquement ET dans le code (Section 14) : elle est EXACTEMENT à w_energy=w_auth, pas "loin" comme suggéré précédemment.
6. La sensibilité à la latence a été reformulée avec sa réserve méthodologique structurelle (Section 14).
7. Option A n'est plus présentée comme une "validation" (Section 8) : c'est une calibration, sa cohérence avec les points de calibration est vraie par construction.
8. Option B est maintenant évaluée sur le SURCOÛT INCRÉMENTAL au-dessus de RFF_ONLY, pas sur l'erreur totale (Section 17) — la conclusion "63-89% expliqué" était fausse, corrigée en "moins de 15% du surcoût incrémental expliqué".
9. Le temps de transition CC110L utilisait par erreur un temps de réveil "depuis le deep-sleep" alors que le deep-sleep est explicitement exclu par Haenel et al. pour ce banc d'essai — corrigé (Section 16).
10. P0_COMPLETE est maintenant dans une table séparée (Section 19), jamais mêlée à la comparaison principale.

## 1. Question scientifique

Que fait notre Decision Maker multiobjectif P0 si on lui soumet les mécanismes d'authentification décrits par Haenel et al. (RFF, MAC cryptographique), avec les performances qu'ils publient, mais qu'on remplace leur règle de décision fixe (RFF-puis-MAC) par un arbitrage multiobjectif ?

**Aucun objectif de faire gagner P0 artificiellement.** Ce document rapporte ce qui a été observé, y compris quand cela ne va pas dans le sens d'un avantage pour P0.

## 2. Ce que Haenel et al. a réellement fait

A. Haenel, Y. Haddad, M. Laurent, Z. Zhang, *"Practical Cross-Layer Radio Frequency-Based Authentication Scheme for Internet of Things"*, Sensors 2021, 21(12), 4034. DOI: 10.3390/s21124034.

Ils proposent un protocole hybride : chaque message est authentifié d'abord par empreinte radiofréquence (RFF) ; en cas de rejet, un repli vers un code d'authentification cryptographique (MAC, Chaskey-12) est déclenché via un échange challenge-réponse. Ils mesurent l'énergie de ce protocole sur un banc d'essai réel et la comparent à un protocole MAC-seul et à un RFF-seul théorique.

## 3. Matériel expérimental Haenel

- **Microcontrôleur du banc d'essai ÉNERGÉTIQUE (Section 6.3.2)** : Texas Instruments **MSP430G2x**, via le kit MSP-EXP430G2ET. Citation littérale : *"we used the Texas Instrument ultra-low-power microcontroller MSP430G2x and the sub-1 GHz RF transceiver CC110L [...] by means of the MSP-EXP430G2ET Launchpad Evaluation Kit"*. Le MSP430FR5994 est utilisé ailleurs dans le papier (nœud aéroporté par drone).
- Radio : CC110L, bande 868–870 MHz.
- Mesure d'énergie : EnergyTrace (Texas Instruments), via MSP-EXP430G2ET + Code Composer Studio.
- Primitive cryptographique : Chaskey-12 (variante normalisée ISO/IEC).
- Batterie : 3 V, 2400 mAh.
- **Deep-sleep explicitement exclu entre deux transmissions** : *"This also prevented the nodes from using the 'deep-sleep' mode of the modules between two transmissions."*

## 4. Protocole : première authentification complète + RFF/fallback

Haenel et al., Section 6.3.3, Figure 11 : *"Due to the first full authentication, the hybrid protocol was a little more energy-demanding at the start of the experiment."* Puis, après environ six transmissions, l'énergie cumulée du MAC-only et de l'hybride devient équivalente, avant que l'hybride ne devienne plus avantageux.

**Le papier ne publie aucune valeur numérique isolée pour ce coût de démarrage.** Impossible de le décomposer physiquement. Conséquence méthodologique (voir Section 8) : le modèle Option A utilise un terme fixe agrégé, nommé explicitement `EFFECTIVE_FIXED_HYBRID_OVERHEAD_MJ`, jamais présenté comme "le coût physique exact de la première authentification".

Convention retenue dans la transposition stochastique B5_HAENEL_CALIBRATED (`run_haenel_experiment_a.py`) : ce terme fixe est ajouté **une seule fois par campagne**, conventionnellement sur le message d'indice 0, uniquement pour les cas HYBRID (jamais RFF_ONLY, cas limite théorique "no fall back" du papier ; jamais MAC_ONLY, où chaque message est déjà une authentification complète).

## 5. Valeurs énergétiques publiées

| Cas | Énergie publiée (mJ / 300 s) |
|---|---|
| RFF_ONLY | 355,412 |
| HYBRID_FRR_05 | 404,790 |
| HYBRID_FRR_10 | 454,076 |
| MAC_ONLY | 564,743 |

## 6. Limite : leur matériel vs notre simulation

**Notre travail est une simulation, jamais une reproduction physique.** Nous n'avons pas mesuré ce matériel. Toute valeur numérique utilisée est classée selon un statut explicite (voir `haenel_parameter_traceability.csv`, `haenel_option_b_sources.csv`) : PUBLISHED_HAENEL, DERIVED_FROM_HAENEL, CALIBRATED_EFFECTIVE, OFFICIAL_DATASHEET, EXTERNAL_SCIENTIFIC_SOURCE, ASSUMED, ASSUMED_STATE_TRANSITION, ou UNAVAILABLE (jamais fabriquée).

## 7. Construction de la transposition (B5_HAENEL_CALIBRATED)

`haenel_b5.py` transpose, de façon **calibrée** (pas littérale), la règle de Haenel et al. par un tirage stochastique `u ~ Uniform(0,1)`, rejet RFF si `u < FRR`. 7 tests statistiques valident la convergence vers 5% et 10% sur 100 000 tirages. **Distinct** du B5 déjà présent dans `physec_dm/case_studies.py` (`select_b5_haenel_rff_then_mac_decision`), qui répond à une question différente (admissibilité FAR réelle dans nos propres scénarios S1-S5) — les deux ne sont jamais mélangés.

## 8. Option A — calibration agrégée (pas une validation indépendante)

**Formulation obligatoire** : Option A est un modèle énergétique agrégé, **calibré directement** sur les 4 mesures publiées de Haenel et al. Il sert d'échelle commune pour comparer les politiques. Son accord avec les points de calibration est une **vérification de cohérence** (le système d'équations a été résolu correctement), **pas une validation indépendante** : les paramètres sont ajustés précisément pour reproduire ces points, les retrouver est donc vrai par construction.

Modèle (système 2×2 résolu exactement sur les deux points HYBRID publiés) :

    E_hybrid(FRR) = E_RFF_BASE_MJ + EFFECTIVE_FIXED_HYBRID_OVERHEAD_MJ
                  + N_fallback_attendu(FRR) × EFFECTIVE_FALLBACK_COST_MJ

Résultat : `EFFECTIVE_FIXED_HYBRID_OVERHEAD_MJ ≈ 0,092 mJ`, `EFFECTIVE_FALLBACK_COST_MJ ≈ 9,857 mJ/repli`. Ce terme fixe agrège tout ce qui n'est pas décomposable (notamment la première authentification complète, Section 4) — **jamais présenté comme un coût physique exact**.

| Cas | Publié (mJ) | Option A (mJ) | Écart |
|---|---|---|---|
| RFF_ONLY | 355,412 | 355,412 | 0,00 % (cas limite théorique, aucun terme fixe) |
| HYBRID_FRR_05 | 404,790 | 404,790 | 0,00 % (cohérence de calibration) |
| HYBRID_FRR_10 | 454,076 | 454,076 | 0,00 % (cohérence de calibration) |
| MAC_ONLY | 564,743 | 564,743 | **published reference used directly**, jamais prédit par la formule hybride |

Sur 30 graines, B5_HAENEL_CALIBRATED (tirage stochastique réel) donne 408,08 ± 26,31 mJ à FRR=5% et 452,43 ± 32,85 mJ à FRR=10%, cohérent avec les valeurs publiées.

## 9. P0_AUTH_ONLY — adaptation énergétique commune

`haenel_energy_adapter.py` donne aux deux candidats (A1-K0, A2-K0) évalués par P0 la MÊME échelle énergétique calibrée sur Haenel et al. (mJ/message), tandis que la robustesse (Rauth) et la qualité de clé (Qkey) restent calculées par le vrai modèle physec_dm (jamais recalibrées). La latence, non publiée de façon comparable, est explicitement **neutralisée** (statut `UNAVAILABLE / NOT DIRECTLY COMPARABLE`).

## 10. Utilisation du même RFF Haenel (comparaison principale)

**Correction majeure de cette passe.** La question scientifique (Section 1) exige que A2 reçoive la MÊME performance de sécurité que Haenel et al. publie — pas le FAR natif de notre propre modèle de canal (`~8,39×10⁻⁵`, dépendant d'un contexte SNR ASSUMED).

`haenel_energy_adapter.apply_haenel_rff_far_to_a2` remplace le FAR de A2 par `FAR_RFF_HAENEL = 0,002`, en réutilisant les VRAIES formules du modèle physec_dm (`authentication.calculate_a2_total_false_acceptance`, `calculate_a2_robustness`) — jamais un calcul `1 - far` à la main. Ceci donne naissance à **P0_AUTH_ONLY_HAENEL_RFF**, la comparaison principale de ce document.

Le FAR natif (~8,39×10⁻⁵) n'est PAS supprimé : il reste disponible séparément sous le nom **P0_NATIVE_RFF_SENSITIVITY** (`p0_auth_only_haenel_scale.py`), qui répond à une question différente ("que ferait P0 avec son propre modèle statistique RFF ?"), jamais mélangée à la comparaison principale.

## 11. Résultat principal — FRR=10% / FAR=0,002 (cas le plus propre scientifiquement)

Haenel et al., Section 6.3.1 : *"This value [FRR=10%] was chosen as it led to a FAR of 0.2% in our live experiment."* Cette phrase associe explicitement le FRR=10% simulé dans le banc d'essai énergétique au FAR=0,2% de l'expérience de classification (Section 6.2.2, où le FRR mesuré est 10,89%, arrondi à 10% pour la simulation énergétique). C'est le SEUL cas où Haenel et al. relie explicitement un FRR énergétique à un FAR de sécurité.

**Résultat : P0_AUTH_ONLY_HAENEL_RFF choisit A1 (MAC, 564,743 mJ), jamais A2 (RFF, 454,076 mJ), sous poids égaux.**

Écarts d'énergie (comparaisons non mélangées, calibré vs Monte-Carlo distingués) :
- P0 (564,743 mJ, déterministe) vs Haenel Hybrid FRR=10% publié (454,076 mJ) : **+110,667 mJ, soit +24,38%**.
- P0 (564,743 mJ) vs B5_HAENEL_CALIBRATED moyenne Monte-Carlo (452,43 ± 32,85 mJ, 30 graines) : **+112,31 mJ, soit +24,82%**.

![Figure 1 — La courbe publiée de Haenel et al. baisse avec le FRR (le RFF est utilisé de plus en plus souvent) ; B5_HAENEL_CALIBRATED (bande IC95%, 30 graines) suit cette même tendance ; P0_AUTH_ONLY_HAENEL_RFF reste sur une ligne plate, confondue avec le plafond MAC_ONLY publié, quel que soit le FRR. C'est la comparaison centrale de ce rapport : RFF-vers-MAC (Haenel) contre choix fixe (P0).](results/haenel_comparison/figures/figure_1_energy_comparison.png)

![Figure 2 — Répartition des décisions par message (sur 100) : B5_HAENEL_CALIBRATED alterne entre RFF direct et repli MAC selon le FRR simulé, alors que P0_AUTH_ONLY_HAENEL_RFF choisit A1 (MAC) pour 100% des messages, aux deux FRR testés.](results/haenel_comparison/figures/figure_2_decision_split.png)

## 12. FRR=5% comme sensibilité énergétique (pas une paire mesurée)

Haenel et al. mesure aussi l'énergie à FRR=5% (pour illustrer une amélioration future du RFF) mais **ne publie pas de FAR apparié expérimentalement à ce FRR précis**. Si ce module réutilise FAR=0,002 pour ce cas, il est étiqueté explicitement `ASSUMED_CONSTANT_FAR_FOR_FRR5_SENSITIVITY` dans tous les CSV et jamais présenté comme une paire FRR=5%/FAR=0,2% mesurée par Haenel et al.

Résultat identique sous cette hypothèse : P0 choisit A1 (564,743 mJ) contre Hybrid FRR=5% publié (404,790 mJ, **+159,953 mJ soit +39,52%**) et B5_HAENEL_CALIBRATED Monte-Carlo (408,08 ± 26,31 mJ, **+156,66 mJ soit +38,39%**).

![Figure 3 — Nombre de replis MAC observés (B5_HAENEL_CALIBRATED, moyenne ± écart-type sur 30 graines) en fonction du FRR configuré, comparé à la valeur théorique attendue (FRR × 100 messages). Confirme que le mécanisme de repli simulé se comporte comme attendu, indépendamment de la décision de P0.](results/haenel_comparison/figures/figure_3_fallback_vs_frr.png)

## 13. Pareto / Tchebycheff / tie-break — vérifié dans le code

Les deux candidats sont admissibles, tous deux sur le front de Pareto (2 points), et obtiennent **exactement le même score de Tchebycheff (0,25)**. Ce n'est pas une coïncidence : `calculate_tchebycheff_score` calcule `score = max_k(poids_k × écart_normalisé_k)`. Avec latence et Qkey neutres (identiques pour les deux), et A2 idéal en énergie / nadir en Rauth, A1 idéal en Rauth / nadir en énergie :

    score(A1) = w_energy   (A1 au nadir sur l'axe énergie)
    score(A2) = w_auth     (A2 au nadir sur l'axe robustesse)

Vérifié numériquement dans `weight_boundary_sensitivity.py` : écart maximal entre `score(A1)` et `w_energy` sur 11 points testés = **0,00e+00** (exact). Sous poids égaux, égalité stricte (0,25 = 0,25), départagée par le tie-break FAR croissant : A1 (FAR≈0) bat A2 (FAR=0,002).

## 14. Frontière des poids — EXACTEMENT à w_energy = w_auth

**Ne plus écrire** : *"il faut donner beaucoup plus d'importance à l'énergie pour que P0 choisisse A2"*. Le sweep fin (`weight_boundary_sensitivity.py`, `w_latency=w_qkey=0,25` fixés, `w_energy+w_auth=0,50`) donne :

| w_energy | w_auth | score(A1) | score(A2) | Choix |
|---|---|---|---|---|
| 0,20 | 0,30 | 0,200 | 0,300 | A1 |
| 0,245 | 0,255 | 0,245 | 0,255 | A1 |
| 0,249 | 0,251 | 0,249 | 0,251 | A1 |
| **0,250** | **0,250** | **0,250** | **0,250** | **A1 (tie-break)** |
| 0,251 | 0,249 | 0,251 | 0,249 | **A2** |
| 0,255 | 0,245 | 0,255 | 0,245 | A2 |
| 0,30 | 0,20 | 0,300 | 0,200 | A2 |

![Figure 5 — Score de Tchebycheff d'A1 et d'A2 en fonction du poids énergie (w_energy), sur le sweep fin de 11 points. Les deux courbes se croisent EXACTEMENT à w_energy = w_auth = 0,25 : au-delà de ce point, la décision bascule d'A1 vers A2.](results/haenel_comparison/figures/figure_5_weight_sensitivity.png)

**Un écart de seulement 0,001 (0,251 contre 0,249) fait basculer la décision.** Formulation correcte : *"avec les poids égaux, P0 tombe exactement sur une égalité entre le gain énergétique d'A2 et l'avantage de robustesse d'A1 ; le tie-break sur le FAR sélectionne alors A1. Ce résultat dépend du point de préférence choisi et de la règle de départage, pas d'une préférence forte pour la sécurité."*

**Réserve sur la sensibilité latence** (`latency_sensitivity.py`) : faire varier le ratio de latence A2/A1 de 0,01 à 100 ne change jamais la décision — mais avec seulement deux candidats, l'écart normalisé sur un axe où un candidat est au nadir vaut toujours exactement 1,0 par construction. **Cette expérience illustre le comportement de la scalarisation dans ce problème réduit à deux candidats ; elle ne constitue pas une validation physique de l'absence d'effet de la latence.**

## 15. Expérience sécurité — 100 000 tentatives (illustration, pas validation pour P0)

Campagne Monte-Carlo dédiée (`security_monte_carlo.py`), distincte du banc d'essai énergétique :

| Politique | Tentatives | Acceptées | FAR empirique | FAR attendu | IC95% (Clopper-Pearson) |
|---|---|---|---|---|---|
| B5_HAENEL_CALIBRATED (A2/RFF) | 100 000 | 189 | 0,189% | 0,20% (PUBLISHED_HAENEL) | [0,163% ; 0,218%] |
| P0_AUTH_ONLY_HAENEL_RFF (A1) | 100 000 | 0 | 0% | 5,42×10⁻²⁰ (borne théorique) | [0% ; 0,00369%] |

Le FAR publié de Haenel et al. est compatible avec l'IC95% mesuré côté B5 (méthode validée). **Pour P0, "0 acceptation sur 100 000" est une illustration Monte-Carlo du modèle, PAS une validation expérimentale, et n'est jamais présenté comme une preuve de supériorité de sécurité** : l'IC95% supérieur (≈3,7×10⁻⁵) montre que ce volume ne peut pas distinguer une borne théorique de 5,4×10⁻²⁰ d'un FAR simplement inférieur à ~3,7×10⁻⁵.

![Figure 4 — Campagne Monte-Carlo de sécurité (100 000 tentatives) : FAR empirique de B5_HAENEL_CALIBRATED (barre d'erreur = IC95% Clopper-Pearson) comparé au FAR observé de P0_AUTH_ONLY_HAENEL_RFF (0 acceptation sur 100 000, borne supérieure de l'IC95% affichée).](results/haenel_comparison/figures/figure_4_security.png)

## 16. Option B — modèle événementiel (matériel réel, timing corrigé)

Construit sur le MSP430G2x + CC110L réels (Section 3). Deux corrections de cette passe :
- **Transition d'état CC110L** : une première version utilisait 240 µs ("From Sleep to RX Mode", datasheet CC110L page de garde) — un temps de réveil DEPUIS LE DEEP-SLEEP, incohérent avec l'exclusion explicite du deep-sleep par Haenel et al. (Section 3). Corrigé sur la Table 5-11 du datasheet CC110L (transitions depuis IDLE) : 75,1 µs (LOW, sans calibration) à 799 µs (CENTRAL, avec calibration par défaut) à 1598 µs (HIGH, deux calibrations). Statut `ASSUMED_STATE_TRANSITION` (le papier ne publie pas la configuration exacte de calibration).
- **Coût Chaskey sur MSP430** : recherché activement (Mouha et al. 2015, eprint 2015/1182) — donne les chiffres ARM Cortex-M (9,8/7,0 cycles/octet) et un ratio relatif "+30% sur MSP430" pour Chaskey-12, mais AUCUNE valeur absolue MSP430. Un article dédié existe (Lee & Seo, IEEE, "Optimized implementation of chaskey MAC on 16-bit MSP430") mais était inaccessible cette session (accès payant). Plage 10-40 cycles/octet conservée, statut `EXTERNAL_SCIENTIFIC_SOURCE`/`ASSUMED_MAPPING`, valeur absolue MSP430 `UNAVAILABLE`.

## 17. Ce que l'Option B explique réellement — surcoût incrémental

**Correction majeure de cette passe.** L'ancienne formulation ("Option B explique 63 à 89% du surcoût réel") était fausse : RFF_ONLY est reproduit PAR CONSTRUCTION grâce à un résiduel calibré dessus, donc comparer les totaux ABSOLUS surestime largement ce qu'Option B explique. La grandeur pertinente est le **surcoût incrémental** au-dessus de RFF_ONLY :

    measured_increment  = E_Haenel(cas) - E_Haenel(RFF_ONLY)
    modeled_increment   = E_OptionB(cas) - E_OptionB(RFF_ONLY)
    increment_explained_pct = 100 × modeled_increment / measured_increment

| Cas | Set | Mesuré (mJ) | Modélisé (mJ) | Expliqué |
|---|---|---|---|---|
| HYBRID_FRR_05 | LOW | 49,378 | 0,093 | 0,19% |
| HYBRID_FRR_05 | CENTRAL | 49,378 | 0,191 | 0,39% |
| HYBRID_FRR_05 | HIGH | 49,378 | 3,853 | 7,80% |
| HYBRID_FRR_10 | LOW | 98,664 | 0,187 | 0,19% |
| HYBRID_FRR_10 | CENTRAL | 98,664 | 0,381 | 0,39% |
| HYBRID_FRR_10 | HIGH | 98,664 | 7,706 | 7,81% |
| MAC_ONLY | LOW | 209,331 | 0,641 | 0,31% |
| MAC_ONLY | CENTRAL | 209,331 | 1,338 | 0,64% |
| MAC_ONLY | HIGH | 209,331 | 30,242 | 14,45% |

**Conclusion recalculée (pas copiée) : Option B retrouve l'ordre qualitatif des configurations (RFF_ONLY < HYBRID_05 < HYBRID_10 < MAC_ONLY sur les 3 jeux d'hypothèses), mais le modèle bottom-up actuel ne reconstruit qu'une FAIBLE FRACTION du surcoût incrémental crypto/fallback mesuré par Haenel et al. : entre 0,19% et 14,45% selon le cas et le jeu d'hypothèses.** Une part importante de l'énergie reste agrégée dans le résiduel calibré (Option A) et/ou dépend de détails d'implémentation non publiés (fenêtre d'écoute/timeout en réception, coût de resynchronisation, configuration de calibration radio) — des causes **possibles**, non confirmées, non mesurées.

**Option A reste la référence QUANTITATIVE de la comparaison P0/B5. Option B est une ANALYSE STRUCTURELLE / PHYSIQUE DE SENSIBILITÉ, jamais un modèle d'énergie absolue validé.**

## 18. Incertitudes matérielles (synthèse traçabilité)

`haenel_option_b_sources.csv` : 10 OFFICIAL_DATASHEET, 2 PUBLISHED_IN_HAENEL, 1 DERIVED, 2 EXTERNAL_SCIENTIFIC_SOURCE, 1 ASSUMED_STATE_TRANSITION, 3 UNAVAILABLE. `haenel_parameter_traceability.csv` : 8 PUBLISHED_HAENEL, 2 CALIBRATED_EFFECTIVE, 1 DERIVED_FROM_HAENEL, 1 ASSUMED, 1 OFFICIAL_DATASHEET, 1 ASSUMED_STATE_TRANSITION, 1 EXTERNAL_SCIENTIFIC_SOURCE. Chaque statut est documenté avec sa colonne `used_in` (où le paramètre sert réellement dans le code).

## 19. P0_COMPLETE — extension exploratoire (table séparée)

**NE PAS confondre avec la comparaison principale (Sections 10-15).** `p0_complete_extension_table.csv` (table SÉPARÉE, jamais insérée dans le même classement que A/B/C) : en réactivant K1a/K1b/K2 (Decision Maker complet, non restreint, sur l'échelle LoRa/Semtech native — Haenel et al. ne couvre pas la gestion de clé physique), le Decision Maker choisit **A1-K1a** dans le contexte statique testé. Cette extension reste exploratoire, sans référence publiée à laquelle se comparer, et son énergie (échelle LoRa native) n'est PAS comparable en valeur absolue à Haenel et al.

## 20. Limites

- Contexte P0 (SNR, séparation Alice/Mallory) ASSUMED pour l'analyse secondaire P0_NATIVE_RFF_SENSITIVITY — n'affecte PAS la comparaison principale (Section 10), qui utilise directement le FAR publié.
- Option B bloquée par des paramètres non publiés (taille de trame, débit, coût Chaskey réel sur MSP430) ; le surcoût incrémental expliqué reste sous 15% même à la borne HIGH.
- La référence exacte de puce dans la famille MSP430G2x (ex. MSP430G2553) est une déduction (DERIVED, à partir du kit MSP-EXP430G2ET nommé par Haenel et al.), pas une confirmation explicite du papier.
- La sensibilité à la latence est structurellement bornée par la normalisation à 2 candidats (Section 14) — ne pas en tirer une conclusion physique générale.
- Résultat "P0 = 100% A1 sous poids égaux" spécifique à ce contexte statique à 2 candidats (K0 figé, pas d'attaquant en Expérience A) — ne généralise pas nécessairement aux scénarios S1-S5 complets (8 décisions, contexte dynamique), qui restent la référence scientifique principale du projet et n'ont pas été modifiés.

## 21. Conclusion

Dans la transposition du scénario de Haenel et al., leur stratégie publiée exploite systématiquement le RFF puis utilise la cryptographie en repli. Lorsque les mêmes options d'authentification (avec la MÊME performance RFF publiée, FAR=0,002) sont soumises à P0 avec des poids égaux, **P0 sélectionne A1**. Dans ce cas réduit à deux candidats, l'avantage énergétique d'A2 et l'avantage de robustesse d'A1 conduisent à une **égalité stricte de scalarisation**, départagée en faveur d'A1 par le FAR (vérifié mathématiquement et dans le code, Sections 13-14). Cette décision entraîne donc une consommation d'énergie plus élevée (+24,4% à FRR=10%, +39,5% à FRR=5%) que la stratégie hybride de Haenel et al. dans ce scénario précis — mais elle résulte du compromis et de la règle de départage, **pas de l'inadmissibilité du RFF** (les deux candidats sont admissibles). Une modification des préférences de seulement 0,001 sur les poids déplace la décision vers A2. Il ne s'agit donc ni d'un échec de P0 ni d'une victoire de B5, mais d'une illustration honnête et précisément quantifiée d'un compromis multiobjectif au bord de sa frontière de décision.

## 22. Prochaines étapes pour publication ICC/GLOBECOM

1. Sourcer précisément le coût Chaskey(-12) sur architecture MSP430 16 bits (l'article dédié de Lee & Seo existe mais était inaccessible cette session) — obtenir ce chiffre clorait la plus grande partie de l'incertitude d'Option B.
2. Obtenir ou mesurer la configuration réelle de calibration radio (registres MCSM0/TEST0/FSCAL3) et la fenêtre d'écoute/timeout du protocole de Haenel et al. — cause la plus probable du surcoût incrémental non expliqué (Section 17).
3. Étendre la comparaison principale à un contexte dynamique (SNR variable) plutôt que statique, pour observer si P0 bascule vers A2 dans des conditions plus favorables au RFF.
4. Explorer la zone de la frontière des poids (Section 14) comme point de discussion central : la décision de P0 est réversible avec un déplacement minime des préférences, ce qui est en soi un résultat notable pour un article.
5. Si publication : présenter clairement la distinction comparaison principale (FAR publié Haenel, Section 10-15) / analyse secondaire (FAR natif physec_dm) / extension exploratoire (P0_COMPLETE) pour éviter toute confusion côté relecteurs.
