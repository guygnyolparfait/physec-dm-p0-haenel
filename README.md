# P0 : arbitre multiobjectif d'authentification et de gestion de clé pour capteurs LoRa

Code complet du travail associé à l'article « Optimisation multiobjectif de l'authentification et de la gestion des clés adaptée au contexte pour les réseaux IoT LoRa — étude de cas face à un schéma publié d'authentification hybride empreinte radio / MAC ».

Tous les résultats proviennent de la **campagne corrigée** (calcul de Tchebycheff corrigé).

## Structure

| Dossier | Contenu |
|---|---|
| `src/physec_dm/` | Modèle : menaces, canal, énergie et latence, génération de clés, arbitre P0 |
| `src/scripts/` | Campagne S1 à S5, analyse, figures, export des scénarios |
| `src/haenel_comparison/` | Comparaison avec Haenel et al. (calibration, sécurité, frontière des poids, figures) et script de pipeline |
| `scenarios/` | Paramètres des phases des scénarios S1 à S5 (généré par le code) |
| `results/` | Résultats utiles : résumés et courbes de la campagne corrigée et de la comparaison Haenel |
| `docs/` | Explications du modèle et des paramètres, article (FR et EN), documentation de la correction, guide complet |
| `tests/` | Tests du modèle (469) |

Tests de la comparaison Haenel : `src/haenel_comparison/tests/` (76).

## Logiciels nécessaires

- Python 3.12
- Bibliothèques : `numpy`, `matplotlib`, `scipy` (voir `requirements.txt`)
- Pour compiler l'article : `tectonic` (ou une distribution LaTeX avec la classe `IEEEtran`)

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Lancer les tests

Depuis la racine du dépôt :

```bash
PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py"
PYTHONPATH=src python -m unittest discover -s src/haenel_comparison/tests -p "test_*.py"
```

## Lancer les simulations

Toutes les commandes se lancent depuis la racine du dépôt, avec `PYTHONPATH=src`.

Comparaison avec Haenel et al. (pipeline complet) :

```bash
bash src/haenel_comparison/run_all_final.sh
```

Campagne S1 à S5 corrigée (longue ; le journal brut est fourni à part, voir ci-dessous) :

```bash
PYTHONPATH=src python -m scripts.run_five_case_studies_v2_adaptive
PYTHONPATH=src python -m scripts.generate_v2_comparison_figures
PYTHONPATH=src python -m scripts.generate_v2_comparison_figures_en
```

Paramètres des scénarios :

```bash
PYTHONPATH=src python -m scripts.export_scenarios
```

## Données brutes

Le journal brut de la campagne corrigée (878 Mo) dépasse les limites de GitHub. Il est fourni compressé dans la version « données brutes » du dépôt. Le guide explique comment le restaurer.

## Documentation

Commencer par [docs/GUIDE_COMPLET.md](docs/GUIDE_COMPLET.md), qui présente le travail dans l'ordre où il a été réalisé.

## Statut

Dépôt privé pendant la préparation de l'article ; il sera rendu public à la fin du travail.
