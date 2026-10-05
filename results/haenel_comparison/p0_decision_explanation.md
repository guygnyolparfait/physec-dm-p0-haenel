# Explication de la décision P0_AUTH_ONLY_HAENEL_RFF (comparaison principale)

## Résultat observé

Pour le cas principal (FRR=10%, A2 reçoit le FAR PUBLIÉ de Haenel
et al. = 0.002 -- voir `p0_auth_only_haenel_rff.py`), avec la
gestion de clé figée à K0, **P0 choisit A1 (MAC cryptographique)**,
pas A2 (RFF), sous poids égaux. Ce même résultat tient aussi pour le
cas de sensibilité FRR=5% (FAR toujours 0.002 par hypothèse
ASSUMED_CONSTANT_FAR_FOR_FRR5_SENSITIVITY, voir
`p0_auth_only_haenel_rff.far_status_for_frr`).

## Les deux candidats sont admissibles

| | A1-K0 (MAC) | A2-K0 (RFF, FAR publié Haenel) |
|---|---|---|
| Admissible | True | True |
| Énergie (mJ, échelle Haenel) | 5.64743 | 4.54076 |
| Latence (neutralisée) | 0.0 | 0.0 |
| R_auth | 1.00000000 | 0.99800000 |
| Q_key | 1.000000 | 1.000000 |
| FAR | 0.00000000 | 0.00200000 |
| Sur le front de Pareto | True | True |
| Score Tchebycheff | 0.25000000 | 0.25000000 |
| Clé de tie-break | `(5.421010862427522e-20, 5.647430000000001, 0.0, 'A1-K0')` | `(0.002, 4.540760000000001, 0.0, 'A2-K0')` |

**A2 est nettement moins cher en énergie** (4.541 mJ
contre 5.647 mJ, soit un écart bien plus visible
que sur l'échelle LoRa native), **mais A1 a un FAR bien plus bas**
(borne cryptographique idéalisée, ~5.4e-20) que A2 (FAR
publié Haenel et al., 0.002).

## Pourquoi le score Tchebycheff est identique pour les deux

C'est une **propriété mathématique générale**, VÉRIFIÉE dans le code
(voir `weight_boundary_sensitivity.py`), pas un artefact de
paramétrage : sur un front de Pareto à exactement 2 points, avec des
poids égaux, chaque candidat est nécessairement au **point idéal**
sur au moins un axe et au **point nadir** sur au moins un autre (sinon
l'un dominerait l'autre et ne serait pas sur le front). Le score de
Tchebycheff prend le MAX des écarts normalisés pondérés : sur l'axe
où un candidat est au nadir, son écart normalisé vaut TOUJOURS 1,0
par construction (la normalisation ramène nadir à 1 et idéal à 0).

Concrètement, dans ce problème réduit à 2 candidats avec latence et
Qkey neutres (identiques) :

    score(A1) = w_energy   (A1 est au nadir sur l'axe énergie)
    score(A2) = w_auth     (A2 est au nadir sur l'axe robustesse)

Sous poids égaux (w_energy = w_auth = 0.25), les deux scores sont
IDENTIQUEMENT 0.25 -- **quelle que soit l'ampleur réelle de l'écart**
sur l'axe où chacun est en tête. C'est pour cela que ni le
changement d'échelle d'énergie, ni la variation du ratio de latence
sur 4 ordres de grandeur (voir réserve méthodologique dans
`latency_sensitivity.py`), ne changent le résultat : la
normalisation absorbe systématiquement la magnitude.

## Pourquoi le tie-break tranche pour A1

Le score étant à égalité stricte, le Decision Maker applique le
bris d'égalité (`build_tie_break_key`, `physec_dm/decision_maker.py`) :
**FAR croissant en premier critère**. A1 a un FAR quasi nul (borne
cryptographique), A2 le FAR publié de Haenel et al. (0.002) --
strictement positif. A1 gagne donc systématiquement le tie-break.

## Ce qui ferait basculer P0 vers A2 -- LA FRONTIÈRE EST FINE

**Corrigé le 25/09/2026** : ne plus dire "il faut donner beaucoup
plus d'importance à l'énergie". Le sweep fin de
`weight_boundary_sensitivity.py` (résultats dans
`weight_boundary_sensitivity.csv`) montre que la frontière est
EXACTEMENT à w_energy = w_auth = 0.25, et qu'un écart de seulement
0.001 (w_energy=0.251 contre w_auth=0.249) suffit à faire basculer
la décision vers A2. Ce n'est pas un résultat qui nécessite un poids
extrême : c'est une frontière immédiatement adjacente au point de
poids égaux.

## Conclusion

Ce n'est ni un bug, ni un résultat arrangé : avec les poids égaux,
A1 et A2 obtiennent une égalité stricte de score, départagée en
faveur d'A1 par le FAR. Cette décision entraîne donc une
consommation d'énergie plus élevée que la stratégie hybride de
Haenel et al. dans ce scénario, mais elle résulte du compromis et de
la règle de départage -- pas de l'inadmissibilité du RFF (les deux
candidats sont admissibles). Une légère modification des préférences
(0.001 sur les poids) peut déplacer la décision vers A2.
