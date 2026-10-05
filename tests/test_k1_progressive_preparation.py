# Ce fichier teste la correction scientifique K1a/K1b
# décrite dans :
# results/three_scenarios_explicit_analysis/
# k1a_k1b_model_consistency_audit.md
#
# Il couvre : l'initialisation des compteurs, le calcul
# du reliquat de mesures, l'accumulation opportuniste de
# K1a, l'émission incrémentale des sondages K1b sous
# contrainte de duty-cycle, la séparation préparation /
# activation, et la progression réelle de K1a/K1b dans
# les trois scénarios de la thèse (cryptopériode nominale).
import unittest

from unittest.mock import patch


from physec_dm.models import (
    AuthenticationAction,
    AuthenticationMetrics,
    ChannelMetrics,
    Context,
    CostMetrics,
    Decision,
    DecisionEvaluation,
    DecisionMakerResult,
    KeyAction,
    KeyMetrics,
    MissionState
)

from physec_dm.parameters import Parameters

from physec_dm.key_generation import (
    calculate_key_metrics,
    calculate_remaining_measurements
)

from physec_dm.energy_latency import (
    calculate_k1a_incremental_costs,
    calculate_k1b_incremental_costs,
    calculate_probe_energy,
    calculate_time_on_air
)

from physec_dm.decision_maker import (
    evaluate_decision,
    run_decision_maker
)

from physec_dm.mission import (
    create_initial_mission_state,
    create_mission_context,
    create_random_generator,
    run_mission_step,
    update_key_state
)

from physec_dm.thesis_scenarios import (
    apply_scenario_overrides_for_validation,
    build_thesis_scenarios,
    build_three_scenario_parameters
)


# ================================================================
# Outils partagés à ce fichier de test uniquement.
# ================================================================


def create_test_parameters():

    parameters = Parameters()

    parameters.mean_snr_db = 20.0
    parameters.shadowing_std_db = 0.0

    parameters.critical_message_probability = 0.0
    parameters.mallory_attempt_probability = 0.0

    parameters.minimum_deadline_s = 1.0
    parameters.security_strength_bits = 128

    parameters.mac_cycles = 32000
    parameters.challenge_response_latency_s = 4.0

    parameters.sensing_energy_j = 0.001
    parameters.application_energy_j = 0.002
    parameters.receive_windows_energy_j = 0.003
    parameters.sleep_energy_j = 0.004

    parameters.raw_bit_count = 128
    parameters.reconciliation_cycles_per_bit = 100
    parameters.privacy_amplification_cycles = 6400
    parameters.reconciliation_message_energy_j = 0.005
    parameters.reconciliation_message_latency_s = 0.5

    parameters.dominance_tolerance = 1e-12
    parameters.score_tolerance = 1e-12
    parameters.contextual_weights = [
        0.25,
        0.25,
        0.25,
        0.25
    ]

    return parameters


def create_state(
    key_age_s=0.0,
    messages_with_current_key=0,
    k1a_measurements_collected=0,
    k1b_measurements_collected=0,
    candidate_key_ready=False,
    candidate_key_action=None
):

    return MissionState(
        step_index=0,
        time_s=0.0,
        battery_energy_j=28512.0,
        key_age_s=key_age_s,
        messages_with_current_key=(
            messages_with_current_key
        ),
        current_key_identifier="KEY-001",
        remaining_duty_cycle_airtime_s=10.0,
        k1a_measurements_collected=(
            k1a_measurements_collected
        ),
        k1b_measurements_collected=(
            k1b_measurements_collected
        ),
        candidate_key_ready=candidate_key_ready,
        candidate_key_action=candidate_key_action
    )


def create_channel_metrics():

    return ChannelMetrics(
        snr_db=20.0,
        snr_linear=100.0,
        doppler_hz=0.0,
        temporal_correlation=1.0,
        noise_correlation=0.75,
        rho_ab=0.95
    )


def create_authentication_metrics(
    action=AuthenticationAction.A1
):

    return AuthenticationMetrics(
        authentication_action=action,
        far=0.001,
        frr=0.0,
        mac_forgery_probability=2 ** (-64),
        total_false_acceptance_probability=0.001,
        authentication_robustness=0.999,
        alice_fallback_probability=0.0,
        mallory_fallback_probability=0.0
    )


def create_cost_metrics():

    return CostMetrics(
        base_energy_j=0.01,
        authentication_security_energy_j=0.0,
        key_security_energy_j=0.0,
        security_energy_j=0.0,
        total_energy_j=0.01,
        authentication_latency_s=0.001,
        prudent_authentication_latency_s=0.001,
        key_latency_s=0.0,
        normalized_latency=0.01,
        airtime_s=0.0,
        expected_energy_j=0.01,
        worst_case_energy_j=0.01
    )


# Cette fonction construit un DecisionMakerResult de test
# où la décision sélectionnée est fournie explicitement,
# et où les key_metrics de K1a/K1b (nécessaires à
# find_key_metrics_for_action) utilisent les VRAIES
# fonctions de key_generation.py plutôt que des valeurs
# inventées.
def create_decision_result(
    context,
    selected_key_action,
    rho_ab=0.95,
    k1a_collected=0,
    k1b_collected=0,
    legitimate_message_served=True
):

    parameters = create_test_parameters()

    k1a_metrics = calculate_key_metrics(
        key_action=KeyAction.K1A,
        parameters=parameters,
        rho_ab=rho_ab,
        key_age_s=context.key_age_s,
        messages_with_current_key=(
            context.messages_with_current_key
        ),
        variation_feasible=True,
        collected_measurements=k1a_collected
    )

    k1b_metrics = calculate_key_metrics(
        key_action=KeyAction.K1B,
        parameters=parameters,
        rho_ab=rho_ab,
        key_age_s=context.key_age_s,
        messages_with_current_key=(
            context.messages_with_current_key
        ),
        variation_feasible=True,
        collected_measurements=k1b_collected
    )

    k1a_evaluation = DecisionEvaluation(
        Decision(AuthenticationAction.A1, KeyAction.K1A)
    )
    k1a_evaluation.key_metrics = k1a_metrics
    k1a_evaluation.authentication_metrics = (
        create_authentication_metrics()
    )

    k1b_evaluation = DecisionEvaluation(
        Decision(AuthenticationAction.A1, KeyAction.K1B)
    )
    k1b_evaluation.key_metrics = k1b_metrics
    k1b_evaluation.authentication_metrics = (
        create_authentication_metrics()
    )

    selected_evaluation = None

    if selected_key_action is not None:

        selected_evaluation = DecisionEvaluation(
            Decision(
                AuthenticationAction.A1,
                selected_key_action
            )
        )

        selected_evaluation.authentication_metrics = (
            create_authentication_metrics()
        )

        if selected_key_action == KeyAction.K1A:

            selected_evaluation.key_metrics = k1a_metrics

        elif selected_key_action == KeyAction.K1B:

            selected_evaluation.key_metrics = k1b_metrics

        else:

            selected_evaluation.key_metrics = (
                calculate_key_metrics(
                    key_action=selected_key_action,
                    parameters=parameters,
                    key_age_s=context.key_age_s,
                    messages_with_current_key=(
                        context.messages_with_current_key
                    )
                )
            )

        selected_evaluation.admissible = True

    all_evaluations = [
        k1a_evaluation,
        k1b_evaluation
    ]

    if selected_evaluation is not None:

        all_evaluations.append(
            selected_evaluation
        )

    return DecisionMakerResult(
        context=context,
        all_evaluations=all_evaluations,
        admissible_evaluations=(
            [selected_evaluation]
            if selected_evaluation is not None
            else []
        ),
        pareto_front=(
            [selected_evaluation]
            if selected_evaluation is not None
            else []
        ),
        rejection_journal=[],
        contextual_weights=[
            0.25,
            0.25,
            0.25,
            0.25
        ],
        ideal_point=[0.0, 0.0, -1.0, -1.0],
        nadir_point=[1.0, 1.0, 0.0, 0.0],
        selected_evaluation=selected_evaluation,
        refusal_of_service=(
            selected_evaluation is None
        ),
        fallback_mode_used=(
            None
            if selected_evaluation is not None
            else "refuse"
        ),
        explanation="Décision de test."
    )


# ================================================================
# 1. MissionState : compteurs initiaux
# ================================================================


class TestMissionStateInitialCounters(unittest.TestCase):

    # Test demandé n°1 :
    # MissionState initialise les compteurs à zéro.
    def test_counters_start_at_zero(self):

        state = create_initial_mission_state(
            parameters=create_test_parameters(),
            initial_duty_cycle_airtime_s=10.0
        )

        self.assertEqual(
            state.k1a_measurements_collected,
            0
        )

        self.assertEqual(
            state.k1b_measurements_collected,
            0
        )

        self.assertFalse(
            state.candidate_key_ready
        )

        self.assertIsNone(
            state.candidate_key_action
        )

    def test_negative_k1a_counter_is_rejected(self):

        with self.assertRaises(ValueError):

            create_state(
                k1a_measurements_collected=-1
            )

    def test_ready_without_action_is_rejected(self):

        with self.assertRaises(ValueError):

            create_state(
                candidate_key_ready=True,
                candidate_key_action=None
            )

    def test_action_without_ready_is_rejected(self):

        with self.assertRaises(ValueError):

            create_state(
                candidate_key_ready=False,
                candidate_key_action=KeyAction.K1A
            )


# ================================================================
# 2. Reliquat de mesures (key_generation.py)
# ================================================================


class TestRemainingMeasurements(unittest.TestCase):

    # Test demandé n°4 (partie key_generation) :
    # le reliquat utilise bien required - collected.
    def test_remaining_uses_shortfall(self):

        self.assertEqual(
            calculate_remaining_measurements(
                required_measurements=10,
                collected_measurements=3
            ),
            7
        )

    # Test demandé n°15 :
    # aucun reliquat ne devient négatif, même si
    # collected dépasse required (canal amélioré
    # entre deux périodes).
    def test_remaining_never_negative(self):

        self.assertEqual(
            calculate_remaining_measurements(
                required_measurements=5,
                collected_measurements=9
            ),
            0
        )

    def test_remaining_matches_required_when_nothing_collected(self):

        self.assertEqual(
            calculate_remaining_measurements(
                required_measurements=42,
                collected_measurements=0
            ),
            42
        )

    # calculate_key_metrics doit exposer collected_measurements
    # et remaining_measurements de façon cohérente.
    def test_key_metrics_exposes_remaining_measurements(self):

        parameters = create_test_parameters()

        key_metrics = calculate_key_metrics(
            key_action=KeyAction.K1A,
            parameters=parameters,
            rho_ab=0.95,
            variation_feasible=True,
            collected_measurements=2
        )

        self.assertEqual(
            key_metrics.collected_measurements,
            2
        )

        self.assertEqual(
            key_metrics.remaining_measurements,
            key_metrics.required_measurements - 2
        )


# ================================================================
# 3. Coûts incrémentaux K1a / K1b (energy_latency.py)
# ================================================================


class TestIncrementalCosts(unittest.TestCase):

    # Test demandé n°4 (partie energy_latency) : K1a
    # n'engage aucune énergie tant que la collecte
    # n'est pas terminée (mesure opportuniste gratuite).
    def test_k1a_incremental_cost_is_free_mid_collection(self):

        parameters = create_test_parameters()

        costs = calculate_k1a_incremental_costs(
            remaining_measurements=5,
            parameters=parameters,
            required_measurements=20
        )

        self.assertEqual(
            costs["energy_j"],
            0.0
        )

        self.assertEqual(
            costs["airtime_s"],
            0.0
        )

    def test_k1a_incremental_cost_at_completion(self):

        parameters = create_test_parameters()

        costs = calculate_k1a_incremental_costs(
            remaining_measurements=0,
            parameters=parameters,
            required_measurements=10
        )

        self.assertGreater(
            costs["energy_j"],
            0.0
        )

    # Test demandé n°5/6 (partie coût) : le sondage K1b
    # n'a jamais un coût cumulé de tous les sondages
    # restants — seulement UN sondage par période.
    def test_k1b_incremental_cost_is_a_single_probe(self):

        parameters = create_test_parameters()

        costs = calculate_k1b_incremental_costs(
            remaining_measurements=500,
            parameters=parameters,
            required_measurements=500
        )

        self.assertAlmostEqual(
            costs["energy_j"],
            calculate_probe_energy(parameters),
            places=12
        )

        self.assertAlmostEqual(
            costs["airtime_s"],
            calculate_time_on_air(
                parameters.probe_payload_bytes,
                parameters
            ),
            places=12
        )

    # Test demandé n°7 : le rythme dedicated_probe_interval_s
    # est dérivé de T_air / duty_cycle_fraction : un seul
    # sondage par période reste donc, par construction,
    # toujours soutenable par la recharge du duty-cycle.
    def test_single_probe_airtime_is_sustainable_by_recharge(self):

        parameters = create_test_parameters()

        probe_airtime_s = calculate_time_on_air(
            parameters.probe_payload_bytes,
            parameters
        )

        sustainable_rate = (
            probe_airtime_s
            / parameters.dedicated_probe_interval_s
        )

        self.assertAlmostEqual(
            sustainable_rate,
            parameters.duty_cycle_fraction,
            places=6
        )


# ================================================================
# 4. Préparation vs activation (update_key_state)
# ================================================================


class TestPreparationDoesNotActivate(unittest.TestCase):

    # Test demandé n°8 : la préparation (candidate_key_ready
    # encore faux) n'active pas prématurément la nouvelle clé.
    def test_k1a_selected_without_ready_candidate_does_not_reset(self):

        updated = update_key_state(
            previous_key_age_s=600.0,
            previous_message_count=10,
            current_key_identifier="KEY-001",
            key_action=KeyAction.K1A,
            legitimate_message_served=True,
            message_period_s=60.0,
            renewal_required=True,
            candidate_key_ready=False,
            candidate_key_action=None
        )

        self.assertFalse(
            updated["key_renewed"]
        )

        self.assertEqual(
            updated["key_age_s"],
            660.0
        )

        self.assertEqual(
            updated["messages_with_current_key"],
            11
        )

    # candidate_key_ready=True mais pour l'AUTRE mécanisme :
    # aucune activation ne doit avoir lieu non plus.
    def test_ready_candidate_of_other_action_does_not_activate(self):

        updated = update_key_state(
            previous_key_age_s=600.0,
            previous_message_count=10,
            current_key_identifier="KEY-001",
            key_action=KeyAction.K1A,
            legitimate_message_served=True,
            message_period_s=60.0,
            renewal_required=True,
            candidate_key_ready=True,
            candidate_key_action=KeyAction.K1B
        )

        self.assertFalse(
            updated["key_renewed"]
        )

    # renewal_required=False : même une clé candidate prête
    # ne doit pas être activée par anticipation.
    def test_ready_candidate_without_renewal_required_does_not_activate(self):

        updated = update_key_state(
            previous_key_age_s=600.0,
            previous_message_count=10,
            current_key_identifier="KEY-001",
            key_action=KeyAction.K1A,
            legitimate_message_served=True,
            message_period_s=60.0,
            renewal_required=False,
            candidate_key_ready=True,
            candidate_key_action=KeyAction.K1A
        )

        self.assertFalse(
            updated["key_renewed"]
        )

    # Test demandé n°9 : une clé candidate prête PEUT être
    # activée lorsque renewal_required=True et que l'action
    # correspond.
    def test_ready_candidate_activates_when_renewal_required(self):

        updated = update_key_state(
            previous_key_age_s=6000.0,
            previous_message_count=100,
            current_key_identifier="KEY-001",
            key_action=KeyAction.K1A,
            legitimate_message_served=True,
            message_period_s=60.0,
            renewal_required=True,
            candidate_key_ready=True,
            candidate_key_action=KeyAction.K1A
        )

        self.assertTrue(
            updated["key_renewed"]
        )

        self.assertEqual(
            updated["key_age_s"],
            0.0
        )

        self.assertEqual(
            updated["messages_with_current_key"],
            0
        )

        self.assertEqual(
            updated["current_key_identifier"],
            "KEY-002"
        )

    # K2 reste instantané, inchangé, dès lors qu'il est
    # sélectionnable (toujours sous renewal_required=True).
    def test_k2_still_activates_instantly(self):

        updated = update_key_state(
            previous_key_age_s=6000.0,
            previous_message_count=100,
            current_key_identifier="KEY-001",
            key_action=KeyAction.K2,
            legitimate_message_served=True,
            message_period_s=60.0,
            renewal_required=True
        )

        self.assertTrue(
            updated["key_renewed"]
        )


# ================================================================
# 5. Accumulation dans run_mission_step (mocké, déterministe)
# ================================================================


class TestRunMissionStepAccumulation(unittest.TestCase):

    def run_step_with_mocked_decision(
        self,
        state,
        selected_key_action,
        k1a_collected=None,
        k1b_collected=None,
        legitimate_message_served=True
    ):

        parameters = create_test_parameters()

        channel_metrics = create_channel_metrics()

        context = create_mission_context(
            state=state,
            channel_metrics=channel_metrics,
            criticality=0,
            rff_profile_available=True,
            compromise_suspected=False,
            key_context_metrics=calculate_key_metrics(
                key_action=KeyAction.K0,
                parameters=parameters,
                key_age_s=state.key_age_s,
                messages_with_current_key=(
                    state.messages_with_current_key
                )
            )
        )

        decision_result = create_decision_result(
            context=context,
            selected_key_action=selected_key_action,
            k1a_collected=(
                k1a_collected
                if k1a_collected is not None
                else state.k1a_measurements_collected
            ),
            k1b_collected=(
                k1b_collected
                if k1b_collected is not None
                else state.k1b_measurements_collected
            )
        )

        realized_costs = {
            "energy_j": 0.01,
            "airtime_s": 0.0,
            "alice_fallback_triggered": False
        }

        with patch(
            "physec_dm.mission.calculate_channel_metrics",
            return_value=channel_metrics
        ):

            with patch(
                "physec_dm.mission.run_decision_maker",
                return_value=decision_result
            ):

                with patch(
                    "physec_dm.mission."
                    "calculate_realized_alice_costs",
                    return_value=realized_costs
                ):

                    with patch(
                        "physec_dm.mission.evaluate_mallory",
                        return_value={
                            "accepted": False,
                            "authentication_metrics": None
                        }
                    ):

                        return run_mission_step(
                            state=state,
                            parameters=parameters,
                            random_generator=(
                                create_random_generator(1)
                            ),
                            maximum_duty_cycle_airtime_s=10.0,
                            duty_cycle_recharge_s=0.6,
                            observed_snr_db=20.0,
                            real_snr_db=20.0,
                            criticality=0,
                            mallory_attempted=False
                        )

    # Test demandé n°2 : une mesure K1a valide (échange
    # servi, PHY faisable) augmente le compteur, même si
    # K1a n'est pas l'action sélectionnée (elle est
    # opportuniste).
    def test_k1a_counter_increments_on_served_exchange(self):

        state = create_state()

        step_result = self.run_step_with_mocked_decision(
            state=state,
            selected_key_action=KeyAction.K0
        )

        self.assertTrue(
            step_result.legitimate_message_served
        )

        self.assertEqual(
            step_result.k1a_measurements_before,
            0
        )

        self.assertEqual(
            step_result.k1a_measurements_after,
            1
        )

    # Test demandé n°3 : un refus de service (aucune
    # décision servie) n'augmente pas le compteur K1a.
    def test_k1a_counter_frozen_on_refusal(self):

        state = create_state()

        step_result = self.run_step_with_mocked_decision(
            state=state,
            selected_key_action=None
        )

        self.assertFalse(
            step_result.legitimate_message_served
        )

        self.assertEqual(
            step_result.k1a_measurements_after,
            0
        )

    # Test demandé n°6 : K1b sélectionnée et servie
    # incrémente le compteur d'UN sondage.
    def test_k1b_counter_increments_when_selected_and_served(self):

        state = create_state()

        step_result = self.run_step_with_mocked_decision(
            state=state,
            selected_key_action=KeyAction.K1B
        )

        self.assertEqual(
            step_result.k1b_measurements_before,
            0
        )

        self.assertEqual(
            step_result.k1b_measurements_after,
            1
        )

    # Test demandé n°5 : si K1b n'est PAS la décision
    # sélectionnée (par exemple parce que le budget de
    # duty-cycle l'a rendue inadmissible en amont, dans le
    # Decision Maker), aucun sondage n'est comptabilisé.
    def test_k1b_counter_frozen_when_not_selected(self):

        state = create_state()

        step_result = self.run_step_with_mocked_decision(
            state=state,
            selected_key_action=KeyAction.K0
        )

        self.assertEqual(
            step_result.k1b_measurements_after,
            0
        )

    # Test demandé n°10 : l'activation remet correctement
    # les compteurs à zéro.
    def test_activation_resets_counters(self):

        # key_age_s et messages_with_current_key sont
        # choisis pour dépasser renewal_trigger (0,60) sous
        # la cryptopériode NOMINALE des paramètres par
        # défaut (maximum_key_age_s=86400,
        # maximum_messages_per_key=1000), afin que
        # create_mission_context calcule
        # renewal_required=True.
        parameters = create_test_parameters()

        reference_metrics = calculate_key_metrics(
            key_action=KeyAction.K1A,
            parameters=parameters,
            rho_ab=0.95,
            variation_feasible=True,
            collected_measurements=0
        )

        state = create_state(
            key_age_s=60000.0,
            messages_with_current_key=700,
            k1a_measurements_collected=(
                reference_metrics.required_measurements
            ),
            candidate_key_ready=True,
            candidate_key_action=KeyAction.K1A
        )

        step_result = self.run_step_with_mocked_decision(
            state=state,
            selected_key_action=KeyAction.K1A,
            k1a_collected=(
                reference_metrics.required_measurements
            )
        )

        self.assertEqual(
            step_result.state_after.key_age_s,
            0.0
        )

        self.assertEqual(
            step_result.k1a_measurements_after,
            0
        )

        self.assertFalse(
            step_result.candidate_key_ready_after
        )

        self.assertIsNone(
            step_result.state_after.candidate_key_action
        )

    # Aucun compteur ne dépasse required_measurements
    # (test demandé n°15, volet accumulation).
    def test_k1a_counter_never_exceeds_required(self):

        parameters = create_test_parameters()

        reference_metrics = calculate_key_metrics(
            key_action=KeyAction.K1A,
            parameters=parameters,
            rho_ab=0.95,
            variation_feasible=True,
            collected_measurements=0
        )

        state = create_state(
            k1a_measurements_collected=(
                reference_metrics.required_measurements
            )
        )

        step_result = self.run_step_with_mocked_decision(
            state=state,
            selected_key_action=KeyAction.K0,
            k1a_collected=(
                reference_metrics.required_measurements
            )
        )

        self.assertLessEqual(
            step_result.k1a_measurements_after,
            reference_metrics.required_measurements
        )


# ================================================================
# 6. Intégration réelle : progression dans S1 / S2 / S3
# ================================================================


class TestRealScenarioProgression(unittest.TestCase):

    def setUp(self):

        self.base_parameters = (
            build_three_scenario_parameters()
        )

        self.scenarios = build_thesis_scenarios(
            parameters=self.base_parameters,
            max_steps=300
        )

    def get_scenario(self, scenario_id):

        return next(
            scenario
            for scenario in self.scenarios
            if scenario["scenario_id"] == scenario_id
        )

    # Test demandé n°11 : S1 rejette K1a/K1b pour cause
    # physique (variation_feasible=False), même avec la
    # nouvelle logique de préparation — ce test utilise les
    # véritables classes de models.py et le véritable
    # Decision Maker, sans aucun contournement.
    def test_s1_rejects_k1_for_physical_cause(self):

        scenario = self.get_scenario(
            "S1-DEGRADED-CHANNEL"
        )

        parameters = (
            apply_scenario_overrides_for_validation(
                self.base_parameters,
                scenario
            )
        )

        # renewal_required=True : sous la règle stricte
        # (95)-(96), K1a est rejetée dès les règles de
        # raisonnement (KEY_RENEWAL_NOT_REQUIRED) tant que le
        # renouvellement n'est pas requis. Pour isoler la
        # cause PHYSIQUE (variation_feasible=False, propre à
        # S1), il faut donc placer K1a dans un contexte où
        # elle franchit d'abord l'étape de raisonnement.
        context = Context(
            snr_db=parameters.mean_snr_db,
            doppler_hz=0.0,
            battery_energy_j=(
                parameters.initial_battery_energy_j
            ),
            criticality=0,
            key_age_s=0.0,
            messages_with_current_key=0,
            rff_profile_available=True,
            renewal_required=True,
            key_expired=False,
            compromise_suspected=False,
            key_deadline_s=24000.0,
            remaining_duty_cycle_airtime_s=36.0
        )

        # rho_ab=0.95 est choisi pour que
        # agreement_feasible soit VRAI (bonne corrélation) :
        # cela isole la cause du rejet sur
        # variation_feasible=False, propre à S1, plutôt que
        # de la confondre avec un désaccord KDR.
        result = run_decision_maker(
            context=context,
            parameters=parameters,
            rho_ab=0.95,
            variation_feasible=(
                scenario["variation_feasible"]
            ),
            k2_protocol=scenario["k2_protocol"]
        )

        k1a_evaluation = next(
            evaluation
            for evaluation in result.all_evaluations
            if evaluation.decision.key_action
            == KeyAction.K1A
        )

        self.assertFalse(
            k1a_evaluation.admissible
        )

        reason_codes = [
            rejection.reason_code
            for rejection in (
                k1a_evaluation.rejection_reasons
            )
        ]

        self.assertIn(
            "PHY_VARIATION_INFEASIBLE",
            reason_codes
        )

    # Tests demandés n°12 et n°13 : sous la cryptopériode
    # NOMINALE restaurée, K1a doit pouvoir progresser
    # (rester admissible, hors contrainte PHY) dans S2 et
    # S3, contrairement à l'ancienne cryptopériode
    # raccourcie (cf. audit, section 3.4).
    def check_k1a_can_progress(self, scenario_id):

        scenario = self.get_scenario(scenario_id)

        parameters = (
            apply_scenario_overrides_for_validation(
                self.base_parameters,
                scenario
            )
        )

        # Premier instant du renouvellement
        # (q_t = renewal_trigger), échéance maximale :
        # le cas le plus favorable pour juger de la
        # progression de K1a.
        key_age_s = (
            parameters.renewal_trigger
            * parameters.maximum_key_age_s
        )

        messages_with_current_key = (
            parameters.renewal_trigger
            * parameters.maximum_messages_per_key
        )

        context = Context(
            snr_db=parameters.mean_snr_db,
            doppler_hz=0.0,
            battery_energy_j=(
                parameters.initial_battery_energy_j
            ),
            criticality=0,
            key_age_s=key_age_s,
            messages_with_current_key=(
                messages_with_current_key
            ),
            rff_profile_available=True,
            renewal_required=True,
            key_expired=False,
            compromise_suspected=False,
            key_deadline_s=(
                (1 - parameters.renewal_trigger)
                * parameters.maximum_key_age_s
            ),
            remaining_duty_cycle_airtime_s=36.0,
            # La moitié des mesures est déjà accumulée :
            # représente une préparation en cours, commencée
            # avant le déclenchement du renouvellement.
            k1a_measurements_collected=0
        )

        result = run_decision_maker(
            context=context,
            parameters=parameters,
            rho_ab=0.95,
            variation_feasible=(
                scenario["variation_feasible"]
            ),
            k2_protocol=scenario["k2_protocol"]
        )

        k1a_evaluation = next(
            evaluation
            for evaluation in result.all_evaluations
            if evaluation.decision.key_action
            == KeyAction.K1A
            and evaluation.decision.authentication_action
            == AuthenticationAction.A1
        )

        # La cryptopériode nominale doit désormais
        # permettre à K1a de rester admissible dans ce cas
        # favorable (elle ne l'était plus du tout sous
        # l'ancienne cryptopériode raccourcie, cf. audit).
        self.assertTrue(
            k1a_evaluation.admissible,
            "K1a devrait être admissible sous la "
            "cryptopériode nominale pour "
            + scenario_id
            + " ; motifs observés : "
            + ", ".join(
                rejection.reason_code
                for rejection in (
                    k1a_evaluation.rejection_reasons
                )
            )
        )

    def test_s2_allows_k1a_progression(self):

        self.check_k1a_can_progress(
            "S2-RESOURCE-CONSTRAINED"
        )

    def test_s3_allows_k1a_progression(self):

        self.check_k1a_can_progress(
            "S3-HIGH-SECURITY-PRESSURE"
        )

    # Test demandé n°14 : S3 permet la progression de K1b
    # si le budget temporel (échéance) le permet — sous la
    # cryptopériode nominale, avec une préparation déjà
    # bien avancée (peu de sondages restants).
    def test_s3_allows_k1b_progression_when_nearly_complete(self):

        scenario = self.get_scenario(
            "S3-HIGH-SECURITY-PRESSURE"
        )

        parameters = (
            apply_scenario_overrides_for_validation(
                self.base_parameters,
                scenario
            )
        )

        key_age_s = (
            parameters.renewal_trigger
            * parameters.maximum_key_age_s
        )

        messages_with_current_key = (
            parameters.renewal_trigger
            * parameters.maximum_messages_per_key
        )

        # On calcule d'abord required_measurements réel
        # pour ce scénario, afin de placer la préparation
        # juste avant son terme (reliquat de 5 sondages).
        reference_metrics = calculate_key_metrics(
            key_action=KeyAction.K1B,
            parameters=parameters,
            rho_ab=0.95,
            variation_feasible=(
                scenario["variation_feasible"]
            ),
            collected_measurements=0
        )

        almost_done_collected = max(
            reference_metrics.required_measurements
            - 5,
            0
        )

        context = Context(
            snr_db=parameters.mean_snr_db,
            doppler_hz=0.0,
            battery_energy_j=(
                parameters.initial_battery_energy_j
            ),
            criticality=0,
            key_age_s=key_age_s,
            messages_with_current_key=(
                messages_with_current_key
            ),
            rff_profile_available=True,
            renewal_required=True,
            key_expired=False,
            compromise_suspected=False,
            key_deadline_s=(
                (1 - parameters.renewal_trigger)
                * parameters.maximum_key_age_s
            ),
            remaining_duty_cycle_airtime_s=36.0,
            k1b_measurements_collected=(
                almost_done_collected
            )
        )

        result = run_decision_maker(
            context=context,
            parameters=parameters,
            rho_ab=0.95,
            variation_feasible=(
                scenario["variation_feasible"]
            ),
            k2_protocol=scenario["k2_protocol"]
        )

        k1b_evaluation = next(
            evaluation
            for evaluation in result.all_evaluations
            if evaluation.decision.key_action
            == KeyAction.K1B
            and evaluation.decision.authentication_action
            == AuthenticationAction.A1
        )

        self.assertTrue(
            k1b_evaluation.admissible,
            "K1b devrait être admissible en fin de "
            "préparation pour S3 ; motifs observés : "
            + ", ".join(
                rejection.reason_code
                for rejection in (
                    k1b_evaluation.rejection_reasons
                )
            )
        )

        self.assertEqual(
            k1b_evaluation.key_metrics
            .remaining_measurements,
            5
        )


# ================================================================
# 4. Tests de reachability déterministes (validation du
#    retour à la règle stricte (95)-(96) demandée par
#    l'encadrante).
# ================================================================


class TestK1ReachabilityDeterministic(unittest.TestCase):

    # Test n°1 : K1a doit accumuler passivement AVANT que le
    # renouvellement soit requis, puis devenir sélectionnable
    # (activée) une fois r_t=1, sans jamais avoir été retournée
    # comme décision par le DM avant.
    def test_k1a_accumulates_then_becomes_selectable(self):

        parameters = create_test_parameters()

        # Une longueur de clé réduite garde le test rapide
        # (peu de mesures nécessaires) sans changer la
        # mécanique testée.
        parameters.key_length_bits = 8

        # Échéance de renouvellement atteinte après la
        # candidature K1a (voir calcul manuel en commentaire
        # de PR : avec rho_ab ≈ 0.95 et key_length_bits=8,
        # K1a devient prête vers la période 20-25 ; le
        # renouvellement est réglé pour se déclencher à la
        # période 30, laissant une marge confortable).
        parameters.maximum_key_age_s = 3000.0
        parameters.maximum_messages_per_key = 1000000
        parameters.renewal_trigger = 0.60
        parameters.message_period_s = 60.0

        # Aucun k2_protocol n'est fourni : K2 reste
        # inadmissible (MODEL_CALCULATION_ERROR), ce qui
        # isole la démonstration sur K1a face à K0/K1b.
        state = create_initial_mission_state(
            parameters,
            initial_duty_cycle_airtime_s=1000.0
        )

        random_generator = create_random_generator(
            seed=42
        )

        candidate_ready_step = None
        candidate_ready_during_renewal_required = None
        activation_step = None
        activation_key_action = None

        for step_index in range(60):

            step_result = run_mission_step(
                state=state,
                parameters=parameters,
                random_generator=random_generator,
                maximum_duty_cycle_airtime_s=1000.0,
                duty_cycle_recharge_s=1000.0,
                observed_snr_db=20.0,
                real_snr_db=20.0,
                criticality=0,
                mallory_attempted=False,
                variation_feasible=True
            )

            state = step_result.state_after

            if (
                candidate_ready_step is None
                and state.candidate_key_ready
                and state.candidate_key_action
                == KeyAction.K1A
            ):

                candidate_ready_step = step_index

                candidate_ready_during_renewal_required = (
                    step_result.context.renewal_required
                )

            if (
                activation_step is None
                and step_result.state_before
                .candidate_key_ready
                and step_result.state_before
                .candidate_key_action == KeyAction.K1A
                and state.key_age_s == 0.0
                and state.messages_with_current_key == 0
            ):

                activation_step = step_index

                selected_evaluation = (
                    step_result.decision_maker_result
                    .selected_evaluation
                )

                if selected_evaluation is not None:

                    activation_key_action = (
                        selected_evaluation
                        .decision
                        .key_action
                    )

            if activation_step is not None:

                break

        self.assertIsNotNone(
            candidate_ready_step,
            "K1a n'est jamais devenue prête pendant "
            "la préparation."
        )

        # Condition centrale du test : la préparation a
        # abouti AVANT que le renouvellement soit requis
        # (accumulation passive, jamais une décision K1a
        # retournée par le DM pendant cette phase).
        self.assertFalse(
            candidate_ready_during_renewal_required,
            "K1a candidate devrait être prête pendant une "
            "phase où renewal_required=False (collecte "
            "passive), pas après."
        )

        self.assertIsNotNone(
            activation_step,
            "K1a n'a jamais été activée après être "
            "devenue prête."
        )

        self.assertGreater(
            activation_step,
            candidate_ready_step
        )

        self.assertEqual(
            activation_key_action,
            KeyAction.K1A
        )

    # Test n°2 : K1b, isolée de la compétition avec K1a/K2
    # (évaluation directe d'une seule décision), doit payer
    # RÉELLEMENT chaque sondage tant qu'il reste des mesures,
    # rester admissible tout au long, puis finir par produire
    # une clé (remaining_measurements=0, coût de réconciliation
    # seul) lorsque canal, échéance et duty-cycle sont
    # favorables.
    def test_k1b_pays_each_probe_and_completes_when_favorable(
        self
    ):

        parameters = create_test_parameters()
        parameters.key_length_bits = 8

        decision_k1b = Decision(
            AuthenticationAction.A1,
            KeyAction.K1B
        )

        rho_ab = 0.95

        probe_energy_j = calculate_probe_energy(
            parameters
        )

        k1b_collected = 0
        total_probe_energy_paid_j = 0.0
        required_measurements = None
        steps_taken = 0

        while True:

            steps_taken += 1

            if steps_taken > 200:

                self.fail(
                    "K1b n'a jamais complété sa collecte "
                    "dans des conditions annoncées comme "
                    "favorables."
                )

            context = Context(
                snr_db=20.0,
                doppler_hz=0.0,
                battery_energy_j=28512.0,
                criticality=0,
                key_age_s=90000.0,
                messages_with_current_key=0,
                rff_profile_available=True,
                renewal_required=True,
                key_expired=True,
                compromise_suspected=False,
                # Échéance très généreuse : ce test isole
                # le paiement par sondage, pas la contrainte
                # d'échéance (voir test n°3 pour le cas
                # défavorable).
                key_deadline_s=1000000.0,
                remaining_duty_cycle_airtime_s=1000.0,
                k1b_measurements_collected=k1b_collected
            )

            evaluation = evaluate_decision(
                decision=decision_k1b,
                context=context,
                parameters=parameters,
                rho_ab=rho_ab,
                variation_feasible=True
            )

            self.assertTrue(
                evaluation.admissible,
                "K1b devrait rester admissible à chaque "
                "période sous des conditions favorables ; "
                "motifs observés : "
                + ", ".join(
                    rejection.reason_code
                    for rejection in (
                        evaluation.rejection_reasons
                    )
                )
            )

            required_measurements = (
                evaluation.key_metrics
                .required_measurements
            )

            remaining_measurements = (
                evaluation.key_metrics
                .remaining_measurements
            )

            if remaining_measurements > 0:

                # Chaque période non terminale doit payer
                # EXACTEMENT un sondage, jamais le cumul des
                # sondages restants.
                self.assertAlmostEqual(
                    evaluation.cost_metrics
                    .key_security_energy_j,
                    probe_energy_j,
                    places=9
                )

                total_probe_energy_paid_j += (
                    evaluation.cost_metrics
                    .key_security_energy_j
                )

                k1b_collected += 1

            else:

                # Collecte terminée : coût de
                # réconciliation seul, strictement inférieur
                # au coût d'un sondage supplémentaire.
                self.assertLess(
                    evaluation.cost_metrics
                    .key_security_energy_j,
                    probe_energy_j
                )

                break

        self.assertGreater(
            total_probe_energy_paid_j,
            0.0
        )

        self.assertEqual(
            k1b_collected,
            required_measurements
        )

    # Test n°3 : K1b doit être REJETÉE (contrainte
    # d'échéance) lorsque son achèvement ne peut pas
    # respecter l'échéance disponible, même si le canal et
    # le duty-cycle seraient par ailleurs favorables.
    def test_k1b_rejected_when_deadline_unreachable(self):

        parameters = create_test_parameters()
        parameters.key_length_bits = 8

        decision_k1b = Decision(
            AuthenticationAction.A1,
            KeyAction.K1B
        )

        rho_ab = 0.95

        # Échéance extrêmement courte devant le rythme des
        # sondages dédiés (dedicated_probe_interval_s) :
        # aucun nombre raisonnable de sondages ne peut
        # respecter cette échéance.
        context = Context(
            snr_db=20.0,
            doppler_hz=0.0,
            battery_energy_j=28512.0,
            criticality=0,
            key_age_s=90000.0,
            messages_with_current_key=0,
            rff_profile_available=True,
            renewal_required=True,
            key_expired=True,
            compromise_suspected=False,
            key_deadline_s=1.0,
            remaining_duty_cycle_airtime_s=1000.0,
            k1b_measurements_collected=0
        )

        evaluation = evaluate_decision(
            decision=decision_k1b,
            context=context,
            parameters=parameters,
            rho_ab=rho_ab
        )

        self.assertFalse(
            evaluation.admissible
        )

        reason_codes = [
            rejection.reason_code
            for rejection in (
                evaluation.rejection_reasons
            )
        ]

        self.assertIn(
            "KEY_DEADLINE_CONSTRAINT",
            reason_codes
        )


if __name__ == "__main__":

    unittest.main()
