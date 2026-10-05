# On importe Enum depuis la bibliothèque standard de Python.
# Enum permet de créer une liste fermée de valeurs autorisées.
# Ici, cela évite d'utiliser par erreur une action qui n'existe pas
# dans notre modélisation, comme A3 ou K3.
from enum import Enum


# Cette classe représente les deux actions d'authentification
# définies dans notre modélisation.
#
# A1 : authentification conventionnelle par MAC.
# A2 : authentification par empreinte radio RFF avec
#      défi-réponse cryptographique en cas de rejet.
class AuthenticationAction(Enum):

    # La valeur affichée et enregistrée pour la première action est "A1".
    A1 = "A1"

    # La valeur affichée et enregistrée pour la deuxième action est "A2".
    A2 = "A2"


# Cette classe représente les quatre actions possibles
# pour la gestion ou le renouvellement de la clé.
class KeyAction(Enum):

    # K0 signifie que l'on conserve la clé actuellement utilisée.
    K0 = "K0"

    # K1a représente la génération de clé PHY opportuniste.
    # Elle utilise les communications normales déjà présentes.
    K1A = "K1a"

    # K1b représente la génération de clé PHY avec des sondages dédiés.
    K1B = "K1b"

    # K2 représente le renouvellement conventionnel de la clé par ECC.
    K2 = "K2"


# Cette classe représente une décision complète du Decision Maker.
#
# Dans la modélisation, une décision est écrite :
#
# D = (A_j, K_i)
#
# Cela signifie qu'une décision contient :
# - une action d'authentification ;
# - une action de gestion de clé.
class Decision:

    # La fonction __init__ est appelée automatiquement
    # chaque fois que l'on crée une nouvelle décision.
    #
    # Exemple :
    #
    # Decision(AuthenticationAction.A2, KeyAction.K1B)
    #
    # crée la décision A2-K1b.
    def __init__(self, authentication_action, key_action):

        # On enregistre l'action d'authentification
        # dans l'objet Decision actuellement créé.
        self.authentication_action = authentication_action

        # On enregistre l'action de gestion de clé
        # dans le même objet Decision.
        self.key_action = key_action

    # Cette fonction retourne un nom simple et lisible
    # pour la décision.
    #
    # Exemple :
    # AuthenticationAction.A2 + KeyAction.K1B
    # donne le texte "A2-K1b".
    def get_name(self):

        # L'attribut .value permet de récupérer le texte
        # contenu dans l'énumération.
        #
        # Par exemple :
        # AuthenticationAction.A2.value retourne "A2".
        authentication_name = self.authentication_action.value

        # Même principe pour l'action de clé.
        #
        # KeyAction.K1B.value retourne "K1b".
        key_name = self.key_action.value

        # On assemble le nom de l'authentification,
        # un tiret et le nom de l'action de clé.
        #
        # Exemple :
        # "A2" + "-" + "K1b" donne "A2-K1b".
        return authentication_name + "-" + key_name


# Cette fonction construit toutes les décisions possibles
# du modèle.
#
# La modélisation définit :
#
# D = {A1, A2} × {K0, K1a, K1b, K2}
#
# Il y a donc :
#
# 2 actions d'authentification × 4 actions de clé = 8 décisions.
def create_all_decisions():

    # On crée une liste vide.
    # Cette liste recevra progressivement les huit décisions.
    decisions = []

    # Cette première boucle parcourt les deux actions :
    # A1 puis A2.
    for authentication_action in AuthenticationAction:

        # Pour chaque action d'authentification,
        # cette deuxième boucle parcourt :
        # K0, K1a, K1b et K2.
        for key_action in KeyAction:

            # On crée une décision à partir de l'action
            # d'authentification et de l'action de clé
            # actuellement parcourues par les boucles.
            decision = Decision(
                authentication_action,
                key_action
            )

            # La fonction append ajoute la nouvelle décision
            # à la fin de la liste decisions.
            decisions.append(decision)

    # Une fois les deux boucles terminées,
    # la liste contient les huit décisions.
    #
    # On retourne cette liste pour qu'elle puisse être
    # utilisée plus tard par le Decision Maker.
    return decisions


# Cette classe représente le contexte observé
# au moment où le Decision Maker doit choisir une décision.
#
# Dans la modélisation, ce contexte est noté :
#
# c_t
#
# Le contexte contient les informations sur :
# - le canal radio ;
# - la batterie d'Alice ;
# - la criticité du message ;
# - l'état de la clé ;
# - la disponibilité du profil RFF ;
# - le budget de duty-cycle restant.
#
# Cette classe ne réalise aucun calcul.
# Elle sert uniquement à regrouper et transporter
# les informations nécessaires au Decision Maker.
class Context:

    # La fonction __init__ est appelée automatiquement
    # lorsqu'on crée un nouveau contexte.
    #
    # Chaque paramètre reçu correspond à une information
    # utilisée plus tard dans la modélisation.
    def __init__(
        self,
        snr_db,
        doppler_hz,
        battery_energy_j,
        criticality,
        key_age_s,
        messages_with_current_key,
        rff_profile_available,
        renewal_required,
        key_expired,
        compromise_suspected,
        key_deadline_s,
        remaining_duty_cycle_airtime_s,
        k1a_measurements_collected=0,
        k1b_measurements_collected=0,
        candidate_key_ready=False,
        candidate_key_action=None
    ):

        # Avant d'enregistrer les informations,
        # nous vérifions qu'elles respectent les domaines
        # autorisés par la modélisation.

        # La criticité doit uniquement valoir :
        # 0 pour un message normal ;
        # 1 pour un message critique.
        #
        # Si une autre valeur est reçue,
        # le contexte est invalide.
        if criticality != 0 and criticality != 1:

            # ValueError permet d'arrêter la création
            # du contexte et d'expliquer clairement l'erreur.
            raise ValueError(
                "La criticité doit valoir 0 ou 1."
            )

        # L'énergie restante dans la batterie
        # ne peut pas être négative.
        if battery_energy_j < 0:

            # Une valeur négative signifierait que la batterie
            # contient moins de zéro joule, ce qui est impossible.
            raise ValueError(
                "L'énergie de la batterie ne peut pas être négative."
            )

        # L'âge de la clé représente un temps écoulé.
        # Il doit donc être positif ou nul.
        if key_age_s < 0:
            raise ValueError(
                "L'âge de la clé ne peut pas être négatif."
            )

        # Le nombre de messages protégés par la clé
        # est un compteur.
        # Un compteur ne peut pas être négatif.
        if messages_with_current_key < 0:
            raise ValueError(
                "Le nombre de messages ne peut pas être négatif."
            )

        # L'échéance indique le temps restant
        # pour terminer le renouvellement de la clé.
        #
        # Elle doit être strictement supérieure à zéro,
        # car une échéance nulle serait inutilisable
        # dans la normalisation de la latence.
        if key_deadline_s <= 0:
            raise ValueError(
                "L'échéance de la clé doit être supérieure à zéro."
            )

        # Le budget de duty-cycle représente le temps
        # d'antenne encore disponible.
        # Il ne peut donc pas être négatif.
        if remaining_duty_cycle_airtime_s < 0:
            raise ValueError(
                "Le budget de duty-cycle ne peut pas être négatif."
            )

        # k1a_measurements_collected et k1b_measurements_collected
        # représentent le nombre de mesures déjà accumulées
        # pour une clé candidate en préparation.
        #
        # Ce sont des compteurs : ils ne peuvent pas être négatifs.
        if k1a_measurements_collected < 0:
            raise ValueError(
                "k1a_measurements_collected ne peut pas être négatif."
            )

        if k1b_measurements_collected < 0:
            raise ValueError(
                "k1b_measurements_collected ne peut pas être négatif."
            )

        # candidate_key_action ne peut désigner
        # qu'une préparation K1a ou K1b.
        if candidate_key_action is not None and (
            candidate_key_action != KeyAction.K1A
            and candidate_key_action != KeyAction.K1B
        ):
            raise ValueError(
                "candidate_key_action doit être None, "
                "KeyAction.K1A ou KeyAction.K1B."
            )

        if candidate_key_ready and candidate_key_action is None:
            raise ValueError(
                "candidate_key_action doit être défini "
                "lorsque candidate_key_ready est vrai."
            )

        if (
            not candidate_key_ready
            and candidate_key_action is not None
        ):
            raise ValueError(
                "candidate_key_action doit être None "
                "lorsque candidate_key_ready est faux."
            )

        # snr_db représente le rapport signal sur bruit
        # exprimé en décibels.
        #
        # Cette information sera calculée plus tard
        # dans channel.py.
        #
        # Le SNR sera notamment utilisé pour calculer :
        # - la corrélation liée au bruit ;
        # - la FAR de l'authentification RFF ;
        # - la robustesse de l'action A2.
        self.snr_db = snr_db

        # doppler_hz représente la fréquence Doppler
        # exprimée en hertz.
        #
        # Elle dépend principalement :
        # - de la vitesse ;
        # - de la fréquence porteuse ;
        # - de la vitesse de la lumière.
        #
        # Elle sera utilisée dans le modèle de Clarke-Jakes
        # pour calculer la corrélation temporelle du canal.
        self.doppler_hz = doppler_hz

        # battery_energy_j représente l'énergie restante
        # dans la batterie d'Alice.
        #
        # L'unité utilisée est le joule.
        #
        # Cette valeur sera utilisée pour vérifier
        # la contrainte de batterie :
        #
        # E_t(D) <= B_t - B_min
        self.battery_energy_j = battery_energy_j

        # criticality indique si le message est normal
        # ou critique.
        #
        # Nous utilisons :
        # 0 pour un message normal ;
        # 1 pour un message critique.
        #
        # La criticité influencera :
        # - la FAR maximale autorisée ;
        # - le délai maximal autorisé ;
        # - les poids du Decision Maker.
        self.criticality = criticality

        # key_age_s représente l'âge de la clé actuelle.
        #
        # L'unité utilisée est la seconde.
        #
        # Cette valeur sera utilisée pour calculer
        # le taux d'utilisation temporelle de la clé :
        #
        # u_time = min(1, key_age / maximum_key_age)
        self.key_age_s = key_age_s

        # messages_with_current_key représente le nombre
        # de messages déjà protégés avec la clé actuelle.
        #
        # Cette valeur sera utilisée pour calculer :
        #
        # u_msg = min(
        #     1,
        #     messages_with_current_key / maximum_messages
        # )
        self.messages_with_current_key = messages_with_current_key

        # rff_profile_available indique si Bob possède
        # déjà un profil RFF de référence pour Alice.
        #
        # True signifie que le profil est disponible.
        # False signifie qu'il n'est pas disponible.
        #
        # Cette information est nécessaire pour appliquer
        # la règle suivante :
        #
        # A2 sélectionnée
        # implique
        # profil RFF disponible.
        self.rff_profile_available = rff_profile_available

        # renewal_required indique si la clé doit
        # être renouvelée.
        #
        # True signifie qu'un renouvellement est nécessaire.
        # False signifie que la clé peut encore être conservée.
        #
        # Cette valeur correspond à la variable r_t
        # de la modélisation.
        self.renewal_required = renewal_required

        # key_expired indique si la clé a déjà atteint
        # une limite dure.
        #
        # La clé peut être expirée à cause :
        # - de son âge ;
        # - du nombre de messages ;
        # - d'une suspicion de compromission.
        self.key_expired = key_expired

        # compromise_suspected indique si une compromission
        # de la clé est suspectée.
        #
        # True signifie qu'une compromission est signalée.
        # False signifie qu'aucune compromission n'est signalée.
        #
        # Si cette valeur est True, la clé doit être
        # considérée comme expirée.
        self.compromise_suspected = compromise_suspected

        # key_deadline_s représente le temps restant
        # pour terminer le renouvellement de la clé.
        #
        # Cette valeur sera calculée à partir :
        # - du temps restant avant la limite d'âge ;
        # - du temps restant avant la limite de messages.
        #
        # Le Decision Maker devra vérifier :
        #
        # key_latency <= key_deadline
        self.key_deadline_s = key_deadline_s

        # remaining_duty_cycle_airtime_s représente
        # le temps d'antenne encore disponible.
        #
        # Cette valeur est utilisée pour respecter
        # la contrainte de duty-cycle LoRa.
        #
        # Le Decision Maker devra vérifier :
        #
        # decision_airtime <= remaining_duty_cycle_airtime
        self.remaining_duty_cycle_airtime_s = (
            remaining_duty_cycle_airtime_s
        )

        # k1a_measurements_collected représente le nombre
        # de mesures opportunistes déjà accumulées pour
        # une éventuelle clé candidate K1a.
        #
        # Cette valeur permet au Decision Maker de calculer
        # remaining_measurements = max(
        #     required_measurements - collected_measurements,
        #     0
        # )
        # plutôt que d'exiger required_measurements en entier
        # à chaque période.
        self.k1a_measurements_collected = (
            k1a_measurements_collected
        )

        # k1b_measurements_collected représente le nombre
        # de sondages dédiés déjà réalisés pour une
        # éventuelle clé candidate K1b.
        self.k1b_measurements_collected = (
            k1b_measurements_collected
        )

        # candidate_key_ready / candidate_key_action
        # indiquent si une clé candidate (K1a ou K1b) a déjà
        # accumulé toutes les mesures nécessaires.
        #
        # Le Decision Maker les utilise pour ne jamais
        # « refacturer » à une clé candidate déjà prête le
        # coût de la collecte qu'elle a déjà réalisée : voir
        # key_generation.calculate_key_metrics, paramètre
        # candidate_ready.
        self.candidate_key_ready = candidate_key_ready

        self.candidate_key_action = candidate_key_action


# Cette classe sert à conserver les résultats
# produits par le futur fichier channel.py.
#
# Le fichier models.py ne réalise pas les calculs.
# Il définit seulement la manière dont les résultats
# du canal seront regroupés et transmis aux autres fichiers.
#
# Ces informations seront ensuite utilisées par :
#
# authentication.py
#     pour calculer la FAR et la robustesse de A2 ;
#
# key_generation.py
#     pour calculer le KDR et la faisabilité PHY ;
#
# decision_maker.py
#     pour évaluer les différentes décisions.
class ChannelMetrics:

    # La fonction __init__ est appelée automatiquement
    # lorsqu'on crée un nouvel objet ChannelMetrics.
    #
    # Chaque paramètre correspond à un résultat
    # provenant des équations du modèle du canal.
    def __init__(
        self,
        snr_db,
        snr_linear,
        doppler_hz,
        temporal_correlation,
        noise_correlation,
        rho_ab
    ):

        # snr_db représente le rapport signal sur bruit
        # exprimé en décibels.
        #
        # Exemple :
        # snr_db = 5 signifie un SNR de 5 dB.
        #
        # Cette valeur est pratique pour afficher
        # les résultats et construire les graphiques.
        self.snr_db = snr_db

        # snr_linear représente le même SNR,
        # mais sous sa forme linéaire.
        #
        # Les équations utilisent généralement
        # le SNR linéaire et non le SNR en décibels.
        #
        # La conversion sera réalisée plus tard
        # dans channel.py avec la relation :
        #
        # snr_linear = 10 ** (snr_db / 10)
        self.snr_linear = snr_linear

        # doppler_hz représente la fréquence Doppler
        # exprimée en hertz.
        #
        # Elle sera calculée dans channel.py
        # à partir de la vitesse, de la fréquence porteuse
        # et de la vitesse de la lumière.
        #
        # Elle intervient ensuite dans la corrélation
        # temporelle du canal.
        self.doppler_hz = doppler_hz

        # temporal_correlation représente la corrélation
        # temporelle calculée avec le modèle de Clarke-Jakes.
        #
        # Dans notre modélisation, elle correspond à :
        #
        # rho_time = J0(2 * pi * f_d * Delta_t)
        #
        # Cette valeur peut être positive, nulle
        # ou négative.
        self.temporal_correlation = temporal_correlation

        # noise_correlation représente la partie
        # de la corrélation liée au niveau de bruit.
        #
        # Dans notre modélisation :
        #
        # rho_noise = gamma / (1 + gamma)
        #
        # où gamma représente le SNR linéaire.
        #
        # Cette valeur appartient normalement
        # à l'intervalle compris entre 0 et 1.
        self.noise_correlation = noise_correlation

        # rho_ab représente la corrélation finale
        # entre les observations d'Alice et de Bob.
        #
        # Dans notre modélisation :
        #
        # rho_AB =
        #     rho_HW
        #     * rho_time
        #     * rho_noise
        #
        # Cette corrélation sera utilisée principalement
        # pour calculer le KDR dans key_generation.py.
        #
        # Il est important de conserver son signe.
        # Une valeur négative ne doit pas être remplacée
        # automatiquement par zéro ou par sa valeur absolue.
        self.rho_ab = rho_ab


# Cette classe sert à conserver les résultats
# produits plus tard par le fichier authentication.py.
#
# Elle ne réalise aucun calcul d'authentification.
# Elle reçoit seulement les résultats déjà calculés
# et les regroupe dans un même objet.
#
# Ces résultats seront utilisés ensuite par :
#
# energy_latency.py
#     pour calculer les coûts de A1 et A2 ;
#
# decision_maker.py
#     pour vérifier le plancher de FAR
#     et comparer la robustesse des décisions ;
#
# simulation.py
#     pour enregistrer les résultats de chaque période.
class AuthenticationMetrics:

    # Cette fonction est appelée automatiquement
    # lorsque l'on crée un objet AuthenticationMetrics.
    def __init__(
        self,
        authentication_action,
        far,
        frr,
        mac_forgery_probability,
        total_false_acceptance_probability,
        authentication_robustness,
        alice_fallback_probability,
        mallory_fallback_probability
    ):

        # authentication_action indique le mécanisme
        # d'authentification concerné.
        #
        # Sa valeur doit normalement être :
        # - AuthenticationAction.A1 ;
        # - AuthenticationAction.A2.
        #
        # Nous utilisons l'énumération déjà créée
        # au début de models.py.
        self.authentication_action = authentication_action

        # far représente le taux de fausse acceptation.
        #
        # Une fausse acceptation se produit lorsque
        # Mallory est acceptée comme Alice.
        #
        # Pour l'action A2, cette valeur correspond
        # à l'équation AU-EQ33 :
        #
        # FAR(theta, lambda_M)
        #
        # La valeur est comprise entre 0 et 1.
        self.far = far

        # frr représente le taux de faux rejet.
        #
        # Un faux rejet se produit lorsque
        # la véritable Alice est rejetée.
        #
        # Cette valeur correspond à l'équation AU-EQ32 :
        #
        # FRR(theta) = 1 - F_chi2(theta)
        #
        # Elle intervient principalement dans
        # le coût attendu de l'action A2.
        self.frr = frr

        # mac_forgery_probability représente
        # la probabilité idéale de falsifier un tag MAC.
        #
        # Elle correspond à l'équation AU-EQ38 :
        #
        # p_forge = 2 ** (-b_MAC)
        #
        # Pour un tag de 64 bits, cette probabilité
        # est extrêmement faible.
        self.mac_forgery_probability = (
            mac_forgery_probability
        )

        # total_false_acceptance_probability représente
        # la probabilité totale de réussite de Mallory
        # lorsque l'action A2 est utilisée.
        #
        # Cette valeur est différente de la FAR RFF seule.
        #
        # Elle correspond à l'équation AU-EQ40 :
        #
        # P_FA(A2) =
        #     FAR
        #     + (1 - FAR) * p_forge
        #
        # Mallory peut donc réussir :
        # - directement par la RFF ;
        # - ou après rejet RFF, en falsifiant le MAC.
        self.total_false_acceptance_probability = (
            total_false_acceptance_probability
        )

        # authentication_robustness représente
        # la robustesse finale de l'authentification.
        #
        # Elle correspond à l'équation AU-EQ41 :
        #
        # R_auth(A2) = 1 - P_FA(A2)
        #
        # Une valeur proche de 1 signifie
        # une authentification plus robuste.
        self.authentication_robustness = (
            authentication_robustness
        )

        # alice_fallback_probability représente
        # la probabilité que le défi-réponse soit déclenché
        # alors que le message provient réellement d'Alice.
        #
        # Cette probabilité correspond à AU-EQ42 :
        #
        # p_fb(A) = FRR
        #
        # Elle influence l'énergie et la latence
        # réellement consommées par Alice.
        self.alice_fallback_probability = (
            alice_fallback_probability
        )

        # mallory_fallback_probability représente
        # la probabilité que Mallory soit rejetée par la RFF
        # et envoyée vers le défi-réponse.
        #
        # Cette probabilité correspond à AU-EQ43 :
        #
        # p_fb(M) = 1 - FAR
        #
        # Elle sert à analyser la sécurité chez Bob.
        #
        # Elle ne doit jamais être comptée
        # dans l'énergie consommée par Alice.
        self.mallory_fallback_probability = (
            mallory_fallback_probability
        )


# Cette classe sert à conserver les résultats
# produits plus tard par le fichier key_generation.py.
#
# Elle ne calcule pas directement le KDR,
# l'entropie ou le nombre de mesures.
#
# Elle reçoit les résultats calculés par les fonctions
# de key_generation.py et les regroupe dans un objet.
#
# Ces informations seront ensuite utilisées par :
#
# energy_latency.py
#     pour calculer le coût de K0, K1a, K1b et K2 ;
#
# decision_maker.py
#     pour vérifier la faisabilité des actions de clé
#     et comparer leur qualité ;
#
# simulation.py
#     pour enregistrer l'état de la clé pendant la mission.
class KeyMetrics:

    # La fonction __init__ est appelée automatiquement
    # lorsqu'on crée un nouvel objet KeyMetrics.
    def __init__(
        self,
        key_action,
        raw_kdr,
        effective_kdr,
        binary_entropy,
        reconciliation_yield,
        required_measurements,
        agreement_feasible,
        variation_feasible,
        phy_feasible,
        key_aging_index,
        renewal_required,
        key_expired,
        key_deadline_s,
        key_quality,
        collected_measurements=None,
        remaining_measurements=None
    ):

        # key_action indique l'action de gestion
        # de clé concernée par les résultats.
        #
        # Les valeurs autorisées sont :
        # - KeyAction.K0 ;
        # - KeyAction.K1A ;
        # - KeyAction.K1B ;
        # - KeyAction.K2.
        self.key_action = key_action

        # raw_kdr représente le taux brut
        # de désaccord entre les bits d'Alice et Bob.
        #
        # Dans le mode analytique, il correspond
        # à l'équation KM-EQ44 :
        #
        # raw_kdr = arccos(rho_ab) / pi
        #
        # Cette valeur est calculée avant
        # une éventuelle calibration du quantificateur.
        self.raw_kdr = raw_kdr

        # effective_kdr représente le KDR réellement
        # utilisé par le reste du modèle.
        #
        # Dans le mode analytique :
        #
        # effective_kdr = raw_kdr
        #
        # Dans un futur mode calibré, cette valeur
        # pourra provenir d'une courbe expérimentale.
        self.effective_kdr = effective_kdr

        # binary_entropy représente l'entropie binaire
        # calculée à partir du KDR.
        #
        # Elle correspond à KM-EQ49 :
        #
        # h2(p) =
        #     -p * log2(p)
        #     -(1 - p) * log2(1 - p)
        #
        # Cette valeur appartient normalement
        # à l'intervalle compris entre 0 et 1.
        self.binary_entropy = binary_entropy

        # reconciliation_yield représente le rendement
        # approximatif de la réconciliation.
        #
        # Il correspond à KM-EQ50 :
        #
        # y_rec =
        #     eta_keep
        #     * (1 - h2(KDR))
        #
        # Cette valeur indique approximativement
        # combien de bits utiles sont obtenus
        # pour une mesure du canal.
        self.reconciliation_yield = reconciliation_yield

        # required_measurements représente le nombre
        # de mesures nécessaires pour produire
        # une clé de la longueur souhaitée.
        #
        # Il correspond à KM-EQ51 :
        #
        # N_meas =
        #     ceil(
        #         key_length
        #         / max(y_rec, epsilon)
        #     )
        self.required_measurements = required_measurements

        # agreement_feasible indique si Alice et Bob
        # peuvent produire des bits suffisamment proches.
        #
        # Cette valeur correspond à KM-EQ55 :
        #
        # agreement_feasible = True
        # si KDR <= KDR_max.
        self.agreement_feasible = agreement_feasible

        # variation_feasible indique si le canal
        # possède suffisamment de variabilité
        # pour produire de nouveaux bits de clé.
        #
        # Cette partie reste encore à valider
        # scientifiquement dans notre modélisation.
        self.variation_feasible = variation_feasible

        # phy_feasible représente la faisabilité PHY
        # complète de la génération de clé.
        #
        # Elle correspond à KM-EQ56 :
        #
        # phy_feasible =
        #     agreement_feasible
        #     and variation_feasible
        self.phy_feasible = phy_feasible

        # key_aging_index représente le niveau
        # de consommation de la cryptopériode.
        #
        # Il correspond à KM-EQ59 :
        #
        # q_t = max(u_time, u_msg)
        #
        # Une valeur proche de 0 représente
        # une clé encore récente.
        #
        # Une valeur proche de 1 représente
        # une clé proche de son expiration.
        self.key_aging_index = key_aging_index

        # renewal_required indique si le seuil
        # de renouvellement anticipé a été atteint.
        #
        # Cette valeur correspond à KM-EQ60 :
        #
        # renewal_required = True
        # si q_t >= q_trigger.
        self.renewal_required = renewal_required

        # key_expired indique si la clé a atteint
        # une limite dure.
        #
        # Cela peut arriver à cause :
        # - de l'âge maximal ;
        # - du nombre maximal de messages ;
        # - d'une suspicion de compromission.
        #
        # Cette information correspond à KM-EQ61.
        self.key_expired = key_expired

        # key_deadline_s représente le temps restant
        # pour terminer un renouvellement de clé.
        #
        # Cette valeur correspond à KM-EQ64.
        #
        # Elle sera comparée à la latence
        # des actions K1a, K1b et K2.
        self.key_deadline_s = key_deadline_s

        # key_quality représente l'indice de qualité
        # ou de fraîcheur de la clé.
        #
        # Selon l'action, cette valeur provient de :
        #
        # KM-EQ65 pour K0 ;
        # KM-EQ66 pour K1a et K1b ;
        # KM-EQ67 pour K2.
        #
        # Cet indice sera maximisé
        # par le Decision Maker.
        self.key_quality = key_quality

        # collected_measurements représente le nombre
        # de mesures (K1a) ou de sondages (K1b) déjà
        # accumulés pour la clé candidate en préparation.
        #
        # Cette valeur vaut None pour K0 et K2, qui ne
        # possèdent pas de phase d'accumulation.
        self.collected_measurements = (
            collected_measurements
        )

        # remaining_measurements représente le reliquat
        # de mesures encore nécessaires :
        #
        # remaining_measurements = max(
        #     required_measurements
        #     - collected_measurements,
        #     0
        # )
        #
        # Cette valeur est utilisée à la place de
        # required_measurements pour calculer la latence
        # restante de K1a et K1b (energy_latency.py),
        # afin qu'une collecte déjà partiellement réalisée
        # ne recommence pas de zéro à chaque période.
        #
        # Elle vaut None pour K0 et K2.
        self.remaining_measurements = (
            remaining_measurements
        )


# Cette classe regroupe les coûts d'énergie,
# de latence et de temps d'antenne d'une décision.
#
# Elle sera remplie plus tard par energy_latency.py.
#
# Cette classe ne calcule rien.
# Elle sert uniquement à ranger les résultats
# calculés par les fonctions d'énergie et de latence.
class CostMetrics:

    # La fonction __init__ reçoit tous les coûts
    # associés à une décision.
    def __init__(
        self,
        base_energy_j,
        authentication_security_energy_j,
        key_security_energy_j,
        security_energy_j,
        total_energy_j,
        authentication_latency_s,
        prudent_authentication_latency_s,
        key_latency_s,
        normalized_latency,
        airtime_s,
        expected_energy_j,
        worst_case_energy_j
    ):

        # base_energy_j représente l'énergie normale
        # consommée par Alice pendant une période.
        #
        # Elle comprend notamment :
        # - l'acquisition du capteur ;
        # - le traitement applicatif ;
        # - la transmission normale ;
        # - les fenêtres de réception ;
        # - la veille.
        self.base_energy_j = base_energy_j

        # authentication_security_energy_j représente
        # uniquement le surcoût de l'authentification.
        #
        # Exemples :
        # - calcul du MAC pour A1 ;
        # - défi-réponse éventuel pour A2.
        self.authentication_security_energy_j = (
            authentication_security_energy_j
        )

        # key_security_energy_j représente
        # le surcoût de la gestion ou du renouvellement
        # de la clé.
        #
        # Cette valeur dépendra de K0, K1a, K1b ou K2.
        self.key_security_energy_j = key_security_energy_j

        # security_energy_j représente la somme
        # des deux surcoûts de sécurité :
        #
        # security_energy =
        #     authentication_security_energy
        #     + key_security_energy
        self.security_energy_j = security_energy_j

        # total_energy_j représente l'énergie totale
        # de la décision :
        #
        # total_energy =
        #     base_energy
        #     + security_energy
        #
        # Cette valeur sera utilisée dans la contrainte :
        #
        # E_t(D) <= B_t - B_min
        self.total_energy_j = total_energy_j

        # authentication_latency_s représente
        # la latence moyenne ou attendue
        # de l'authentification.
        self.authentication_latency_s = (
            authentication_latency_s
        )

        # prudent_authentication_latency_s représente
        # la latence prudente utilisée pour vérifier
        # la contrainte de délai.
        #
        # Pour A2, elle doit prendre en compte
        # le pire cas avec défi-réponse.
        self.prudent_authentication_latency_s = (
            prudent_authentication_latency_s
        )

        # key_latency_s représente le temps nécessaire
        # pour produire ou renouveler la clé.
        self.key_latency_s = key_latency_s

        # normalized_latency représente l'objectif
        # temporel normalisé :
        #
        # normalized_latency =
        #     max(
        #         authentication_latency / authentication_budget,
        #         key_latency / key_deadline
        #     )
        #
        # Une valeur inférieure ou égale à 1 signifie
        # que les deux budgets sont respectés.
        self.normalized_latency = normalized_latency

        # airtime_s représente le temps d'antenne
        # consommé par la décision.
        #
        # Cette valeur sera utilisée pour vérifier
        # la contrainte de duty-cycle LoRa.
        self.airtime_s = airtime_s

        # expected_energy_j représente l'énergie moyenne
        # attendue lorsque certaines actions dépendent
        # d'une probabilité.
        #
        # Exemple :
        # le défi-réponse de A2 dépend de la FRR.
        self.expected_energy_j = expected_energy_j

        # worst_case_energy_j représente l'énergie
        # consommée dans le pire cas.
        #
        # Elle sera utile pour vérifier les contraintes
        # de manière prudente.
        self.worst_case_energy_j = worst_case_energy_j


# Cette classe décrit pourquoi une décision
# a été rejetée par le Decision Maker.
#
# Elle permet de conserver une explication claire
# pour les journaux, les tableaux et le rapport final.
class RejectionRecord:

    def __init__(
        self,
        decision,
        stage,
        reason_code,
        explanation,
        measured_value=None,
        allowed_value=None
    ):

        # decision représente la décision rejetée.
        #
        # Exemple :
        # A2-K1b
        self.decision = decision

        # stage indique à quelle étape
        # la décision a été rejetée.
        #
        # Exemples :
        # "reasoning"
        # "physical"
        # "resource"
        # "security"
        self.stage = stage

        # reason_code est un code court
        # qui facilite l'enregistrement dans les fichiers.
        #
        # Exemple :
        # "FAR_TOO_HIGH"
        self.reason_code = reason_code

        # explanation contient une phrase claire
        # destinée à expliquer le rejet.
        self.explanation = explanation

        # measured_value représente la valeur
        # réellement calculée.
        #
        # Exemple :
        # FAR = 0.08
        #
        # Cette valeur est facultative.
        self.measured_value = measured_value

        # allowed_value représente la limite autorisée.
        #
        # Exemple :
        # FAR_max = 0.05
        #
        # Cette valeur est également facultative.
        self.allowed_value = allowed_value


# Cette classe regroupe toute l'évaluation
# d'une seule décision candidate.
#
# Le Decision Maker créera un objet
# DecisionEvaluation pour chacune des huit décisions.
class DecisionEvaluation:

    def __init__(self, decision):

        # decision représente la décision évaluée.
        self.decision = decision

        # authentication_metrics recevra plus tard
        # un objet AuthenticationMetrics.
        #
        # Au moment de la création, aucune mesure
        # n'a encore été calculée.
        self.authentication_metrics = None

        # key_metrics recevra plus tard
        # un objet KeyMetrics.
        self.key_metrics = None

        # cost_metrics recevra plus tard
        # un objet CostMetrics.
        self.cost_metrics = None

        # objective_vector recevra les quatre objectifs :
        #
        # [
        #     énergie,
        #     latence,
        #     -robustesse,
        #     -qualité de clé
        # ]
        self.objective_vector = None

        # reasoning_rules_ok indique si les règles
        # logiques sont respectées.
        #
        # Exemple :
        # A2 exige un profil RFF disponible.
        self.reasoning_rules_ok = False

        # resource_constraints_ok indique si les contraintes
        # de batterie, de délai, d'échéance
        # et de duty-cycle sont respectées.
        self.resource_constraints_ok = False

        # security_constraint_ok indique si le plancher
        # de FAR est respecté.
        self.security_constraint_ok = False

        # admissible indique si la décision
        # respecte toutes les règles et contraintes.
        #
        # Elle reste False tant que les vérifications
        # ne sont pas terminées.
        self.admissible = False

        # rejection_reasons est une liste
        # contenant tous les motifs de rejet.
        #
        # On crée une nouvelle liste pour chaque objet.
        self.rejection_reasons = []

        # pareto_optimal indique si la décision
        # appartient au front de Pareto.
        self.pareto_optimal = False

        # tchebycheff_score recevra plus tard
        # le score d'arbitrage final.
        self.tchebycheff_score = None

    # Cette fonction ajoute un motif de rejet
    # à la décision.
    def add_rejection(self, rejection_record):

        # append ajoute le nouveau motif
        # à la fin de la liste.
        self.rejection_reasons.append(
            rejection_record
        )

        # Une décision qui possède un motif de rejet
        # ne peut pas rester admissible.
        self.admissible = False


# Cette classe représente le résultat complet
# retourné par le Decision Maker pour un contexte.
class DecisionMakerResult:

    def __init__(
        self,
        context,
        all_evaluations,
        admissible_evaluations,
        pareto_front,
        rejection_journal,
        contextual_weights,
        ideal_point,
        nadir_point,
        selected_evaluation,
        refusal_of_service,
        fallback_mode_used,
        explanation
    ):

        # context représente les informations observées
        # au moment de la décision.
        self.context = context

        # all_evaluations contient les évaluations
        # des huit décisions.
        self.all_evaluations = all_evaluations

        # admissible_evaluations contient seulement
        # les décisions qui respectent toutes
        # les règles et contraintes.
        self.admissible_evaluations = (
            admissible_evaluations
        )

        # pareto_front contient les décisions
        # admissibles qui ne sont dominées
        # par aucune autre décision admissible.
        self.pareto_front = pareto_front

        # rejection_journal contient tous les motifs
        # de rejet produits pendant l'évaluation.
        self.rejection_journal = rejection_journal

        # contextual_weights contient les quatre poids :
        #
        # [
        #     poids énergie,
        #     poids latence,
        #     poids authentification,
        #     poids clé
        # ]
        self.contextual_weights = contextual_weights

        # ideal_point contient la meilleure valeur
        # obtenue pour chaque objectif.
        self.ideal_point = ideal_point

        # nadir_point contient la plus mauvaise valeur
        # du front pour chaque objectif.
        self.nadir_point = nadir_point

        # selected_evaluation représente la décision
        # finalement choisie.
        #
        # Cette valeur peut être None si aucune décision
        # n'est admissible.
        self.selected_evaluation = selected_evaluation

        # refusal_of_service vaut True
        # lorsqu'aucune décision normale
        # n'est admissible.
        self.refusal_of_service = refusal_of_service

        # fallback_mode_used indique le mode de secours
        # éventuellement utilisé.
        #
        # Cette valeur peut rester None.
        self.fallback_mode_used = fallback_mode_used

        # explanation contient une phrase
        # expliquant le choix final ou le refus.
        self.explanation = explanation


# Cette classe représente l'état de la mission
# à un instant donné.
#
# Contrairement à Context, MissionState représente
# l'état interne qui évolue après chaque période.
class MissionState:

    def __init__(
        self,
        step_index,
        time_s,
        battery_energy_j,
        key_age_s,
        messages_with_current_key,
        current_key_identifier,
        remaining_duty_cycle_airtime_s,
        legitimate_messages=0,
        served_messages=0,
        legitimate_refusals=0,
        mallory_attempts=0,
        false_acceptances=0,
        critical_mallory_attempts=0,
        critical_false_acceptances=0,
        security_floor_violations=0,
        k1a_measurements_collected=0,
        k1b_measurements_collected=0,
        candidate_key_ready=False,
        candidate_key_action=None,
        k1b_time_since_last_probe_s=0.0,
        recent_rho_ab_window=()
    ):

        # L'indice de période ne peut pas être négatif.
        if step_index < 0:
            raise ValueError(
                "L'indice de période ne peut pas être négatif."
            )

        # Le temps écoulé ne peut pas être négatif.
        if time_s < 0:
            raise ValueError(
                "Le temps de mission ne peut pas être négatif."
            )

        # La batterie ne peut pas contenir
        # une énergie négative.
        if battery_energy_j < 0:
            raise ValueError(
                "L'énergie de mission ne peut pas être négative."
            )

        # L'âge de la clé ne peut pas être négatif.
        if key_age_s < 0:
            raise ValueError(
                "L'âge de clé ne peut pas être négatif."
            )

        # Le compteur de messages ne peut pas être négatif.
        if messages_with_current_key < 0:
            raise ValueError(
                "Le compteur de messages ne peut pas être négatif."
            )

        # Le budget de duty-cycle ne peut pas être négatif.
        if remaining_duty_cycle_airtime_s < 0:
            raise ValueError(
                "Le budget de duty-cycle ne peut pas être négatif."
            )

        # Les compteurs de préparation K1a/K1b sont des
        # nombres entiers de mesures ou de sondages.
        # Ils ne peuvent pas être négatifs.
        if not isinstance(k1a_measurements_collected, int):
            raise ValueError(
                "k1a_measurements_collected doit être un entier."
            )

        if k1a_measurements_collected < 0:
            raise ValueError(
                "k1a_measurements_collected ne peut pas "
                "être négatif."
            )

        if not isinstance(k1b_measurements_collected, int):
            raise ValueError(
                "k1b_measurements_collected doit être un entier."
            )

        if k1b_measurements_collected < 0:
            raise ValueError(
                "k1b_measurements_collected ne peut pas "
                "être négatif."
            )

        # candidate_key_ready doit être un booléen strict.
        if not isinstance(candidate_key_ready, bool):
            raise ValueError(
                "candidate_key_ready doit être un booléen."
            )

        # candidate_key_action ne peut désigner
        # qu'une préparation K1a ou K1b : K0 et K2 ne
        # possèdent pas de phase de préparation.
        if candidate_key_action is not None and (
            candidate_key_action != KeyAction.K1A
            and candidate_key_action != KeyAction.K1B
        ):
            raise ValueError(
                "candidate_key_action doit être None, "
                "KeyAction.K1A ou KeyAction.K1B."
            )

        # Une clé candidate prête doit désigner l'action
        # qui l'a préparée ; à l'inverse, tant qu'aucune
        # clé candidate n'est prête, aucune action ne doit
        # être verrouillée.
        if candidate_key_ready and candidate_key_action is None:
            raise ValueError(
                "candidate_key_action doit être défini "
                "lorsque candidate_key_ready est vrai."
            )

        if (
            not candidate_key_ready
            and candidate_key_action is not None
        ):
            raise ValueError(
                "candidate_key_action doit être None "
                "lorsque candidate_key_ready est faux."
            )

        # Le temps écoulé depuis le dernier sondage K1b
        # ne peut pas être négatif.
        if k1b_time_since_last_probe_s < 0:
            raise ValueError(
                "k1b_time_since_last_probe_s ne peut pas "
                "être négatif."
            )

        # recent_rho_ab_window est la fenêtre glissante des
        # dernières corrélations Alice-Bob observées,
        # utilisée pour calculer réellement phi_var (voir
        # channel.calculate_temporal_variability_feasible).
        for rho_ab_value in recent_rho_ab_window:
            if rho_ab_value < -1 or rho_ab_value > 1:
                raise ValueError(
                    "recent_rho_ab_window ne doit contenir "
                    "que des corrélations dans [-1, 1]."
                )

        # Numéro de la période courante.
        self.step_index = step_index

        # Temps total écoulé depuis le début
        # de la mission.
        self.time_s = time_s

        # Énergie restante dans la batterie d'Alice.
        self.battery_energy_j = battery_energy_j

        # Âge de la clé courante.
        self.key_age_s = key_age_s

        # Nombre de messages déjà protégés
        # avec la clé courante.
        self.messages_with_current_key = (
            messages_with_current_key
        )

        # Nom ou numéro de la clé actuelle.
        #
        # Exemple :
        # "KEY-001"
        self.current_key_identifier = (
            current_key_identifier
        )

        # Temps d'antenne encore disponible.
        self.remaining_duty_cycle_airtime_s = (
            remaining_duty_cycle_airtime_s
        )

        # Nombre total de messages légitimes produits.
        self.legitimate_messages = legitimate_messages

        # Nombre de messages légitimes réellement servis.
        self.served_messages = served_messages

        # Nombre de messages légitimes refusés.
        self.legitimate_refusals = legitimate_refusals

        # Nombre total de tentatives de Mallory.
        self.mallory_attempts = mallory_attempts

        # Nombre total de fausses acceptations.
        self.false_acceptances = false_acceptances

        # Nombre de tentatives de Mallory
        # pendant des périodes critiques.
        self.critical_mallory_attempts = (
            critical_mallory_attempts
        )

        # Nombre de fausses acceptations
        # pendant des périodes critiques.
        self.critical_false_acceptances = (
            critical_false_acceptances
        )

        # Nombre de violations du plancher de sécurité
        # observées au SNR réel.
        self.security_floor_violations = (
            security_floor_violations
        )

        # k1a_measurements_collected représente le nombre
        # de mesures opportunistes déjà accumulées pour
        # une clé candidate K1a en préparation.
        #
        # Cette valeur est remise à zéro après l'activation
        # d'une nouvelle clé.
        self.k1a_measurements_collected = (
            k1a_measurements_collected
        )

        # k1b_measurements_collected représente le nombre
        # de sondages dédiés déjà réalisés pour une clé
        # candidate K1b en préparation.
        self.k1b_measurements_collected = (
            k1b_measurements_collected
        )

        # candidate_key_ready indique qu'une clé candidate
        # (K1a ou K1b) a accumulé suffisamment de mesures
        # et peut être activée dès que le renouvellement
        # est requis (renewal_required=True).
        self.candidate_key_ready = candidate_key_ready

        # candidate_key_action indique quelle action
        # (KeyAction.K1A ou KeyAction.K1B) a préparé la
        # clé candidate actuellement en cours ou prête.
        #
        # Vaut None tant qu'aucune préparation n'a atteint
        # son terme.
        self.candidate_key_action = candidate_key_action

        # k1b_time_since_last_probe_s représente le temps
        # écoulé depuis le dernier sondage dédié K1b.
        #
        # Un nouveau sondage n'est planifié que lorsque
        # cette valeur atteint dedicated_probe_interval_s,
        # afin de respecter le rythme soutenable dérivé du
        # duty-cycle (voir
        # results/three_scenarios_explicit_analysis/
        # k1a_k1b_model_consistency_audit.md, section 6).
        self.k1b_time_since_last_probe_s = (
            k1b_time_since_last_probe_s
        )

        # recent_rho_ab_window : fenêtre glissante des
        # dernières corrélations Alice-Bob observées.
        #
        # Stockée en tuple (immuable) pour éviter qu'un
        # appelant modifie silencieusement l'historique
        # d'un autre état de mission.
        self.recent_rho_ab_window = tuple(
            recent_rho_ab_window
        )


# Cette classe regroupe le résultat
# d'une seule période de mission.
class MissionStepResult:

    def __init__(
        self,
        state_before,
        context,
        channel_metrics,
        decision_maker_result,
        legitimate_message_served,
        mallory_attempted,
        mallory_accepted,
        energy_debited_from_alice_j,
        state_after,
        k1a_measurements_before=None,
        k1a_measurements_after=None,
        k1b_measurements_before=None,
        k1b_measurements_after=None,
        candidate_key_ready_before=None,
        candidate_key_ready_after=None,
        candidate_key_action=None,
        eve_validation=None
    ):

        # L'énergie débitée de la batterie d'Alice
        # ne peut pas être négative.
        if energy_debited_from_alice_j < 0:
            raise ValueError(
                "L'énergie débitée ne peut pas être négative."
            )

        # État de la mission avant la décision.
        self.state_before = state_before

        # Contexte présenté au Decision Maker.
        self.context = context

        # Résultats du canal pendant cette période.
        self.channel_metrics = channel_metrics

        # Résultat complet du Decision Maker.
        self.decision_maker_result = (
            decision_maker_result
        )

        # Indique si le message légitime
        # a réellement été servi.
        self.legitimate_message_served = (
            legitimate_message_served
        )

        # Indique si Mallory a tenté une attaque.
        self.mallory_attempted = mallory_attempted

        # Indique si Mallory a été acceptée.
        self.mallory_accepted = mallory_accepted

        # Énergie réellement retirée
        # de la batterie d'Alice.
        #
        # Une tentative de Mallory ne doit jamais
        # ajouter directement une énergie à cette valeur.
        self.energy_debited_from_alice_j = (
            energy_debited_from_alice_j
        )

        # État de la mission après la période.
        self.state_after = state_after

        # Ces sept champs exposent explicitement
        # la progression de la préparation K1a/K1b
        # pendant cette période, afin de pouvoir la
        # tracer sans devoir relire state_before/state_after.
        #
        # Ils sont redondants avec state_before/state_after
        # (qui contiennent déjà ces compteurs) mais
        # facilitent l'export direct en CSV.
        self.k1a_measurements_before = (
            k1a_measurements_before
        )

        self.k1a_measurements_after = (
            k1a_measurements_after
        )

        self.k1b_measurements_before = (
            k1b_measurements_before
        )

        self.k1b_measurements_after = (
            k1b_measurements_after
        )

        self.candidate_key_ready_before = (
            candidate_key_ready_before
        )

        self.candidate_key_ready_after = (
            candidate_key_ready_after
        )

        # candidate_key_action reflète l'action
        # (K1A ou K1B) associée à la clé candidate en
        # préparation ou prête à la fin de cette période.
        self.candidate_key_action = (
            candidate_key_action
        )

        # eve_validation contient le résultat de
        # physec_dm.eve_validation.evaluate_eve_secrecy_for_period
        # (rho_ae, kdr_ab, kdr_eve, secrecy_margin, secure)
        # UNIQUEMENT lorsqu'une clé K1a/K1b vient d'être
        # activée pendant cette période ; None sinon. Ce
        # champ est un résultat de VALIDATION a posteriori :
        # il n'a jamais été utilisé par le Decision Maker
        # pour choisir cette décision.
        self.eve_validation = eve_validation


# Cette classe représente le résultat complet
# d'une mission pour une politique et une graine.
class MissionResult:

    def __init__(
        self,
        parameters_snapshot,
        seed,
        policy_id,
        steps,
        lifetime_s,
        mean_energy_per_generated_message_j,
        mean_energy_per_served_message_j,
        false_acceptance_rate,
        critical_false_acceptance_rate,
        legitimate_refusal_rate,
        security_floor_violation_rate,
        decision_counts,
        final_state,
        stop_reason,
        censored=False
    ):

        # parameters_snapshot contient une copie
        # des paramètres utilisés pendant la mission.
        self.parameters_snapshot = parameters_snapshot

        # seed est la graine utilisée
        # par le générateur aléatoire.
        self.seed = seed

        # policy_id est le nom de la politique évaluée.
        #
        # Exemples :
        # "P0"
        # "B1"
        # "B2"
        self.policy_id = policy_id

        # steps contient la liste des résultats
        # de toutes les périodes.
        self.steps = steps

        # lifetime_s représente la durée de vie
        # de la mission en secondes.
        self.lifetime_s = lifetime_s

        # Énergie moyenne divisée par le nombre
        # de messages légitimes produits.
        self.mean_energy_per_generated_message_j = (
            mean_energy_per_generated_message_j
        )

        # Énergie moyenne divisée par le nombre
        # de messages réellement servis.
        self.mean_energy_per_served_message_j = (
            mean_energy_per_served_message_j
        )

        # FAR empirique globale.
        self.false_acceptance_rate = (
            false_acceptance_rate
        )

        # FAR empirique calculée uniquement
        # pour les périodes critiques.
        self.critical_false_acceptance_rate = (
            critical_false_acceptance_rate
        )

        # Taux de refus des messages légitimes.
        self.legitimate_refusal_rate = (
            legitimate_refusal_rate
        )

        # Taux de violation du plancher de sécurité.
        self.security_floor_violation_rate = (
            security_floor_violation_rate
        )

        # decision_counts indique combien de fois
        # chaque décision a été sélectionnée.
        #
        # Exemple :
        # {
        #     "A1-K0": 100,
        #     "A2-K1a": 20
        # }
        self.decision_counts = decision_counts

        # Dernier état de la mission.
        self.final_state = final_state

        # Motif de l'arrêt.
        #
        # Exemples :
        # "battery_reserve_reached"
        # "maximum_steps"
        self.stop_reason = stop_reason

        # censored indique si la mission
        # a été arrêtée avant d'observer
        # l'épuisement réel de la batterie.
        self.censored = censored


# Cette classe regroupe les résultats
# d'une campagne complète de simulation.
#
# Une campagne peut contenir plusieurs scénarios,
# plusieurs politiques et plusieurs graines.
class CampaignResult:

    def __init__(
        self,
        campaign_id,
        scenario_ids,
        policy_ids,
        seeds,
        mission_results,
        output_directory
    ):

        # Identifiant de la campagne.
        #
        # Exemple :
        # "CAMP-05"
        self.campaign_id = campaign_id

        # Liste des scénarios évalués.
        self.scenario_ids = scenario_ids

        # Liste des politiques comparées.
        self.policy_ids = policy_ids

        # Liste des graines utilisées.
        self.seeds = seeds

        # Liste de tous les résultats de mission.
        self.mission_results = mission_results

        # Dossier dans lequel les résultats,
        # tableaux et figures seront enregistrés.
        self.output_directory = output_directory

