# Architecture scientifique et logicielle de PHYSEC-DM

## 1. Statut du document

Ce document est la référence d’architecture du projet **PHYSEC-DM**.

Il est aligné sur les deux sources de vérité suivantes :

```text
modelisation_parametres_modifies(1).tex
modelisation parametre modifié.pdf
```

En cas de contradiction avec une ancienne version de la documentation, le dernier fichier de modélisation prévaut.

---

## 2. But scientifique du système

PHYSEC-DM simule un Decision Maker qui choisit, à chaque période, une décision conjointe :

\[
D_t^\star=(A_j,K_i)
\]

avec :

\[
A_j\in\{A_1,A_2\}
\]

et :

\[
K_i\in\{K_0,K_{1a},K_{1b},K_2\}
\]

Le choix cherche simultanément à :

\[
\min E_t(D),\qquad
\min L_t(D),\qquad
\max R_t^{\mathrm{auth}}(D),\qquad
\max Q_t^{\mathrm{key}}(D)
\]

Le Decision Maker ne doit jamais sélectionner une décision :

- logiquement incohérente ;
- physiquement irréalisable ;
- incompatible avec la batterie ;
- incompatible avec les délais ;
- incompatible avec le duty-cycle ;
- insuffisamment sûre au regard du plancher de FAR.

---

## 3. Acteurs

### 3.1. Alice

Alice est un capteur LoRa alimenté par batterie.

Dans le scénario de base :

- Alice est fixe ;
- elle produit un message légitime toutes les \(T_{\mathrm{msg}}\) secondes ;
- son énergie est la seule énergie optimisée ;
- elle exécute les opérations radio et cryptographiques nécessaires ;
- elle ne paie jamais l’énergie des émissions de Mallory.

### 3.2. Bob

Bob est une passerelle de confiance alimentée sur secteur.

Il :

- reçoit les trames ;
- estime le SNR et le canal ;
- extrait l’empreinte RFF ;
- calcule les métriques scientifiques ;
- héberge le Decision Maker ;
- construit l’ensemble admissible ;
- calcule le front de Pareto ;
- retourne une décision unique.

Les traitements réalisés chez Bob peuvent compter dans la latence lorsqu’ils bloquent la décision, mais pas dans l’énergie d’Alice.

### 3.3. Mallory

Mallory tente d’usurper l’identité d’Alice.

Dans le périmètre initial :

- Mallory est active pour l’usurpation ;
- elle reste passive vis-à-vis de l’estimation du canal ;
- elle ne réalise pas d’attaque de relais ;
- elle ne manipule pas volontairement le canal ;
- elle ne synthétise pas parfaitement l’empreinte d’Alice ;
- sa séparation RFF est représentée par \(d_M\).

Les tentatives de Mallory sont simulées séparément du trafic légitime.

---

## 4. Séparation entre trafic légitime et attaques

À chaque période :

```text
1. Alice produit un message légitime.
2. Le DM choisit une décision pour ce message.
3. Alice paie uniquement les coûts réellement engagés.
4. Une tentative de Mallory est tirée séparément selon p_M.
5. Bob évalue cette tentative sans débiter la batterie d’Alice.
```

Cette séparation est un invariant scientifique du projet.

---

## 5. Espace des décisions

### 5.1. Authentification

```text
A1 : authentification cryptographique conventionnelle par MAC.
A2 : authentification RFF chez Bob, suivie d’un défi–réponse
     cryptographique uniquement en cas de rejet de l’empreinte.
```

### 5.2. Gestion de clé

```text
K0  : conserver la clé courante.
K1a : génération de clé PHY opportuniste à partir des échanges
      déjà présents dans le fonctionnement normal.
K1b : génération de clé PHY par sondages dédiés supplémentaires.
K2  : renouvellement conventionnel par mécanisme ECC.
```

### 5.3. Huit décisions

```text
(A1, K0)
(A1, K1a)
(A1, K1b)
(A1, K2)
(A2, K0)
(A2, K1a)
(A2, K1b)
(A2, K2)
```

---

## 6. Plateforme simulée de référence

La première phase est entièrement réalisée par modélisation et simulation Python.

La plateforme de référence est :

```text
Radio : Semtech SX1276
Bande : EU868
Classe : LoRaWAN Classe A
MCU   : ARM Cortex-M3 / STM32L151xC-A
```

Les courants, tensions et temps provenant des datasheets ou d’articles sont des entrées du modèle. Ils ne sont pas présentés comme des mesures réalisées dans ce travail.

---

## 7. Modules scientifiques officiels

La correspondance officielle issue de la modélisation est :

```text
parameters.py
channel.py
authentication.py
key_generation.py
energy_latency.py
decision_maker.py
mission.py
validation.py
campaign.py
```

Un fichier technique `models.py` peut contenir les structures de données typées. Il ne doit contenir aucune formule scientifique.

---

## 8. Responsabilité de chaque module

### 8.1. `parameters.py`

Responsabilité :

- centraliser tous les paramètres ;
- stocker leur unité ;
- stocker leur statut scientifique ;
- stocker leur provenance ;
- empêcher toute constante cachée ;
- valider les domaines numériques.

Statuts autorisés :

```text
littérature
datasheet
dérivé
calibré
scénario
politique
à valider
```

### 8.2. `channel.py`

Entrées principales :

```text
SNR imposé ou distance
shadowing
fréquence Doppler effective
délai entre sondages
facteur matériel rho_HW
```

Sorties principales :

```text
Gamma_t
gamma_t
rho_time,t
rho_noise,t
rho_AB,t
```

Responsabilité scientifique :

- équations du SNR ;
- modèle log-distance ;
- bilan de liaison ;
- bruit thermique ;
- Clarke–Jakes ;
- dégradation par bruit ;
- modèle composite de réciprocité.

### 8.3. `authentication.py`

Entrées principales :

```text
gamma_t
d_M
theta
b_MAC
paramètres RFF
```

Sorties principales :

```text
FAR
FRR
P_FA(A2)
R_auth(A1)
R_auth(A2)
p_fb^(A)
p_fb^(M)
```

Responsabilité scientifique :

- vecteur CFO–DCO–PO ;
- observation gaussienne ;
- référence d’enrôlement ;
- distance de Mahalanobis ;
- lois chi-deux centrale et non centrale ;
- FAR et FRR ;
- robustesse de A1 et A2 ;
- probabilités de repli.

### 8.4. `key_generation.py`

Entrées principales :

```text
rho_AB,t
kappa_gb
eta_keep
longueur de clé
état de cryptopériode
```

Sorties principales :

```text
KDR_brut
KDR effectif
rendement
N_meas
phi_agree
phi_PHY
q_t
r_t
e_key,t
T_deadline,t
Q_key
```

Responsabilité scientifique :

- loi de l’arc-sinus ;
- modes analytique et calibré ;
- entropie binaire ;
- surrogate de rendement ;
- nombre de mesures ;
- faisabilité d’accord ;
- cryptopériode ;
- qualité/fraîcheur de clé.

### 8.5. `energy_latency.py`

Entrées principales :

```text
actions
tailles de trames
plateforme radio
plateforme CPU
probabilités de repli
nombre de mesures
```

Sorties principales :

```text
T_air
E_tx
E_rx
E_cpu
E_base
E_sec
E_total
L_auth
L_key
L_normalisée
```

Responsabilité scientifique :

- Time-on-Air LoRa ;
- énergie radio et CPU ;
- coût différentiel de A1 ;
- espérance et pire cas de A2 ;
- coûts de K0, K1a, K1b et K2 ;
- objectif temporel normalisé.

### 8.6. `decision_maker.py`

Entrées :

```text
contexte
métriques du canal
métriques d’authentification
métriques de clé
coûts
politique de poids validée
```

Sorties :

```text
ensemble admissible
journal des rejets
front de Pareto
scores
décision D_t^*
ou refus motivé
```

Responsabilité :

- huit décisions ;
- règles de raisonnement ;
- contraintes ;
- plancher de sécurité ;
- Pareto exact ;
- Tchebychev pondéré ;
- bris d’égalité déterministe.

### 8.7. `mission.py`

Responsabilité :

- boucle temporelle de la mission ;
- état de batterie ;
- état de clé ;
- trafic légitime ;
- processus d’attaque séparé ;
- compteurs de mission ;
- refus de service ;
- arrêt lorsque \(B_t\leq B_{\min}\).

### 8.8. `validation.py`

Responsabilité :

- cas tests ;
- reproduction de valeurs de littérature ;
- vérification des unités ;
- tests de monotonie ;
- vérification des bilans ;
- rapports d’écart.

### 8.9. `campaign.py`

Responsabilité :

- balayages déterministes ;
- Monte Carlo ;
- graines communes entre politiques ;
- intervalles de confiance ;
- analyses de sensibilité ;
- figures ;
- tableaux ;
- fichiers de résultats.

---

## 9. Structures de données techniques

Le fichier facultatif `models.py` ne contient que des structures typées.

Structures recommandées :

```text
ParameterRecord
Context
ChannelMetrics
AuthenticationMetrics
KeyMetrics
CostMetrics
Decision
DecisionEvaluation
DecisionMakerResult
MissionState
MissionStepResult
MissionResult
```

Les structures ne doivent pas :

- recalculer les équations ;
- sélectionner une décision ;
- modifier des paramètres ;
- contenir des constantes cachées.

---

## 10. Flux scientifique global

```text
parameters
    ↓
mission construit le contexte c_t
    ↓
channel calcule Gamma_t, gamma_t et rho_AB,t
    ↓
authentication calcule FAR, FRR et R_auth
    ↓
key_generation calcule KDR, faisabilité et Q_key
    ↓
energy_latency calcule énergie et délais
    ↓
decision_maker filtre, construit Pareto et arbitre
    ↓
mission met à jour l’état
    ↓
campaign agrège plusieurs scénarios/répétitions
```

---

## 11. Dépendances autorisées

```text
models.py
    ne dépend d’aucun module scientifique

parameters.py
    peut être importé par tous les modules

channel.py
    dépend de parameters.py et models.py

authentication.py
    dépend de parameters.py et models.py

key_generation.py
    dépend de parameters.py et models.py

energy_latency.py
    dépend de parameters.py et models.py

decision_maker.py
    orchestre les métriques déjà calculées

mission.py
    dépend des modules scientifiques et du Decision Maker

validation.py
    peut appeler les fonctions scientifiques

campaign.py
    appelle mission.py et validation.py
```

---

## 12. Dépendances interdites

```text
parameters.py → decision_maker.py
channel.py → mission.py
authentication.py → decision_maker.py
key_generation.py → mission.py
energy_latency.py → campaign.py
models.py → module scientifique
```

Une fonction scientifique élémentaire ne doit pas appeler le Decision Maker.

---

## 13. Invariants scientifiques

Le logiciel doit toujours respecter les invariants suivants :

```text
Les huit décisions sont évaluées dans le même contexte.
```

```text
Mallory ne débite jamais la batterie d’Alice.
```

```text
Les traitements de Bob ne sont pas comptés dans l’énergie d’Alice.
```

```text
Les corrélations négatives sont conservées dans le modèle nominal.
```

```text
La troncature max(0, rho_AB) est une variante explicite.
```

```text
Une forte corrélation ne prouve pas à elle seule l’entropie du canal.
```

```text
K0 est interdit lorsque la clé est expirée.
```

```text
K1a et K1b exigent la faisabilité PHY.
```

```text
Le front de Pareto ne contient que des décisions admissibles.
```

```text
La décision finale appartient au front de Pareto.
```

```text
Aucune constante numérique n’est cachée dans une fonction.
```

---

## 14. Périmètre exclu de la première version

La première version ne couvre pas explicitement :

- attaque de relais ;
- manipulation active du canal ;
- capacité secrète conditionnelle vis-à-vis de Mallory ;
- consommation énergétique de Bob ;
- congestion complète ;
- collisions ;
- retransmissions MAC complètes ;
- ADR ;
- chimie détaillée de la pile ;
- dépendance complète à la température ;
- preuve d’entropie du canal tant que \(\phi_t^{\mathrm{var}}\) n’est pas validée.

---

## 15. Ordre d’implémentation recommandé

```text
1. models.py
2. parameters.py
3. channel.py
4. validation des équations du canal
5. authentication.py
6. validation FAR/FRR
7. key_generation.py
8. validation KDR/rendement
9. energy_latency.py
10. validation ToA et bilans
11. decision_maker.py
12. validation Pareto/Tchebychev
13. mission.py
14. campaign.py
```

---

## 16. Critère d’acceptation de l’architecture

L’architecture est acceptable si :

- chaque équation possède un module responsable ;
- chaque valeur possède une provenance ;
- les attaques restent séparées du trafic légitime ;
- les huit décisions sont représentables ;
- les quatre objectifs sont calculables ;
- les motifs de rejet sont enregistrés ;
- le refus de service est explicite ;
- aucune dépendance circulaire n’est nécessaire ;
- la simulation est reproductible ;
- les variantes sont séparées du modèle nominal.