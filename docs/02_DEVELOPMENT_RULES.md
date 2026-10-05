# Règles de développement de PHYSEC-DM

## 1. Source de vérité

Les développements doivent respecter :

```text
modelisation_parametres_modifies(1).tex
modelisation parametre modifié.pdf
```

Une ancienne formule, un ancien nom ou une ancienne hypothèse incompatible doit être retiré.

---

## 2. Ordre de travail obligatoire

```text
sources
→ modèle
→ validation
→ pseudo-code
→ code
→ simulation
→ résultats
```

Le code ne doit pas précéder la validation scientifique d’une équation.

---

## 3. Classification scientifique obligatoire

Chaque équation et chaque paramètre reçoit un statut :

| Statut | Signification |
|---|---|
| littérature | repris directement d’une source identifiée |
| datasheet | valeur issue d’une fiche technique |
| dérivé | obtenu par une dérivation explicitée |
| calibré | ajusté sur données ou résultat expérimental |
| scénario | valeur servant à définir une expérience |
| politique | règle propre au Decision Maker |
| à valider | information insuffisamment documentée |

Une citation après une équation ne signifie pas que l’équation complète apparaît telle quelle dans la source.

---

## 4. Interdiction des constantes cachées

Toute constante numérique doit être déclarée dans `parameters.py` avec :

```text
nom
valeur
unité
statut
source
commentaire
plage de sensibilité
```

Interdit :

```python
score = 0.6 * energy + 0.4 * security
```

tant que les coefficients n’ont pas été validés et déclarés.

---

## 5. Unités internes

Unités obligatoires :

```text
énergie       : joule
temps         : seconde
fréquence     : hertz
distance      : mètre
vitesse       : mètre par seconde
courant       : ampère
tension       : volt
puissance RF  : watt ou dBm selon variable explicitement nommée
probabilité   : valeur décimale dans [0,1]
```

Les noms doivent indiquer les unités :

```text
carrier_frequency_hz
time_s
energy_j
power_dbm
current_a
voltage_v
```

---

## 6. dB et domaine linéaire

Le logiciel doit distinguer :

```text
Gamma_t : SNR en dB
gamma_t : SNR linéaire
```

Conversions :

\[
\Gamma_t=10\log_{10}(\gamma_t)
\]

\[
\gamma_t=10^{\Gamma_t/10}
\]

Interdictions :

- utiliser un SNR en dB dans \(\gamma/(1+\gamma)\) ;
- additionner directement des puissances en dBm ;
- utiliser \(20\log_{10}\) pour un rapport de puissances.

---

## 7. Modèle nominal et variantes

Le modèle nominal conserve :

\[
\rho_{AB,t}
=
\rho_{\mathrm{HW}}
J_0(2\pi f_{d,t}\Delta t)
\frac{\gamma_t}{1+\gamma_t}
\]

La variante :

\[
\rho_{AB,t}^{+}=\max(0,\rho_{AB,t})
\]

doit être :

- implémentée séparément ;
- activée par un paramètre explicite ;
- enregistrée dans les résultats ;
- comparée en sensibilité.

Il est interdit d’appliquer silencieusement une valeur absolue ou une troncature.

---

## 8. Règles d’énergie

L’énergie optimisée est celle d’Alice.

Inclure :

```text
E_base,t
E_sec,t(D)
```

avec :

\[
E_t(D)=E_{\mathrm{base},t}+E_t^{\mathrm{sec}}(D)
\]

Ne pas inclure :

- l’énergie de Bob ;
- l’énergie des trames émises par Mallory.

Les traitements de Bob peuvent être inclus dans la latence bloquante.

---

## 9. Trafic légitime et Mallory

Les deux processus doivent être codés séparément.

```text
processus 1 : message légitime d’Alice
processus 2 : tentative indépendante de Mallory
```

Les compteurs doivent distinguer :

```text
N_M
N_FA
N_M,C
N_FA,C
N_ref
N_viol
```

---

## 10. A1 et A2

### A1

A1 utilise un MAC de \(b_{\mathrm{MAC}}\) bits.

\[
p_{\mathrm{forge}}=2^{-b_{\mathrm{MAC}}}
\]

\[
R_t^{\mathrm{auth}}(A_1)=1-2^{-b_{\mathrm{MAC}}}
\]

### A2

A2 utilise :

```text
test RFF chez Bob
→ acceptation directe
ou
→ rejet puis défi–réponse
```

La robustesse complète est :

\[
P_{\mathrm{FA},t}(A_2)
=
\mathrm{FAR}_t
+
(1-\mathrm{FAR}_t)2^{-b_{\mathrm{MAC}}}
\]

\[
R_t^{\mathrm{auth}}(A_2)
=
1-P_{\mathrm{FA},t}(A_2)
\]

Ne pas remplacer cette formule par \(1-\mathrm{FAR}\) dans le modèle nominal.

---

## 11. Probabilités de repli

Pour Alice :

\[
p_{\mathrm{fb},t}^{(A)}=\mathrm{FRR}(\theta)
\]

Pour Mallory :

\[
p_{\mathrm{fb},t}^{(M)}=1-\mathrm{FAR}_t
\]

Seule la probabilité d’Alice entre dans l’espérance d’énergie d’Alice.

---

## 12. KDR

Dans le mode analytique :

\[
\mathrm{KDR}_{\mathrm{brut},t}
=
\frac{\arccos(\rho_{AB,t})}{\pi}
\]

La fonction accepte une corrélation signée dans \([-1,1]\).

Ne pas appliquer préalablement :

```text
abs(rho_AB)
max(0, rho_AB)
```

dans le chemin nominal.

---

## 13. Modes de quantification

Le code doit distinguer :

```text
mode analytique :
    KDR_t = KDR_brut,t

mode calibré :
    KDR_t = g_q(rho_AB,t ; beta_q)
```

Un facteur multiplicatif exploratoire est classé `calibré`, pas `littérature`.

---

## 14. Faisabilité PHY

L’accord est :

\[
\phi_t^{\mathrm{agree}}
=
\mathbb{1}\{\mathrm{KDR}_t\leq\mathrm{KDR}_{\max}\}
\]

La faisabilité complète est réservée à :

\[
\phi_t^{\mathrm{PHY}}
=
\phi_t^{\mathrm{agree}}\phi_t^{\mathrm{var}}
\]

Tant que \(\phi_t^{\mathrm{var}}\) n’est pas validée, les résultats doivent parler de **faisabilité d’accord**, pas de sécurité informationnelle complète.

---

## 15. Cryptopériode

Les règles de vieillissement sont des politiques.

Le code doit conserver :

```text
age de clé
nombre de messages
compromission/suspicion
q_t
r_t
e_key,t
T_deadline,t
```

Lorsque :

\[
e_t^{\mathrm{key}}=1
\]

alors `K0` est interdit.

---

## 16. Latences distinctes

Ne pas additionner naïvement :

```text
latence d’authentification
délai de production de clé
```

L’objectif est :

\[
L_t(D)
=
\max
\left(
\frac{L_t^{\mathrm{auth}}(D)}{L_{\max}(\sigma_t)},
\frac{L_t^{\mathrm{key}}(D)}{T_t^{\mathrm{deadline}}}
\right)
\]

---

## 17. Coût attendu et contrainte prudente

Pour A2 légitime :

\[
E_t^{\mathrm{sec}}(A_2)
=
\mathrm{FRR}(\theta)E_{\mathrm{CR}}
\]

est un coût attendu.

Pour l’admissibilité, utiliser un majorant prudent lorsqu’un repli aléatoire peut se produire.

Les résultats doivent distinguer :

```text
coût attendu
coût de pire cas
```

---

## 18. Décisions évaluées dans un contexte immuable

Pendant l’évaluation des huit décisions :

- le contexte ne change pas ;
- la batterie ne change pas ;
- l’âge de clé ne change pas ;
- les compteurs ne changent pas.

L’état n’est mis à jour qu’après le choix final.

---

## 19. Rejets et erreurs

### Erreur

Une erreur indique une incohérence du logiciel ou des paramètres.

Exemples :

```text
BW <= 0
rho_HW hors [0,1]
SNR linéaire négatif
poids dont la somme est nulle
```

### Rejet

Un rejet indique qu’une décision valide n’est pas admissible dans le contexte.

Exemples :

```text
A2 sans profil RFF
K1 sans faisabilité PHY
batterie insuffisante
FAR au-dessus du plancher
```

Une erreur arrête l’expérience. Un rejet est journalisé et la simulation continue.

---

## 20. Journalisation obligatoire

Chaque cycle du DM enregistre :

```text
contexte
huit décisions évaluées
métriques brutes
motifs de rejet
ensemble admissible
front de Pareto
poids
valeurs idéales et nadir
scores Tchebychev
décision finale
raison du choix
```

---

## 21. Pareto exact

Avec huit décisions, l’énumération exhaustive est obligatoire.

Une métaheuristique est inutile.

La dominance utilise les quatre objectifs orientés en minimisation :

\[
\mathbf f_t(D)
=
\begin{bmatrix}
E_t(D)\\
L_t(D)\\
-R_t^{\mathrm{auth}}(D)\\
-Q_t^{\mathrm{key}}(D)
\end{bmatrix}
\]

---

## 22. Poids contextuels

Les poids sont une politique :

\[
w_k(c_t)\geq0
\]

\[
\sum_k w_k(c_t)=1
\]

Ils doivent respecter les monotonies validées :

```text
batterie qui baisse → poids énergie qui augmente
message critique     → poids auth et latence qui augmentent
clé vieillissante    → poids clé qui augmente
```

Aucun coefficient numérique ne doit être inventé avant validation.

---

## 23. Bris d’égalité

Ordre obligatoire :

```text
1. FAR la plus faible
2. énergie la plus faible
3. latence bloquante la plus faible
4. ordre lexicographique des actions
```

La tolérance de score doit être déclarée.

---

## 24. Reproductibilité

Toute fonction aléatoire reçoit un générateur contrôlé.

Interdit :

```python
random.seed(...)
```

dans plusieurs fonctions.

Les campagnes doivent utiliser les mêmes graines pour toutes les politiques comparées.

---

## 25. Précision numérique

Utiliser des comparaisons avec tolérance.

Ne jamais utiliser une égalité stricte entre flottants pour :

- scores ;
- quantiles ;
- valeurs de Bessel ;
- reproductions de littérature ;
- calculs d’énergie.

---

## 26. Tests minimaux

Chaque sous-modèle exige :

```text
test nominal
test limite
test invalide
test de monotonie
test d’unité
test de reproduction
```

Tests scientifiques obligatoires mentionnés dans le modèle :

```text
T_air contre exemples Semtech
FAR décroissante avec le SNR
FAR croissante lorsque d_M diminue
KDR_brut(0,6) ≈ 0,2952
N_meas décroissant avec rho_AB
bilans énergétiques vérifiés à la main
cas B_t → B_min
cas q_t → 1
SNR très faible et très élevé
```

---

## 27. Nommage

Fonctions :

```text
compute_...
build_...
check_...
select_...
run_...
```

Variables :

```text
snake_case
```

Les noms scientifiques doivent rester reconnaissables :

```text
snr_db
snr_linear
temporal_correlation
noise_correlation
reciprocity
false_acceptance_rate
false_rejection_rate
key_disagreement_rate
```

---

## 28. Fonctions élémentaires

Une fonction scientifique élémentaire implémente une relation principale.

Une fonction d’orchestration peut appeler plusieurs fonctions élémentaires, mais ne doit pas cacher leurs calculs.

---

## 29. Aucun écrasement des valeurs brutes

Conserver simultanément :

```text
snr_db et snr_linear
rho_time, rho_noise et rho_AB
KDR_brut et KDR effectif
énergie attendue et pire cas
métriques brutes et normalisées
```

---

## 30. Critère d’acceptation d’un module

Un module est accepté lorsque :

- ses équations sont référencées ;
- ses paramètres sont typés ;
- ses unités sont vérifiées ;
- ses cas limites sont testés ;
- ses résultats sont reproductibles ;
- ses variantes sont explicitement nommées ;
- son journal permet d’expliquer les résultats.