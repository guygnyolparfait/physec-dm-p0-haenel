# On importe la bibliothèque math de Python.
#
# Elle nous permet d'utiliser :
# - log10 pour les conversions en décibels ;
# - pi pour la constante mathématique π.
import math


# On importe la fonction j0 depuis SciPy.
#
# j0 calcule la fonction de Bessel d'ordre zéro.
#
# Cette fonction est nécessaire pour le modèle
# temporel de Clarke-Jakes :
#
# rho_time = J0(2 * pi * f_d * Delta_t)
from scipy.special import j0


# On importe ChannelMetrics depuis models.py.
#
# Cette classe permet de regrouper les résultats
# calculés par les fonctions du canal.
from physec_dm.models import ChannelMetrics


# Cette fonction convertit une valeur en décibels
# vers sa forme linéaire.
#
# Elle correspond à la relation :
#
# gamma = 10 ** (Gamma_dB / 10)
#
# Exemple :
#
# 0 dB devient 1
# 10 dB devient 10
# -10 dB devient 0.1
def convert_db_to_linear(value_db):

    # L'opérateur ** signifie "puissance".
    #
    # On divise d'abord la valeur en dB par 10,
    # puis on élève 10 à cette puissance.
    value_linear = 10 ** (
        value_db / 10
    )

    # On retourne la valeur linéaire calculée.
    return value_linear


# Cette fonction effectue la conversion inverse.
#
# Elle transforme une valeur linéaire
# en valeur exprimée en décibels.
#
# La relation utilisée est :
#
# Gamma_dB = 10 * log10(gamma)
def convert_linear_to_db(value_linear):

    # Le logarithme d'une valeur nulle
    # ou négative n'est pas défini dans ce contexte.
    if value_linear <= 0:

        raise ValueError(
            "La valeur linéaire doit être "
            "strictement supérieure à zéro."
        )

    # math.log10 calcule le logarithme
    # en base 10.
    value_db = 10 * math.log10(
        value_linear
    )

    return value_db


# Cette fonction calcule la perte de propagation
# avec le modèle log-distance.
#
# La relation utilisée est :
#
# PL(d) =
#     PL(d0)
#     + 10 * n * log10(d / d0)
#
# avec :
#
# d
#     distance entre l'émetteur et le récepteur ;
#
# d0
#     distance de référence ;
#
# n
#     exposant de perte.
#
# Le shadowing X_sh,t n'appartient pas à PL(d) dans la
# modélisation : il est ajouté séparément, avec un signe
# positif, dans le bilan de liaison
# (calculate_received_power_dbm). Le confondre avec une
# perte supplémentaire inverserait son signe.
def calculate_path_loss_db(
    distance_m,
    reference_distance_m,
    reference_path_loss_db,
    path_loss_exponent
):

    # Une distance réelle doit être
    # strictement supérieure à zéro.
    if distance_m <= 0:

        raise ValueError(
            "La distance doit être "
            "strictement supérieure à zéro."
        )

    # La distance de référence doit également
    # être strictement positive.
    if reference_distance_m <= 0:

        raise ValueError(
            "La distance de référence doit être "
            "strictement supérieure à zéro."
        )

    # L'exposant de perte doit être positif.
    if path_loss_exponent <= 0:

        raise ValueError(
            "L'exposant de perte doit être "
            "strictement supérieur à zéro."
        )

    # On calcule le rapport d / d0.
    distance_ratio = (
        distance_m
        / reference_distance_m
    )

    # On applique ensuite le modèle log-distance.
    path_loss_db = (
        reference_path_loss_db
        + 10
        * path_loss_exponent
        * math.log10(distance_ratio)
    )

    return path_loss_db


# Cette fonction calcule la puissance reçue.
#
# La relation du bilan de liaison est :
#
# P_rx =
#     P_tx
#     + G_tx
#     + G_rx
#     - PL
#     - L_system
#     + X_sh,t
#
# Toutes les valeurs sont exprimées en dB ou dBm.
#
# Le shadowing est ajouté avec un signe positif : une
# valeur positive de X_sh,t représente un signal
# ponctuellement plus favorable que la moyenne, pas une
# perte supplémentaire.
def calculate_received_power_dbm(
    tx_power_dbm,
    tx_antenna_gain_dbi,
    rx_antenna_gain_dbi,
    path_loss_db,
    system_loss_db,
    shadowing_db=0.0
):

    # On additionne les gains, on retire les pertes,
    # puis on ajoute la fluctuation de shadowing.
    received_power_dbm = (
        tx_power_dbm
        + tx_antenna_gain_dbi
        + rx_antenna_gain_dbi
        - path_loss_db
        - system_loss_db
        + shadowing_db
    )

    return received_power_dbm


# Cette fonction calcule la puissance
# du bruit thermique du récepteur.
#
# L'approximation utilisée est :
#
# P_noise =
#     -174
#     + 10 * log10(BW)
#     + NF
#
# avec :
#
# -174 dBm/Hz
#     densité spectrale de bruit thermique approximative ;
#
# BW
#     bande passante en hertz ;
#
# NF
#     figure de bruit en décibels.
def calculate_noise_power_dbm(
    bandwidth_hz,
    noise_figure_db
):

    # La bande passante doit être positive,
    # car son logarithme est utilisé.
    if bandwidth_hz <= 0:

        raise ValueError(
            "La bande passante doit être "
            "strictement supérieure à zéro."
        )

    # On applique la formule du bruit thermique.
    noise_power_dbm = (
        -174.0
        + 10 * math.log10(bandwidth_hz)
        + noise_figure_db
    )

    return noise_power_dbm


# Cette fonction calcule le SNR exprimé en dB.
#
# La relation utilisée est :
#
# Gamma_dB =
#     P_received_dBm
#     - P_noise_dBm
def calculate_snr_db(
    received_power_dbm,
    noise_power_dbm
):

    snr_db = (
        received_power_dbm
        - noise_power_dbm
    )

    return snr_db


# Cette fonction calcule la fréquence Doppler.
#
# La relation exacte retenue dans notre modélisation est :
#
# f_d = v * f_c / c
#
# avec :
#
# v
#     vitesse effective en m/s ;
#
# f_c
#     fréquence porteuse en Hz ;
#
# c
#     vitesse de la lumière en m/s.
#
# Important :
#
# notre équation officielle ne contient pas cos(theta).
def calculate_doppler_hz(
    speed_m_s,
    carrier_frequency_hz,
    speed_of_light_m_s
):

    # Une vitesse effective négative
    # n'est pas utilisée dans notre modèle.
    if speed_m_s < 0:

        raise ValueError(
            "La vitesse effective ne peut pas "
            "être négative."
        )

    # La fréquence porteuse doit être positive.
    if carrier_frequency_hz <= 0:

        raise ValueError(
            "La fréquence porteuse doit être "
            "strictement supérieure à zéro."
        )

    # La vitesse de la lumière doit être positive.
    if speed_of_light_m_s <= 0:

        raise ValueError(
            "La vitesse de la lumière doit être "
            "strictement supérieure à zéro."
        )

    # On applique directement l'équation du Doppler.
    doppler_hz = (
        speed_m_s
        * carrier_frequency_hz
        / speed_of_light_m_s
    )

    return doppler_hz


# Cette fonction calcule la corrélation temporelle
# entre les observations d'Alice et Bob.
#
# La relation de Clarke-Jakes est :
#
# rho_time =
#     J0(
#         2 * pi * f_d * Delta_t
#     )
#
# La fonction J0 peut retourner une valeur négative.
#
# Cette valeur négative doit être conservée
# dans le modèle nominal.
def calculate_temporal_correlation(
    doppler_hz,
    probe_delay_s
):

    # Le Doppler est déjà calculé comme une fréquence positive
    # ou nulle dans notre modèle.
    if doppler_hz < 0:

        raise ValueError(
            "La fréquence Doppler ne peut pas "
            "être négative."
        )

    # Le délai entre les sondages doit être positif ou nul.
    if probe_delay_s < 0:

        raise ValueError(
            "Le délai entre les sondages "
            "ne peut pas être négatif."
        )

    # On calcule d'abord l'argument de J0.
    bessel_argument = (
        2
        * math.pi
        * doppler_hz
        * probe_delay_s
    )

    # j0 retourne un type numérique SciPy.
    #
    # float permet de convertir le résultat
    # en nombre décimal Python simple.
    temporal_correlation = float(
        j0(bessel_argument)
    )

    return temporal_correlation


# Cette fonction calcule la corrélation
# liée au niveau de bruit.
#
# La relation utilisée est :
#
# rho_noise =
#     gamma / (1 + gamma)
#
# où gamma représente le SNR linéaire.
def calculate_noise_correlation(
    snr_linear
):

    # Le SNR linéaire peut être nul,
    # mais il ne peut pas être négatif.
    if snr_linear < 0:

        raise ValueError(
            "Le SNR linéaire ne peut pas "
            "être négatif."
        )

    noise_correlation = (
        snr_linear
        / (1 + snr_linear)
    )

    return noise_correlation


# Cette fonction calcule la corrélation finale
# entre Alice et Bob.
#
# La relation officielle est :
#
# rho_AB =
#     rho_HW
#     * rho_time
#     * rho_noise
#
# Cette relation est une construction
# de notre étude à partir des trois facteurs.
def calculate_reciprocity(
    hardware_reciprocity,
    temporal_correlation,
    noise_correlation
):

    # Le facteur matériel appartient à [0, 1].
    if (
        hardware_reciprocity < 0
        or hardware_reciprocity > 1
    ):

        raise ValueError(
            "La réciprocité matérielle doit "
            "appartenir à [0, 1]."
        )

    # Une corrélation doit appartenir à [-1, 1].
    if (
        temporal_correlation < -1
        or temporal_correlation > 1
    ):

        raise ValueError(
            "La corrélation temporelle doit "
            "appartenir à [-1, 1]."
        )

    # Le facteur lié au bruit appartient à [0, 1].
    if (
        noise_correlation < 0
        or noise_correlation > 1
    ):

        raise ValueError(
            "La corrélation liée au bruit doit "
            "appartenir à [0, 1]."
        )

    # On multiplie les trois facteurs.
    rho_ab = (
        hardware_reciprocity
        * temporal_correlation
        * noise_correlation
    )

    # Aucun max(0, rho_ab) n'est appliqué ici.
    #
    # Le signe est donc conservé.
    return rho_ab


# Cette fonction représente uniquement
# une variante d'analyse de sensibilité.
#
# Elle applique :
#
# rho_AB_positive =
#     max(0, rho_AB)
#
# Cette fonction ne doit jamais remplacer
# calculate_reciprocity dans le modèle nominal.
def calculate_truncated_reciprocity(
    rho_ab
):

    truncated_reciprocity = max(
        0.0,
        rho_ab
    )

    return truncated_reciprocity


# Cette fonction calcule RÉELLEMENT phi_var_t, la
# condition de variabilité temporelle du canal.
#
# Dans la modélisation (Section VI.F), une corrélation
# rho_AB élevée prouve seulement que Bob et Alice
# PEUVENT s'accorder (phi_agree) ; elle ne prouve pas que
# le canal varie assez dans le temps pour empêcher un
# espion de deviner la même clé à partir d'observations
# répétées. phi_var doit donc être une condition séparée.
#
# Aucune formule de phi_var n'est donnée dans le document :
# nous la construisons ici comme un test statistique de
# dispersion sur les dernières observations de rho_AB.
#
# Un canal figé (rho_AB quasi constant d'une période à
# l'autre) produirait des mesures très corrélées entre
# elles dans le temps, donc une entropie effective réduite,
# même si chaque mesure individuelle a un bon KDR. Nous
# testons donc :
#
# phi_var_t =
#     écart-type(rho_AB sur la fenêtre) >= seuil
#
# Statut : dérivé/politique. L'écart-type est une mesure de
# dispersion standard ; le seuil minimal et la taille de la
# fenêtre sont des choix de politique explicites, à balayer
# en sensibilité (voir Étape 6 du protocole).
#
# Cette fonction retourne None tant que la fenêtre ne
# contient pas assez d'observations pour juger — dans ce
# cas, l'appelant doit se limiter à la faisabilité d'accord
# seule (comme le prévoit calculate_phy_feasibility de
# key_generation.py), jamais annoncer une variabilité non
# encore mesurée.
def calculate_window_std_dev(
    rho_ab_window
):

    window_mean = sum(rho_ab_window) / len(
        rho_ab_window
    )

    squared_deviations = [
        (value - window_mean) ** 2
        for value in rho_ab_window
    ]

    window_variance = sum(
        squared_deviations
    ) / len(rho_ab_window)

    return math.sqrt(
        window_variance
    )


# Cette fonction calcule l'autocorrélation au décalage 1
# de la fenêtre de rho_AB.
#
# Une autocorrélation élevée indique que deux observations
# consécutives se ressemblent trop : le canal varie
# statistiquement (écart-type suffisant), mais de façon
# trop prévisible d'une période à l'autre pour apporter une
# entropie réellement nouvelle à chaque mesure.
#
# Formule standard (corrélation de Pearson entre la série
# et elle-même décalée d'un rang) :
#
# r_1 =
#     somme[(x_i - moyenne)(x_{i+1} - moyenne)]
#     / somme[(x_i - moyenne)^2]
#
# Statut : dérivé (statistique standard).
def calculate_lag1_autocorrelation(
    rho_ab_window
):

    window_mean = sum(rho_ab_window) / len(
        rho_ab_window
    )

    centered = [
        value - window_mean
        for value in rho_ab_window
    ]

    denominator = sum(
        value ** 2
        for value in centered
    )

    # Une fenêtre parfaitement constante (canal figé) a une
    # variance nulle : l'autocorrélation n'est pas définie
    # au sens strict. Nous retenons 1.0 (prévisibilité
    # maximale), le cas le plus défavorable pour phi_var,
    # cohérent avec le fait qu'un canal figé doit de toute
    # façon échouer sur le critère d'écart-type.
    if denominator == 0.0:

        return 1.0

    numerator = sum(
        centered[index] * centered[index + 1]
        for index in range(len(centered) - 1)
    )

    return numerator / denominator


# Cette fonction quantifie la fenêtre par signe, relative à
# sa PROPRE médiane (convention explicite de cette étude,
# statut politique — le document ne fixe aucune convention
# de quantification pour ce diagnostic), puis calcule :
#
# - le taux de transition (fraction de changements de bit
#   d'une période à l'autre) ;
# - la fréquence maximale d'un même bit sur la fenêtre ;
# - une min-entropie empirique bornée
#   H_min = -log2(fréquence maximale).
#
# Une min-entropie calculée sur un bit MARGINAL isolé serait
# triviale sous l'hypothèse gaussienne centrée déjà adoptée
# par ce modèle (chaque bit isolé y est par construction
# équilibré) : cette fonction porte donc sur la SÉQUENCE
# temporelle quantifiée, pas sur un bit isolé, ce qui la
# rend informative sans introduire de biais non modélisé
# ailleurs dans ce document.
def calculate_quantized_transition_statistics(
    rho_ab_window
):

    sorted_window = sorted(
        rho_ab_window
    )

    window_length = len(
        sorted_window
    )

    middle_index = window_length // 2

    if window_length % 2 == 0:

        window_median = (
            sorted_window[middle_index - 1]
            + sorted_window[middle_index]
        ) / 2

    else:

        window_median = sorted_window[
            middle_index
        ]

    quantized_bits = [
        1 if value >= window_median else 0
        for value in rho_ab_window
    ]

    transition_count = sum(
        1
        for index in range(len(quantized_bits) - 1)
        if quantized_bits[index]
        != quantized_bits[index + 1]
    )

    transition_rate = transition_count / (
        len(quantized_bits) - 1
    )

    ones_count = sum(quantized_bits)
    zeros_count = len(quantized_bits) - ones_count

    maximum_bit_frequency = max(
        ones_count,
        zeros_count
    ) / len(quantized_bits)

    minimum_entropy_bits = -math.log2(
        maximum_bit_frequency
    )

    return {
        "transition_rate": transition_rate,
        "maximum_bit_frequency": (
            maximum_bit_frequency
        ),
        "minimum_entropy_bits": (
            minimum_entropy_bits
        )
    }


# Cette fonction combine QUATRE conditions réellement
# calculées pour juger phi_var_t (aucune n'est à elle seule
# suffisante, d'où la combinaison par ET logique) :
#
# 1. écart-type de rho_AB sur la fenêtre >= seuil
#    (canal non figé) ;
# 2. |autocorrélation à décalage 1| <= seuil
#    (observations successives non redondantes) ;
# 3. fréquence maximale du bit quantifié (signe relatif à
#    la médiane de la fenêtre) <= seuil, c'est-à-dire une
#    min-entropie empirique de séquence >= seuil implicite
#    (le bit quantifié ne reste pas bloqué du même côté) ;
# 4. nombre de mesures valides sur la fenêtre
#    (taille de fenêtre * kept_measurement_ratio) >= minimum
#    requis.
#
# Statut : dérivé (statistiques standard, formules 1-3) et
# politique (les quatre seuils et la taille de fenêtre),
# à balayer en sensibilité (Étape 6 du protocole).
def calculate_temporal_variability_feasible(
    rho_ab_window,
    minimum_window_size,
    minimum_std_dev,
    maximum_lag1_autocorrelation,
    maximum_bit_frequency,
    kept_measurement_ratio,
    minimum_valid_measurements
):

    if minimum_window_size <= 1:

        raise ValueError(
            "minimum_window_size doit être "
            "strictement supérieur à 1."
        )

    if minimum_std_dev < 0:

        raise ValueError(
            "minimum_std_dev ne peut pas être négatif."
        )

    if (
        maximum_lag1_autocorrelation < 0
        or maximum_lag1_autocorrelation > 1
    ):

        raise ValueError(
            "maximum_lag1_autocorrelation doit "
            "appartenir à [0, 1]."
        )

    if (
        maximum_bit_frequency <= 0.5
        or maximum_bit_frequency > 1
    ):

        raise ValueError(
            "maximum_bit_frequency doit appartenir "
            "à ]0,5 ; 1]."
        )

    if (
        kept_measurement_ratio <= 0
        or kept_measurement_ratio > 1
    ):

        raise ValueError(
            "kept_measurement_ratio doit appartenir "
            "à ]0, 1]."
        )

    if minimum_valid_measurements <= 0:

        raise ValueError(
            "minimum_valid_measurements doit être "
            "strictement positif."
        )

    if len(rho_ab_window) < minimum_window_size:

        return None

    # Condition 1 : dispersion suffisante.
    window_std_dev = calculate_window_std_dev(
        rho_ab_window
    )

    std_dev_ok = (
        window_std_dev
        >= minimum_std_dev
    )

    # Condition 2 : non-redondance temporelle.
    lag1_autocorrelation = (
        calculate_lag1_autocorrelation(
            rho_ab_window
        )
    )

    autocorrelation_ok = (
        abs(lag1_autocorrelation)
        <= maximum_lag1_autocorrelation
    )

    # Condition 3 : transitions/min-entropie de la
    # séquence quantifiée par signe.
    transition_statistics = (
        calculate_quantized_transition_statistics(
            rho_ab_window
        )
    )

    transitions_ok = (
        transition_statistics[
            "maximum_bit_frequency"
        ]
        <= maximum_bit_frequency
    )

    # Condition 4 : nombre de mesures valides suffisant.
    valid_measurements = (
        len(rho_ab_window)
        * kept_measurement_ratio
    )

    valid_measurements_ok = (
        valid_measurements
        >= minimum_valid_measurements
    )

    return (
        std_dev_ok
        and autocorrelation_ok
        and transitions_ok
        and valid_measurements_ok
    )


# Cette fonction regroupe tous les calculs du canal.
#
# Elle permet de construire directement
# un objet ChannelMetrics.
#
# Elle accepte deux modes :
#
# "imposed"
#     le SNR est fourni directement ;
#
# "distance"
#     le SNR est calculé avec le bilan de liaison.
def calculate_channel_metrics(
    parameters,
    snr_db=None,
    distance_m=None,
    speed_m_s=None,
    shadowing_db=0.0
):

    # Si aucune vitesse particulière n'est fournie,
    # on utilise la vitesse enregistrée
    # dans parameters.py.
    if speed_m_s is None:

        speed_m_s = (
            parameters.effective_speed_m_s
        )

    # ------------------------------------------------------------
    # MODE 1 : SNR IMPOSÉ
    # ------------------------------------------------------------

    if parameters.snr_mode == "imposed":

        # Si aucun SNR n'est transmis directement,
        # on utilise le SNR moyen du scénario.
        if snr_db is None:

            snr_db = parameters.mean_snr_db

        # Une valeur None empêcherait les calculs.
        if snr_db is None:

            raise ValueError(
                "Un SNR en dB est requis "
                "dans le mode imposé."
            )

    # ------------------------------------------------------------
    # MODE 2 : SNR CALCULÉ À PARTIR DE LA DISTANCE
    # ------------------------------------------------------------

    elif parameters.snr_mode == "distance":

        # La distance doit être fournie
        # pour calculer la perte de propagation.
        if distance_m is None:

            raise ValueError(
                "La distance est requise "
                "dans le mode distance."
            )

        # Ces trois paramètres doivent avoir été définis
        # avant d'utiliser le mode distance.
        if parameters.tx_power_dbm is None:

            raise ValueError(
                "tx_power_dbm doit être défini "
                "dans le mode distance."
            )

        if parameters.reference_path_loss_db is None:

            raise ValueError(
                "reference_path_loss_db doit être défini "
                "dans le mode distance."
            )

        if parameters.path_loss_exponent is None:

            raise ValueError(
                "path_loss_exponent doit être défini "
                "dans le mode distance."
            )

        # On calcule la perte de propagation
        # (déterministe, sans shadowing).
        path_loss_db = calculate_path_loss_db(
            distance_m=distance_m,
            reference_distance_m=(
                parameters.reference_distance_m
            ),
            reference_path_loss_db=(
                parameters.reference_path_loss_db
            ),
            path_loss_exponent=(
                parameters.path_loss_exponent
            )
        )

        # On calcule la puissance reçue.
        #
        # Le shadowing est ajouté ici, séparément
        # de la perte de propagation.
        received_power_dbm = (
            calculate_received_power_dbm(
                tx_power_dbm=(
                    parameters.tx_power_dbm
                ),
                tx_antenna_gain_dbi=(
                    parameters.tx_antenna_gain_dbi
                ),
                rx_antenna_gain_dbi=(
                    parameters.rx_antenna_gain_dbi
                ),
                path_loss_db=path_loss_db,
                system_loss_db=(
                    parameters.system_loss_db
                ),
                shadowing_db=shadowing_db
            )
        )

        # On calcule la puissance de bruit.
        noise_power_dbm = (
            calculate_noise_power_dbm(
                bandwidth_hz=(
                    parameters.bandwidth_hz
                ),
                noise_figure_db=(
                    parameters.noise_figure_db
                )
            )
        )

        # On calcule enfin le SNR en dB.
        snr_db = calculate_snr_db(
            received_power_dbm,
            noise_power_dbm
        )

    # ------------------------------------------------------------
    # MODE INCONNU
    # ------------------------------------------------------------

    else:

        raise ValueError(
            "Le mode SNR doit valoir "
            "'imposed' ou 'distance'."
        )

    # On convertit le SNR dB en SNR linéaire.
    snr_linear = convert_db_to_linear(
        snr_db
    )

    # On calcule la fréquence Doppler.
    doppler_hz = calculate_doppler_hz(
        speed_m_s=speed_m_s,
        carrier_frequency_hz=(
            parameters.carrier_frequency_hz
        ),
        speed_of_light_m_s=(
            parameters.speed_of_light_m_s
        )
    )

    # On calcule la corrélation temporelle.
    temporal_correlation = (
        calculate_temporal_correlation(
            doppler_hz=doppler_hz,
            probe_delay_s=(
                parameters.probe_delay_s
            )
        )
    )

    # On calcule la corrélation liée au bruit.
    noise_correlation = (
        calculate_noise_correlation(
            snr_linear
        )
    )

    # On calcule la corrélation finale.
    rho_ab = calculate_reciprocity(
        hardware_reciprocity=(
            parameters.hardware_reciprocity
        ),
        temporal_correlation=(
            temporal_correlation
        ),
        noise_correlation=(
            noise_correlation
        )
    )

    # On regroupe tous les résultats
    # dans l'objet défini dans models.py.
    channel_metrics = ChannelMetrics(
        snr_db=snr_db,
        snr_linear=snr_linear,
        doppler_hz=doppler_hz,
        temporal_correlation=(
            temporal_correlation
        ),
        noise_correlation=(
            noise_correlation
        ),
        rho_ab=rho_ab
    )

    return channel_metrics
