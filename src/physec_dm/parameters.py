# On importe la bibliothèque math de Python.
#
# Elle nous permet d'utiliser :
# - pi pour la constante mathématique π ;
# - cos pour calculer la corrélation minimale ;
# - isclose pour comparer deux nombres décimaux.
import math


# Cette classe contient tous les paramètres du projet PHYSEC-DM.
#
# L'objectif est de centraliser les valeurs dans un seul fichier.
#
# Les autres fichiers utiliseront cet objet :
# - channel.py pour le canal ;
# - authentication.py pour la FAR et la FRR ;
# - key_generation.py pour le KDR et la cryptopériode ;
# - energy_latency.py pour l'énergie et la latence ;
# - decision_maker.py pour les contraintes et les seuils.
#
# Les paramètres qui ne sont pas encore définis
# dans la modélisation restent volontairement à None.
#
# None signifie :
# "cette valeur doit encore être mesurée, profilée ou validée".
#
# Nous évitons ainsi d'inventer une valeur silencieusement.
class Parameters:

    # La fonction __init__ est appelée automatiquement
    # lorsqu'on crée un objet Parameters.
    def __init__(self):

        # ============================================================
        # 1. CONSTANTES ET SCÉNARIO GÉNÉRAL
        # ============================================================

        # Vitesse de la lumière dans le vide.
        #
        # Unité : m/s.
        #
        # Cette constante intervient dans :
        #
        # f_d = v * f_c / c
        #
        # Statut : constante physique.
        self.speed_of_light_m_s = 299792458.0

        # Mode utilisé pour obtenir le SNR.
        #
        # "imposed" :
        #     le SNR est directement imposé par le scénario.
        #
        # "distance" :
        #     le SNR est calculé avec le bilan de liaison.
        #
        # Nous commençons avec "imposed"
        # pour valider plus facilement le modèle.
        self.snr_mode = "imposed"

        # SNR moyen du scénario de départ.
        #
        # Unité : dB.
        #
        # Statut : paramètre de scénario.
        self.mean_snr_db = 5.0

        # Écart-type du shadowing.
        #
        # Unité : dB.
        #
        # Statut : paramètre de scénario
        # à étudier dans l'analyse de sensibilité.
        self.shadowing_std_db = 3.0

        # ============================================================
        # 2. PARAMÈTRES DU CANAL
        # ============================================================

        # Fréquence porteuse de la bande EU868.
        #
        # Unité : Hz.
        self.carrier_frequency_hz = 868000000.0

        # Bande passante LoRa.
        #
        # Unité : Hz.
        self.bandwidth_hz = 125000.0

        # Figure de bruit du récepteur.
        #
        # Unité : dB.
        self.noise_figure_db = 6.0

        # Facteur matériel de réciprocité.
        #
        # Il intervient dans :
        #
        # rho_AB = rho_HW * rho_time * rho_noise
        #
        # Statut : valeur calibrée du modèle.
        self.hardware_reciprocity = 0.9582

        # Vitesse effective du nœud.
        #
        # Unité : m/s.
        #
        # La valeur zéro représente un nœud fixe.
        self.effective_speed_m_s = 0.0

        # Délai entre les mesures d'Alice et Bob.
        #
        # Unité : s.
        #
        # Il intervient dans :
        #
        # rho_time = J0(2 * pi * f_d * Delta_t)
        self.probe_delay_s = 1.0

        # ------------------------------------------------------
        # Extension : espionne passive Ève
        # ------------------------------------------------------
        #
        # Ces paramètres alimentent UNIQUEMENT
        # physec_dm.eve_validation, jamais decision_maker.py
        # ni la construction du Context présenté au DM. Ève
        # n'observe jamais rien que Bob pourrait utiliser en
        # temps réel.
        #
        # Séparation Bob-Ève (pertinente pour la liaison
        # montante Alice->Bob vs Alice->Ève) et séparation
        # Alice-Ève (pertinente pour la liaison descendante
        # Bob->Alice vs Bob->Ève). Une hypothèse symétrique
        # (les deux égales à eve_standoff_distance_m) est
        # utilisée par défaut comme simplification explicite
        # de scénario ; les deux distances peuvent être
        # renseignées séparément pour une géométrie plus
        # réaliste.
        #
        # Statut : scénario, à balayer en sensibilité
        # (aucune distance "sûre" universelle : la littérature
        # suppose souvent une demi-longueur d'onde, mais cette
        # hypothèse peut être insuffisante en propagation
        # longue portée).
        self.eve_standoff_distance_m = 0.10

        # Marge de secret minimale exigée :
        #
        # KDR_Eve - KDR_AB > eve_secrecy_margin_minimum
        #
        # Statut : politique, critère exploratoire
        # pré-enregistré, balayé en sensibilité
        # (0,05 / 0,10 / 0,15).
        self.eve_secrecy_margin_minimum = 0.10

        # Paramètres utilisés uniquement dans le mode "distance".

        # Puissance d'émission.
        #
        # Unité : dBm.
        #
        # Elle reste à None tant que le scénario
        # de distance n'est pas défini.
        self.tx_power_dbm = None

        # Distance de référence.
        #
        # Unité : m.
        self.reference_distance_m = 1.0

        # Perte de propagation à la distance de référence.
        #
        # Unité : dB.
        #
        # Statut : à calibrer.
        self.reference_path_loss_db = None

        # Exposant du modèle log-distance.
        #
        # Statut : à calibrer selon l'environnement.
        self.path_loss_exponent = None

        # Gains d'antenne.
        #
        # Unité : dBi.
        self.tx_antenna_gain_dbi = 0.0
        self.rx_antenna_gain_dbi = 0.0

        # Pertes supplémentaires du système.
        #
        # Unité : dB.
        self.system_loss_db = 0.0

        # ============================================================
        # 3. PARAMÈTRES DE L'AUTHENTIFICATION
        # ============================================================

        # Nombre d'attributs de l'empreinte RFF.
        #
        # Le vecteur est :
        #
        # [CFO, DCO, PO]
        self.rff_feature_count = 3

        # Taux de faux rejet cible.
        #
        # Cette valeur sert à calculer le seuil :
        #
        # theta = F_chi2_inverse(1 - target_frr)
        self.target_frr = 0.05

        # Seuil nominal pour :
        #
        # n_f = 3
        # target_frr = 0.05
        #
        # Statut : valeur dérivée.
        self.rff_threshold = 7.814727903251179

        # Séparation normalisée entre Alice et Mallory.
        #
        # Elle correspond à d_M.
        #
        # Elle intervient dans :
        #
        # lambda_M = d_M ** 2 * gamma_M
        #
        # Statut : paramètre de scénario.
        self.mallory_separation = 2.0

        # Taille du tag AES-CMAC.
        #
        # Unité : octets.
        self.mac_tag_bytes = 8

        # Même taille exprimée en bits.
        #
        # Cette valeur doit rester égale à :
        #
        # 8 * mac_tag_bytes
        self.mac_tag_bits = 64

        # Temps de traitement RFF chez Bob.
        #
        # Unité : s.
        #
        # 1.84 ms = 0.00184 s.
        #
        # Statut : ancrage de littérature,
        # non universel pour toutes les plateformes.
        self.rff_processing_time_bob_s = 0.00184

        # Latence complète du défi-réponse.
        #
        # Unité : s.
        #
        # Cette valeur reste à définir.
        self.challenge_response_latency_s = None

        # Nombre de cycles du calcul AES-CMAC.
        #
        # Unité : cycles.
        #
        # Cette valeur doit être profilée sur STM32L1.
        self.mac_cycles = None

        # ============================================================
        # 4. GÉNÉRATION ET GESTION DE CLÉ
        # ============================================================

        # KDR maximal acceptable entre Alice et Bob.
        self.maximum_kdr = 0.30

        # Corrélation minimale équivalente :
        #
        # rho_min = cos(pi * KDR_max)
        #
        # Statut : valeur dérivée.
        self.minimum_correlation = math.cos(
            math.pi * self.maximum_kdr
        )

        # Longueur de la clé cible.
        #
        # Unité : bits.
        self.key_length_bits = 128

        # Proportion de mesures conservées.
        #
        # 0.70 signifie 70 %.
        #
        # Statut : valeur de scénario.
        self.kept_measurement_ratio = 0.70

        # Facteur exploratoire de bande de garde.
        #
        # La valeur 1.0 représente un facteur neutre.
        self.guard_band_factor = 1.0

        # Mode de quantification.
        #
        # "analytic" :
        #     utilisation de la loi de l'arc-sinus.
        #
        # "calibrated" :
        #     utilisation future d'une courbe expérimentale.
        self.quantization_mode = "analytic"

        # Faisabilité liée à la variabilité du canal.
        #
        # None conserve le comportement honnête d'origine :
        # tant qu'aucune valeur n'est explicitement fournie
        # à calculate_key_metrics/run_mission_step, le champ
        # est calculé RÉELLEMENT à partir d'une fenêtre
        # glissante d'observations de rho_AB (voir
        # channel.calculate_temporal_variability_feasible),
        # au lieu de rester un booléen figé par scénario.
        self.variation_feasible = None

        # Taille minimale de la fenêtre d'observations de
        # rho_AB nécessaire pour juger phi_var.
        #
        # Statut : politique, à balayer en sensibilité.
        self.variability_window_size = 10

        # Écart-type minimal de rho_AB sur la fenêtre pour
        # considérer le canal comme suffisamment variable
        # dans le temps.
        #
        # Statut : politique, à balayer en sensibilité
        # (0,02 / 0,05 / 0,10).
        self.variability_minimum_std_dev = 0.05

        # Autocorrélation maximale à décalage 1 tolérée sur
        # la fenêtre : au-delà, deux observations
        # consécutives sont jugées trop redondantes pour
        # apporter une entropie réellement nouvelle.
        #
        # Statut : politique, à balayer en sensibilité
        # (0,50 / 0,70 / 0,90).
        self.variability_maximum_lag1_autocorrelation = (
            0.70
        )

        # Fréquence maximale tolérée d'un même bit après
        # quantification par signe (relative à la médiane
        # de la fenêtre) : au-delà, le bit quantifié reste
        # trop souvent bloqué du même côté (min-entropie
        # empirique de séquence insuffisante).
        #
        # Statut : politique, à balayer en sensibilité
        # (0,80 / 0,90 / 0,95).
        self.variability_maximum_bit_frequency = 0.90

        # Nombre minimal de mesures valides
        # (taille de fenêtre * kept_measurement_ratio)
        # exigé pour juger phi_var.
        #
        # Statut : politique, à balayer en sensibilité.
        self.variability_minimum_valid_measurements = 5

        # Petite valeur de protection numérique
        # utilisée pour éviter une division par zéro.
        self.key_numerical_epsilon = 1e-12

        # Âge maximal d'une clé.
        #
        # Unité : s.
        self.maximum_key_age_s = 86400.0

        # Nombre maximal de messages par clé.
        self.maximum_messages_per_key = 1000

        # Seuil de renouvellement anticipé.
        #
        # Le renouvellement devient nécessaire si :
        #
        # q_t >= renewal_trigger
        self.renewal_trigger = 0.60

        # Échéance minimale de renouvellement T_min.
        #
        # Unité : s.
        #
        # Statut : à valider.
        self.minimum_deadline_s = None

        # Nombre de cycles de réconciliation par bit.
        #
        # Unité : cycles/bit.
        self.reconciliation_cycles_per_bit = None

        # Nombre de cycles de l'amplification
        # de confidentialité.
        #
        # Unité : cycles.
        self.privacy_amplification_cycles = None

        # Énergie des messages de réconciliation.
        #
        # Unité : J.
        self.reconciliation_message_energy_j = None

        # Latence des messages de réconciliation.
        #
        # Unité : s.
        self.reconciliation_message_latency_s = None

        # Niveau de sécurité de K2.
        #
        # Unité : bits.
        #
        # Cette valeur correspond à b_sec.
        self.security_strength_bits = None

        # Identifiant du protocole K2 complet.
        #
        # Il reste à None tant que les opérations,
        # messages et délais ne sont pas fixés.
        self.k2_protocol_id = None

        # Énergie de référence d'une signature ECC.
        #
        # Unité : J.
        #
        # Cette valeur n'est pas le coût complet de K2.
        self.ecc_signature_energy_j = 0.019

        # Temps de référence d'une signature ECC.
        #
        # Unité : s.
        #
        # 218 ms = 0.218 s.
        #
        # Cette valeur n'est pas la latence complète de K2.
        self.ecc_signature_time_s = 0.218

        # ============================================================
        # 5. PARAMÈTRES LORA
        # ============================================================

        # Facteur d'étalement.
        self.spreading_factor = 12

        # Indice du taux de correction.
        #
        # Pour 4/5, l'indice Semtech vaut 1.
        self.coding_rate_index = 1

        # Nombre de symboles du préambule.
        self.preamble_symbols = 8

        # True correspond à CRC = 1.
        self.crc_enabled = True

        # False correspond à IH = 0.
        self.implicit_header = False

        # True correspond à DE = 1.
        self.low_data_rate_optimization = True

        # Duty-cycle de 1 %.
        self.duty_cycle_fraction = 0.01

        # Taille du message applicatif.
        #
        # Unité : octets.
        self.data_payload_bytes = 32

        # Taille du sondage dédié.
        #
        # Unité : octets.
        self.probe_payload_bytes = 32

        # Taille du défi.
        #
        # Unité : octets.
        self.challenge_bytes = 8

        # Taille de la réponse.
        #
        # Unité : octets.
        self.response_bytes = 8

        # Intervalle nominal d'un sondage dédié.
        #
        # Unité : s.
        #
        # Il correspond approximativement à :
        #
        # T_air(32 octets) / 0.01
        self.dedicated_probe_interval_s = 181.0432

        # Période normale des messages.
        #
        # Unité : s.
        self.message_period_s = 60.0

        # ============================================================
        # 6. ÉNERGIE ET PLATEFORME
        # ============================================================

        # Tension d'alimentation.
        #
        # Unité : V.
        self.supply_voltage_v = 3.3

        # Courant de transmission.
        #
        # Unité : A.
        #
        # 29 mA = 0.029 A.
        self.tx_current_a = 0.029

        # Courant de réception.
        #
        # Unité : A.
        #
        # 10.8 mA = 0.0108 A.
        self.rx_current_a = 0.0108

        # Courant de sommeil radio.
        #
        # Unité : A.
        self.radio_sleep_current_a = 0.2e-6

        # Courant actif du processeur.
        #
        # Unité : A.
        self.cpu_current_a = 5.92e-3

        # Fréquence du processeur.
        #
        # Unité : Hz.
        self.cpu_frequency_hz = 32000000.0

        # Courant du MCU en sommeil avec RTC.
        #
        # Unité : A.
        self.mcu_sleep_current_a = 1.4e-6

        # Courant équivalent de fuite de la pile.
        #
        # Unité : A.
        self.battery_leak_current_a = 2.7e-6

        # Énergies qui composent l'énergie de base.
        #
        # Elles restent à None tant qu'elles
        # ne sont pas mesurées ou documentées.

        # Énergie d'acquisition du capteur.
        #
        # Unité : J.
        self.sensing_energy_j = None

        # Énergie du traitement applicatif.
        #
        # Unité : J.
        self.application_energy_j = None

        # Énergie des fenêtres RX1 et RX2.
        #
        # Unité : J.
        self.receive_windows_energy_j = None

        # Énergie de veille par période.
        #
        # Unité : J.
        self.sleep_energy_j = None

        # ============================================================
        # 7. BATTERIE ET MISSION
        # ============================================================

        # Énergie initiale de la batterie.
        #
        # Unité : J.
        self.initial_battery_energy_j = 28512.0

        # Fraction de batterie conservée comme réserve.
        #
        # 0.05 correspond à 5 %.
        self.battery_reserve_fraction = 0.05

        # Énergie minimale non consommable :
        #
        # B_min = 0.05 * B_0
        self.minimum_battery_energy_j = (
            self.battery_reserve_fraction
            * self.initial_battery_energy_j
        )

        # Probabilité qu'un message soit critique.
        #
        # Statut : à fixer pour chaque campagne.
        self.critical_message_probability = None

        # Probabilité d'une tentative de Mallory.
        #
        # Statut : à fixer pour chaque campagne.
        self.mallory_attempt_probability = None

        # ============================================================
        # 8. DECISION MAKER
        # ============================================================

        # Délai maximal pour un message critique.
        #
        # Unité : s.
        self.critical_latency_budget_s = 5.0

        # Délai maximal pour un message normal.
        #
        # Unité : s.
        self.normal_latency_budget_s = 600.0

        # FAR maximale pour un message critique.
        self.critical_far_limit = 0.01

        # FAR maximale pour un message normal.
        self.normal_far_limit = 0.05

        # Protection numérique de Tchebychev.
        self.tchebycheff_epsilon = 1e-12

        # Tolérance pour considérer
        # deux scores comme égaux.
        #
        # Statut : à valider.
        self.score_tolerance = None

        # Tolérance utilisée dans la dominance.
        #
        # Statut : à valider.
        self.dominance_tolerance = None

        # Poids des quatre objectifs.
        #
        # Ordre :
        # [énergie, latence, authentification, clé]
        #
        # Statut : politique à valider.
        self.contextual_weights = None

        # Mode utilisé lorsque l'ensemble admissible est vide.
        self.fallback_mode = "refuse"

    # Cette fonction retourne la limite de latence
    # adaptée à la criticité du message.
    def get_authentication_latency_limit(self, criticality):

        if criticality == 0:
            return self.normal_latency_budget_s

        if criticality == 1:
            return self.critical_latency_budget_s

        raise ValueError(
            "La criticité doit valoir 0 ou 1."
        )

    # Cette fonction retourne la FAR maximale
    # adaptée à la criticité du message.
    def get_far_limit(self, criticality):

        if criticality == 0:
            return self.normal_far_limit

        if criticality == 1:
            return self.critical_far_limit

        raise ValueError(
            "La criticité doit valoir 0 ou 1."
        )

    # Cette fonction retourne la liste
    # des paramètres encore non définis.
    def get_missing_parameters(self):

        missing_parameters = []

        required_parameters = {
            "challenge_response_latency_s":
                self.challenge_response_latency_s,

            "mac_cycles":
                self.mac_cycles,

            "variation_feasible":
                self.variation_feasible,

            "minimum_deadline_s":
                self.minimum_deadline_s,

            "reconciliation_cycles_per_bit":
                self.reconciliation_cycles_per_bit,

            "privacy_amplification_cycles":
                self.privacy_amplification_cycles,

            "reconciliation_message_energy_j":
                self.reconciliation_message_energy_j,

            "reconciliation_message_latency_s":
                self.reconciliation_message_latency_s,

            "security_strength_bits":
                self.security_strength_bits,

            "k2_protocol_id":
                self.k2_protocol_id,

            "sensing_energy_j":
                self.sensing_energy_j,

            "application_energy_j":
                self.application_energy_j,

            "receive_windows_energy_j":
                self.receive_windows_energy_j,

            "sleep_energy_j":
                self.sleep_energy_j,

            "critical_message_probability":
                self.critical_message_probability,

            "mallory_attempt_probability":
                self.mallory_attempt_probability,

            "score_tolerance":
                self.score_tolerance,

            "dominance_tolerance":
                self.dominance_tolerance,

            "contextual_weights":
                self.contextual_weights
        }

        for parameter_name in required_parameters:

            parameter_value = required_parameters[
                parameter_name
            ]

            if parameter_value is None:
                missing_parameters.append(
                    parameter_name
                )

        return missing_parameters

    # Cette fonction vérifie la cohérence
    # de la configuration.
    #
    # Elle retourne :
    # - une liste d'erreurs ;
    # - une liste d'avertissements.
    def validate(self, require_complete=False):

        errors = []
        warnings = []

        # Probabilités et fractions
        # qui doivent appartenir à [0, 1].
        probability_parameters = {
            "hardware_reciprocity":
                self.hardware_reciprocity,

            "target_frr":
                self.target_frr,

            "maximum_kdr":
                self.maximum_kdr,

            "kept_measurement_ratio":
                self.kept_measurement_ratio,

            "renewal_trigger":
                self.renewal_trigger,

            "duty_cycle_fraction":
                self.duty_cycle_fraction,

            "battery_reserve_fraction":
                self.battery_reserve_fraction,

            "critical_far_limit":
                self.critical_far_limit,

            "normal_far_limit":
                self.normal_far_limit
        }

        for parameter_name in probability_parameters:

            parameter_value = probability_parameters[
                parameter_name
            ]

            if parameter_value < 0 or parameter_value > 1:
                errors.append(
                    parameter_name
                    + " doit appartenir à [0, 1]."
                )

        # Probabilités de mission facultatives
        # pendant le développement.
        optional_probabilities = {
            "critical_message_probability":
                self.critical_message_probability,

            "mallory_attempt_probability":
                self.mallory_attempt_probability
        }

        for parameter_name in optional_probabilities:

            parameter_value = optional_probabilities[
                parameter_name
            ]

            if parameter_value is not None:

                if parameter_value < 0 or parameter_value > 1:
                    errors.append(
                        parameter_name
                        + " doit appartenir à [0, 1]."
                    )

        # Valeurs qui doivent être strictement positives.
        positive_parameters = {
            "speed_of_light_m_s":
                self.speed_of_light_m_s,

            "carrier_frequency_hz":
                self.carrier_frequency_hz,

            "bandwidth_hz":
                self.bandwidth_hz,

            "noise_figure_db":
                self.noise_figure_db,

            "probe_delay_s":
                self.probe_delay_s,

            "rff_feature_count":
                self.rff_feature_count,

            "mac_tag_bytes":
                self.mac_tag_bytes,

            "mac_tag_bits":
                self.mac_tag_bits,

            "key_length_bits":
                self.key_length_bits,

            "maximum_key_age_s":
                self.maximum_key_age_s,

            "maximum_messages_per_key":
                self.maximum_messages_per_key,

            "spreading_factor":
                self.spreading_factor,

            "coding_rate_index":
                self.coding_rate_index,

            "preamble_symbols":
                self.preamble_symbols,

            "data_payload_bytes":
                self.data_payload_bytes,

            "probe_payload_bytes":
                self.probe_payload_bytes,

            "challenge_bytes":
                self.challenge_bytes,

            "response_bytes":
                self.response_bytes,

            "supply_voltage_v":
                self.supply_voltage_v,

            "tx_current_a":
                self.tx_current_a,

            "rx_current_a":
                self.rx_current_a,

            "cpu_current_a":
                self.cpu_current_a,

            "cpu_frequency_hz":
                self.cpu_frequency_hz,

            "initial_battery_energy_j":
                self.initial_battery_energy_j,

            "minimum_battery_energy_j":
                self.minimum_battery_energy_j,

            "message_period_s":
                self.message_period_s,

            "critical_latency_budget_s":
                self.critical_latency_budget_s,

            "normal_latency_budget_s":
                self.normal_latency_budget_s,

            "tchebycheff_epsilon":
                self.tchebycheff_epsilon
        }

        for parameter_name in positive_parameters:

            parameter_value = positive_parameters[
                parameter_name
            ]

            if parameter_value <= 0:
                errors.append(
                    parameter_name
                    + " doit être strictement positif."
                )

        # Cohérence entre octets et bits du tag.
        expected_mac_tag_bits = (
            8 * self.mac_tag_bytes
        )

        if self.mac_tag_bits != expected_mac_tag_bits:
            errors.append(
                "mac_tag_bits doit être égal à "
                "8 * mac_tag_bytes."
            )

        # Cohérence de la corrélation minimale.
        expected_minimum_correlation = math.cos(
            math.pi * self.maximum_kdr
        )

        if not math.isclose(
            self.minimum_correlation,
            expected_minimum_correlation,
            rel_tol=1e-9,
            abs_tol=1e-12
        ):
            errors.append(
                "minimum_correlation doit être égal à "
                "cos(pi * maximum_kdr)."
            )

        # Cohérence de la réserve de batterie.
        expected_minimum_battery = (
            self.battery_reserve_fraction
            * self.initial_battery_energy_j
        )

        if not math.isclose(
            self.minimum_battery_energy_j,
            expected_minimum_battery,
            rel_tol=1e-9,
            abs_tol=1e-9
        ):
            errors.append(
                "minimum_battery_energy_j doit être égal à "
                "battery_reserve_fraction "
                "* initial_battery_energy_j."
            )

        # Les seuils critiques doivent être
        # au moins aussi stricts que les seuils normaux.
        if (
            self.critical_latency_budget_s
            > self.normal_latency_budget_s
        ):
            errors.append(
                "Le délai critique doit être inférieur "
                "ou égal au délai normal."
            )

        if (
            self.critical_far_limit
            > self.normal_far_limit
        ):
            errors.append(
                "La FAR critique doit être inférieure "
                "ou égale à la FAR normale."
            )

        # Vérification des modes autorisés.
        if self.snr_mode not in [
            "imposed",
            "distance"
        ]:
            errors.append(
                "snr_mode doit valoir "
                "'imposed' ou 'distance'."
            )

        if self.quantization_mode not in [
            "analytic",
            "calibrated"
        ]:
            errors.append(
                "quantization_mode doit valoir "
                "'analytic' ou 'calibrated'."
            )

        # L'indice LoRa doit appartenir à {1, 2, 3, 4}.
        if self.coding_rate_index not in [
            1,
            2,
            3,
            4
        ]:
            errors.append(
                "coding_rate_index doit appartenir "
                "à {1, 2, 3, 4}."
            )

        # Le mode distance exige trois paramètres
        # supplémentaires.
        if self.snr_mode == "distance":

            if self.tx_power_dbm is None:
                errors.append(
                    "tx_power_dbm est requis "
                    "pour le mode distance."
                )

            if self.reference_path_loss_db is None:
                errors.append(
                    "reference_path_loss_db est requis "
                    "pour le mode distance."
                )

            if self.path_loss_exponent is None:
                errors.append(
                    "path_loss_exponent est requis "
                    "pour le mode distance."
                )

        # Paramètres encore absents.
        missing_parameters = (
            self.get_missing_parameters()
        )

        for parameter_name in missing_parameters:

            message = (
                parameter_name
                + " reste à définir ou à valider."
            )

            # Pour une campagne complète,
            # une valeur absente devient une erreur.
            if require_complete:
                errors.append(message)

            # Pendant le développement,
            # elle reste un avertissement.
            else:
                warnings.append(message)

        return errors, warnings

    # Cette fonction exporte tous les paramètres
    # dans un dictionnaire Python.
    def to_dictionary(self):

        # vars(self) retourne les attributs de l'objet.
        #
        # dict(...) permet de créer une copie.
        return dict(
            vars(self)
        )
