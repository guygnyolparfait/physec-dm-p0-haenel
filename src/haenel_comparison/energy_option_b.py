# ================================================================
# OPTION B — MODÈLE ÉVÉNEMENTIEL (TX/RX/CPU/IDLE), CÔTÉ CAPTEUR
# (Alice / SN), calqué sur le déroulé protocolaire DÉCRIT PAR
# Haenel et al. (Section 4.5, Fig. 3 et Fig. 4).
# ================================================================
#
# Haenel et al. ne mesure QUE l'énergie côté SN (Section 6.3.2 :
# "The energy consumption is measured continuously for each SN").
# Ce module reproduit donc uniquement le coût côté Alice, dans les
# 3 chemins protocolaires explicitement décrits par le papier :
#
#   RFF réussi (Fig. 3)   : TX(Message) -> RX(SuccessMsg)
#   RFF échoué (Fig. 4)   : TX(Message) -> RX(Challenge) ->
#                            CPU(Chaskey) -> TX(Response) ->
#                            RX(SuccessMsg)
#   MAC_ONLY (Section 6.3.1) : CPU(Chaskey) -> TX(Message+MAC) ->
#                            RX(SuccessMsg)
#
# ----------------------------------------------------------------
# CORRECTION (relecture du 25/09/2026, demandée après revue) :
# microcontrôleur du BANC D'ÉNERGIE (Section 6.3.2)
# ----------------------------------------------------------------
# Une première version de ce fichier utilisait par erreur des
# caractéristiques du MSP430FR5994. Or Haenel et al., Section 6.3.2
# ("Testbed of the Energy Efficiency Evaluation System"), énonce
# littéralement :
#
#   "we used the Texas Instrument ultra-low-power microcontroller
#   MSP430G2x and the sub-1 GHz RF transceiver CC110L [...] EnergyTrace
#   [...] was used, by means of the MSP-EXP430G2ET Launchpad
#   Evaluation Kit and Code Studio Composer (CCS)."
#
# Le MSP430FR5994 n'apparaît nulle part dans cette section : c'est
# un microcontrôleur utilisé ailleurs dans le papier (nœud
# aéroporté/drone, hors banc d'essai énergétique -- voir
# haenel_config.HAENEL_HARDWARE_DOCUMENTATION), pas la cible de
# Section 6.3.2. Toutes les constantes CPU ci-dessous ont été
# resourcées sur la famille MSP430G2x (voir
# haenel_option_b_sources.py pour le détail page/table).
#
# Le papier ne donne pas la référence exacte à l'intérieur de la
# famille "MSP430G2x" (nom générique). Le kit nommé explicitement,
# MSP-EXP430G2ET, est documenté par TI comme livré par défaut avec
# un MSP430G2553 -- retenu ici comme valeur CENTRALE. Pour ne pas
# supposer silencieusement cette référence exacte (consigne
# explicite de l'utilisateur), une borne LOW/HIGH est construite à
# partir de deux datasheets officiels réels (G2553 et G2231, un
# autre membre courant de la famille G2x/LaunchPad), couvrant à la
# fois l'incertitude "quelle puce exacte" et l'incertitude
# "typique vs maximum" du composant retenu comme central.
#
# IMPORTANT (deep-sleep) : Haenel et al., même Section 6.3.2,
# précise aussi : "This also prevented the nodes from using the
# 'deep-sleep' mode of the modules between two transmissions."
# Aucune constante ni formule de ce fichier ne modélise donc un
# mode LPM/deep-sleep MSP430 ou un état SLEEP CC110L entre deux
# messages -- une version précédente définissait de telles
# constantes (I_LPM3_A pour le FR5994, I_SLEEP_A/I_IDLE_A pour le
# CC110L) mais ne les utilisait déjà dans AUCUNE formule ; elles
# ont été supprimées ici pour ne laisser aucune ambiguïté sur ce
# point plutôt que de les laisser comme code mort trompeur.
#
# Chaque grandeur physique (courant, tension) vient d'un datasheet
# officiel, sourcé dans haenel_option_b_sources.py. Ce qui N'EST
# PAS publié (taille exacte des trames, débit radio configuré,
# coût Chaskey-12 sur MSP430) est traité par ANALYSE DE SENSIBILITÉ
# sur une plage documentée -- jamais par une valeur unique inventée
# silencieusement (voir PHASE 10B de la demande utilisateur).

from dataclasses import dataclass, replace


# ----------------------------------------------------------------
# 1. CONSTANTES OFFICIAL_DATASHEET (voir haenel_option_b_sources.py)
# ----------------------------------------------------------------

VDD_V = 3.0                          # PUBLISHED_IN_HAENEL (Table 1)

I_CALIB_A = 8.4e-3                   # OFFICIAL_DATASHEET (CC110L, FSTXON,
                                       # "also representative for other
                                       # intermediate states going from
                                       # IDLE to RX or TX, including
                                       # calibration" -- cohérent avec
                                       # l'absence de deep-sleep, voir
                                       # T_CALIB_S ci-dessous)

# ----------------------------------------------------------------
# CORRECTION (relecture du 25/09/2026) : transition d'état CC110L
# ----------------------------------------------------------------
# Une première version de ce fichier utilisait T_CALIB_S=240µs,
# documenté par le datasheet CC110L comme "240 µs From Sleep to RX
# Mode or TX Mode" (SWRS109C, page de garde) -- une transition
# DEPUIS LA VEILLE PROFONDE (SLEEP). Or Haenel et al., Section
# 6.3.2, précise explicitement que le rythme d'une transmission
# toutes les 3 s empêchait l'usage du deep-sleep pendant CETTE
# expérience précise. Utiliser silencieusement un temps de réveil
# "from Sleep" était donc incohérent avec le fait de par ailleurs
# affirmer qu'aucun deep-sleep n'est modélisé (Section 0 du
# WORK_LOG).
#
# Resourcé sur le datasheet CC110L, Table 5-11 "Overall State
# Transition Times" (SWRS109C, Section 5.19.6.1, p.43), qui donne
# les temps de transition DEPUIS IDLE (l'état de repos plausible
# entre deux messages en l'absence de deep-sleep) :
#   - IDLE -> RX ou TX, SANS calibration      :  75.1 / 75.2 µs
#   - IDLE -> RX ou TX, AVEC calibration      :  799 µs (réglages
#     par défaut SmartRF Studio, TEST0=0x0B, calibration 724 µs)
# Le papier ne publie pas la configuration exacte de calibration
# utilisée (registres MCSM0.FS_AUTOCAL, TEST0, FSCAL3) : traité par
# analyse de sensibilité, statut ASSUMED_STATE_TRANSITION, jamais
# une reproduction de l'état interne exact du CC110L.
T_CALIB_S_LOW = 75.1e-6              # OFFICIAL_DATASHEET (CC110L,
                                       # Table 5-11, IDLE->RX/TX SANS
                                       # calibration) -- ASSUMED_STATE_
                                       # TRANSITION : suppose que le
                                       # récepteur ne recalibre pas à
                                       # chaque message (borne basse)
T_CALIB_S_CENTRAL = 799e-6            # OFFICIAL_DATASHEET (CC110L,
                                       # Table 5-11, IDLE->RX/TX AVEC
                                       # calibration, réglages par
                                       # défaut SmartRF Studio) --
                                       # ASSUMED_STATE_TRANSITION :
                                       # une recalibration par message,
                                       # hypothèse centrale la plus
                                       # représentative d'un usage
                                       # "out of the box"
T_CALIB_S_HIGH = 2 * 799e-6           # ASSUMED_STATE_TRANSITION :
                                       # borne haute, deux transitions
                                       # calibrées par message (ex.
                                       # RX puis TX recalibrés
                                       # séparément) -- pas une valeur
                                       # publiée, sensibilité
                                       # volontairement pessimiste

I_RX_A_CENTRAL = 15.6e-3             # OFFICIAL_DATASHEET (CC110L,
                                       # 868 MHz, 250 kBaud, bien
                                       # au-dessus du seuil)
I_RX_A_HIGH = 16.9e-3                # OFFICIAL_DATASHEET (CC110L,
                                       # au seuil de sensibilité --
                                       # borne haute, réception plus
                                       # coûteuse)

I_TX_A_LOW = 16.4e-3                  # OFFICIAL_DATASHEET (-6 dBm)
I_TX_A_CENTRAL = 16.8e-3              # OFFICIAL_DATASHEET (0 dBm) --
                                        # valeur centrale ASSUMED pour
                                        # la puissance d'émission
                                        # (non précisée par Haenel).
I_TX_A_HIGH = 30.0e-3                 # OFFICIAL_DATASHEET (+10 dBm)

# CPU (MSP430G2x) -- courant actif par MHz d'horloge, à VDD=3.0V,
# fDCO=fMCLK=fSMCLK=1 MHz (condition de mesure du datasheet TI dans
# les deux cas ci-dessous).
I_ACTIVE_A_PER_HZ_LOW = 300e-6 / 1e6      # OFFICIAL_DATASHEET
                                            # (MSP430G2231-EP, SLAS862,
                                            # TYP, 3V, 1MHz -- autre
                                            # membre de la famille
                                            # G2x, borne basse de
                                            # l'incertitude "quelle
                                            # puce exacte")
I_ACTIVE_A_PER_HZ_CENTRAL = 330e-6 / 1e6  # OFFICIAL_DATASHEET
                                            # (MSP430G2553, SLAS735J,
                                            # TYP, 3V, 1MHz -- puce
                                            # livrée par défaut avec
                                            # le kit MSP-EXP430G2ET
                                            # nommé explicitement par
                                            # Haenel et al. Sec. 6.3.2)
I_ACTIVE_A_PER_HZ_HIGH = 420e-6 / 1e6     # OFFICIAL_DATASHEET
                                            # (MSP430G2553, SLAS735J,
                                            # MAX, 3V, 1MHz -- borne
                                            # haute du même composant
                                            # central, incertitude
                                            # "typique vs maximum")

MCU_CLOCK_HZ_CENTRAL = 1e6           # ASSUMED (fréquence d'horloge
                                       # non précisée par Haenel ;
                                       # 1 MHz est aussi la fréquence
                                       # de mesure standard des deux
                                       # datasheets TI utilisés
                                       # ci-dessus, et une valeur
                                       # basse typique pour un
                                       # capteur ultra-basse
                                       # consommation)


# ----------------------------------------------------------------
# 2. PARAMÈTRES UNAVAILABLE -- SENSIBILITÉ DOCUMENTÉE (PAS INVENTÉS)
# ----------------------------------------------------------------


@dataclass(frozen=True)
class OptionBAssumptions:
    """Un jeu d'hypothèses explicite pour les grandeurs que Haenel
    et al. ne publie pas numériquement (taille de trame, débit,
    coût Chaskey) OU publie seulement de façon générique/ambiguë
    (référence exacte de puce dans la famille MSP430G2x, puissance
    TX exacte, marge RX). CENTRAL est la valeur retenue par défaut
    pour les résultats principaux ; LOW/HIGH bornent l'analyse de
    sensibilité (Phase 10B), matériel ET protocole confondus."""

    label: str
    baud_rate_bps: float             # débit radio configuré
    frame_message_bytes: float       # Message{ID, Payload}
    frame_challenge_bytes: float     # Challenge (nonce)
    frame_response_bytes: float      # ResponseToChallenge (+MAC)
    frame_success_bytes: float       # SuccessMsg (ack court)
    frame_mac_tag_bytes: float       # taille du tag Chaskey-12 ajouté
    chaskey_cycles_per_byte: float   # coût CPU du MAC (EXTERNAL_
                                       # SCIENTIFIC_SOURCE / ASSUMED_
                                       # MAPPING, voir Section 8 --
                                       # PAS une mesure MSP430 directe)
    mcu_active_a_per_hz: float       # courant CPU actif (A par Hz)
    tx_current_a: float              # courant TX CC110L (A)
    rx_current_a: float              # courant RX CC110L (A)
    calib_transition_s: float        # durée de transition d'état
                                       # CC110L (ASSUMED_STATE_
                                       # TRANSITION, voir Section 7)


ASSUMPTIONS_CENTRAL = OptionBAssumptions(
    label="CENTRAL",
    baud_rate_bps=250_000,           # ASSUMED (250 kBaud, le débit
                                       # le plus documenté du
                                       # datasheet CC110L en 868 MHz)
    frame_message_bytes=16,          # ASSUMED (ID + payload capteur
                                       # court, ex. 2 octets ID +
                                       # quelques octets de mesure)
    frame_challenge_bytes=8,         # ASSUMED (nonce court)
    frame_response_bytes=16,         # ASSUMED (ID + payload + tag)
    frame_success_bytes=4,           # ASSUMED (accusé minimal)
    frame_mac_tag_bytes=8,           # ASSUMED (Chaskey-12 = tag 128
                                       # bits = 16 octets max,
                                       # souvent tronqué ; 8 octets
                                       # est une valeur médiane
                                       # courante)
    chaskey_cycles_per_byte=20,      # EXTERNAL_SCIENTIFIC_SOURCE /
                                       # ASSUMED_MAPPING (voir Section 8
                                       # -- Mouha et al. rapportent 9.8
                                       # cycles/octet sur ARM Cortex-M0
                                       # et 7.0 sur Cortex-M4 pour
                                       # Chaskey de base, et précisent
                                       # que Chaskey-12 est ~30% plus
                                       # lent QUE CHASKEY DE BASE sur
                                       # MSP430 16 bits -- mais NE
                                       # DONNENT PAS le chiffre absolu
                                       # MSP430. Un papier dédié existe
                                       # (Lee & Seo, IEEE, "Optimized
                                       # implementation of chaskey MAC
                                       # on 16-bit MSP430") mais son
                                       # contenu était inaccessible
                                       # cette session (accès payant).
                                       # 20 cycles/octet reste une
                                       # valeur médiane ASSUMED, ni
                                       # confirmée ni mesurée sur ce
                                       # microcontrôleur précis --
                                       # traité par sensibilité
                                       # (LOW=10, HIGH=40), jamais
                                       # présenté comme une vérité
                                       # déterminée)
    mcu_active_a_per_hz=I_ACTIVE_A_PER_HZ_CENTRAL,
    tx_current_a=I_TX_A_CENTRAL,
    rx_current_a=I_RX_A_CENTRAL,
    calib_transition_s=T_CALIB_S_CENTRAL,
)

ASSUMPTIONS_LOW = replace(
    ASSUMPTIONS_CENTRAL,
    label="LOW (débit élevé, trames courtes, MAC rapide, matériel "
          "le moins gourmand)",
    baud_rate_bps=250_000,
    frame_message_bytes=8,
    frame_challenge_bytes=4,
    frame_response_bytes=8,
    frame_success_bytes=2,
    frame_mac_tag_bytes=4,
    chaskey_cycles_per_byte=10,
    mcu_active_a_per_hz=I_ACTIVE_A_PER_HZ_LOW,
    tx_current_a=I_TX_A_LOW,
    rx_current_a=I_RX_A_CENTRAL,
    calib_transition_s=T_CALIB_S_LOW,
)

ASSUMPTIONS_HIGH = replace(
    ASSUMPTIONS_CENTRAL,
    label="HIGH (débit faible, trames longues, MAC coûteux, "
          "matériel le plus gourmand)",
    baud_rate_bps=38_400,
    frame_message_bytes=32,
    frame_challenge_bytes=16,
    frame_response_bytes=32,
    frame_success_bytes=8,
    frame_mac_tag_bytes=16,
    chaskey_cycles_per_byte=40,
    mcu_active_a_per_hz=I_ACTIVE_A_PER_HZ_HIGH,
    tx_current_a=I_TX_A_HIGH,
    rx_current_a=I_RX_A_HIGH,
    calib_transition_s=T_CALIB_S_HIGH,
)


# ----------------------------------------------------------------
# 3. TERME RÉSIDUEL CALIBRÉ (autorisé explicitement par
# l'utilisateur, Phase 10C) -- couvre ce que le modèle événementiel
# simplifié ne capture pas explicitement (overhead protocolaire non
# détaillé par Haenel et al.). Ne couvre PAS une mise en veille
# profonde : voir note "IMPORTANT (deep-sleep)" en tête de fichier.
# ----------------------------------------------------------------

# Calibré UNE SEULE FOIS ci-dessous par calibrate_residual_baseline(),
# à partir du cas RFF_ONLY (le chemin le plus simple, sans CPU ni
# aller-retour supplémentaire) -- jamais recalibré par cas pour
# forcer une correspondance parfaite sur les 4 points publiés.
CALIBRATED_RESIDUAL_BASELINE_MJ = None  # rempli au premier calcul


def _airtime_s(n_bytes, baud_rate_bps):
    return (n_bytes * 8) / baud_rate_bps


def energy_rff_success_mJ(assumptions=ASSUMPTIONS_CENTRAL):
    """Chemin Fig. 3 : TX(Message) puis RX(SuccessMsg)."""

    t_tx = _airtime_s(
        assumptions.frame_message_bytes, assumptions.baud_rate_bps
    )
    t_rx = _airtime_s(
        assumptions.frame_success_bytes, assumptions.baud_rate_bps
    )

    energy_j = (
        I_CALIB_A * assumptions.calib_transition_s
        + assumptions.tx_current_a * t_tx
        + assumptions.rx_current_a * t_rx
    ) * VDD_V

    return energy_j * 1000.0


def energy_rff_fallback_mJ(assumptions=ASSUMPTIONS_CENTRAL):
    """Chemin Fig. 4 : TX(Message) -> RX(Challenge) ->
    CPU(Chaskey) -> TX(Response) -> RX(SuccessMsg)."""

    t_tx_message = _airtime_s(
        assumptions.frame_message_bytes, assumptions.baud_rate_bps
    )
    t_rx_challenge = _airtime_s(
        assumptions.frame_challenge_bytes, assumptions.baud_rate_bps
    )
    t_tx_response = _airtime_s(
        assumptions.frame_response_bytes, assumptions.baud_rate_bps
    )
    t_rx_success = _airtime_s(
        assumptions.frame_success_bytes, assumptions.baud_rate_bps
    )

    cycles = (
        assumptions.chaskey_cycles_per_byte
        * assumptions.frame_response_bytes
    )
    t_cpu = cycles / MCU_CLOCK_HZ_CENTRAL

    energy_j = (
        I_CALIB_A * assumptions.calib_transition_s
        + assumptions.tx_current_a * t_tx_message
        + assumptions.rx_current_a * t_rx_challenge
        + assumptions.mcu_active_a_per_hz * MCU_CLOCK_HZ_CENTRAL * t_cpu
        + assumptions.tx_current_a * t_tx_response
        + assumptions.rx_current_a * t_rx_success
    ) * VDD_V

    return energy_j * 1000.0


def energy_mac_only_mJ(assumptions=ASSUMPTIONS_CENTRAL):
    """MAC_ONLY (Section 6.3.1) : CPU(Chaskey, tag ajouté au
    message) -> TX(Message+tag) -> RX(SuccessMsg). Pas de RFF, pas
    de challenge-response séparé."""

    frame_bytes = (
        assumptions.frame_message_bytes
        + assumptions.frame_mac_tag_bytes
    )

    t_tx = _airtime_s(frame_bytes, assumptions.baud_rate_bps)
    t_rx = _airtime_s(
        assumptions.frame_success_bytes, assumptions.baud_rate_bps
    )

    cycles = assumptions.chaskey_cycles_per_byte * frame_bytes
    t_cpu = cycles / MCU_CLOCK_HZ_CENTRAL

    energy_j = (
        I_CALIB_A * assumptions.calib_transition_s
        + assumptions.mcu_active_a_per_hz * MCU_CLOCK_HZ_CENTRAL * t_cpu
        + assumptions.tx_current_a * t_tx
        + assumptions.rx_current_a * t_rx
    ) * VDD_V

    return energy_j * 1000.0


def calibrate_residual_baseline_mJ(assumptions=ASSUMPTIONS_CENTRAL):
    """Calibre UN SEUL terme résiduel (mJ/message), à partir du cas
    RFF_ONLY (chemin le plus simple), pour couvrir ce que le modèle
    événementiel simplifié ne détaille pas explicitement (overhead
    protocolaire non décrit par Haenel et al. -- PAS une mise en
    veille profonde, explicitement exclue du banc d'essai, voir
    l'en-tête de ce fichier). Documenté comme
    CALIBRATED_RESIDUAL_BASELINE, jamais recalibré par cas pour
    forcer une correspondance exacte sur les 4 points publiés (voir
    Phase 10C, refus explicite du cherry-picking)."""

    from haenel_comparison.haenel_config import (
        HAENEL_FRR_CONFIGS,
        N_MESSAGES,
        MESSAGE_INTERVAL_S,
    )

    published_rff_only_per_message = (
        HAENEL_FRR_CONFIGS["RFF_ONLY"]["published_energy_mJ"]
        / N_MESSAGES
    )

    modeled_rff_success = energy_rff_success_mJ(assumptions)

    # Le résiduel couvre le reste de la période de 3 s non explicité
    # (overhead protocolaire, marges), PAS une veille profonde
    # (deep-sleep explicitement exclue par Haenel et al., Sec. 6.3.2).
    residual = published_rff_only_per_message - modeled_rff_success

    return residual


def compute_option_b_energy_mJ(
    case_name, frr=None, assumptions=ASSUMPTIONS_CENTRAL,
    include_residual=True,
):
    """Énergie moyenne par message pour un cas donné (en espérance
    sur le FRR pour les cas HYBRID), échelle Option B."""

    residual = (
        calibrate_residual_baseline_mJ(assumptions)
        if include_residual
        else 0.0
    )

    if case_name == "MAC_ONLY":
        return energy_mac_only_mJ(assumptions) + residual

    if case_name == "RFF_ONLY":
        return energy_rff_success_mJ(assumptions) + residual

    # HYBRID_FRR_05 / HYBRID_FRR_10 : espérance sur le tirage FRR.
    success = energy_rff_success_mJ(assumptions)
    fallback = energy_rff_fallback_mJ(assumptions)

    return (1 - frr) * success + frr * fallback + residual


if __name__ == "__main__":

    from haenel_comparison.haenel_config import HAENEL_FRR_CONFIGS

    print("Option B -- hypothèses CENTRAL (MSP430G2553), avec "
          "résiduel calibré\n")

    residual = calibrate_residual_baseline_mJ()
    print(f"Résiduel calibré (RFF_ONLY) : {residual:.4f} mJ/message\n")

    for case_name, frr in (
        ("RFF_ONLY", HAENEL_FRR_CONFIGS["RFF_ONLY"]["frr"]),
        ("HYBRID_FRR_05", HAENEL_FRR_CONFIGS["HYBRID_FRR_05"]["frr"]),
        ("HYBRID_FRR_10", HAENEL_FRR_CONFIGS["HYBRID_FRR_10"]["frr"]),
        ("MAC_ONLY", None),
    ):
        per_message = compute_option_b_energy_mJ(case_name, frr)
        published = HAENEL_FRR_CONFIGS[case_name]["published_energy_mJ"]

        print(
            f"{case_name:<16} Option B/message={per_message:.4f} mJ "
            f"-> total 100 messages={per_message*100:.3f} mJ "
            f"(publié={published:.3f} mJ)"
        )
