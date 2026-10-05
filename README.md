# P0 : arbitre multiobjectif d'authentification et de gestion de clé pour capteurs LoRa

Code complet du travail, associé à l'article « Optimisation multiobjectif de l'authentification et de la gestion des clés adaptée au contexte pour les réseaux IoT LoRa — étude de cas face à un schéma publié d'authentification hybride empreinte radio / MAC ».

**Commencer par [GUIDE_COMPLET.md](GUIDE_COMPLET.md).**

Tous les résultats de ce dépôt proviennent de la campagne **corrigée** (calcul de Tchebycheff corrigé). Le journal brut de la campagne (878 Mo) n'est pas versionné : il est fourni compressé dans la version « données brutes » du dépôt.

## Installation et tests

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -p "test_*.py"                    # 469 tests
python -m unittest discover -s haenel_comparison/tests -p "test_*.py"  # 76 tests
```

## Statut

Dépôt privé pendant la préparation de l'article ; il sera rendu public à la fin du travail.
