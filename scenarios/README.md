# Scénarios S1 à S5 (campagne corrigée)

`scenarios_S1_S5.csv` donne les paramètres de chaque phase des cinq scénarios, tels qu'ils sont utilisés par la campagne corrigée.

Ce fichier est **généré** par le code : il ne faut pas le modifier à la main. La source est `src/physec_dm/case_studies.py`, via `build_five_case_studies_v2()`.

Régénération, depuis la racine du dépôt :

```bash
PYTHONPATH=src python -m scripts.export_scenarios
```

Colonnes principales :

- `separation_mallory` : facteur de séparation entre le nœud légitime et l'attaquant (campagne corrigée).
- `cost_profile` : profil de coût CPU (LOW, CENTRAL ou HIGH).
- `mean_snr_db`, `shadowing_std_db` : rapport signal sur bruit moyen et écart-type de l'ombrage.
- `mallory_attempt_probability` : probabilité qu'une tentative d'attaque ait lieu à chaque période.
- `effective_speed` : vitesse du nœud (une rampe est indiquée par ses bornes).
- `criticality_forced` : criticité imposée pendant la phase d'alarme (S2).

Les phases sont définies par leurs fractions de la mission (`start_fraction`, `end_fraction`).
