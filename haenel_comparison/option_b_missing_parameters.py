# ================================================================
# LISTE DES PARAMÈTRES MANQUANTS POUR OPTION B (modèle événementiel)
# ================================================================
#
# NE FABRIQUE AUCUNE VALEUR. Ce fichier ne fait que documenter et
# exporter en CSV les paramètres nécessaires à une décomposition
# TX/RX/CPU/idle du coût énergétique de Haenel et al., avec leur
# disponibilité réelle dans le papier. Aucune implémentation
# d'Option B ne doit démarrer tant que les lignes "NON" ci-dessous
# n'ont pas de source_needed effectivement consultée.

import csv
from pathlib import Path

OUTPUT_PATH = Path(
    "results/haenel_comparison/option_b_missing_parameters.csv"
)

FIELD_NAMES = [
    "parameter",
    "needed_for",
    "available_in_Haenel",
    "source_needed",
    "unit",
]

# available_in_Haenel : "YES" seulement si Haenel et al. publie
# EXPLICITEMENT la valeur numérique (pas seulement le nom du
# composant matériel).

OPTION_B_PARAMETERS = [
    {
        "parameter": "I_TX (courant d'émission CC110L)",
        "needed_for": "E_tx = V * I_TX * t_tx (coût par message émis)",
        "available_in_Haenel": "NO",
        "source_needed": (
            "Datasheet Texas Instruments CC110L (courant tx en "
            "fonction de la puissance de sortie configurée)"
        ),
        "unit": "mA",
    },
    {
        "parameter": "I_RX (courant de réception CC110L)",
        "needed_for": "E_rx = V * I_RX * t_rx (coût par message reçu)",
        "available_in_Haenel": "NO",
        "source_needed": "Datasheet Texas Instruments CC110L",
        "unit": "mA",
    },
    {
        "parameter": "I_idle / I_sleep (courant de veille MSP430)",
        "needed_for": (
            "E_idle = V * I_idle * t_idle (coût pendant les 3 s - "
            "temps de communication effectif entre deux messages)"
        ),
        "available_in_Haenel": "NO",
        "source_needed": "Datasheet MSP430G2x / MSP430FR5994",
        "unit": "µA ou mA (mode LPM)",
    },
    {
        "parameter": "I_cpu_active (courant CPU en calcul actif)",
        "needed_for": (
            "E_cpu = V * I_cpu * t_cpu (coût de calcul du MAC "
            "Chaskey-12 et de l'extraction RFF)"
        ),
        "available_in_Haenel": "NO",
        "source_needed": "Datasheet MSP430 (courant par MHz d'horloge)",
        "unit": "mA/MHz",
    },
    {
        "parameter": "t_tx (durée d'émission d'un message)",
        "needed_for": "E_tx",
        "available_in_Haenel": "NO",
        "source_needed": (
            "Dérivable de la taille de trame CC110L (débit "
            "symbole configuré) -- non donnée dans l'article"
        ),
        "unit": "ms",
    },
    {
        "parameter": "t_rx (durée d'écoute/réception)",
        "needed_for": "E_rx",
        "available_in_Haenel": "NO",
        "source_needed": "Idem t_tx",
        "unit": "ms",
    },
    {
        "parameter": "Cycles Chaskey-12 (calcul du MAC)",
        "needed_for": "t_cpu du calcul cryptographique",
        "available_in_Haenel": "NO",
        "source_needed": (
            "Mouha et al., 'Chaskey: An Efficient MAC Algorithm "
            "for 32-bit Microcontrollers', SAC 2014 (benchmark "
            "cycles/octet sur Cortex-M ou architectures proches -- "
            "PAS un MSP430 16 bits, à documenter comme "
            "approximation si utilisé)"
        ),
        "unit": "cycles/octet",
    },
    {
        "parameter": "Taille de trame (Message{ID,Payload})",
        "needed_for": "t_tx, t_rx (temps proportionnel à la taille)",
        "available_in_Haenel": "NO",
        "source_needed": (
            "Non donnée numériquement -- seule la structure "
            "logique du message est décrite (Section 4.5, Fig. 3-4)"
        ),
        "unit": "octets",
    },
    {
        "parameter": "Taille de trame (Challenge / ResponseToChallenge)",
        "needed_for": "t_tx, t_rx du repli MAC",
        "available_in_Haenel": "NO",
        "source_needed": "Idem",
        "unit": "octets",
    },
    {
        "parameter": "Coût d'extraction des features RFF (3 RSSI)",
        "needed_for": "t_cpu du test RFF côté GW",
        "available_in_Haenel": "NO",
        "source_needed": (
            "Non donné -- extraction RSSI généralement fournie "
            "nativement par le registre du CC110L (coût "
            "potentiellement quasi nul, mais à confirmer, pas à "
            "supposer)"
        ),
        "unit": "ms ou cycles",
    },
    {
        "parameter": "Tension d'alimentation V",
        "needed_for": "E = V * I * t (toutes les composantes)",
        "available_in_Haenel": "YES",
        "source_needed": (
            "Déjà publié : 3 V, 2400 mAh (Table 1, profil batterie)"
        ),
        "unit": "V",
    },
    {
        "parameter": "Énergie totale mesurée (référence de calibration)",
        "needed_for": "Validation croisée d'Option B contre Option A",
        "available_in_Haenel": "YES",
        "source_needed": "Déjà utilisé (Table 1, p.15)",
        "unit": "mJ",
    },
]


def export_option_b_missing_parameters(output_path=OUTPUT_PATH):

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        "w", newline="", encoding="utf-8"
    ) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELD_NAMES)
        writer.writeheader()
        writer.writerows(OPTION_B_PARAMETERS)

    return output_path


if __name__ == "__main__":

    path = export_option_b_missing_parameters()

    n_available = sum(
        1
        for row in OPTION_B_PARAMETERS
        if row["available_in_Haenel"] == "YES"
    )
    n_missing = len(OPTION_B_PARAMETERS) - n_available

    print(f"CSV écrit : {path}")
    print(
        f"{n_available}/{len(OPTION_B_PARAMETERS)} paramètres "
        f"disponibles dans Haenel et al. ; {n_missing} manquants "
        f"-- Option B ne peut pas démarrer sans les sourcer "
        f"(datasheets CC110L/MSP430, papier Chaskey)."
    )
