# On importe la bibliothèque math de Python.
#
# Elle fournit :
# - ceil pour arrondir le nombre de symboles vers le haut.
import math


# On importe les actions et les structures déjà définies
# dans models.py.
#
# AuthenticationAction permet de distinguer A1 et A2.
#
# KeyAction permet de distinguer K0, K1a, K1b et K2.
#
# CostMetrics sert à regrouper tous les coûts
# calculés pour une décision complète.
from physec_dm.models import (
    AuthenticationAction,
    KeyAction,
    CostMetrics
)


# ================================================================
# 1. TEMPS D'ANTENNE LORA
# ================================================================


# Cette fonction calcule la durée d'un symbole LoRa.
#
# Dans la modélisation :
#
# T_sym = 2 ** SF / BW
#
# Cette fonction correspond à CO-EQ68.
def calculate_symbol_time(
    spreading_factor,
    bandwidth_hz
):

    # Le facteur d'étalement doit être positif.
    if spreading_factor <= 0:

        raise ValueError(
            "Le facteur d'étalement doit être "
            "strictement positif."
        )

    # La bande passante doit être positive,
    # car elle se trouve au dénominateur.
    if bandwidth_hz <= 0:

        raise ValueError(
            "La bande passante doit être "
            "strictement positive."
        )

    symbol_time_s = (
        2 ** spreading_factor
        / bandwidth_hz
    )

    return symbol_time_s


# Cette fonction calcule le temps du préambule.
#
# Dans la modélisation :
#
# T_pre = (N_pre + 4.25) * T_sym
#
# Cette fonction correspond à CO-EQ69.
def calculate_preamble_time(
    preamble_symbols,
    symbol_time_s
):

    # Le nombre de symboles programmés
    # ne peut pas être négatif.
    if preamble_symbols < 0:

        raise ValueError(
            "Le nombre de symboles du préambule "
            "ne peut pas être négatif."
        )

    # La durée d'un symbole doit être positive.
    if symbol_time_s <= 0:

        raise ValueError(
            "La durée d'un symbole doit être "
            "strictement positive."
        )

    preamble_time_s = (
        preamble_symbols
        + 4.25
    ) * symbol_time_s

    return preamble_time_s


# Cette fonction calcule la valeur intermédiaire Xi(M).
#
# Dans la modélisation :
#
# Xi(M) = ceil(
#     [8M - 4SF + 28 + 16CRC - 20IH]
#     / [4(SF - 2DE)]
# )
#
# Cette fonction correspond à CO-EQ70.
def calculate_payload_intermediate(
    payload_bytes,
    spreading_factor,
    crc_enabled,
    implicit_header,
    low_data_rate_optimization
):

    # La charge utile est une taille en octets.
    # Elle ne peut donc pas être négative.
    if payload_bytes < 0:

        raise ValueError(
            "La charge utile ne peut pas être négative."
        )

    if spreading_factor <= 0:

        raise ValueError(
            "Le facteur d'étalement doit être "
            "strictement positif."
        )

    # Les trois paramètres suivants doivent être booléens.
    if not isinstance(crc_enabled, bool):

        raise ValueError(
            "crc_enabled doit être booléen."
        )

    if not isinstance(implicit_header, bool):

        raise ValueError(
            "implicit_header doit être booléen."
        )

    if not isinstance(
        low_data_rate_optimization,
        bool
    ):

        raise ValueError(
            "low_data_rate_optimization "
            "doit être booléen."
        )

    # La formule Semtech utilise des valeurs 0 ou 1.
    crc_value = 1 if crc_enabled else 0
    implicit_header_value = (
        1 if implicit_header else 0
    )
    de_value = (
        1 if low_data_rate_optimization else 0
    )

    numerator = (
        8 * payload_bytes
        - 4 * spreading_factor
        + 28
        + 16 * crc_value
        - 20 * implicit_header_value
    )

    denominator = (
        4
        * (
            spreading_factor
            - 2 * de_value
        )
    )

    # Le dénominateur doit être positif.
    if denominator <= 0:

        raise ValueError(
            "Les paramètres LoRa produisent "
            "un dénominateur invalide."
        )

    # math.ceil arrondit vers l'entier supérieur.
    payload_intermediate = math.ceil(
        numerator
        / denominator
    )

    return payload_intermediate


# Cette fonction calcule le nombre de symboles utiles.
#
# Dans la modélisation :
#
# N_pl = 8 + max(
#     0,
#     (CR_idx + 4) * Xi(M)
# )
#
# Cette fonction correspond à CO-EQ71.
def calculate_payload_symbol_count(
    payload_bytes,
    spreading_factor,
    coding_rate_index,
    crc_enabled,
    implicit_header,
    low_data_rate_optimization
):

    # L'indice du coding rate doit appartenir
    # aux quatre valeurs prévues par LoRa.
    if coding_rate_index not in [
        1,
        2,
        3,
        4
    ]:

        raise ValueError(
            "coding_rate_index doit appartenir "
            "à {1, 2, 3, 4}."
        )

    payload_intermediate = (
        calculate_payload_intermediate(
            payload_bytes=payload_bytes,
            spreading_factor=spreading_factor,
            crc_enabled=crc_enabled,
            implicit_header=implicit_header,
            low_data_rate_optimization=(
                low_data_rate_optimization
            )
        )
    )

    payload_symbol_count = (
        8
        + max(
            0,
            (
                coding_rate_index
                + 4
            )
            * payload_intermediate
        )
    )

    return payload_symbol_count


# Cette fonction calcule le Time-on-Air complet
# d'une trame LoRa.
#
# Dans la modélisation :
#
# T_air(M) = T_pre + N_pl * T_sym
#
# Cette fonction correspond à CO-EQ72.
def calculate_time_on_air(
    payload_bytes,
    parameters
):

    symbol_time_s = calculate_symbol_time(
        spreading_factor=(
            parameters.spreading_factor
        ),
        bandwidth_hz=(
            parameters.bandwidth_hz
        )
    )

    preamble_time_s = calculate_preamble_time(
        preamble_symbols=(
            parameters.preamble_symbols
        ),
        symbol_time_s=symbol_time_s
    )

    payload_symbol_count = (
        calculate_payload_symbol_count(
            payload_bytes=payload_bytes,
            spreading_factor=(
                parameters.spreading_factor
            ),
            coding_rate_index=(
                parameters.coding_rate_index
            ),
            crc_enabled=(
                parameters.crc_enabled
            ),
            implicit_header=(
                parameters.implicit_header
            ),
            low_data_rate_optimization=(
                parameters.low_data_rate_optimization
            )
        )
    )

    time_on_air_s = (
        preamble_time_s
        + payload_symbol_count
        * symbol_time_s
    )

    return time_on_air_s


# ================================================================
# 2. ÉNERGIE RADIO ET CPU
# ================================================================


# Cette fonction calcule l'énergie d'émission.
#
# Dans la modélisation :
#
# E_tx(M) = V_DD * I_tx * T_air(M)
#
# Cette fonction correspond à la première partie
# de CO-EQ73.
def calculate_tx_energy(
    payload_bytes,
    parameters
):

    time_on_air_s = calculate_time_on_air(
        payload_bytes,
        parameters
    )

    tx_energy_j = (
        parameters.supply_voltage_v
        * parameters.tx_current_a
        * time_on_air_s
    )

    return tx_energy_j


# Cette fonction calcule l'énergie de réception.
#
# Dans la modélisation :
#
# E_rx(M) = V_DD * I_rx * T_air(M)
#
# Cette fonction correspond à la deuxième partie
# de CO-EQ73.
def calculate_rx_energy(
    payload_bytes,
    parameters
):

    time_on_air_s = calculate_time_on_air(
        payload_bytes,
        parameters
    )

    rx_energy_j = (
        parameters.supply_voltage_v
        * parameters.rx_current_a
        * time_on_air_s
    )

    return rx_energy_j


# Cette fonction calcule la durée d'un traitement CPU.
#
# La durée est :
#
# T_cpu = N_cycles / f_CPU
#
# Cette relation sert ensuite au calcul de l'énergie CPU.
def calculate_cpu_time(
    cycle_count,
    cpu_frequency_hz
):

    if cycle_count is None:

        raise ValueError(
            "Le nombre de cycles CPU doit être défini."
        )

    if cycle_count < 0:

        raise ValueError(
            "Le nombre de cycles CPU "
            "ne peut pas être négatif."
        )

    if cpu_frequency_hz <= 0:

        raise ValueError(
            "La fréquence CPU doit être "
            "strictement positive."
        )

    cpu_time_s = (
        cycle_count
        / cpu_frequency_hz
    )

    return cpu_time_s


# Cette fonction calcule l'énergie d'un traitement CPU.
#
# Dans la modélisation :
#
# E_cpu(N_cycles) =
#     N_cycles * V_DD * I_cpu / f_CPU
#
# Cette fonction correspond à CO-EQ75.
def calculate_cpu_energy(
    cycle_count,
    parameters
):

    cpu_time_s = calculate_cpu_time(
        cycle_count=cycle_count,
        cpu_frequency_hz=(
            parameters.cpu_frequency_hz
        )
    )

    cpu_energy_j = (
        parameters.supply_voltage_v
        * parameters.cpu_current_a
        * cpu_time_s
    )

    return cpu_energy_j


# Cette fonction calcule l'énergie et la durée
# du calcul AES-CMAC chez Alice.
#
# E_MAC est calculée avec l'équation CPU.
#
# T_MAC est le nombre de cycles divisé
# par la fréquence du processeur.
def calculate_mac_costs(
    parameters
):

    if parameters.mac_cycles is None:

        raise ValueError(
            "mac_cycles doit être défini "
            "avant de calculer le coût du MAC."
        )

    mac_energy_j = calculate_cpu_energy(
        cycle_count=parameters.mac_cycles,
        parameters=parameters
    )

    mac_latency_s = calculate_cpu_time(
        cycle_count=parameters.mac_cycles,
        cpu_frequency_hz=(
            parameters.cpu_frequency_hz
        )
    )

    return mac_energy_j, mac_latency_s


# ================================================================
# 3. ÉNERGIE DE BASE D'UNE PÉRIODE
# ================================================================


# Cette fonction calcule l'énergie normale
# consommée pendant une période.
#
# Dans la modélisation :
#
# E_base =
#     E_sens
#     + E_app
#     + E_tx(M_data)
#     + E_RXwin
#     + E_sleep
#
# Cette fonction correspond à CO-EQ77.
#
# Les composantes symboliques doivent être définies
# avant d'annoncer une autonomie absolue.
def calculate_base_energy(
    parameters
):

    required_parameters = {
        "sensing_energy_j":
            parameters.sensing_energy_j,

        "application_energy_j":
            parameters.application_energy_j,

        "receive_windows_energy_j":
            parameters.receive_windows_energy_j,

        "sleep_energy_j":
            parameters.sleep_energy_j
    }

    for parameter_name in required_parameters:

        parameter_value = required_parameters[
            parameter_name
        ]

        if parameter_value is None:

            raise ValueError(
                parameter_name
                + " doit être défini "
                "pour calculer l'énergie de base."
            )

        if parameter_value < 0:

            raise ValueError(
                parameter_name
                + " ne peut pas être négatif."
            )

    data_tx_energy_j = calculate_tx_energy(
        payload_bytes=(
            parameters.data_payload_bytes
        ),
        parameters=parameters
    )

    base_energy_j = (
        parameters.sensing_energy_j
        + parameters.application_energy_j
        + data_tx_energy_j
        + parameters.receive_windows_energy_j
        + parameters.sleep_energy_j
    )

    return base_energy_j


# Cette fonction additionne l'énergie de base
# et le surcoût de sécurité.
#
# Dans la modélisation :
#
# E_t(D) = E_base,t + E_sec,t(D)
#
# Cette fonction correspond à CO-EQ76.
def calculate_total_energy(
    base_energy_j,
    security_energy_j
):

    if base_energy_j < 0:

        raise ValueError(
            "L'énergie de base ne peut pas être négative."
        )

    if security_energy_j < 0:

        raise ValueError(
            "L'énergie de sécurité "
            "ne peut pas être négative."
        )

    total_energy_j = (
        base_energy_j
        + security_energy_j
    )

    return total_energy_j


# ================================================================
# 4. COÛTS D'AUTHENTIFICATION
# ================================================================


# Cette fonction calcule les coûts de A1.
#
# Dans la modélisation :
#
# E_sec(A1) =
#     E_MAC
#     + E_tx(M_data + M_tag)
#     - E_tx(M_data)
#
# L_auth(A1) =
#     T_MAC
#     + T_air(M_data + M_tag)
#     - T_air(M_data)
#
# Ces relations correspondent à CO-EQ78 et CO-EQ79.
def calculate_a1_costs(
    parameters
):

    mac_energy_j, mac_latency_s = (
        calculate_mac_costs(
            parameters
        )
    )

    data_payload_bytes = (
        parameters.data_payload_bytes
    )

    protected_payload_bytes = (
        parameters.data_payload_bytes
        + parameters.mac_tag_bytes
    )

    normal_tx_energy_j = calculate_tx_energy(
        payload_bytes=data_payload_bytes,
        parameters=parameters
    )

    protected_tx_energy_j = calculate_tx_energy(
        payload_bytes=protected_payload_bytes,
        parameters=parameters
    )

    normal_airtime_s = calculate_time_on_air(
        payload_bytes=data_payload_bytes,
        parameters=parameters
    )

    protected_airtime_s = calculate_time_on_air(
        payload_bytes=protected_payload_bytes,
        parameters=parameters
    )

    incremental_airtime_s = (
        protected_airtime_s
        - normal_airtime_s
    )

    authentication_energy_j = (
        mac_energy_j
        + protected_tx_energy_j
        - normal_tx_energy_j
    )

    authentication_latency_s = (
        mac_latency_s
        + incremental_airtime_s
    )

    # A1 est déterministe dans ce modèle.
    #
    # L'espérance et le pire cas sont donc identiques.
    return {
        "expected_energy_j":
            authentication_energy_j,

        "worst_case_energy_j":
            authentication_energy_j,

        "expected_latency_s":
            authentication_latency_s,

        "worst_case_latency_s":
            authentication_latency_s,

        # Le duty-cycle dépend uniquement
        # du temps d'émission supplémentaire d'Alice.
        "worst_case_airtime_s":
            incremental_airtime_s
    }


# Cette fonction calcule l'énergie
# du défi-réponse cryptographique.
#
# Dans la modélisation :
#
# E_CR =
#     E_rx(M_chal)
#     + E_MAC
#     + E_tx(M_resp)
#
# Cette fonction correspond à CO-EQ80.
#
# La latence complète L_CR reste un paramètre
# du protocole, car elle peut contenir des attentes
# qui ne se réduisent pas au seul Time-on-Air.
def calculate_challenge_response_costs(
    parameters
):

    if (
        parameters.challenge_response_latency_s
        is None
    ):

        raise ValueError(
            "challenge_response_latency_s "
            "doit être défini."
        )

    if parameters.challenge_response_latency_s < 0:

        raise ValueError(
            "La latence du défi-réponse "
            "ne peut pas être négative."
        )

    mac_energy_j, mac_latency_s = (
        calculate_mac_costs(
            parameters
        )
    )

    challenge_rx_energy_j = calculate_rx_energy(
        payload_bytes=(
            parameters.challenge_bytes
        ),
        parameters=parameters
    )

    response_tx_energy_j = calculate_tx_energy(
        payload_bytes=(
            parameters.response_bytes
        ),
        parameters=parameters
    )

    challenge_response_energy_j = (
        challenge_rx_energy_j
        + mac_energy_j
        + response_tx_energy_j
    )

    # Cette durée radio seule est conservée
    # pour la traçabilité et les tests.
    radio_and_cpu_latency_s = (
        calculate_time_on_air(
            parameters.challenge_bytes,
            parameters
        )
        + mac_latency_s
        + calculate_time_on_air(
            parameters.response_bytes,
            parameters
        )
    )

    challenge_response_latency_s = (
        parameters.challenge_response_latency_s
    )

    return {
        "energy_j":
            challenge_response_energy_j,

        "latency_s":
            challenge_response_latency_s,

        "radio_and_cpu_latency_s":
            radio_and_cpu_latency_s,

        # Alice émet seulement la réponse.
        #
        # La réception du défi ne consomme pas
        # de duty-cycle d'émission.
        "alice_tx_airtime_s":
            calculate_time_on_air(
                parameters.response_bytes,
                parameters
            )
    }


# Cette fonction calcule les coûts de A2.
#
# Dans la modélisation :
#
# E_sec(A2) = FRR * E_CR
#
# L_auth(A2) =
#     T_RFF,Bob
#     + FRR * L_CR
#
# Ces relations correspondent à CO-EQ81 et CO-EQ82.
#
# Le pire cas utilisé pour l'admissibilité est :
#
# T_RFF,Bob + L_CR
def calculate_a2_costs(
    authentication_metrics,
    parameters
):

    if (
        authentication_metrics.authentication_action
        != AuthenticationAction.A2
    ):

        raise ValueError(
            "Les métriques fournies doivent "
            "correspondre à A2."
        )

    frr = authentication_metrics.frr

    if frr < 0 or frr > 1:

        raise ValueError(
            "La FRR doit appartenir à [0, 1]."
        )

    challenge_response_costs = (
        calculate_challenge_response_costs(
            parameters
        )
    )

    expected_energy_j = (
        frr
        * challenge_response_costs[
            "energy_j"
        ]
    )

    worst_case_energy_j = (
        challenge_response_costs[
            "energy_j"
        ]
    )

    expected_latency_s = (
        parameters.rff_processing_time_bob_s
        + frr
        * challenge_response_costs[
            "latency_s"
        ]
    )

    worst_case_latency_s = (
        parameters.rff_processing_time_bob_s
        + challenge_response_costs[
            "latency_s"
        ]
    )

    worst_case_airtime_s = (
        challenge_response_costs[
            "alice_tx_airtime_s"
        ]
    )

    return {
        "expected_energy_j":
            expected_energy_j,

        "worst_case_energy_j":
            worst_case_energy_j,

        "expected_latency_s":
            expected_latency_s,

        "worst_case_latency_s":
            worst_case_latency_s,

        "worst_case_airtime_s":
            worst_case_airtime_s
    }


# Cette fonction choisit automatiquement
# le modèle de coût de A1 ou de A2.
def calculate_authentication_costs(
    authentication_action,
    authentication_metrics,
    parameters
):

    if authentication_action == AuthenticationAction.A1:

        return calculate_a1_costs(
            parameters
        )

    if authentication_action == AuthenticationAction.A2:

        return calculate_a2_costs(
            authentication_metrics,
            parameters
        )

    raise ValueError(
        "L'action d'authentification "
        "doit être A1 ou A2."
    )


# ================================================================
# 5. COÛTS DE GESTION DE CLÉ
# ================================================================


# Cette fonction calcule le coût de K0.
#
# Dans la modélisation :
#
# E_sec(K0) = 0
# L_key(K0) = 0
#
# Cette fonction correspond à CO-EQ83.
def calculate_k0_costs():

    return {
        "energy_j": 0.0,
        "latency_s": 0.0,
        "airtime_s": 0.0
    }


# Cette fonction calcule le nombre réel de bits bruts
# (N_raw) produits par la collecte de mesures.
#
# Chaque mesure conservée après bande de garde produit
# un bit brut par quantification de signe. Le nombre de
# bits bruts dépend donc du nombre de mesures réellement
# utilisées pour cette clé, pas d'une constante fixe :
#
# N_raw = round(
#     measurements_used
#     * kept_measurement_ratio
# )
#
# measurements_used doit être le nombre de mesures
# effectivement nécessaires à cette clé
# (key_metrics.required_measurements), pas un nombre
# cible de bits indépendant du canal observé.
def calculate_raw_bit_count_from_measurements(
    measurements_used,
    kept_measurement_ratio
):

    if measurements_used is None:

        raise ValueError(
            "measurements_used doit être défini."
        )

    if measurements_used < 0:

        raise ValueError(
            "measurements_used ne peut pas être négatif."
        )

    if (
        kept_measurement_ratio <= 0
        or kept_measurement_ratio > 1
    ):

        raise ValueError(
            "kept_measurement_ratio doit appartenir "
            "à ]0, 1]."
        )

    raw_bit_count = round(
        measurements_used
        * kept_measurement_ratio
    )

    return raw_bit_count


# Cette fonction calcule le coût
# de la réconciliation et de l'amplification.
#
# Dans la modélisation :
#
# E_rec+PA =
#     E_cpu(N_raw * C_rec/bit)
#     + E_msg,rec
#     + E_cpu(C_PA)
#
# L_rec+PA =
#     N_raw * C_rec/bit / f_CPU
#     + L_msg,rec
#     + C_PA / f_CPU
#
# Cette fonction correspond à CO-EQ84 et CO-EQ85.
#
# raw_bit_count (N_raw) doit refléter le nombre réel
# de bits bruts produits par la collecte effectuée
# (mesures utilisées après bande de garde), et non une
# constante fixe indépendante du canal : voir
# calculate_raw_bit_count_from_measurements.
def calculate_reconciliation_pa_costs(
    parameters,
    raw_bit_count
):

    if raw_bit_count is None:

        raise ValueError(
            "raw_bit_count doit être défini."
        )

    if raw_bit_count < 0:

        raise ValueError(
            "raw_bit_count ne peut pas être négatif."
        )

    required_parameters = {
        "reconciliation_cycles_per_bit":
            parameters.reconciliation_cycles_per_bit,

        "privacy_amplification_cycles":
            parameters.privacy_amplification_cycles,

        "reconciliation_message_energy_j":
            parameters.reconciliation_message_energy_j,

        "reconciliation_message_latency_s":
            parameters.reconciliation_message_latency_s
    }

    for parameter_name in required_parameters:

        parameter_value = required_parameters[
            parameter_name
        ]

        if parameter_value is None:

            raise ValueError(
                parameter_name
                + " doit être défini."
            )

        if parameter_value < 0:

            raise ValueError(
                parameter_name
                + " ne peut pas être négatif."
            )

    reconciliation_cycle_count = (
        raw_bit_count
        * parameters.reconciliation_cycles_per_bit
    )

    reconciliation_cpu_energy_j = (
        calculate_cpu_energy(
            reconciliation_cycle_count,
            parameters
        )
    )

    privacy_amplification_energy_j = (
        calculate_cpu_energy(
            parameters.privacy_amplification_cycles,
            parameters
        )
    )

    reconciliation_cpu_latency_s = (
        calculate_cpu_time(
            reconciliation_cycle_count,
            parameters.cpu_frequency_hz
        )
    )

    privacy_amplification_latency_s = (
        calculate_cpu_time(
            parameters.privacy_amplification_cycles,
            parameters.cpu_frequency_hz
        )
    )

    reconciliation_pa_energy_j = (
        reconciliation_cpu_energy_j
        + parameters.reconciliation_message_energy_j
        + privacy_amplification_energy_j
    )

    reconciliation_pa_latency_s = (
        reconciliation_cpu_latency_s
        + parameters.reconciliation_message_latency_s
        + privacy_amplification_latency_s
    )

    return {
        "energy_j":
            reconciliation_pa_energy_j,

        "latency_s":
            reconciliation_pa_latency_s
    }


# Cette fonction calcule l'énergie d'un sondage dédié.
#
# Dans la modélisation :
#
# E_probe =
#     E_tx(M_probe)
#     + E_rx(M_probe)
#
# Cette fonction correspond à CO-EQ87.
def calculate_probe_energy(
    parameters
):

    probe_energy_j = (
        calculate_tx_energy(
            parameters.probe_payload_bytes,
            parameters
        )
        + calculate_rx_energy(
            parameters.probe_payload_bytes,
            parameters
        )
    )

    return probe_energy_j


# Cette fonction calcule les coûts de K1b,
# la génération par sondages dédiés.
#
# Dans la modélisation :
#
# E(K1b) =
#     N_meas * E_probe
#     + E_rec+PA
#
# L_key(K1b) =
#     N_meas * T_s
#     + L_rec+PA
#
# Cette fonction correspond à CO-EQ86 et CO-EQ88.
def calculate_k1b_costs(
    required_measurements,
    parameters
):

    if required_measurements is None:

        raise ValueError(
            "Le nombre de mesures doit être défini."
        )

    if required_measurements <= 0:

        raise ValueError(
            "Le nombre de mesures doit être "
            "strictement positif."
        )

    raw_bit_count = (
        calculate_raw_bit_count_from_measurements(
            measurements_used=required_measurements,
            kept_measurement_ratio=(
                parameters.kept_measurement_ratio
            )
        )
    )

    reconciliation_pa_costs = (
        calculate_reconciliation_pa_costs(
            parameters,
            raw_bit_count
        )
    )

    probe_energy_j = calculate_probe_energy(
        parameters
    )

    key_energy_j = (
        required_measurements
        * probe_energy_j
        + reconciliation_pa_costs[
            "energy_j"
        ]
    )

    key_latency_s = (
        required_measurements
        * parameters.dedicated_probe_interval_s
        + reconciliation_pa_costs[
            "latency_s"
        ]
    )

    # Pour la contrainte de duty-cycle d'Alice,
    # on compte uniquement ses émissions.
    key_airtime_s = (
        required_measurements
        * calculate_time_on_air(
            parameters.probe_payload_bytes,
            parameters
        )
    )

    return {
        "energy_j":
            key_energy_j,

        "latency_s":
            key_latency_s,

        "airtime_s":
            key_airtime_s
    }


# Cette fonction calcule les coûts de K1a,
# la collecte opportuniste.
#
# Dans la modélisation :
#
# E(K1a) = E_rec+PA
#
# L_key(K1a) =
#     N_meas * T_msg
#     + L_rec+PA
#
# Cette fonction correspond à CO-EQ89 et CO-EQ90.
#
# Le coût radio incrémental est nul seulement
# si les trames et ACK existent déjà dans E_base.
def calculate_k1a_costs(
    required_measurements,
    parameters
):

    if required_measurements is None:

        raise ValueError(
            "Le nombre de mesures doit être défini."
        )

    if required_measurements <= 0:

        raise ValueError(
            "Le nombre de mesures doit être "
            "strictement positif."
        )

    raw_bit_count = (
        calculate_raw_bit_count_from_measurements(
            measurements_used=required_measurements,
            kept_measurement_ratio=(
                parameters.kept_measurement_ratio
            )
        )
    )

    reconciliation_pa_costs = (
        calculate_reconciliation_pa_costs(
            parameters,
            raw_bit_count
        )
    )

    key_energy_j = (
        reconciliation_pa_costs[
            "energy_j"
        ]
    )

    key_latency_s = (
        required_measurements
        * parameters.message_period_s
        + reconciliation_pa_costs[
            "latency_s"
        ]
    )

    return {
        "energy_j":
            key_energy_j,

        "latency_s":
            key_latency_s,

        # Les trames sont supposées déjà incluses
        # dans l'énergie de base.
        "airtime_s": 0.0
    }


# Cette fonction calcule le coût RÉELLEMENT engagé
# par Alice PENDANT UNE SEULE PÉRIODE de préparation K1a.
#
# Contrairement à calculate_k1a_costs (qui calcule la
# latence PROJETÉE de la collecte entière restante, utile
# pour la contrainte d'échéance DM-EQ100), cette fonction
# calcule le coût incrémental réel d'une seule période,
# nécessaire pour ne jamais débiter par avance l'énergie
# de mesures qui n'ont pas encore eu lieu.
#
# K1a est opportuniste : une mesure exploitable est
# obtenue "gratuitement" à partir d'un échange déjà prévu.
# Le seul coût réel est celui de la réconciliation et de
# l'amplification de confidentialité, engagé une seule
# fois, lorsque la collecte se termine effectivement
# (remaining_measurements atteint 0).
def calculate_k1a_incremental_costs(
    remaining_measurements,
    parameters,
    required_measurements
):

    if remaining_measurements is None:

        raise ValueError(
            "remaining_measurements doit être défini."
        )

    if remaining_measurements < 0:

        raise ValueError(
            "remaining_measurements ne peut pas "
            "être négatif."
        )

    if remaining_measurements > 0:

        return {
            "energy_j": 0.0,
            "airtime_s": 0.0
        }

    # La réconciliation porte sur les bits bruts
    # réellement produits par la collecte terminée
    # (required_measurements), pas sur une constante
    # indépendante du canal.
    raw_bit_count = (
        calculate_raw_bit_count_from_measurements(
            measurements_used=required_measurements,
            kept_measurement_ratio=(
                parameters.kept_measurement_ratio
            )
        )
    )

    reconciliation_pa_costs = (
        calculate_reconciliation_pa_costs(
            parameters,
            raw_bit_count
        )
    )

    return {
        "energy_j": (
            reconciliation_pa_costs["energy_j"]
        ),
        "airtime_s": 0.0
    }


# Cette fonction calcule le coût RÉELLEMENT engagé
# par Alice PENDANT UNE SEULE PÉRIODE de préparation K1b.
#
# K1b utilise des sondages dédiés : contrairement à K1a,
# chaque sondage a un coût radio réel (énergie et
# airtime). Ce coût ne doit être débité qu'au moment où
# le sondage est réellement émis — un seul sondage par
# période, jamais le total cumulé des sondages restants.
#
# C'est cette fonction (et non calculate_k1b_costs, qui
# reste la projection totale utilisée pour l'échéance)
# qui doit alimenter la contrainte de duty-cycle DM-EQ101 :
# comparer un seul sondage au budget instantané est
# cohérent avec dedicated_probe_interval_s, dérivé de
# T_air(sondage) / duty_cycle_fraction (voir
# results/three_scenarios_explicit_analysis/
# k1a_k1b_model_consistency_audit.md, section 6).
def calculate_k1b_incremental_costs(
    remaining_measurements,
    parameters,
    required_measurements
):

    if remaining_measurements is None:

        raise ValueError(
            "remaining_measurements doit être défini."
        )

    if remaining_measurements < 0:

        raise ValueError(
            "remaining_measurements ne peut pas "
            "être négatif."
        )

    if remaining_measurements > 0:

        return {
            "energy_j": calculate_probe_energy(
                parameters
            ),
            "airtime_s": calculate_time_on_air(
                parameters.probe_payload_bytes,
                parameters
            )
        }

    # La réconciliation porte sur les bits bruts
    # réellement produits par la collecte terminée
    # (required_measurements), pas sur une constante
    # indépendante du canal.
    raw_bit_count = (
        calculate_raw_bit_count_from_measurements(
            measurements_used=required_measurements,
            kept_measurement_ratio=(
                parameters.kept_measurement_ratio
            )
        )
    )

    reconciliation_pa_costs = (
        calculate_reconciliation_pa_costs(
            parameters,
            raw_bit_count
        )
    )

    return {
        "energy_j": (
            reconciliation_pa_costs["energy_j"]
        ),
        "airtime_s": 0.0
    }


# Cette fonction calcule les coûts de K2
# à partir d'un protocole explicitement décrit.
#
# Dans la modélisation :
#
# E(K2) =
#     somme des énergies des opérations ECC
#     + somme des énergies TX
#     + somme des énergies RX
#
# Cette fonction correspond à CO-EQ91.
#
# Une signature ECC unique ne doit jamais être
# confondue automatiquement avec tout le protocole K2.
def calculate_k2_costs(
    ecc_operation_energies_j,
    ecc_operation_times_s,
    tx_message_sizes_bytes,
    rx_message_sizes_bytes,
    parameters
):

    required_lists = {
        "ecc_operation_energies_j":
            ecc_operation_energies_j,

        "ecc_operation_times_s":
            ecc_operation_times_s,

        "tx_message_sizes_bytes":
            tx_message_sizes_bytes,

        "rx_message_sizes_bytes":
            rx_message_sizes_bytes
    }

    for list_name in required_lists:

        list_value = required_lists[
            list_name
        ]

        if list_value is None:

            raise ValueError(
                list_name
                + " doit être défini."
            )

    # Les deux listes ECC doivent décrire
    # les mêmes opérations.
    if (
        len(ecc_operation_energies_j)
        != len(ecc_operation_times_s)
    ):

        raise ValueError(
            "Les listes d'énergie et de temps ECC "
            "doivent avoir la même longueur."
        )

    all_numeric_values = (
        list(ecc_operation_energies_j)
        + list(ecc_operation_times_s)
        + list(tx_message_sizes_bytes)
        + list(rx_message_sizes_bytes)
    )

    for numeric_value in all_numeric_values:

        if numeric_value < 0:

            raise ValueError(
                "Les coûts et tailles de K2 "
                "ne peuvent pas être négatifs."
            )

    ecc_energy_j = sum(
        ecc_operation_energies_j
    )

    ecc_latency_s = sum(
        ecc_operation_times_s
    )

    tx_energy_j = 0.0
    tx_latency_s = 0.0

    for payload_bytes in tx_message_sizes_bytes:

        tx_energy_j += calculate_tx_energy(
            payload_bytes,
            parameters
        )

        tx_latency_s += calculate_time_on_air(
            payload_bytes,
            parameters
        )

    rx_energy_j = 0.0
    rx_latency_s = 0.0

    for payload_bytes in rx_message_sizes_bytes:

        rx_energy_j += calculate_rx_energy(
            payload_bytes,
            parameters
        )

        rx_latency_s += calculate_time_on_air(
            payload_bytes,
            parameters
        )

    key_energy_j = (
        ecc_energy_j
        + tx_energy_j
        + rx_energy_j
    )

    key_latency_s = (
        ecc_latency_s
        + tx_latency_s
        + rx_latency_s
    )

    # Le duty-cycle d'Alice dépend seulement
    # de ses émissions.
    key_airtime_s = tx_latency_s

    return {
        "energy_j":
            key_energy_j,

        "latency_s":
            key_latency_s,

        "airtime_s":
            key_airtime_s
    }


# Cette fonction choisit automatiquement
# le modèle de coût de K0, K1a, K1b ou K2.
#
# Pour K1a et K1b, deux grandeurs distinctes
# sont combinées :
#
# - latency_s : la latence PROJETÉE pour terminer
#   la collecte restante (remaining_measurements),
#   utilisée par la contrainte d'échéance DM-EQ100 ;
#
# - energy_j / airtime_s : le coût RÉELLEMENT engagé
#   PENDANT CETTE SEULE PÉRIODE (calculate_k1a_incremental_costs
#   / calculate_k1b_incremental_costs), jamais le total
#   cumulé des mesures ou sondages restants. C'est cette
#   valeur qui alimente la contrainte de duty-cycle
#   DM-EQ101 et le débit réel de la batterie.
#
# key_metrics.remaining_measurements est absent (None)
# uniquement lorsque key_metrics a été construit sans
# collected_measurements (ancien appelant) : on utilise
# alors required_measurements, ce qui reproduit
# exactement l'ancien comportement.
def calculate_key_costs(
    key_action,
    key_metrics,
    parameters,
    k2_protocol=None
):

    if key_action == KeyAction.K0:

        return calculate_k0_costs()

    if key_action == KeyAction.K1A:

        remaining_measurements = (
            key_metrics.remaining_measurements
        )

        if remaining_measurements is None:

            remaining_measurements = (
                key_metrics.required_measurements
            )

        if remaining_measurements > 0:

            latency_s = calculate_k1a_costs(
                required_measurements=(
                    remaining_measurements
                ),
                parameters=parameters
            )["latency_s"]

        else:

            latency_s = (
                calculate_reconciliation_pa_costs(
                    parameters,
                    raw_bit_count=(
                        calculate_raw_bit_count_from_measurements(
                            measurements_used=(
                                key_metrics
                                .required_measurements
                            ),
                            kept_measurement_ratio=(
                                parameters
                                .kept_measurement_ratio
                            )
                        )
                    )
                )["latency_s"]
            )

        incremental_costs = (
            calculate_k1a_incremental_costs(
                remaining_measurements=(
                    remaining_measurements
                ),
                parameters=parameters,
                required_measurements=(
                    key_metrics.required_measurements
                )
            )
        )

        return {
            "energy_j": (
                incremental_costs["energy_j"]
            ),
            "latency_s": latency_s,
            "airtime_s": (
                incremental_costs["airtime_s"]
            )
        }

    if key_action == KeyAction.K1B:

        remaining_measurements = (
            key_metrics.remaining_measurements
        )

        if remaining_measurements is None:

            remaining_measurements = (
                key_metrics.required_measurements
            )

        if remaining_measurements > 0:

            latency_s = calculate_k1b_costs(
                required_measurements=(
                    remaining_measurements
                ),
                parameters=parameters
            )["latency_s"]

        else:

            latency_s = (
                calculate_reconciliation_pa_costs(
                    parameters,
                    raw_bit_count=(
                        calculate_raw_bit_count_from_measurements(
                            measurements_used=(
                                key_metrics
                                .required_measurements
                            ),
                            kept_measurement_ratio=(
                                parameters
                                .kept_measurement_ratio
                            )
                        )
                    )
                )["latency_s"]
            )

        incremental_costs = (
            calculate_k1b_incremental_costs(
                remaining_measurements=(
                    remaining_measurements
                ),
                parameters=parameters,
                required_measurements=(
                    key_metrics.required_measurements
                )
            )
        )

        return {
            "energy_j": (
                incremental_costs["energy_j"]
            ),
            "latency_s": latency_s,
            "airtime_s": (
                incremental_costs["airtime_s"]
            )
        }

    if key_action == KeyAction.K2:

        if k2_protocol is None:

            raise ValueError(
                "Le protocole complet K2 doit être fourni."
            )

        return calculate_k2_costs(
            ecc_operation_energies_j=(
                k2_protocol[
                    "ecc_operation_energies_j"
                ]
            ),
            ecc_operation_times_s=(
                k2_protocol[
                    "ecc_operation_times_s"
                ]
            ),
            tx_message_sizes_bytes=(
                k2_protocol[
                    "tx_message_sizes_bytes"
                ]
            ),
            rx_message_sizes_bytes=(
                k2_protocol[
                    "rx_message_sizes_bytes"
                ]
            ),
            parameters=parameters
        )

    raise ValueError(
        "L'action de clé doit être "
        "K0, K1a, K1b ou K2."
    )


# ================================================================
# 6. LATENCE NORMALISÉE ET COÛT COMPLET
# ================================================================


# Cette fonction calcule l'objectif
# de latence normalisée.
#
# Dans la modélisation :
#
# L_t(D) = max(
#     L_auth(D) / L_max(criticité),
#     L_key(D) / T_deadline
# )
#
# Cette fonction correspond à CO-EQ92.
def calculate_normalized_latency(
    authentication_latency_s,
    authentication_latency_limit_s,
    key_latency_s,
    key_deadline_s
):

    if authentication_latency_s < 0:

        raise ValueError(
            "La latence d'authentification "
            "ne peut pas être négative."
        )

    if authentication_latency_limit_s <= 0:

        raise ValueError(
            "La limite d'authentification doit être "
            "strictement positive."
        )

    if key_latency_s < 0:

        raise ValueError(
            "La latence de clé ne peut pas être négative."
        )

    if key_deadline_s <= 0:

        raise ValueError(
            "L'échéance de clé doit être "
            "strictement positive."
        )

    authentication_ratio = (
        authentication_latency_s
        / authentication_latency_limit_s
    )

    key_ratio = (
        key_latency_s
        / key_deadline_s
    )

    normalized_latency = max(
        authentication_ratio,
        key_ratio
    )

    return normalized_latency


# Cette fonction construit toutes les métriques
# d'énergie et de latence d'une décision.
#
# Elle rassemble :
# - l'énergie de base ;
# - les coûts d'authentification ;
# - les coûts de clé ;
# - l'objectif de latence normalisée ;
# - le pire cas utilisé pour l'admissibilité.
def build_cost_metrics(
    decision,
    authentication_metrics,
    key_metrics,
    context,
    parameters,
    k2_protocol=None
):

    # Les métriques doivent correspondre
    # aux actions contenues dans la décision.
    if (
        authentication_metrics.authentication_action
        != decision.authentication_action
    ):

        raise ValueError(
            "Les métriques d'authentification "
            "ne correspondent pas à la décision."
        )

    if (
        key_metrics.key_action
        != decision.key_action
    ):

        raise ValueError(
            "Les métriques de clé "
            "ne correspondent pas à la décision."
        )

    base_energy_j = calculate_base_energy(
        parameters
    )

    authentication_costs = (
        calculate_authentication_costs(
            authentication_action=(
                decision.authentication_action
            ),
            authentication_metrics=(
                authentication_metrics
            ),
            parameters=parameters
        )
    )

    key_costs = calculate_key_costs(
        key_action=decision.key_action,
        key_metrics=key_metrics,
        parameters=parameters,
        k2_protocol=k2_protocol
    )

    authentication_security_energy_j = (
        authentication_costs[
            "expected_energy_j"
        ]
    )

    key_security_energy_j = (
        key_costs[
            "energy_j"
        ]
    )

    security_energy_j = (
        authentication_security_energy_j
        + key_security_energy_j
    )

    total_energy_j = calculate_total_energy(
        base_energy_j,
        security_energy_j
    )

    worst_case_energy_j = (
        base_energy_j
        + authentication_costs[
            "worst_case_energy_j"
        ]
        + key_security_energy_j
    )

    authentication_latency_limit_s = (
        parameters.get_authentication_latency_limit(
            context.criticality
        )
    )

    normalized_latency = (
        calculate_normalized_latency(
            authentication_latency_s=(
                authentication_costs[
                    "expected_latency_s"
                ]
            ),
            authentication_latency_limit_s=(
                authentication_latency_limit_s
            ),
            key_latency_s=(
                key_costs[
                    "latency_s"
                ]
            ),
            key_deadline_s=(
                context.key_deadline_s
            )
        )
    )

    # Le temps d'antenne est conservatif :
    # - pire cas d'authentification ;
    # - émissions supplémentaires de la gestion de clé.
    airtime_s = (
        authentication_costs[
            "worst_case_airtime_s"
        ]
        + key_costs[
            "airtime_s"
        ]
    )

    cost_metrics = CostMetrics(
        base_energy_j=base_energy_j,
        authentication_security_energy_j=(
            authentication_security_energy_j
        ),
        key_security_energy_j=(
            key_security_energy_j
        ),
        security_energy_j=(
            security_energy_j
        ),
        total_energy_j=(
            total_energy_j
        ),
        authentication_latency_s=(
            authentication_costs[
                "expected_latency_s"
            ]
        ),
        prudent_authentication_latency_s=(
            authentication_costs[
                "worst_case_latency_s"
            ]
        ),
        key_latency_s=(
            key_costs[
                "latency_s"
            ]
        ),
        normalized_latency=(
            normalized_latency
        ),
        airtime_s=airtime_s,
        expected_energy_j=(
            total_energy_j
        ),
        worst_case_energy_j=(
            worst_case_energy_j
        )
    )

    return cost_metrics
