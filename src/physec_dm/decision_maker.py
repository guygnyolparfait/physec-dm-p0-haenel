# On importe les classes et les fonctions de models.py.
#
# DecisionEvaluation conserve le résultat de l'évaluation
# d'une seule décision.
#
# DecisionMakerResult conserve le résultat final du décideur.
#
# RejectionRecord explique pourquoi une décision est rejetée.
#
# AuthenticationAction et KeyAction permettent de reconnaître
# les actions A1, A2, K0, K1a, K1b et K2.
#
# create_all_decisions construit les huit décisions du modèle.
from physec_dm.models import (
    AuthenticationAction,
    DecisionEvaluation,
    DecisionMakerResult,
    KeyAction,
    RejectionRecord,
    create_all_decisions
)


# On importe les trois fonctions qui traduisent
# les sous-modèles déjà validés :
#
# authentication.py
#     calcule la FAR, la FRR et la robustesse ;
#
# key_generation.py
#     calcule le KDR, la faisabilité PHY
#     et la qualité de clé ;
#
# energy_latency.py
#     calcule l'énergie, la latence
#     et le temps d'antenne.
from physec_dm.authentication import (
    calculate_authentication_metrics
)

from physec_dm.key_generation import (
    calculate_key_metrics
)

from physec_dm.energy_latency import (
    build_cost_metrics
)


# ================================================================
# 1. VECTEUR DES QUATRE OBJECTIFS
# ================================================================


# Cette fonction construit le vecteur objectif
# d'une décision admissible.
#
# Dans la modélisation :
#
# f_t(D) = [
#     E_t(D),
#     L_t(D),
#     -R_auth_t(D),
#     -Q_key_t(D)
# ]
#
# Cette fonction correspond à DM-EQ93.
#
# L'énergie et la latence sont déjà des objectifs
# à minimiser.
#
# La robustesse et la qualité de clé doivent être maximisées.
# Nous plaçons donc un signe moins devant elles
# afin que les quatre composantes soient minimisées.
def build_objective_vector(
    authentication_metrics,
    key_metrics,
    cost_metrics
):

    # L'objectif énergétique utilise l'énergie attendue
    # du trafic légitime.
    #
    # Le pire cas énergétique sera utilisé séparément
    # pour la contrainte de batterie.
    energy_objective = (
        cost_metrics.expected_energy_j
    )

    # L'objectif de latence est la latence normalisée
    # déjà calculée dans energy_latency.py.
    latency_objective = (
        cost_metrics.normalized_latency
    )

    # Le signe moins transforme la maximisation
    # de la robustesse en minimisation.
    authentication_objective = (
        -authentication_metrics.authentication_robustness
    )

    # Même principe pour la qualité de clé.
    key_objective = (
        -key_metrics.key_quality
    )

    objective_vector = [
        energy_objective,
        latency_objective,
        authentication_objective,
        key_objective
    ]

    return objective_vector


# ================================================================
# 2. JOURNAL DES REJETS
# ================================================================


# Cette fonction crée un motif de rejet
# et l'ajoute à l'évaluation de la décision.
#
# Elle évite de répéter le même code
# dans toutes les vérifications.
def add_rejection(
    evaluation,
    stage,
    reason_code,
    explanation,
    measured_value=None,
    allowed_value=None
):

    rejection_record = RejectionRecord(
        decision=evaluation.decision,
        stage=stage,
        reason_code=reason_code,
        explanation=explanation,
        measured_value=measured_value,
        allowed_value=allowed_value
    )

    # La méthode add_rejection a déjà été définie
    # dans models.py.
    evaluation.add_rejection(
        rejection_record
    )

    return rejection_record


# ================================================================
# 3. CONDITIONS DE RAISONNEMENT
# ================================================================


# Cette fonction applique les règles logiques
# qui empêchent d'évaluer une décision sans sens.
#
# Ces règles ne sont pas des contraintes d'optimisation.
#
# Elles correspondent, à la lettre, à DM-EQ94, DM-EQ95
# et DM-EQ96 :
#
# A2 autorisée implique profil RFF disponible ;
#
# r_t=0 implique K_i=K0 (aucune exception) ;
#
# r_t=1 implique K_i≠K0.
#
# ----------------------------------------------------------------
# RETOUR À LA RÈGLE STRICTE (validé avec l'encadrante) :
#
# Une version antérieure de ce fichier autorisait K1a et
# K1b comme décisions ÉVALUABLES avant que le renouvellement
# soit requis, au nom d'une "phase de préparation". Cette
# exception ne figure dans aucune équation du document de
# modélisation et a été retirée : la décision RETOURNÉE par
# le Decision Maker respecte de nouveau (95)-(96) sans
# exception — seul K0 est possible tant que
# renewal_required=False.
#
# La collecte progressive de mesures pour une future clé
# K1a reste possible, mais elle est désormais un phénomène
# de mission (physec_dm/mission.py), calculé indépendamment
# de l'évaluation du Decision Maker via un appel direct à
# key_generation.calculate_key_metrics — jamais comme une
# décision que le DM pourrait retourner. K1b n'accumule
# plus jamais gratuitement : elle ne progresse que
# lorsqu'elle est réellement sélectionnée ici, ce qui ne
# peut arriver qu'une fois renewal_required=True.
def apply_reasoning_rules(
    evaluation,
    context
):

    decision = evaluation.decision

    # ------------------------------------------------------------
    # DM-EQ94 : A2 exige un profil RFF disponible
    # ------------------------------------------------------------

    if (
        decision.authentication_action
        == AuthenticationAction.A2
        and not context.rff_profile_available
    ):

        add_rejection(
            evaluation=evaluation,
            stage="reasoning",
            reason_code="RFF_PROFILE_UNAVAILABLE",
            explanation=(
                "A2 est interdite car le profil RFF "
                "d'Alice n'est pas disponible."
            ),
            measured_value=False,
            allowed_value=True
        )

    # ------------------------------------------------------------
    # DM-EQ95 : si aucun renouvellement n'est requis,
    #            seule K0 a un sens (95)-(96), sans
    #            exception pour K1a ou K1b.
    # ------------------------------------------------------------

    if (
        not context.renewal_required
        and decision.key_action != KeyAction.K0
    ):

        add_rejection(
            evaluation=evaluation,
            stage="reasoning",
            reason_code="KEY_RENEWAL_NOT_REQUIRED",
            explanation=(
                "Seule K0 est admissible tant qu'aucun "
                "renouvellement n'est requis (r_t=0 ⇒ "
                "K_i=K0)."
            ),
            measured_value=decision.key_action.value,
            allowed_value="K0"
        )

    # ------------------------------------------------------------
    # DM-EQ96 : si le renouvellement est requis,
    #            K0 est interdit
    # ------------------------------------------------------------

    if (
        context.renewal_required
        and decision.key_action == KeyAction.K0
    ):

        add_rejection(
            evaluation=evaluation,
            stage="reasoning",
            reason_code="KEY_RENEWAL_REQUIRED",
            explanation=(
                "K0 est interdite car le contexte exige "
                "un renouvellement de la clé."
            ),
            measured_value=KeyAction.K0.value,
            allowed_value="K1a, K1b ou K2"
        )

    # Les règles sont respectées uniquement
    # si aucun rejet logique n'a été ajouté.
    evaluation.reasoning_rules_ok = (
        len(evaluation.rejection_reasons) == 0
    )

    return evaluation.reasoning_rules_ok


# ================================================================
# 4. CONTRAINTES PHYSIQUES, DE RESSOURCES ET DE SÉCURITÉ
# ================================================================


# Cette fonction vérifie toutes les contraintes
# après le calcul des métriques.
#
# Elle correspond à DM-EQ97 jusqu'à DM-EQ102.
#
# enforce_far_floor=False désactive UNIQUEMENT le plancher
# de sécurité DM-EQ102, en conservant toutes les autres
# contraintes (logiques, physiques, ressources) inchangées.
# Cette option n'existe que pour construire la politique de
# référence B4 (« DM sans plancher de FAR »), exigée par le
# protocole pour isoler l'effet de cette seule contrainte :
# elle ne doit jamais être utilisée par P0 ni par aucune
# autre politique de référence.
def apply_resource_and_security_constraints(
    evaluation,
    context,
    parameters,
    enforce_far_floor=True
):

    decision = evaluation.decision
    authentication_metrics = (
        evaluation.authentication_metrics
    )
    key_metrics = evaluation.key_metrics
    cost_metrics = evaluation.cost_metrics

    # Les métriques doivent avoir été calculées
    # avant d'appliquer les contraintes.
    if (
        authentication_metrics is None
        or key_metrics is None
        or cost_metrics is None
    ):

        raise ValueError(
            "Les métriques doivent être calculées "
            "avant les contraintes."
        )

    resource_rejections_before = len(
        evaluation.rejection_reasons
    )

    # ------------------------------------------------------------
    # DM-EQ97 : K1a et K1b exigent une faisabilité PHY complète
    # ------------------------------------------------------------

    if (
        decision.key_action == KeyAction.K1A
        or decision.key_action == KeyAction.K1B
    ):

        # L'accord entre Alice et Bob doit être possible.
        if key_metrics.agreement_feasible is not True:

            add_rejection(
                evaluation=evaluation,
                stage="physical",
                reason_code="PHY_AGREEMENT_INFEASIBLE",
                explanation=(
                    "Le KDR ne permet pas un accord "
                    "suffisant entre Alice et Bob."
                ),
                measured_value=(
                    key_metrics.effective_kdr
                ),
                allowed_value=(
                    parameters.maximum_kdr
                )
            )

        # La variabilité doit avoir été validée.
        #
        # Une valeur None ne constitue pas une preuve
        # de faisabilité PHY complète.
        elif key_metrics.variation_feasible is None:

            add_rejection(
                evaluation=evaluation,
                stage="physical",
                reason_code="PHY_VARIATION_NOT_VALIDATED",
                explanation=(
                    "La condition de variabilité du canal "
                    "n'est pas encore validée."
                ),
                measured_value=None,
                allowed_value=True
            )

        # Une variabilité explicitement fausse
        # interdit la génération PHY.
        elif key_metrics.variation_feasible is not True:

            add_rejection(
                evaluation=evaluation,
                stage="physical",
                reason_code="PHY_VARIATION_INFEASIBLE",
                explanation=(
                    "Le canal ne présente pas la variabilité "
                    "nécessaire à la génération de clé."
                ),
                measured_value=False,
                allowed_value=True
            )

        # La variable combinée doit elle aussi être vraie.
        elif key_metrics.phy_feasible is not True:

            add_rejection(
                evaluation=evaluation,
                stage="physical",
                reason_code="PHY_INFEASIBLE",
                explanation=(
                    "La faisabilité PHY complète "
                    "n'est pas satisfaite."
                ),
                measured_value=key_metrics.phy_feasible,
                allowed_value=True
            )

    # ------------------------------------------------------------
    # DM-EQ98 : contrainte de batterie
    # ------------------------------------------------------------

    available_energy_j = (
        context.battery_energy_j
        - parameters.minimum_battery_energy_j
    )

    # La contrainte utilise le pire cas,
    # conformément au majorant prudent du modèle.
    if (
        cost_metrics.worst_case_energy_j
        > available_energy_j
    ):

        add_rejection(
            evaluation=evaluation,
            stage="resource",
            reason_code="BATTERY_CONSTRAINT",
            explanation=(
                "L'énergie du pire cas dépasse "
                "l'énergie disponible au-dessus de la réserve."
            ),
            measured_value=(
                cost_metrics.worst_case_energy_j
            ),
            allowed_value=available_energy_j
        )

    # ------------------------------------------------------------
    # DM-EQ99 : contrainte de latence d'authentification
    # ------------------------------------------------------------

    authentication_latency_limit_s = (
        parameters.get_authentication_latency_limit(
            context.criticality
        )
    )

    # La contrainte utilise la latence prudente,
    # et non la simple espérance de A2.
    if (
        cost_metrics.prudent_authentication_latency_s
        > authentication_latency_limit_s
    ):

        add_rejection(
            evaluation=evaluation,
            stage="resource",
            reason_code="AUTH_LATENCY_CONSTRAINT",
            explanation=(
                "La latence prudente d'authentification "
                "dépasse la limite du message."
            ),
            measured_value=(
                cost_metrics.prudent_authentication_latency_s
            ),
            allowed_value=(
                authentication_latency_limit_s
            )
        )

    # ------------------------------------------------------------
    # DM-EQ100 : échéance de renouvellement de la clé
    # ------------------------------------------------------------

    if (
        cost_metrics.key_latency_s
        > context.key_deadline_s
    ):

        add_rejection(
            evaluation=evaluation,
            stage="resource",
            reason_code="KEY_DEADLINE_CONSTRAINT",
            explanation=(
                "La clé ne peut pas être renouvelée "
                "avant son échéance."
            ),
            measured_value=cost_metrics.key_latency_s,
            allowed_value=context.key_deadline_s
        )

    # ------------------------------------------------------------
    # DM-EQ101 : contrainte de duty-cycle
    # ------------------------------------------------------------

    if (
        cost_metrics.airtime_s
        > context.remaining_duty_cycle_airtime_s
    ):

        add_rejection(
            evaluation=evaluation,
            stage="resource",
            reason_code="DUTY_CYCLE_CONSTRAINT",
            explanation=(
                "Le temps d'antenne de la décision "
                "dépasse le budget de duty-cycle restant."
            ),
            measured_value=cost_metrics.airtime_s,
            allowed_value=(
                context.remaining_duty_cycle_airtime_s
            )
        )

    # Les ressources sont acceptées seulement
    # si aucune nouvelle raison physique ou de ressource
    # n'a été ajoutée pendant cette partie.
    evaluation.resource_constraints_ok = (
        len(evaluation.rejection_reasons)
        == resource_rejections_before
    )

    # ------------------------------------------------------------
    # DM-EQ102 : plancher de sécurité
    # ------------------------------------------------------------

    far_limit = parameters.get_far_limit(
        context.criticality
    )

    if (
        enforce_far_floor
        and authentication_metrics.far > far_limit
    ):

        add_rejection(
            evaluation=evaluation,
            stage="security",
            reason_code="FAR_CONSTRAINT",
            explanation=(
                "La FAR de la décision dépasse "
                "le plancher de sécurité autorisé."
            ),
            measured_value=authentication_metrics.far,
            allowed_value=far_limit
        )

        evaluation.security_constraint_ok = False

    else:

        evaluation.security_constraint_ok = True

    # DM-EQ103 :
    #
    # une décision appartient à l'ensemble admissible
    # seulement si elle respecte :
    # - les règles logiques ;
    # - les contraintes physiques et de ressources ;
    # - le plancher de sécurité.
    evaluation.admissible = (
        evaluation.reasoning_rules_ok
        and evaluation.resource_constraints_ok
        and evaluation.security_constraint_ok
        and len(evaluation.rejection_reasons) == 0
    )

    return evaluation.admissible


# ================================================================
# 5. ÉVALUATION D'UNE DÉCISION
# ================================================================


# Cette fonction applique toute la chaîne
# à une seule décision :
#
# logique -> métriques -> contraintes -> objectifs.
def evaluate_decision(
    decision,
    context,
    parameters,
    rho_ab,
    variation_feasible=None,
    k2_protocol=None,
    enforce_far_floor=True
):

    evaluation = DecisionEvaluation(
        decision
    )

    # On commence toujours par les règles logiques.
    reasoning_ok = apply_reasoning_rules(
        evaluation,
        context
    )

    # Une décision logiquement impossible
    # n'est pas calculée davantage.
    if not reasoning_ok:

        return evaluation

    try:

        # Calcul des métriques d'authentification.
        authentication_metrics = (
            calculate_authentication_metrics(
                authentication_action=(
                    decision.authentication_action
                ),
                parameters=parameters,
                mallory_snr_db=context.snr_db
            )
        )

        # collected_measurements dépend de l'action de clé
        # évaluée : K1a et K1b accumulent des compteurs
        # indépendants (context.k1a_measurements_collected
        # et context.k1b_measurements_collected). K0 et K2
        # ne possèdent pas de phase d'accumulation.
        if decision.key_action == KeyAction.K1A:

            collected_measurements = (
                context.k1a_measurements_collected
            )

        elif decision.key_action == KeyAction.K1B:

            collected_measurements = (
                context.k1b_measurements_collected
            )

        else:

            collected_measurements = 0

        # candidate_ready_for_this_action est vrai lorsque
        # la décision évaluée correspond exactement à la
        # clé candidate déjà déclarée prête (context.
        # candidate_key_ready / candidate_key_action,
        # alimentés par MissionState). Dans ce cas,
        # calculate_key_metrics ne recalcule pas un reliquat
        # à partir d'un required_measurements recalculé sur
        # le canal courant : la collecte déjà réalisée n'est
        # jamais refacturée une seconde fois.
        candidate_ready_for_this_action = (
            context.candidate_key_ready
            and context.candidate_key_action
            == decision.key_action
        )

        # Calcul des métriques de clé.
        key_metrics = calculate_key_metrics(
            key_action=decision.key_action,
            parameters=parameters,
            rho_ab=rho_ab,
            key_age_s=context.key_age_s,
            messages_with_current_key=(
                context.messages_with_current_key
            ),
            compromise_suspected=(
                context.compromise_suspected
            ),
            variation_feasible=variation_feasible,
            collected_measurements=(
                collected_measurements
            ),
            candidate_ready=(
                candidate_ready_for_this_action
            )
        )

        # Calcul des coûts de la décision complète.
        cost_metrics = build_cost_metrics(
            decision=decision,
            authentication_metrics=(
                authentication_metrics
            ),
            key_metrics=key_metrics,
            context=context,
            parameters=parameters,
            k2_protocol=k2_protocol
        )

    # Un sous-modèle peut refuser une décision
    # lorsqu'un paramètre indispensable manque.
    #
    # Le motif est enregistré au lieu d'être caché.
    except ValueError as error:

        add_rejection(
            evaluation=evaluation,
            stage="model",
            reason_code="MODEL_CALCULATION_ERROR",
            explanation=str(error)
        )

        return evaluation

    # On conserve les trois familles de métriques.
    evaluation.authentication_metrics = (
        authentication_metrics
    )

    evaluation.key_metrics = key_metrics
    evaluation.cost_metrics = cost_metrics

    # On construit le vecteur des quatre objectifs.
    evaluation.objective_vector = (
        build_objective_vector(
            authentication_metrics,
            key_metrics,
            cost_metrics
        )
    )

    # On applique les contraintes.
    apply_resource_and_security_constraints(
        evaluation,
        context,
        parameters,
        enforce_far_floor=enforce_far_floor
    )

    return evaluation


# Cette fonction évalue les huit décisions.
def evaluate_all_decisions(
    context,
    parameters,
    rho_ab,
    variation_feasible=None,
    k2_protocol=None,
    enforce_far_floor=True
):

    all_evaluations = []
    rejection_journal = []

    # L'espace contient exactement huit décisions.
    for decision in create_all_decisions():

        evaluation = evaluate_decision(
            decision=decision,
            context=context,
            parameters=parameters,
            rho_ab=rho_ab,
            variation_feasible=variation_feasible,
            k2_protocol=k2_protocol,
            enforce_far_floor=enforce_far_floor
        )

        all_evaluations.append(
            evaluation
        )

        # On copie les motifs de rejet
        # dans le journal global.
        rejection_journal.extend(
            evaluation.rejection_reasons
        )

    return (
        all_evaluations,
        rejection_journal
    )


# ================================================================
# 6. DOMINANCE ET FRONT DE PARETO
# ================================================================


# Cette fonction vérifie si le vecteur A
# domine le vecteur B.
#
# Dans la modélisation, A domine B si :
#
# A n'est jamais moins bon sur les quatre objectifs ;
#
# A est strictement meilleur sur au moins un objectif.
#
# Cette fonction correspond à DM-EQ104.
def objective_vector_dominates(
    objective_vector_a,
    objective_vector_b,
    tolerance
):

    if tolerance < 0:

        raise ValueError(
            "La tolérance de dominance "
            "ne peut pas être négative."
        )

    if (
        len(objective_vector_a)
        != len(objective_vector_b)
    ):

        raise ValueError(
            "Les deux vecteurs objectifs "
            "doivent avoir la même taille."
        )

    never_worse = True
    strictly_better = False

    for index in range(
        len(objective_vector_a)
    ):

        value_a = objective_vector_a[index]
        value_b = objective_vector_b[index]

        # A est moins bon si sa valeur
        # dépasse B au-delà de la tolérance.
        if value_a > value_b + tolerance:

            never_worse = False

        # A est strictement meilleur
        # si sa valeur est plus petite
        # au-delà de la tolérance.
        if value_a < value_b - tolerance:

            strictly_better = True

    return (
        never_worse
        and strictly_better
    )


# Cette fonction applique la dominance
# directement à deux évaluations.
def evaluation_dominates(
    evaluation_a,
    evaluation_b,
    tolerance
):

    if (
        evaluation_a.objective_vector is None
        or evaluation_b.objective_vector is None
    ):

        raise ValueError(
            "Les vecteurs objectifs doivent être calculés."
        )

    return objective_vector_dominates(
        evaluation_a.objective_vector,
        evaluation_b.objective_vector,
        tolerance
    )


# Cette fonction calcule le front de Pareto exact
# par énumération exhaustive.
#
# Cette fonction correspond à DM-EQ105.
#
# Avec au plus huit décisions,
# aucune métaheuristique n'est nécessaire.
def calculate_pareto_front(
    admissible_evaluations,
    tolerance
):

    pareto_front = []

    for candidate in admissible_evaluations:

        candidate_is_dominated = False

        for other_evaluation in admissible_evaluations:

            # Une décision n'est pas comparée à elle-même.
            if other_evaluation is candidate:

                continue

            if evaluation_dominates(
                other_evaluation,
                candidate,
                tolerance
            ):

                candidate_is_dominated = True
                break

        if not candidate_is_dominated:

            candidate.pareto_optimal = True

            pareto_front.append(
                candidate
            )

    return pareto_front


# ================================================================
# 7. NORMALISATION ET TCHEBYCHEV
# ================================================================


# Cette fonction calcule :
#
# le point idéal :
#     minimum de chaque objectif ;
#
# le point nadir :
#     maximum de chaque objectif sur le front.
def calculate_ideal_and_nadir_points(
    pareto_front
):

    if len(pareto_front) == 0:

        raise ValueError(
            "Le front de Pareto ne peut pas être vide."
        )

    objective_count = len(
        pareto_front[0].objective_vector
    )

    ideal_point = []
    nadir_point = []

    for objective_index in range(
        objective_count
    ):

        objective_values = []

        for evaluation in pareto_front:

            objective_values.append(
                evaluation.objective_vector[
                    objective_index
                ]
            )

        ideal_point.append(
            min(objective_values)
        )

        nadir_point.append(
            max(objective_values)
        )

    return (
        ideal_point,
        nadir_point
    )


# Cette fonction vérifie les poids contextuels.
#
# Dans la modélisation :
#
# w_k >= 0
# somme(w_k) = 1
#
# Cette fonction correspond à DM-EQ107.
#
# Les relations DM-EQ108 à DM-EQ110
# décrivent les monotonicités que la table de politique
# devra respecter.
#
# Le code ne crée aucun coefficient arbitraire.
# Il consomme seulement une liste déjà validée.
def validate_contextual_weights(
    contextual_weights,
    epsilon
):

    if contextual_weights is None:

        raise ValueError(
            "Les poids contextuels doivent être "
            "définis et validés avant la sélection."
        )

    if len(contextual_weights) != 4:

        raise ValueError(
            "Il faut exactement quatre poids contextuels."
        )

    validated_weights = []

    for weight in contextual_weights:

        if weight < 0:

            raise ValueError(
                "Les poids contextuels "
                "ne peuvent pas être négatifs."
            )

        validated_weights.append(
            float(weight)
        )

    weight_sum = sum(
        validated_weights
    )

    if abs(weight_sum - 1.0) > epsilon:

        raise ValueError(
            "La somme des poids contextuels doit être égale à 1."
        )

    return validated_weights


# Cette fonction calcule le score
# de Tchebychev pondéré d'une décision.
#
# Dans la modélisation :
#
# score(D) =
#     max_k [
#         w_k
#         * (f_k(D) - f_ideal_k)
#         / (f_nadir_k - f_ideal_k)
#     ]
#
# avec la convention : si (f_nadir_k - f_ideal_k) est
# numériquement nul (à epsilon près), la dimension k est
# neutre (contribution 0) plutôt que divisée.
#
# Cette fonction correspond à DM-EQ106.
#
# ----------------------------------------------------------
# CORRECTION STEP8 (voir docs/correction_tchebycheff/01_CODE_AUDIT/
# STEP8_PARETO_TCHEBYCHEFF_DIAGNOSTIC.md pour la démonstration
# complète, chiffrée sur le code réel, avant cette correction) :
#
# La version précédente ajoutait epsilon au dénominateur sur
# LES QUATRE dimensions, systématiquement, y compris quand le
# span (nadir_k - ideal_k) était normal. Cela introduisait un
# biais dépendant de l'échelle propre à chaque objectif (span
# différent pour l'énergie, la latence, l'authentification, la
# clé), capable de casser une égalité mathématique réelle entre
# deux scores de Tchebycheff -- et donc de contourner
# silencieusement le tie-break documenté (DM-EQ107 :
# FAR -> énergie -> latence -> nom, cf. build_tie_break_key
# ci-dessous). Mesuré sur la campagne principale (poids égaux,
# S1-S5, 3 graines) : ce contournement se produit dans 7249 des
# 22500 périodes testées (~32 %), à chaque fois qu'un front de
# Pareto à deux membres atteint structurellement le même score
# maximal sous poids égaux.
#
# epsilon garde désormais son rôle initial de SEUIL de
# détection d'un span numériquement dégénéré (ideal == nadir
# sur cette dimension pour l'ensemble du front), et non de
# terme de lissage ajouté partout. Quand span == 0, toutes les
# décisions du front partagent la même valeur sur cette
# dimension : le numérateur (f_k(D) - ideal_k) vaut alors aussi
# 0, et la contribution de cette dimension est neutre (0) --
# ce cas donnait déjà 0 avec l'ancienne formule (0 / epsilon
# = 0), la correction ne change donc rien à ce cas précis, elle
# supprime uniquement le biais introduit sur les spans non nuls.
def calculate_tchebycheff_score(
    objective_vector,
    contextual_weights,
    ideal_point,
    nadir_point,
    epsilon
):

    if epsilon <= 0:

        raise ValueError(
            "L'epsilon de Tchebychev "
            "doit être strictement positif."
        )

    vector_length = len(
        objective_vector
    )

    if (
        len(contextual_weights) != vector_length
        or len(ideal_point) != vector_length
        or len(nadir_point) != vector_length
    ):

        raise ValueError(
            "Les vecteurs de Tchebychev "
            "doivent avoir la même taille."
        )

    weighted_distances = []

    for index in range(
        vector_length
    ):

        span = (
            nadir_point[index]
            - ideal_point[index]
        )

        # span numériquement dégénéré : dimension neutre,
        # jamais de division par une quantité quasi nulle.
        if abs(span) <= epsilon:

            normalized_distance = 0.0

        else:

            numerator = (
                objective_vector[index]
                - ideal_point[index]
            )

            normalized_distance = (
                numerator
                / span
            )

        weighted_distance = (
            contextual_weights[index]
            * normalized_distance
        )

        weighted_distances.append(
            weighted_distance
        )

    score = max(
        weighted_distances
    )

    return score


# Cette fonction retourne les valeurs utilisées
# pour le bris d'égalité.
#
# L'ordre imposé par la modélisation est :
#
# 1. FAR la plus faible ;
# 2. énergie la plus faible ;
# 3. latence la plus faible ;
# 4. ordre lexicographique des actions.
def build_tie_break_key(
    evaluation
):

    far = (
        evaluation.authentication_metrics.far
    )

    energy = (
        evaluation.cost_metrics.expected_energy_j
    )

    latency = (
        evaluation.cost_metrics.normalized_latency
    )

    decision_name = (
        evaluation.decision.get_name()
    )

    return (
        far,
        energy,
        latency,
        decision_name
    )


# Cette fonction applique Tchebychev
# et le bris d'égalité.
def select_from_pareto_front(
    pareto_front,
    contextual_weights,
    epsilon,
    score_tolerance
):

    if len(pareto_front) == 0:

        raise ValueError(
            "Le front de Pareto ne peut pas être vide."
        )

    if score_tolerance is None:

        raise ValueError(
            "La tolérance de score doit être définie."
        )

    if score_tolerance < 0:

        raise ValueError(
            "La tolérance de score "
            "ne peut pas être négative."
        )

    validated_weights = (
        validate_contextual_weights(
            contextual_weights,
            epsilon
        )
    )

    (
        ideal_point,
        nadir_point
    ) = calculate_ideal_and_nadir_points(
        pareto_front
    )

    # On calcule et on enregistre
    # le score de chaque point du front.
    for evaluation in pareto_front:

        evaluation.tchebycheff_score = (
            calculate_tchebycheff_score(
                objective_vector=(
                    evaluation.objective_vector
                ),
                contextual_weights=(
                    validated_weights
                ),
                ideal_point=ideal_point,
                nadir_point=nadir_point,
                epsilon=epsilon
            )
        )

    best_score = min(
        evaluation.tchebycheff_score
        for evaluation in pareto_front
    )

    tied_evaluations = []

    for evaluation in pareto_front:

        if (
            abs(
                evaluation.tchebycheff_score
                - best_score
            )
            <= score_tolerance
        ):

            tied_evaluations.append(
                evaluation
            )

    # min utilise successivement les quatre éléments
    # de la clé de bris d'égalité.
    selected_evaluation = min(
        tied_evaluations,
        key=build_tie_break_key
    )

    return (
        selected_evaluation,
        ideal_point,
        nadir_point,
        validated_weights
    )


# ================================================================
# 8. FONCTIONNEMENT COMPLET DU DECISION MAKER
# ================================================================


# Cette fonction exécute tout le Decision Maker.
#
# Elle suit l'algorithme officiel :
#
# 1. évaluer les huit décisions ;
# 2. construire l'ensemble admissible ;
# 3. refuser si cet ensemble est vide ;
# 4. calculer le front de Pareto exact ;
# 5. appliquer Tchebychev ;
# 6. retourner une décision explicable.
def run_decision_maker(
    context,
    parameters,
    rho_ab,
    variation_feasible=None,
    k2_protocol=None,
    contextual_weights=None,
    enforce_far_floor=True
):

    # Les deux tolérances sont des paramètres
    # de politique qui doivent être définis.
    if parameters.dominance_tolerance is None:

        raise ValueError(
            "dominance_tolerance doit être définie "
            "avant d'exécuter le Decision Maker."
        )

    if parameters.score_tolerance is None:

        raise ValueError(
            "score_tolerance doit être définie "
            "avant d'exécuter le Decision Maker."
        )

    # Une liste fournie directement a priorité.
    #
    # Sinon, on utilise la politique
    # enregistrée dans parameters.py.
    if contextual_weights is None:

        contextual_weights = (
            parameters.contextual_weights
        )

    # On valide les poids avant les calculs.
    validated_weights = (
        validate_contextual_weights(
            contextual_weights,
            parameters.tchebycheff_epsilon
        )
    )

    (
        all_evaluations,
        rejection_journal
    ) = evaluate_all_decisions(
        context=context,
        parameters=parameters,
        rho_ab=rho_ab,
        variation_feasible=variation_feasible,
        k2_protocol=k2_protocol,
        enforce_far_floor=enforce_far_floor
    )

    admissible_evaluations = []

    for evaluation in all_evaluations:

        if evaluation.admissible:

            admissible_evaluations.append(
                evaluation
            )

    # DM-EQ103 :
    #
    # si l'ensemble admissible est vide,
    # le refus ou le mode de secours
    # doit être explicite.
    if len(admissible_evaluations) == 0:

        return DecisionMakerResult(
            context=context,
            all_evaluations=all_evaluations,
            admissible_evaluations=[],
            pareto_front=[],
            rejection_journal=(
                rejection_journal
            ),
            contextual_weights=(
                validated_weights
            ),
            ideal_point=None,
            nadir_point=None,
            selected_evaluation=None,
            refusal_of_service=True,
            fallback_mode_used=(
                parameters.fallback_mode
            ),
            explanation=(
                "Aucune décision n'est admissible. "
                "Le système applique le mode : "
                + str(parameters.fallback_mode)
                + "."
            )
        )

    pareto_front = calculate_pareto_front(
        admissible_evaluations,
        parameters.dominance_tolerance
    )

    (
        selected_evaluation,
        ideal_point,
        nadir_point,
        validated_weights
    ) = select_from_pareto_front(
        pareto_front=pareto_front,
        contextual_weights=(
            validated_weights
        ),
        epsilon=(
            parameters.tchebycheff_epsilon
        ),
        score_tolerance=(
            parameters.score_tolerance
        )
    )

    explanation = (
        "La décision "
        + selected_evaluation.decision.get_name()
        + " est admissible, appartient au front de Pareto "
        + "et minimise le score de Tchebychev après "
        + "application du bris d'égalité."
    )

    return DecisionMakerResult(
        context=context,
        all_evaluations=all_evaluations,
        admissible_evaluations=(
            admissible_evaluations
        ),
        pareto_front=pareto_front,
        rejection_journal=rejection_journal,
        contextual_weights=validated_weights,
        ideal_point=ideal_point,
        nadir_point=nadir_point,
        selected_evaluation=(
            selected_evaluation
        ),
        refusal_of_service=False,
        fallback_mode_used=None,
        explanation=explanation
    )
