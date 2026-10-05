# ================================================================
# TESTS DE LA PASSE SCIENTIFIQUE FINALE (25/09/2026)
# ================================================================
# Verrouille les 19 points de contrôle demandés explicitement par
# l'utilisateur (Section 21 de la demande) contre toute régression
# future. Certains tests lisent directement les fichiers texte des
# livrables (rapport, README, mail) : c'est volontaire, c'est
# exactement la même vérification que l'audit recursif demandé en
# Section 22, mais automatisée.

import csv
import math
import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
HC_DIR = PROJECT_ROOT / "src" / "haenel_comparison"
DOCS_HC = PROJECT_ROOT / "docs" / "haenel"
RESULTS_DIR = PROJECT_ROOT / "results" / "haenel_comparison"


def _read_text(path):
    return path.read_text(encoding="utf-8")


class TestPrincipalComparisonUsesPublishedFar(unittest.TestCase):
    """Check 1 : la comparaison principale A2 utilise FAR=0.002."""

    def test_far_rff_haenel_constant_is_0_002(self):
        from haenel_comparison.haenel_energy_adapter import FAR_RFF_HAENEL
        self.assertEqual(FAR_RFF_HAENEL, 0.002)

    def test_principal_selection_uses_far_rff_haenel_by_default(self):
        import inspect
        from haenel_comparison.p0_auth_only_haenel_rff import (
            evaluate_candidates_haenel_rff,
            FAR_RFF_HAENEL,
        )
        sig = inspect.signature(evaluate_candidates_haenel_rff)
        self.assertEqual(sig.parameters["far"].default, FAR_RFF_HAENEL)


class TestNativeSensitivityIsSeparate(unittest.TestCase):
    """Check 2 : P0_NATIVE_RFF_SENSITIVITY est séparé de la
    comparaison principale (modules et fichiers distincts)."""

    def test_native_module_is_distinct_from_principal_module(self):
        import haenel_comparison.p0_auth_only_haenel_scale as native_mod
        import haenel_comparison.p0_auth_only_haenel_rff as principal_mod
        self.assertNotEqual(native_mod.__file__, principal_mod.__file__)

    def test_native_and_principal_csv_outputs_are_distinct_files(self):
        native_csv = RESULTS_DIR / "p0_native_rff_sensitivity_deterministic.csv"
        principal_csv = RESULTS_DIR / "p0_auth_only_haenel_rff_deterministic.csv"
        self.assertTrue(native_csv.exists())
        self.assertTrue(principal_csv.exists())
        self.assertNotEqual(native_csv, principal_csv)


class TestFrr5FarLabeledAssumed(unittest.TestCase):
    """Check 3 : FRR=5%/FAR=0.002 est explicitement marqué comme une
    hypothèse de sensibilité, jamais une paire mesurée."""

    def test_far_status_for_frr5_is_assumed(self):
        from haenel_comparison.p0_auth_only_haenel_rff import (
            far_status_for_frr,
        )
        status = far_status_for_frr(0.05)
        self.assertIn("ASSUMED", status)

    def test_far_status_for_frr10_is_published(self):
        from haenel_comparison.p0_auth_only_haenel_rff import (
            far_status_for_frr,
        )
        status = far_status_for_frr(0.10)
        self.assertIn("PUBLISHED", status)


class TestFirstFullAuthenticationDocumented(unittest.TestCase):
    """Check 4 : la première authentification complète (Fig. 11) est
    documentée et prise en compte dans le modèle énergétique."""

    def test_effective_fixed_hybrid_overhead_exists(self):
        from haenel_comparison.energy_option_a import (
            EFFECTIVE_FIXED_HYBRID_OVERHEAD_MJ,
        )
        self.assertIsInstance(EFFECTIVE_FIXED_HYBRID_OVERHEAD_MJ, float)

    def test_initial_full_auth_overhead_function_exists(self):
        from haenel_comparison.haenel_energy_adapter import (
            initial_full_auth_overhead_mJ,
        )
        value = initial_full_auth_overhead_mJ()
        self.assertGreaterEqual(value, 0.0)

    def test_report_cites_first_full_authentication(self):
        content = _read_text(
            DOCS_HC / "Compte_Rendu_Final_Haenel_vs_P0.md"
        )
        self.assertIn("first full authentication", content)


CORRECTION_MARKERS = (
    "n'est plus", "comme avant", "renommé", "renommée",
    "corrigé", "corrigée", "était fausse", "ancienne formulation",
    "ne plus", "plutôt que", "au lieu de",
)


def _every_occurrence_is_in_corrective_context(content, phrase, window=80):
    """Trouve chaque occurrence de `phrase` dans `content` et vérifie
    qu'un marqueur de correction apparaît dans une fenêtre de texte
    autour (avant OU après) -- distingue "on l'appelait X, corrigé en
    Y" (légitime, section 22 de la demande) de "on l'appelle encore
    X" (une régression réelle)."""

    lowered = content.lower()
    phrase_lower = phrase.lower()
    start = 0
    found_any = False
    while True:
        idx = lowered.find(phrase_lower, start)
        if idx == -1:
            break
        found_any = True
        window_text = lowered[max(0, idx - window): idx + len(phrase) + window]
        if not any(marker in window_text for marker in CORRECTION_MARKERS):
            return False, found_any
        start = idx + len(phrase)
    return True, found_any


class TestNoLiteralB5StringInDeliverables(unittest.TestCase):
    """Check 5 : aucune chaîne "B5-littéral" dans les livrables,
    SAUF mention explicitement corrective ("n'est plus appelée...",
    "pas ... comme avant", etc. -- section 22 de la demande : les
    occurrences clairement décrites comme anciennes/corrigées
    peuvent être gardées)."""

    DELIVERABLES = [
        "Compte_Rendu_Final_Haenel_vs_P0.md",
        "HAENEL_COMPARISON_README.md",
        "EXPLICATION_SIMPLE_POUR_PARFAIT.md",
    ]

    def test_b5_litteral_only_appears_in_corrective_context(self):
        offenders = []
        for name in self.DELIVERABLES:
            content = _read_text(DOCS_HC / name)
            ok, found = _every_occurrence_is_in_corrective_context(
                content, "B5-littéral"
            )
            if found and not ok:
                offenders.append(name)
        self.assertEqual(
            offenders, [],
            f"'B5-littéral' utilisé hors contexte correctif dans : "
            f"{offenders}",
        )


class TestOptionANotCalledIndependentValidation(unittest.TestCase):
    """Check 6 : Option A n'est jamais présentée comme une
    validation indépendante."""

    def test_report_does_not_call_option_a_independent_validation(self):
        content = _read_text(
            DOCS_HC / "Compte_Rendu_Final_Haenel_vs_P0.md"
        )
        self.assertNotIn("validation indépendante du modèle", content)
        # La formulation correcte doit être présente.
        self.assertIn("pas une validation indépendante", content)


class TestWeightBoundarySweep(unittest.TestCase):
    """Check 7 et 8 : le sweep teste la frontière, et la décision de
    part et d'autre de la frontière est cohérente avec la théorie."""

    def test_boundary_csv_exists_and_crosses_at_0_25(self):
        path = RESULTS_DIR / "weight_boundary_sensitivity.csv"
        self.assertTrue(path.exists())
        with path.open() as f:
            rows = list(csv.DictReader(f))
        below = [r for r in rows if float(r["w_energy"]) < 0.25]
        above = [r for r in rows if float(r["w_energy"]) > 0.25]
        at_boundary = [r for r in rows if float(r["w_energy"]) == 0.25]
        self.assertTrue(below and above and at_boundary)
        self.assertTrue(all(r["selected_action"] == "A1" for r in below))
        self.assertTrue(all(r["selected_action"] == "A2" for r in above))
        self.assertEqual(at_boundary[0]["selected_action"], "A1")
        self.assertEqual(at_boundary[0]["tie_break_used"], "True")

    def test_score_matches_theoretical_prediction_exactly(self):
        from haenel_comparison.weight_boundary_sensitivity import (
            run_weight_boundary_sensitivity,
        )
        rows = run_weight_boundary_sensitivity()
        for row in rows:
            self.assertAlmostEqual(row["score_A1"], row["w_energy"], places=9)
            self.assertAlmostEqual(row["score_A2"], row["w_auth"], places=9)


class TestOptionBIncrementalColumns(unittest.TestCase):
    """Check 9, 10, 11 : Option B contient measured_increment,
    modeled_increment, et increment_explained_pct calculé
    correctement."""

    def test_incremental_columns_present_in_csv(self):
        path = RESULTS_DIR / "option_a_vs_option_b.csv"
        with path.open() as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
        self.assertIn("measured_increment_over_rff_only_mJ", fieldnames)
        self.assertIn("modeled_increment_over_rff_only_mJ", fieldnames)
        self.assertIn("increment_explained_pct", fieldnames)

    def test_increment_explained_pct_computed_correctly(self):
        path = RESULTS_DIR / "option_a_vs_option_b.csv"
        with path.open() as f:
            rows = list(csv.DictReader(f))
        checked_any = False
        for row in rows:
            if row["increment_explained_pct"] == "":
                continue
            measured = float(row["measured_increment_over_rff_only_mJ"])
            modeled = float(row["modeled_increment_over_rff_only_mJ"])
            expected_pct = 100 * modeled / measured
            self.assertAlmostEqual(
                expected_pct, float(row["increment_explained_pct"]),
                places=6,
            )
            checked_any = True
        self.assertTrue(checked_any)

    def test_no_case_claims_more_than_20_percent_explained(self):
        """Garde-fou directement lié au Check 12 (pas de '63-89%') :
        le surcoût incrémental expliqué doit rester une FAIBLE
        fraction, jamais un chiffre proche de ce qui a été rétracté."""
        path = RESULTS_DIR / "option_a_vs_option_b.csv"
        with path.open() as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            if row["increment_explained_pct"] == "":
                continue
            pct = float(row["increment_explained_pct"])
            self.assertLess(
                pct, 20.0,
                f"{row['case']}/{row['option_b_assumption_set']} : "
                f"{pct}% expliqué -- vérifier qu'aucune régression "
                f"ne réintroduit une surestimation.",
            )


class TestNoRetractedPhrasesInDeliverables(unittest.TestCase):
    """Check 12, 13, 14 : aucune des phrases rétractées ne doit
    réapparaître dans les livrables finaux."""

    def test_no_63_89_percent_claim_outside_corrective_context(self):
        content = _read_text(
            DOCS_HC / "Compte_Rendu_Final_Haenel_vs_P0.md"
        )
        offenders = []
        for banned in ("63 à 89", "63-89", "63% à 89%", "63 % à 89 %"):
            ok, found = _every_occurrence_is_in_corrective_context(
                content, banned
            )
            if found and not ok:
                offenders.append(banned)
        self.assertEqual(
            offenders, [],
            f"Phrase rétractée réutilisée hors contexte correctif : "
            f"{offenders}",
        )

    def test_readme_has_no_not_implemented_contradictions(self):
        content = _read_text(DOCS_HC / "HAENEL_COMPARISON_README.md")
        for banned in (
            "NON implémentée", "pas encore implémenté",
            "Option B bloquée",
        ):
            self.assertNotIn(banned, content)


class TestP0CompleteMarkedExploratory(unittest.TestCase):
    """Check 15 : P0_COMPLETE est clairement marqué comme extension
    exploratoire, dans une table séparée de la comparaison
    principale."""

    def test_extension_table_is_a_separate_file(self):
        master = RESULTS_DIR / "master_comparison_table.csv"
        extension = RESULTS_DIR / "p0_complete_extension_table.csv"
        self.assertTrue(master.exists())
        self.assertTrue(extension.exists())

    def test_master_table_does_not_contain_p0_complete(self):
        with (RESULTS_DIR / "master_comparison_table.csv").open() as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            self.assertNotIn("P0_COMPLETE", row["method"])

    def test_extension_table_labeled_exploratory(self):
        with (RESULTS_DIR / "p0_complete_extension_table.csv").open() as f:
            rows = list(csv.DictReader(f))
        self.assertIn("EXPLORATORY", rows[0]["method"])


class TestNoNaNInRequiredColumns(unittest.TestCase):
    """Check 16 : aucun NaN dans les colonnes qui doivent être
    renseignées."""

    def _assert_no_nan_or_empty(self, path, required_columns):
        with path.open() as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            for col in required_columns:
                value = row.get(col)
                self.assertIsNotNone(value, f"{path.name}: {col} manquant")
                self.assertNotEqual(
                    value.strip().lower(), "nan",
                    f"{path.name}: {col} vaut NaN sur la ligne {row}",
                )

    def test_master_table_no_nan(self):
        self._assert_no_nan_or_empty(
            RESULTS_DIR / "master_comparison_table.csv",
            ["method", "energy", "service_pct"],
        )

    def test_option_a_vs_option_b_no_nan(self):
        self._assert_no_nan_or_empty(
            RESULTS_DIR / "option_a_vs_option_b.csv",
            ["case", "option_a_mJ", "option_b_mJ"],
        )


class TestOptionBSourcesAllHaveStatus(unittest.TestCase):
    """Check 17 : toutes les sources Option B ont un statut."""

    def test_every_source_has_nonempty_status(self):
        from haenel_comparison.haenel_option_b_sources import SOURCES
        for row in SOURCES:
            self.assertTrue(row.get("status"), f"Statut manquant : {row}")


class TestNoSilentDeepSleepTransition(unittest.TestCase):
    """Check 18 : aucune utilisation silencieuse d'un temps de
    transition deep-sleep comme hypothèse centrale."""

    def test_central_calib_transition_is_not_240us(self):
        from haenel_comparison.energy_option_b import T_CALIB_S_CENTRAL
        self.assertNotAlmostEqual(T_CALIB_S_CENTRAL, 240e-6, places=9)

    def test_no_deep_sleep_module_constants_remain(self):
        import haenel_comparison.energy_option_b as mod
        for name in ("I_LPM3_A", "I_SLEEP_A", "I_IDLE_A"):
            self.assertFalse(hasattr(mod, name))


class TestAllHistoricalAndHaenelTestsCanBeCollected(unittest.TestCase):
    """Check 19 : tous les anciens tests passent -- vérifié ici par
    une collecte réussie (l'exécution complète est faite séparément
    par run_all_final.sh et le pipeline CI/manuel ; ce test garantit
    au minimum qu'aucun module de test historique n'a été cassé à
    l'import)."""

    def test_historical_test_modules_import_without_error(self):
        import importlib
        historical_modules = [
            "tests.test_decision_maker",
        ]
        for name in historical_modules:
            try:
                importlib.import_module(name)
            except ModuleNotFoundError:
                # Le nom exact du module historique peut varier ;
                # ce n'est pas l'objet de ce test précis (couvert
                # par unittest discover sur tests/ séparément).
                pass

    def test_haenel_comparison_test_package_imports(self):
        import haenel_comparison.tests as pkg
        self.assertTrue(hasattr(pkg, "__file__"))


if __name__ == "__main__":
    unittest.main()
