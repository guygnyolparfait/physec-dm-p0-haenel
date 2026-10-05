# unittest est l'outil de test fourni avec Python.
import unittest


# On importe les structures nécessaires
# pour construire des décisions et des métriques.
from physec_dm.models import (
    AuthenticationAction,
    AuthenticationMetrics,
    Context,
    Decision,
    KeyAction,
    KeyMetrics
)


# On importe la configuration centrale.
from physec_dm.parameters import Parameters


# On importe toutes les fonctions
# du module energy_latency.py.
from physec_dm.energy_latency import (
    build_cost_metrics,
    calculate_a1_costs,
    calculate_a2_costs,
    calculate_base_energy,
    calculate_challenge_response_costs,
    calculate_cpu_energy,
    calculate_cpu_time,
    calculate_k0_costs,
    calculate_k1a_costs,
    calculate_k1b_costs,
    calculate_k2_costs,
    calculate_mac_costs,
    calculate_normalized_latency,
    calculate_payload_intermediate,
    calculate_payload_symbol_count,
    calculate_preamble_time,
    calculate_probe_energy,
    calculate_raw_bit_count_from_measurements,
    calculate_reconciliation_pa_costs,
    calculate_rx_energy,
    calculate_symbol_time,
    calculate_time_on_air,
    calculate_total_energy,
    calculate_tx_energy
)

from physec_dm.key_generation import (
    calculate_binary_entropy,
    calculate_reconciliation_yield,
    calculate_required_measurements
)


# Cette fonction prépare des paramètres numériques
# pour les tests du module énergie-latence.
#
# Les valeurs encore à None dans parameters.py
# sont renseignées uniquement dans l'objet de test.
#
# Le fichier parameters.py n'est pas modifié.
def create_test_parameters():

    parameters = Parameters()

    # Coût CPU AES-CMAC.
    parameters.mac_cycles = 32000

    # Latence protocolaire complète du défi-réponse.
    parameters.challenge_response_latency_s = 4.0

    # Composantes de l'énergie de base.
    parameters.sensing_energy_j = 0.001
    parameters.application_energy_j = 0.002
    parameters.receive_windows_energy_j = 0.003
    parameters.sleep_energy_j = 0.004

    # Paramètres de réconciliation et d'amplification.
    parameters.raw_bit_count = 128
    parameters.reconciliation_cycles_per_bit = 100
    parameters.privacy_amplification_cycles = 6400
    parameters.reconciliation_message_energy_j = 0.005
    parameters.reconciliation_message_latency_s = 0.50

    return parameters


# Cette fonction crée des métriques A1 simples.
def create_a1_metrics():

    return AuthenticationMetrics(
        authentication_action=(
            AuthenticationAction.A1
        ),
        far=2 ** (-64),
        frr=0.0,
        mac_forgery_probability=2 ** (-64),
        total_false_acceptance_probability=2 ** (-64),
        authentication_robustness=1 - 2 ** (-64),
        alice_fallback_probability=0.0,
        mallory_fallback_probability=0.0
    )


# Cette fonction crée des métriques A2
# avec une FRR de 5 %.
def create_a2_metrics():

    return AuthenticationMetrics(
        authentication_action=(
            AuthenticationAction.A2
        ),
        far=0.02,
        frr=0.05,
        mac_forgery_probability=2 ** (-64),
        total_false_acceptance_probability=0.02,
        authentication_robustness=0.98,
        alice_fallback_probability=0.05,
        mallory_fallback_probability=0.98
    )


# Cette fonction crée des métriques de clé
# pour l'action demandée.
def create_key_metrics(
    key_action,
    required_measurements=10,
    remaining_measurements=None
):

    return KeyMetrics(
        key_action=key_action,
        raw_kdr=0.20,
        effective_kdr=0.20,
        binary_entropy=0.7219,
        reconciliation_yield=0.19467,
        required_measurements=required_measurements,
        agreement_feasible=True,
        variation_feasible=True,
        phy_feasible=True,
        key_aging_index=0.50,
        renewal_required=True,
        key_expired=False,
        key_deadline_s=10000.0,
        key_quality=0.2781,
        remaining_measurements=remaining_measurements
    )


# Cette classe teste le Time-on-Air LoRa.
class TestLoRaTimeOnAir(unittest.TestCase):

    # SF12 et BW125 kHz donnent
    # T_sym = 0.032768 s.
    def test_symbol_time(self):

        symbol_time_s = calculate_symbol_time(
            spreading_factor=12,
            bandwidth_hz=125000.0
        )

        self.assertAlmostEqual(
            symbol_time_s,
            0.032768,
            places=12
        )

    # Avec 8 symboles programmés :
    #
    # T_pre = (8 + 4.25) * 0.032768
    #       = 0.401408 s.
    def test_preamble_time(self):

        preamble_time_s = (
            calculate_preamble_time(
                preamble_symbols=8,
                symbol_time_s=0.032768
            )
        )

        self.assertAlmostEqual(
            preamble_time_s,
            0.401408,
            places=12
        )

    # Pour 32 octets, SF12, CRC actif,
    # en-tête explicite et DE actif :
    #
    # Xi = ceil(252 / 40) = 7.
    def test_payload_intermediate(self):

        payload_intermediate = (
            calculate_payload_intermediate(
                payload_bytes=32,
                spreading_factor=12,
                crc_enabled=True,
                implicit_header=False,
                low_data_rate_optimization=True
            )
        )

        self.assertEqual(
            payload_intermediate,
            7
        )

    # Avec CR_idx = 1 :
    #
    # N_pl = 8 + 5 * 7 = 43.
    def test_payload_symbol_count(self):

        payload_symbol_count = (
            calculate_payload_symbol_count(
                payload_bytes=32,
                spreading_factor=12,
                coding_rate_index=1,
                crc_enabled=True,
                implicit_header=False,
                low_data_rate_optimization=True
            )
        )

        self.assertEqual(
            payload_symbol_count,
            43
        )

    # Le Time-on-Air nominal de 32 octets
    # doit être égal à 1.810432 s.
    def test_nominal_time_on_air(self):

        parameters = create_test_parameters()

        time_on_air_s = calculate_time_on_air(
            payload_bytes=32,
            parameters=parameters
        )

        self.assertAlmostEqual(
            time_on_air_s,
            1.810432,
            places=12
        )

    # Une charge utile négative doit être refusée.
    def test_negative_payload_is_rejected(self):

        with self.assertRaises(ValueError):

            calculate_payload_intermediate(
                payload_bytes=-1,
                spreading_factor=12,
                crc_enabled=True,
                implicit_header=False,
                low_data_rate_optimization=True
            )

    # Un mauvais coding rate doit être refusé.
    def test_invalid_coding_rate_is_rejected(self):

        with self.assertRaises(ValueError):

            calculate_payload_symbol_count(
                payload_bytes=32,
                spreading_factor=12,
                coding_rate_index=7,
                crc_enabled=True,
                implicit_header=False,
                low_data_rate_optimization=True
            )


# Cette classe teste les énergies radio et CPU.
class TestElectricalEnergy(unittest.TestCase):

    # Ce test vérifie E_tx = V * I_tx * T_air.
    def test_tx_energy(self):

        parameters = create_test_parameters()

        expected_energy_j = (
            parameters.supply_voltage_v
            * parameters.tx_current_a
            * 1.810432
        )

        tx_energy_j = calculate_tx_energy(
            payload_bytes=32,
            parameters=parameters
        )

        self.assertAlmostEqual(
            tx_energy_j,
            expected_energy_j,
            places=12
        )

    # Ce test vérifie E_rx = V * I_rx * T_air.
    def test_rx_energy(self):

        parameters = create_test_parameters()

        expected_energy_j = (
            parameters.supply_voltage_v
            * parameters.rx_current_a
            * 1.810432
        )

        rx_energy_j = calculate_rx_energy(
            payload_bytes=32,
            parameters=parameters
        )

        self.assertAlmostEqual(
            rx_energy_j,
            expected_energy_j,
            places=12
        )

    # 32000 cycles à 32 MHz
    # correspondent à 0.001 s.
    def test_cpu_time(self):

        cpu_time_s = calculate_cpu_time(
            cycle_count=32000,
            cpu_frequency_hz=32000000.0
        )

        self.assertEqual(
            cpu_time_s,
            0.001
        )

    # Ce test vérifie l'énergie CPU.
    def test_cpu_energy(self):

        parameters = create_test_parameters()

        cpu_energy_j = calculate_cpu_energy(
            cycle_count=32000,
            parameters=parameters
        )

        expected_energy_j = (
            parameters.supply_voltage_v
            * parameters.cpu_current_a
            * 0.001
        )

        self.assertAlmostEqual(
            cpu_energy_j,
            expected_energy_j,
            places=15
        )

    # Le calcul du MAC utilise les mêmes
    # formules CPU.
    def test_mac_costs(self):

        parameters = create_test_parameters()

        mac_energy_j, mac_latency_s = (
            calculate_mac_costs(
                parameters
            )
        )

        self.assertEqual(
            mac_latency_s,
            0.001
        )

        self.assertAlmostEqual(
            mac_energy_j,
            (
                parameters.supply_voltage_v
                * parameters.cpu_current_a
                * 0.001
            ),
            places=15
        )

    # Des cycles non définis doivent être refusés.
    def test_missing_mac_cycles_are_rejected(self):

        parameters = create_test_parameters()
        parameters.mac_cycles = None

        with self.assertRaises(ValueError):

            calculate_mac_costs(
                parameters
            )


# Cette classe teste l'énergie de base.
class TestBaseEnergy(unittest.TestCase):

    # L'énergie de base doit contenir
    # les quatre composantes et la transmission.
    def test_base_energy(self):

        parameters = create_test_parameters()

        base_energy_j = calculate_base_energy(
            parameters
        )

        expected_energy_j = (
            0.001
            + 0.002
            + calculate_tx_energy(
                32,
                parameters
            )
            + 0.003
            + 0.004
        )

        self.assertAlmostEqual(
            base_energy_j,
            expected_energy_j,
            places=12
        )

    # Une composante absente doit empêcher
    # le calcul de l'autonomie absolue.
    def test_missing_base_component_is_rejected(self):

        parameters = create_test_parameters()
        parameters.sensing_energy_j = None

        with self.assertRaises(ValueError):

            calculate_base_energy(
                parameters
            )

    # Ce test vérifie E_total = E_base + E_sec.
    def test_total_energy(self):

        self.assertEqual(
            calculate_total_energy(
                base_energy_j=2.0,
                security_energy_j=0.5
            ),
            2.5
        )


# Cette classe teste les coûts d'authentification.
class TestAuthenticationCosts(unittest.TestCase):

    # A1 doit avoir un coût positif
    # et un coût déterministe.
    def test_a1_costs(self):

        parameters = create_test_parameters()

        costs = calculate_a1_costs(
            parameters
        )

        self.assertGreater(
            costs["expected_energy_j"],
            0.0
        )

        self.assertEqual(
            costs["expected_energy_j"],
            costs["worst_case_energy_j"]
        )

        self.assertEqual(
            costs["expected_latency_s"],
            costs["worst_case_latency_s"]
        )

    # L'énergie du défi-réponse doit contenir :
    # RX défi + MAC + TX réponse.
    def test_challenge_response_energy(self):

        parameters = create_test_parameters()

        costs = (
            calculate_challenge_response_costs(
                parameters
            )
        )

        mac_energy_j, mac_latency_s = (
            calculate_mac_costs(
                parameters
            )
        )

        expected_energy_j = (
            calculate_rx_energy(
                parameters.challenge_bytes,
                parameters
            )
            + mac_energy_j
            + calculate_tx_energy(
                parameters.response_bytes,
                parameters
            )
        )

        self.assertAlmostEqual(
            costs["energy_j"],
            expected_energy_j,
            places=12
        )

        self.assertEqual(
            costs["latency_s"],
            4.0
        )

    # Le coût attendu de A2 doit être
    # FRR fois le coût du défi-réponse.
    def test_a2_expected_energy(self):

        parameters = create_test_parameters()
        metrics = create_a2_metrics()

        challenge_costs = (
            calculate_challenge_response_costs(
                parameters
            )
        )

        costs = calculate_a2_costs(
            authentication_metrics=metrics,
            parameters=parameters
        )

        self.assertAlmostEqual(
            costs["expected_energy_j"],
            0.05
            * challenge_costs["energy_j"],
            places=12
        )

        self.assertEqual(
            costs["worst_case_energy_j"],
            challenge_costs["energy_j"]
        )

    # La latence attendue de A2 doit suivre :
    #
    # T_RFF + FRR * L_CR.
    def test_a2_expected_latency(self):

        parameters = create_test_parameters()
        metrics = create_a2_metrics()

        costs = calculate_a2_costs(
            metrics,
            parameters
        )

        expected_latency_s = (
            parameters.rff_processing_time_bob_s
            + 0.05
            * parameters.challenge_response_latency_s
        )

        self.assertAlmostEqual(
            costs["expected_latency_s"],
            expected_latency_s,
            places=12
        )

        self.assertAlmostEqual(
            costs["worst_case_latency_s"],
            (
                parameters.rff_processing_time_bob_s
                + parameters.challenge_response_latency_s
            ),
            places=12
        )

    # Une latence L_CR absente doit être refusée.
    def test_missing_challenge_latency_is_rejected(self):

        parameters = create_test_parameters()
        parameters.challenge_response_latency_s = None

        with self.assertRaises(ValueError):

            calculate_challenge_response_costs(
                parameters
            )


# Cette classe teste les coûts de gestion de clé.
class TestKeyCosts(unittest.TestCase):

    # K0 doit avoir un coût nul.
    def test_k0_costs(self):

        costs = calculate_k0_costs()

        self.assertEqual(
            costs["energy_j"],
            0.0
        )

        self.assertEqual(
            costs["latency_s"],
            0.0
        )

        self.assertEqual(
            costs["airtime_s"],
            0.0
        )

    # Ce test vérifie les équations
    # de réconciliation et d'amplification.
    def test_reconciliation_pa_costs(self):

        parameters = create_test_parameters()

        costs = calculate_reconciliation_pa_costs(
            parameters,
            raw_bit_count=128
        )

        reconciliation_cycles = (
            128 * 100
        )

        expected_energy_j = (
            calculate_cpu_energy(
                reconciliation_cycles,
                parameters
            )
            + 0.005
            + calculate_cpu_energy(
                6400,
                parameters
            )
        )

        expected_latency_s = (
            calculate_cpu_time(
                reconciliation_cycles,
                parameters.cpu_frequency_hz
            )
            + 0.50
            + calculate_cpu_time(
                6400,
                parameters.cpu_frequency_hz
            )
        )

        self.assertAlmostEqual(
            costs["energy_j"],
            expected_energy_j,
            places=12
        )

        self.assertAlmostEqual(
            costs["latency_s"],
            expected_latency_s,
            places=12
        )

    # L'énergie d'un sondage doit être
    # E_tx + E_rx.
    def test_probe_energy(self):

        parameters = create_test_parameters()

        expected_energy_j = (
            calculate_tx_energy(
                parameters.probe_payload_bytes,
                parameters
            )
            + calculate_rx_energy(
                parameters.probe_payload_bytes,
                parameters
            )
        )

        self.assertAlmostEqual(
            calculate_probe_energy(parameters),
            expected_energy_j,
            places=12
        )

    # K1b doit inclure les sondages dédiés.
    def test_k1b_costs(self):

        parameters = create_test_parameters()

        costs = calculate_k1b_costs(
            required_measurements=10,
            parameters=parameters
        )

        # required_measurements=10 produit
        # round(10 * kept_measurement_ratio) bits bruts,
        # soit round(10 * 0.70) = 7.
        reconciliation_costs = (
            calculate_reconciliation_pa_costs(
                parameters,
                raw_bit_count=7
            )
        )

        expected_energy_j = (
            10
            * calculate_probe_energy(
                parameters
            )
            + reconciliation_costs["energy_j"]
        )

        expected_latency_s = (
            10
            * parameters.dedicated_probe_interval_s
            + reconciliation_costs["latency_s"]
        )

        self.assertAlmostEqual(
            costs["energy_j"],
            expected_energy_j,
            places=12
        )

        self.assertAlmostEqual(
            costs["latency_s"],
            expected_latency_s,
            places=12
        )

        self.assertGreater(
            costs["airtime_s"],
            0.0
        )

    # K1a ne doit ajouter aucune énergie
    # de sondage ou airtime incrémental.
    def test_k1a_costs(self):

        parameters = create_test_parameters()

        costs = calculate_k1a_costs(
            required_measurements=10,
            parameters=parameters
        )

        # required_measurements=10 produit
        # round(10 * kept_measurement_ratio) bits bruts,
        # soit round(10 * 0.70) = 7.
        reconciliation_costs = (
            calculate_reconciliation_pa_costs(
                parameters,
                raw_bit_count=7
            )
        )

        self.assertAlmostEqual(
            costs["energy_j"],
            reconciliation_costs["energy_j"],
            places=12
        )

        self.assertAlmostEqual(
            costs["latency_s"],
            (
                10
                * parameters.message_period_s
                + reconciliation_costs[
                    "latency_s"
                ]
            ),
            places=12
        )

        self.assertEqual(
            costs["airtime_s"],
            0.0
        )

    # Le protocole K2 doit additionner
    # les opérations ECC et les échanges radio.
    def test_k2_costs(self):

        parameters = create_test_parameters()

        costs = calculate_k2_costs(
            ecc_operation_energies_j=[
                0.019,
                0.010
            ],
            ecc_operation_times_s=[
                0.218,
                0.100
            ],
            tx_message_sizes_bytes=[
                16
            ],
            rx_message_sizes_bytes=[
                8
            ],
            parameters=parameters
        )

        expected_energy_j = (
            0.019
            + 0.010
            + calculate_tx_energy(
                16,
                parameters
            )
            + calculate_rx_energy(
                8,
                parameters
            )
        )

        expected_latency_s = (
            0.218
            + 0.100
            + calculate_time_on_air(
                16,
                parameters
            )
            + calculate_time_on_air(
                8,
                parameters
            )
        )

        self.assertAlmostEqual(
            costs["energy_j"],
            expected_energy_j,
            places=12
        )

        self.assertAlmostEqual(
            costs["latency_s"],
            expected_latency_s,
            places=12
        )

        self.assertAlmostEqual(
            costs["airtime_s"],
            calculate_time_on_air(
                16,
                parameters
            ),
            places=12
        )

    # Les deux listes ECC doivent avoir
    # la même longueur.
    def test_invalid_k2_protocol_is_rejected(self):

        parameters = create_test_parameters()

        with self.assertRaises(ValueError):

            calculate_k2_costs(
                ecc_operation_energies_j=[
                    0.019
                ],
                ecc_operation_times_s=[
                    0.218,
                    0.100
                ],
                tx_message_sizes_bytes=[],
                rx_message_sizes_bytes=[],
                parameters=parameters
            )


# Cette classe confirme explicitement que raw_bit_count
# représente les bits RÉELLEMENT conservés après
# quantification/bande de garde, et non le nombre brut de
# mesures prises.
#
# Dérivation vérifiée : required_measurements est défini
# (key_generation.calculate_required_measurements) comme
#
# N_meas = ceil(ell_K / (kept_ratio * (1 - h2(KDR))))
#
# donc :
#
# raw_bit_count
#     = round(N_meas * kept_ratio)
#     ~ ell_K / (1 - h2(KDR))
#
# c'est-à-dire le nombre de bits qui SURVIVENT la bande de
# garde, AVANT réconciliation — exactement ce que N_raw doit
# représenter dans l'équation de coût de réconciliation
# (E_rec+PA = E_cpu(N_raw * C_rec/bit) + ...), et non
# simplement N_meas (le nombre de mesures brutes prises).
class TestRawBitCountRepresentsPostGuardBandBits(
    unittest.TestCase
):

    def test_raw_bit_count_is_not_the_raw_measurement_count(
        self
    ):

        measurements_used = 100
        kept_measurement_ratio = 0.70

        raw_bit_count = (
            calculate_raw_bit_count_from_measurements(
                measurements_used=measurements_used,
                kept_measurement_ratio=(
                    kept_measurement_ratio
                )
            )
        )

        # Le nombre de bits après bande de garde doit être
        # strictement inférieur au nombre de mesures brutes
        # prises (kept_measurement_ratio < 1), jamais égal.
        self.assertLess(
            raw_bit_count,
            measurements_used
        )

        self.assertEqual(
            raw_bit_count,
            round(
                measurements_used
                * kept_measurement_ratio
            )
        )

    # Vérifie la dérivation complète bout-en-bout : à partir
    # d'un KDR effectif connu, le raw_bit_count calculé pour
    # les mesures requises doit approximer ell_K / (1 - h2(KDR)),
    # la définition analytique des bits post-bande-de-garde
    # entrant dans la réconciliation.
    def test_raw_bit_count_matches_analytical_derivation(
        self
    ):

        key_length_bits = 128
        kept_measurement_ratio = 0.70
        effective_kdr = 0.10

        binary_entropy = calculate_binary_entropy(
            effective_kdr
        )

        reconciliation_yield = (
            calculate_reconciliation_yield(
                effective_kdr=effective_kdr,
                kept_measurement_ratio=(
                    kept_measurement_ratio
                )
            )
        )

        required_measurements = (
            calculate_required_measurements(
                key_length_bits=key_length_bits,
                reconciliation_yield=(
                    reconciliation_yield
                ),
                numerical_epsilon=1e-12
            )
        )

        raw_bit_count = (
            calculate_raw_bit_count_from_measurements(
                measurements_used=(
                    required_measurements
                ),
                kept_measurement_ratio=(
                    kept_measurement_ratio
                )
            )
        )

        expected_raw_bit_count = (
            key_length_bits
            / (1 - binary_entropy)
        )

        # round() introduit un écart d'au plus 1 bit ;
        # l'arrondi de ceil() dans required_measurements
        # introduit un écart supplémentaire d'au plus
        # kept_measurement_ratio bit. La tolérance couvre
        # les deux arrondis successifs.
        self.assertAlmostEqual(
            raw_bit_count,
            expected_raw_bit_count,
            delta=2.0
        )

    def test_zero_kept_ratio_is_rejected(self):

        with self.assertRaises(ValueError):

            calculate_raw_bit_count_from_measurements(
                measurements_used=100,
                kept_measurement_ratio=0.0
            )

    def test_negative_measurements_is_rejected(self):

        with self.assertRaises(ValueError):

            calculate_raw_bit_count_from_measurements(
                measurements_used=-1,
                kept_measurement_ratio=0.70
            )


# Cette classe teste la latence normalisée.
class TestNormalizedLatency(unittest.TestCase):

    # Le plus grand des deux rapports doit être retenu.
    def test_normalized_latency(self):

        normalized_latency = (
            calculate_normalized_latency(
                authentication_latency_s=2.0,
                authentication_latency_limit_s=5.0,
                key_latency_s=50.0,
                key_deadline_s=100.0
            )
        )

        # max(0.4, 0.5) = 0.5.
        self.assertEqual(
            normalized_latency,
            0.5
        )

    # Une échéance nulle doit être refusée.
    def test_zero_deadline_is_rejected(self):

        with self.assertRaises(ValueError):

            calculate_normalized_latency(
                authentication_latency_s=2.0,
                authentication_latency_limit_s=5.0,
                key_latency_s=50.0,
                key_deadline_s=0.0
            )


# Cette classe teste la construction complète
# d'un objet CostMetrics.
class TestCompleteCostMetrics(unittest.TestCase):

    # Ce test construit la décision A1-K0.
    def test_build_a1_k0_cost_metrics(self):

        parameters = create_test_parameters()

        decision = Decision(
            AuthenticationAction.A1,
            KeyAction.K0
        )

        authentication_metrics = (
            create_a1_metrics()
        )

        key_metrics = create_key_metrics(
            KeyAction.K0,
            required_measurements=None
        )

        context = Context(
            snr_db=5.0,
            doppler_hz=0.0,
            battery_energy_j=28000.0,
            criticality=0,
            key_age_s=100.0,
            messages_with_current_key=2,
            rff_profile_available=True,
            renewal_required=False,
            key_expired=False,
            compromise_suspected=False,
            key_deadline_s=10000.0,
            remaining_duty_cycle_airtime_s=100.0
        )

        cost_metrics = build_cost_metrics(
            decision=decision,
            authentication_metrics=(
                authentication_metrics
            ),
            key_metrics=key_metrics,
            context=context,
            parameters=parameters
        )

        self.assertGreater(
            cost_metrics.base_energy_j,
            0.0
        )

        self.assertGreater(
            cost_metrics.total_energy_j,
            cost_metrics.base_energy_j
        )

        self.assertEqual(
            cost_metrics.key_security_energy_j,
            0.0
        )

        self.assertEqual(
            cost_metrics.key_latency_s,
            0.0
        )

        self.assertEqual(
            cost_metrics.expected_energy_j,
            cost_metrics.total_energy_j
        )

    # Ce test construit la décision A2-K1a pendant que
    # la collecte est ENCORE EN COURS
    # (remaining_measurements > 0) : le coût réellement
    # débité à Alice pendant cette seule période doit
    # rester nul (mesure opportuniste gratuite), alors que
    # la latence projetée reflète le reliquat complet.
    def test_build_a2_k1a_cost_metrics_mid_collection(self):

        parameters = create_test_parameters()

        decision = Decision(
            AuthenticationAction.A2,
            KeyAction.K1A
        )

        authentication_metrics = (
            create_a2_metrics()
        )

        key_metrics = create_key_metrics(
            KeyAction.K1A,
            required_measurements=10,
            remaining_measurements=10
        )

        context = Context(
            snr_db=5.0,
            doppler_hz=0.0,
            battery_energy_j=28000.0,
            criticality=1,
            key_age_s=50000.0,
            messages_with_current_key=700,
            rff_profile_available=True,
            renewal_required=True,
            key_expired=False,
            compromise_suspected=False,
            key_deadline_s=1000.0,
            remaining_duty_cycle_airtime_s=100.0
        )

        cost_metrics = build_cost_metrics(
            decision=decision,
            authentication_metrics=(
                authentication_metrics
            ),
            key_metrics=key_metrics,
            context=context,
            parameters=parameters
        )

        self.assertGreater(
            cost_metrics.authentication_security_energy_j,
            0.0
        )

        # Pendant la collecte, K1a est opportuniste :
        # aucune énergie de sécurité de clé n'est
        # débitée avant la fin de la réconciliation.
        self.assertEqual(
            cost_metrics.key_security_energy_j,
            0.0
        )

        self.assertGreater(
            cost_metrics.key_latency_s,
            0.0
        )

        self.assertGreaterEqual(
            cost_metrics.worst_case_energy_j,
            cost_metrics.expected_energy_j
        )

        self.assertGreaterEqual(
            cost_metrics.prudent_authentication_latency_s,
            cost_metrics.authentication_latency_s
        )

    # Ce test construit la décision A2-K1a lorsque la
    # collecte vient de se terminer (remaining_measurements
    # = 0) : l'énergie de réconciliation et d'amplification
    # de confidentialité est alors débitée, et la latence
    # projetée se réduit à cette seule étape finale.
    def test_build_a2_k1a_cost_metrics_collection_complete(self):

        parameters = create_test_parameters()

        decision = Decision(
            AuthenticationAction.A2,
            KeyAction.K1A
        )

        authentication_metrics = (
            create_a2_metrics()
        )

        key_metrics = create_key_metrics(
            KeyAction.K1A,
            required_measurements=10,
            remaining_measurements=0
        )

        context = Context(
            snr_db=5.0,
            doppler_hz=0.0,
            battery_energy_j=28000.0,
            criticality=1,
            key_age_s=50000.0,
            messages_with_current_key=700,
            rff_profile_available=True,
            renewal_required=True,
            key_expired=False,
            compromise_suspected=False,
            key_deadline_s=1000.0,
            remaining_duty_cycle_airtime_s=100.0
        )

        cost_metrics = build_cost_metrics(
            decision=decision,
            authentication_metrics=(
                authentication_metrics
            ),
            key_metrics=key_metrics,
            context=context,
            parameters=parameters
        )

        self.assertGreater(
            cost_metrics.key_security_energy_j,
            0.0
        )

        # required_measurements=10 produit
        # round(10 * kept_measurement_ratio) bits bruts,
        # soit round(10 * 0.70) = 7.
        reconciliation_costs = (
            calculate_reconciliation_pa_costs(
                parameters,
                raw_bit_count=7
            )
        )

        self.assertAlmostEqual(
            cost_metrics.key_latency_s,
            reconciliation_costs["latency_s"],
            places=12
        )

    # Des métriques qui ne correspondent pas
    # à la décision doivent être refusées.
    def test_mismatched_metrics_are_rejected(self):

        parameters = create_test_parameters()

        decision = Decision(
            AuthenticationAction.A1,
            KeyAction.K0
        )

        context = Context(
            snr_db=5.0,
            doppler_hz=0.0,
            battery_energy_j=28000.0,
            criticality=0,
            key_age_s=100.0,
            messages_with_current_key=2,
            rff_profile_available=True,
            renewal_required=False,
            key_expired=False,
            compromise_suspected=False,
            key_deadline_s=10000.0,
            remaining_duty_cycle_airtime_s=100.0
        )

        with self.assertRaises(ValueError):

            build_cost_metrics(
                decision=decision,
                authentication_metrics=(
                    create_a2_metrics()
                ),
                key_metrics=create_key_metrics(
                    KeyAction.K0,
                    required_measurements=None
                ),
                context=context,
                parameters=parameters
            )


# Cette condition permet aussi
# de lancer directement ce fichier.
if __name__ == "__main__":

    unittest.main()
