# ================================================================
# SOURCES POUR OPTION B — récupérées via recherche web (datasheets
# officielles TI), sourcées précisément (table/page/section).
# AUCUNE VALEUR INVENTÉE. Ce qui n'a pas pu être trouvé est marqué
# UNAVAILABLE avec une plage ASSUMED documentée pour analyse de
# sensibilité (voir energy_option_b.py).
# ================================================================

import csv
from pathlib import Path

OUTPUT_PATH = Path(
    "results/haenel_comparison/haenel_option_b_sources.csv"
)

FIELD_NAMES = [
    "parameter",
    "value",
    "unit",
    "component",
    "source_title",
    "URL_or_DOI",
    "page_section_table",
    "status",
    "notes",
]

# Datasheets récupérés le 2026-09-25 via WebSearch + WebFetch,
# texte extrait localement avec pdftotext -layout (fichiers PDF
# officiels TI).
#
# CORRECTION (relecture du 25/09/2026) : la première version de ce
# fichier sourçait le CPU sur le MSP430FR5994, qui n'est PAS le
# microcontrôleur du banc d'essai énergétique. Haenel et al.,
# Section 6.3.2, énonce littéralement : "we used the Texas
# Instrument ultra-low-power microcontroller MSP430G2x [...] by
# means of the MSP-EXP430G2ET Launchpad Evaluation Kit". Le
# FR5994 sert ailleurs dans le papier (nœud aéroporté/drone). Les
# lignes CPU ci-dessous ont été resourcées sur la famille MSP430G2x
# (confirmé via PMC, https://pmc.ncbi.nlm.nih.gov/articles/PMC8230913/,
# texte intégral en accès libre).

SOURCES = [
    # ------------------------------------------------------------
    # CC110L (radio) -- OFFICIAL_DATASHEET
    # ------------------------------------------------------------
    {
        "parameter": "I_sleep (SLEEP state, régulateur off)",
        "value": "0.2 (typ) / 1 (max)",
        "unit": "µA",
        "component": "CC110L",
        "source_title": "CC110L Value Line Transceiver Datasheet",
        "URL_or_DOI": "https://www.ti.com/lit/ds/symlink/cc110l.pdf",
        "page_section_table": "SWRS109C, Section 4.5 (Table), p.8",
        "status": "OFFICIAL_DATASHEET",
        "notes": "VDD=3.0V, TA=25°C sauf indication contraire.",
    },
    {
        "parameter": "I_idle (IDLE state, régul.+XOSC seuls)",
        "value": 1.7,
        "unit": "mA",
        "component": "CC110L",
        "source_title": "CC110L Value Line Transceiver Datasheet",
        "URL_or_DOI": "https://www.ti.com/lit/ds/symlink/cc110l.pdf",
        "page_section_table": "SWRS109C, Section 4.5, p.8",
        "status": "OFFICIAL_DATASHEET",
        "notes": "",
    },
    {
        "parameter": "I_calib (FSTXON, synthé actif, calibration)",
        "value": 8.4,
        "unit": "mA",
        "component": "CC110L",
        "source_title": "CC110L Value Line Transceiver Datasheet",
        "URL_or_DOI": "https://www.ti.com/lit/ds/symlink/cc110l.pdf",
        "page_section_table": "SWRS109C, Section 4.5, p.8",
        "status": "OFFICIAL_DATASHEET",
        "notes": (
            "\"Also representative for other intermediate states "
            "going from IDLE to RX or TX, including calibration.\""
        ),
    },
    {
        "parameter": "Durée de transition d'état IDLE->RX/TX "
                      "(calib_transition_s) [LOW/CENTRAL/HIGH]",
        "value": "75.1 (LOW, sans calib.) / 799 (CENTRAL, avec "
                  "calib. défaut) / 1598 (HIGH, 2x calib.)",
        "unit": "µs",
        "component": "CC110L",
        "source_title": "CC110L Value Line Transceiver Datasheet",
        "URL_or_DOI": "https://www.ti.com/lit/ds/symlink/cc110l.pdf",
        "page_section_table": "SWRS109C, Section 5.19.6.1, Table "
                               "5-11 \"Overall State Transition "
                               "Times\", p.43",
        "status": "ASSUMED_STATE_TRANSITION",
        "notes": (
            "CORRECTION (25/09/2026) : remplace une première valeur "
            "de 240 µs (\"From Sleep to RX Mode or TX Mode\", page de "
            "garde du même datasheet) -- incohérente avec le fait que "
            "Haenel et al. (Section 6.3.2) exclut explicitement le "
            "deep-sleep de ce banc d'essai. Table 5-11 donne les "
            "temps de transition DEPUIS IDLE (état de repos plausible "
            "en l'absence de deep-sleep) : 75.1/75.2 µs sans "
            "calibration, 799 µs avec calibration (réglages par "
            "défaut SmartRF Studio). Le papier ne publie pas la "
            "configuration de calibration réelle (registres "
            "MCSM0.FS_AUTOCAL, TEST0, FSCAL3) : statut "
            "ASSUMED_STATE_TRANSITION, jamais une reproduction de "
            "l'état interne exact du CC110L. HIGH (1598 µs = 2x799) "
            "est une borne pessimiste non publiée, pour couvrir le "
            "cas de deux transitions calibrées par message."
        ),
    },
    {
        "parameter": "I_rx (868 MHz, 250 kBaud, bien au-dessus du "
                      "seuil de sensibilité)",
        "value": 15.6,
        "unit": "mA",
        "component": "CC110L",
        "source_title": "CC110L Value Line Transceiver Datasheet",
        "URL_or_DOI": "https://www.ti.com/lit/ds/symlink/cc110l.pdf",
        "page_section_table": "SWRS109C, Section 4.5, p.8 (table "
                               "\"Current consumption, 868/915 MHz\")",
        "status": "OFFICIAL_DATASHEET",
        "notes": "Bande utilisée par Haenel et al. (868-870 MHz).",
    },
    {
        "parameter": "I_rx (868 MHz, 250 kBaud, au seuil de "
                      "sensibilité)",
        "value": 16.9,
        "unit": "mA",
        "component": "CC110L",
        "source_title": "CC110L Value Line Transceiver Datasheet",
        "URL_or_DOI": "https://www.ti.com/lit/ds/symlink/cc110l.pdf",
        "page_section_table": "SWRS109C, Section 4.5, p.8",
        "status": "OFFICIAL_DATASHEET",
        "notes": "Borne haute pour analyse de sensibilité.",
    },
    {
        "parameter": "I_tx (868 MHz, 0 dBm)",
        "value": 16.8,
        "unit": "mA",
        "component": "CC110L",
        "source_title": "CC110L Value Line Transceiver Datasheet",
        "URL_or_DOI": "https://www.ti.com/lit/ds/symlink/cc110l.pdf",
        "page_section_table": "SWRS109C, Section 4.5, p.8",
        "status": "OFFICIAL_DATASHEET",
        "notes": (
            "Puissance d'émission réelle non précisée par Haenel "
            "et al. -- 0 dBm retenu comme valeur centrale "
            "raisonnable pour un capteur IoT courte portée."
        ),
    },
    {
        "parameter": "I_tx (868 MHz, -6 dBm) [borne basse]",
        "value": 16.4,
        "unit": "mA",
        "component": "CC110L",
        "source_title": "CC110L Value Line Transceiver Datasheet",
        "URL_or_DOI": "https://www.ti.com/lit/ds/symlink/cc110l.pdf",
        "page_section_table": "SWRS109C, Section 4.5, p.8",
        "status": "OFFICIAL_DATASHEET",
        "notes": "Borne basse pour analyse de sensibilité.",
    },
    {
        "parameter": "I_tx (868 MHz, +10 dBm) [borne haute]",
        "value": 30.0,
        "unit": "mA",
        "component": "CC110L",
        "source_title": "CC110L Value Line Transceiver Datasheet",
        "URL_or_DOI": "https://www.ti.com/lit/ds/symlink/cc110l.pdf",
        "page_section_table": "SWRS109C, Section 4.5, p.8",
        "status": "OFFICIAL_DATASHEET",
        "notes": (
            "Borne haute pour analyse de sensibilité (portée "
            "longue distance, peu probable pour un test en "
            "intérieur/proche comme celui de Haenel et al.)."
        ),
    },
    # ------------------------------------------------------------
    # MSP430G2x (microcontrôleur DU BANC D'ÉNERGIE, Section 6.3.2)
    # -- OFFICIAL_DATASHEET
    # ------------------------------------------------------------
    {
        "parameter": "Correspondance MSP-EXP430G2ET -> puce MSP430G2x "
                      "livrée par défaut",
        "value": "MSP430G2553",
        "unit": "-",
        "component": "MSP-EXP430G2ET (kit nommé par Haenel et al.)",
        "source_title": "Texas Instruments -- fiches produit/kit "
                          "MSP-EXP430G2ET (référence croisée "
                          "distributeur/TI)",
        "URL_or_DOI": "https://www.ti.com/lit/ug/slau772a/slau772a.pdf",
        "page_section_table": "SLAU772A, page de garde (kit "
                               "\"MSP430G2553 LaunchPad Development "
                               "Kit (MSP-EXP430G2ET)\")",
        "status": "DERIVED",
        "notes": (
            "Haenel et al. écrit seulement \"MSP430G2x\" (nom de "
            "famille générique), sans préciser la référence exacte "
            "de la puce. Le kit MSP-EXP430G2ET explicitement nommé "
            "en Section 6.3.2 est documenté par TI comme livré par "
            "défaut avec un MSP430G2553 -- retenu comme hypothèse "
            "CENTRALE, jamais présentée comme confirmée par le "
            "papier lui-même. Voir bornes LOW/HIGH ci-dessous pour "
            "l'incertitude documentée sur ce choix."
        ),
    },
    {
        "parameter": "I_active (mode actif, 1 MHz, 3.0V) [CENTRAL]",
        "value": "330 (typ) / 420 (max)",
        "unit": "µA/MHz",
        "component": "MSP430G2553 (MSP430G2x53/G2x13 family)",
        "source_title": "MSP430G2x53, MSP430G2x13 Mixed Signal "
                          "Microcontroller Datasheet",
        "URL_or_DOI": "https://www.ti.com/lit/ds/symlink/msp430g2553.pdf",
        "page_section_table": "SLAS735J, Electrical Characteristics, "
                               "table \"Active Mode Supply Current "
                               "Into VCC\", paramètre IAM,1MHz, "
                               "ligne VCC=3V",
        "status": "OFFICIAL_DATASHEET",
        "notes": (
            "Condition de mesure du datasheet : fDCO=fMCLK=fSMCLK="
            "1 MHz, programme exécuté en flash. TYP retenu comme "
            "valeur centrale, MAX comme borne haute de sensibilité "
            "(incertitude silicium typique/maximum, PAS incertitude "
            "sur la puce elle-même)."
        ),
    },
    {
        "parameter": "I_active (mode actif, 1 MHz, 3.0V) [borne "
                      "basse, autre membre famille G2x]",
        "value": "300 (typ) / 390 (max)",
        "unit": "µA/MHz",
        "component": "MSP430G2231-EP",
        "source_title": "MSP430G2231-EP Mixed Signal Microcontroller "
                          "Datasheet",
        "URL_or_DOI": (
            "https://www.ti.com/lit/ds/symlink/msp430g2231-ep.pdf"
        ),
        "page_section_table": "SLAS862, Electrical Characteristics, "
                               "table \"Active Mode Supply Current "
                               "Into VCC\", paramètre IAM,1MHz, "
                               "ligne VCC=3V",
        "status": "OFFICIAL_DATASHEET",
        "notes": (
            "TYP (300 µA/MHz) utilisé comme borne LOW de l'analyse "
            "de sensibilité, pour couvrir l'incertitude \"quelle "
            "puce exacte de la famille MSP430G2x\" (Haenel et al. "
            "ne précise pas la référence). Variante qualifiée "
            "temperature étendue (-EP) : le cœur électrique est "
            "identique à la version standard (SLAS694) à "
            "température ambiante, utilisée ici uniquement comme "
            "point de comparaison intra-famille, pas comme le "
            "composant réellement utilisé par Haenel et al."
        ),
    },
    {
        "parameter": "VDD (tension d'alimentation du système)",
        "value": 3.0,
        "unit": "V",
        "component": "Système (CC110L + MSP430)",
        "source_title": "Haenel et al. 2021 (Table 1) + datasheets "
                          "TI (mesures à 3.0V)",
        "URL_or_DOI": "https://doi.org/10.3390/s21124034",
        "page_section_table": "Table 1, p.15 (\"3V, 2400mAh\")",
        "status": "PUBLISHED_IN_HAENEL",
        "notes": "Cohérent avec les tables datasheets, prises à 3.0V.",
    },
    {
        "parameter": "Deep-sleep / LPM utilisé entre deux "
                      "transmissions durant le banc d'essai "
                      "énergétique ?",
        "value": "NON",
        "unit": "-",
        "component": "MSP430G2x + CC110L (banc d'essai complet)",
        "source_title": "Haenel et al. 2021",
        "URL_or_DOI": "https://doi.org/10.3390/s21124034",
        "page_section_table": "Section 6.3.2, p.14",
        "status": "PUBLISHED_IN_HAENEL",
        "notes": (
            "Citation littérale : \"The SNs transmit a data packet "
            "(the temperature) every 3 s to a GW; this is much "
            "faster and more energy-consuming than real-life "
            "scenarios. This also prevented the nodes from using "
            "the 'deep-sleep' mode of the modules between two "
            "transmissions.\" Conséquence directe pour ce module : "
            "energy_option_b.py ne modélise aucun courant LPM/"
            "deep-sleep (MSP430) ni SLEEP (CC110L) entre deux "
            "messages -- le confirmer explicitement ici évite de "
            "réintroduire cette hypothèse par erreur plus tard."
        ),
    },
    # ------------------------------------------------------------
    # Chaskey-12 sur MSP430 -- EXTERNAL_SCIENTIFIC_SOURCE /
    # ASSUMED_MAPPING (recherché le 25/09/2026, voir notes -- le
    # chiffre ABSOLU MSP430 reste UNAVAILABLE malgré la recherche)
    # ------------------------------------------------------------
    {
        "parameter": "Coût Chaskey (8 tours, base) sur ARM Cortex-M",
        "value": "9.8 (Cortex-M0) / 7.0 (Cortex-M4)",
        "unit": "cycles/octet",
        "component": "ARM Cortex-M0 / Cortex-M4 (PAS le MSP430 de "
                      "Haenel et al.)",
        "source_title": "Mouha, Mennink, Van Herrewege, Watanabe, "
                          "Preneel, Verbauwhede, \"Chaskey: A MAC "
                          "Algorithm for Microcontrollers -- Status "
                          "Update and Proposal of Chaskey-12\", "
                          "Cryptology ePrint Archive 2015/1182",
        "URL_or_DOI": "https://eprint.iacr.org/2015/1182.pdf",
        "page_section_table": "Section \"Conclusion\", p.8 (PDF "
                               "récupéré et lu intégralement le "
                               "25/09/2026)",
        "status": "EXTERNAL_SCIENTIFIC_SOURCE",
        "notes": (
            "Chiffres réels et vérifiés, mais sur ARM 32 bits -- PAS "
            "le MSP430 16 bits du banc d'essai Haenel et al. Utilisés "
            "uniquement comme point d'ancrage de sensibilité, jamais "
            "comme le coût réel de Haenel et al."
        ),
    },
    {
        "parameter": "Ralentissement Chaskey-12 (12 tours) vs "
                      "Chaskey de base, SUR MSP430 16 bits",
        "value": "~30% plus lent (relatif, pas de valeur absolue)",
        "unit": "ratio",
        "component": "MSP430 16 bits (architecture générique, "
                      "implémentation non précisée)",
        "source_title": "Même source que ci-dessus (2015/1182)",
        "URL_or_DOI": "https://eprint.iacr.org/2015/1182.pdf",
        "page_section_table": "Section 2.3 et Conclusion, p.4 et p.8 : "
                               "\"about 30% slower on 16-bit Texas "
                               "Instrument MSP430 and 8-bit Atmel AVR "
                               "ATmega128\" (implémentation FELICS de "
                               "Jason Smith)",
        "status": "EXTERNAL_SCIENTIFIC_SOURCE",
        "notes": (
            "C'est la citation la PLUS PERTINENTE trouvée cette "
            "session : elle mentionne explicitement le MSP430 16 "
            "bits. Mais elle ne donne qu'un ratio relatif (+30%), pas "
            "le nombre de cycles/octet absolu de Chaskey DE BASE sur "
            "MSP430 -- impossible d'en dériver un chiffre absolu sans "
            "fabriquer une valeur."
        ),
    },
    {
        "parameter": "Coût Chaskey-12 (cycles/octet, ABSOLU, sur "
                      "MSP430 16 bits)",
        "value": None,
        "unit": "cycles/octet",
        "component": "MSP430 (calcul MAC)",
        "source_title": "Lee & Seo, \"Optimized implementation of "
                          "chaskey MAC on 16-bit MSP430\", IEEE "
                          "(article dédié à cette architecture "
                          "précise, existe mais inaccessible)",
        "URL_or_DOI": "https://ieeexplore.ieee.org/document/7993930/",
        "page_section_table": "NON ACCESSIBLE CETTE SESSION (accès "
                               "payant IEEE Xplore / ResearchGate)",
        "status": "UNAVAILABLE",
        "notes": (
            "NON FOURNI PAR HAENEL, ET NON ACCESSIBLE MALGRÉ "
            "RECHERCHE ACTIVE (25/09/2026) : un article scientifique "
            "dédié à Chaskey MAC sur MSP430 16 bits existe bel et "
            "bien (Lee & Seo, IEEE Conference), mais son contenu "
            "était derrière un péage d'accès cette session -- "
            "recherché via WebSearch/WebFetch, non fabriqué. La "
            "plage ASSUMED utilisée dans energy_option_b.py "
            "(10-40 cycles/octet, médiane 20) reste une hypothèse de "
            "sensibilité, ni confirmée ni mesurée sur ce "
            "microcontrôleur précis -- statut ASSUMED_MAPPING pour "
            "la valeur elle-même (dérivée par extrapolation "
            "raisonnée des chiffres ARM ci-dessus, élargie pour "
            "couvrir l'incertitude d'architecture), UNAVAILABLE pour "
            "la mesure MSP430 directe."
        ),
    },
    {
        "parameter": "Taille de trame Message{ID, Payload}",
        "value": None,
        "unit": "octets",
        "component": "Protocole applicatif",
        "source_title": "Haenel et al. 2021",
        "URL_or_DOI": "https://doi.org/10.3390/s21124034",
        "page_section_table": "Non donné numériquement (Section 4.5, "
                               "Fig. 3-4 : structure logique "
                               "seulement)",
        "status": "UNAVAILABLE",
        "notes": (
            "NON FOURNI PAR HAENEL — À MODÉLISER : une plage "
            "ASSUMED de 8 à 32 octets (ID + payload capteur "
            "court) est utilisée pour l'analyse de sensibilité."
        ),
    },
    {
        "parameter": "Débit radio configuré (baud rate)",
        "value": None,
        "unit": "kBaud",
        "component": "CC110L",
        "source_title": "Haenel et al. 2021",
        "URL_or_DOI": "https://doi.org/10.3390/s21124034",
        "page_section_table": "Non précisé dans le texte principal",
        "status": "UNAVAILABLE",
        "notes": (
            "NON FOURNI PAR HAENEL — ASSUMED : 250 kBaud retenu "
            "(débit le plus documenté dans le datasheet CC110L "
            "pour la bande 868 MHz), avec 38.4 kBaud comme borne "
            "basse pour la sensibilité."
        ),
    },
]


def export_sources(output_path=OUTPUT_PATH):

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        "w", newline="", encoding="utf-8"
    ) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELD_NAMES)
        writer.writeheader()
        writer.writerows(SOURCES)

    return output_path


if __name__ == "__main__":

    path = export_sources()

    by_status = {}
    for row in SOURCES:
        by_status.setdefault(row["status"], 0)
        by_status[row["status"]] += 1

    print(f"CSV écrit : {path}")
    for status, count in by_status.items():
        print(f"  {status}: {count}")
