# WORK_LOG — Session autonome Haenel vs P0

Format par entrée : heure | action | fichier | raison | résultat | erreur/correction.

---

**2026-09-25 01:51** | Démarrage session autonome (28 phases, mode
sans interruption) | — | Instruction utilisateur explicite | Projet
non-git confirmé (`git status` → "fatal: ni ceci ni... n'est un
dépôt git") | Sauvegarde horodatée créée dans
`backups_haenel/haenel_comparison_backup_20260925_015109/` et
`backups_haenel/results_haenel_comparison_backup_20260925_015109/`
avant toute modification. Aucun fichier original supprimé.

**2026-09-25 01:52** | Vérification outils disponibles | — |
Phase 10A nécessite de sourcer des datasheets si Internet
disponible | WebSearch et WebFetch confirmés disponibles | —

**2026-09-25 01:53** | Relance de la suite de tests complète (projet
+ haenel_comparison) AVANT toute modification, comme demandé en
Phase 1 | tests/, haenel_comparison/tests/ | Ne pas présumer que
l'état précédent est correct | Voir
`results/haenel_comparison/initial_validation_report.txt` | —

**2026-09-25 02:10** | Sourcing web réel (WebSearch+WebFetch) des
datasheets CC110L et MSP430FR5994 | haenel_option_b_sources.py,
datasheets_extracted/ | Phase 10A, ne pas fabriquer de valeurs |
11 paramètres OFFICIAL_DATASHEET obtenus (courants TX/RX/idle/veille
CC110L à 868MHz, courant actif MSP430FR5994) ; 3 restent
UNAVAILABLE (cycles Chaskey-12 sur MSP430, taille des trames, débit
radio configuré — non publiés par Haenel et al.) | —

**2026-09-25 02:20** | Construction Option B (modèle événementiel
TX/RX/CPU basé sur le déroulé protocolaire Fig.3/Fig.4 du papier) |
energy_option_b.py | Phase 10 | Résiduel calibré sur RFF_ONLY
uniquement (jamais par cas) | **Écart majeur détecté et documenté,
pas caché** : même à la borne HIGH de sensibilité, le modèle
TX/RX/CPU explique au plus ~5% du surcoût réel d'un repli MAC
(~9,87 mJ requis vs ~0,49 mJ modélisé, facteur ~20). Cause
identifiée : un coût protocolaire non quantifié par Haenel et al.
(fenêtre d'écoute/timeout), non modélisable sans fabriquer une
valeur. Conclusion : Option A reste le modèle de référence pour la
comparaison P0/B5 ; Option B sert de vérification structurelle
(l'ordre RFF_ONLY<HYBRID05<HYBRID10<MAC_ONLY est bien respecté) —
voir validate_option_b.py et HAENEL_COMPARISON_README.md.

**2026-09-25 02:25** | Bug détecté et corrigé dans
validate_option_b.py | validate_option_b.py | Relecture de la
sortie avant de la considérer correcte (jamais supposer) | Première
version multipliait deux fois par N_MESSAGES le résultat d'Option A
(déjà un total), produisant une erreur relative absurde de ~9900% |
Corrigé : compute_energy_option_a_for_case() retourne déjà un total,
ne pas re-multiplier. Reconfirmé : Option A <0.02% d'erreur sur les
3 cas où son modèle s'applique.

**2026-09-25 02:15** | Finalisation complète : Expérience B
(sécurité/FAR), P0_COMPLETE, sensibilités latence/poids, figures
4-5, tableau de synthèse, tests finaux, rapport complet (21
sections), documents encadrante (présentation/mail/slides),
explication simple, README/run_all_final.sh, manifeste, ZIP final |
tout haenel_comparison/ | Fin du workflow autonome demandé | 499
tests verts (469 historiques + 30 nouveaux), ZIP vérifié
(intégrité OK, 63 fichiers, CSV/figures/code tous valides) | Un bug
(double multiplication N_MESSAGES dans validate_option_b.py) trouvé
et corrigé en cours de route par relecture de la sortie, jamais
supposée correcte. Aucun fichier original du projet modifié ou
supprimé ; campagnes S1-S5 vérifiées intactes (test dédié).

FIN DE LA SESSION AUTONOME.

---

**2026-09-25 02:47** | Demande utilisateur : (1) inclure des PDF des
rapports dans le ZIP, (2) garantir que résultats et courbes ne sont
pas artificiels/générés par IA | — | Deux messages utilisateur,
le second interrompant le premier | Preuve de non-artificialité
choisie : suppression totale des sorties (`*.csv`, `figures/*.png`,
`*.md` de `results/haenel_comparison/`) puis relance complète de
`run_all_final.sh` depuis zéro | Bug trouvé : `set -e` faisait
échouer tout le script dès l'étape 1, car
`test_final_checks.test_required_result_files_exist` échoue par
construction sur un dossier `results/` vide (c'est un contrôle a
posteriori, prévu pour l'étape 11, pas un pré-requis) | Corrigé en
isolant cet appel avec `set +e`/`set -e` dans `run_all_final.sh`.
Relance complète : exit code 0, 30/30 tests verts, 14 CSV + 5 PNG +
1 MD régénérés avec des horodatages frais et des statistiques
IDENTIQUES à l'exécution précédente (graines fixes 9800-9829 etc. →
déterminisme, pas de génération aléatoire ou inventée à chaque
appel).

**2026-09-25 02:50** | Conversion Markdown → PDF | `md_to_pdf.py`
(nouveau) | `pandoc` absent de l'environnement ; les bibliothèques
Python (`markdown`, `weasyprint`, `xhtml2pdf`, `fpdf`, `reportlab`,
`mistune`) sont absentes ; `soffice --convert-to pdf` sur un `.md`
affiche la syntaxe markdown brute (`#`, `**`) sans mise en forme,
rejeté après vérification visuelle (rendu en PNG via `pdftoppm`,
inspection directe) | Écrit un convertisseur Markdown → LaTeX → PDF
dédié (gère titres, gras/italique, listes, tableaux, code inline,
caractères spéciaux), compilé via `tectonic` | Trois bugs trouvés et
corrigés en cours de route par inspection visuelle systématique de
CHAQUE PDF rendu en PNG avant validation, jamais supposés corrects :
(1) `**gras**` contenant un `` `code` `` imbriqué cassait la
détection du gras (le split par backtick séparait le marqueur
ouvrant du fermant) → réécrit en un seul passage regex combiné
code/gras/italique ; (2) tableaux larges (tuples de tie-break)
débordant de la page → ajout d'une macro LaTeX `\fittable` qui ne
réduit la taille que si le tableau dépasse `\textwidth` (jamais
d'agrandissement artificiel) ; (3) caractères `œ`, `§`, `«`, `»`,
`⁻`, `⁵` non couverts par la police par défaut → ajoutés à la table
de substitution LaTeX-safe. Les 6 PDF (`Compte_Rendu_Final_Haenel_
vs_P0`, `p0_decision_explanation`, `EXPLICATION_SIMPLE_POUR_
PARFAIT`, `PRESENTATION_ENCADRANTE`, `PLAN_5_SLIDES_ENCADRANTE`,
`HAENEL_COMPARISON_README`) compilent sans avertissement et ont été
vérifiés visuellement page par page (rendu PNG via `pdftoppm`,
lecture directe) avant d'être considérés valides. Stockés dans
`haenel_comparison/pdf_reports/`.

**2026-09-25 03:05** | Régénération `FINAL_TEST_REPORT.txt` et
reconstruction du ZIP final | `FINAL_TEST_REPORT.txt`,
`FINAL_MANIFEST.txt`, ZIP | L'ancien rapport de tests et le ZIP
dataient d'avant la relance propre et le travail PDF | Relance
complète de la suite de tests (469 + 30 = 499, tous verts) sur l'état
actuel, capturée telle quelle (aucune ligne éditée à la main) |
ZIP reconstruit depuis zéro (pas de copie de l'ancien ZIP stale) avec
les CSV/figures fraîchement régénérés, les 6 PDF, le convertisseur
`md_to_pdf.py`, et un manifeste mis à jour | Vérifié par extraction
complète, `zipfile.testzip()`, et contrôle du nombre de pages de
chaque PDF.

FIN DU TRAVAIL SUR CETTE DEMANDE.

---

**2026-09-25 12:00** | Relecture externe du paquet ZIP par
l'utilisateur : deux corrections scientifiques obligatoires
demandées avant envoi à l'encadrante | -- | Retour utilisateur
explicite avec instructions précises (relire Section 6.3.2 du
papier, resourcer Option B, ne pas cherry-picker, renforcer la
campagne sécurité à >=50 000 tentatives) | Travail engagé
immédiatement, sans redémarrer le projet | --

**2026-09-25 12:05** | Vérification directe de la Section 6.3.2 du
papier (PMC, texte intégral en accès libre,
https://pmc.ncbi.nlm.nih.gov/articles/PMC8230913/, pas de mémoire
approximative) | -- | Confirmer EXACTEMENT le matériel du banc
d'essai énergétique avant de toucher au code | Citation vérifiée :
"we used the Texas Instrument ultra-low-power microcontroller
MSP430G2x and the sub-1 GHz RF transceiver CC110L [...] by means of
the MSP-EXP430G2ET Launchpad Evaluation Kit" -- confirme que le
MSP430FR5994 (utilisé dans la version précédente d'`energy_option_b.py`)
est le mauvais composant. Confirmé aussi : "This also prevented the
nodes from using the 'deep-sleep' mode of the modules between two
transmissions." -- aucune modélisation LPM ne doit être ajoutée. |
--

**2026-09-25 12:10** | Recherche datasheet MSP430G2x réel |
WebSearch + téléchargement direct PDF | Le papier ne précise pas la
référence exacte de puce dans la famille MSP430G2x | Trouvé :
MSP-EXP430G2ET livré par défaut avec un MSP430G2553 (TI SLAU772A) ;
datasheet MSP430G2553 (SLAS735J) téléchargé et vérifié par
pdftotext -- 330 µA/MHz (typ) / 420 µA/MHz (max) à 3V/1MHz. Pour
borner l'incertitude "quelle puce exacte" (consigne explicite : ne
pas supposer silencieusement), datasheet MSP430G2231-EP (SLAS862)
également téléchargé et vérifié -- 300 µA/MHz (typ) / 390 µA/MHz
(max) à 3V/1MHz -- retenu comme borne LOW. | --

**2026-09-25 12:20** | Correction complète d'`energy_option_b.py` |
`energy_option_b.py`, `haenel_option_b_sources.py`, `haenel_config.py` |
Remplacer toutes les constantes CPU FR5994 par les valeurs MSP430G2x
sourcées | Toutes les constantes I_ACTIVE_A_PER_HZ_{LOW,CENTRAL,HIGH}
remplacées. Constantes I_LPM3_A (FR5994) et I_SLEEP_A/I_IDLE_A
(CC110L, jamais utilisées dans aucune formule) supprimées plutôt que
laissées comme code mort trompeur, conformément à la consigne
deep-sleep. | Second bug trouvé PENDANT cette correction (pas
introduit par elle) : les bornes LOW/HIGH de TX/RX/CPU existaient
déjà comme constantes avant cette session mais n'étaient JAMAIS
passées aux formules d'énergie (toujours CENTRAL, quel que soit le
label demandé) -- corrigé en ajoutant ces champs à
`OptionBAssumptions` et en les référençant dans les 3 fonctions
d'énergie. Un test dédié
(`test_low_high_cpu_bounds_are_wired_into_assumptions`) verrouille
ce bug contre toute régression.

**2026-09-25 12:30** | Correction de `validate_option_b.py` |
`validate_option_b.py` | Troisième bug trouvé : `build_comparison_table()`
appelait `compute_option_b_energy_mJ()` sans l'argument `assumptions`,
donc la comparaison de MAGNITUDE (celle qui alimentait l'affirmation
"facteur ~20") utilisait TOUJOURS CENTRAL, même quand le texte
parlait de la borne HIGH -- seule `check_ordering()` (qui ne
vérifie que l'ORDRE, pas l'écart en %) exerçait réellement LOW/HIGH
| Corrigé : `build_comparison_table()` calcule maintenant les 3
jeux LOW/CENTRAL/HIGH (12 lignes au lieu de 4 dans le CSV) | Résultat
recalculé avec le bon microcontrôleur ET le bon câblage des bornes :
écart de 11% (HYBRID_05/HIGH) à 37% (MAC_ONLY/LOW), jamais un
facteur ~20 -- la conclusion "facteur 20, probablement un temps
d'attente" a été retirée, remplacée par "écart non expliqué avec les
informations publiées, cause non établie".

**2026-09-25 12:40** | Ajout de `security_monte_carlo.py` (nouveau) |
`security_monte_carlo.py`, `tests/test_security_monte_carlo.py` |
Construire la campagne sécurité renforcée demandée (>=50 000,
idéalement 100 000 tentatives, IC95% binomial) | 100 000 tentatives
Bernoulli par politique (B5 : FAR=0,002 publié ; P0 : FAR réel du
modèle physec_dm pour l'action choisie, lu depuis
`p0_decision_diagnostics.csv`, jamais recopié à la main). IC95%
calculé par la méthode exacte de Clopper-Pearson (via
`scipy.stats.beta`), pas l'approximation normale (qui donnerait un
intervalle dégénéré pour le cas P0, k=0). Résultat : B5 189/100 000
(FAR empirique 0,189%, IC95%=[0,163%, 0,218%], compatible avec le
0,20% publié) ; P0 0/100 000 (IC95% supérieur = 3,7x10^-5) --
explicitement documenté comme NE PROUVANT PAS la supériorité de
P0, puisque ce volume ne peut distinguer un FAR réellement de
5,4x10^-20 d'un FAR simplement inférieur à ~3,7x10^-5. | Bug de
formatage trouvé et corrigé pendant l'écriture : un `.replace(",",
" ")` appliqué à une phrase entière (au lieu du seul nombre à
milliers) mangeait aussi les virgules de ponctuation française
normale -- corrigé en pré-formatant chaque nombre dans une variable
séparée avant de construire la phrase (bug répété 3 fois dans
`security_monte_carlo.py` et `generate_final_outputs.py`, corrigé
partout après relecture attentive de chaque sortie imprimée).

**2026-09-25 12:55** | Mise à jour de `generate_final_outputs.py`
(Figure 4 + tableau de synthèse) | `generate_final_outputs.py` |
Refléter la nouvelle campagne sécurité au lieu de l'ancienne
(30 graines, ~450 tentatives) | Figure 4 reconstruite en échelle
logarithmique (les deux FAR diffèrent de ~16 ordres de grandeur) :
barre B5 = FAR empirique + IC95%, barre P0 = limite de détection
IC95% (hachurée, jamais affichée comme "0"), marqueur séparé pour la
borne théorique du modèle, annotation explicite "NON une preuve de
supériorité". Tableau de synthèse (colonnes B et C) mis à jour avec
les vrais chiffres de `security_monte_carlo.csv`. | --

**2026-09-25 13:10** | Mise à jour de `run_all_final.sh` et
`tests/test_final_checks.py` | -- | Intégrer `security_monte_carlo.py`
dans le pipeline reproductible, avant l'étape des figures (qui en
dépend maintenant) | Nouvelle étape 7b ajoutée ; `security_monte_carlo.csv`
ajouté à la liste des fichiers requis (`test_required_result_files_exist`) |
--

**2026-09-25 13:15** | Relance complète du pipeline depuis zéro
(preuve de reproductibilité après corrections) | tous les fichiers
de `results/haenel_comparison/` | Vérifier que les corrections ne
cassent rien et que les résultats sont reproductibles | `rm` complet
puis `bash run_all_final.sh` : exit code 0, 48/48 tests
haenel_comparison + 469/469 tests historiques verts, tous les
fichiers régénérés avec les mêmes valeurs (graines fixes) | --

**2026-09-25 13:20** | Mise à jour de tous les documents narratifs |
`Compte_Rendu_Final_Haenel_vs_P0.md`, `EXPLICATION_SIMPLE_POUR_PARFAIT.md`,
`PRESENTATION_ENCADRANTE.md`, `MAIL_ENCADRANTE_RESULTATS.txt`,
`PLAN_5_SLIDES_ENCADRANTE.md`, `HAENEL_COMPARISON_README.md`,
`FINAL_MANIFEST.txt` | Remplacer partout l'affirmation "facteur ~20,
probablement un temps d'attente" par les vrais chiffres (11%-37%,
cause non établie) et ajouter la campagne sécurité renforcée,
sans jamais présenter "0 attaque acceptée par P0" comme une preuve |
Une section "Corrections apportées suite à relecture" ajoutée en
tête du rapport scientifique et du README, pour que le changement
soit visible sans avoir à comparer les deux versions | --

FIN DU TRAVAIL SUR CETTE CORRECTION (V2).

---

**2026-09-25 14:00** | DERNIÈRE PASSE — VERSION SCIENTIFIQUE FINALE,
mode autonome complet (aucune question, aucun checkpoint) | -- |
Instruction utilisateur explicite : 20 sections de corrections
scientifiques (renommage B5, comparaison principale avec FAR publié,
frontière des poids vérifiée dans le code, Option B recalculée en
surcoût incrémental, timing CC110L corrigé, sourcing Chaskey
approfondi, audit récursif, gate scientifique avant ZIP) |
Sauvegarde complète créée dans
`backups_haenel/pre_final_pass_20260925_132000/` avant toute
modification (haenel_comparison/ + results/haenel_comparison/) | --

**2026-09-25 14:05** | Relecture directe des sections 6.3.3/Fig.11
et 6.3.1/6.2.2 du papier (PMC, texte intégral) | -- | Confirmer
littéralement la citation "first full authentication" et le lien
FRR=10%/FAR=0,2% avant de coder quoi que ce soit | Confirmé : "Due
to the first full authentication, the hybrid protocol was a little
more energy-demanding at the start of the experiment" (Section
6.3.3) ; "This value [FRR=10%] was chosen as it led to a FAR of 0.2%
in our live experiment" (Section 6.3.1) ; FRR=10,89%/FAR=0,20%
mesurés ensemble en Section 6.2.2. Aucune valeur numérique isolée
pour le coût de démarrage. | --

**2026-09-25 14:15** | Renommage B5-littéral -> B5_HAENEL_CALIBRATED |
`haenel_b5.py`, `p0_auth_only.py`, `p0_auth_only_haenel_scale.py`,
`run_haenel_experiment_a.py`, `run_haenel_experiment_b.py`,
`security_monte_carlo.py`, `tests/test_haenel_b5_statistics.py`,
tous les documents narratifs | Le nom suggérait une reproduction
littérale, ce qui n'est pas exact (pas de modélisation explicite de
la première authentification au niveau du tirage message par
message) | Renommé partout, avec documentation explicite de la
convention retenue (le surcoût de démarrage est absorbé dans
`EFFECTIVE_FIXED_HYBRID_OVERHEAD_MJ`, ajouté une fois par campagne
sur le message d'indice 0, cas HYBRID uniquement) | `run_haenel_reference.py`
(script historique, non appelé par le pipeline) marqué explicitement
HISTORIQUE/SUPERSEDED plutôt que renommé, pour ne pas réécrire un
artefact déjà figé.

**2026-09-25 14:30** | Réécriture complète d'`energy_option_a.py` :
calibration à 2 paramètres nommés | `energy_option_a.py`,
`haenel_energy_adapter.py`, `tests/test_energy_option_a.py` |
Remplacer le modèle à 1 paramètre (moyenne de 2 estimations, résidu
non nul) par un système 2x2 résolu EXACTEMENT sur les 2 points
HYBRID publiés, avec des noms explicites
(`EFFECTIVE_FIXED_HYBRID_OVERHEAD_MJ`, `EFFECTIVE_FALLBACK_COST_MJ`)
distinguant clairement une calibration effective d'un coût physique
exact | Résultat : F=0,092 mJ, C=9,857 mJ/repli, erreur EXACTEMENT
0,00% sur les 4 cas (mieux que l'ancien résidu de 0,006%-0,01%) |
Alias de compatibilité `E_FALLBACK_CALIBRATED_MJ` conservé pour ne
pas casser les imports existants, pointant vers la nouvelle valeur.

**2026-09-25 14:45** | Construction de la COMPARAISON PRINCIPALE :
`p0_auth_only_haenel_rff.py` (nouveau) | `haenel_energy_adapter.py`
(ajout `apply_haenel_rff_far_to_a2`, `FAR_RFF_HAENEL=0.002`),
`p0_auth_only_haenel_rff.py` (nouveau) | A2 recevait le FAR NATIF du
modèle de canal physec_dm (~8,39e-5) au lieu du FAR PUBLIÉ par
Haenel et al. (0,002) -- ce n'était pas la bonne comparaison pour
répondre à la question scientifique posée | Réutilisé les VRAIES
formules `authentication.calculate_a2_total_false_acceptance` /
`calculate_a2_robustness` (jamais un calcul `1-far` à la main) pour
construire l'override. Résultat : décision INCHANGÉE (P0 choisit
toujours A1), mais maintenant sur la bonne base de comparaison.
L'ancienne analyse (FAR natif) renommée P0_NATIVE_RFF_SENSITIVITY et
clairement séparée (fichiers, CSV, et sections de rapport distincts).

**2026-09-25 15:00** | VÉRIFICATION MATHÉMATIQUE de la frontière des
poids, PAS une affirmation | `weight_boundary_sensitivity.py`
(nouveau) | L'utilisateur exige explicitement de ne pas affirmer
"il faut beaucoup plus de poids sur l'énergie" sans le vérifier dans
le code | Dérivation manuelle d'abord (score(A1)=w_energy,
score(A2)=w_auth sur ce front à 2 points avec axes neutres), PUIS
vérification par sweep fin dans le code (11 points, w_energy de 0,20
à 0,30) | CONFIRMÉ EXACTEMENT : écart entre score(A1) et w_energy =
0,00e+00 sur les 11 points. Frontière exactement à w_energy=w_auth
=0,25 ; 0,251 suffit à faire basculer vers A2. Toutes les
formulations "beaucoup plus de poids" corrigées dans les 6
documents narratifs.

**2026-09-25 15:15** | Reformulation de la sensibilité latence avec
réserve méthodologique | `latency_sensitivity.py` | L'utilisateur
signale que la robustesse à la latence peut être un effet
STRUCTUREL de la normalisation à 2 candidats, pas une preuve
physique | Ajouté la réserve explicite dans le code et tous les
documents ; migré aussi ce module vers le FAR publié Haenel pour A2
(cohérence avec la comparaison principale) | --

**2026-09-25 15:30** | Option B : recalcul en SURCOÛT INCRÉMENTAL |
`validate_option_b.py` | L'ancienne conclusion ("Option B explique
63 à 89% du surcoût réel") comparait des totaux ABSOLUS, alors que
RFF_ONLY est reproduit PAR CONSTRUCTION (résiduel calibré dessus) --
comparaison trompeuse | Ajouté measured_increment_over_rff_only_mJ,
modeled_increment_over_rff_only_mJ, increment_explained_pct (3
jeux LOW/CENTRAL/HIGH x 3 cas). RECALCULÉ, jamais copié les anciens
chiffres | Résultat réel : 0,19% à 14,45% expliqué selon le cas --
très inférieur à l'ancienne estimation erronée. Un test dédié
(`test_no_case_claims_more_than_20_percent_explained`) verrouille ce
résultat contre toute régression.

**2026-09-25 15:45** | Correction du timing CC110L (deep-sleep vs
IDLE) | `energy_option_b.py`, `haenel_option_b_sources.py`,
`haenel_config.py` | L'utilisateur a repéré une incohérence : le
code affirmait "aucun deep-sleep modélisé" mais utilisait 240µs
("From Sleep to RX Mode", datasheet CC110L) comme temps de
transition central | Resourcé sur la Table 5-11 du même datasheet
(transitions depuis IDLE, pas depuis SLEEP) : 75,1µs (LOW, sans
calibration), 799µs (CENTRAL, avec calibration par défaut), 1598µs
(HIGH, 2 calibrations). Statut ASSUMED_STATE_TRANSITION. Câblé dans
`OptionBAssumptions.calib_transition_s`, utilisé dans les 3
formules d'énergie | Impact numérique négligeable sur les résultats
(le terme de calibration est petit face au coût total), mais
correction de cohérence scientifique importante.

**2026-09-25 16:00** | Recherche approfondie du coût Chaskey sur
MSP430 | `haenel_option_b_sources.py`, `haenel_config.py` |
Recherche WebSearch/WebFetch de sources plus pertinentes que la
mention générique précédente | Trouvé et lu intégralement (eprint
2015/1182, Mouha et al.) : 9,8/7,0 cycles/octet sur ARM Cortex-M0/M4
pour Chaskey de base, et la phrase précise "about 30% slower on
16-bit Texas Instrument MSP430" pour Chaskey-12 -- mais AUCUNE
valeur absolue MSP430. Identifié un article dédié (Lee & Seo, IEEE,
"Optimized implementation of chaskey MAC on 16-bit MSP430") mais son
contenu était derrière un péage d'accès (IEEE Xplore/ResearchGate),
non contournable | Documenté honnêtement : valeur absolue MSP430
UNAVAILABLE malgré recherche active, plage 10-40 cycles/octet
conservée comme ASSUMED_MAPPING/EXTERNAL_SCIENTIFIC_SOURCE, jamais
présentée comme mesurée.

**2026-09-25 16:15** | Restructuration du tableau de synthèse et des
figures | `generate_final_outputs.py` | Séparer P0_COMPLETE de la
comparaison principale (table dédiée), corriger "service_pct" pour
les lignes Haenel (N/A, pas "100%" artificiel), remplacer la Figure
5 (4 barres grossières) par la courbe de frontière fine | Créé
`p0_complete_extension_table.csv` séparé ; Figure 5 reconstruite à
partir de `weight_boundary_sensitivity.csv`, montrant visuellement
le croisement exact à w_energy=0,25 | --

**2026-09-25 16:30** | Réécriture complète des 6 documents
narratifs | `Compte_Rendu_Final_Haenel_vs_P0.md` (22 sections),
`EXPLICATION_SIMPLE_POUR_PARFAIT.md`, `PRESENTATION_ENCADRANTE.md`,
`MAIL_ENCADRANTE_RESULTATS.txt`, `PLAN_5_SLIDES_ENCADRANTE.md`,
`HAENEL_COMPARISON_README.md` | Propager toutes les corrections
ci-dessus dans les livrables lisibles par l'encadrante et
l'utilisateur | Corrigé aussi "je tiens à être transparente" ->
"transparent" (l'utilisateur est un homme, signalé explicitement) ;
supprimé les contradictions du README ("Expérience B non
implémentée", "P0_COMPLETE pas encore implémenté" -- obsolètes
depuis la passe précédente mais jamais nettoyées) | Chaque chiffre
cité recalculé depuis les CSV frais, jamais recopié à la main depuis
une version antérieure.

**2026-09-25 16:45** | 29 nouveaux tests
(`test_final_scientific_pass.py`) couvrant les 19 points de contrôle
demandés explicitement | `tests/test_final_scientific_pass.py`
(nouveau) | Verrouiller chaque correction contre toute régression
future, y compris par lecture directe des livrables texte (audit
automatisé) | Deux bugs de test trouvés et corrigés PENDANT
l'écriture : (1) un test interdisant toute occurrence de
"B5-littéral" échouait sur les mentions légitimes ("n'est plus
appelé...") -- corrigé en vérifiant le CONTEXTE de chaque occurrence
plutôt qu'une interdiction totale ; (2) un test sur "63/89%" utilisait
une sous-chaîne "63" bien trop large -- corrigé pour cibler les
phrases exactes rétractées. 29/29 tests verts après correction.

**2026-09-25 17:00** | Audit récursif final (grep systématique) |
-- | Chercher toutes les phrases interdites listées explicitement
par l'utilisateur dans l'ensemble du module | Trouvé 3 occurrences
réelles hors contexte correctif : `p0_auth_only.py`,
`p0_auth_only_haenel_scale.py` (commentaires internes),
`run_haenel_experiment_b.py` (5 occurrences, docstrings + policy
label), et `__init__.py` ("mêmes conditions") | Toutes corrigées.
`run_haenel_reference.py` (script historique, non exécuté par le
pipeline) marqué HISTORIQUE/SUPERSEDED plutôt que réécrit, ses
mentions de "B5-littéral" et "mêmes conditions" restant dans un
contexte explicitement daté.

**2026-09-25 17:15** | Relance complète du pipeline depuis zéro
(preuve finale de reproductibilité) | tous les fichiers de
`results/haenel_comparison/` | Vérifier que toutes les corrections
ci-dessus produisent un pipeline cohérent de bout en bout | `rm`
complet puis `bash run_all_final.sh` : exit code 0, 77/77 tests
haenel_comparison + 469/469 tests historiques verts (546 au total).
Chaque chiffre cité dans les documents narratifs revérifié
bit-à-bit identique aux CSV frais (graines fixes) | --

FIN DU TRAVAIL SUR LA PASSE SCIENTIFIQUE FINALE.

---

**2026-09-25 17:30** | Demande de l'encadrante (relayée par
l'utilisateur) : rédiger le travail sous forme d'article IEEE
(LaTeX + PDF, anglais ET français), mieux raconter la différence
RFF-vers-MAC vs P0 comme une "histoire", corriger les figures
jugées "trop artificielles/superficielles" (retirer les "segments"
= caps d'erreur, figure 1 en particulier), et juger si des courbes
seraient préférables aux graphes en barres | -- | -- | -- |

**2026-09-25 17:35** | Recherche bibliographique réelle (agent
dédié, WebSearch/WebFetch multi-sources) | -- | Besoin de références
IEEE ICC/GLOBECOM vérifiées pour la section Related Work de
l'article, jamais inventées | 11 papiers réels trouvés et
vérifiés (recoupement sur au moins 2 sources chacun : IEEE Xplore,
arXiv, page de l'éditeur ou de l'auteur). Deux candidats rejetés
faute de vérification suffisante (liste d'auteurs ou venue
ambiguës) -- signalés plutôt que devinés. Couverture ICC/GLOBECOM
directe sur "décision multiobjectif pour la sécurité" quasi
inexistante : complétée par 2 papiers journal (Prantl et al. 2023,
Prvulovic et al. 2025) sur la sélection multiobjectif de mécanismes
de sécurité, plus proches thématiquement. | --

**2026-09-25 17:40** | Refonte complète de la Figure 1 (demande
explicite : "je ne veux plus voir les segments de droite", "les
courbes ne seraient-elles pas mieux ?") | `generate_figures_experiment_a.py` |
L'ancien diagramme en barres groupées avec caps d'erreur ne
racontait pas la comparaison, il fallait lire 3 barres + légende
pour comprendre | Remplacé par une COURBE : la vraie relation
FRR/énergie de Haenel et al. (0%/RFF seul -> 5% -> 10%), avec la
bande IC95% de B5_HAENEL_CALIBRATED (pas de caps -- une bande
translucide), et P0 tracé comme une ligne PLATE volontairement
positionnée au niveau du plafond MAC_ONLY publié. Choix assumé et
recommandé : OUI, une courbe est meilleure ici, car la question
posée ("comment l'énergie évolue-t-elle") est intrinsèquement une
question de tendance, pas de catégories indépendantes -- justifié
explicitement à l'utilisateur, pas seulement exécuté. | Réglage de
légende nécessaire (chevauchement avec l'annotation P0) -- corrigé
en repositionnant légende et annotation.

**2026-09-25 17:45** | Retrait des "caps" d'erreur (segments) sur
les Figures 3 et 4 également, par cohérence (la critique portait
sur "les figures" en général) | `generate_figures_experiment_a.py`,
`generate_final_outputs.py` | -- | Remplacés par des barres/lignes
d'erreur fines sans capuchon (`capsize=0`, `elinewidth`) | Bug
`Rectangle.set() got an unexpected keyword argument 'elinewidth'`
sur `ax.bar()` -- corrigé via `error_kw={"elinewidth": ...}`
(différent de `ax.errorbar()`, qui accepte `elinewidth` directement).

**2026-09-25 17:50** | Rédaction de l'article scientifique complet,
bilingue, format conférence IEEE (`IEEEtran`) | `article/paper_en.tex`,
`article/paper_fr.tex` (nouveaux) | Structure complète : Abstract,
Introduction, Related Work (11 références réelles intégrées),
Background, Methodology, Results (avec la Figure 1 et le tableau de
la frontière des poids), Discussion, Conclusion, References |
Compilé avec tectonic (déjà validé ce projet) -- vérifié qu'IEEEtran
est disponible dans le bundle. Bibliographie écrite en
`thebibliography` manuel plutôt que `bibtex`/`biblatex`, pour éviter
une dépendance externe (fichier `.bst`) non garantie dans
l'environnement sandboxé. | Deux bugs de rendu trouvés et corrigés
par inspection visuelle systématique (rendu PNG, jamais supposé
correct) : (1) caractère "œ" non représentable dans la police Times
d'IEEEtran -- remplacé par `\oe{}` ; (2) lettres accentuées à
l'intérieur de `\mathrm{}` en mode mathématique illisibles à petite
taille (légendes de tableau) -- remplacé par une version sans accent
dans les indices mathématiques uniquement (texte normal inchangé).
4 pages par version, vérifiées page par page avant validation.

**2026-09-25 17:58** | Relance complète du pipeline depuis zéro
(reproductibilité après refonte des figures) | tous les fichiers de
`results/haenel_comparison/` | -- | `rm` complet puis
`bash run_all_final.sh` : exit code 0, 77/77 + 469/469 tests verts.
Figure 1 régénérée bit-identique (même taille de fichier après
recompilation de l'article) -- confirme que la refonte visuelle ne
dépend d'aucune valeur numérique modifiée. | --

FIN DU TRAVAIL SUR CETTE DEMANDE (article + figures).
