# SCIENTIFIC FINAL GATE — Comparaison P0 vs Haenel et al.

Vérifié le 25/09/2026, avant création du ZIP final. Chaque item est
vérifié individuellement, avec preuve concrète (fichier, test, ou
citation), avant d'être marqué PASS. Aucun item n'est marqué PASS
sans évidence vérifiable.

| CHECK | STATUS | EVIDENCE |
|---|---|---|
| Article Haenel relu | PASS | Texte intégral relu via PMC (accès libre) cette passe : Sections 6.2.2, 6.3.1, 6.3.2, 6.3.3, Fig. 11 citées littéralement dans `Compte_Rendu_Final_Haenel_vs_P0.md` Sections 2-4, 11 |
| MSP430G2x correct | PASS | `energy_option_b.py` sourcé sur MSP430G2553 (SLAS735J) et MSP430G2231 (SLAS862), voir `haenel_option_b_sources.csv` ; `tests/test_energy_option_b.py::test_cpu_current_is_not_fr5994_value` verrouille contre régression |
| CC110L correct | PASS | Constantes TX/RX/calibration sourcées sur SWRS109C (CC110L), inchangé depuis V2, jamais remis en cause |
| deep-sleep correctement traité | PASS | `T_CALIB_S_CENTRAL=799e-6` (IDLE, pas SLEEP) ; aucune constante `I_LPM3_A`/`I_SLEEP_A`/`I_IDLE_A` dans `energy_option_b.py` ; `tests/test_final_scientific_pass.py::TestNoSilentDeepSleepTransition` (2 tests) |
| première full authentication prise en compte/documentée | PASS | `EFFECTIVE_FIXED_HYBRID_OVERHEAD_MJ` (energy_option_a.py), `initial_full_auth_overhead_mJ()` (haenel_energy_adapter.py), convention documentée dans `run_haenel_experiment_a.py` ; citation Fig. 11 dans le rapport Section 4 ; `tests/test_final_scientific_pass.py::TestFirstFullAuthenticationDocumented` (3 tests) |
| B5 renommé transposition calibrée | PASS | `B5_HAENEL_CALIBRATED` partout dans le code actif et les 6 documents narratifs ; `tests/test_final_scientific_pass.py::TestNoLiteralB5StringInDeliverables` (occurrences résiduelles toutes en contexte correctif explicite, vérifié automatiquement) |
| Option A correctement décrite comme calibration | PASS | Rapport Section 8 : "pas une validation indépendante" ; `tests/test_final_scientific_pass.py::TestOptionANotCalledIndependentValidation` |
| MAC-only correctement décrit comme référence publiée | PASS | `energy_option_a.py::validate_option_a` : note "published reference used directly" ; master table Section A |
| même FAR Haenel utilisé pour comparaison principale | PASS | `p0_auth_only_haenel_rff.py`, `FAR_RFF_HAENEL=0.002` ; `tests/test_final_scientific_pass.py::TestPrincipalComparisonUsesPublishedFar` (2 tests) |
| FRR5/FAR correctement qualifié | PASS | `far_status_for_frr(0.05)` retourne `ASSUMED_CONSTANT_FAR_FOR_FRR5_SENSITIVITY` ; `tests/test_final_scientific_pass.py::TestFrr5FarLabeledAssumed` (2 tests) |
| P0 native RFF séparé | PASS | `p0_auth_only_haenel_scale.py` distinct de `p0_auth_only_haenel_rff.py`, CSV distincts (`p0_native_rff_sensitivity_deterministic.csv` vs `p0_auth_only_haenel_rff_deterministic.csv`) ; `tests/test_final_scientific_pass.py::TestNativeSensitivityIsSeparate` (2 tests) |
| frontière des poids vérifiée | PASS | `weight_boundary_sensitivity.py` : écart max entre score(A1) et w_energy = 0,00e+00 sur 11 points ; croisement exact à w_energy=0,25 ; `tests/test_final_scientific_pass.py::TestWeightBoundarySweep` (2 tests) |
| sensibilité latence correctement interprétée | PASS | Réserve méthodologique explicite ajoutée dans `latency_sensitivity.py` et rapport Section 14 |
| Option B incremental overhead recalculé | PASS | `option_a_vs_option_b.csv` colonnes `measured_increment_over_rff_only_mJ`/`modeled_increment_over_rff_only_mJ`/`increment_explained_pct` ; résultat réel 0,19%-14,45% (recalculé, pas copié) ; `tests/test_final_scientific_pass.py::TestOptionBIncrementalColumns` (3 tests) |
| timing CC110L cohérent | PASS | Table 5-11 (IDLE), plus de référence "Sleep to RX" comme hypothèse centrale ; voir item deep-sleep ci-dessus |
| hypothèse Chaskey tracée | PASS | `haenel_option_b_sources.csv` : 2 sources EXTERNAL_SCIENTIFIC_SOURCE (ARM Cortex-M + ratio MSP430 relatif), 1 UNAVAILABLE (valeur absolue MSP430, article dédié identifié mais inaccessible) |
| campagne sécurité >=100000 | PASS | `security_monte_carlo.py::N_ATTEMPTS_TOTAL=100_000` ; `tests/test_security_monte_carlo.py::test_sample_size_meets_minimum_requirement` |
| P0_COMPLETE séparé de comparaison principale | PASS | `p0_complete_extension_table.csv` fichier séparé, absent de `master_comparison_table.csv` ; `tests/test_final_scientific_pass.py::TestP0CompleteMarkedExploratory` (3 tests) |
| README sans contradiction | PASS | `HAENEL_COMPARISON_README.md` entièrement réécrit (statut "TERMINÉ", plus de section "CE QUI RESTE À FAIRE") ; `tests/test_final_scientific_pass.py::test_readme_has_no_not_implemented_contradictions` |
| mail encadrante corrigé | PASS | "transparent" (pas "transparente"), reformulations Section 20 appliquées ; `tests/test_final_scientific_pass.py::test_mail_has_no_feminine_transparente` |
| tableaux cohérents | PASS | `tests/test_final_scientific_pass.py::TestNoNaNInRequiredColumns` (2 tests), `TestOptionBSourcesAllHaveStatus` (1 test) |
| figures cohérentes | PASS | Figures 1-5 régénérées et inspectées visuellement (rendu PNG) après cette passe ; titres corrigés pour ne plus être tronqués ; Figure 5 remplacée par la courbe de frontière fine |
| tous tests Haenel PASS | PASS | 77/77 tests verts (`haenel_comparison/tests/`, y compris les 29 nouveaux de `test_final_scientific_pass.py`) |
| tous tests historiques PASS | PASS | 469/469 tests verts (`tests/`, S1-S5 inclus) |
| aucun fichier S1-S5 modifié | PASS | `tests/test_final_checks.py::test_s1_s5_case_studies_still_produce_five_cases` toujours vert ; aucune modification apportée à `physec_dm/case_studies.py` ni au moteur `physec_dm/decision_maker.py` cette session (seuls des adaptateurs locaux à `haenel_comparison/` ont été créés/modifiés) |

**TOUS LES ITEMS SONT PASS. Le ZIP final peut être créé.**

Total tests : 546 (469 historiques + 77 haenel_comparison), tous verts.
Voir `FINAL_TEST_REPORT.txt` pour la sortie complète.
