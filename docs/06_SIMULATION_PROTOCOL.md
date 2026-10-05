# Protocole complet de simulation de PHYSEC-DM

## 1. Objet du document

Ce document définit le protocole expérimental officiel du projet **PHYSEC-DM**. Il transforme la modélisation scientifique en expériences reproductibles permettant de vérifier :

- le canal radio ;
- l’authentification physique ;
- la génération et la gestion de clé ;
- les coûts d’énergie et de latence ;
- les règles d’admissibilité ;
- le front de Pareto ;
- l’arbitrage final du Decision Maker ;
- les performances de mission ;
- la comparaison avec les politiques de référence.

La source scientifique de vérité reste :

```text
modelisation_parametres_modifies(1).tex
modelisation parametre modifié.pdf
```

Le protocole ne modifie aucune équation. Il précise comment les fonctions seront testées, combinées et comparées.

---

## 2. Ordre expérimental obligatoire

```text
1. valider les paramètres ;
2. exécuter les tests unitaires ;
3. reproduire les valeurs de référence ;
4. réaliser les balayages déterministes ;
5. valider le Decision Maker sur des contextes contrôlés ;
6. exécuter une mission complète ;
7. comparer P0 aux politiques B1 à B4 ;
8. répéter par Monte Carlo ;
9. calculer les intervalles de confiance ;
10. réaliser l’analyse de sensibilité ;
11. exporter les figures, tableaux et manifestes ;
12. interpréter les résultats dans les limites du modèle.
```

Une mission aléatoire ne doit pas être utilisée pour masquer un sous-modèle non validé.

---

## 3. Reproductibilité

Chaque résultat doit être reconstructible à partir de :

```text
version du code
version du modèle
version des paramètres
identifiant du scénario
identifiant de la politique
graine aléatoire
versions des bibliothèques
```

### 3.1. Générateur aléatoire

Chaque répétition utilise une graine :

\[
s_r
\]

Un seul générateur est créé au début de la répétition puis transmis aux fonctions.

```python
rng = numpy.random.default_rng(seed)
```

Il est interdit de réinitialiser la graine dans plusieurs fonctions.

### 3.2. Graines communes

Pour un même scénario, toutes les politiques utilisent :

\[
s_1,\ldots,s_{N_{\mathrm{MC}}}
\]

Elles reçoivent donc les mêmes :

- réalisations de shadowing ;
- valeurs de criticité ;
- tentatives de Mallory ;
- événements de compromission ;
- traces radio ;
- conditions initiales.

Seule la règle de décision change.

### 3.3. Instantané des paramètres

Chaque campagne exporte la totalité des paramètres utilisés, avec :

```text
nom
valeur
unité
statut
source
```

---

## 4. Organisation des fichiers

```text
physec_dm/
├── simulation.py
├── campaign.py
├── validation.py
├── configs/
│   ├── nominal.yaml
│   ├── deterministic_sweeps.yaml
│   ├── monte_carlo.yaml
│   ├── sensitivity.yaml
│   └── policies.yaml
├── results/
│   ├── raw/
│   ├── processed/
│   ├── figures/
│   ├── tables/
│   ├── logs/
│   └── manifests/
└── tests/
```

Le dossier `raw` contient les résultats non agrégés. Le dossier `processed` contient les agrégations et les intervalles de confiance.

---

## 5. Niveaux de simulation

### Niveau 1 — Fonction isolée

Exemples :

```text
SNR
rho_AB
FAR
FRR
KDR
Time-on-Air
énergie TX/RX/CPU
```

### Niveau 2 — Action isolée

```text
A1
A2
K0
K1a
K1b
K2
```

### Niveau 3 — Decision Maker dans un contexte fixe

Les huit décisions sont évaluées sans modifier l’état.

### Niveau 4 — Mission complète

La batterie, la clé, le duty-cycle et les compteurs évoluent dans le temps.

---

# 6. Étape 0 — Validation des paramètres

Avant toute expérience :

```python
parameters.validate()
```

La validation doit vérifier :

- les unités ;
- les domaines numériques ;
- la cohérence des tailles de paquets ;
- la cohérence \(b_{\mathrm{MAC}}=8M_{\mathrm{tag}}\) ;
- la cohérence \(\rho_{\min}=\cos(\pi KDR_{\max})\) ;
- les budgets strictement positifs ;
- les poids de somme 1 ;
- la présence des paramètres obligatoires ;
- le statut des paramètres non validés.

Les paramètres encore ouverts doivent être signalés :

```text
numerical_epsilon
minimum_deadline_s
security_strength_bits
variation_feasible
courbe calibrée g_q
C_MAC
C_rec_per_bit
C_PA
E_sens
E_app
E_RXwin
E_sleep
L_CR
protocole K2
poids contextuels
score_tolerance
dominance_tolerance
mode de secours
```

Une campagne utilisant ces paramètres doit être marquée `exploratory_run = True`.

---

# 7. Étape 1 — Tests unitaires

## 7.1. Canal

```text
CH-TEST-001 : 0 dB ↔ gamma = 1
CH-TEST-002 : conversion dB/linéaire aller-retour
CH-TEST-003 : PL(d0) = PL(d0)
CH-TEST-004 : bilan de liaison manuel
CH-TEST-005 : bruit thermique à 125 kHz et NF = 6 dB
CH-TEST-006 : Doppler nul pour vitesse nulle
CH-TEST-007 : J0(0) = 1
CH-TEST-008 : rho_noise monotone en SNR
CH-TEST-009 : conservation d’une corrélation négative
CH-TEST-010 : rho_AB dans [-1,1]
```

## 7.2. Authentification

```text
AU-TEST-001 : vecteur CFO–DCO–PO de dimension 3
AU-TEST-002 : moyenne d’enrôlement
AU-TEST-003 : Mahalanobis nulle sur la référence
AU-TEST-004 : forme générale = forme isotrope
AU-TEST-005 : T = theta implique acceptation
AU-TEST-006 : theta ≈ 7,815 pour nf = 3 et FRR = 5 %
AU-TEST-007 : FRR(theta) ≈ 0,05
AU-TEST-008 : lambda = d_M² gamma_M
AU-TEST-009 : FAR décroissante avec lambda
AU-TEST-010 : p_forge = 2^(-64)
AU-TEST-011 : robustesse complète de A2
AU-TEST-012 : repli Alice = FRR
AU-TEST-013 : repli Mallory = 1 - FAR
```

## 7.3. Gestion de clé

```text
KM-TEST-001 : KDR(0,6) ≈ 0,2952
KM-TEST-002 : KDR(1) = 0
KM-TEST-003 : KDR(0) = 0,5
KM-TEST-004 : KDR(-1) = 1
KM-TEST-005 : rho_min ≈ 0,587785
KM-TEST-006 : h2(0) = 0
KM-TEST-007 : h2(0,5) = 1
KM-TEST-008 : rendement nul à KDR = 0,5
KM-TEST-009 : N_meas décroît avec le rendement
KM-TEST-010 : seuil de faisabilité inclusif
KM-TEST-011 : vieillissement de clé
KM-TEST-012 : expiration par âge
KM-TEST-013 : expiration par messages
KM-TEST-014 : expiration par compromission
KM-TEST-015 : échéance gouvernée par la première limite
```

## 7.4. Énergie et latence

```text
CO-TEST-001 : T_air(8) = 0,991232 s
CO-TEST-002 : T_air(32) = 1,810432 s
CO-TEST-003 : T_air(40) = 1,974272 s
CO-TEST-004 : T_air(32)/0,01 ≈ 181,0432 s
CO-TEST-005 : E_TX = VIT
CO-TEST-006 : E_RX = VIT
CO-TEST-007 : énergie CPU linéaire en cycles
CO-TEST-008 : A1 ne recompte pas M_data
CO-TEST-009 : coût attendu A2 ≤ pire cas A2
CO-TEST-010 : K0 a un coût nul
CO-TEST-011 : K1b croît avec N_meas
CO-TEST-012 : latence normalisée = maximum des deux ratios
```

## 7.5. Decision Maker

```text
DM-TEST-001 : exactement huit décisions
DM-TEST-002 : A2 rejetée sans profil RFF
DM-TEST-003 : K0 seule si r_t = 0
DM-TEST-004 : K0 rejetée si r_t = 1
DM-TEST-005 : K1 rejetée si phi_PHY = 0
DM-TEST-006 : batterie au seuil admissible
DM-TEST-007 : délai au seuil admissible
DM-TEST-008 : FAR critique et normale
DM-TEST-009 : dominance
DM-TEST-010 : front exact
DM-TEST-011 : Tchebychev
DM-TEST-012 : bris d’égalité
DM-TEST-013 : refus motivé
DM-TEST-014 : contexte immuable
```

Tous les tests bloquants doivent réussir avant les balayages.

---

# 8. Étape 2 — Reproduction des références

## 8.1. Time-on-Air

Configuration :

```text
M = 32 octets
SF = 12
BW = 125 kHz
CR_idx = 1
N_pre = 8
CRC = 1
IH = 0
DE = 1
```

Résultats attendus :

\[
T_{\mathrm{air}}=1{,}810432\ \mathrm{s}
\]

\[
T_s=181{,}0432\ \mathrm{s}
\]

à 1 % de duty-cycle.

## 8.2. Seuil RFF

\[
n_f=3,\quad \alpha_{\mathrm{FRR}}=0{,}05
\]

\[
\theta\approx7{,}815
\]

## 8.3. KDR

\[
\rho_{AB}=0{,}6
\]

\[
KDR_{\mathrm{brut}}\approx0{,}2952
\]

## 8.4. Ruotsalainen hors ligne

Reproduire :

\[
n_{\mathrm{keys}}=\frac{128}{KDR_{\mathrm{Eve}}-KDR_{AB}}
\]

\[
n_{\mathrm{meas}}=\frac{n_{\mathrm{keys}}}{KPM}
\]

\[
T_{\mathrm{AES}}=n_{\mathrm{meas}}T_s
\]

Ces équations ne deviennent jamais une règle en ligne du DM.

## 8.5. ECC

Vérifier séparément les points de comparaison :

```text
signature secp192r1 :
    environ 0,019 J
    environ 218 ms
```

Ils ne représentent pas K2 complet.

---

# 9. Étape 3 — Balayages du canal

## CH-SWEEP-01 — SNR imposé

Balayer :

```text
-20 dB à 30 dB
pas de 0,5 ou 1 dB
```

Fixer :

```text
f_d = 0
Delta_t = 1 s
rho_HW = valeur nominale
```

Exporter :

```text
snr_db
snr_linear
rho_noise
rho_AB
KDR
agreement_feasible
```

## CH-SWEEP-02 — SNR et Doppler

Balayer :

```text
SNR
f_d de 0 à 2,89 Hz
```

Produire :

```text
carte rho_AB(SNR, f_d)
carte KDR(SNR, f_d)
frontière de faisabilité
```

## CH-SWEEP-03 — Corrélations négatives

Comparer :

```text
modèle signé
variante tronquée
```

Exporter :

```text
rho_signed
rho_truncated
KDR_signed
KDR_truncated
```

## CH-SWEEP-04 — Distance

Utiliser uniquement le mode distance et balayer :

```text
distance
path_loss_exponent
shadowing
```

Exporter :

```text
path_loss_db
received_power_dbm
noise_power_dbm
snr_db
```

---

# 10. Étape 4 — Balayages de l’authentification

## AU-SWEEP-01 — FAR selon le SNR

Fixer :

```text
n_f = 3
theta = seuil nominal
d_M = valeur nominale
```

Calculer :

```text
gamma_M
lambda_M
FAR
P_FA_total(A2)
R_auth(A2)
```

## AU-SWEEP-02 — FAR selon d_M

Balayer :

```text
d_M de 0,5 à 5
```

à plusieurs SNR.

## AU-SWEEP-03 — FAR et FRR selon le seuil

Balayer \(\theta\) et produire :

```text
FAR(theta)
FRR(theta)
ROC
point nominal
```

## AU-SWEEP-04 — EER

Trouver numériquement :

\[
FAR(\theta)\approx FRR(\theta)
\]

L’EER reste une métrique de diagnostic.

## AU-SWEEP-05 — A1 contre A2

Comparer :

```text
robustesse A1
robustesse A2
coût A1
coût attendu A2
pire cas A2
```

---

# 11. Étape 5 — Balayages de la gestion de clé

## KM-SWEEP-01 — KDR selon la corrélation

Balayer :

\[
\rho_{AB}\in[-1,1]
\]

Calculer :

```text
KDR_brut
h2
Q_key(K1)
agreement_feasible
```

## KM-SWEEP-02 — Rendement et nombre de mesures

Balayer :

```text
KDR
eta_keep
```

Produire :

```text
y_rec selon KDR
N_meas selon KDR
```

## KM-SWEEP-03 — K1a contre K1b

Comparer pour plusieurs \(N_{\mathrm{meas}}\) :

```text
énergie K1a
énergie K1b
latence K1a
latence K1b
```

## KM-SWEEP-04 — Cryptopériode

Balayer :

```text
âge
nombre de messages
```

Calculer :

```text
u_time
u_msg
q_t
r_t
e_key
T_deadline
Q_key(K0)
```

## KM-SWEEP-05 — Paramètres encore ouverts

Tester explicitement :

```text
minimum_deadline_s
security_strength_bits
variation_feasible
quantization_mode
```

Ces résultats sont exploratoires.

---

# 12. Étape 6 — Balayages des coûts

## CO-SWEEP-01 — Taille de paquet

Balayer `payload_bytes` et calculer :

```text
T_air
E_tx
E_rx
```

## CO-SWEEP-02 — A1

Balayer :

```text
M_tag
C_MAC
```

Séparer le coût radio et le coût CPU.

## CO-SWEEP-03 — A2

Balayer :

```text
FRR
E_CR
L_CR
```

Comparer coût attendu et pire cas.

## CO-SWEEP-04 — Clés

Comparer :

```text
K0
K1a
K1b
K2
```

sur les mêmes hypothèses de clé cible.

---

# 13. Étape 7 — Contextes contrôlés du Decision Maker

## DM-CTX-01 — Clé valide, RFF disponible

```text
r_t = 0
v_RFF = 1
```

Décisions logiquement possibles :

```text
A1-K0
A2-K0
```

## DM-CTX-02 — Clé valide, RFF indisponible

```text
r_t = 0
v_RFF = 0
```

Décision logique restante :

```text
A1-K0
```

## DM-CTX-03 — Renouvellement requis, PHY faisable

```text
r_t = 1
phi_PHY = 1
```

## DM-CTX-04 — Renouvellement requis, PHY non faisable

```text
r_t = 1
phi_PHY = 0
```

K1a et K1b sont rejetées.

## DM-CTX-05 — Batterie faible

Construire un contexte où certaines décisions dépassent :

\[
B_t-B_{\min}
\]

## DM-CTX-06 — Message critique

```text
L_max = 5 s
FAR_max = 0,01
```

## DM-CTX-07 — Duty-cycle insuffisant

Rejeter les actions aux échanges supplémentaires.

## DM-CTX-08 — Ensemble admissible vide

Vérifier :

```text
refus motivé
aucune décision cachée
journal complet
```

## DM-CTX-09 — Front avec plusieurs points

Construire plusieurs décisions non dominées.

## DM-CTX-10 — Égalité

Vérifier l’ordre :

```text
FAR
énergie
latence bloquante
ordre lexicographique
```

---

# 14. Étape 8 — Cartes de décision

Produire au minimum :

```text
décision selon SNR et batterie
décision selon SNR et âge de clé
décision selon SNR et criticité
décision selon rho_AB et q_t
décision selon d_M et SNR
```

Chaque cellule exporte :

```text
selected_decision
admissible_count
pareto_count
refusal
dominant_rejection_reason
score
```

Chaque carte précise les paramètres fixes, les poids et le statut de \(\phi_{\mathrm{var}}\).

---

# 15. Politiques comparées

## P0 — DM proposé

```text
règles logiques
contraintes
plancher de FAR
Pareto exact
Tchebychev
```

## B1 — Conventionnelle

```text
A1
K0 si la clé reste valide
K2 si renouvellement requis
```

## B2 — PhySec naïve

```text
A2 lorsque disponible
K1 dès qu’une condition minimale est satisfaite
aucun plancher de FAR
```

La règle exacte doit être écrite dans `policies.yaml`.

## B3 — Hybride fixe

Exemple de structure :

```text
A2 au-dessus d’un seuil SNR fixe
A1 sinon
K1a au-dessus d’un seuil de corrélation
K2 sinon
```

Les seuils doivent être déclarés.

## B4 — DM sans plancher de FAR

Identique à P0, sauf suppression de DM-EQ102.

## 15.1. Comparaison équitable

Toutes les politiques utilisent :

```text
même E_base
mêmes coûts radio
mêmes coûts CPU
mêmes traces
mêmes attaques
mêmes graines
même protocole K2
```

---

# 16. Étape 9 — Mission complète

## 16.1. État initial

```text
B_0
âge de clé initial
messages avec la clé
identifiant de clé
budget duty-cycle
compteurs
t = 0
```

## 16.2. Boucle

À chaque période :

```text
1. générer ou lire Gamma_t ;
2. générer ou lire f_d,t ;
3. tirer la criticité ;
4. calculer le canal ;
5. calculer l’état de clé ;
6. construire le contexte ;
7. appeler la politique ;
8. traiter Alice ;
9. débiter seulement l’énergie réellement engagée ;
10. mettre à jour la clé ;
11. tirer Mallory indépendamment ;
12. évaluer Mallory chez Bob ;
13. ne pas débiter Alice pour Mallory ;
14. vérifier le plancher au SNR réel ;
15. mettre à jour les compteurs ;
16. avancer le temps.
```

## 16.3. Arrêt

```text
B_t <= B_min
durée maximale
nombre maximal de périodes
erreur bloquante
```

## 16.4. Refus de service

Si aucune décision n’est admissible :

- enregistrer le refus ;
- débiter uniquement les coûts déjà engagés ;
- ne pas sélectionner automatiquement une décision ;
- utiliser uniquement un mode de secours déclaré.

---

# 17. Processus de Mallory

À chaque période :

\[
M_t\sim\mathrm{Bernoulli}(p_M)
\]

Si Mallory attaque :

```text
N_M += 1
évaluer l’action d’authentification
N_FA += 1 si acceptée
```

Pour les messages critiques :

```text
N_M,C
N_FA,C
```

Toujours :

```text
energy_debited_from_alice_for_mallory = 0
```

La FAR empirique est :

\[
\widehat{FAR}=\frac{N_{FA}}{N_M}
\]

si \(N_M>0\). Lorsque \(N_M=0\), la FAR est `non définie`, pas zéro.

---

# 18. SNR observé et SNR réel

Pour compter :

\[
N_{\mathrm{viol}}
\]

le protocole distingue :

```text
SNR observé par le DM
SNR réel utilisé après décision
```

Une extension contrôlée peut utiliser :

\[
\Gamma_t^{\mathrm{obs}}=\Gamma_t^{\mathrm{real}}+\varepsilon_{\Gamma,t}
\]

La loi de \(\varepsilon_{\Gamma,t}\) est un paramètre de scénario à valider.

---

# 19. Métriques de mission

## 19.1. Autonomie

\[
T_{\mathrm{life}}=\text{temps jusqu’à }B_t\leq B_{\min}
\]

## 19.2. Énergie moyenne

\[
\overline E_{\mathrm{msg}}=
\frac{\text{énergie totale débitée}}{\text{messages légitimes produits}}
\]

Une seconde métrique peut utiliser les messages servis.

## 19.3. FAR empirique

\[
\widehat{FAR}=\frac{N_{FA}}{N_M}
\]

## 19.4. FAR critique

\[
\widehat{FAR}_C=\frac{N_{FA,C}}{N_{M,C}}
\]

## 19.5. Refus légitime

\[
R_{\mathrm{ref}}=\frac{N_{\mathrm{ref}}}{N_{\mathrm{legit}}}
\]

## 19.6. Violations

\[
R_{\mathrm{viol}}=\frac{N_{\mathrm{viol}}}{N_{\mathrm{decisions}}}
\]

## 19.7. Répartition des décisions

\[
p(D)=\frac{N_D}{N_{\mathrm{decisions}}}
\]

## 19.8. Métriques complémentaires

```text
nombre moyen d’admissibles
nombre moyen de points Pareto
motifs de rejet
nombre de renouvellements
part K1a/K1b/K2
âge moyen au renouvellement
```

---

# 20. Étape 10 — Monte Carlo

Pour chaque scénario et graine :

```text
générer une trace commune
exécuter P0, B1, B2, B3 et B4
```

Pour comparer P0 à une politique \(B_j\), utiliser une différence appariée :

\[
\Delta_r=Y_r(P0)-Y_r(B_j)
\]

Le nombre \(N_{\mathrm{MC}}\) est augmenté jusqu’au critère de précision.

---

# 21. Intervalles de confiance

Pour une moyenne :

\[
\bar Y=\frac1N\sum_{r=1}^N Y_r
\]

\[
SE=\frac{s_Y}{\sqrt N}
\]

Employer la loi de Student lorsque ses hypothèses sont raisonnables.

Pour les proportions rares :

```text
Wilson
Clopper–Pearson
bootstrap
```

La méthode doit être enregistrée.

Augmenter \(N_{\mathrm{MC}}\) jusqu’à ce que la demi-largeur de l’IC à 95 % soit inférieure à la tolérance fixée avant l’analyse finale.

Les missions arrêtées par une durée maximale avant épuisement de la batterie sont censurées et doivent être signalées.

---

# 22. Étape 11 — Analyse de sensibilité

Balayer au minimum :

\[
\mu_\Gamma,
\sigma_{sh},
f_d,
d_M,
\kappa_{gb},
q_{trig},
p_C,
p_M,
T_{msg},
C_B,
\Delta\Gamma,
w_k
\]

Ajouter selon les besoins :

```text
rho_HW
KDR_max
eta_keep
minimum_deadline_s
security_strength_bits
```

Séparer clairement :

```text
incertitude physique
choix de scénario
choix de politique
```

---

# 23. Campagnes officielles

```text
CAMP-01 : validation scientifique
CAMP-02 : canal et authentification
CAMP-03 : coûts
CAMP-04 : contextes du DM
CAMP-05 : mission nominale
CAMP-06 : sensibilité radio
CAMP-07 : sensibilité mission
CAMP-08 : sensibilité politique
CAMP-09 : robustesse à l’estimation
```

---

# 24. Fichiers de sortie

## 24.1. `decision_steps.csv`

```text
campaign_id
scenario_id
policy_id
seed
step_index
time_s
snr_real_db
snr_observed_db
doppler_hz
reciprocity
kdr
battery_before_j
battery_after_j
key_age_s
messages_with_key
criticality
renewal_required
selected_decision
admissible_count
pareto_count
refusal
energy_debited_j
constraint_far
total_false_acceptance_probability
authentication_robustness
key_quality
normalized_latency
```

## 24.2. `decision_evaluations.csv`

```text
campaign_id
scenario_id
policy_id
seed
step_index
decision
reasoning_valid
admissible
rejection_reasons
total_energy_j
expected_energy_j
worst_case_energy_j
auth_latency_s
prudent_auth_latency_s
key_latency_s
airtime_s
constraint_far
authentication_robustness
key_quality
objective_vector
pareto_optimal
tchebycheff_score
```

## 24.3. `mission_summary.csv`

```text
campaign_id
scenario_id
policy_id
seed
lifetime_s
lifetime_days
lifetime_years
legitimate_messages
served_messages
refused_messages
mean_energy_per_generated_message_j
mean_energy_per_served_message_j
mallory_attempts
false_acceptances
empirical_far
critical_far
security_floor_violations
violation_rate
renewal_count
decision_counts
stop_reason
censored
```

---

# 25. Figures obligatoires

```text
FIG-01 : rho_noise selon SNR
FIG-02 : rho_AB selon SNR et Doppler
FIG-03 : KDR selon rho_AB
FIG-04 : FAR selon SNR
FIG-05 : FAR selon d_M
FIG-06 : FAR et FRR selon theta
FIG-07 : ROC/EER
FIG-08 : N_meas selon KDR
FIG-09 : Time-on-Air selon payload
FIG-10 : énergie des actions
FIG-11 : latence des actions
FIG-12 : front de Pareto
FIG-13 : score Tchebychev
FIG-14 : carte SNR–batterie
FIG-15 : carte SNR–âge de clé
FIG-16 : motifs de rejet
FIG-17 : batterie selon le temps
FIG-18 : autonomie par politique
FIG-19 : énergie moyenne
FIG-20 : FAR empirique
FIG-21 : taux de refus
FIG-22 : répartition des décisions
FIG-23 : compromis autonomie–sécurité
FIG-24 : violations au SNR réel
```

---

# 26. Tableaux obligatoires

```text
TAB-01 : paramètres nominaux et statuts
TAB-02 : paramètres à valider
TAB-03 : tests de reproduction
TAB-04 : coûts des actions
TAB-05 : contextes contrôlés du DM
TAB-06 : performances nominales
TAB-07 : comparaisons appariées
TAB-08 : sensibilité
TAB-09 : motifs de rejet
TAB-10 : limites d’interprétation
```

---

# 27. Contrôles automatiques de cohérence

À la fin de chaque mission :

```text
batterie jamais augmentée sans événement prévu
batterie jamais négative
énergie Mallory débitée à Alice = 0
N_FA <= N_M
N_FA,C <= N_M,C
refus <= messages légitimes
décision sélectionnée admissible
décision sélectionnée sur Pareto
poids de somme 1
compteurs cohérents
```

Toute violation invalide la mission.

---

# 28. Critères de réussite scientifique

Le système est correctement simulé si :

1. les cas tests sont reproduits ;
2. les monotonies attendues sont vérifiées ;
3. aucune décision rejetée n’est sélectionnée ;
4. la décision finale appartient au front ;
5. le bris d’égalité est reproductible ;
6. Mallory ne débite jamais Alice ;
7. les politiques utilisent les mêmes traces ;
8. l’incertitude est affichée ;
9. les paramètres exploratoires sont visibles ;
10. les conclusions restent dans le domaine du modèle.

---

# 29. Interdictions

Il est interdit de :

```text
modifier une équation pour améliorer les résultats
utiliser des graines différentes entre politiques
retirer les missions défavorables
annoncer une moyenne sans dispersion
annoncer FAR = 0 lorsque N_M = 0
compter Mallory dans l’énergie d’Alice
comparer des politiques avec des coûts différents
masquer les paramètres exploratoires
utiliser KDR_Eve en ligne
présenter phi_agree comme preuve d’entropie
présenter 0,019 J comme coût complet de K2
présenter 1,84 ms comme temps universel RFF
choisir les poids après observation des résultats
arrêter Monte Carlo lorsque le résultat devient favorable
```

---

# 30. Pseudocode de campagne

```text
fonction run_campaign(config):

    charger et valider les paramètres
    créer le manifeste
    exécuter les tests obligatoires

    pour chaque scénario:
        créer la liste des graines communes

        pour chaque graine:
            générer ou charger la trace commune

            pour chaque politique:
                exécuter la mission
                enregistrer les résultats bruts
                vérifier les invariants

        agréger les métriques
        calculer les intervalles de confiance
        comparer les politiques de manière appariée

    produire figures et tableaux
    finaliser le manifeste
    retourner CampaignResult
```

---

# 31. Livrables de la phase simulation

```text
configurations de campagne
tests automatisés
traces communes
résultats bruts
résultats agrégés
manifestes
figures
 tableaux
rapport de sensibilité
rapport des limites
```

---

# 32. Prochaine étape documentaire

Le prochain document est :

```text
docs/07_VALIDATION_PROTOCOL.md
```

Il définira :

- les niveaux de preuve ;
- les tolérances ;
- les critères d’acceptation ;
- la validation analytique ;
- la validation numérique ;
- la validation statistique ;
- la validation croisée avec la littérature ;
- la traçabilité équation–test–résultat.