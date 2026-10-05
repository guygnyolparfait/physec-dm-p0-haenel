#!/usr/bin/env bash
# ================================================================
# PIPELINE FINAL — Comparaison P0 vs Haenel et al.
# Relance tout le pipeline depuis zéro, dans l'ordre.
# Usage (depuis la racine du dépôt, environnement virtuel actif) :
#     bash src/haenel_comparison/run_all_final.sh
# ================================================================
set -e

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY="${PYTHON:-python3}"
export PYTHONPATH="$ROOT/src"
cd "$ROOT"

echo "=== 1. Tests (projet + tests unitaires haenel_comparison) ==="
echo "===    vérification des fichiers de résultats -- ceux-ci n'existent"
echo "===    pas encore avant la génération, voir étape 11) ==="
$PY -m unittest discover -s tests -p "test_*.py"
# test_final_checks.test_required_result_files_exist est un CONTROLE
# A POSTERIORI : sur un dossier results/ vide (première exécution ou
# rejeu propre), il échoue par construction avant que le pipeline
# n'ait rien généré. On ne le traite donc pas comme fatal ici -- il
# est revérifié, cette fois de façon significative, à l'étape 11.
set +e
$PY -m unittest discover -s src/haenel_comparison/tests -p "test_*.py" -v
set -e

echo "=== 2. Traçabilité des paramètres ==="
$PY -m haenel_comparison.haenel_parameter_traceability
$PY -m haenel_comparison.option_b_missing_parameters
$PY -m haenel_comparison.haenel_option_b_sources

echo "=== 3. Option A (calibration + validation) ==="
$PY -m haenel_comparison.energy_option_a

echo "=== 4. Expérience A (énergie/FRR, 30 graines) ==="
$PY -m haenel_comparison.run_haenel_experiment_a

echo "=== 5. Diagnostic détaillé P0_AUTH_ONLY (principal + secondaire) ==="
$PY -m haenel_comparison.p0_auth_only_haenel_rff
$PY -m haenel_comparison.p0_auth_only_haenel_scale
$PY -m haenel_comparison.export_p0_diagnostics

echo "=== 6. Sensibilités (latence, poids, frontière fine) ==="
$PY -m haenel_comparison.latency_sensitivity
$PY -m haenel_comparison.weight_sensitivity
$PY -m haenel_comparison.weight_boundary_sensitivity

echo "=== 7. Expérience B (sécurité/FAR, campagne historique 30 graines) ==="
$PY -m haenel_comparison.run_haenel_experiment_b

echo "=== 7b. Expérience sécurité renforcée (Monte-Carlo >=100000 tentatives, ==="
echo "===     corrige le sous-échantillonnage de l'étape 7, voir WORK_LOG) ==="
$PY -m haenel_comparison.security_monte_carlo

echo "=== 8. Option B (modèle événementiel MSP430G2x + validation) ==="
$PY -m haenel_comparison.energy_option_b
$PY -m haenel_comparison.validate_option_b

echo "=== 9. P0_COMPLETE (extension exploratoire) ==="
$PY -m haenel_comparison.p0_complete

echo "=== 10. Figures finales + tableau de synthèse ==="
$PY -m haenel_comparison.generate_figures_experiment_a
$PY -m haenel_comparison.generate_final_outputs

echo "=== 12. Figures anglaises de l'article ==="
$PY -m haenel_comparison.generate_article_figures_en

echo "=== 11. Tests finaux ==="
$PY -m unittest discover -s src/haenel_comparison/tests -p "test_*.py" -v

echo ""
echo "Pipeline terminé. Résultats dans results/haenel_comparison/"
echo "Rapport final : docs/haenel/Compte_Rendu_Final_Haenel_vs_P0.md"
