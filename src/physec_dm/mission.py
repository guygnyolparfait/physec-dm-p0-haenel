# On importe NumPy pour créer un seul générateur aléatoire
# reproductible pendant toute la mission.
import numpy as np


# On importe les structures simples déjà définies dans models.py.
#
# AuthenticationAction et KeyAction permettent de reconnaître
# les mécanismes choisis par le Decision Maker.
#
# Context représente les informations présentées au Decision Maker.
#
# MissionState représente l'état évolutif de la mission.
#
# MissionStepResult conserve le résultat d'une période.
#
# MissionResult conserve le résultat complet de la mission.
from physec_dm.models import (
    AuthenticationAction,
    Context,
    KeyAction,
    MissionResult,
    MissionState,
    MissionStepResult
)


# calculate_channel_metrics calcule le canal observé
# pendant une période.
from physec_dm.channel import (
    calculate_channel_metrics,
    calculate_temporal_variability_feasible
)


# calculate_authentication_metrics permet d'évaluer
# l'action sélectionnée au SNR réel.
from physec_dm.authentication import (
    calculate_authentication_metrics
)


# calculate_key_metrics calcule l'état de vieillissement,
# le besoin de renouvellement, l'expiration
# et l'échéance de la clé.
from physec_dm.key_generation import (
    calculate_key_metrics
)


# evaluate_eve_secrecy_for_period calcule, après coup, la
# marge de secret d'une clé K1a/K1b face à Ève — jamais
# utilisée par le Decision Maker ni par create_mission_context.
from physec_dm.eve_validation import (
    evaluate_eve_secrecy_for_period
)


# Ces fonctions permettent de calculer les coûts réellement engagés.
#
# calculate_base_energy
#     calcule l'énergie normale d'une période ;
#
# calculate_authentication_costs
#     calcule les coûts de A1 ou A2 ;
#
# calculate_key_costs
#     calcule les coûts de K0, K1a, K1b ou K2 ;
#
# calculate_probe_energy / calculate_time_on_air
#     calculent le coût d'UN SEUL sondage K1b, pour le
#     sondage indépendant planifié progressivement
#     (voir section 7bis de run_mission_step).
from physec_dm.energy_latency import (
    calculate_authentication_costs,
    calculate_base_energy,
    calculate_key_costs,
    calculate_probe_energy,
    calculate_time_on_air
)


# run_decision_maker évalue les huit décisions
# et sélectionne une décision admissible.
from physec_dm.decision_maker import (
    run_decision_maker
)


# ================================================================
# 1. OUTILS ALÉATOIRES
# ================================================================


# Cette fonction vérifie qu'une probabilité
# appartient à l'intervalle [0, 1].
def validate_probability(
    probability,
    parameter_name
):

    if probability is None:

        raise ValueError(
            parameter_name
            + " doit être défini."
        )

    if probability < 0 or probability > 1:

        raise ValueError(
            parameter_name
            + " doit appartenir à [0, 1]."
        )

    return float(probability)


# Cette fonction crée le générateur aléatoire unique
# utilisé pendant toute une répétition.
#
# Le protocole interdit de réinitialiser la graine
# dans plusieurs fonctions.
def create_random_generator(
    seed
):

    return np.random.default_rng(
        seed
    )


# Cette fonction réalise un tirage de Bernoulli.
#
# Elle retourne True avec la probabilité fournie.
def draw_bernoulli(
    probability,
    random_generator
):

    probability = validate_probability(
        probability,
        "La probabilité"
    )

    random_value = random_generator.random()

    return random_value < probability


# Cette fonction génère le SNR observé
# dans le mode de scénario imposé.
#
# Le SNR suit ici une loi normale :
#
# Gamma_t ~ N(mean_snr_db, shadowing_std_db²)
#
# Le choix de la moyenne et de l'écart-type
# appartient au scénario.
def draw_observed_snr_db(
    parameters,
    random_generator
):

    if parameters.mean_snr_db is None:

        raise ValueError(
            "mean_snr_db doit être défini."
        )

    if parameters.shadowing_std_db is None:

        raise ValueError(
            "shadowing_std_db doit être défini."
        )

    if parameters.shadowing_std_db < 0:

        raise ValueError(
            "shadowing_std_db ne peut pas être négatif."
        )

    observed_snr_db = random_generator.normal(
        loc=parameters.mean_snr_db,
        scale=parameters.shadowing_std_db
    )

    return float(
        observed_snr_db
    )


# ================================================================
# 2. ÉTAT INITIAL ET CONTEXTE
# ================================================================


# Cette fonction crée l'état initial de la mission.
def create_initial_mission_state(
    parameters,
    initial_duty_cycle_airtime_s,
    current_key_identifier="KEY-001"
):

    if initial_duty_cycle_airtime_s < 0:

        raise ValueError(
            "Le budget initial de duty-cycle "
            "ne peut pas être négatif."
        )

    return MissionState(
        step_index=0,
        time_s=0.0,
        battery_energy_j=(
            parameters.initial_battery_energy_j
        ),
        key_age_s=0.0,
        messages_with_current_key=0,
        current_key_identifier=(
            current_key_identifier
        ),
        remaining_duty_cycle_airtime_s=(
            initial_duty_cycle_airtime_s
        )
    )


# Cette fonction calcule l'état actuel de la clé.
#
# Nous appelons K0 uniquement pour obtenir :
# - l'indice de vieillissement ;
# - l'expiration ;
# - le besoin de renouvellement ;
# - l'échéance.
#
# Cela ne signifie pas que K0 sera sélectionnée.
def calculate_key_context_metrics(
    state,
    parameters,
    compromise_suspected
):

    key_metrics = calculate_key_metrics(
        key_action=KeyAction.K0,
        parameters=parameters,
        key_age_s=state.key_age_s,
        messages_with_current_key=(
            state.messages_with_current_key
        ),
        compromise_suspected=(
            compromise_suspected
        )
    )

    return key_metrics


# Cette fonction construit le contexte présenté
# au Decision Maker pendant une période.
def create_mission_context(
    state,
    channel_metrics,
    criticality,
    rff_profile_available,
    compromise_suspected,
    key_context_metrics
):

    # Une clé expirée ou compromise impose un renouvellement,
    # même lorsque le seuil anticipé n'a pas encore été atteint.
    renewal_required = (
        key_context_metrics.renewal_required
        or key_context_metrics.key_expired
    )

    return Context(
        snr_db=channel_metrics.snr_db,
        doppler_hz=channel_metrics.doppler_hz,
        battery_energy_j=state.battery_energy_j,
        criticality=criticality,
        key_age_s=state.key_age_s,
        messages_with_current_key=(
            state.messages_with_current_key
        ),
        rff_profile_available=(
            rff_profile_available
        ),
        renewal_required=renewal_required,
        key_expired=key_context_metrics.key_expired,
        compromise_suspected=(
            compromise_suspected
        ),
        key_deadline_s=(
            key_context_metrics.key_deadline_s
        ),
        remaining_duty_cycle_airtime_s=(
            state.remaining_duty_cycle_airtime_s
        ),
        k1a_measurements_collected=(
            state.k1a_measurements_collected
        ),
        k1b_measurements_collected=(
            state.k1b_measurements_collected
        ),
        candidate_key_ready=(
            state.candidate_key_ready
        ),
        candidate_key_action=(
            state.candidate_key_action
        )
    )


# Cette fonction recherche, parmi toutes les évaluations
# calculées par le Decision Maker pendant cette période,
# celle qui correspond à une action de clé donnée.
#
# Elle permet d'observer la faisabilité PHY et le nombre
# de mesures requises pour K1a ou K1b MÊME LORSQUE cette
# action n'a pas été sélectionnée — nécessaire car K1a
# accumule ses mesures de façon opportuniste, indépendamment
# de la décision réellement choisie.
#
# Retourne None si aucune évaluation correspondante
# n'a atteint le calcul des métriques de clé (par exemple
# si elle a été rejetée dès les règles logiques).
def find_key_metrics_for_action(
    all_evaluations,
    key_action
):

    for evaluation in all_evaluations:

        if (
            evaluation.decision.key_action == key_action
            and evaluation.key_metrics is not None
        ):

            return evaluation.key_metrics

    return None


# ================================================================
# 3. COÛTS RÉELLEMENT ENGAGÉS PAR ALICE
# ================================================================


# Cette fonction calcule l'énergie et le temps d'antenne
# réellement engagés par Alice.
#
# Pour A1, le coût est déterministe.
#
# Pour A2, le défi-réponse est tiré avec la probabilité FRR.
#
# Important :
# seule la FRR d'Alice peut déclencher un coût supplémentaire
# dans la batterie d'Alice.
#
# Le repli de Mallory ne débite jamais Alice.
def calculate_realized_alice_costs(
    selected_evaluation,
    parameters,
    random_generator,
    k2_protocol=None
):

    if selected_evaluation is None:

        return {
            "energy_j": 0.0,
            "airtime_s": 0.0,
            "alice_fallback_triggered": False
        }

    decision = selected_evaluation.decision

    authentication_metrics = (
        selected_evaluation.authentication_metrics
    )

    key_metrics = (
        selected_evaluation.key_metrics
    )

    if (
        authentication_metrics is None
        or key_metrics is None
    ):

        raise ValueError(
            "Les métriques de la décision sélectionnée "
            "doivent être disponibles."
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

    alice_fallback_triggered = False

    # A1 possède un coût déterministe.
    if (
        decision.authentication_action
        == AuthenticationAction.A1
    ):

        authentication_energy_j = (
            authentication_costs[
                "expected_energy_j"
            ]
        )

        authentication_airtime_s = (
            authentication_costs[
                "worst_case_airtime_s"
            ]
        )

    # A2 ne débite le défi-réponse
    # que lorsque la véritable Alice est rejetée par la RFF.
    elif (
        decision.authentication_action
        == AuthenticationAction.A2
    ):

        alice_fallback_triggered = draw_bernoulli(
            authentication_metrics.frr,
            random_generator
        )

        if alice_fallback_triggered:

            authentication_energy_j = (
                authentication_costs[
                    "worst_case_energy_j"
                ]
            )

            authentication_airtime_s = (
                authentication_costs[
                    "worst_case_airtime_s"
                ]
            )

        else:

            # Le traitement RFF est réalisé chez Bob.
            #
            # Aucun coût radio ou cryptographique supplémentaire
            # n'est donc débité à Alice dans ce cas.
            authentication_energy_j = 0.0
            authentication_airtime_s = 0.0

    else:

        raise ValueError(
            "L'action d'authentification "
            "doit être A1 ou A2."
        )

    realized_energy_j = (
        base_energy_j
        + authentication_energy_j
        + key_costs["energy_j"]
    )

    realized_airtime_s = (
        authentication_airtime_s
        + key_costs["airtime_s"]
    )

    return {
        "energy_j": realized_energy_j,
        "airtime_s": realized_airtime_s,
        "alice_fallback_triggered": (
            alice_fallback_triggered
        )
    }


# ================================================================
# 4. PROCESSUS DE MALLORY
# ================================================================


# Cette fonction évalue l'action sélectionnée
# au SNR réel de Mallory.
#
# La probabilité de succès utilise
# la fausse acceptation complète du mécanisme :
#
# - A1 : forge du MAC ;
# - A2 : acceptation RFF ou forge après rejet RFF.
def evaluate_mallory(
    selected_evaluation,
    real_snr_db,
    parameters,
    random_generator,
    mallory_attempted
):

    if not mallory_attempted:

        return {
            "accepted": False,
            "authentication_metrics": None
        }

    # Si aucune décision n'a été sélectionnée,
    # le service est refusé et Mallory ne peut pas être acceptée.
    if selected_evaluation is None:

        return {
            "accepted": False,
            "authentication_metrics": None
        }

    authentication_action = (
        selected_evaluation.decision.authentication_action
    )

    real_authentication_metrics = (
        calculate_authentication_metrics(
            authentication_action=(
                authentication_action
            ),
            parameters=parameters,
            mallory_snr_db=real_snr_db
        )
    )

    success_probability = (
        real_authentication_metrics
        .total_false_acceptance_probability
    )

    accepted = draw_bernoulli(
        success_probability,
        random_generator
    )

    return {
        "accepted": accepted,
        "authentication_metrics": (
            real_authentication_metrics
        )
    }


# ================================================================
# 5. MISE À JOUR DE LA CLÉ ET DU DUTY-CYCLE
# ================================================================


# Cette fonction produit l'identifiant de la clé suivante.
#
# Exemple :
#
# KEY-001 devient KEY-002.
def create_next_key_identifier(
    current_key_identifier
):

    prefix = "KEY-"

    if current_key_identifier.startswith(
        prefix
    ):

        number_text = current_key_identifier[
            len(prefix):
        ]

        if number_text.isdigit():

            next_number = int(
                number_text
            ) + 1

            return (
                prefix
                + str(next_number).zfill(
                    len(number_text)
                )
            )

    # Pour un identifiant libre,
    # on ajoute simplement un suffixe lisible.
    return (
        current_key_identifier
        + "-NEXT"
    )


# Cette fonction met à jour l'âge,
# le compteur de messages et l'identifiant de clé.
#
# Convention de mission :
#
# le message courant est traité avec la clé présente
# au début de la période.
#
# K2 reste un renouvellement conventionnel immédiat :
# sa sélection active toujours la nouvelle clé (elle
# n'est de toute façon jamais sélectionnable avant que
# le renouvellement soit requis, cf. DM-EQ95).
#
# K1a et K1b possèdent désormais une phase de
# PRÉPARATION (accumulation progressive) : leur seule
# sélection ne suffit plus à activer la nouvelle clé.
# L'activation exige en plus :
# - qu'une clé candidate soit prête
#   (candidate_key_ready) ;
# - que cette clé candidate corresponde à l'action
#   sélectionnée (candidate_key_action == key_action) ;
# - que le renouvellement soit effectivement requis
#   (renewal_required).
#
# Tant que ces conditions ne sont pas réunies, K1a/K1b
# ne remettent PAS à zéro l'âge de la clé active : la
# préparation continue en arrière-plan sans interrompre
# l'usage de la clé courante.
def update_key_state(
    previous_key_age_s,
    previous_message_count,
    current_key_identifier,
    key_action,
    legitimate_message_served,
    message_period_s,
    renewal_required=False,
    candidate_key_ready=False,
    candidate_key_action=None
):

    if message_period_s <= 0:

        raise ValueError(
            "La période des messages doit être "
            "strictement positive."
        )

    key_activated = (
        legitimate_message_served
        and key_action is not None
        and (
            key_action == KeyAction.K2
            or (
                (
                    key_action == KeyAction.K1A
                    or key_action == KeyAction.K1B
                )
                and candidate_key_ready
                and candidate_key_action == key_action
                and renewal_required
            )
        )
    )

    if key_activated:

        return {
            "key_age_s": 0.0,
            "messages_with_current_key": 0,
            "current_key_identifier": (
                create_next_key_identifier(
                    current_key_identifier
                )
            ),
            "key_renewed": True
        }

    # Sans renouvellement, le temps continue de s'écouler.
    new_key_age_s = (
        previous_key_age_s
        + message_period_s
    )

    new_message_count = (
        previous_message_count
    )

    # Le compteur augmente seulement lorsque
    # le message légitime a réellement été servi.
    if legitimate_message_served:

        new_message_count += 1

    return {
        "key_age_s": new_key_age_s,
        "messages_with_current_key": (
            new_message_count
        ),
        "current_key_identifier": (
            current_key_identifier
        ),
        "key_renewed": False
    }


# Cette fonction met à jour un budget de duty-cycle
# avec un mécanisme simple de type "seau de jetons".
#
# 1. le temps d'antenne réellement utilisé est retiré ;
# 2. le budget de la nouvelle période est ajouté ;
# 3. le résultat est limité par un maximum déclaré.
#
# Le maximum et la recharge sont des paramètres de simulation.
def update_duty_cycle_budget(
    current_airtime_s,
    used_airtime_s,
    recharge_airtime_s,
    maximum_airtime_s
):

    if (
        current_airtime_s < 0
        or used_airtime_s < 0
        or recharge_airtime_s < 0
        or maximum_airtime_s < 0
    ):

        raise ValueError(
            "Les valeurs de duty-cycle "
            "ne peuvent pas être négatives."
        )

    remaining_after_use_s = max(
        0.0,
        current_airtime_s
        - used_airtime_s
    )

    updated_airtime_s = min(
        maximum_airtime_s,
        remaining_after_use_s
        + recharge_airtime_s
    )

    return updated_airtime_s


# ================================================================
# 6. UNE PÉRIODE COMPLÈTE DE MISSION
# ================================================================


# Cette fonction exécute une période complète.
#
# L'ordre suit le protocole :
#
# canal -> clé -> contexte -> décision -> Alice
# -> Mallory -> compteurs -> nouvel état.
def run_mission_step(
    state,
    parameters,
    random_generator,
    maximum_duty_cycle_airtime_s,
    duty_cycle_recharge_s,
    rff_profile_available=True,
    variation_feasible=None,
    k2_protocol=None,
    observed_snr_db=None,
    real_snr_db=None,
    criticality=None,
    mallory_attempted=None,
    compromise_suspected=False,
    speed_m_s=None,
    decision_policy_fn=None,
    contextual_weights_resolver_fn=None
):

    if maximum_duty_cycle_airtime_s < 0:

        raise ValueError(
            "Le maximum de duty-cycle "
            "ne peut pas être négatif."
        )

    if duty_cycle_recharge_s < 0:

        raise ValueError(
            "La recharge de duty-cycle "
            "ne peut pas être négative."
        )

    # ------------------------------------------------------------
    # 1. SNR observé
    # ------------------------------------------------------------

    if observed_snr_db is None:

        observed_snr_db = draw_observed_snr_db(
            parameters,
            random_generator
        )

    # La première version utilise le même SNR
    # pour l'observation et la réalité.
    #
    # Une trace différente peut toutefois être fournie
    # pour étudier une erreur d'estimation.
    if real_snr_db is None:

        real_snr_db = observed_snr_db

    # ------------------------------------------------------------
    # 2. Criticité
    # ------------------------------------------------------------

    if criticality is None:

        criticality = 1 if draw_bernoulli(
            parameters.critical_message_probability,
            random_generator
        ) else 0

    if criticality not in [
        0,
        1
    ]:

        raise ValueError(
            "La criticité doit valoir 0 ou 1."
        )

    # ------------------------------------------------------------
    # 3. Tentative de Mallory
    # ------------------------------------------------------------

    if mallory_attempted is None:

        mallory_attempted = draw_bernoulli(
            parameters.mallory_attempt_probability,
            random_generator
        )

    # ------------------------------------------------------------
    # 4. Canal
    # ------------------------------------------------------------

    channel_metrics = calculate_channel_metrics(
        parameters=parameters,
        snr_db=observed_snr_db,
        speed_m_s=speed_m_s
    )

    # ------------------------------------------------------------
    # 4bis. phi_var réellement calculé
    # ------------------------------------------------------------
    #
    # La fenêtre glissante inclut l'observation de cette
    # période : elle sert à juger si le canal varie assez
    # dans le temps (voir
    # channel.calculate_temporal_variability_feasible).
    #
    # Un appelant peut toujours forcer explicitement
    # variation_feasible (utile pour les tests unitaires ou
    # une analyse exploratoire assumée) : dans ce cas, la
    # valeur calculée ci-dessous n'est PAS utilisée. Sinon
    # (valeur par défaut None), phi_var est désormais une
    # métrique réellement mesurée sur la trace du canal,
    # plus jamais un booléen figé par scénario.
    new_recent_rho_ab_window = (
        state.recent_rho_ab_window
        + (channel_metrics.rho_ab,)
    )[-parameters.variability_window_size:]

    if variation_feasible is None:

        computed_variation_feasible = (
            calculate_temporal_variability_feasible(
                rho_ab_window=(
                    new_recent_rho_ab_window
                ),
                minimum_window_size=(
                    parameters.variability_window_size
                ),
                minimum_std_dev=(
                    parameters
                    .variability_minimum_std_dev
                ),
                maximum_lag1_autocorrelation=(
                    parameters
                    .variability_maximum_lag1_autocorrelation
                ),
                maximum_bit_frequency=(
                    parameters
                    .variability_maximum_bit_frequency
                ),
                kept_measurement_ratio=(
                    parameters.kept_measurement_ratio
                ),
                minimum_valid_measurements=(
                    parameters
                    .variability_minimum_valid_measurements
                )
            )
        )

    else:

        computed_variation_feasible = (
            variation_feasible
        )

    # ------------------------------------------------------------
    # 5. État de clé et contexte
    # ------------------------------------------------------------

    key_context_metrics = (
        calculate_key_context_metrics(
            state=state,
            parameters=parameters,
            compromise_suspected=(
                compromise_suspected
            )
        )
    )

    context = create_mission_context(
        state=state,
        channel_metrics=channel_metrics,
        criticality=criticality,
        rff_profile_available=(
            rff_profile_available
        ),
        compromise_suspected=(
            compromise_suspected
        ),
        key_context_metrics=(
            key_context_metrics
        )
    )

    # ------------------------------------------------------------
    # 6. Decision Maker
    # ------------------------------------------------------------
    #
    # decision_policy_fn permet de brancher une politique de
    # décision ALTERNATIVE (par exemple, la baseline
    # B1-CONVENTIONAL de physec_dm/case_studies.py), sans
    # dupliquer le reste du pipeline de mission (coûts réels,
    # Mallory, mise à jour de l'état). Par défaut (None), le
    # comportement historique est conservé à l'identique :
    # run_decision_maker (P0) est appelé. Toute politique
    # alternative doit accepter les mêmes arguments et
    # retourner un objet compatible avec DecisionMakerResult
    # (selected_evaluation, refusal_of_service, etc.) — elle
    # doit réutiliser les mêmes équations de
    # decision_maker.py, jamais en recréer de nouvelles.
    if decision_policy_fn is None:

        decision_policy_fn = run_decision_maker

    # contextual_weights_resolver_fn permet de brancher la
    # résolution des poids contextuels
    # (physec_dm.contextual_policy.resolve_contextual_weights,
    # point d'entrée unique pour les cinq cas d'étude) sans
    # modifier run_decision_maker : par défaut (None), ce
    # dernier retombe sur son propre comportement historique
    # (parameters.contextual_weights).
    resolved_contextual_weights = None

    if contextual_weights_resolver_fn is not None:

        resolved_contextual_weights = (
            contextual_weights_resolver_fn(
                context,
                state,
                parameters
            )
        )

    decision_maker_result = decision_policy_fn(
        context=context,
        parameters=parameters,
        rho_ab=channel_metrics.rho_ab,
        variation_feasible=computed_variation_feasible,
        k2_protocol=k2_protocol,
        contextual_weights=resolved_contextual_weights
    )

    selected_evaluation = (
        decision_maker_result.selected_evaluation
    )

    legitimate_message_served = (
        selected_evaluation is not None
        and not decision_maker_result.refusal_of_service
    )

    # selected_key_action est calculé ici (avant la
    # section 11 qui l'utilisait jusqu'ici) car la
    # planification indépendante des sondages K1b
    # (section 7bis) a besoin de le connaître pour éviter
    # tout double débit.
    selected_key_action = None

    if selected_evaluation is not None:

        selected_key_action = (
            selected_evaluation
            .decision
            .key_action
        )

    # ------------------------------------------------------------
    # 7. Coût réellement débité à Alice
    # ------------------------------------------------------------

    realized_costs = calculate_realized_alice_costs(
        selected_evaluation=selected_evaluation,
        parameters=parameters,
        random_generator=random_generator,
        k2_protocol=k2_protocol
    )

    energy_debited_from_alice_j = (
        realized_costs["energy_j"]
    )

    airtime_used_s = (
        realized_costs["airtime_s"]
    )

    # ------------------------------------------------------------
    # 7bis. Métriques K1a/K1b indépendantes de la sélection
    # ------------------------------------------------------------
    #
    # DM-EQ95/96 (strictes, sans exception) : le Decision
    # Maker ne peut JAMAIS retourner K1a ou K1b tant que
    # renewal_required=False. Dans ce cas,
    # decision_maker_result.all_evaluations ne contient
    # aucune métrique de clé pour K1a/K1b (rejetées dès les
    # règles de raisonnement, cf. Algorithme 1).
    #
    # K1a reste toutefois opportuniste : Alice et Bob
    # obtiennent une mesure de canal "gratuitement" à partir
    # de N'IMPORTE QUEL échange légitime déjà servi, que le
    # DM ait ou non sélectionné K1a. Cette observation est
    # un phénomène physique de la MISSION, pas une décision
    # du DM : on calcule donc ses métriques directement via
    # key_generation.calculate_key_metrics, indépendamment
    # de ce que le DM a retourné cette période.
    #
    # K1b, elle, exige des sondages dédiés réellement
    # coûteux (énergie + temps d'antenne). Elle ne progresse
    # donc plus jamais gratuitement en arrière-plan : ses
    # métriques ne viennent que de l'évaluation du DM
    # (k1b_key_metrics est None tant que renewal_required
    # =False), et son compteur de mesures n'avance que
    # lorsqu'elle est réellement la décision sélectionnée
    # (k1b_probe_sent_via_selection). Le coût du sondage est
    # alors déjà débité par calculate_realized_alice_costs
    # (section 7), au moment même où il est engagé — jamais
    # par anticipation.
    k1a_key_metrics = calculate_key_metrics(
        key_action=KeyAction.K1A,
        parameters=parameters,
        rho_ab=channel_metrics.rho_ab,
        key_age_s=state.key_age_s,
        messages_with_current_key=(
            state.messages_with_current_key
        ),
        compromise_suspected=compromise_suspected,
        variation_feasible=computed_variation_feasible,
        collected_measurements=(
            state.k1a_measurements_collected
        ),
        candidate_ready=(
            state.candidate_key_ready
            and state.candidate_key_action
            == KeyAction.K1A
        )
    )

    k1b_key_metrics = find_key_metrics_for_action(
        decision_maker_result.all_evaluations,
        KeyAction.K1B
    )

    k1b_probe_sent_via_selection = (
        legitimate_message_served
        and selected_key_action == KeyAction.K1B
        and k1b_key_metrics is not None
    )

    # k1b_time_since_last_probe_s ne gate plus aucun sondage
    # indépendant (section 7bis supprimée) : il est conservé
    # inchangé, sauf remise à zéro après activation
    # (section 11c).
    new_k1b_time_since_last_probe_s = (
        state.k1b_time_since_last_probe_s
    )

    # ------------------------------------------------------------
    # 8. Mallory, indépendamment d'Alice
    # ------------------------------------------------------------

    mallory_result = evaluate_mallory(
        selected_evaluation=selected_evaluation,
        real_snr_db=real_snr_db,
        parameters=parameters,
        random_generator=random_generator,
        mallory_attempted=mallory_attempted
    )

    mallory_accepted = (
        mallory_result["accepted"]
    )

    # ------------------------------------------------------------
    # 9. Plancher de sécurité au SNR réel
    # ------------------------------------------------------------

    security_floor_violated = False

    if selected_evaluation is not None:

        real_authentication_metrics = (
            calculate_authentication_metrics(
                authentication_action=(
                    selected_evaluation
                    .decision
                    .authentication_action
                ),
                parameters=parameters,
                mallory_snr_db=real_snr_db
            )
        )

        real_far_limit = parameters.get_far_limit(
            criticality
        )

        # Le Decision Maker utilise le champ FAR
        # de la modélisation pour son plancher.
        security_floor_violated = (
            real_authentication_metrics.far
            > real_far_limit
        )

    # ------------------------------------------------------------
    # 10. Mise à jour de la batterie
    # ------------------------------------------------------------

    new_battery_energy_j = max(
        0.0,
        state.battery_energy_j
        - energy_debited_from_alice_j
    )

    # ------------------------------------------------------------
    # 11. Mise à jour de la clé
    # ------------------------------------------------------------

    # --------------------------------------------------------
    # 11a. Progression de la préparation K1a / K1b
    # --------------------------------------------------------
    #
    # K1a est opportuniste : une mesure exploitable est
    # obtenue "gratuitement" à partir de N'IMPORTE QUEL
    # échange légitime servi, indépendamment de l'action
    # réellement sélectionnée, tant que la PHY reste
    # faisable au SNR de cette période.
    #
    # Hypothèse exploratoire documentée (aucune équation ou
    # documentation existante ne précise ce taux) :
    # UNE observation réciproque valide est produite par
    # échange légitime servi. Voir
    # results/three_scenarios_explicit_analysis/
    # k1a_k1b_model_consistency_audit.md, section 6.
    #
    # K1b progresse soit par sélection directe (rare, une
    # fois sa collecte assez avancée pour redevenir
    # compétitive dans l'échéance), soit — le cas normal, dès
    # le début de la préparation — par le sondage
    # INDÉPENDANT planifié en section 7bis. k1a_key_metrics
    # et k1b_key_metrics ont déjà été calculés en 7bis.
    #
    # Une fois une clé candidate prête (candidate_key_ready),
    # les deux compteurs sont gelés : il n'y a plus rien à
    # accumuler tant que la clé prête n'a pas été activée.
    new_k1a_measurements_collected = (
        state.k1a_measurements_collected
    )

    new_k1b_measurements_collected = (
        state.k1b_measurements_collected
    )

    if not state.candidate_key_ready:

        if (
            legitimate_message_served
            and k1a_key_metrics is not None
            and k1a_key_metrics.phy_feasible is True
        ):

            new_k1a_measurements_collected = min(
                state.k1a_measurements_collected + 1,
                k1a_key_metrics.required_measurements
            )

        if k1b_probe_sent_via_selection:

            new_k1b_measurements_collected = min(
                state.k1b_measurements_collected + 1,
                k1b_key_metrics.required_measurements
            )

    # --------------------------------------------------------
    # 11b. Détection d'une clé candidate prête
    # --------------------------------------------------------
    #
    # Dès qu'UNE des deux préparations atteint son nombre
    # de mesures requis, elle devient LA clé candidate : les
    # deux compteurs sont ensuite gelés (voir ci-dessus)
    # jusqu'à l'activation. K1a est vérifiée en premier par
    # convention arbitraire lorsque les deux se termineraient
    # simultanément (cas limite documenté, non observé dans
    # les campagnes de validation).
    new_candidate_key_ready = state.candidate_key_ready
    new_candidate_key_action = state.candidate_key_action

    if not new_candidate_key_ready:

        if (
            k1a_key_metrics is not None
            and k1a_key_metrics.required_measurements
            is not None
            and new_k1a_measurements_collected
            >= k1a_key_metrics.required_measurements
        ):

            new_candidate_key_ready = True
            new_candidate_key_action = KeyAction.K1A

        elif (
            k1b_key_metrics is not None
            and k1b_key_metrics.required_measurements
            is not None
            and new_k1b_measurements_collected
            >= k1b_key_metrics.required_measurements
        ):

            new_candidate_key_ready = True
            new_candidate_key_action = KeyAction.K1B

    candidate_key_ready_before = (
        state.candidate_key_ready
    )

    key_update = update_key_state(
        previous_key_age_s=state.key_age_s,
        previous_message_count=(
            state.messages_with_current_key
        ),
        current_key_identifier=(
            state.current_key_identifier
        ),
        key_action=selected_key_action,
        legitimate_message_served=(
            legitimate_message_served
        ),
        message_period_s=(
            parameters.message_period_s
        ),
        renewal_required=(
            context.renewal_required
        ),
        candidate_key_ready=(
            new_candidate_key_ready
        ),
        candidate_key_action=(
            new_candidate_key_action
        )
    )

    # Après une activation, la préparation repart de zéro :
    # les compteurs K1, l'état de la clé candidate et le
    # rythme de sondage K1b sont remis à leur valeur
    # initiale.
    if key_update["key_renewed"]:

        new_k1a_measurements_collected = 0
        new_k1b_measurements_collected = 0
        new_candidate_key_ready = False
        new_candidate_key_action = None
        new_k1b_time_since_last_probe_s = 0.0

    # ------------------------------------------------------------
    # 11c. Validation a posteriori face à Ève (extension)
    # ------------------------------------------------------------
    #
    # Calculée UNIQUEMENT lorsqu'une clé physique (K1a ou
    # K1b) vient d'être activée, sur les mêmes rho_ab et
    # noise_correlation que ceux observés par Bob cette
    # période. Ève n'influence jamais la décision : ce
    # calcul a lieu APRÈS que le Decision Maker a choisi,
    # et son résultat n'est jamais réinjecté dans le
    # contexte ni dans aucune contrainte.
    eve_validation = None

    if (
        key_update["key_renewed"]
        and selected_key_action
        in (KeyAction.K1A, KeyAction.K1B)
    ):

        eve_validation = (
            evaluate_eve_secrecy_for_period(
                rho_ab=channel_metrics.rho_ab,
                noise_correlation=(
                    channel_metrics.noise_correlation
                ),
                parameters=parameters
            )
        )

    # ------------------------------------------------------------
    # 12. Mise à jour du duty-cycle
    # ------------------------------------------------------------

    new_duty_cycle_airtime_s = (
        update_duty_cycle_budget(
            current_airtime_s=(
                state.remaining_duty_cycle_airtime_s
            ),
            used_airtime_s=airtime_used_s,
            recharge_airtime_s=(
                duty_cycle_recharge_s
            ),
            maximum_airtime_s=(
                maximum_duty_cycle_airtime_s
            )
        )
    )

    # ------------------------------------------------------------
    # 13. Mise à jour des compteurs
    # ------------------------------------------------------------

    legitimate_messages = (
        state.legitimate_messages
        + 1
    )

    served_messages = (
        state.served_messages
        + (
            1
            if legitimate_message_served
            else 0
        )
    )

    legitimate_refusals = (
        state.legitimate_refusals
        + (
            0
            if legitimate_message_served
            else 1
        )
    )

    mallory_attempts = (
        state.mallory_attempts
        + (
            1
            if mallory_attempted
            else 0
        )
    )

    false_acceptances = (
        state.false_acceptances
        + (
            1
            if mallory_accepted
            else 0
        )
    )

    critical_mallory_attempts = (
        state.critical_mallory_attempts
    )

    critical_false_acceptances = (
        state.critical_false_acceptances
    )

    if criticality == 1 and mallory_attempted:

        critical_mallory_attempts += 1

        if mallory_accepted:

            critical_false_acceptances += 1

    security_floor_violations = (
        state.security_floor_violations
        + (
            1
            if security_floor_violated
            else 0
        )
    )

    # ------------------------------------------------------------
    # 14. Nouvel état
    # ------------------------------------------------------------

    state_after = MissionState(
        step_index=state.step_index + 1,
        time_s=(
            state.time_s
            + parameters.message_period_s
        ),
        battery_energy_j=(
            new_battery_energy_j
        ),
        key_age_s=(
            key_update["key_age_s"]
        ),
        messages_with_current_key=(
            key_update[
                "messages_with_current_key"
            ]
        ),
        current_key_identifier=(
            key_update[
                "current_key_identifier"
            ]
        ),
        remaining_duty_cycle_airtime_s=(
            new_duty_cycle_airtime_s
        ),
        legitimate_messages=(
            legitimate_messages
        ),
        served_messages=served_messages,
        legitimate_refusals=(
            legitimate_refusals
        ),
        mallory_attempts=mallory_attempts,
        false_acceptances=(
            false_acceptances
        ),
        critical_mallory_attempts=(
            critical_mallory_attempts
        ),
        critical_false_acceptances=(
            critical_false_acceptances
        ),
        security_floor_violations=(
            security_floor_violations
        ),
        k1a_measurements_collected=(
            new_k1a_measurements_collected
        ),
        k1b_measurements_collected=(
            new_k1b_measurements_collected
        ),
        candidate_key_ready=(
            new_candidate_key_ready
        ),
        candidate_key_action=(
            new_candidate_key_action
        ),
        k1b_time_since_last_probe_s=(
            new_k1b_time_since_last_probe_s
        ),
        recent_rho_ab_window=(
            new_recent_rho_ab_window
        )
    )

    return MissionStepResult(
        state_before=state,
        context=context,
        channel_metrics=channel_metrics,
        decision_maker_result=(
            decision_maker_result
        ),
        legitimate_message_served=(
            legitimate_message_served
        ),
        mallory_attempted=(
            mallory_attempted
        ),
        mallory_accepted=(
            mallory_accepted
        ),
        energy_debited_from_alice_j=(
            energy_debited_from_alice_j
        ),
        state_after=state_after,
        k1a_measurements_before=(
            state.k1a_measurements_collected
        ),
        k1a_measurements_after=(
            new_k1a_measurements_collected
        ),
        k1b_measurements_before=(
            state.k1b_measurements_collected
        ),
        k1b_measurements_after=(
            new_k1b_measurements_collected
        ),
        candidate_key_ready_before=(
            candidate_key_ready_before
        ),
        candidate_key_ready_after=(
            new_candidate_key_ready
        ),
        candidate_key_action=(
            new_candidate_key_action
        ),
        eve_validation=eve_validation
    )


# ================================================================
# 7. OUTILS DE RÉSULTATS
# ================================================================


# Cette fonction calcule un taux.
#
# Lorsque le dénominateur vaut zéro,
# le taux est non défini et la fonction retourne None.
def calculate_rate(
    numerator,
    denominator
):

    if numerator < 0 or denominator < 0:

        raise ValueError(
            "Les compteurs ne peuvent pas être négatifs."
        )

    if denominator == 0:

        return None

    return (
        numerator
        / denominator
    )


# Cette fonction lit une valeur optionnelle
# dans une trace déterministe.
def get_trace_value(
    trace,
    step_index,
    trace_name
):

    if trace is None:

        return None

    if step_index >= len(trace):

        raise ValueError(
            trace_name
            + " ne contient pas assez de valeurs."
        )

    return trace[
        step_index
    ]


# ================================================================
# 8. MISSION COMPLÈTE
# ================================================================


# Cette fonction exécute une mission complète.
#
# Elle peut fonctionner :
#
# - avec des tirages aléatoires ;
# - avec des traces déterministes fournies par campaign.py.
def run_mission(
    parameters,
    seed,
    policy_id="P0",
    max_steps=1000,
    max_duration_s=None,
    initial_duty_cycle_airtime_s=None,
    maximum_duty_cycle_airtime_s=None,
    duty_cycle_recharge_s=None,
    rff_profile_available=True,
    variation_feasible=None,
    k2_protocol=None,
    observed_snr_trace=None,
    real_snr_trace=None,
    criticality_trace=None,
    mallory_trace=None,
    compromise_trace=None,
    speed_trace=None,
    decision_policy_fn=None,
    contextual_weights_resolver_fn=None
):

    if max_steps <= 0:

        raise ValueError(
            "max_steps doit être strictement positif."
        )

    if (
        max_duration_s is not None
        and max_duration_s <= 0
    ):

        raise ValueError(
            "max_duration_s doit être "
            "strictement positif."
        )

    # Le budget ajouté à chaque période
    # est dérivé du duty-cycle et de la période.
    derived_period_budget_s = (
        parameters.duty_cycle_fraction
        * parameters.message_period_s
    )

    if initial_duty_cycle_airtime_s is None:

        initial_duty_cycle_airtime_s = (
            derived_period_budget_s
        )

    if maximum_duty_cycle_airtime_s is None:

        maximum_duty_cycle_airtime_s = (
            initial_duty_cycle_airtime_s
        )

    if duty_cycle_recharge_s is None:

        duty_cycle_recharge_s = (
            derived_period_budget_s
        )

    random_generator = create_random_generator(
        seed
    )

    state = create_initial_mission_state(
        parameters=parameters,
        initial_duty_cycle_airtime_s=(
            initial_duty_cycle_airtime_s
        )
    )

    steps = []
    decision_counts = {}

    stop_reason = "maximum_steps"
    censored = True

    while len(steps) < max_steps:

        # La réserve marque la fin de vie.
        if (
            state.battery_energy_j
            <= parameters.minimum_battery_energy_j
        ):

            stop_reason = (
                "battery_reserve_reached"
            )

            censored = False
            break

        if (
            max_duration_s is not None
            and state.time_s >= max_duration_s
        ):

            stop_reason = (
                "maximum_duration"
            )

            censored = True
            break

        step_index = len(
            steps
        )

        observed_snr_db = get_trace_value(
            observed_snr_trace,
            step_index,
            "observed_snr_trace"
        )

        real_snr_db = get_trace_value(
            real_snr_trace,
            step_index,
            "real_snr_trace"
        )

        criticality = get_trace_value(
            criticality_trace,
            step_index,
            "criticality_trace"
        )

        mallory_attempted = get_trace_value(
            mallory_trace,
            step_index,
            "mallory_trace"
        )

        compromise_suspected = get_trace_value(
            compromise_trace,
            step_index,
            "compromise_trace"
        )

        if compromise_suspected is None:

            compromise_suspected = False

        speed_m_s = get_trace_value(
            speed_trace,
            step_index,
            "speed_trace"
        )

        step_result = run_mission_step(
            state=state,
            parameters=parameters,
            random_generator=(
                random_generator
            ),
            maximum_duty_cycle_airtime_s=(
                maximum_duty_cycle_airtime_s
            ),
            duty_cycle_recharge_s=(
                duty_cycle_recharge_s
            ),
            rff_profile_available=(
                rff_profile_available
            ),
            variation_feasible=(
                variation_feasible
            ),
            k2_protocol=k2_protocol,
            observed_snr_db=(
                observed_snr_db
            ),
            real_snr_db=real_snr_db,
            criticality=criticality,
            mallory_attempted=(
                mallory_attempted
            ),
            compromise_suspected=(
                compromise_suspected
            ),
            speed_m_s=speed_m_s,
            decision_policy_fn=(
                decision_policy_fn
            ),
            contextual_weights_resolver_fn=(
                contextual_weights_resolver_fn
            )
        )

        steps.append(
            step_result
        )

        selected_evaluation = (
            step_result
            .decision_maker_result
            .selected_evaluation
        )

        if selected_evaluation is not None:

            decision_name = (
                selected_evaluation
                .decision
                .get_name()
            )

            decision_counts[
                decision_name
            ] = (
                decision_counts.get(
                    decision_name,
                    0
                )
                + 1
            )

        state = step_result.state_after

    # Si la boucle atteint exactement max_steps,
    # le motif reste maximum_steps.
    if (
        len(steps) == max_steps
        and state.battery_energy_j
        <= parameters.minimum_battery_energy_j
    ):

        stop_reason = (
            "battery_reserve_reached"
        )

        censored = False

    total_energy_debited_j = (
        parameters.initial_battery_energy_j
        - state.battery_energy_j
    )

    mean_energy_per_generated_message_j = (
        calculate_rate(
            total_energy_debited_j,
            state.legitimate_messages
        )
    )

    mean_energy_per_served_message_j = (
        calculate_rate(
            total_energy_debited_j,
            state.served_messages
        )
    )

    false_acceptance_rate = calculate_rate(
        state.false_acceptances,
        state.mallory_attempts
    )

    critical_false_acceptance_rate = (
        calculate_rate(
            state.critical_false_acceptances,
            state.critical_mallory_attempts
        )
    )

    legitimate_refusal_rate = calculate_rate(
        state.legitimate_refusals,
        state.legitimate_messages
    )

    # Le nombre de décisions correspond ici
    # au nombre de messages servis.
    security_floor_violation_rate = (
        calculate_rate(
            state.security_floor_violations,
            state.served_messages
        )
    )

    return MissionResult(
        parameters_snapshot=(
            parameters.to_dictionary()
        ),
        seed=seed,
        policy_id=policy_id,
        steps=steps,
        lifetime_s=state.time_s,
        mean_energy_per_generated_message_j=(
            mean_energy_per_generated_message_j
        ),
        mean_energy_per_served_message_j=(
            mean_energy_per_served_message_j
        ),
        false_acceptance_rate=(
            false_acceptance_rate
        ),
        critical_false_acceptance_rate=(
            critical_false_acceptance_rate
        ),
        legitimate_refusal_rate=(
            legitimate_refusal_rate
        ),
        security_floor_violation_rate=(
            security_floor_violation_rate
        ),
        decision_counts=decision_counts,
        final_state=state,
        stop_reason=stop_reason,
        censored=censored
    )
