# Référentiel scientifique des équations de PHYSEC-DM

## 1. Objet du document

Ce document relie :

```text
équations de la modélisation
→ statut scientifique
→ variables
→ fonction Python
→ tests
```

La source de vérité est :

```text
modelisation_parametres_modifies(1).tex
modelisation parametre modifié.pdf
```

Les identifiants utilisent le numéro de l’équation du modèle afin d’éviter toute renumérotation ambiguë :

```text
CH-EQ05
AU-EQ23
KM-EQ44
CO-EQ68
DM-EQ93
```

---

## 2. Statuts scientifiques

| Statut | Définition |
|---|---|
| LITTÉRATURE | relation reprise d’une source identifiée |
| DATASHEET | relation ou valeur issue d’une fiche technique |
| DÉRIVÉ | relation explicitement dérivée |
| CALIBRÉ | relation ou paramètre ajusté |
| SCÉNARIO | choix d’expérience |
| POLITIQUE | règle du Decision Maker |
| À VALIDER | validation insuffisante |

---

## 3. Conventions

### 3.1. SNR

\[
\gamma_t=\frac{P_{s,t}}{P_n}
\]

\[
\Gamma_t=10\log_{10}(\gamma_t)
\]

```text
gamma_t : domaine linéaire
Gamma_t : décibels
```

### 3.2. Énergie

```text
joule
```

### 3.3. Temps

```text
seconde
```

### 3.4. Probabilités

```text
valeurs décimales dans [0,1]
```

### 3.5. Corrélation

```text
rho_AB,t appartient à [-1,1]
```

La corrélation signée est conservée dans le modèle nominal.

---

# 4. Registre général de traçabilité

## 4.1. Décision et objectifs

| ID | Équation | Statut | Module |
|---|---|---|---|
| GEN-EQ01 | \(D_t^\star=(A_j,K_i)\) | politique/formulation | `decision_maker.py` |
| GEN-EQ02 | quatre objectifs | formulation scientifique | `decision_maker.py` |
| GEN-EQ04 | \(\mathcal D=\{A_1,A_2\}\times\{K_0,K_{1a},K_{1b},K_2\}\) | définition | `decision_maker.py` |

## 4.2. Canal radio

| ID | Objet | Statut | Fonction |
|---|---|---|---|
| CH-EQ05 | SNR linéaire | définition physique | `compute_snr_linear()` |
| CH-EQ06 | conversions SNR | définition physique | `snr_db_to_linear()`, `snr_linear_to_db()` |
| CH-EQ07 | SNR moyen imposé | scénario | `generate_imposed_snr_db()` |
| CH-EQ08 | shadowing gaussien en dB | scénario/littérature | `sample_shadowing_db()` |
| CH-EQ09 | perte log-distance | littérature | `compute_path_loss_db()` |
| CH-EQ10 | bilan de liaison complet | dérivé | `compute_received_power_dbm()` |
| CH-EQ11 | bilan réduit | dérivé | option de `compute_received_power_dbm()` |
| CH-EQ12 | bruit dans la bande | dérivé de \(kTB\) | `compute_noise_power_dbm()` |
| CH-EQ13 | SNR reçu en dB | définition dérivée | `compute_snr_db()` |
| CH-EQ14 | observation d’Alice | modèle adapté | structure de simulation |
| CH-EQ15 | observation de Bob | modèle adapté | structure de simulation |
| CH-EQ16 | corrélation observée | littérature/mesure | `compute_empirical_correlation()` |
| CH-EQ17 | corrélation Clarke–Jakes | littérature | `compute_temporal_correlation()` |
| CH-EQ18 | Doppler | définition physique | `compute_doppler_hz()` |
| CH-EQ19 | facteur de bruit | dérivé | `compute_noise_correlation_factor()` |
| CH-EQ20 | dérivation par variances | dérivé | documentation/test |
| CH-EQ21 | réciprocité composite | construction de l’étude | `compute_reciprocity()` |
| CH-EQ22 | variante tronquée | choix algorithmique | `compute_truncated_reciprocity()` |

## 4.3. Authentification

| ID | Objet | Statut | Fonction |
|---|---|---|---|
| AU-EQ23 | vecteur CFO–DCO–PO | adaptation/littérature | `build_rff_vector()` |
| AU-EQ24 | observation gaussienne | choix de modélisation | `sample_rff_observation()` |
| AU-EQ25 | référence d’enrôlement | estimation standard | `estimate_rff_reference()` |
| AU-EQ26 | Mahalanobis | adaptation/littérature | `compute_mahalanobis_statistic()` |
| AU-EQ27 | test binaire RFF | politique | `apply_rff_test()` |
| AU-EQ28 | cas isotrope | cas particulier dérivé | `compute_isotropic_statistic()` |
| AU-EQ29 | loi sous Alice | littérature adaptée | documentation/scipy |
| AU-EQ30 | loi sous Mallory | littérature adaptée | documentation/scipy |
| AU-EQ31 | non-centralité générale | littérature adaptée | `compute_noncentrality()` |
| AU-EQ32 | FRR | dérivé de la CDF | `compute_frr()` |
| AU-EQ33 | FAR | dérivé de la CDF | `compute_far()` |
| AU-EQ34 | variance RFF liée au SNR | hypothèse analytique | `compute_rff_noise_variance()` |
| AU-EQ35 | séparation normalisée | définition de scénario | `compute_normalized_separation()` |
| AU-EQ36 | \(\lambda=d_M^2\gamma\) | dérivé | `compute_noncentrality_from_snr()` |
| AU-EQ37 | seuil de FRR cible | dérivé | `compute_rff_threshold()` |
| AU-EQ38 | forge MAC | borne idéalisée | `compute_mac_forgery_probability()` |
| AU-EQ39 | robustesse A1 | dérivé | `compute_a1_robustness()` |
| AU-EQ40 | usurpation totale A2 | dérivé | `compute_a2_false_acceptance()` |
| AU-EQ41 | robustesse A2 | dérivé | `compute_a2_robustness()` |
| AU-EQ42 | repli Alice | dérivé | `compute_alice_fallback_probability()` |
| AU-EQ43 | repli Mallory | dérivé | `compute_mallory_fallback_probability()` |

## 4.4. Génération et gestion de clé

| ID | Objet | Statut | Fonction |
|---|---|---|---|
| KM-EQ44 | KDR par arc-sinus | littérature | `compute_raw_kdr()` |
| KM-EQ45 | seuil KDR max | politique | paramètre |
| KM-EQ46 | seuil \(\rho_{\min}\) | dérivé/politique | `derive_minimum_correlation()` |
| KM-EQ47 | mode KDR analytique | mode de modèle | `compute_effective_kdr()` |
| KM-EQ48 | mode KDR calibré | calibré | `compute_calibrated_kdr()` |
| KM-EQ49 | entropie binaire | définition | `binary_entropy()` |
| KM-EQ50 | rendement en ligne | dérivé/calibré | `compute_reconciliation_yield()` |
| KM-EQ51 | nombre de mesures | dérivé | `compute_required_measurements()` |
| KM-EQ52–54 | reproduction Ruotsalainen | littérature hors ligne | fonctions de validation |
| KM-EQ55 | faisabilité d’accord | politique | `check_agreement_feasibility()` |
| KM-EQ56 | faisabilité PHY | formulation réservée | `check_phy_feasibility()` |
| KM-EQ57–59 | vieillissement de clé | politique | `compute_key_aging_index()` |
| KM-EQ60 | renouvellement anticipé | politique | `is_renewal_triggered()` |
| KM-EQ61 | expiration dure | politique | `is_key_expired()` |
| KM-EQ62–64 | échéance | dérivé/politique | `compute_key_deadline_s()` |
| KM-EQ65 | qualité K0 | indice proposé | `compute_k0_quality()` |
| KM-EQ66 | qualité K1a/K1b | indice proposé | `compute_phy_key_quality()` |
| KM-EQ67 | qualité K2 | indice proposé | `compute_k2_quality()` |

## 4.5. Énergie et latence

| ID | Objet | Statut | Fonction |
|---|---|---|---|
| CO-EQ68–72 | Time-on-Air LoRa | datasheet/littérature | `compute_lora_airtime_s()` |
| CO-EQ73 | énergie TX | dérivé de \(E=VIT\) | `compute_tx_energy_j()` |
| CO-EQ74 | énergie RX | dérivé de \(E=VIT\) | `compute_rx_energy_j()` |
| CO-EQ75 | énergie CPU | dérivé | `compute_cpu_energy_j()` |
| CO-EQ76–77 | énergie totale et base | bilan du scénario | `compute_total_energy_j()` |
| CO-EQ78–79 | coût A1 | bilan différentiel | `compute_a1_cost()` |
| CO-EQ80–82 | coût A2 | dérivé/espérance | `compute_a2_cost()` |
| CO-EQ83 | K0 | définition | `compute_k0_cost()` |
| CO-EQ84–85 | réconciliation + PA | bilan dérivé | `compute_reconciliation_cost()` |
| CO-EQ86–88 | K1b | bilan dérivé | `compute_k1b_cost()` |
| CO-EQ89–90 | K1a | bilan dérivé | `compute_k1a_cost()` |
| CO-EQ91 | K2 | somme d’opérations | `compute_k2_cost()` |
| CO-EQ92 | latence normalisée | politique | `compute_normalized_latency()` |

## 4.6. Decision Maker

| ID | Objet | Statut | Fonction |
|---|---|---|---|
| DM-EQ93 | vecteur objectif | formulation | `build_objective_vector()` |
| DM-EQ94–96 | règles de raisonnement | politique logique | `check_reasoning_rules()` |
| DM-EQ97 | faisabilité PHY des K1 | contrainte | `check_phy_constraint()` |
| DM-EQ98 | batterie | contrainte | `check_battery_constraint()` |
| DM-EQ99 | délai auth | contrainte | `check_auth_latency_constraint()` |
| DM-EQ100 | échéance clé | contrainte | `check_key_deadline_constraint()` |
| DM-EQ101 | duty-cycle | contrainte | `check_duty_cycle_constraint()` |
| DM-EQ102 | plancher FAR | politique de sécurité | `check_far_floor()` |
| DM-EQ103 | ensemble admissible | définition | `build_admissible_set()` |
| DM-EQ104 | dominance | Pareto | `dominates()` |
| DM-EQ105 | front exact | Pareto | `compute_pareto_front()` |
| DM-EQ106 | Tchebychev | optimisation | `compute_tchebycheff_score()` |
| DM-EQ107–110 | poids et monotonies | politique à valider | `compute_contextual_weights()` |

---

# 5. Fiches détaillées du canal radio

## CH-EQ05 — SNR linéaire

### Expression

\[
\gamma_t=\frac{P_{s,t}}{P_n}
\]

### Nature

```text
définition physique
```

### Conditions

- \(P_{s,t}\geq0\) ;
- \(P_n>0\) ;
- les deux puissances sont exprimées dans la même unité linéaire.

### Fonction

```python
compute_snr_linear(signal_power_w, noise_power_w)
```

### Tests

- rapport égal à 1 ;
- signal nul ;
- bruit nul rejeté ;
- cohérence avec CH-EQ06.

---

## CH-EQ06 — Conversion du SNR

### Expressions

\[
\Gamma_t=10\log_{10}(\gamma_t)
\]

\[
\gamma_t=10^{\Gamma_t/10}
\]

### Fonctions

```python
snr_linear_to_db()
snr_db_to_linear()
```

### Invariant

```text
0 dB correspond à gamma = 1
```

---

## CH-EQ07 et CH-EQ08 — SNR moyen imposé

### Expressions

\[
\Gamma_t=\mu_\Gamma+X_{\mathrm{sh},t}
\]

\[
X_{\mathrm{sh},t}\sim\mathcal N(0,\sigma_{\mathrm{sh}}^2)
\]

### Nature

```text
forme en dB du shadowing log-normal
paramètres de scénario
```

### Fonction

```python
generate_imposed_snr_db(mean_snr_db, shadowing_std_db, rng)
```

### Règle

Ce mode ne doit pas être utilisé simultanément avec le mode distance dans une même expérience.

---

## CH-EQ09 — Perte log-distance

### Expression

\[
PL(d)
=
PL(d_0)
+
10n_p\log_{10}\left(\frac d{d_0}\right)
\]

### Nature

```text
littérature
```

### Conditions

\[
d\geq d_0>0,\qquad n_p>0
\]

### Fonction

```python
compute_path_loss_db(
    distance_m,
    reference_distance_m,
    reference_path_loss_db,
    path_loss_exponent
)
```

---

## CH-EQ10 et CH-EQ11 — Bilan de liaison

### Forme complète

\[
P_{\mathrm{rx},t}
=
P_{\mathrm{tx}}
+
G_{\mathrm{tx}}
+
G_{\mathrm{rx}}
-
PL(d)
-
L_{\mathrm{sys}}
+
X_{\mathrm{sh},t}
\]

### Forme réduite

\[
P_{\mathrm{rx},t}
=
P_{\mathrm{tx}}
-
PL(d)
+
X_{\mathrm{sh},t}
\]

### Nature

```text
bilan dérivé
```

La forme réduite n’est utilisée que si les gains et pertes sont déjà absorbés dans la référence.

### Fonction

```python
compute_received_power_dbm(...)
```

---

## CH-EQ12 — Bruit thermique dans la bande

### Expression

\[
P_N
=
-174
+
10\log_{10}(BW)
+
NF
\]

avec :

```text
P_N : dBm
BW  : Hz
NF  : dB
```

### Nature

```text
dérivé de kTB et de la figure de bruit
```

### Fonction

```python
compute_noise_power_dbm(bandwidth_hz, noise_figure_db)
```

### Tests

Pour \(BW=125\,000\) Hz et \(NF=6\) dB, vérifier un résultat voisin de \(-117\) dBm.

---

## CH-EQ13 — SNR reçu en dB

\[
\Gamma_t
=
P_{\mathrm{rx},t}
-
P_N
\]

### Fonction

```python
compute_snr_db(received_power_dbm, noise_power_dbm)
```

---

## CH-EQ14 et CH-EQ15 — Observations bruitées

\[
z_{A,t}=h(t)+n_{A,t}
\]

\[
z_{B,t}=h(t+\Delta t)+n_{B,t}
\]

### Nature

```text
modèle d’observation classique adapté au sondage semi-duplex LoRa
```

Ces équations décrivent le modèle statistique. Elles ne doivent pas obligatoirement correspondre à une fonction publique si la simulation travaille directement avec les métriques analytiques.

---

## CH-EQ16 — Corrélation empirique

\[
\rho_{AB,t}
=
\frac{
\mathbb E[(z_{A,t}-\mu_A)(z_{B,t}-\mu_B)^*]
}{
\sigma_A\sigma_B
}
\]

### Fonction de validation

```python
compute_empirical_correlation(alice_samples, bob_samples)
```

Cette fonction sert notamment à comparer le modèle analytique à des traces.

---

## CH-EQ17 — Corrélation Clarke–Jakes

\[
\rho_{\mathrm{time},t}
=
J_0(2\pi f_{d,t}\Delta t)
\]

### Nature

```text
littérature
```

### Fonction

```python
compute_temporal_correlation(doppler_hz, probe_delay_s)
```

### Règle

La sortie peut être négative.

---

## CH-EQ18 — Doppler

\[
f_{d,t}=\frac{v_tf_c}{c}
\]

### Fonction

```python
compute_doppler_hz(
    effective_speed_m_s,
    carrier_frequency_hz
)
```

### Cas de base

```text
fd = 0 Hz
```

Le balayage recommandé correspond à une vitesse effective de 0 à 1 m/s en EU868.

---

## CH-EQ19 et CH-EQ20 — Dégradation par le bruit

### Définition

\[
\gamma_t
=
\frac{\sigma_h^2}{\sigma_n^2}
\]

### Facteur

\[
\rho_{\mathrm{noise},t}
=
\frac{\gamma_t}{1+\gamma_t}
\]

### Nature

```text
dérivé dans cette étude
```

### Fonction

```python
compute_noise_correlation_factor(snr_linear)
```

### Propriétés

\[
\gamma=0\Rightarrow\rho_{\mathrm{noise}}=0
\]

\[
\gamma\to+\infty\Rightarrow\rho_{\mathrm{noise}}\to1
\]

---

## CH-EQ21 — Réciprocité composite

### Expression officielle

\[
\rho_{AB,t}
=
\rho_{\mathrm{HW}}
J_0(2\pi f_{d,t}\Delta t)
\frac{\gamma_t}{1+\gamma_t}
\]

ou :

\[
\rho_{AB,t}
=
\rho_{\mathrm{HW}}
\rho_{\mathrm{time},t}
\rho_{\mathrm{noise},t}
\]

### Nature des composantes

| Composante | Nature |
|---|---|
| \(J_0(2\pi f_d\Delta t)\) | littérature |
| \(\gamma/(1+\gamma)\) | dérivé |
| \(\rho_{\mathrm{HW}}\) | calibré |
| produit complet | construction de l’étude |

### Fonction

```python
compute_reciprocity(
    hardware_reciprocity,
    temporal_correlation,
    noise_correlation
)
```

### Domaine

\[
-1\leq\rho_{AB,t}\leq1
\]

### Règle fondamentale

La fonction nominale ne doit appliquer ni valeur absolue ni troncature.

---

## CH-EQ22 — Variante tronquée

\[
\rho_{AB,t}^{+}
=
\max\{0,\rho_{AB,t}\}
\]

### Nature

```text
choix algorithmique explicite
```

### Fonction

```python
compute_truncated_reciprocity(reciprocity)
```

### Règle

Cette fonction est réservée à une analyse de sensibilité et doit être activée par un paramètre de scénario.

---

# 6. Chaîne officielle du canal

```text
MODE A
mean_snr_db + shadowing
        ↓
Gamma_t
        ↓
gamma_t
```

```text
MODE B
distance
    ↓
PL(d)
    ↓
P_rx,t
    +
P_N
    ↓
Gamma_t
    ↓
gamma_t
```

Puis, dans les deux modes :

```text
vitesse effective + fréquence porteuse
        ↓
f_d,t
        ↓
rho_time,t
```

```text
gamma_t
        ↓
rho_noise,t
```

```text
rho_HW × rho_time,t × rho_noise,t
        ↓
rho_AB,t
```

---

# 7. Paramètres nominaux du canal

| Paramètre | Valeur de départ | Statut |
|---|---:|---|
| \(f_c\) | 868 MHz | littérature/scénario |
| \(BW\) | 125 kHz | littérature |
| \(NF\) | 6 dB | littérature |
| \(\Delta t\) | 1 s | littérature/scénario |
| \(f_d\) nominal | 0 Hz | scénario |
| plage \(f_d\) | 0 à 2,89 Hz | dérivé/scénario |
| \(\rho_{\mathrm{HW}}\) | 0,9582 | calibré |
| \(\sigma_{\mathrm{sh}}\) | 3 dB | scénario |

---

# 8. Tests officiels du canal

Le module `validation.py` doit vérifier :

1. conversion dB/linéaire ;
2. perte log-distance ;
3. bilan de liaison ;
4. bruit thermique ;
5. SNR obtenu ;
6. \(J_0(0)=1\) ;
7. fréquence Doppler nulle pour vitesse nulle ;
8. monotonie de \(\gamma/(1+\gamma)\) ;
9. conservation des corrélations négatives ;
10. bornes de \(\rho_{AB,t}\) ;
11. différence entre modèle nominal et variante tronquée ;
12. cohérence avec des traces ou valeurs de littérature lorsque disponibles.

---

# 9. Interdictions de traçabilité

Il est interdit de :

- présenter CH-EQ21 comme une formule intégrale de Jakes ;
- présenter \(\rho_{\mathrm{HW}}\) comme une constante universelle ;
- appliquer \(|\rho_{AB}|\) ;
- utiliser le SNR en dB dans CH-EQ19 ;
- appeler \(Q_t^{\mathrm{key}}\) une probabilité absolue de sécurité ;
- confondre faisabilité d’accord et entropie du canal ;
- utiliser simultanément le mode SNR imposé et le mode distance.

---

---

# 10. Fiches détaillées de l’authentification physique

## 10.1. Architecture scientifique de l’action A2

L’action \(A_2\) combine deux niveaux :

```text
1. Bob extrait l’empreinte radio et applique le test RFF.
2. Si l’empreinte est acceptée, aucun repli n’est déclenché.
3. Si l’empreinte est rejetée, Bob déclenche un défi–réponse cryptographique.
```

L’architecture hybride est motivée par la littérature cross-layer. Le modèle analytique en lois \(\chi^2\) et \(\chi'^2\), en revanche, est celui adopté dans cette étude.

La séparation des responsabilités est :

```text
RFF :
    exécutée chez Bob

Défi–réponse :
    exécuté seulement après rejet de l’empreinte

Énergie optimisée :
    celle d’Alice uniquement
```

---

## AU-EQ23 — Vecteur d’empreinte RFF CFO–DCO–PO

### Expression officielle

\[
\mathbf f_X
=
\begin{bmatrix}
\mathrm{CFO}_X &
\mathrm{DCO}_X &
\mathrm{PO}_X
\end{bmatrix}^{T},
\qquad
n_f=3
\]

avec :

\[
X\in\{A,M\}
\]

où :

- \(A\) représente Alice ;
- \(M\) représente Mallory ;
- \(\mathrm{CFO}\) est le `Carrier Frequency Offset` ;
- \(\mathrm{DCO}\) est le `DC Offset` ;
- \(\mathrm{PO}\) est le `Phase Offset` ;
- \(n_f\) est le nombre de composantes de l’empreinte.

### Nature scientifique

```text
Attributs inspirés de la littérature.
Choix de trois attributs retenu dans le modèle.
Application analytique ultérieure : adaptation statistique de cette étude.
```

La valeur :

\[
n_f=3
\]

vient exactement du nombre d’attributs retenus. Elle n’est pas une constante universelle de l’authentification RFF.

### Point d’attention sur les unités

Les trois attributs peuvent avoir des unités et des échelles différentes. Ils ne doivent donc pas être combinés par une distance euclidienne brute sans normalisation.

La covariance \(\boldsymbol\Sigma_w\) du test de Mahalanobis prend en compte ces différences d’échelle.

### Entrées

```text
cfo
dco
phase_offset
```

### Sortie

```text
rff_feature_vector
```

### Module

```text
authentication.py
```

### Fonction

```python
build_rff_vector(
    cfo,
    dco,
    phase_offset
) -> array
```

### Tests

- la sortie contient exactement trois composantes ;
- l’ordre est strictement `CFO`, `DCO`, `PO` ;
- toutes les composantes sont finies ;
- aucune normalisation arbitraire n’est appliquée dans cette fonction.

---

## AU-EQ24 — Observation gaussienne de l’empreinte

### Expression officielle

\[
\mathbf f_{\mathrm{obs},t}
=
\mathbf f_X
+
\mathbf w_t
\]

avec :

\[
\mathbf w_t
\sim
\mathcal N
\left(
\mathbf 0,
\boldsymbol\Sigma_w
\right)
\]

### Signification

Bob ne mesure pas directement l’empreinte moyenne idéale de l’émetteur. Il observe une version perturbée par une erreur aléatoire.

```text
f_X :
    moyenne de l’empreinte de l’émetteur X

w_t :
    erreur d’extraction ou de mesure

Sigma_w :
    covariance de l’erreur

f_obs,t :
    empreinte observée par Bob
```

### Nature scientifique

```text
Choix de modélisation gaussien.
```

Cette hypothèse permet d’obtenir des expressions analytiques de FAR et de FRR. Elle doit être vérifiée sur des données RFF avant toute validation expérimentale définitive.

### Hypothèses

- erreur centrée ;
- covariance finie ;
- covariance symétrique ;
- covariance définie positive pour le test nominal ;
- stationnarité locale de la distribution ;
- profil moyen de l’émetteur stable sur l’intervalle étudié.

### Entrées

```text
mean_feature_vector
error_covariance
random_generator
```

### Sortie

```text
observed_feature_vector
```

### Fonction

```python
sample_rff_observation(
    mean_feature_vector,
    error_covariance,
    rng
) -> array
```

### Tests

- moyenne empirique proche de \(\mathbf f_X\) sur un grand échantillon ;
- covariance empirique proche de \(\boldsymbol\Sigma_w\) ;
- rejet d’une covariance de mauvaise dimension ;
- rejet d’une covariance non finie ;
- reproductibilité avec une graine fixée.

---

## AU-EQ25 — Référence d’enrôlement d’Alice

### Expression officielle

\[
\mathbf f_{A,\mathrm{ref}}
=
\frac{1}{N_{\mathrm{enr}}}
\sum_{i=1}^{N_{\mathrm{enr}}}
\mathbf f_{A,i}
\]

### Signification

Bob construit le profil de référence d’Alice à partir de \(N_{\mathrm{enr}}\) observations d’enrôlement.

### Nature scientifique

```text
Moyenne empirique standard.
```

Le modèle ne fixe pas encore une valeur numérique universelle de :

\[
N_{\mathrm{enr}}
\]

Cette valeur doit être définie par le protocole d’enrôlement, puis analysée en sensibilité.

### Entrée

```text
alice_enrollment_samples
```

Dimension attendue :

```text
N_enr × n_f
```

### Sortie

```text
alice_reference_vector
```

### Fonction

```python
estimate_rff_reference(
    alice_enrollment_samples
) -> array
```

### Conditions

\[
N_{\mathrm{enr}}\geq1
\]

Toutes les observations doivent avoir la même dimension \(n_f\).

### Tests

- une seule observation retourne cette observation ;
- plusieurs observations identiques retournent leur valeur commune ;
- comparaison avec une moyenne calculée manuellement ;
- rejet d’un ensemble vide ;
- rejet de dimensions incohérentes.

---

## AU-EQ26 — Statistique de Mahalanobis

### Expression officielle

\[
T_t
=
\left(
\mathbf f_{\mathrm{obs},t}
-
\mathbf f_{A,\mathrm{ref}}
\right)^T
\boldsymbol\Sigma_w^{-1}
\left(
\mathbf f_{\mathrm{obs},t}
-
\mathbf f_{A,\mathrm{ref}}
\right)
\]

### Objectif

La statistique mesure la distance entre l’empreinte observée et la référence d’Alice en tenant compte :

- de la variance de chaque attribut ;
- des corrélations entre les attributs ;
- des différentes échelles de CFO, DCO et PO.

### Nature scientifique

```text
Discriminant quadratique de type Mahalanobis adapté au vecteur RFF réel.
```

### Domaine

Sous une covariance valide :

\[
T_t\geq0
\]

### Entrées

```text
observed_feature_vector
alice_reference_vector
error_covariance
```

### Sortie

```text
rff_statistic
```

### Fonction

```python
compute_mahalanobis_statistic(
    observed_feature_vector,
    alice_reference_vector,
    error_covariance
) -> float
```

### Règle numérique

L’implémentation doit résoudre un système linéaire plutôt que calculer explicitement une matrice inverse lorsque cela est possible.

Conceptuellement :

```text
difference = observed - reference
solution = solve(covariance, difference)
statistic = difference.T @ solution
```

### Tests

- observation égale à la référence : \(T_t=0\) ;
- statistique toujours non négative à la tolérance numérique ;
- invariance à un changement d’échelle cohérent avec la covariance ;
- comparaison avec un calcul manuel en dimension réduite ;
- rejet d’une covariance singulière dans le chemin nominal ;
- rejet de dimensions incompatibles.

---

## AU-EQ27 — Test binaire RFF

### Règle officielle

\[
\begin{cases}
T_t\leq\theta,
&
\text{empreinte acceptée comme Alice},
\\[2mm]
T_t>\theta,
&
\text{empreinte rejetée et repli déclenché}.
\end{cases}
\]

### Interprétation du seuil

Un seuil plus faible :

- réduit généralement l’acceptation de Mallory ;
- augmente le risque de rejeter Alice.

Un seuil plus élevé :

- réduit le faux rejet d’Alice ;
- augmente le risque d’accepter Mallory.

### Entrées

```text
rff_statistic
rff_threshold
```

### Sorties

```text
accepted_as_alice
fallback_triggered
```

### Fonction

```python
apply_rff_test(
    rff_statistic,
    rff_threshold
) -> bool
```

Convention :

```text
True  : empreinte acceptée comme Alice
False : empreinte rejetée
```

### Cas frontière

Le modèle impose :

\[
T_t=\theta
\Rightarrow
\text{acceptation}
\]

### Tests

- \(T_t<\theta\) : acceptation ;
- \(T_t=\theta\) : acceptation ;
- \(T_t>\theta\) : rejet ;
- seuil négatif rejeté ;
- valeurs non finies rejetées.

---

## AU-EQ28 — Cas isotrope de Mahalanobis

### Hypothèse

\[
\boldsymbol\Sigma_w
=
\sigma_w^2\mathbf I_{n_f}
\]

### Expression

\[
T_t
=
\frac{
\left\|
\mathbf f_{\mathrm{obs},t}
-
\mathbf f_{A,\mathrm{ref}}
\right\|_2^2
}{
\sigma_w^2
}
\]

### Nature scientifique

```text
Cas particulier de la statistique de Mahalanobis.
```

Ce n’est pas une nouvelle loi statistique.

### Entrées

```text
observed_feature_vector
alice_reference_vector
error_variance
```

### Fonction

```python
compute_isotropic_statistic(
    observed_feature_vector,
    alice_reference_vector,
    error_variance
) -> float
```

### Condition

\[
\sigma_w^2>0
\]

### Test de cohérence

Pour une covariance isotrope, la fonction doit donner le même résultat que `compute_mahalanobis_statistic()`.

---

## AU-EQ29 — Distribution sous Alice

### Hypothèse

\[
\mathcal H_A :
\text{la trame provient d’Alice}
\]

### Distribution officielle

\[
T_t
\mid
\mathcal H_A
\sim
\chi^2_{n_f}
\]

### Nature scientifique

```text
Résultat de la statistique quadratique gaussienne,
appliqué ici au vecteur CFO–DCO–PO.
```

### Hypothèses nécessaires

- référence d’Alice correctement estimée ;
- covariance correctement estimée ;
- erreur gaussienne ;
- absence de dérive significative du profil ;
- même modèle statistique entre enrôlement et fonctionnement.

### Utilisation

Cette distribution fournit la FRR de l’équation AU-EQ32.

---

## AU-EQ30 — Distribution sous Mallory

### Hypothèse

\[
\mathcal H_M :
\text{la trame provient de Mallory}
\]

### Distribution officielle

\[
T_t
\mid
\mathcal H_M
\sim
\chi'^2_{n_f}
\left(
\lambda_{M,t}
\right)
\]

### Nature scientifique

```text
Loi chi-deux non centrale issue de la statistique quadratique
gaussienne, adaptée au vecteur RFF du modèle.
```

### Utilisation

Cette distribution fournit la FAR de l’équation AU-EQ33.

---

## AU-EQ31 — Paramètre de non-centralité général

### Expression officielle

\[
\lambda_{M,t}
=
\left(
\mathbf f_M
-
\mathbf f_{A,\mathrm{ref}}
\right)^T
\boldsymbol\Sigma_w^{-1}
\left(
\mathbf f_M
-
\mathbf f_{A,\mathrm{ref}}
\right)
\]

### Interprétation

\(\lambda_{M,t}\) mesure la séparabilité statistique entre le profil moyen de Mallory et la référence d’Alice.

```text
lambda faible :
    Mallory ressemble statistiquement à Alice

lambda élevée :
    Mallory est plus facilement distinguable
```

### Domaine

\[
\lambda_{M,t}\geq0
\]

### Fonction

```python
compute_noncentrality(
    mallory_feature_vector,
    alice_reference_vector,
    error_covariance
) -> float
```

### Tests

- profils identiques : \(\lambda=0\) ;
- augmentation de la distance : \(\lambda\) augmente ;
- cohérence avec Mahalanobis ;
- covariance invalide rejetée.

---

## AU-EQ32 — Taux de faux rejet

### Définition

La FRR est la probabilité de rejeter Alice alors que la trame provient réellement d’Alice.

### Expression officielle

\[
\mathrm{FRR}(\theta)
=
\Pr
\left[
T_t>\theta
\mid
\mathcal H_A
\right]
\]

\[
\boxed{
\mathrm{FRR}(\theta)
=
1
-
F_{\chi^2_{n_f}}(\theta)
}
\]

### Entrées

```text
rff_threshold
feature_count
```

### Sortie

```text
false_rejection_rate
```

### Fonction

```python
compute_frr(
    rff_threshold,
    feature_count
) -> float
```

### Calcul numérique recommandé

```text
chi2 survival function
```

afin d’éviter une perte de précision dans :

```text
1 - CDF
```

### Propriétés

\[
0\leq\mathrm{FRR}\leq1
\]

À \(n_f\) fixé, la FRR décroît lorsque \(\theta\) augmente.

### Point scientifique central

Dans le modèle analytiquement normalisé retenu, la FRR ne dépend pas explicitement du SNR.

Cette propriété n’est plus garantie lorsque :

- la covariance est mal estimée ;
- l’empreinte dérive ;
- la distribution n’est pas gaussienne ;
- le seuil ou la normalisation dépend du SNR.

---

## AU-EQ33 — Taux de fausse acceptation

### Définition

La FAR est la probabilité d’accepter Mallory comme Alice.

### Expression officielle

\[
\mathrm{FAR}
\left(
\theta,
\lambda_{M,t}
\right)
=
\Pr
\left[
T_t\leq\theta
\mid
\mathcal H_M
\right]
\]

\[
\boxed{
\mathrm{FAR}
\left(
\theta,
\lambda_{M,t}
\right)
=
F_{\chi'^2_{n_f}(\lambda_{M,t})}
(\theta)
}
\]

### Entrées

```text
rff_threshold
feature_count
noncentrality_parameter
```

### Sortie

```text
false_acceptance_rate
```

### Fonction

```python
compute_far(
    rff_threshold,
    feature_count,
    noncentrality_parameter
) -> float
```

### Propriétés attendues

À \(\theta\) et \(n_f\) fixés :

- la FAR diminue lorsque \(\lambda_{M,t}\) augmente ;
- la FAR augmente lorsque Mallory devient plus proche d’Alice ;
- la FAR augmente lorsque le seuil augmente.

### Cas limite

Si :

\[
\lambda_{M,t}=0
\]

les lois sous Alice et Mallory deviennent identiques. On obtient alors :

\[
\mathrm{FAR}
=
F_{\chi^2_{n_f}}(\theta)
=
1-\mathrm{FRR}(\theta)
\]

---

## AU-EQ34 — Variance RFF liée au SNR

### Expression officielle

\[
\sigma_w^2
\left(
\gamma_{M,t}
\right)
=
\frac{
\sigma_0^2
}{
\gamma_{M,t}
}
\]

### Nature scientifique

```text
Hypothèse analytique de première simulation.
```

Cette relation n’est pas attribuée à Alla, Haenel ou Forssell.

### Interprétation

Une augmentation du SNR de la trame de Mallory réduit la variance d’extraction supposée de son empreinte.

### Conditions

\[
\sigma_0^2>0
\]

\[
\gamma_{M,t}>0
\]

La limite \(\gamma_{M,t}=0\) doit être traitée numériquement sans division par zéro.

### Fonction

```python
compute_rff_noise_variance(
    reference_variance,
    mallory_snr_linear
) -> float
```

### Limite du modèle

La loi variance–SNR doit être validée expérimentalement. Elle peut devenir insuffisante lorsque :

- l’erreur possède un plancher indépendant du SNR ;
- l’extracteur est biaisé ;
- des non-linéarités dominent ;
- les attributs ont des variances différentes.

---

## AU-EQ35 — Séparation normalisée Alice–Mallory

### Expression officielle

\[
d_M^2
=
\frac{
\left\|
\mathbf f_M
-
\mathbf f_{A,\mathrm{ref}}
\right\|_2^2
}{
\sigma_0^2
}
\]

### Signification

\(d_M\) résume la séparation entre les empreintes de Mallory et d’Alice dans le modèle isotrope simplifié.

### Nature scientifique

```text
Définition de scénario normalisée.
Paramètre à calibrer ou à balayer.
```

### Domaine

\[
d_M\geq0
\]

### Paramètre nominal

```text
d_M = 2,0
```

### Analyse de sensibilité obligatoire

```text
d_M dans [0,5 ; 5]
```

Aucun auteur ne fournit une valeur universelle de \(d_M\) pour ce scénario.

### Fonction éventuelle

```python
compute_normalized_separation(
    mallory_feature_vector,
    alice_reference_vector,
    reference_variance
) -> float
```

Dans la simulation analytique principale, \(d_M\) peut être fourni directement comme paramètre de scénario.

---

## AU-EQ36 — Non-centralité liée au SNR

### Expression officielle

\[
\boxed{
\lambda_{M,t}
=
d_M^2
\gamma_{M,t}
}
\]

### Dérivation

La relation résulte de la combinaison de :

\[
\sigma_w^2
=
\frac{\sigma_0^2}{\gamma_{M,t}}
\]

et :

\[
d_M^2
=
\frac{
\left\|
\mathbf f_M
-
\mathbf f_{A,\mathrm{ref}}
\right\|_2^2
}{
\sigma_0^2
}
\]

### Nature scientifique

```text
Dérivée dans cette étude.
```

### Entrées

```text
mallory_separation
mallory_snr_linear
```

### Sortie

```text
noncentrality_parameter
```

### Fonction

```python
compute_noncentrality_from_snr(
    mallory_separation,
    mallory_snr_linear
) -> float
```

### Propriétés

Pour \(d_M>0\) :

- \(\lambda\) augmente avec le SNR ;
- \(\lambda\) augmente avec \(d_M\) ;
- une augmentation du SNR réduit normalement la FAR.

### Tests

- \(d_M=0\Rightarrow\lambda=0\) ;
- \(\gamma_M=0\Rightarrow\lambda=0\) dans la forme algébrique ;
- doublement du SNR : doublement de \(\lambda\) ;
- doublement de \(d_M\) : multiplication de \(\lambda\) par quatre.

---

## AU-EQ37 — Choix du seuil RFF

### Expression officielle

Pour une cible de faux rejet \(\alpha_{\mathrm{FRR}}\) :

\[
\boxed{
\theta
=
F^{-1}_{\chi^2_{n_f}}
\left(
1-\alpha_{\mathrm{FRR}}
\right)
}
\]

### Nature scientifique

```text
Dérivée de la fonction quantile de la loi chi-deux centrale.
```

### Paramètres nominaux

\[
n_f=3
\]

\[
\alpha_{\mathrm{FRR}}=0{,}05
\]

donnent :

\[
\theta
\approx
7{,}815
\]

Cette valeur est calculée. Elle n’est pas copiée comme constante depuis un article.

### Entrées

```text
target_frr
feature_count
```

### Sortie

```text
rff_threshold
```

### Fonction

```python
compute_rff_threshold(
    target_frr,
    feature_count
) -> float
```

### Conditions

\[
0<\alpha_{\mathrm{FRR}}<1
\]

\[
n_f\in\mathbb N^\star
\]

### Test principal

Pour :

```text
target_frr = 0.05
feature_count = 3
```

vérifier :

```text
threshold ≈ 7.8147
compute_frr(threshold, 3) ≈ 0.05
```

---

## AU-EQ38 — Probabilité idéale de forge d’un tag MAC

### Expression officielle

\[
\boxed{
p_{\mathrm{forge}}
=
2^{-b_{\mathrm{MAC}}}
}
\]

### Hypothèses

- clé non compromise ;
- tag uniforme ;
- algorithme cryptographique correctement utilisé ;
- une seule tentative ;
- absence d’attaque exploitant une faiblesse d’implémentation.

### Nature scientifique

```text
Borne cryptographique idéalisée.
```

### Paramètre nominal

Le modèle utilise un tag de :

```text
8 octets
```

soit :

\[
b_{\mathrm{MAC}}=64
\]

### Entrée

```text
mac_tag_bits
```

### Sortie

```text
mac_forgery_probability
```

### Fonction

```python
compute_mac_forgery_probability(
    mac_tag_bits
) -> float
```

### Test nominal

\[
b_{\mathrm{MAC}}=64
\Rightarrow
p_{\mathrm{forge}}
=
2^{-64}
\approx
5{,}4210\times10^{-20}
\]

---

## AU-EQ39 — Robustesse de l’authentification A1

### Expression officielle

\[
\boxed{
R_t^{\mathrm{auth}}(A_1)
=
1
-
2^{-b_{\mathrm{MAC}}}
}
\]

### Signification

A1 est l’authentification cryptographique conventionnelle par MAC.

Sa robustesse dépend de la longueur du tag dans le modèle idéalisé.

### Entrée

```text
mac_tag_bits
```

### Sortie

```text
a1_authentication_robustness
```

### Fonction

```python
compute_a1_robustness(
    mac_tag_bits
) -> float
```

### Propriétés

\[
0\leq R_t^{\mathrm{auth}}(A_1)<1
\]

La robustesse augmente lorsque \(b_{\mathrm{MAC}}\) augmente.

### Plancher de sécurité

Pour la contrainte FAR du Decision Maker, A1 utilise :

\[
\mathrm{FAR}_t(A_1)
=
2^{-b_{\mathrm{MAC}}}
\]

---

## AU-EQ40 — Probabilité totale d’usurpation sous A2

### Événements possibles pour Mallory

Mallory réussit si :

```text
1. elle est acceptée directement par le test RFF ;
ou
2. elle est rejetée par la RFF, puis forge le MAC du repli.
```

Ces deux événements sont disjoints dans l’arbre du protocole.

### Expression officielle

\[
\boxed{
P_{\mathrm{FA},t}(A_2)
=
\mathrm{FAR}_t
+
\left(
1-\mathrm{FAR}_t
\right)
2^{-b_{\mathrm{MAC}}}
}
\]

### Nature scientifique

```text
Dérivée par la loi des probabilités totales.
```

### Entrées

```text
rff_false_acceptance_rate
mac_tag_bits
```

### Sortie

```text
a2_total_false_acceptance_probability
```

### Fonction

```python
compute_a2_false_acceptance(
    rff_false_acceptance_rate,
    mac_tag_bits
) -> float
```

### Propriétés

\[
P_{\mathrm{FA},t}(A_2)
\geq
\mathrm{FAR}_t
\]

\[
P_{\mathrm{FA},t}(A_2)
\leq
\mathrm{FAR}_t
+
2^{-b_{\mathrm{MAC}}}
\]

### Point important

L’approximation :

\[
P_{\mathrm{FA},t}(A_2)
\approx
\mathrm{FAR}_t
\]

ou :

\[
R_t^{\mathrm{auth}}(A_2)
\approx
1-\mathrm{FAR}_t
\]

n’est permise que si le repli est considéré impossible à falsifier.

Cette approximation n’est pas le modèle nominal.

---

## AU-EQ41 — Robustesse de l’authentification A2

### Expression officielle

\[
\boxed{
R_t^{\mathrm{auth}}(A_2)
=
1
-
P_{\mathrm{FA},t}(A_2)
}
\]

En développant :

\[
R_t^{\mathrm{auth}}(A_2)
=
1
-
\mathrm{FAR}_t
-
\left(
1-\mathrm{FAR}_t
\right)
2^{-b_{\mathrm{MAC}}}
\]

### Entrées

```text
rff_false_acceptance_rate
mac_tag_bits
```

### Sortie

```text
a2_authentication_robustness
```

### Fonction

```python
compute_a2_robustness(
    rff_false_acceptance_rate,
    mac_tag_bits
) -> float
```

### Propriétés

\[
0\leq R_t^{\mathrm{auth}}(A_2)\leq1
\]

\[
R_t^{\mathrm{auth}}(A_2)
\leq
1-\mathrm{FAR}_t
\]

dans le modèle nominal, puisque le repli possède une probabilité de forge non nulle.

---

## AU-EQ42 — Probabilité de repli pour Alice

### Expression officielle

\[
\boxed{
p_{\mathrm{fb},t}^{(A)}
=
\mathrm{FRR}(\theta)
}
\]

### Signification

Pour une trame légitime, le repli est déclenché lorsque l’empreinte d’Alice est rejetée à tort.

### Entrée

```text
false_rejection_rate
```

### Sortie

```text
alice_fallback_probability
```

### Fonction

```python
compute_alice_fallback_probability(
    false_rejection_rate
) -> float
```

### Utilisation

Cette probabilité entre dans l’espérance d’énergie et de latence d’Alice sous A2 :

\[
E_t^{\mathrm{sec}}(A_2)
=
\mathrm{FRR}(\theta)E_{\mathrm{CR}}
\]

Elle affecte donc le coût et la disponibilité, mais n’est pas directement une faille de sécurité.

---

## AU-EQ43 — Probabilité de repli pour Mallory

### Expression officielle

\[
\boxed{
p_{\mathrm{fb},t}^{(M)}
=
1-\mathrm{FAR}_t
}
\]

### Signification

Pour une trame de Mallory, le repli est déclenché si le test RFF ne l’accepte pas directement comme Alice.

### Entrée

```text
rff_false_acceptance_rate
```

### Sortie

```text
mallory_fallback_probability
```

### Fonction

```python
compute_mallory_fallback_probability(
    rff_false_acceptance_rate
) -> float
```

### Règle énergétique

Cette probabilité ne doit jamais débiter la batterie d’Alice.

Elle sert à construire le risque de réussite du repli de Mallory dans AU-EQ40 et les métriques d’attaque observées chez Bob.

---

# 11. Chaîne officielle de l’authentification

## 11.1. Chaîne statistique RFF

```text
CFO + DCO + PO
        ↓
vecteur f_X
        ↓
observation gaussienne f_obs,t
        ↓
référence d’Alice f_A,ref
        ↓
statistique de Mahalanobis T_t
        ↓
test T_t <= theta
```

## 11.2. Chaîne FAR–FRR

```text
Sous Alice :
    T_t ~ chi2(n_f)
        ↓
    FRR(theta)
```

```text
Sous Mallory :
    d_M + gamma_M,t
        ↓
    lambda_M,t = d_M^2 * gamma_M,t
        ↓
    T_t ~ chi2 non centrale
        ↓
    FAR(theta, lambda_M,t)
```

## 11.3. Chaîne A1

```text
b_MAC
    ↓
p_forge = 2^(-b_MAC)
    ↓
R_auth(A1) = 1 - p_forge
```

## 11.4. Chaîne A2

```text
FAR RFF
    +
forge du repli
        ↓
P_FA(A2)
        ↓
R_auth(A2)
```

Pour Alice :

```text
FRR
    ↓
probabilité de repli légitime
    ↓
énergie et latence attendues de A2
```

---

# 12. Paramètres nominaux de l’authentification

| Paramètre | Symbole | Valeur de départ | Statut | Rôle |
|---|---:|---:|---|---|
| nombre d’attributs | \(n_f\) | 3 | littérature/choix de modèle | degrés de liberté |
| séparation Mallory | \(d_M\) | 2,0 | scénario | non-centralité et FAR |
| plage de \(d_M\) | — | 0,5 à 5 | scénario/sensibilité | robustesse des conclusions |
| cible FRR | \(\alpha_{\mathrm{FRR}}\) | 0,05 | politique de réglage | choix du seuil |
| seuil RFF | \(\theta\) | 7,815 | dérivé | FRR nominale de 5 % |
| longueur du tag | \(b_{\mathrm{MAC}}\) | 64 bits | politique | robustesse de A1 et du repli |
| taille du tag | \(M_{\mathrm{tag}}\) | 8 octets | politique | surcharge radio |
| temps RFF chez Bob | \(T_{\mathrm{RFF,Bob}}\) | 1,84 ms | littérature/scénario | latence de A2 |
| énergie RFF incrémentale chez Alice | \(E_{\mathrm{RFF,Alice}}\) | 0 J | littérature/dérivé | coût de A2 |

Le nombre d’observations d’enrôlement \(N_{\mathrm{enr}}\) reste à fixer par le protocole d’enrôlement.

---

# 13. Interfaces officielles de `authentication.py`

```python
build_rff_vector(
    cfo,
    dco,
    phase_offset
) -> array
```

```python
sample_rff_observation(
    mean_feature_vector,
    error_covariance,
    rng
) -> array
```

```python
estimate_rff_reference(
    alice_enrollment_samples
) -> array
```

```python
compute_mahalanobis_statistic(
    observed_feature_vector,
    alice_reference_vector,
    error_covariance
) -> float
```

```python
apply_rff_test(
    rff_statistic,
    rff_threshold
) -> bool
```

```python
compute_isotropic_statistic(
    observed_feature_vector,
    alice_reference_vector,
    error_variance
) -> float
```

```python
compute_noncentrality(
    mallory_feature_vector,
    alice_reference_vector,
    error_covariance
) -> float
```

```python
compute_frr(
    rff_threshold,
    feature_count
) -> float
```

```python
compute_far(
    rff_threshold,
    feature_count,
    noncentrality_parameter
) -> float
```

```python
compute_rff_noise_variance(
    reference_variance,
    mallory_snr_linear
) -> float
```

```python
compute_normalized_separation(
    mallory_feature_vector,
    alice_reference_vector,
    reference_variance
) -> float
```

```python
compute_noncentrality_from_snr(
    mallory_separation,
    mallory_snr_linear
) -> float
```

```python
compute_rff_threshold(
    target_frr,
    feature_count
) -> float
```

```python
compute_mac_forgery_probability(
    mac_tag_bits
) -> float
```

```python
compute_a1_robustness(
    mac_tag_bits
) -> float
```

```python
compute_a2_false_acceptance(
    rff_false_acceptance_rate,
    mac_tag_bits
) -> float
```

```python
compute_a2_robustness(
    rff_false_acceptance_rate,
    mac_tag_bits
) -> float
```

```python
compute_alice_fallback_probability(
    false_rejection_rate
) -> float
```

```python
compute_mallory_fallback_probability(
    rff_false_acceptance_rate
) -> float
```

Fonction d’orchestration :

```python
evaluate_authentication_action(
    authentication_action,
    snr_linear,
    parameters
) -> AuthenticationMetrics
```

---

# 14. Tests officiels de l’authentification

## 14.1. Tests déterministes

1. vecteur RFF de dimension trois ;
2. référence d’enrôlement calculée correctement ;
3. Mahalanobis nulle pour observation égale à la référence ;
4. cohérence entre forme générale et forme isotrope ;
5. acceptation pour \(T_t=\theta\) ;
6. seuil \(\theta\approx7{,}815\) pour \(n_f=3\) et \(\alpha_{\mathrm{FRR}}=0{,}05\) ;
7. \(\mathrm{FRR}\approx0{,}05\) au seuil nominal ;
8. \(\lambda=d_M^2\gamma_M\) ;
9. \(p_{\mathrm{forge}}=2^{-64}\) ;
10. robustesse A1 égale à \(1-2^{-64}\) ;
11. robustesse A2 calculée avec le repli ;
12. repli d’Alice égal à la FRR ;
13. repli de Mallory égal à \(1-\mathrm{FAR}\).

## 14.2. Tests de monotonie

À paramètres constants :

```text
theta augmente
    → FRR diminue
    → FAR augmente
```

```text
SNR de Mallory augmente
    → lambda augmente
    → FAR diminue
```

```text
d_M augmente
    → lambda augmente
    → FAR diminue
```

```text
d_M diminue
    → FAR augmente
```

```text
b_MAC augmente
    → p_forge diminue
    → robustesse A1 augmente
    → robustesse A2 augmente ou reste pratiquement inchangée
```

## 14.3. Tests limites

```text
d_M = 0
lambda = 0
FAR = 1 - FRR
```

```text
FAR = 0
P_FA(A2) = 2^(-b_MAC)
```

```text
FAR = 1
P_FA(A2) = 1
R_auth(A2) = 0
```

```text
b_MAC très grand
R_auth(A2) tend vers 1 - FAR
```

## 14.4. Tests statistiques

Lorsque le mode d’échantillonnage RFF est activé :

- vérifier empiriquement la loi centrale sous Alice ;
- vérifier empiriquement la loi non centrale sous Mallory ;
- comparer FAR et FRR empiriques aux expressions analytiques ;
- documenter le nombre de tirages et l’intervalle de confiance.

---

# 15. Erreurs scientifiques à éviter

Il est interdit de :

```text
présenter le modèle chi-deux comme provenant d’Alla et al.
```

```text
présenter l’architecture de Haenel comme source de la loi chi-deux.
```

```text
utiliser une distance euclidienne brute sur CFO, DCO et PO
sans covariance ou normalisation.
```

```text
faire dépendre la FRR du SNR dans le modèle nominal
sans changer explicitement les hypothèses.
```

```text
utiliser le SNR en dB dans lambda = d_M^2 * gamma_M.
```

```text
présenter d_M = 2 comme une valeur universelle.
```

```text
remplacer la robustesse complète de A2 par 1 - FAR
dans le modèle nominal.
```

```text
compter le repli de Mallory dans l’énergie d’Alice.
```

```text
confondre un faux rejet d’Alice avec une usurpation réussie.
```

```text
confondre FAR RFF et probabilité totale d’usurpation de A2.
```

```text
attribuer une valeur fixe à N_enr sans la documenter.
```

---

# 16. Limites du modèle d’authentification

Le modèle analytique initial ne représente pas explicitement :

- une distribution non gaussienne des attributs ;
- une covariance dépendante du temps ;
- la dérive thermique des empreintes ;
- une covariance mal estimée ;
- un profil d’Alice compromis ;
- un attaquant reproduisant précisément l’empreinte ;
- des attributs supplémentaires ;
- les performances d’un classifieur d’apprentissage ;
- une attaque de relais ;
- plusieurs tentatives cryptographiques cumulées ;
- la compromission de la clé MAC ;
- les défauts d’implémentation cryptographique.

Ces limites doivent être rappelées au moment d’interpréter FAR, FRR et robustesse.

---

# 17. Résumé de traçabilité de l’authentification

```text
AU-EQ23 :
    CFO–DCO–PO
    littérature + choix de trois attributs

AU-EQ24 :
    observation gaussienne
    choix de modélisation

AU-EQ25 :
    référence d’enrôlement
    estimation standard

AU-EQ26 à AU-EQ31 :
    Mahalanobis et lois centrale/non centrale
    littérature adaptée au vecteur RFF

AU-EQ32 et AU-EQ33 :
    FRR et FAR
    dérivées des CDF

AU-EQ34 à AU-EQ36 :
    lien SNR–variance–non-centralité
    hypothèse et dérivation de cette étude

AU-EQ37 :
    seuil RFF
    dérivé d’une cible de FRR

AU-EQ38 et AU-EQ39 :
    forge et robustesse A1
    borne cryptographique idéalisée

AU-EQ40 et AU-EQ41 :
    usurpation totale et robustesse A2
    loi des probabilités totales

AU-EQ42 et AU-EQ43 :
    probabilités de repli
    dérivées de FRR et FAR
```

---

---

# 18. Fiches détaillées de la génération et de la gestion de clé

## 18.1. Chaîne fonctionnelle retenue

La chaîne de génération de clé PHY est regroupée en quatre blocs :

```text
1. sondage du canal ;
2. quantification ;
3. réconciliation ;
4. amplification de confidentialité.
```

Le modèle s’inspire de la chaîne LoRaWAN comprenant notamment :

- collecte et synchronisation des mesures ;
- pré-correction DCT ;
- quantification avec bande de garde ;
- réconciliation BCH ;
- amplification de confidentialité par SHA-256.

Cette simplification conserve les fonctions scientifiques principales. Elle ne signifie pas que les coûts CPU de DCT, BCH et SHA-256 sont déjà calibrés pour le microcontrôleur de référence.

Les actions concernées sont :

```text
K0  : conserver la clé courante ;
K1a : génération PHY opportuniste ;
K1b : génération PHY par sondages dédiés ;
K2  : renouvellement conventionnel par ECC.
```

---

## KM-EQ44 — KDR analytique par loi de l’arc-sinus

### Expression officielle

\[
\boxed{
\mathrm{KDR}_{\mathrm{brut},t}
=
\frac{
\arccos(\rho_{AB,t})
}{
\pi
}
}
\]

### Signification

\(\mathrm{KDR}_{\mathrm{brut},t}\) représente la probabilité de désaccord entre les bits produits par Alice et Bob avant réconciliation lorsque :

- leurs observations sont gaussiennes conjointes ;
- elles sont centrées ;
- leur coefficient de corrélation est \(\rho_{AB,t}\) ;
- chaque observation est quantifiée par son signe.

### Nature scientifique

```text
Relation issue de la loi de l’arc-sinus de Van Vleck–Middleton.
```

### Hypothèses de validité

- gaussianité conjointe ;
- observations centrées ;
- quantification binaire par signe ;
- même règle de quantification chez Alice et Bob ;
- aucune bande de garde dans la forme analytique exacte ;
- aucune quantification différentielle dans la forme analytique exacte.

### Entrée

```text
reciprocity
```

avec :

\[
-1\leq\rho_{AB,t}\leq1
\]

### Sortie

```text
raw_key_disagreement_rate
```

### Domaine mathématique

Puisque la corrélation nominale reste signée :

\[
0
\leq
\mathrm{KDR}_{\mathrm{brut},t}
\leq
1
\]

Cas particuliers :

\[
\rho_{AB,t}=1
\Rightarrow
\mathrm{KDR}_{\mathrm{brut},t}=0
\]

\[
\rho_{AB,t}=0
\Rightarrow
\mathrm{KDR}_{\mathrm{brut},t}=0{,}5
\]

\[
\rho_{AB,t}=-1
\Rightarrow
\mathrm{KDR}_{\mathrm{brut},t}=1
\]

### Note de cohérence documentaire

Le tableau des variables du modèle indique ponctuellement un domaine \([0,0{,}5]\). Ce domaine n’est valable que si la corrélation d’entrée est supposée non négative.

Comme le modèle nominal conserve les corrélations négatives, le domaine mathématiquement cohérent de l’équation (44) est :

\[
[0,1]
\]

L’implémentation doit donc accepter toute corrélation dans \([-1,1]\).

### Module

```text
key_generation.py
```

### Fonction

```python
compute_raw_kdr(
    reciprocity
) -> float
```

### Pseudocode

```text
fonction compute_raw_kdr(reciprocity):

    vérifier -1 <= reciprocity <= 1

    raw_kdr =
        arccos(reciprocity)
        / pi

    retourner raw_kdr
```

### Test officiel

Pour :

\[
\rho_{AB,t}=0{,}6
\]

on obtient :

\[
\mathrm{KDR}_{\mathrm{brut},t}
=
\frac{\arccos(0{,}6)}{\pi}
\approx
0{,}2952
\]

---

## KM-EQ45 — Seuil maximal de KDR

### Expression officielle

\[
\boxed{
\mathrm{KDR}_{\max}
=
0{,}30
}
\]

### Nature scientifique

```text
Politique de scénario.
```

La valeur de 30 % :

- n’est pas une constante universelle ;
- n’est pas attribuée à Ruotsalainen ;
- doit être analysée en sensibilité ;
- représente la limite d’accord acceptée par le modèle.

### Paramètre Python

```text
maximum_kdr = 0.30
```

### Domaine

\[
0
\leq
\mathrm{KDR}_{\max}
\leq
1
\]

Pour une quantification destinée à l’accord direct, une valeur inférieure à \(0{,}5\) est normalement attendue.

---

## KM-EQ46 — Seuil minimal de corrélation

### Expression officielle

En inversant KM-EQ44 :

\[
\boxed{
\rho_{\min}
=
\cos
\left(
\pi\mathrm{KDR}_{\max}
\right)
}
\]

Avec :

\[
\mathrm{KDR}_{\max}=0{,}30
\]

on obtient :

\[
\rho_{\min}
=
\cos(0{,}30\pi)
\approx
0{,}587785
\]

soit, dans le tableau numérique :

\[
\rho_{\min}
\approx
0{,}588
\]

### Nature scientifique

```text
Dérivé d’une politique de KDR.
```

### Fonction

```python
derive_minimum_correlation(
    maximum_kdr
) -> float
```

### Règle

La valeur :

```text
0.588
```

est la valeur nominale cohérente avec le tableau final des paramètres.

Une variante arrondie à :

```text
0.60
```

ne peut être utilisée que comme arrondi conservatif explicitement déclaré.

### Test

```text
derive_minimum_correlation(0.30)
≈ 0.5877852523
```

---

## KM-EQ47 — Mode analytique du KDR

### Expression officielle

\[
\boxed{
\mathrm{KDR}_t
=
\mathrm{KDR}_{\mathrm{brut},t}
}
\]

### Nature

```text
Mode analytique.
```

### Utilisation

Ce mode est employé lorsque la quantification est représentée exactement par une quantification binaire par signe.

### Fonction

```python
compute_effective_kdr(
    raw_kdr,
    mode="analytic"
) -> float
```

### Règle

Le mode analytique ne doit appliquer :

- ni facteur de bande de garde ;
- ni correction empirique ;
- ni troncature de la corrélation ;
- ni valeur absolue de la corrélation.

---

## KM-EQ48 — Mode calibré du KDR

### Expression officielle

\[
\boxed{
\mathrm{KDR}_t
=
g_{\mathrm q}
\left(
\rho_{AB,t};
\boldsymbol\beta_{\mathrm q}
\right)
}
\]

où :

- \(g_{\mathrm q}\) est une courbe monotone calibrée ;
- \(\boldsymbol\beta_{\mathrm q}\) contient ses paramètres.

### Nature scientifique

```text
Calibré.
```

### Exigences

La fonction \(g_{\mathrm q}\) doit être ajustée sur les résultats du quantificateur réellement retenu, par exemple :

- quantification avec bande de garde ;
- quantification différentielle ;
- autre quantificateur mesuré.

Aucune forme numérique ne doit être inventée avant calibration.

### Variante exploratoire

Une forme multiplicative peut être utilisée uniquement comme surrogate exploratoire :

\[
\mathrm{KDR}_t
=
\kappa_{\mathrm{gb}}
\mathrm{KDR}_{\mathrm{brut},t}
\]

Elle doit alors être classée :

```text
calibrée / exploratoire
```

et non :

```text
relation de littérature
```

### Paramètre nominal

\[
\kappa_{\mathrm{gb}}=1{,}00
\]

Cette valeur est neutre et revient à ne pas modifier le KDR brut.

### Fonctions

```python
compute_calibrated_kdr(
    reciprocity,
    calibration_parameters,
    calibration_model
) -> float
```

```python
compute_exploratory_guard_band_kdr(
    raw_kdr,
    guard_band_factor
) -> float
```

### Règles numériques

La sortie doit être bornée conformément au domaine du modèle calibré.

Une saturation éventuelle doit être explicitement documentée et testée, et non appliquée silencieusement.

---

## KM-EQ49 — Entropie binaire

### Expression officielle

\[
\boxed{
h_2(p)
=
-p\log_2(p)
-
(1-p)\log_2(1-p)
}
\]

avec la convention :

\[
0\log_2(0)=0
\]

### Domaine

\[
0\leq p\leq1
\]

### Propriétés

\[
h_2(0)=0
\]

\[
h_2(1)=0
\]

\[
h_2(0{,}5)=1
\]

\[
0\leq h_2(p)\leq1
\]

### Fonction

```python
binary_entropy(
    probability
) -> float
```

### Pseudocode

```text
si probability == 0 ou probability == 1:
    retourner 0

sinon:
    retourner
        -p * log2(p)
        -(1-p) * log2(1-p)
```

### Utilisation

Le terme :

\[
1-h_2(\mathrm{KDR}_t)
\]

est motivé par la borne de Slepian–Wolf dans le cas d’un canal binaire symétrique idéal.

Il ne constitue pas, à lui seul, une capacité secrète vis-à-vis de Mallory.

---

## KM-EQ50 — Rendement de réconciliation en ligne

### Expression officielle

\[
\boxed{
y_{\mathrm{rec},t}
=
\eta_{\mathrm{keep}}
\left[
1-h_2(\mathrm{KDR}_t)
\right]
}
\]

### Signification

\(y_{\mathrm{rec},t}\) représente un rendement approximatif exprimé en :

```text
bit utile par mesure
```

Le facteur :

\[
\eta_{\mathrm{keep}}\in(0,1]
\]

représente la proportion de mesures conservées après :

- bande de garde ;
- prétraitement ;
- rejet éventuel de mesures.

### Nature scientifique

```text
Dérivé / calibré dans cette étude.
```

Slepian–Wolf motive le terme \(1-h_2(\mathrm{KDR})\), mais ne fournit pas la formule composite complète.

### Cohérence des notations du fichier source

Le corps du modèle utilise :

```text
eta_keep
y_rec,t
```

tandis que le dictionnaire et le tableau numérique utilisent ponctuellement :

```text
eta_samp
y_sec,t
```

Pour l’implémentation, la convention retenue est :

```text
kept_measurement_ratio
reconciliation_yield
```

avec l’équivalence documentaire :

\[
\eta_{\mathrm{keep}}
\equiv
\eta_{\mathrm{samp}}
\]

dans la première version.

Le symbole principal de l’équation reste :

\[
y_{\mathrm{rec},t}
\]

### Paramètre nominal

\[
\eta_{\mathrm{keep}}=0{,}70
\]

Cette valeur est inspirée du cas expérimental :

\[
\mathrm{KPM}=70\%
\]

### Fonction

```python
compute_reconciliation_yield(
    effective_kdr,
    kept_measurement_ratio
) -> float
```

### Propriétés

- le rendement diminue lorsque le KDR se rapproche de \(0{,}5\) ;
- à \(KDR=0\), le rendement vaut \(\eta_{\mathrm{keep}}\) ;
- à \(KDR=0{,}5\), le rendement vaut zéro ;
- pour un KDR supérieur à \(0{,}5\), \(1-h_2(KDR)\) redevient positif mathématiquement, mais cela ne signifie pas qu’un accord direct est exploitable.

La faisabilité d’accord doit donc être testée séparément avec KM-EQ55.

---

## KM-EQ51 — Nombre de mesures nécessaire en ligne

### Expression officielle

\[
\boxed{
N_{\mathrm{meas},t}^{\mathrm{online}}
=
\left\lceil
\frac{
\ell_K
}{
\max
\left(
y_{\mathrm{rec},t},
\epsilon
\right)
}
\right\rceil
}
\]

### Variables

| Variable | Signification |
|---|---|
| \(\ell_K\) | longueur cible de la clé en bits |
| \(y_{\mathrm{rec},t}\) | rendement approximatif en bit/mesure |
| \(\epsilon\) | protection numérique strictement positive |
| \(N_{\mathrm{meas},t}^{\mathrm{online}}\) | nombre entier de mesures |

### Nature scientifique

```text
Dérivé par division de la longueur cible par le rendement.
```

### Paramètre nominal

\[
\ell_K=128\ \mathrm{bits}
\]

### Paramètre non fixé

La valeur numérique de :

\[
\epsilon
\]

n’est pas fixée dans le tableau final des paramètres. Elle doit être déclarée dans `parameters.py` avec le statut :

```text
protection numérique / à valider
```

### Fonction

```python
compute_required_measurements(
    key_length_bits,
    reconciliation_yield,
    numerical_epsilon
) -> int
```

### Propriétés

- le résultat est un entier positif ;
- il diminue lorsque le rendement augmente ;
- il augmente lorsque la longueur de clé augmente ;
- lorsque le rendement tend vers zéro, le nombre de mesures devient très grand.

### Règle de sécurité numérique

La protection \(\epsilon\) empêche une division par zéro. Elle ne doit pas masquer une situation physiquement irréalisable.

La fonction doit donc retourner également un indicateur ou permettre au filtre de détecter :

```text
rendement pratiquement nul
```

---

## KM-EQ52 — Nombre de bits intermédiaires dans la reproduction de Ruotsalainen

### Expression officielle

\[
\boxed{
n_{\mathrm{keys}}
=
\frac{
128
}{
\mathrm{KDR}_{\mathrm{Eve}}
-
\mathrm{KDR}_{AB}
}
}
\]

### Nature scientifique

```text
Relation expérimentale de littérature utilisée hors ligne.
```

### Condition indispensable

\[
\mathrm{KDR}_{\mathrm{Eve}}
>
\mathrm{KDR}_{AB}
\]

Si cette condition n’est pas respectée, la formule n’est pas exploitable.

### Utilisation

Cette relation sert uniquement à reproduire l’expérience de référence lorsque la statistique d’Eve est connue.

Elle n’est pas une entrée disponible en temps réel chez Bob.

### Fonction de validation

```python
reproduce_ruotsalainen_required_key_bits(
    eve_kdr,
    alice_bob_kdr
) -> float
```

---

## KM-EQ53 — Nombre de mesures dans la reproduction de Ruotsalainen

### Expression officielle

\[
\boxed{
n_{\mathrm{meas}}
=
\frac{
n_{\mathrm{keys}}
}{
\mathrm{KPM}
}
}
\]

### Condition

\[
0<\mathrm{KPM}\leq1
\]

### Valeur expérimentale de référence

\[
\mathrm{KPM}=0{,}70
\]

### Fonction de validation

```python
reproduce_ruotsalainen_measurements(
    required_key_bits,
    key_percentage_per_measurement
) -> float
```

La formule source n’impose pas explicitement un plafond entier. Toute conversion en nombre entier pour une simulation de paquets doit être déclarée séparément.

---

## KM-EQ54 — Temps de production dans la reproduction de Ruotsalainen

### Expression officielle

\[
\boxed{
T_{\mathrm{AES}}
=
n_{\mathrm{meas}}
T_s
}
\]

### Valeur expérimentale/scénario associée

Le modèle utilise un intervalle nominal de sondage dédié :

\[
T_s
=
181{,}04\ \mathrm{s}
\]

dérivé du Time-on-Air d’une trame de 32 octets à :

```text
SF = 12
BW = 125 kHz
duty-cycle = 1 %
```

### Fonction de validation

```python
reproduce_ruotsalainen_generation_time_s(
    measurement_count,
    probe_interval_s
) -> float
```

### Règle

KM-EQ52 à KM-EQ54 ne doivent pas être utilisées comme règle en ligne du Decision Maker, car \(\mathrm{KDR}_{\mathrm{Eve}}\) n’est pas observée en temps réel.

---

## KM-EQ55 — Faisabilité d’accord

### Expression officielle

\[
\boxed{
\phi_t^{\mathrm{agree}}
=
\mathbb 1
\left\{
\mathrm{KDR}_t
\leq
\mathrm{KDR}_{\max}
\right\}
}
\]

### Sortie

```text
agreement_feasible
```

### Fonction

```python
check_agreement_feasibility(
    effective_kdr,
    maximum_kdr
) -> bool
```

### Cas frontière

\[
\mathrm{KDR}_t
=
\mathrm{KDR}_{\max}
\Rightarrow
\phi_t^{\mathrm{agree}}=1
\]

### Équivalence dans le mode analytique uniquement

Lorsque :

\[
\mathrm{KDR}_t
=
\frac{\arccos(\rho_{AB,t})}{\pi}
\]

alors :

\[
\phi_t^{\mathrm{agree}}
=
\mathbb 1
\left\{
\rho_{AB,t}
\geq
\rho_{\min}
\right\}
\]

Après calibration d’un autre quantificateur, le seuil de corrélation doit être recalculé à partir de \(g_{\mathrm q}\).

---

## KM-EQ56 — Faisabilité PHY complète

### Expression officielle

\[
\boxed{
\phi_t^{\mathrm{PHY}}
=
\phi_t^{\mathrm{agree}}
\phi_t^{\mathrm{var}}
}
\]

### Signification

- \(\phi_t^{\mathrm{agree}}\) vérifie que les bits d’Alice et Bob peuvent être suffisamment proches ;
- \(\phi_t^{\mathrm{var}}\) doit vérifier une condition de variabilité ou d’entropie ;
- \(\phi_t^{\mathrm{PHY}}\) représente la faisabilité complète réservée à la génération PHY.

### Nature scientifique

```text
Formulation du modèle, dont la composante de variabilité reste à valider.
```

### Point bloquant explicite

Le dernier fichier de modélisation ne définit pas encore la métrique numérique exacte de :

\[
\phi_t^{\mathrm{var}}
\]

Le code ne doit donc pas inventer une formule cachée.

### Fonction

```python
check_phy_feasibility(
    agreement_feasible,
    variation_feasible
) -> bool
```

### Règle d’interprétation

Tant que la variabilité n’est pas validée, les résultats doivent annoncer :

```text
faisabilité d’accord
```

et non :

```text
sécurité informationnelle complète
```

### Intégration au Decision Maker

Le résultat doit conserver séparément :

```text
agreement_feasible
variation_feasible
phy_feasible
variation_metric_validated
```

Une éventuelle campagne exploratoire qui suppose :

```text
variation_feasible = True
```

doit être étiquetée comme hypothèse de scénario et journalisée.

---

## KM-EQ57 — Taux d’utilisation temporelle de la clé

### Expression officielle

\[
\boxed{
u_t^{\mathrm{time}}
=
\min
\left\{
1,
\frac{
a_t^{\mathrm{key}}
}{
\tau_{\max}
}
\right\}
}
\]

### Variables

- \(a_t^{\mathrm{key}}\) : âge actuel de la clé ;
- \(\tau_{\max}\) : âge maximal autorisé.

### Nature scientifique

```text
Politique du modèle.
```

### Conditions

\[
a_t^{\mathrm{key}}\geq0
\]

\[
\tau_{\max}>0
\]

---

## KM-EQ58 — Taux d’utilisation par nombre de messages

### Expression officielle

\[
\boxed{
u_t^{\mathrm{msg}}
=
\min
\left\{
1,
\frac{
n_t^{\mathrm{key}}
}{
N_{\max}
}
\right\}
}
\]

### Variables

- \(n_t^{\mathrm{key}}\) : messages déjà protégés avec la clé ;
- \(N_{\max}\) : nombre maximal autorisé.

### Conditions

\[
n_t^{\mathrm{key}}\geq0
\]

\[
N_{\max}>0
\]

---

## KM-EQ59 — Indice de consommation de la cryptopériode

### Expression officielle

\[
\boxed{
q_t
=
\max
\left\{
u_t^{\mathrm{time}},
u_t^{\mathrm{msg}}
\right\}
}
\]

### Nature scientifique

```text
Règle conservative de politique.
```

La première limite critique entre l’âge et le nombre de messages gouverne l’indice.

### Domaine

\[
0\leq q_t\leq1
\]

### Fonction commune pour KM-EQ57 à KM-EQ59

```python
compute_key_aging_index(
    key_age_s,
    maximum_key_age_s,
    messages_with_current_key,
    maximum_messages_per_key
) -> float
```

### Propriétés

- \(q_t=0\) pour une clé neuve sans message ;
- \(q_t=1\) dès qu’une limite est atteinte ou dépassée ;
- \(q_t\) ne diminue pas tant que la clé n’est pas renouvelée.

---

## KM-EQ60 — Déclenchement anticipé du renouvellement

### Expression officielle

\[
\boxed{
r_t
=
\mathbb 1
\left\{
q_t
\geq
q_{\mathrm{trig}}
\right\}
}
\]

### Paramètre nominal

\[
q_{\mathrm{trig}}=0{,}60
\]

### Sortie

```text
renewal_required
```

### Fonction

```python
is_renewal_triggered(
    key_aging_index,
    renewal_trigger
) -> bool
```

### Règle de raisonnement associée

```text
r_t = 0  → seule K0 est cohérente
r_t = 1  → K0 est exclue
```

Cette règle provient de la formulation actuelle du modèle. Elle doit être appliquée avant les contraintes numériques.

---

## KM-EQ61 — Expiration dure de la clé

### Expression officielle

\[
\boxed{
e_t^{\mathrm{key}}
=
\mathbb 1
\left\{
a_t^{\mathrm{key}}
\geq
\tau_{\max}
\;\lor\;
n_t^{\mathrm{key}}
\geq
N_{\max}
\;\lor\;
c_t=1
\right\}
}
\]

### Signification

La clé est expirée si :

- son âge maximal est atteint ;
- son nombre maximal de messages est atteint ;
- une compromission ou suspicion est signalée.

### Note sur le symbole

Le fichier emploie déjà \(\mathbf c_t\) pour le vecteur de contexte. Afin d’éviter une collision dans le code, le drapeau \(c_t\) de cette équation sera nommé :

```text
compromise_suspected
```

### Sortie

```text
key_expired
```

### Fonction

```python
is_key_expired(
    key_age_s,
    maximum_key_age_s,
    messages_with_current_key,
    maximum_messages_per_key,
    compromise_suspected
) -> bool
```

### Règle

Lorsque :

\[
e_t^{\mathrm{key}}=1
\]

alors :

```text
K0 est interdite
```

---

## KM-EQ62 — Temps restant selon l’âge

### Expression officielle

\[
\boxed{
T_t^{\mathrm{age}}
=
\max
\left\{
\tau_{\max}
-
a_t^{\mathrm{key}},
0
\right\}
}
\]

### Sortie

```text
remaining_time_by_age_s
```

---

## KM-EQ63 — Temps restant selon le nombre de messages

### Expression officielle

\[
\boxed{
T_t^{\mathrm{msg}}
=
\max
\left\{
N_{\max}
-
n_t^{\mathrm{key}},
0
\right\}
T_{\mathrm{msg}}
}
\]

### Hypothèse indispensable

Cette relation suppose :

- un trafic périodique ;
- ou une période moyenne explicitement assumée.

### Paramètre nominal

\[
T_{\mathrm{msg}}=60\ \mathrm{s}
\]

### Sortie

```text
remaining_time_by_messages_s
```

---

## KM-EQ64 — Échéance de renouvellement

### Expression officielle

\[
\boxed{
T_t^{\mathrm{deadline}}
=
\max
\left\{
T_{\min},
\min
\left(
T_t^{\mathrm{age}},
T_t^{\mathrm{msg}}
\right)
\right\}
}
\]

### Signification

L’échéance est gouvernée par la première des deux limites :

- limite d’âge ;
- limite de nombre de messages.

Le terme \(T_{\min}\) protège le modèle d’une échéance nulle ou trop petite.

### Nature scientifique

```text
Dérivé par comptabilisation et politique.
```

### Paramètre non fixé

La valeur de :

\[
T_{\min}
\]

n’apparaît pas dans le tableau numérique final.

Elle doit être ajoutée à `parameters.py` avec le statut :

```text
politique / à valider
```

### Fonction commune pour KM-EQ62 à KM-EQ64

```python
compute_key_deadline_s(
    key_age_s,
    maximum_key_age_s,
    messages_with_current_key,
    maximum_messages_per_key,
    message_period_s,
    minimum_deadline_s
) -> float
```

### Paramètres nominaux

\[
\tau_{\max}=86400\ \mathrm{s}
\]

\[
N_{\max}=1000
\]

\[
T_{\mathrm{msg}}=60\ \mathrm{s}
\]

### Tests

- clé neuve ;
- limite d’âge plus proche ;
- limite de messages plus proche ;
- clé déjà expirée ;
- application correcte de \(T_{\min}\).

---

## KM-EQ65 — Indice de qualité/fraîcheur de K0

### Expression officielle

\[
\boxed{
Q_t^{\mathrm{key}}(K_0)
=
1-q_t
}
\]

### Signification

L’indice de K0 diminue lorsque la cryptopériode est consommée.

### Domaine

\[
0\leq Q_t^{\mathrm{key}}(K_0)\leq1
\]

### Fonction

```python
compute_k0_quality(
    key_aging_index
) -> float
```

### Nature scientifique

```text
Indice de décision proposé.
```

Il ne s’agit pas d’une probabilité absolue de non-compromission.

---

## KM-EQ66 — Indice de qualité de K1a et K1b

### Expression officielle

\[
\boxed{
Q_t^{\mathrm{key}}(K_{1a})
=
Q_t^{\mathrm{key}}(K_{1b})
=
1-h_2(\mathrm{KDR}_t)
}
\]

### Signification

Les deux actions PHY partagent le même indice de qualité d’accord. Elles se distinguent principalement par :

- leur coût énergétique ;
- leur délai ;
- leur mode de collecte des mesures.

### Fonction

```python
compute_phy_key_quality(
    effective_kdr
) -> float
```

### Nature scientifique

```text
Indice de décision proposé.
```

### Limite importante

L’indice mesure une qualité d’accord binaire. Il ne représente pas :

- l’entropie conditionnelle vis-à-vis de Mallory ;
- une capacité secrète ;
- une probabilité universelle de sécurité ;
- une preuve d’imprévisibilité.

---

## KM-EQ67 — Indice de qualité de K2

### Expression officielle

\[
\boxed{
Q_t^{\mathrm{key}}(K_2)
=
1
-
2^{-b_{\mathrm{sec}}}
}
\]

### Signification

\(b_{\mathrm{sec}}\) représente le niveau de sécurité cryptographique utilisé pour placer K2 sur une échelle normalisée.

### Nature scientifique

```text
Indice de décision proposé à partir d’une borne cryptographique.
```

### Paramètre non résolu

Le dernier fichier de modélisation ne fournit pas de valeur numérique explicite pour :

\[
b_{\mathrm{sec}}
\]

Cette valeur ne doit pas être déduite automatiquement :

- de la longueur de clé AES ;
- de la taille de la courbe ECC ;
- de la taille d’une signature ;
- de \(b_{\mathrm{MAC}}\).

Elle doit correspondre au niveau de sécurité réel du mécanisme K2 retenu et être validée.

### Fonction

```python
compute_k2_quality(
    security_strength_bits
) -> float
```

### Règle

Le paramètre Python :

```text
security_strength_bits
```

doit être classé :

```text
à valider
```

tant que le protocole ECC exact et son niveau de sécurité ne sont pas définitivement fixés.

---

# 19. Chaîne officielle de génération et de gestion de clé

## 19.1. Chaîne de qualité d’accord

```text
rho_AB,t
    ↓
KM-EQ44
    ↓
KDR_brut,t
    ↓
KM-EQ47 ou KM-EQ48
    ↓
KDR_t
    ↓
KM-EQ49
    ↓
h2(KDR_t)
```

## 19.2. Chaîne du nombre de mesures

```text
KDR_t
    +
eta_keep
    ↓
KM-EQ50
    ↓
y_rec,t
    +
longueur de clé ell_K
    ↓
KM-EQ51
    ↓
N_meas,t
```

## 19.3. Chaîne de faisabilité

```text
KDR_t <= KDR_max
    ↓
phi_agree
    +
phi_var
    ↓
phi_PHY
```

## 19.4. Chaîne de cryptopériode

```text
âge de clé / âge maximal
        ↓
u_time
```

```text
messages / limite de messages
        ↓
u_msg
```

```text
max(u_time, u_msg)
        ↓
q_t
        ↓
r_t
```

En parallèle :

```text
âge expiré
ou messages expirés
ou compromission
        ↓
e_key,t
```

## 19.5. Chaîne des indices de décision

```text
K0  → 1 - q_t
K1a → 1 - h2(KDR_t)
K1b → 1 - h2(KDR_t)
K2  → 1 - 2^(-b_sec)
```

---

# 20. Paramètres nominaux de la gestion de clé

| Paramètre | Symbole | Valeur de départ | Statut |
|---|---:|---:|---|
| KDR maximal | \(\mathrm{KDR}_{\max}\) | 0,30 | politique |
| corrélation minimale | \(\rho_{\min}\) | 0,588 | dérivé/politique |
| longueur de clé | \(\ell_K\) | 128 bits | littérature |
| facteur exploratoire | \(\kappa_{\mathrm{gb}}\) | 1,00 | dérivé/neutre |
| mesures conservées | \(\eta_{\mathrm{keep}}\) | 0,70 | littérature/scénario |
| intervalle dédié | \(T_s\) | 181,04 s | dérivé |
| période message | \(T_{\mathrm{msg}}\) | 60 s | scénario |
| âge maximal | \(\tau_{\max}\) | 86400 s | politique |
| messages max | \(N_{\max}\) | 1000 | politique |
| seuil anticipé | \(q_{\mathrm{trig}}\) | 0,60 | politique |
| protection numérique | \(\epsilon\) | à fixer | à valider |
| échéance minimale | \(T_{\min}\) | à fixer | politique/à valider |
| niveau K2 | \(b_{\mathrm{sec}}\) | à fixer | à valider |
| métrique de variabilité | \(\phi_t^{\mathrm{var}}\) | à définir | à valider |

---

# 21. Interfaces officielles de `key_generation.py`

```python
compute_raw_kdr(
    reciprocity
) -> float
```

```python
derive_minimum_correlation(
    maximum_kdr
) -> float
```

```python
compute_effective_kdr(
    raw_kdr,
    mode
) -> float
```

```python
compute_calibrated_kdr(
    reciprocity,
    calibration_parameters,
    calibration_model
) -> float
```

```python
compute_exploratory_guard_band_kdr(
    raw_kdr,
    guard_band_factor
) -> float
```

```python
binary_entropy(
    probability
) -> float
```

```python
compute_reconciliation_yield(
    effective_kdr,
    kept_measurement_ratio
) -> float
```

```python
compute_required_measurements(
    key_length_bits,
    reconciliation_yield,
    numerical_epsilon
) -> int
```

```python
reproduce_ruotsalainen_required_key_bits(
    eve_kdr,
    alice_bob_kdr
) -> float
```

```python
reproduce_ruotsalainen_measurements(
    required_key_bits,
    key_percentage_per_measurement
) -> float
```

```python
reproduce_ruotsalainen_generation_time_s(
    measurement_count,
    probe_interval_s
) -> float
```

```python
check_agreement_feasibility(
    effective_kdr,
    maximum_kdr
) -> bool
```

```python
check_phy_feasibility(
    agreement_feasible,
    variation_feasible
) -> bool
```

```python
compute_key_aging_index(
    key_age_s,
    maximum_key_age_s,
    messages_with_current_key,
    maximum_messages_per_key
) -> float
```

```python
is_renewal_triggered(
    key_aging_index,
    renewal_trigger
) -> bool
```

```python
is_key_expired(
    key_age_s,
    maximum_key_age_s,
    messages_with_current_key,
    maximum_messages_per_key,
    compromise_suspected
) -> bool
```

```python
compute_key_deadline_s(
    key_age_s,
    maximum_key_age_s,
    messages_with_current_key,
    maximum_messages_per_key,
    message_period_s,
    minimum_deadline_s
) -> float
```

```python
compute_k0_quality(
    key_aging_index
) -> float
```

```python
compute_phy_key_quality(
    effective_kdr
) -> float
```

```python
compute_k2_quality(
    security_strength_bits
) -> float
```

Fonction d’orchestration :

```python
evaluate_key_action(
    key_action,
    reciprocity,
    key_state,
    parameters
) -> KeyMetrics
```

---

# 22. Tests officiels de la génération et de la gestion de clé

## 22.1. Tests de KM-EQ44

| \(\rho_{AB}\) | KDR attendu |
|---:|---:|
| \(1\) | \(0\) |
| \(0{,}6\) | environ \(0{,}2952\) |
| \(0\) | \(0{,}5\) |
| \(-1\) | \(1\) |

Vérifier également :

- monotonie décroissante du KDR avec \(\rho_{AB}\) ;
- rejet d’une corrélation hors de \([-1,1]\) ;
- conservation du comportement des corrélations négatives.

## 22.2. Tests de seuil

```text
KDR_max = 0.30
rho_min ≈ 0.587785
```

Vérifier l’équivalence analytique :

```text
KDR <= 0.30
équivaut à
rho >= rho_min
```

à la tolérance numérique.

## 22.3. Tests de l’entropie

```text
h2(0) = 0
h2(0.5) = 1
h2(1) = 0
h2(p) = h2(1-p)
```

## 22.4. Tests du rendement

```text
KDR = 0
y_rec = eta_keep
```

```text
KDR = 0.5
y_rec = 0
```

Vérifier que le rendement diminue sur l’intervalle utile :

\[
0\leq KDR\leq0{,}5
\]

## 22.5. Tests du nombre de mesures

- résultat entier ;
- résultat décroissant avec le rendement ;
- résultat croissant avec la longueur de clé ;
- protection correcte lorsque le rendement vaut zéro ;
- signalement d’une faisabilité très faible.

## 22.6. Tests de faisabilité

```text
KDR < KDR_max  → accord faisable
KDR = KDR_max  → accord faisable
KDR > KDR_max  → accord non faisable
```

Vérifier les quatre combinaisons booléennes de :

```text
agreement_feasible
variation_feasible
```

## 22.7. Tests de cryptopériode

- clé neuve ;
- limite d’âge dominante ;
- limite de messages dominante ;
- égalité des deux limites ;
- seuil anticipé exactement atteint ;
- âge maximal exactement atteint ;
- nombre maximal exactement atteint ;
- compromission signalée ;
- remise à zéro après renouvellement.

## 22.8. Tests des indices

```text
q_t = 0  → Q_key(K0) = 1
q_t = 1  → Q_key(K0) = 0
```

```text
KDR = 0   → Q_key(K1) = 1
KDR = 0.5 → Q_key(K1) = 0
```

Pour K2 :

- valeur dans \([0,1]\) ;
- croissance avec \(b_{\mathrm{sec}}\) ;
- rejet d’un niveau négatif.

---

# 23. Erreurs scientifiques à éviter

Il est interdit de :

```text
présenter KDR_max = 0,30 comme une valeur universelle.
```

```text
présenter rho_min = 0,588 comme une mesure de littérature.
```

```text
utiliser automatiquement le domaine [0,0,5] du KDR
tout en conservant des corrélations négatives.
```

```text
appliquer abs(rho_AB) avant la loi de l’arc-sinus.
```

```text
appliquer max(0, rho_AB) dans le modèle nominal.
```

```text
présenter kappa_gb comme une loi fournie par Ruotsalainen.
```

```text
présenter y_rec comme une capacité secrète vis-à-vis de Mallory.
```

```text
utiliser les équations 52 à 54 en ligne
sans connaître KDR_Eve.
```

```text
affirmer qu’un accord faisable garantit l’imprévisibilité.
```

```text
inventer une métrique phi_var dans le code.
```

```text
confondre q_t avec une probabilité de compromission.
```

```text
appeler Q_key une probabilité absolue de sécurité.
```

```text
fixer T_min, epsilon ou b_sec sans les déclarer et les valider.
```

```text
déduire b_sec directement de la taille de la courbe ECC.
```

---

# 24. Limites du modèle de clé

Le modèle initial ne représente pas explicitement :

- l’information observée par Mallory ;
- une capacité secrète conditionnelle ;
- une métrique validée d’entropie temporelle ;
- une attaque active sur le canal ;
- les erreurs réelles de BCH ;
- les fuites exactes de réconciliation ;
- les coûts CPU calibrés de DCT, BCH et SHA-256 ;
- une courbe calibrée \(g_{\mathrm q}\) définitive ;
- les effets complets de la bande de garde ;
- le taux de bits secrets final après amplification ;
- les échecs de protocole ou retransmissions complètes ;
- une valeur validée de \(b_{\mathrm{sec}}\) pour K2.

---

# 25. Résumé de traçabilité de la gestion de clé

```text
KM-EQ44 :
    KDR par loi de l’arc-sinus
    littérature

KM-EQ45 :
    seuil KDR maximal
    politique

KM-EQ46 :
    seuil de corrélation
    dérivé de KM-EQ45

KM-EQ47 :
    mode analytique
    identité avec le KDR brut

KM-EQ48 :
    mode calibré
    fonction à ajuster sur mesures

KM-EQ49 :
    entropie binaire
    définition standard

KM-EQ50 :
    rendement en ligne
    dérivé / calibré

KM-EQ51 :
    nombre de mesures
    dérivé

KM-EQ52 à KM-EQ54 :
    reproduction Ruotsalainen
    littérature hors ligne

KM-EQ55 :
    faisabilité d’accord
    politique

KM-EQ56 :
    faisabilité PHY
    variabilité encore à valider

KM-EQ57 à KM-EQ59 :
    vieillissement de cryptopériode
    politique conservative

KM-EQ60 :
    renouvellement anticipé
    politique

KM-EQ61 :
    expiration dure
    politique

KM-EQ62 à KM-EQ64 :
    échéance de clé
    dérivé / politique

KM-EQ65 à KM-EQ67 :
    indices de qualité/fraîcheur
    proposés pour le Decision Maker
```

---

# 26. Points à valider avant le code définitif de `key_generation.py`

Les éléments suivants restent explicitement ouverts dans le dernier fichier de modélisation :

```text
1. valeur de numerical_epsilon ;
2. valeur de minimum_deadline_s ;
3. niveau security_strength_bits de K2 ;
4. définition de variation_feasible ;
5. courbe calibrée g_q ;
6. nombre et protocole exacts des opérations DCT/BCH/SHA-256 ;
7. harmonisation eta_keep / eta_samp ;
8. harmonisation y_rec / y_sec ;
9. domaine du KDR dans le dictionnaire des variables.
```

Ces points ne bloquent pas la rédaction des fonctions analytiques élémentaires, mais ils doivent rester visibles dans les paramètres et les rapports de validation.

---

---

# 27. Fiches détaillées du modèle d’énergie et de latence

## 27.1. Périmètre énergétique

L’objectif énergétique porte exclusivement sur Alice, le capteur alimenté par batterie.

Le modèle distingue :

```text
énergie de fonctionnement normal
+
surcoût de sécurité associé à la décision
```

Les traitements exécutés chez Bob :

- ne sont pas débités de la batterie d’Alice ;
- peuvent être comptés dans la latence lorsqu’ils bloquent la décision.

Les tentatives de Mallory :

- sont évaluées chez Bob ;
- ne débitent jamais la batterie d’Alice.

---

## CO-EQ68 — Durée d’un symbole LoRa

### Expression officielle

\[
\boxed{
T_{\mathrm{sym}}
=
\frac{2^{SF}}{BW}
}
\]

### Variables

| Variable | Signification | Unité |
|---|---|---|
| \(SF\) | facteur d’étalement | entier |
| \(BW\) | bande passante | Hz |
| \(T_{\mathrm{sym}}\) | durée d’un symbole | s |

### Nature scientifique

```text
Relation provenant du calcul de paquet LoRa Semtech.
```

### Conditions

\[
SF>0
\]

\[
BW>0
\]

### Module

```text
energy_latency.py
```

### Fonction

```python
compute_lora_symbol_time_s(
    spreading_factor,
    bandwidth_hz
) -> float
```

### Exemple nominal

Pour :

\[
SF=12
\]

et :

\[
BW=125000\ \mathrm{Hz}
\]

on obtient :

\[
T_{\mathrm{sym}}
=
\frac{4096}{125000}
=
0{,}032768\ \mathrm{s}
\]

soit :

```text
32,768 ms
```

---

## CO-EQ69 — Temps de préambule

### Expression officielle

\[
\boxed{
T_{\mathrm{pre}}
=
\left(
N_{\mathrm{pre}}
+
4{,}25
\right)
T_{\mathrm{sym}}
}
\]

### Variables

| Variable | Signification | Unité |
|---|---|---|
| \(N_{\mathrm{pre}}\) | nombre de symboles de préambule programmés | symboles |
| \(T_{\mathrm{sym}}\) | durée d’un symbole | s |
| \(T_{\mathrm{pre}}\) | durée du préambule | s |

### Fonction

```python
compute_lora_preamble_time_s(
    preamble_symbols,
    symbol_time_s
) -> float
```

### Paramètre nominal

\[
N_{\mathrm{pre}}=8
\]

### Exemple nominal

\[
T_{\mathrm{pre}}
=
(8+4{,}25)
\times
0{,}032768
\]

\[
T_{\mathrm{pre}}
=
0{,}401408\ \mathrm{s}
\]

---

## CO-EQ70 — Terme intermédiaire du payload

### Expression officielle

\[
\boxed{
\Xi(M)
=
\left\lceil
\frac{
8M
-
4SF
+
28
+
16CRC
-
20IH
}{
4(SF-2DE)
}
\right\rceil
}
\]

### Variables

| Variable | Signification | Domaine |
|---|---|---|
| \(M\) | charge utile | octets |
| \(SF\) | facteur d’étalement | entier |
| \(CRC\) | CRC activé | \(\{0,1\}\) |
| \(IH\) | en-tête implicite | \(\{0,1\}\) |
| \(DE\) | optimisation bas débit | \(\{0,1\}\) |

### Interprétation des indicateurs

```text
CRC = 1 :
    CRC activé

CRC = 0 :
    CRC désactivé
```

```text
IH = 1 :
    en-tête implicite

IH = 0 :
    en-tête explicite
```

```text
DE = 1 :
    optimisation bas débit activée

DE = 0 :
    optimisation bas débit désactivée
```

### Fonction

```python
compute_lora_payload_intermediate(
    payload_bytes,
    spreading_factor,
    crc_enabled,
    implicit_header,
    low_data_rate_optimization
) -> int
```

### Conditions

\[
M\geq0
\]

\[
SF-2DE>0
\]

### Point documentaire à rendre explicite

Le tableau des paramètres fixe :

```text
SF = 12
BW = 125 kHz
CR = 4/5
N_pre = 8
```

mais ne donne pas directement une ligne numérique distincte pour :

```text
CRC
IH
DE
```

Pour reproduire l’intervalle :

\[
T_s=181{,}04\ \mathrm{s}
\]

à 1 % de duty-cycle avec une charge utile de 32 octets, la convention cohérente est :

```text
CRC = 1
IH  = 0
DE  = 1
```

Cette convention doit être ajoutée explicitement dans `parameters.py` et dans le protocole de validation.

---

## CO-EQ71 — Nombre de symboles du payload

### Expression officielle

\[
\boxed{
N_{\mathrm{pl}}
=
8
+
\max
\left\{
0,
\left(
CR_{\mathrm{idx}}
+
4
\right)
\Xi(M)
\right\}
}
\]

### Codage du taux de correction

\[
CR_{\mathrm{idx}}
\in
\{1,2,3,4\}
\]

avec :

| Taux LoRa | \(CR_{\mathrm{idx}}\) |
|---|---:|
| \(4/5\) | 1 |
| \(4/6\) | 2 |
| \(4/7\) | 3 |
| \(4/8\) | 4 |

### Règle importante

Il ne faut pas transmettre directement la fraction :

```text
4/5
```

à la formule lorsqu’elle attend l’indice entier :

```text
1
```

### Fonction

```python
compute_lora_payload_symbols(
    payload_intermediate,
    coding_rate_index
) -> int
```

### Paramètre nominal

```text
coding_rate_index = 1
```

---

## CO-EQ72 — Time-on-Air LoRa

### Expression officielle

\[
\boxed{
T_{\mathrm{air}}(M)
=
T_{\mathrm{pre}}
+
N_{\mathrm{pl}}
T_{\mathrm{sym}}
}
\]

### Nature scientifique

```text
Calcul Semtech du temps de paquet LoRa.
```

### Entrées

```text
payload_bytes
spreading_factor
bandwidth_hz
preamble_symbols
crc_enabled
implicit_header
low_data_rate_optimization
coding_rate_index
```

### Sortie

```text
airtime_s
```

### Fonction principale

```python
compute_lora_airtime_s(
    payload_bytes,
    spreading_factor,
    bandwidth_hz,
    preamble_symbols,
    crc_enabled,
    implicit_header,
    low_data_rate_optimization,
    coding_rate_index
) -> float
```

### Exemple de validation nominal

Avec :

```text
M       = 32 octets
SF      = 12
BW      = 125000 Hz
N_pre   = 8
CRC     = 1
IH      = 0
DE      = 1
CR_idx  = 1
```

on obtient :

\[
\Xi(32)=7
\]

\[
N_{\mathrm{pl}}=43
\]

\[
T_{\mathrm{air}}(32)
=
1{,}810432\ \mathrm{s}
\]

À 1 % de duty-cycle :

\[
\frac{
T_{\mathrm{air}}(32)
}{
0{,}01
}
=
181{,}0432\ \mathrm{s}
\]

ce qui reproduit le paramètre :

\[
T_s
\approx
181{,}04\ \mathrm{s}
\]

### Autres valeurs de test avec la même configuration

Pour une charge de 8 octets :

\[
T_{\mathrm{air}}(8)
=
0{,}991232\ \mathrm{s}
\]

Pour une charge de 40 octets :

\[
T_{\mathrm{air}}(40)
=
1{,}974272\ \mathrm{s}
\]

Ces valeurs constituent des cas tests, pas des constantes universelles.

---

## CO-EQ73 — Énergie de transmission

### Expression officielle

\[
\boxed{
E_{\mathrm{tx}}(M)
=
V_{DD}
I_{\mathrm{tx}}
T_{\mathrm{air}}(M)
}
\]

### Variables

| Variable | Unité |
|---|---|
| \(V_{DD}\) | V |
| \(I_{\mathrm{tx}}\) | A |
| \(T_{\mathrm{air}}\) | s |
| \(E_{\mathrm{tx}}\) | J |

### Nature scientifique

```text
Dérivé de E = VIT.
```

### Fonction

```python
compute_tx_energy_j(
    payload_bytes,
    supply_voltage_v,
    tx_current_a,
    lora_parameters
) -> float
```

Une version élémentaire peut recevoir directement `airtime_s`.

### Paramètres nominaux

\[
V_{DD}=3{,}3\ \mathrm{V}
\]

\[
I_{\mathrm{tx}}=29\ \mathrm{mA}
=
0{,}029\ \mathrm{A}
\]

### Exemple nominal

Pour 32 octets :

\[
E_{\mathrm{tx}}(32)
=
3{,}3
\times
0{,}029
\times
1{,}810432
\]

\[
E_{\mathrm{tx}}(32)
\approx
0{,}173258\ \mathrm{J}
\]

---

## CO-EQ74 — Énergie de réception

### Expression officielle

\[
\boxed{
E_{\mathrm{rx}}(M)
=
V_{DD}
I_{\mathrm{rx}}
T_{\mathrm{air}}(M)
}
\]

### Nature scientifique

```text
Dérivé de E = VIT.
```

### Fonction

```python
compute_rx_energy_j(
    payload_bytes,
    supply_voltage_v,
    rx_current_a,
    lora_parameters
) -> float
```

### Paramètre nominal

\[
I_{\mathrm{rx}}
=
10{,}8\ \mathrm{mA}
=
0{,}0108\ \mathrm{A}
\]

### Exemple nominal

Pour 32 octets :

\[
E_{\mathrm{rx}}(32)
\approx
0{,}064524\ \mathrm{J}
\]

### Limite

Les courants dépendent du mode exact du SX1276. Ils ne doivent pas être transférés à une autre puissance, une autre sortie RF ou une autre configuration sans vérification de datasheet.

---

## CO-EQ75 — Énergie CPU

### Expression officielle

\[
\boxed{
E_{\mathrm{cpu}}
\left(
N_{\mathrm{cyc}}
\right)
=
N_{\mathrm{cyc}}
\frac{
V_{DD}
I_{\mathrm{cpu}}
}{
f_{\mathrm{CPU}}
}
}
\]

### Dérivation

La durée du calcul est :

\[
T_{\mathrm{cpu}}
=
\frac{
N_{\mathrm{cyc}}
}{
f_{\mathrm{CPU}}
}
\]

puis :

\[
E_{\mathrm{cpu}}
=
V_{DD}
I_{\mathrm{cpu}}
T_{\mathrm{cpu}}
\]

### Nature scientifique

```text
Dérivé.
```

### Fonction

```python
compute_cpu_energy_j(
    cycle_count,
    supply_voltage_v,
    cpu_current_a,
    cpu_frequency_hz
) -> float
```

### Fonction temporelle associée

```python
compute_cpu_time_s(
    cycle_count,
    cpu_frequency_hz
) -> float
```

### Paramètres nominaux

\[
I_{\mathrm{cpu}}
=
5{,}92\ \mathrm{mA}
\]

\[
f_{\mathrm{CPU}}
=
32\ \mathrm{MHz}
\]

### Limite

L’équation suppose un courant actif approximativement constant.

Elle doit être remplacée ou calibrée par une mesure si le courant dépend fortement :

- de la fréquence ;
- de la mémoire ;
- des périphériques ;
- du mode d’alimentation ;
- de l’implémentation logicielle.

---

## CO-EQ76 — Énergie totale d’une période

### Expression officielle

\[
\boxed{
E_t(D)
=
E_{\mathrm{base},t}
+
E_t^{\mathrm{sec}}(D)
}
\]

### Signification

Le Decision Maker ne compare pas seulement le surcoût cryptographique. L’autonomie de mission dépend du fonctionnement complet d’Alice.

### Fonction

```python
compute_total_energy_j(
    base_energy_j,
    security_energy_j
) -> float
```

### Conditions

\[
E_{\mathrm{base},t}\geq0
\]

\[
E_t^{\mathrm{sec}}(D)\geq0
\]

### Contrainte batterie associée

\[
E_t(D)
\leq
B_t-B_{\min}
\]

---

## CO-EQ77 — Énergie de base d’une période

### Expression officielle

\[
\boxed{
E_{\mathrm{base},t}
=
E_{\mathrm{sens}}
+
E_{\mathrm{app}}
+
E_{\mathrm{tx}}(M_{\mathrm{data}})
+
E_{\mathrm{RXwin}}
+
E_{\mathrm{sleep}}
}
\]

### Composantes

```text
E_sens :
    acquisition de la grandeur physique

E_app :
    traitement applicatif

E_tx(M_data) :
    transmission normale du message

E_RXwin :
    fenêtres de réception LoRaWAN Classe A

E_sleep :
    veille entre les activités
```

### Nature scientifique

```text
Bilan construit pour le scénario.
```

### Fonction

```python
compute_base_energy_j(
    sensing_energy_j,
    application_energy_j,
    data_tx_energy_j,
    receive_windows_energy_j,
    sleep_energy_j
) -> float
```

### Paramètres encore à mesurer ou documenter

Le modèle ne donne pas encore une valeur finale universelle pour :

```text
sensing_energy_j
application_energy_j
receive_windows_energy_j
```

La veille doit inclure explicitement, selon le protocole retenu :

- sommeil radio ;
- sommeil MCU avec RTC ;
- fuite équivalente de la pile ;
- durée réelle de veille.

### Règle d’interprétation

Une simulation qui ne renseigne pas correctement \(E_{\mathrm{base},t}\) ne peut pas annoncer une autonomie absolue crédible.

Elle peut seulement comparer des surcoûts de sécurité.

---

## CO-EQ78 — Surcoût énergétique de A1

### Expression officielle

\[
\boxed{
E^{\mathrm{sec}}(A_1)
=
E_{\mathrm{MAC}}
+
E_{\mathrm{tx}}
\left(
M_{\mathrm{data}}
+
M_{\mathrm{tag}}
\right)
-
E_{\mathrm{tx}}
\left(
M_{\mathrm{data}}
\right)
}
\]

### Interprétation

La transmission normale de \(M_{\mathrm{data}}\) est déjà comptée dans \(E_{\mathrm{base}}\).

A1 ajoute seulement :

- le calcul du MAC ;
- l’augmentation du Time-on-Air due au tag.

### Énergie du MAC

Lorsque le coût est exprimé en cycles :

\[
E_{\mathrm{MAC}}
=
E_{\mathrm{cpu}}
\left(
C_{\mathrm{MAC}}
\right)
\]

### Paramètres nominaux

\[
M_{\mathrm{data}}=32\ \mathrm{octets}
\]

\[
M_{\mathrm{tag}}=8\ \mathrm{octets}
\]

### Paramètre à profiler

\[
C_{\mathrm{MAC}}
=
\text{à profiler}
\]

La valeur doit correspondre à l’implémentation AES-CMAC réellement retenue sur STM32L1.

### Fonction

```python
compute_a1_energy_j(
    data_payload_bytes,
    mac_tag_bytes,
    mac_energy_j,
    radio_parameters
) -> float
```

### Exemple de surcharge radio nominale

Avec la configuration LoRa de référence :

\[
T_{\mathrm{air}}(40)
-
T_{\mathrm{air}}(32)
=
0{,}16384\ \mathrm{s}
\]

La surcharge énergétique TX correspondante est approximativement :

\[
0{,}0156795\ \mathrm{J}
\]

à laquelle il faut ajouter \(E_{\mathrm{MAC}}\).

### Limite

Cette équation suppose que le tag est ajouté à la même trame.

Une trame de tag séparée constitue un autre protocole.

---

## CO-EQ79 — Latence d’authentification de A1

### Expression officielle

\[
\boxed{
L^{\mathrm{auth}}(A_1)
=
T_{\mathrm{MAC}}
+
T_{\mathrm{air}}
\left(
M_{\mathrm{data}}
+
M_{\mathrm{tag}}
\right)
-
T_{\mathrm{air}}
\left(
M_{\mathrm{data}}
\right)
}
\]

avec :

\[
T_{\mathrm{MAC}}
=
\frac{
C_{\mathrm{MAC}}
}{
f_{\mathrm{CPU}}
}
\]

lorsque le nombre de cycles est utilisé.

### Fonction

```python
compute_a1_latency_s(
    data_payload_bytes,
    mac_tag_bytes,
    mac_time_s,
    lora_parameters
) -> float
```

### Nature scientifique

```text
Bilan différentiel dérivé du format de paquet.
```

---

## CO-EQ80 — Énergie du défi–réponse

### Expression officielle

\[
\boxed{
E_{\mathrm{CR}}
=
E_{\mathrm{rx}}
\left(
M_{\mathrm{chal}}
\right)
+
E_{\mathrm{MAC}}
+
E_{\mathrm{tx}}
\left(
M_{\mathrm{resp}}
\right)
}
\]

### Déroulement chez Alice

```text
1. réception du défi ;
2. calcul du MAC ;
3. transmission de la réponse.
```

### Paramètres nominaux

\[
M_{\mathrm{chal}}=8\ \mathrm{octets}
\]

\[
M_{\mathrm{resp}}=8\ \mathrm{octets}
\]

### Fonction

```python
compute_challenge_response_energy_j(
    challenge_bytes,
    response_bytes,
    mac_energy_j,
    radio_parameters
) -> float
```

### Exemple radio nominal hors MAC

Avec la configuration LoRa de référence :

\[
E_{\mathrm{rx}}(8)
\approx
0{,}035328\ \mathrm{J}
\]

\[
E_{\mathrm{tx}}(8)
\approx
0{,}094861\ \mathrm{J}
\]

donc :

\[
E_{\mathrm{CR}}
\approx
0{,}130188\ \mathrm{J}
+
E_{\mathrm{MAC}}
\]

### Latence du défi–réponse

Le symbole :

\[
L_{\mathrm{CR}}
\]

est utilisé dans le modèle, mais sa décomposition complète n’est pas donnée sous la forme d’une équation numérotée.

Il doit être construit à partir du protocole exact, par exemple en explicitant séparément :

- temps de réception du défi ;
- temps MAC ;
- temps de transmission de la réponse ;
- temps de retournement ;
- délais imposés par les fenêtres LoRaWAN ;
- éventuelles attentes protocolaires.

Il est interdit d’inventer une constante cachée pour \(L_{\mathrm{CR}}\).

---

## CO-EQ81 — Surcoût énergétique attendu de A2

### Expression officielle

\[
\boxed{
E_t^{\mathrm{sec}}(A_2)
=
\mathrm{FRR}(\theta)
E_{\mathrm{CR}}
}
\]

### Nature scientifique

```text
Espérance pour un trafic légitime.
```

### Interprétation

Chez Alice :

- si Bob accepte l’empreinte, le surcoût RFF incrémental est nul ;
- si Bob rejette Alice à tort, le défi–réponse est exécuté.

La probabilité de ce repli légitime est :

\[
p_{\mathrm{fb},t}^{(A)}
=
\mathrm{FRR}(\theta)
\]

### Fonction

```python
compute_a2_expected_energy_j(
    false_rejection_rate,
    challenge_response_energy_j
) -> float
```

### Pire cas énergétique

Pour une contrainte prudente ou une analyse de pic :

\[
E_{\mathrm{A2,worst}}
=
E_{\mathrm{CR}}
\]

Le résultat doit conserver simultanément :

```text
expected_energy_j
worst_case_energy_j
```

---

## CO-EQ82 — Latence attendue de A2

### Expression officielle

\[
\boxed{
L_t^{\mathrm{auth}}(A_2)
=
T_{\mathrm{RFF,Bob}}
+
\mathrm{FRR}(\theta)
L_{\mathrm{CR}}
}
\]

### Paramètre nominal

\[
T_{\mathrm{RFF,Bob}}
=
1{,}84\ \mathrm{ms}
\]

Cette valeur provient d’un point de comparaison TinyRFNet sur Raspberry Pi. Elle reste :

```text
littérature / scénario
```

et non :

```text
temps universel de RFF
```

### Fonction

```python
compute_a2_expected_latency_s(
    rff_processing_time_bob_s,
    false_rejection_rate,
    challenge_response_latency_s
) -> float
```

### Pire cas pour l’admissibilité

\[
\boxed{
L_{\mathrm{A2,worst}}
=
T_{\mathrm{RFF,Bob}}
+
L_{\mathrm{CR}}
}
\]

La contrainte de délai doit utiliser ce majorant prudent lorsque le repli est possible.

### Séparation fondamentale

```text
FRR :
    augmente le coût et la latence légitimes de A2

FAR :
    dégrade la robustesse de sécurité de A2
```

---

## CO-EQ83 — Coût de K0

### Expressions officielles

\[
\boxed{
E^{\mathrm{sec}}(K_0)=0
}
\]

\[
\boxed{
L^{\mathrm{key}}(K_0)=0
}
\]

### Signification

K0 conserve la clé courante sans lancer de renouvellement.

### Fonction

```python
compute_k0_cost() -> KeyCost
```

### Règle

Le coût nul n’autorise pas K0 lorsque :

- le renouvellement est requis ;
- la clé est expirée ;
- une compromission est suspectée.

L’admissibilité logique est traitée par le Decision Maker.

---

## CO-EQ84 — Énergie de réconciliation et d’amplification

### Expression officielle

\[
\boxed{
E_{\mathrm{rec+PA}}
=
E_{\mathrm{cpu}}
\left(
N_{\mathrm{raw}}
C_{\mathrm{rec/bit}}
\right)
+
E_{\mathrm{msg,rec}}
+
E_{\mathrm{cpu}}
\left(
C_{\mathrm{PA}}
\right)
}
\]

### Variables

| Variable | Signification |
|---|---|
| \(N_{\mathrm{raw}}\) | nombre de bits bruts traités |
| \(C_{\mathrm{rec/bit}}\) | cycles de réconciliation par bit |
| \(E_{\mathrm{msg,rec}}\) | énergie des messages de réconciliation |
| \(C_{\mathrm{PA}}\) | cycles d’amplification de confidentialité |

### Nature scientifique

```text
Bilan dérivé.
```

### Paramètres à profiler

```text
C_rec_per_bit
C_PA
```

La littérature justifie BCH et SHA-256, mais ne fournit pas un coût universel en cycles pour STM32L1.

### Paramètre protocolaire à définir

```text
E_msg_rec
```

Ce coût doit être calculé à partir :

- du nombre réel de messages ;
- de leur taille ;
- de leur direction ;
- du Time-on-Air ;
- du rôle exact d’Alice.

### Fonction

```python
compute_reconciliation_energy_j(
    raw_bit_count,
    reconciliation_cycles_per_bit,
    reconciliation_message_energy_j,
    privacy_amplification_cycles,
    cpu_parameters
) -> float
```

---

## CO-EQ85 — Latence de réconciliation et d’amplification

### Expression officielle

\[
\boxed{
L_{\mathrm{rec+PA}}
=
\frac{
N_{\mathrm{raw}}
C_{\mathrm{rec/bit}}
}{
f_{\mathrm{CPU}}
}
+
L_{\mathrm{msg,rec}}
+
\frac{
C_{\mathrm{PA}}
}{
f_{\mathrm{CPU}}
}
}
\]

### Variables

```text
L_msg_rec :
    latence des messages de réconciliation
```

### Fonction

```python
compute_reconciliation_latency_s(
    raw_bit_count,
    reconciliation_cycles_per_bit,
    reconciliation_message_latency_s,
    privacy_amplification_cycles,
    cpu_frequency_hz
) -> float
```

### Point à valider

Le modèle ne donne pas encore une valeur finale de :

```text
raw_bit_count
reconciliation_message_energy_j
reconciliation_message_latency_s
```

Ces paramètres doivent être dérivés du protocole de quantification et de réconciliation effectivement implémenté.

---

## CO-EQ86 — Énergie de K1b

### Expression officielle

\[
\boxed{
E(K_{1b})
=
N_{\mathrm{meas},t}
E_{\mathrm{probe}}
+
E_{\mathrm{rec+PA}}
}
\]

### Signification

K1b utilise des sondages dédiés supplémentaires.

Son coût dépend fortement du nombre de mesures calculé dans KM-EQ51.

### Fonction

```python
compute_k1b_energy_j(
    required_measurements,
    probe_energy_j,
    reconciliation_energy_j
) -> float
```

### Propriété

À coûts unitaires fixes :

\[
E(K_{1b})
\]

augmente linéairement avec :

\[
N_{\mathrm{meas},t}
\]

---

## CO-EQ87 — Énergie d’un sondage dédié

### Expression officielle

\[
\boxed{
E_{\mathrm{probe}}
=
E_{\mathrm{tx}}
\left(
M_{\mathrm{probe}}
\right)
+
E_{\mathrm{rx}}
\left(
M_{\mathrm{probe}}
\right)
}
\]

### Paramètre nominal

\[
M_{\mathrm{probe}}
=
32\ \mathrm{octets}
\]

### Fonction

```python
compute_probe_energy_j(
    probe_payload_bytes,
    radio_parameters
) -> float
```

### Interprétation

La formule représente, pour Alice, une émission et une réception associées à un sondage.

Si le protocole final utilise :

- des tailles asymétriques ;
- plusieurs réponses ;
- un ACK différent ;
- des fenêtres supplémentaires ;

la formule doit être adaptée explicitement.

### Exemple nominal

\[
E_{\mathrm{probe}}
\approx
0{,}173258
+
0{,}064524
\]

\[
E_{\mathrm{probe}}
\approx
0{,}237782\ \mathrm{J}
\]

hors coûts CPU ou protocolaires supplémentaires.

---

## CO-EQ88 — Latence de K1b

### Expression officielle

\[
\boxed{
L^{\mathrm{key}}(K_{1b})
=
N_{\mathrm{meas},t}
T_s
+
L_{\mathrm{rec+PA}}
}
\]

### Paramètre nominal

\[
T_s
=
181{,}04\ \mathrm{s}
\]

### Fonction

```python
compute_k1b_latency_s(
    required_measurements,
    dedicated_probe_interval_s,
    reconciliation_latency_s
) -> float
```

### Interprétation

K1b consomme plus d’énergie que K1a, mais son délai est gouverné par l’intervalle dédié plutôt que par la période des messages applicatifs.

---

## CO-EQ89 — Énergie de K1a

### Expression officielle

\[
\boxed{
E(K_{1a})
=
E_{\mathrm{rec+PA}}
}
\]

### Hypothèse indispensable

Le coût incrémental du sondage est nul uniquement si :

- les trames de données existent déjà dans \(E_{\mathrm{base}}\) ;
- les ACK ou fenêtres utilisés existent déjà dans le fonctionnement normal ;
- aucun paquet supplémentaire n’est généré pour mesurer le canal.

### Fonction

```python
compute_k1a_energy_j(
    reconciliation_energy_j,
    opportunistic_packets_already_in_base
) -> float
```

### Règle

Si :

```text
opportunistic_packets_already_in_base = False
```

la formule nominale ne peut pas être utilisée sans ajouter les coûts radio manquants.

---

## CO-EQ90 — Latence de K1a

### Expression officielle

\[
\boxed{
L^{\mathrm{key}}(K_{1a})
=
N_{\mathrm{meas},t}
T_{\mathrm{msg}}
+
L_{\mathrm{rec+PA}}
}
\]

### Paramètre nominal

\[
T_{\mathrm{msg}}
=
60\ \mathrm{s}
\]

### Fonction

```python
compute_k1a_latency_s(
    required_measurements,
    message_period_s,
    reconciliation_latency_s
) -> float
```

### Interprétation

K1a peut être énergétiquement avantageuse, mais elle attend les échanges normaux du réseau pour accumuler les mesures.

---

## CO-EQ91 — Énergie de K2

### Expression officielle

\[
\boxed{
E(K_2)
=
\sum_{r\in\mathcal O_{\mathrm{ECC}}}
E_r
+
\sum_u
E_{\mathrm{tx}}(M_u)
+
\sum_v
E_{\mathrm{rx}}(M_v)
}
\]

### Signification

Le coût complet de K2 doit additionner :

- chaque opération ECC réellement exécutée par Alice ;
- chaque trame émise par Alice ;
- chaque trame reçue par Alice.

### Nature scientifique

```text
Bilan du protocole.
```

### Ancrages externes disponibles

Le modèle mentionne, pour une signature secp192r1 sur CC2538 :

\[
E_{\mathrm{ECC,sign}}
\approx
0{,}019\ \mathrm{J}
\]

\[
T_{\mathrm{ECC,sign}}
\approx
0{,}218\ \mathrm{s}
\]

Ces valeurs représentent une signature ECC, pas un protocole complet de renouvellement LoRaWAN.

### Fonction

```python
compute_k2_energy_j(
    ecc_operation_energies_j,
    transmitted_payloads_bytes,
    received_payloads_bytes,
    radio_parameters
) -> float
```

### Latence de K2

Le fichier de modélisation ne fournit pas une équation numérotée complète pour :

\[
L^{\mathrm{key}}(K_2)
\]

La fonction d’implémentation doit toutefois la calculer à partir du protocole exact :

```text
somme des temps ECC
+
somme des Time-on-Air TX/RX
+
délais de fenêtre ou d’attente
```

Une signature de 218 ms ne doit pas être utilisée seule comme latence complète de K2.

### Paramètres à valider avant résultats définitifs

```text
nombre d’opérations ECC
type de chaque opération
tailles des messages TX
tailles des messages RX
ordre du protocole
délais LoRaWAN associés
```

---

## CO-EQ92 — Objectif de latence normalisée

### Expression officielle

\[
\boxed{
L_t(D)
=
\max
\left\{
\frac{
L_t^{\mathrm{auth}}(D)
}{
L_{\max}(\sigma_t)
},
\frac{
L_t^{\mathrm{key}}(D)
}{
T_t^{\mathrm{deadline}}
}
\right\}
}
\]

### Objectif

La latence bloquante d’authentification et le délai différé de production de clé utilisent des budgets différents.

La normalisation évite de les additionner directement.

### Variables

| Variable | Signification |
|---|---|
| \(L_t^{\mathrm{auth}}(D)\) | délai bloquant de l’authentification |
| \(L_{\max}(\sigma_t)\) | budget d’authentification selon la criticité |
| \(L_t^{\mathrm{key}}(D)\) | délai de production de la clé |
| \(T_t^{\mathrm{deadline}}\) | temps restant avant expiration |
| \(L_t(D)\) | objectif temporel normalisé |

### Paramètres nominaux

Pour un message critique :

\[
L_{\max}(1)=5\ \mathrm{s}
\]

Pour un message normal :

\[
L_{\max}(0)=600\ \mathrm{s}
\]

### Nature scientifique

```text
Politique de cette étude.
```

### Fonction

```python
compute_normalized_latency(
    authentication_latency_s,
    authentication_budget_s,
    key_latency_s,
    key_deadline_s
) -> float
```

### Propriété

Si les deux budgets sont respectés :

\[
L_t(D)\leq1
\]

Réciproquement, si :

\[
L_t(D)>1
\]

au moins un budget est dépassé.

### Conditions numériques

\[
L_{\max}(\sigma_t)>0
\]

\[
T_t^{\mathrm{deadline}}>0
\]

---

# 28. Combinaison des coûts d’une décision conjointe

Une décision est :

\[
D=(A_j,K_i)
\]

Le modèle donne séparément les coûts d’authentification et de gestion de clé.

Pour l’implémentation, le surcoût de décision peut être assemblé par :

```text
security_energy(D)
=
authentication_security_energy(A_j)
+
key_management_energy(K_i)
```

et les deux latences restent séparées :

```text
authentication_latency(D)
key_latency(D)
```

Cette addition énergétique est un bilan d’implémentation, pas une nouvelle équation publiée.

Avant de l’utiliser, il faut vérifier qu’une même opération n’est pas comptée deux fois, notamment :

- transmission normale déjà incluse dans \(E_{\mathrm{base}}\) ;
- ACK déjà inclus dans les fenêtres normales ;
- MAC éventuellement partagé ;
- messages de réconciliation ;
- fenêtres RX communes ;
- renouvellement ECC et authentification A1 simultanés.

### Fonction

```python
combine_decision_costs(
    authentication_cost,
    key_cost,
    base_energy_j
) -> CostMetrics
```

### Sorties minimales

```text
base_energy_j
authentication_security_energy_j
key_security_energy_j
security_energy_j
total_energy_j
authentication_latency_s
key_latency_s
normalized_latency
expected_energy_j
worst_case_energy_j
airtime_s
```

---

# 29. Paramètres nominaux d’énergie et de latence

| Paramètre | Symbole | Valeur | Statut |
|---|---:|---:|---|
| tension | \(V_{DD}\) | 3,3 V | datasheet |
| courant TX | \(I_{\mathrm{tx}}\) | 29 mA | datasheet |
| courant RX | \(I_{\mathrm{rx}}\) | 10,8 mA | datasheet |
| sommeil radio | \(I_{\mathrm{sleep,radio}}\) | 0,2 µA | datasheet |
| courant CPU | \(I_{\mathrm{cpu}}\) | 5,92 mA | datasheet/dérivé |
| fréquence CPU | \(f_{\mathrm{CPU}}\) | 32 MHz | datasheet |
| sommeil MCU + RTC | \(I_{\mathrm{sleep,MCU}}\) | 1,4 µA | datasheet |
| fuite pile | \(I_{\mathrm{leak}}\) | 2,7 µA | dérivé |
| bande | \(BW\) | 125 kHz | littérature |
| spreading factor | \(SF\) | 12 | littérature |
| coding rate | \(CR\) | 4/5 | scénario |
| indice coding rate | \(CR_{\mathrm{idx}}\) | 1 | dérivé du protocole |
| préambule | \(N_{\mathrm{pre}}\) | 8 symboles | datasheet/scénario |
| duty-cycle | \(\delta_{\mathrm{duty}}\) | 1 % | littérature/scénario |
| payload données | \(M_{\mathrm{data}}\) | 32 octets | littérature |
| tag MAC | \(M_{\mathrm{tag}}\) | 8 octets | politique |
| sondage | \(M_{\mathrm{probe}}\) | 32 octets | littérature/scénario |
| défi | \(M_{\mathrm{chal}}\) | 8 octets | politique |
| réponse | \(M_{\mathrm{resp}}\) | 8 octets | politique |
| temps RFF Bob | \(T_{\mathrm{RFF,Bob}}\) | 1,84 ms | littérature/scénario |
| intervalle dédié | \(T_s\) | 181,04 s | dérivé |
| période message | \(T_{\mathrm{msg}}\) | 60 s | scénario |
| énergie signature ECC | \(E_{\mathrm{ECC,sign}}\) | 0,019 J | littérature/ancrage |
| temps signature ECC | \(T_{\mathrm{ECC,sign}}\) | 0,218 s | littérature/ancrage |
| délai critique | \(L_{\max}(1)\) | 5 s | politique |
| délai normal | \(L_{\max}(0)\) | 600 s | politique |

---

# 30. Paramètres encore à profiler ou à définir

Les résultats énergétiques définitifs exigent encore :

```text
C_MAC
C_rec_per_bit
C_PA
N_raw
E_msg_rec
L_msg_rec
E_sens
E_app
E_RXwin
E_sleep
L_CR
protocole complet de K2
latence complète de K2
```

Les conventions LoRa suivantes doivent également être inscrites explicitement dans `parameters.py` :

```text
CRC
IH
DE
```

Pour reproduire le cas nominal de 181,04 s :

```text
CRC = 1
IH  = 0
DE  = 1
```

Toute valeur encore `à profiler` ou `à valider` :

- peut servir à une simulation exploratoire ;
- doit être signalée dans les résultats ;
- ne peut pas soutenir une affirmation d’autonomie absolue définitive.

---

# 31. Interfaces officielles de `energy_latency.py`

```python
compute_lora_symbol_time_s(
    spreading_factor,
    bandwidth_hz
) -> float
```

```python
compute_lora_preamble_time_s(
    preamble_symbols,
    symbol_time_s
) -> float
```

```python
compute_lora_payload_intermediate(
    payload_bytes,
    spreading_factor,
    crc_enabled,
    implicit_header,
    low_data_rate_optimization
) -> int
```

```python
compute_lora_payload_symbols(
    payload_intermediate,
    coding_rate_index
) -> int
```

```python
compute_lora_airtime_s(
    payload_bytes,
    spreading_factor,
    bandwidth_hz,
    preamble_symbols,
    crc_enabled,
    implicit_header,
    low_data_rate_optimization,
    coding_rate_index
) -> float
```

```python
compute_tx_energy_j(
    payload_bytes,
    supply_voltage_v,
    tx_current_a,
    lora_parameters
) -> float
```

```python
compute_rx_energy_j(
    payload_bytes,
    supply_voltage_v,
    rx_current_a,
    lora_parameters
) -> float
```

```python
compute_cpu_time_s(
    cycle_count,
    cpu_frequency_hz
) -> float
```

```python
compute_cpu_energy_j(
    cycle_count,
    supply_voltage_v,
    cpu_current_a,
    cpu_frequency_hz
) -> float
```

```python
compute_base_energy_j(
    sensing_energy_j,
    application_energy_j,
    data_tx_energy_j,
    receive_windows_energy_j,
    sleep_energy_j
) -> float
```

```python
compute_a1_energy_j(
    data_payload_bytes,
    mac_tag_bytes,
    mac_energy_j,
    radio_parameters
) -> float
```

```python
compute_a1_latency_s(
    data_payload_bytes,
    mac_tag_bytes,
    mac_time_s,
    lora_parameters
) -> float
```

```python
compute_challenge_response_energy_j(
    challenge_bytes,
    response_bytes,
    mac_energy_j,
    radio_parameters
) -> float
```

```python
compute_a2_expected_energy_j(
    false_rejection_rate,
    challenge_response_energy_j
) -> float
```

```python
compute_a2_expected_latency_s(
    rff_processing_time_bob_s,
    false_rejection_rate,
    challenge_response_latency_s
) -> float
```

```python
compute_reconciliation_energy_j(
    raw_bit_count,
    reconciliation_cycles_per_bit,
    reconciliation_message_energy_j,
    privacy_amplification_cycles,
    cpu_parameters
) -> float
```

```python
compute_reconciliation_latency_s(
    raw_bit_count,
    reconciliation_cycles_per_bit,
    reconciliation_message_latency_s,
    privacy_amplification_cycles,
    cpu_frequency_hz
) -> float
```

```python
compute_probe_energy_j(
    probe_payload_bytes,
    radio_parameters
) -> float
```

```python
compute_k0_cost() -> KeyCost
```

```python
compute_k1a_cost(
    required_measurements,
    message_period_s,
    reconciliation_energy_j,
    reconciliation_latency_s,
    opportunistic_packets_already_in_base
) -> KeyCost
```

```python
compute_k1b_cost(
    required_measurements,
    probe_energy_j,
    dedicated_probe_interval_s,
    reconciliation_energy_j,
    reconciliation_latency_s
) -> KeyCost
```

```python
compute_k2_cost(
    ecc_operation_energies_j,
    ecc_operation_times_s,
    transmitted_payloads_bytes,
    received_payloads_bytes,
    protocol_waits_s,
    radio_parameters
) -> KeyCost
```

```python
compute_total_energy_j(
    base_energy_j,
    security_energy_j
) -> float
```

```python
compute_normalized_latency(
    authentication_latency_s,
    authentication_budget_s,
    key_latency_s,
    key_deadline_s
) -> float
```

```python
combine_decision_costs(
    authentication_cost,
    key_cost,
    base_energy_j
) -> CostMetrics
```

---

# 32. Tests officiels d’énergie et de latence

## 32.1. Tests du Time-on-Air

Reproduire avec la configuration nominale :

| Payload | Time-on-Air attendu |
|---:|---:|
| 8 octets | 0,991232 s |
| 32 octets | 1,810432 s |
| 40 octets | 1,974272 s |

Vérifier :

```text
T_air(40) > T_air(32) > T_air(8)
```

Vérifier aussi :

```text
T_air(32) / 0.01 ≈ 181.0432 s
```

## 32.2. Tests radio

- énergie TX positive ;
- énergie RX positive ;
- croissance avec le Time-on-Air ;
- croissance avec le courant ;
- croissance avec la tension ;
- cohérence manuelle avec \(E=VIT\).

## 32.3. Tests CPU

- zéro cycle donne zéro joule et zéro seconde ;
- doublement des cycles double énergie et temps ;
- fréquence plus élevée réduit le temps dans ce modèle ;
- courant plus élevé augmente l’énergie ;
- fréquence nulle rejetée.

## 32.4. Tests A1

- surcoût radio égal à la différence 40 octets moins 32 octets ;
- ajout correct de l’énergie MAC ;
- ajout correct du temps MAC ;
- aucune double comptabilisation de la trame de données.

## 32.5. Tests A2

```text
FRR = 0
→ énergie attendue = 0
→ latence attendue = T_RFF,Bob
```

```text
FRR = 1
→ énergie attendue = E_CR
→ latence attendue = T_RFF,Bob + L_CR
```

Vérifier :

```text
expected <= worst_case
```

## 32.6. Tests K0

```text
énergie = 0
latence = 0
```

## 32.7. Tests K1a

- énergie égale à la réconciliation lorsque les paquets sont déjà dans la base ;
- latence croissante avec \(N_{\mathrm{meas}}\) ;
- refus de l’hypothèse gratuite lorsque les paquets n’existent pas déjà.

## 32.8. Tests K1b

- énergie croissante linéairement avec \(N_{\mathrm{meas}}\) ;
- latence croissante linéairement avec \(N_{\mathrm{meas}}\) ;
- coût d’un sondage égal à TX + RX.

## 32.9. Tests K2

- somme correcte des opérations ECC ;
- somme correcte des messages TX/RX ;
- aucune interprétation de 0,019 J comme protocole complet ;
- aucune interprétation de 0,218 s comme latence complète.

## 32.10. Tests de latence normalisée

```text
auth_ratio = 0.4
key_ratio = 0.7
→ L_t = 0.7
```

```text
auth_ratio = 1.2
key_ratio = 0.8
→ L_t = 1.2
```

Vérifier l’équivalence :

```text
L_t <= 1
si et seulement si
les deux budgets sont respectés
```

---

# 33. Erreurs scientifiques à éviter

Il est interdit de :

```text
annoncer l’autonomie avec le seul surcoût de sécurité.
```

```text
compter l’énergie de Bob dans la batterie d’Alice.
```

```text
compter une tentative de Mallory dans l’énergie d’Alice.
```

```text
utiliser une valeur de courant provenant d’un autre mode radio.
```

```text
confondre le coding rate 4/5 avec CR_idx = 4/5.
```

```text
laisser CRC, IH ou DE implicites dans un test de reproduction.
```

```text
compter deux fois la transmission normale M_data dans A1.
```

```text
présenter E_sec(A2) comme un pire cas alors qu’il s’agit d’une espérance.
```

```text
utiliser la FAR à la place de la FRR dans le coût légitime de A2.
```

```text
utiliser la FRR comme métrique de robustesse contre Mallory.
```

```text
considérer K1a gratuit si les trames ou ACK ne sont pas déjà inclus.
```

```text
utiliser l’énergie d’une signature ECC comme énergie d’un protocole complet K2.
```

```text
utiliser 218 ms comme latence complète de K2.
```

```text
additionner directement L_auth et L_key.
```

```text
cacher les coûts à profiler derrière des valeurs arbitraires.
```

---

# 34. Limites du modèle d’énergie et de latence

Le modèle initial ne représente pas encore complètement :

- la variation du courant pendant une opération CPU ;
- les transitions de modes radio ;
- le coût exact des fenêtres RX1 et RX2 ;
- les collisions ;
- les retransmissions MAC complètes ;
- la congestion ;
- l’ADR ;
- les délais réseau variables ;
- la température de la pile ;
- la chimie détaillée de la pile ;
- la dérive de tension ;
- les coûts mémoire ;
- les interruptions et périphériques ;
- le protocole complet K2 ;
- la taille réelle des messages de réconciliation ;
- les cycles réels de BCH et SHA-256 ;
- les cycles AES-CMAC de l’implémentation finale.

---

# 35. Résumé de traçabilité de l’énergie et de la latence

```text
CO-EQ68 à CO-EQ72 :
    Time-on-Air LoRa
    datasheet Semtech

CO-EQ73 et CO-EQ74 :
    énergie radio
    dérivée de E = VIT

CO-EQ75 :
    énergie CPU
    dérivée du nombre de cycles

CO-EQ76 et CO-EQ77 :
    énergie totale et énergie de base
    bilan du scénario

CO-EQ78 et CO-EQ79 :
    coût différentiel de A1
    dérivé du format de paquet

CO-EQ80 :
    énergie du défi–réponse
    bilan du protocole

CO-EQ81 et CO-EQ82 :
    coûts attendus de A2
    espérances sur trafic légitime

CO-EQ83 :
    coût de K0
    nul par définition

CO-EQ84 et CO-EQ85 :
    réconciliation et amplification
    bilan dérivé, cycles à profiler

CO-EQ86 à CO-EQ88 :
    K1b
    sondages dédiés

CO-EQ89 et CO-EQ90 :
    K1a
    collecte opportuniste

CO-EQ91 :
    K2
    somme des opérations et échanges

CO-EQ92 :
    latence normalisée
    politique de l’étude
```

---

---

# 36. Fiches détaillées de la formulation multi-objectif et du Decision Maker

## 36.1. Rôle du Decision Maker

À chaque période \(t\), le Decision Maker observe un contexte :

\[
\mathbf c_t
\]

puis évalue l’espace fixe :

\[
\mathcal D
=
\{A_1,A_2\}
\times
\{K_0,K_{1a},K_{1b},K_2\}
\]

avec :

\[
|\mathcal D|=8
\]

Le traitement suit strictement l’ordre suivant :

```text
1. construire le contexte ;
2. calculer les métriques scientifiques ;
3. évaluer les huit décisions ;
4. appliquer les règles de raisonnement ;
5. appliquer les contraintes physiques, de ressources et de sécurité ;
6. construire l’ensemble admissible ;
7. calculer le front de Pareto exact ;
8. appliquer la scalarisation de Tchebychev ;
9. appliquer le bris d’égalité ;
10. retourner une décision unique ou un refus motivé.
```

Le Decision Maker ne doit jamais :

- sélectionner une décision non admissible ;
- cacher un mode de secours ;
- fusionner les quatre objectifs en un score avant le filtrage de Pareto ;
- modifier le contexte pendant l’évaluation des huit décisions.

---

## DM-EQ93 — Vecteur des quatre objectifs

### Expression officielle

Pour toute décision admissible \(D\) :

\[
\boxed{
\mathbf f_t(D)
=
\begin{bmatrix}
E_t(D)
\\[1mm]
L_t(D)
\\[1mm]
-R_t^{\mathrm{auth}}(D)
\\[1mm]
-Q_t^{\mathrm{key}}(D)
\end{bmatrix}
}
\]

### Orientation des objectifs

| Composante | Sens physique | Orientation interne |
|---|---|---|
| \(E_t(D)\) | énergie totale d’Alice | minimiser |
| \(L_t(D)\) | charge temporelle normalisée | minimiser |
| \(R_t^{\mathrm{auth}}(D)\) | robustesse d’authentification | maximiser |
| \(Q_t^{\mathrm{key}}(D)\) | qualité/fraîcheur de clé | maximiser |

Les deux objectifs à maximiser sont multipliés par \(-1\) afin que toutes les composantes du vecteur soient orientées en minimisation.

### Nature scientifique

```text
Formulation multi-objectif de cette étude.
```

### Pourquoi séparer authentification et clé

Les deux indices ne doivent pas être fusionnés avant l’optimisation :

```text
R_auth :
    dépend principalement de la FAR, du SNR RFF
    et de la séparabilité Alice–Mallory

Q_key :
    dépend de la réciprocité, du KDR
    et de l’état de la cryptopériode
```

Une authentification PHY peut être exploitable alors que la génération de clé ne l’est pas, et inversement.

### Entrées

```text
total_energy_j
normalized_latency
authentication_robustness
key_quality
```

### Sortie

```text
objective_vector
```

### Module

```text
decision_maker.py
```

### Fonction

```python
build_objective_vector(
    total_energy_j,
    normalized_latency,
    authentication_robustness,
    key_quality
) -> tuple[float, float, float, float]
```

### Pseudocode

```text
retourner (
    total_energy_j,
    normalized_latency,
    -authentication_robustness,
    -key_quality
)
```

### Conditions

\[
E_t(D)\geq0
\]

\[
L_t(D)\geq0
\]

\[
0\leq R_t^{\mathrm{auth}}(D)\leq1
\]

\[
0\leq Q_t^{\mathrm{key}}(D)\leq1
\]

### Tests

- ordre exact des quatre composantes ;
- signes négatifs sur les deux indices maximisés ;
- rejet des valeurs non finies ;
- conservation des valeurs brutes dans les métriques séparées.

---

# 37. Conditions de raisonnement

Les équations DM-EQ94 à DM-EQ96 ne sont pas des contraintes d’optimisation numériques.

Elles éliminent les décisions qui n’ont pas de sens dans le contexte courant.

Elles doivent être testées avant les contraintes de ressources.

---

## DM-EQ94 — Disponibilité du profil RFF

### Expression officielle

\[
\boxed{
A_2\ \text{sélectionnée}
\Rightarrow
v_t^{\mathrm{RFF}}=1
}
\]

### Interprétation correcte

L’implication signifie :

```text
si une décision utilise A2,
alors le profil RFF d’Alice doit être disponible.
```

Elle ne signifie pas :

```text
si le profil RFF est disponible,
alors A2 doit obligatoirement être choisie.
```

### Variable

\[
v_t^{\mathrm{RFF}}
\in
\{0,1\}
\]

### Motif de rejet

```text
RFF_PROFILE_UNAVAILABLE
```

### Fonction

```python
check_rff_reasoning_rule(
    authentication_action,
    rff_profile_available
) -> tuple[bool, str | None]
```

### Cas

| Action | Profil disponible | Résultat |
|---|---:|---|
| A1 | 0 | autorisée |
| A1 | 1 | autorisée |
| A2 | 0 | rejetée |
| A2 | 1 | autorisée |

---

## DM-EQ95 — Absence de besoin de renouvellement

### Expression officielle

\[
\boxed{
r_t=0
\Rightarrow
K_i=K_0
}
\]

### Interprétation

Dans la formulation actuelle, lorsqu’aucun renouvellement n’est requis, la seule action de gestion de clé cohérente est :

```text
K0
```

Les actions :

```text
K1a
K1b
K2
```

sont alors éliminées avant l’optimisation.

### Motif de rejet

```text
UNNECESSARY_KEY_RENEWAL
```

### Point important

Cette règle est plus restrictive qu’une politique autorisant un renouvellement opportuniste permanent.

Toute relaxation future doit être présentée comme une nouvelle politique et non introduite silencieusement dans le code.

---

## DM-EQ96 — Besoin de renouvellement

### Expression officielle

\[
\boxed{
r_t=1
\Rightarrow
K_i\neq K_0
}
\]

### Interprétation

Lorsque le renouvellement est requis, conserver la clé courante est incohérent.

### Motif de rejet

```text
RENEWAL_REQUIRED_K0_FORBIDDEN
```

### Fonction commune à DM-EQ95 et DM-EQ96

```python
check_key_reasoning_rule(
    key_action,
    renewal_required
) -> tuple[bool, str | None]
```

### Table de vérité

| \(r_t\) | K0 | K1a | K1b | K2 |
|---:|---|---|---|---|
| 0 | autorisée | rejetée | rejetée | rejetée |
| 1 | rejetée | autorisée | autorisée | autorisée |

### Expiration dure

Lorsque :

\[
e_t^{\mathrm{key}}=1
\]

K0 est également interdite.

Dans l’implémentation, l’expiration doit rester enregistrée séparément du déclenchement anticipé.

---

# 38. Contraintes physiques et de ressources

Les équations DM-EQ97 à DM-EQ101 sont appliquées après les règles de raisonnement.

Le coût utilisé dans une contrainte doit être un majorant prudent lorsqu’une action contient un repli aléatoire.

Le code doit donc conserver :

```text
métrique attendue pour l’objectif
métrique prudente pour l’admissibilité
```

---

## DM-EQ97 — Faisabilité PHY des actions K1

### Expression officielle

\[
\boxed{
K_i
\in
\{K_{1a},K_{1b}\}
\Rightarrow
\phi_t^{\mathrm{PHY}}=1
}
\]

### Interprétation

Les actions de génération de clé PHY ne sont admissibles que si la faisabilité PHY est établie.

### Motif de rejet

```text
PHY_KEY_GENERATION_INFEASIBLE
```

### Fonction

```python
check_phy_constraint(
    key_action,
    phy_feasible
) -> tuple[bool, str | None]
```

### Point scientifique non résolu

Le modèle distingue :

\[
\phi_t^{\mathrm{agree}}
\]

et :

\[
\phi_t^{\mathrm{var}}
\]

avec :

\[
\phi_t^{\mathrm{PHY}}
=
\phi_t^{\mathrm{agree}}
\phi_t^{\mathrm{var}}
\]

Tant que la métrique de variabilité n’est pas validée, le code ne doit pas prétendre démontrer une sécurité informationnelle complète.

Une campagne exploratoire supposant :

```text
variation_feasible = True
```

doit le signaler explicitement.

---

## DM-EQ98 — Contrainte de batterie

### Expression officielle

\[
\boxed{
E_t(D)
\leq
B_t-B_{\min}
}
\]

### Variables

| Variable | Signification | Unité |
|---|---|---|
| \(E_t(D)\) | énergie totale de la décision | J |
| \(B_t\) | énergie restante | J |
| \(B_{\min}\) | réserve non consommable | J |

### Paramètres nominaux

\[
B_0
=
28512\ \mathrm{J}
\]

\[
B_{\min}
=
0{,}05B_0
=
1425{,}6\ \mathrm{J}
\]

### Motif de rejet

```text
INSUFFICIENT_BATTERY_ENERGY
```

### Fonction

```python
check_battery_constraint(
    total_energy_j,
    remaining_battery_energy_j,
    minimum_battery_energy_j
) -> tuple[bool, str | None]
```

### Cas frontière

L’égalité est admissible :

\[
E_t(D)
=
B_t-B_{\min}
\]

Après exécution, la batterie atteint exactement la réserve.

### Conditions

\[
B_t\geq B_{\min}
\]

\[
E_t(D)\geq0
\]

---

## DM-EQ99 — Contrainte de délai d’authentification

### Expression officielle

\[
\boxed{
L_t^{\mathrm{auth}}(D)
\leq
L_{\max}(\sigma_t)
}
\]

### Budget selon la criticité

\[
L_{\max}(\sigma_t)
=
\begin{cases}
L_{\max}^{C}, & \sigma_t=1,
\\
L_{\max}^{N}, & \sigma_t=0.
\end{cases}
\]

### Paramètres nominaux

\[
L_{\max}(1)
=
5\ \mathrm{s}
\]

\[
L_{\max}(0)
=
600\ \mathrm{s}
\]

### Motif de rejet

```text
AUTHENTICATION_LATENCY_EXCEEDED
```

### Fonction

```python
check_authentication_latency_constraint(
    prudent_authentication_latency_s,
    criticality,
    critical_latency_budget_s,
    normal_latency_budget_s
) -> tuple[bool, str | None]
```

### Règle prudente pour A2

Pour A2, la contrainte doit utiliser :

\[
T_{\mathrm{RFF,Bob}}
+
L_{\mathrm{CR}}
\]

et non uniquement la latence attendue :

\[
T_{\mathrm{RFF,Bob}}
+
\mathrm{FRR}L_{\mathrm{CR}}
\]

---

## DM-EQ100 — Contrainte d’échéance de clé

### Expression officielle

\[
\boxed{
L_t^{\mathrm{key}}(D)
\leq
T_t^{\mathrm{deadline}}
}
\]

### Interprétation

Le renouvellement doit pouvoir être terminé avant la première limite de cryptopériode.

### Motif de rejet

```text
KEY_RENEWAL_DEADLINE_EXCEEDED
```

### Fonction

```python
check_key_deadline_constraint(
    key_latency_s,
    key_deadline_s
) -> tuple[bool, str | None]
```

### Cas K0

Pour K0 :

\[
L_t^{\mathrm{key}}(K_0)=0
\]

mais K0 peut déjà avoir été rejetée par les règles de raisonnement.

### Cas frontière

L’égalité est admissible.

---

## DM-EQ101 — Contrainte de duty-cycle

### Expression officielle

\[
\boxed{
T_{\mathrm{air},t}(D)
\leq
\tau_t^{\mathrm{duty}}
}
\]

### Variables

- \(T_{\mathrm{air},t}(D)\) : temps d’antenne incrémental ou total pertinent de la décision ;
- \(\tau_t^{\mathrm{duty}}\) : budget d’antenne encore disponible.

### Motif de rejet

```text
DUTY_CYCLE_BUDGET_EXCEEDED
```

### Fonction

```python
check_duty_cycle_constraint(
    prudent_airtime_s,
    remaining_duty_cycle_airtime_s
) -> tuple[bool, str | None]
```

### Règle de comptabilisation

Le temps d’antenne utilisé doit être cohérent avec le bilan énergétique :

- ne pas recompter la trame normale déjà incluse ;
- inclure le tag supplémentaire de A1 ;
- inclure les sondages dédiés de K1b ;
- inclure les échanges supplémentaires de K2 ;
- inclure le pire cas du repli lorsque la contrainte doit être prudente ;
- ne pas attribuer à Alice l’airtime des émissions de Mallory.

---

# 39. Plancher de sécurité

## DM-EQ102 — Contrainte de FAR

### Expression officielle

\[
\boxed{
\mathrm{FAR}_t(D)
\leq
\mathrm{FAR}_{\max}(\sigma_t)
}
\]

avec :

\[
\mathrm{FAR}_{\max}(\sigma_t)
=
\begin{cases}
\mathrm{FAR}_{\max}^{C},
&
\sigma_t=1,
\\[1mm]
\mathrm{FAR}_{\max}^{N},
&
\sigma_t=0.
\end{cases}
\]

### Paramètres nominaux

Pour un message critique :

\[
\mathrm{FAR}_{\max}^{C}
=
0{,}01
\]

Pour un message normal :

\[
\mathrm{FAR}_{\max}^{N}
=
0{,}05
\]

### FAR utilisée par action

Pour A1 :

\[
\boxed{
\mathrm{FAR}_t(A_1)
=
2^{-b_{\mathrm{MAC}}}
}
\]

Pour A2 :

\[
\boxed{
\mathrm{FAR}_t(A_2)
=
F_{\chi'^2_{n_f}(\lambda_{M,t})}(\theta)
}
\]

c’est-à-dire la FAR RFF de AU-EQ33.

### Distinction essentielle

Le plancher DM-EQ102 utilise, conformément au fichier de modélisation :

```text
A2 :
    FAR RFF de l’équation 33
```

La robustesse de l’objectif utilise en revanche la probabilité complète :

\[
P_{\mathrm{FA},t}(A_2)
=
\mathrm{FAR}_t
+
(1-\mathrm{FAR}_t)2^{-b_{\mathrm{MAC}}}
\]

Ces deux grandeurs doivent rester séparées dans le logiciel :

```text
constraint_far
total_false_acceptance_probability
```

### Motif de rejet

```text
FAR_SECURITY_FLOOR_VIOLATED
```

### Fonction

```python
check_far_security_constraint(
    constraint_far,
    criticality,
    critical_far_limit,
    normal_far_limit
) -> tuple[bool, str | None]
```

### Pourquoi l’objectif ne suffit pas

Maximiser \(R_t^{\mathrm{auth}}\) ne garantit pas qu’une décision respecte une valeur minimale acceptable.

Une décision peut être Pareto-efficace tout en restant trop dangereuse.

Le plancher de FAR est donc une contrainte dure, antérieure au front de Pareto.

---

# 40. Ensemble admissible

## DM-EQ103 — Définition de l’ensemble admissible

### Expression officielle

\[
\boxed{
\mathcal A(\mathbf c_t)
=
\left\{
D\in\mathcal D
:
D\ \text{respecte les règles et DM-EQ97 à DM-EQ102}
\right\}
}
\]

### Construction

Une décision appartient à \(\mathcal A(\mathbf c_t)\) si et seulement si :

```text
1. elle respecte DM-EQ94 à DM-EQ96 ;
2. elle respecte la faisabilité PHY si elle utilise K1 ;
3. son énergie respecte la réserve ;
4. sa latence d’authentification respecte le budget ;
5. son délai de clé respecte l’échéance ;
6. son airtime respecte le duty-cycle ;
7. sa FAR respecte le plancher de sécurité.
```

### Fonction

```python
build_admissible_set(
    decision_evaluations,
    context,
    parameters
) -> tuple[list[DecisionEvaluation], list[RejectionRecord]]
```

### Journal des rejets

Chaque décision rejetée doit conserver tous les motifs applicables ou, au minimum, le premier motif selon une convention documentée.

La stratégie recommandée est d’enregistrer tous les motifs numériques après validation des règles logiques.

Structure :

```text
RejectionRecord:
    decision
    stage
    reason_code
    measured_value
    allowed_value
    explanation
```

### Ensemble vide

Si :

\[
\mathcal A(\mathbf c_t)=\varnothing
\]

le Decision Maker doit retourner :

```text
refus de service motivé
```

ou appliquer un mode de secours défini à l’avance.

Le mode de secours :

- doit être paramétré ;
- doit apparaître dans le journal ;
- ne doit pas être une sélection cachée de A1-K2 ;
- doit être distingué d’une décision normale du DM.

### Sorties

```text
admissible_decisions
rejection_journal
refusal_of_service
```

---

# 41. Front de Pareto exact

## DM-EQ104 — Dominance

### Expression officielle

Une décision \(D_a\) domine \(D_b\) si :

\[
\boxed{
D_a\prec D_b
\Longleftrightarrow
\left[
\forall k,\ 
f_{t,k}(D_a)
\leq
f_{t,k}(D_b)
\right]
\land
\left[
\exists k,\ 
f_{t,k}(D_a)
<
f_{t,k}(D_b)
\right]
}
\]

### Interprétation

\(D_a\) :

- n’est moins bonne sur aucun objectif ;
- est strictement meilleure sur au moins un objectif.

### Fonction

```python
dominates(
    objective_vector_a,
    objective_vector_b,
    comparison_tolerance=0.0
) -> bool
```

### Tolérance

L’équation mathématique utilise des comparaisons exactes.

Dans le logiciel, une tolérance numérique peut être nécessaire. Elle doit être :

- déclarée dans les paramètres ;
- identique pour toutes les décisions ;
- suffisamment petite pour ne pas modifier artificiellement le front.

### Propriétés à tester

- une décision ne se domine pas elle-même ;
- si les vecteurs sont identiques, aucune dominance stricte ;
- une amélioration stricte sans dégradation entraîne la dominance ;
- la relation n’est pas généralement totale ;
- la relation doit utiliser les objectifs orientés de DM-EQ93.

---

## DM-EQ105 — Front de Pareto

### Expression officielle

\[
\boxed{
\mathcal P(\mathbf c_t)
=
\left\{
D\in\mathcal A(\mathbf c_t)
:
\nexists
D'\in\mathcal A(\mathbf c_t)
\ \text{tel que}\ 
D'\prec D
\right\}
}
\]

### Fonction

```python
compute_pareto_front(
    admissible_evaluations,
    comparison_tolerance=0.0
) -> list[DecisionEvaluation]
```

### Algorithme exact

```text
front = []

pour chaque décision candidate:
    dominated = False

    pour chaque autre décision:
        si autre domine candidate:
            dominated = True
            arrêter la boucle interne

    si non dominated:
        ajouter candidate au front

retourner front
```

### Complexité

Avec au plus huit décisions :

```text
8 × 7 = 56 comparaisons orientées
```

Une métaheuristique comme NSGA-II n’est pas justifiée.

### Invariants

```text
front ⊆ ensemble admissible
```

```text
front non vide si ensemble admissible non vide
```

```text
aucun membre du front n’est dominé par un autre admissible
```

```text
toute décision admissible hors front est dominée
par au moins une décision admissible
```

---

# 42. Arbitrage par Tchebychev pondéré

## DM-EQ106 — Sélection d’un point unique

### Expression officielle

\[
\boxed{
D_t^\star
=
\arg\min_{D\in\mathcal P(\mathbf c_t)}
\max_k
\left[
w_k(\mathbf c_t)
\frac{
f_{t,k}(D)-f_{t,k}^{\mathrm{id}}
}{
f_{t,k}^{\mathrm{nad}}
-
f_{t,k}^{\mathrm{id}}
+
\varepsilon
}
\right]
}
\]

### Définitions

Pour chaque objectif \(k\), sur l’ensemble utilisé pour l’arbitrage :

\[
f_{t,k}^{\mathrm{id}}
=
\min_{D\in\mathcal P(\mathbf c_t)}
f_{t,k}(D)
\]

\[
f_{t,k}^{\mathrm{nad}}
=
\max_{D\in\mathcal P(\mathbf c_t)}
f_{t,k}(D)
\]

Dans l’implémentation retenue, les points idéal et nadir sont calculés sur le front courant.

### Nature scientifique

```text
Scalarisation multi-objectif par Tchebychev pondéré.
```

### Pourquoi cette méthode

La méthode peut sélectionner des points Pareto non supportés, contrairement à une simple somme pondérée dans certains fronts non convexes.

### Normalisation

Pour chaque décision et objectif :

\[
\widetilde f_{t,k}(D)
=
\frac{
f_{t,k}(D)-f_{t,k}^{\mathrm{id}}
}{
f_{t,k}^{\mathrm{nad}}
-
f_{t,k}^{\mathrm{id}}
+
\varepsilon
}
\]

Puis :

\[
S(D\mid\mathbf c_t)
=
\max_k
\left[
w_k(\mathbf c_t)
\widetilde f_{t,k}(D)
\right]
\]

et :

\[
D_t^\star
=
\arg\min_D
S(D\mid\mathbf c_t)
\]

### Paramètre numérique

\[
\varepsilon>0
\]

évite une division par zéro lorsque le front ne varie pas sur un objectif.

La valeur de \(\varepsilon\) n’est pas fixée dans le tableau final de la modélisation.

Elle doit être déclarée dans `parameters.py` avec le statut :

```text
protection numérique / à valider
```

### Fonctions

```python
compute_ideal_and_nadir_points(
    pareto_front
) -> tuple[tuple[float, ...], tuple[float, ...]]
```

```python
compute_tchebycheff_score(
    objective_vector,
    ideal_point,
    nadir_point,
    contextual_weights,
    numerical_epsilon
) -> float
```

```python
select_tchebycheff_candidate(
    pareto_front,
    contextual_weights,
    numerical_epsilon,
    score_tolerance
) -> list[DecisionEvaluation]
```

La dernière fonction retourne éventuellement plusieurs ex æquo avant le bris d’égalité.

### Cas d’un front à une seule décision

La décision unique est sélectionnée.

Les scores normalisés peuvent être nuls sur tous les objectifs, ce qui est acceptable.

### Tests

- invariance à une translation cohérente des objectifs après normalisation ;
- score non négatif ;
- sélection du score minimal ;
- gestion d’un dénominateur nul ;
- gestion d’un front à une décision ;
- vérification manuelle sur un petit exemple.

---

# 43. Poids contextuels

## DM-EQ107 — Contraintes sur les poids

### Expression officielle

\[
\boxed{
w_k(\mathbf c_t)\geq0
}
\]

\[
\boxed{
\sum_k
w_k(\mathbf c_t)
=
1
}
\]

### Ordre des poids

La convention logicielle est :

```text
energy
latency
authentication
key
```

soit :

\[
\mathbf w(\mathbf c_t)
=
\begin{bmatrix}
w_E &
w_L &
w_{\mathrm{auth}} &
w_{\mathrm{key}}
\end{bmatrix}
\]

### Nature scientifique

```text
Politique du Decision Maker.
```

### Point bloquant

Le fichier de modélisation interdit de coder des coefficients numériques arbitraires avant validation par l’encadrante.

La documentation ne doit donc pas inventer une formule comme :

```text
w_E = 0.4
w_L = 0.2
w_auth = 0.2
w_key = 0.2
```

sans table de politique validée.

### Fonction

```python
compute_contextual_weights(
    context,
    validated_weight_policy
) -> tuple[float, float, float, float]
```

### Validation

La fonction doit vérifier :

- chaque poids est fini ;
- chaque poids est positif ou nul ;
- la somme vaut 1 à la tolérance ;
- l’ordre des poids correspond à DM-EQ93 ;
- la politique possède un identifiant/version ;
- les poids utilisés sont enregistrés dans le résultat.

---

## DM-EQ108 — Monotonie liée à la batterie

### Expression officielle

\[
\boxed{
B_t\downarrow
\Rightarrow
w_E\uparrow
}
\]

### Nature

```text
Exigence qualitative de politique.
```

### Interprétation

À contextes identiques par ailleurs, une batterie plus faible ne doit pas réduire le poids de l’énergie.

### Test de politique

Pour deux contextes ne différant que par la batterie :

```text
si B_low < B_high
alors w_E(B_low) >= w_E(B_high)
```

La relation n’impose pas encore la forme fonctionnelle exacte.

---

## DM-EQ109 — Monotonie liée à la criticité

### Expression officielle

\[
\boxed{
\sigma_t=1
\Rightarrow
w_{\mathrm{auth}}\uparrow,
\quad
w_L\uparrow
}
\]

### Interprétation

Un message critique doit accorder davantage d’importance :

- à la robustesse d’authentification ;
- à la latence bloquante.

### Test de politique

À contexte identique par ailleurs :

```text
w_auth(critical) >= w_auth(normal)
w_latency(critical) >= w_latency(normal)
```

La redistribution nécessaire pour maintenir une somme égale à 1 doit être définie par la table de politique validée.

---

## DM-EQ110 — Monotonie liée au vieillissement de la clé

### Expression officielle

\[
\boxed{
q_t\uparrow
\Rightarrow
w_{\mathrm{key}}\uparrow
}
\]

### Interprétation

Plus la cryptopériode est consommée, plus la qualité/fraîcheur de la clé doit peser dans l’arbitrage.

### Test de politique

À contexte identique par ailleurs :

```text
si q_old > q_fresh
alors w_key(q_old) >= w_key(q_fresh)
```

### Limite

Les équations DM-EQ108 à DM-EQ110 décrivent des monotonies, pas des coefficients numériques.

Une politique est validée seulement si elle respecte simultanément :

- positivité ;
- somme égale à 1 ;
- monotonie batterie ;
- monotonie criticité ;
- monotonie vieillissement.

---

# 44. Bris d’égalité

Le bris d’égalité n’est pas numéroté dans les équations 93 à 110, mais il fait partie du contrat officiel du Decision Maker.

Lorsque plusieurs décisions ont des scores égaux à une tolérance :

\[
\varepsilon_S
\]

l’ordre est :

```text
1. plus faible FAR ;
2. plus faible énergie ;
3. plus faible latence bloquante ;
4. ordre lexicographique des actions.
```

## 44.1. FAR utilisée pour le bris

La modélisation indique « plus faible FAR ».

La convention cohérente avec la contrainte est :

```text
A1 :
    2^(-b_MAC)

A2 :
    FAR RFF
```

La probabilité totale d’usurpation A2 reste disponible comme métrique explicative.

Cette convention doit être conservée dans la documentation du code.

## 44.2. Latence bloquante

La latence bloquante utilisée est :

\[
L_t^{\mathrm{auth}}(D)
\]

et non l’objectif normalisé complet \(L_t(D)\), puisque le texte précise « latence bloquante ».

## 44.3. Ordre lexicographique

L’ordre recommandé, cohérent avec l’espace de décisions, est :

```text
A1-K0
A1-K1a
A1-K1b
A1-K2
A2-K0
A2-K1a
A2-K1b
A2-K2
```

Cet ordre doit être centralisé et testé.

## 44.4. Paramètre non fixé

La valeur numérique de :

\[
\varepsilon_S
\]

n’est pas fixée dans le tableau final.

Elle doit être déclarée avec le statut :

```text
tolérance numérique / à valider
```

## 44.5. Fonction

```python
break_decision_tie(
    tied_evaluations,
    score_tolerance
) -> DecisionEvaluation
```

---

# 45. Fonctionnement complet du Decision Maker

## 45.1. Entrées

```text
Context
SimulationParameters
huit décisions
métriques de canal
état de clé
politique de poids validée
```

## 45.2. Sorties

```text
décision D_t^*
ou refus motivé

métriques de la décision
ensemble admissible
front de Pareto
journal des rejets
poids
points idéal et nadir
scores Tchebychev
explication du choix
```

## 45.3. Pseudocode officiel détaillé

```text
fonction run_decision_maker(
    context,
    parameters,
    validated_weight_policy
):

    vérifier que le contexte est valide
    construire les huit décisions

    all_evaluations = []
    admissible_evaluations = []
    rejection_journal = []

    pour chaque décision D:

        vérifier les règles de raisonnement

        si une règle est violée:
            enregistrer le rejet
            ajouter l’évaluation à all_evaluations
            continuer

        évaluer l’action d’authentification
        évaluer l’action de gestion de clé
        calculer les coûts attendus
        calculer les coûts prudents
        calculer R_auth
        calculer Q_key
        calculer le vecteur objectif

        vérifier:
            faisabilité PHY
            batterie
            délai d’authentification
            échéance de clé
            duty-cycle
            plancher de FAR

        enregistrer tous les motifs de rejet

        si aucune contrainte n’est violée:
            marquer la décision admissible
            ajouter aux admissibles

        ajouter l’évaluation à all_evaluations

    si aucune décision n’est admissible:
        retourner:
            refus motivé
            all_evaluations
            rejection_journal

    calculer le front de Pareto exact

    calculer les poids contextuels validés
    vérifier les poids et leurs monotonies

    calculer le point idéal
    calculer le point nadir

    calculer le score Tchebychev de chaque décision du front

    construire la liste des meilleurs scores
    dans la tolérance epsilon_S

    si plusieurs décisions restent:
        appliquer le bris d’égalité

    construire une explication complète

    retourner DecisionMakerResult
```

---

# 46. Données enregistrées pour l’explicabilité

Chaque décision doit être explicable par quatre objets fondamentaux :

```text
1. contexte observé ;
2. motifs de rejet ;
3. front de Pareto ;
4. score final.
```

Le résultat complet doit également conserver :

```text
métriques scientifiques brutes
coûts attendus
coûts prudents
vecteur objectif
poids contextuels
point idéal
point nadir
ordre du bris d’égalité
version de la politique
```

### Structure recommandée

```text
DecisionMakerResult:
    context
    all_evaluations
    admissible_evaluations
    pareto_front
    rejection_journal
    contextual_weights
    ideal_point
    nadir_point
    tchebycheff_scores
    selected_evaluation
    refusal_of_service
    fallback_mode_used
    explanation
```

---

# 47. Paramètres nominaux du Decision Maker

| Paramètre | Valeur | Statut |
|---|---:|---|
| décisions | 8 | définition |
| réserve batterie | \(5\%\ de\ B_0\) | politique |
| délai critique | 5 s | politique |
| délai normal | 600 s | politique |
| FAR critique max | 1 % | politique |
| FAR normale max | 5 % | littérature/politique |
| \(q_{\mathrm{trig}}\) | 0,60 | politique |
| \(\mathrm{KDR}_{\max}\) | 0,30 | politique |
| \(\varepsilon\) Tchebychev | à fixer | protection numérique |
| \(\varepsilon_S\) | à fixer | tolérance numérique |
| poids contextuels | à valider | politique |
| mode de secours | à définir explicitement | politique |

---

# 48. Interfaces officielles de `decision_maker.py`

```python
build_decision_space() -> tuple[Decision, ...]
```

```python
build_objective_vector(
    total_energy_j,
    normalized_latency,
    authentication_robustness,
    key_quality
) -> tuple[float, float, float, float]
```

```python
check_reasoning_rules(
    decision,
    context
) -> list[RejectionRecord]
```

```python
check_phy_constraint(
    key_action,
    phy_feasible
) -> tuple[bool, str | None]
```

```python
check_battery_constraint(
    total_energy_j,
    remaining_battery_energy_j,
    minimum_battery_energy_j
) -> tuple[bool, str | None]
```

```python
check_authentication_latency_constraint(
    prudent_authentication_latency_s,
    criticality,
    critical_latency_budget_s,
    normal_latency_budget_s
) -> tuple[bool, str | None]
```

```python
check_key_deadline_constraint(
    key_latency_s,
    key_deadline_s
) -> tuple[bool, str | None]
```

```python
check_duty_cycle_constraint(
    prudent_airtime_s,
    remaining_duty_cycle_airtime_s
) -> tuple[bool, str | None]
```

```python
check_far_security_constraint(
    constraint_far,
    criticality,
    critical_far_limit,
    normal_far_limit
) -> tuple[bool, str | None]
```

```python
build_admissible_set(
    decision_evaluations,
    context,
    parameters
) -> tuple[list[DecisionEvaluation], list[RejectionRecord]]
```

```python
dominates(
    objective_vector_a,
    objective_vector_b,
    comparison_tolerance
) -> bool
```

```python
compute_pareto_front(
    admissible_evaluations,
    comparison_tolerance
) -> list[DecisionEvaluation]
```

```python
compute_contextual_weights(
    context,
    validated_weight_policy
) -> tuple[float, float, float, float]
```

```python
validate_contextual_weights(
    weights,
    tolerance
) -> None
```

```python
compute_ideal_and_nadir_points(
    pareto_front
) -> tuple[tuple[float, ...], tuple[float, ...]]
```

```python
compute_tchebycheff_score(
    objective_vector,
    ideal_point,
    nadir_point,
    contextual_weights,
    numerical_epsilon
) -> float
```

```python
break_decision_tie(
    tied_evaluations,
    score_tolerance
) -> DecisionEvaluation
```

```python
run_decision_maker(
    context,
    parameters,
    validated_weight_policy
) -> DecisionMakerResult
```

---

# 49. Tests officiels du Decision Maker

## 49.1. Espace des décisions

Vérifier :

```text
exactement 8 décisions
aucun doublon
ordre stable
```

## 49.2. Règles de raisonnement

Tester toute la table :

```text
A1/A2 × profil RFF disponible/indisponible
K0/K1a/K1b/K2 × renouvellement requis/non requis
```

## 49.3. Contraintes physiques

Pour chaque contrainte :

```text
valeur inférieure au seuil → admissible
valeur égale au seuil      → admissible
valeur supérieure au seuil → rejetée
```

## 49.4. FAR selon la criticité

```text
message normal :
    limite = 0.05

message critique :
    limite = 0.01
```

Tester une décision admissible en normal mais rejetée en critique.

## 49.5. A1 et A2

Vérifier :

```text
A1 :
    constraint_far = 2^(-b_MAC)

A2 :
    constraint_far = FAR RFF
    robustness utilise P_FA total
```

## 49.6. Ensemble admissible vide

Construire un contexte où toutes les décisions sont rejetées.

Vérifier :

- refus de service ;
- aucune décision cachée ;
- journal non vide ;
- explication complète.

## 49.7. Dominance

Cas obligatoires :

```text
vecteurs identiques :
    aucune dominance

amélioration stricte sur un objectif,
égalité sur les autres :
    dominance

meilleure énergie mais moins bonne sécurité :
    aucune dominance mutuelle
```

## 49.8. Front de Pareto

Comparer le front calculé à un exemple manuel.

Vérifier :

- aucune décision dominée dans le front ;
- chaque admissible hors front est dominée ;
- ordre de sortie reproductible.

## 49.9. Tchebychev

Tester :

- front à une décision ;
- objectif constant sur le front ;
- poids nuls autorisés individuellement ;
- somme des poids égale à 1 ;
- sélection du score minimal ;
- valeurs idéal/nadir correctes ;
- effet de \(\varepsilon\).

## 49.10. Poids contextuels

Tester les monotonies :

```text
batterie plus faible
→ poids énergie non inférieur
```

```text
message critique
→ poids auth et latence non inférieurs
```

```text
q_t plus élevé
→ poids clé non inférieur
```

## 49.11. Bris d’égalité

Construire des égalités successives afin de vérifier :

```text
1. FAR
2. énergie
3. latence bloquante
4. ordre lexicographique
```

## 49.12. Immutabilité du contexte

Vérifier que l’évaluation des huit décisions ne modifie pas :

```text
batterie
âge de clé
compteurs
budget duty-cycle
contexte radio
```

---

# 50. Erreurs scientifiques à éviter

Il est interdit de :

```text
appliquer Pareto avant le filtrage d’admissibilité.
```

```text
appliquer Tchebychev à des décisions rejetées.
```

```text
fusionner R_auth et Q_key en un seul indice de sécurité.
```

```text
utiliser les coûts attendus de A2 comme majorants prudents.
```

```text
utiliser P_FA total de A2 à la place de la FAR RFF
dans DM-EQ102 sans modifier la modélisation.
```

```text
sélectionner automatiquement A1-K2 lorsque l’ensemble admissible est vide.
```

```text
cacher un mode de secours dans une fonction.
```

```text
inventer des poids numériques avant validation.
```

```text
utiliser une somme pondérée à la place de Tchebychev
sans déclarer une variante.
```

```text
utiliser une métaheuristique pour huit décisions.
```

```text
calculer le front sur les métriques non orientées
sans traiter les objectifs à maximiser.
```

```text
mettre à jour la batterie pendant l’évaluation des candidats.
```

```text
comparer des flottants sans tolérance documentée.
```

```text
laisser l’ordre lexicographique dépendre d’un set Python non ordonné.
```

```text
présenter les poids comme une loi physique.
```

---

# 51. Limites et éléments à valider

Avant l’implémentation définitive de l’arbitrage, les éléments suivants restent ouverts :

```text
1. table numérique des poids contextuels ;
2. forme fonctionnelle éventuelle des poids ;
3. valeur de numerical_epsilon pour Tchebychev ;
4. valeur de score_tolerance epsilon_S ;
5. valeur de dominance_tolerance ;
6. mode de secours lorsque A(c_t) est vide ;
7. statut opérationnel de phi_var ;
8. protocole complet de K2 ;
9. coûts encore à profiler ;
10. validation finale des seuils par l’encadrante.
```

Ces éléments doivent être visibles dans `parameters.py`.

Aucun d’eux ne doit être remplacé par une constante silencieuse.

---

# 52. Résumé de traçabilité du Decision Maker

```text
DM-EQ93 :
    vecteur des quatre objectifs
    formulation multi-objectif

DM-EQ94 à DM-EQ96 :
    règles de raisonnement
    politique logique

DM-EQ97 :
    faisabilité PHY des K1
    contrainte physique

DM-EQ98 :
    batterie
    contrainte de ressource

DM-EQ99 :
    délai bloquant
    contrainte QoS

DM-EQ100 :
    échéance de clé
    contrainte de cryptopériode

DM-EQ101 :
    duty-cycle
    contrainte radio

DM-EQ102 :
    plancher de FAR
    garantie minimale de sécurité

DM-EQ103 :
    ensemble admissible
    définition

DM-EQ104 :
    dominance
    optimisation multi-objectif

DM-EQ105 :
    front de Pareto exact
    énumération exhaustive

DM-EQ106 :
    Tchebychev pondéré
    arbitrage d’un point unique

DM-EQ107 :
    positivité et normalisation des poids
    politique

DM-EQ108 :
    batterie basse → poids énergie élevé
    monotonie de politique

DM-EQ109 :
    criticité → poids auth et latence élevés
    monotonie de politique

DM-EQ110 :
    vieillissement → poids clé élevé
    monotonie de politique
```

---

# 53. État final du référentiel des équations

Les familles détaillées sont désormais :

```text
CH-EQ05 à CH-EQ22
    canal radio

AU-EQ23 à AU-EQ43
    authentification physique

KM-EQ44 à KM-EQ67
    génération et gestion de clé

CO-EQ68 à CO-EQ92
    énergie et latence

DM-EQ93 à DM-EQ110
    formulation multi-objectif et Decision Maker
```

Le référentiel couvre ainsi toutes les équations numérotées du modèle scientifique utilisées par les futurs modules Python.

---

# 54. Prochaine étape du projet

Le prochain document à produire intégralement est :

```text
docs/06_SIMULATION_PROTOCOL.md
```

Il devra traduire le protocole scientifique en expériences reproductibles :

- tests unitaires des sous-modèles ;
- balayages déterministes ;
- boucle complète de mission ;
- politiques de référence B1 à B4 ;
- répétitions Monte Carlo ;
- intervalles de confiance ;
- analyse de sensibilité ;
- fichiers et figures attendus ;
- règles de comparaison équitable entre politiques.