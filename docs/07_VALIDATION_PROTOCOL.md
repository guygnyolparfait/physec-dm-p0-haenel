# Protocole complet de validation de PHYSEC-DM

## 1. Objet du document

Ce document définit comment accepter, rejeter ou limiter scientifiquement chaque composant de **PHYSEC-DM** avant l’exploitation des résultats.

Il couvre :

- la validation des paramètres ;
- la validation analytique des équations ;
- la validation numérique des fonctions ;
- la validation statistique des modèles aléatoires ;
- la validation des bilans d’énergie et de latence ;
- la validation logique du Decision Maker ;
- la validation de la simulation de mission ;
- la validation croisée avec les sources ;
- la validation de la reproductibilité ;
- la traçabilité entre équations, code, tests et résultats.

La source scientifique de vérité reste :

```text
modelisation_parametres_modifies(1).tex
modelisation parametre modifié.pdf
```

Le présent document ne crée aucune nouvelle loi physique. Il fixe les preuves minimales nécessaires pour affirmer qu’un module est correctement implémenté dans le domaine de validité du modèle.

---

## 2. Principe de validation

La validation suit la chaîne :

```text
équation
→ hypothèses
→ paramètres
→ fonction
→ test
→ résultat attendu
→ tolérance
→ statut
→ preuve enregistrée
```

Une fonction n’est pas validée parce qu’elle « s’exécute sans erreur ». Elle doit produire un résultat :

- mathématiquement cohérent ;
- numériquement stable ;
- dimensionnellement correct ;
- conforme à la modélisation ;
- reproductible ;
- correctement interprété.

---

## 3. Niveaux de preuve

### Niveau V0 — Présence documentaire

La formule, ses variables, son statut et ses hypothèses sont documentés.

Ce niveau ne prouve pas que le code est correct.

### Niveau V1 — Vérification analytique

La relation est vérifiée par :

- calcul manuel ;
- dérivation ;
- cas particulier ;
- identité mathématique ;
- conservation d’un invariant.

### Niveau V2 — Vérification numérique

La fonction Python reproduit les valeurs analytiques avec une tolérance définie.

### Niveau V3 — Vérification statistique

Pour un modèle aléatoire, les statistiques empiriques sont compatibles avec le modèle théorique.

### Niveau V4 — Validation croisée

Le résultat est comparé à :

- une datasheet ;
- un article ;
- une bibliothèque scientifique fiable ;
- une implémentation indépendante ;
- une valeur de référence du modèle.

### Niveau V5 — Validation de mission

Le composant reste cohérent lorsqu’il est intégré dans le Decision Maker et la boucle de mission.

### Niveau V6 — Validation expérimentale matérielle

Le modèle est comparé à une plateforme réelle.

Ce niveau est hors du périmètre de la première phase de simulation, sauf données externes déjà disponibles.

---

## 4. Statuts officiels de validation

Chaque test ou composant reçoit un statut unique.

```text
NOT_RUN
PASS
PASS_WITH_LIMITATIONS
FAIL
BLOCKED
EXPLORATORY_ONLY
```

### `NOT_RUN`

Le test n’a pas encore été exécuté.

### `PASS`

Tous les critères prévus sont respectés.

### `PASS_WITH_LIMITATIONS`

Le test réussit dans un domaine restreint ou avec une hypothèse explicitement non validée.

Exemple :

```text
accord PHY validé
mais variabilité du canal non validée
```

### `FAIL`

Au moins un critère obligatoire n’est pas respecté.

### `BLOCKED`

Le test ne peut pas être exécuté faute de paramètre, protocole ou donnée.

### `EXPLORATORY_ONLY`

Le résultat repose sur une valeur calibrée ou non validée et ne peut soutenir qu’une analyse exploratoire.

---

## 5. Portes de validation

L’avancement est contrôlé par des portes successives.

### GATE-0 — Documentation

Conditions :

- équation identifiée ;
- statut scientifique défini ;
- variables et unités connues ;
- fonction prévue ;
- tests prévus.

### GATE-1 — Paramètres

Conditions :

- paramètres obligatoires présents ;
- unités valides ;
- domaines valides ;
- provenance enregistrée ;
- paramètres ouverts signalés.

### GATE-2 — Fonctions élémentaires

Conditions :

- tests nominaux ;
- cas limites ;
- erreurs d’entrée ;
- tolérances respectées ;
- invariants respectés.

### GATE-3 — Sous-modèles

Conditions :

- canal validé ;
- authentification validée ;
- gestion de clé validée ;
- énergie/latence validées.

### GATE-4 — Decision Maker

Conditions :

- huit décisions ;
- filtrage correct ;
- Pareto exact ;
- Tchebychev correct ;
- refus explicite ;
- reproductibilité.

### GATE-5 — Mission

Conditions :

- état correctement mis à jour ;
- Mallory séparée ;
- compteurs cohérents ;
- énergie conservée ;
- arrêt cohérent.

### GATE-6 — Campagnes

Conditions :

- graines communes ;
- intervalles de confiance ;
- manifestes ;
- comparaisons équitables ;
- résultats bruts conservés.

### GATE-7 — Résultats scientifiques

Conditions :

- figures et tableaux reproduisibles ;
- limites visibles ;
- paramètres exploratoires identifiés ;
- conclusions compatibles avec les preuves disponibles.

Une porte échouée bloque les étapes qui en dépendent.

---

## 6. Tolérances numériques

Les tolérances sont des paramètres d’ingénierie logicielle. Elles ne sont pas des constantes physiques du modèle.

Elles doivent être centralisées dans `parameters.py` ou une configuration de validation.

### 6.1. Tolérances recommandées de départ

```text
absolute_tolerance_algebraic      = 1e-12
relative_tolerance_algebraic      = 1e-9
absolute_tolerance_special        = 1e-8
absolute_tolerance_probability    = 1e-10
absolute_tolerance_time_s         = 1e-6
absolute_tolerance_energy_j       = 1e-9
weight_sum_tolerance              = 1e-12
dominance_tolerance               = à valider
score_tolerance                   = à valider
```

Ces valeurs sont des valeurs initiales de test logiciel. Elles peuvent être adaptées si une bibliothèque ou une plateforme impose une précision différente.

### 6.2. Comparaison générale

Pour une valeur calculée \(x\) et une référence \(x_{\mathrm{ref}}\) :

\[
e_{\mathrm{abs}}
=
|x-x_{\mathrm{ref}}|
\]

\[
e_{\mathrm{rel}}
=
\frac{
|x-x_{\mathrm{ref}}|
}{
\max(|x_{\mathrm{ref}}|,\epsilon_{\mathrm{scale}})
}
\]

Le test réussit si :

\[
e_{\mathrm{abs}}
\leq
\epsilon_{\mathrm{abs}}
\]

ou :

\[
e_{\mathrm{rel}}
\leq
\epsilon_{\mathrm{rel}}
\]

selon la règle définie pour le test.

### 6.3. Valeurs proches de zéro

Une erreur relative n’est pas pertinente lorsque la référence est proche de zéro.

Utiliser alors une tolérance absolue.

### 6.4. Probabilités extrêmes

Une probabilité comme :

\[
2^{-64}
\]

ne doit pas être validée par Monte Carlo.

Elle doit être validée analytiquement et numériquement par une fonction exponentielle stable.

---

## 7. Validation dimensionnelle

Chaque fonction doit déclarer les unités de ses entrées et sorties.

### 7.1. Règles

```text
Hz × s                    → sans dimension
V × A × s                 → J
cycles / Hz               → s
dBm - dBm                 → dB
probabilité               → sans dimension
corrélation               → sans dimension
```

### 7.2. Erreurs interdites

```text
utiliser des mA comme des A
utiliser des ms comme des s
utiliser des MHz comme des Hz
utiliser le SNR dB dans une formule linéaire
additionner des dBm comme des watts
confondre octets et bits
```

### 7.3. Test automatisé

Les tests doivent vérifier au minimum les conversions :

```text
29 mA = 0,029 A
10,8 mA = 0,0108 A
32 MHz = 32 000 000 Hz
125 kHz = 125 000 Hz
8 octets = 64 bits
```

---

# 8. Validation des paramètres

## 8.1. Enregistrement obligatoire

Chaque paramètre possède :

```text
name
value
unit
status
source
description
sensitivity_range
validated
```

## 8.2. Cohérences croisées

Valider :

\[
b_{\mathrm{MAC}}
=
8M_{\mathrm{tag}}
\]

\[
\rho_{\min}
=
\cos
\left(
\pi KDR_{\max}
\right)
\]

\[
B_{\min}
=
0{,}05B_0
\]

pour la configuration nominale.

Vérifier aussi :

```text
CR = 4/5 correspond à CR_idx = 1
CRC, IH et DE sont explicites
SF et BW sont compatibles avec le cas de référence
les seuils critiques sont au moins aussi stricts que les seuils normaux
```

## 8.3. Paramètres bloquants avant campagne définitive

```text
poids contextuels validés
numerical_epsilon
score_tolerance
dominance_tolerance
mode de secours
minimum_deadline_s
security_strength_bits
protocole K2
coûts CPU profilés
coûts de base
```

Une campagne peut continuer en mode exploratoire, mais pas être présentée comme validation définitive.

---

# 9. Validation du canal radio

## 9.1. SNR et conversions

### Tests

\[
\Gamma=0\ \mathrm{dB}
\Rightarrow
\gamma=1
\]

\[
\Gamma=10\ \mathrm{dB}
\Rightarrow
\gamma=10
\]

\[
\Gamma=-10\ \mathrm{dB}
\Rightarrow
\gamma=0{,}1
\]

Valider l’aller-retour :

\[
\Gamma
\rightarrow
\gamma
\rightarrow
\Gamma
\]

sur une grille couvrant la plage de simulation.

### Critère

Erreur absolue inférieure à la tolérance algébrique adaptée.

---

## 9.2. Modèle log-distance

À :

\[
d=d_0
\]

vérifier :

\[
PL(d)=PL(d_0)
\]

Pour :

\[
d_2>d_1
\]

et :

\[
n_p>0
\]

vérifier :

\[
PL(d_2)>PL(d_1)
\]

### Validation croisée

Comparer à un calcul indépendant ou une feuille de calcul manuelle.

---

## 9.3. Bruit thermique

Avec :

```text
BW = 125000 Hz
NF = 6 dB
```

vérifier une valeur voisine de :

```text
-117 dBm
```

La valeur exacte dépend de l’utilisation de \(-174\ \mathrm{dBm/Hz}\) comme approximation.

### Statut

```text
PASS_WITH_LIMITATIONS
```

si la validation repose sur cette approximation et non sur une température explicitement calculée.

---

## 9.4. Clarke–Jakes

Vérifier :

\[
J_0(0)=1
\]

Vérifier que la fonction :

- peut devenir négative ;
- reste finie ;
- est comparée à une bibliothèque scientifique indépendante.

### Interdiction

Ne pas tronquer ou prendre la valeur absolue dans la fonction nominale.

---

## 9.5. Facteur de bruit

\[
\rho_{\mathrm{noise}}
=
\frac{\gamma}{1+\gamma}
\]

Vérifier :

```text
gamma = 0   → 0
gamma = 1   → 0,5
gamma = 10  → 10/11
```

Vérifier la monotonie sur une grille strictement croissante.

---

## 9.6. Réciprocité composite

\[
\rho_{AB}
=
\rho_{\mathrm{HW}}
\rho_{\mathrm{time}}
\rho_{\mathrm{noise}}
\]

Valider :

- bornes dans \([-1,1]\) ;
- signe identique à \(\rho_{\mathrm{time}}\) lorsque les autres facteurs sont positifs ;
- zéro si un facteur est nul ;
- comparaison manuelle sur plusieurs triplets ;
- distinction entre modèle signé et variante tronquée.

### Statut scientifique

Le produit complet est une construction de l’étude.

La validation doit donc porter sur :

```text
validité de chaque composante
cohérence du produit
sensibilité à rho_HW
compatibilité avec d’éventuelles données
```

et non prétendre qu’une source publie le produit exact.

---

# 10. Validation de l’authentification

## 10.1. Vecteur RFF

Vérifier :

```text
dimension = 3
ordre = CFO, DCO, PO
aucune normalisation cachée
```

## 10.2. Référence d’enrôlement

Comparer la moyenne calculée à une moyenne indépendante.

Tester :

- un échantillon ;
- plusieurs échantillons identiques ;
- un ensemble vide ;
- des dimensions incohérentes.

## 10.3. Mahalanobis

Vérifier :

\[
T=0
\]

si observation et référence sont identiques.

Comparer :

- calcul par résolution linéaire ;
- calcul indépendant avec une bibliothèque ;
- forme générale ;
- forme isotrope.

Le résultat doit être non négatif à la tolérance numérique.

## 10.4. Lois sous Alice et Mallory

### Sous Alice

\[
T\mid H_A
\sim
\chi^2_{n_f}
\]

### Sous Mallory

\[
T\mid H_M
\sim
\chi'^2_{n_f}(\lambda)
\]

Validation statistique :

- moyenne empirique ;
- variance empirique ;
- quantiles ;
- courbe Q–Q ;
- comparaison CDF empirique/théorique.

Un test de Kolmogorov–Smirnov peut être utilisé comme diagnostic, mais ne doit pas constituer l’unique preuve.

## 10.5. FRR

Pour :

\[
n_f=3
\]

et :

\[
\theta
=
F^{-1}_{\chi^2_3}(0{,}95)
\]

vérifier :

\[
FRR
\approx
0{,}05
\]

### Validation statistique

Simuler des observations d’Alice et vérifier que la FRR théorique appartient à l’intervalle de confiance binomial de la FRR empirique.

## 10.6. FAR

Vérifier les monotonies :

```text
lambda augmente → FAR diminue
theta augmente  → FAR augmente
d_M augmente    → FAR diminue
SNR augmente    → FAR diminue
```

### Cas limite

Pour :

\[
\lambda=0
\]

vérifier :

\[
FAR
=
1-FRR
\]

au même seuil.

## 10.7. Seuil nominal

Vérifier :

\[
n_f=3,\quad
\alpha_{\mathrm{FRR}}=0{,}05
\]

\[
\theta
\approx
7{,}8147
\]

Tolérance recommandée :

```text
1e-3
```

pour la valeur affichée, et tolérance plus stricte pour le calcul interne.

## 10.8. Forge MAC

Vérifier analytiquement :

\[
p_{\mathrm{forge}}
=
2^{-64}
\]

La simulation empirique de cette probabilité est interdite car irréaliste.

## 10.9. Robustesse de A2

Vérifier :

\[
P_{\mathrm{FA}}(A_2)
=
FAR
+
(1-FAR)2^{-b_{\mathrm{MAC}}}
\]

Cas limites :

```text
FAR = 0 → P_FA = 2^(-b_MAC)
FAR = 1 → P_FA = 1
b_MAC → grand → P_FA tend vers FAR
```

## 10.10. Coût et sécurité

Vérifier la séparation :

```text
FRR → coût légitime de A2
FAR → sécurité contre Mallory
```

Une fonction qui utilise FAR dans l’énergie légitime ou FRR dans la robustesse contre Mallory échoue la validation.

---

# 11. Validation de la génération et gestion de clé

## 11.1. Loi de l’arc-sinus

Vérifier :

\[
KDR(1)=0
\]

\[
KDR(0{,}6)\approx0{,}295167
\]

\[
KDR(0)=0{,}5
\]

\[
KDR(-1)=1
\]

### Point de cohérence

Le domaine \([0,0{,}5]\) n’est valable que si la corrélation est non négative.

Le modèle nominal conservant les corrélations négatives, la fonction doit accepter un KDR mathématique jusqu’à 1.

## 11.2. Seuil de corrélation

Vérifier :

\[
KDR_{\max}=0{,}30
\]

\[
\rho_{\min}
=
\cos(0{,}30\pi)
\approx0{,}587785
\]

Tester l’équivalence :

\[
KDR\leq0{,}30
\Longleftrightarrow
\rho\geq\rho_{\min}
\]

dans le mode analytique.

## 11.3. Entropie binaire

Vérifier :

\[
h_2(0)=0
\]

\[
h_2(0{,}5)=1
\]

\[
h_2(1)=0
\]

\[
h_2(p)=h_2(1-p)
\]

## 11.4. Rendement

Vérifier :

\[
KDR=0
\Rightarrow
y_{\mathrm{rec}}=\eta_{\mathrm{keep}}
\]

\[
KDR=0{,}5
\Rightarrow
y_{\mathrm{rec}}=0
\]

La monotonie n’est exigée que sur l’intervalle opérationnel :

\[
0\leq KDR\leq0{,}5
\]

## 11.5. Nombre de mesures

Vérifier :

- sortie entière ;
- croissance avec la longueur de clé ;
- décroissance avec le rendement ;
- protection contre la division par zéro ;
- signalement d’un rendement quasi nul.

La protection \(\epsilon\) ne doit pas transformer une situation non faisable en situation acceptable.

## 11.6. Faisabilité d’accord

Cas frontière :

\[
KDR=KDR_{\max}
\Rightarrow
\phi^{\mathrm{agree}}=1
\]

## 11.7. Faisabilité PHY

Vérifier la table booléenne :

| Accord | Variabilité | PHY |
|---:|---:|---:|
| 0 | 0 | 0 |
| 0 | 1 | 0 |
| 1 | 0 | 0 |
| 1 | 1 | 1 |

Tant que la métrique de variabilité n’est pas validée :

```text
statut = PASS_WITH_LIMITATIONS
```

ou :

```text
EXPLORATORY_ONLY
```

selon le scénario.

## 11.8. Cryptopériode

Valider séparément :

- limite d’âge ;
- limite de messages ;
- compromission ;
- déclenchement anticipé ;
- échéance minimale ;
- remise à zéro après renouvellement.

Vérifier que :

\[
q_t
\]

ne diminue pas avant un renouvellement, sauf modification explicite de l’état.

## 11.9. Indices de qualité

Vérifier :

```text
K0 :
    q = 0 → Q = 1
    q = 1 → Q = 0
```

```text
K1 :
    KDR = 0   → Q = 1
    KDR = 0,5 → Q = 0
```

Pour K2, le résultat reste `BLOCKED` ou `EXPLORATORY_ONLY` tant que \(b_{\mathrm{sec}}\) n’est pas validé.

---

# 12. Validation de l’énergie et de la latence

## 12.1. Time-on-Air

Avec :

```text
SF = 12
BW = 125 kHz
CR_idx = 1
N_pre = 8
CRC = 1
IH = 0
DE = 1
```

vérifier :

| Payload | Référence |
|---:|---:|
| 8 octets | 0,991232 s |
| 32 octets | 1,810432 s |
| 40 octets | 1,974272 s |

Tolérance recommandée :

```text
1e-6 s
```

Vérifier aussi :

\[
\frac{T_{\mathrm{air}}(32)}{0{,}01}
\approx181{,}0432\ \mathrm{s}
\]

## 12.2. Énergie radio

Comparer chaque résultat à :

\[
E=VIT
\]

Vérifier :

- linéarité en tension ;
- linéarité en courant ;
- linéarité en temps ;
- utilisation d’ampères et secondes.

## 12.3. Énergie CPU

Vérifier :

\[
N_{\mathrm{cyc}}=0
\Rightarrow
E_{\mathrm{cpu}}=0
\]

et la linéarité en cycles.

## 12.4. Bilan de A1

Construire un bilan manuel :

```text
énergie MAC
+
énergie TX 40 octets
-
énergie TX 32 octets
```

Vérifier l’absence de double comptabilisation du message normal.

## 12.5. Bilan de A2

Cas limites :

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
attendu <= pire cas
```

## 12.6. K1a

Le coût radio incrémental nul n’est accepté que si les trames et ACK sont déjà inclus dans \(E_{\mathrm{base}}\).

Sinon :

```text
FAIL
```

pour le bilan nominal.

## 12.7. K1b

Vérifier la croissance linéaire en :

\[
N_{\mathrm{meas}}
\]

pour l’énergie et la latence à paramètres fixes.

## 12.8. K2

Le coût complet reste :

```text
BLOCKED
```

tant que le protocole exact, le nombre d’opérations et les messages ne sont pas fixés.

Les valeurs :

```text
0,019 J
218 ms
```

ne valident qu’un ancrage de signature ECC, pas K2 complet.

## 12.9. Énergie de base

Une autonomie absolue ne peut être validée tant que :

```text
E_sens
E_app
E_RXwin
E_sleep
```

ne sont pas documentés ou mesurés.

Le résultat doit alors être :

```text
PASS_WITH_LIMITATIONS
```

pour les comparaisons relatives, et non `PASS` pour l’autonomie absolue.

---

# 13. Validation du Decision Maker

## 13.1. Espace de décisions

Vérifier exactement :

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

Aucun doublon, aucun élément manquant.

## 13.2. Oracle de règles logiques

Construire une table de vérité indépendante du code du DM.

Comparer chaque sortie du DM à cet oracle.

## 13.3. Contraintes

Pour chaque contrainte, tester :

```text
seuil - delta
seuil exact
seuil + delta
```

L’égalité doit être admissible pour les équations utilisant \(\leq\).

## 13.4. FAR de contrainte et robustesse

Valider que deux champs distincts existent :

```text
constraint_far
total_false_acceptance_probability
```

Pour A2 :

```text
constraint_far = FAR RFF
robustesse = 1 - P_FA total
```

## 13.5. Ensemble admissible

Comparer la sortie à une construction manuelle sur plusieurs contextes contrôlés.

Tout candidat admissible doit respecter toutes les règles et contraintes.

## 13.6. Dominance

Utiliser un oracle brut indépendant :

```text
toutes les comparaisons paire par paire
```

Vérifier :

- identité ;
- dominance stricte ;
- compromis sans dominance ;
- tolérance.

## 13.7. Front de Pareto

Comparer le front du code à l’oracle indépendant.

Critère :

```text
mêmes identifiants de décisions
```

L’ordre peut être normalisé avant comparaison.

## 13.8. Tchebychev

Valider sur un exemple manuel comportant :

- au moins trois points ;
- quatre objectifs ;
- un objectif constant ;
- des poids non uniformes.

Vérifier :

- point idéal ;
- point nadir ;
- normalisation ;
- score maximal pondéré ;
- minimum final.

## 13.9. Poids

Tant que la table n’est pas validée :

```text
statut global du choix final = EXPLORATORY_ONLY
```

Même si le Pareto est correct.

## 13.10. Bris d’égalité

Valider les quatre niveaux successifs :

```text
FAR
énergie
latence bloquante
ordre lexicographique
```

## 13.11. Ensemble vide

Le DM doit retourner :

```text
refusal_of_service = True
selected_evaluation = None
```

sauf mode de secours explicitement activé.

Un choix caché provoque un `FAIL`.

## 13.12. Immutabilité

Avant et après l’évaluation des huit décisions, comparer le contexte.

Toute modification de :

```text
batterie
âge de clé
compteurs
SNR
duty-cycle
```

pendant l’évaluation provoque un `FAIL`.

---

# 14. Validation de la mission

## 14.1. Conservation de l’énergie

Pour chaque période :

\[
B_{t+1}
=
B_t
-
E_{\mathrm{débitée},t}
\]

sauf événement explicitement modélisé de recharge, absent du scénario nominal.

Vérifier :

```text
B_t non croissante
B_t >= 0
débit >= 0
```

## 14.2. Séparation Mallory

Pour toute attaque :

```text
energy_debited_from_alice_for_mallory = 0
```

Un seul contre-exemple provoque un `FAIL`.

## 14.3. Compteurs

Vérifier :

\[
N_{\mathrm{FA}}
\leq
N_M
\]

\[
N_{\mathrm{FA},C}
\leq
N_{M,C}
\]

\[
N_{\mathrm{ref}}
\leq
N_{\mathrm{legit}}
\]

## 14.4. Mise à jour de clé

Après K1a, K1b ou K2 réussie :

```text
âge = 0
messages = 0
nouvel identifiant
```

Après K0 :

```text
âge augmente
messages augmente si le message est servi
```

## 14.5. Arrêt

Vérifier le motif exact :

```text
battery_reserve_reached
maximum_duration
maximum_steps
blocking_error
```

## 14.6. Rejeu déterministe

Exécuter deux fois la même mission avec :

```text
mêmes paramètres
même graine
même politique
```

Les sorties doivent être identiques, sauf métadonnées temporelles non scientifiques.

---

# 15. Validation statistique

## 15.1. Principes

Une concordance visuelle ne suffit pas.

Une valeur \(p\) de test statistique ne suffit pas non plus.

La validation combine :

- moments ;
- quantiles ;
- intervalles de confiance ;
- courbes empiriques ;
- tests diagnostiques.

## 15.2. Modèle gaussien RFF

Comparer :

```text
moyenne empirique
covariance empirique
histogrammes
Q–Q plots
```

aux valeurs théoriques.

## 15.3. FAR et FRR empiriques

Pour \(N\) essais indépendants :

\[
\widehat p
=
\frac{k}{N}
\]

Construire un intervalle binomial.

Critère recommandé :

```text
la probabilité théorique appartient à l’intervalle à 95 %
```

Ce critère doit être interprété sur plusieurs configurations et non sur un unique tirage.

## 15.4. Taille d’échantillon

Pour une probabilité \(p\), viser suffisamment d’événements attendus :

\[
Np
\]

Pour une première validation, un nombre d’événements attendus d’au moins 20 à 30 est recommandé.

Pour des probabilités cryptographiques extrêmement faibles, utiliser une preuve analytique.

## 15.5. Monte Carlo de mission

Vérifier la stabilisation de :

```text
moyenne
écart-type
intervalle de confiance
classement des politiques
```

lorsque \(N_{\mathrm{MC}}\) augmente.

## 15.6. Comparaison appariée

Avec graines communes, comparer :

\[
\Delta_r
=
Y_r(P0)-Y_r(B_j)
\]

Valider l’intervalle de confiance de \(\Delta\), pas seulement les intervalles séparés.

---

# 16. Validation croisée avec les sources

## 16.1. Niveau de correspondance

Chaque élément est classé :

```text
exactement repris
adapté
dérivé
calibré
politique
```

## 16.2. Source exacte

Pour une relation `littérature` ou `datasheet`, enregistrer :

```text
référence
section
équation ou tableau
conditions expérimentales
unités
différences avec le modèle
```

## 16.3. Relations composites

Pour :

\[
\rho_{AB}
=
\rho_{\mathrm{HW}}
J_0(2\pi f_d\Delta t)
\frac{\gamma}{1+\gamma}
\]

valider séparément :

```text
Jakes
dérivation bruit
facteur matériel
produit proposé
```

Ne pas présenter le produit comme une formule exacte d’une source unique.

## 16.4. Paramètres transférés

Une valeur provenant d’une autre plateforme doit porter un avertissement.

Exemples :

```text
temps RFF sur Raspberry Pi
signature ECC sur CC2538
```

Ces valeurs ne deviennent pas automatiquement valides sur STM32L1.

---

# 17. Validation de sensibilité

Un paramètre calibré ou politique n’est validé que si les conclusions ne reposent pas sur une valeur unique arbitraire.

## 17.1. Paramètres obligatoires

```text
rho_HW
d_M
kappa_gb
eta_keep
q_trigger
KDR_max
FAR_max
poids
T_msg
p_M
p_C
```

## 17.2. Critère

Pour chaque conclusion principale, identifier :

```text
plage où elle reste vraie
point où elle change
paramètre le plus influent
```

## 17.3. Conclusion fragile

Une conclusion est marquée fragile si une petite modification raisonnable d’un paramètre non validé inverse le classement des politiques.

Statut :

```text
PASS_WITH_LIMITATIONS
```

ou :

```text
EXPLORATORY_ONLY
```

---

# 18. Validation de reproductibilité

## 18.1. Manifeste

Chaque campagne enregistre :

```text
code_version
model_version
parameter_hash
config_hash
seed_list
library_versions
operating_system
start_time
end_time
```

## 18.2. Hash des paramètres

Deux résultats comparés doivent avoir le même hash de paramètres, sauf paramètres explicitement balayés.

## 18.3. Test de reproduction

Sur une autre exécution :

- résultats déterministes identiques ;
- résultats aléatoires identiques avec même graine ;
- figures reconstruites depuis les données brutes ;
- tables reconstruites depuis les résultats traités.

## 18.4. Interdiction

Il est interdit de modifier manuellement une figure ou un tableau sans conserver la transformation dans le code.

---

# 19. Matrice de traçabilité

Le fichier suivant doit être généré :

```text
results/validation/traceability_matrix.csv
```

Colonnes :

```text
equation_id
equation_name
scientific_status
source
module
function
test_id
test_level
expected_result
tolerance
validation_status
evidence_file
limitations
```

### Exemple

```text
CH-EQ17
Clarke-Jakes temporal correlation
literature
Jakes
channel.py
compute_temporal_correlation
CH-TEST-007
V2+V4
J0(0)=1
1e-12
PASS
test_channel_jakes.json
signed correlation retained
```

---

# 20. Registre des tests

Créer :

```text
results/validation/test_registry.csv
```

Colonnes :

```text
test_id
test_name
module
category
blocking
inputs
expected
tolerance
actual
status
execution_time_s
seed
evidence
```

Chaque test bloquant en échec bloque la porte correspondante.

---

# 21. Fichiers de preuve

Structure :

```text
results/
└── validation/
    ├── reports/
    ├── numerical/
    ├── statistical/
    ├── plots/
    ├── logs/
    ├── traceability_matrix.csv
    ├── test_registry.csv
    └── validation_manifest.json
```

Pour chaque test, conserver au moins un fichier machine-readable :

```text
JSON
CSV
NPZ
```

Les captures d’écran seules ne sont pas des preuves suffisantes.

---

# 22. Rapport de validation

Le rapport final doit contenir :

## 22.1. Résumé exécutif

```text
portes réussies
portes échouées
éléments bloqués
éléments exploratoires
```

## 22.2. Validation par module

```text
channel
authentication
key_generation
energy_latency
decision_maker
mission
campaign
```

## 22.3. Écarts

Pour chaque écart :

```text
valeur attendue
valeur obtenue
erreur
tolérance
cause probable
correction
nouveau test
```

## 22.4. Limites

Distinguer :

```text
limite scientifique
limite de données
limite de plateforme
limite numérique
limite de politique
```

## 22.5. Conclusion

Le rapport ne doit jamais utiliser simplement :

```text
le modèle est validé
```

Il doit préciser :

```text
quelles parties
dans quel domaine
avec quelles limites
selon quel niveau de preuve
```

---

# 23. Critères d’acceptation par module

## 23.1. `channel.py`

Accepté si :

- conversions correctes ;
- valeurs de référence reproduites ;
- bornes respectées ;
- corrélations négatives conservées ;
- modes SNR exclusifs ;
- tests de monotonie réussis.

## 23.2. `authentication.py`

Accepté si :

- seuil nominal reproduit ;
- FAR/FRR analytiques correctes ;
- distributions empiriques compatibles ;
- robustesse A2 complète ;
- coût et sécurité séparés.

## 23.3. `key_generation.py`

Accepté analytiquement si :

- KDR et entropie corrects ;
- seuil cohérent ;
- cryptopériode correcte ;
- indices corrects.

Accepté seulement avec limitations pour la sécurité PHY tant que \(\phi^{\mathrm{var}}\) n’est pas validée.

## 23.4. `energy_latency.py`

Accepté pour les coûts relatifs si :

- ToA reproduit ;
- bilans corrects ;
- unités correctes ;
- coûts attendus/pire cas séparés.

L’autonomie absolue reste limitée tant que les coûts de base ne sont pas validés.

## 23.5. `decision_maker.py`

Accepté si :

- oracle logique réussi ;
- contraintes réussies ;
- Pareto identique à l’oracle ;
- Tchebychev réussi ;
- aucun choix inadmissible ;
- refus explicite ;
- poids validés ou résultat marqué exploratoire.

## 23.6. `mission.py`

Accepté si :

- énergie conservée ;
- état de clé correct ;
- Mallory séparée ;
- compteurs cohérents ;
- rejeu déterministe réussi.

## 23.7. `campaign.py`

Accepté si :

- graines communes ;
- manifestes complets ;
- IC corrects ;
- résultats bruts disponibles ;
- comparaisons appariées ;
- figures reproductibles.

---

# 24. Critères de rejet immédiat

Le projet échoue la validation en présence d’un seul des cas suivants :

```text
Mallory débite la batterie d’Alice
une décision rejetée est sélectionnée
le choix final n’appartient pas au front
A2 est autorisée sans profil RFF
K1 est autorisée sans faisabilité requise
K0 est choisie malgré renouvellement requis
une valeur absolue est appliquée à rho_AB dans le modèle nominal
FAR et FRR sont interverties
le SNR dB est utilisé comme SNR linéaire
le message normal est compté deux fois dans A1
une constante cachée influence le choix
un mode de secours est caché
des politiques comparées utilisent des traces différentes
```

---

# 25. Anomalies et procédure de correction

Lorsqu’un test échoue :

```text
1. enregistrer l’échec ;
2. conserver les entrées ;
3. conserver la sortie réelle ;
4. identifier la première fonction fautive ;
5. vérifier l’équation ;
6. vérifier les unités ;
7. corriger le code, pas la formule ;
8. ajouter un test de non-régression ;
9. relancer la porte concernée ;
10. relancer toutes les portes dépendantes.
```

Il est interdit d’augmenter simplement la tolérance sans justification.

---

# 26. Validation des résultats finaux

Une figure ou un tableau est accepté si :

- ses données sources existent ;
- son script existe ;
- ses paramètres sont enregistrés ;
- son titre et ses axes sont corrects ;
- ses unités sont visibles ;
- son incertitude est visible lorsqu’elle est pertinente ;
- ses variantes exploratoires sont indiquées ;
- il peut être régénéré automatiquement.

---

# 27. Échelle de confiance des conclusions

## Confiance A — Forte dans le modèle simulé

Conditions :

- niveaux V0 à V5 réussis ;
- paramètres principaux validés ;
- sensibilité stable ;
- résultats reproductibles.

## Confiance B — Modérée

Conditions :

- fonctions et DM validés ;
- certains paramètres calibrés ou transférés ;
- résultats robustes sur une plage raisonnable.

## Confiance C — Exploratoire

Conditions :

- paramètres importants à valider ;
- coûts de plateforme incomplets ;
- poids non validés ;
- \(\phi^{\mathrm{var}}\) supposée.

## Confiance D — Non concluante

Conditions :

- test bloquant échoué ;
- résultats instables ;
- absence de reproductibilité ;
- incohérence scientifique.

Chaque conclusion du rapport doit recevoir une classe de confiance.

---

# 28. Checklist avant le codage principal

```text
[ ] équations figées
[ ] architecture figée
[ ] règles de développement figées
[ ] UML cohérent
[ ] flowchart cohérent
[ ] protocole de simulation rédigé
[ ] protocole de validation rédigé
[ ] paramètres ouverts identifiés
[ ] identifiants de tests définis
[ ] tolérances centralisées
[ ] structure de preuves définie
```

---

# 29. Checklist avant une campagne nominale

```text
[ ] GATE-0 réussi
[ ] GATE-1 réussi
[ ] GATE-2 réussi
[ ] GATE-3 réussi ou limitations explicites
[ ] GATE-4 réussi
[ ] GATE-5 réussi
[ ] graines communes définies
[ ] paramètres nominaux exportés
[ ] politique de poids validée ou campagne exploratoire
[ ] protocole K2 défini ou K2 marqué exploratoire
[ ] coûts de base disponibles ou autonomie limitée
```

---

# 30. Checklist avant la soutenance

```text
[ ] matrice de traçabilité complète
[ ] registre de tests complet
[ ] aucun test bloquant en échec
[ ] limites affichées
[ ] paramètres non validés affichés
[ ] figures reproductibles
[ ] tableaux reproductibles
[ ] comparaisons appariées
[ ] intervalles de confiance
[ ] conclusions classées par niveau de confiance
[ ] aucune revendication de sécurité informationnelle complète
    sans validation de variabilité et modèle de Mallory
```

---

# 31. Livrables de validation

La phase documentaire de validation est complète lorsque les fichiers suivants sont prévus :

```text
docs/07_VALIDATION_PROTOCOL.md
results/validation/traceability_matrix.csv
results/validation/test_registry.csv
results/validation/validation_manifest.json
results/validation/reports/validation_report.md
```

Les trois derniers seront générés pendant l’implémentation et l’exécution des tests.

---

# 32. Étape suivante du projet

La documentation scientifique et expérimentale nécessaire au démarrage du code est désormais définie.

L’ordre d’implémentation devient :

```text
1. models.py
2. parameters.py
3. channel.py
4. tests du canal
5. authentication.py
6. tests de l’authentification
7. key_generation.py
8. tests de la gestion de clé
9. energy_latency.py
10. tests des coûts
11. decision_maker.py
12. tests du DM
13. mission.py
14. campaign.py
15. campagnes et résultats
```