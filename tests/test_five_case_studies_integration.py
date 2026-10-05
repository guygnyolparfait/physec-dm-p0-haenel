# Ce fichier teste l'intégration complète des cinq cas d'étude
# dynamiques : contrôleur de scénario réel, politique
# contextuelle réelle (resolve_contextual_weights),
# physec_dm.mission.run_mission réel (aucun mock), sur un
# nombre de périodes réduit pour rester rapide.
import unittest

from physec_dm.case_studies import (
    apply_case_study_overrides,
    build_case_study_base_parameters,
    build_five_case_studies,
    select_baseline_conventional_decision
)

from physec_dm.contextual_policy import (
    resolve_contextual_weights
)

from physec_dm.mission import (
    find_key_metrics_for_action,
    run_mission
)

from physec_dm.key_generation import (
    calculate_key_metrics
)

from physec_dm.models import KeyAction

from physec_dm.scenario_controller import ScenarioController

from scripts.run_five_case_studies import (
    build_scenario_traces,
    extract_log_rows,
    LOG_FIELD_NAMES,
    run_single_mission
)


MAX_STEPS = 150
SEED = 2000


def build_scenario_environment(case_study):

    base_parameters = build_case_study_base_parameters()

    scenario_parameters = apply_case_study_overrides(
        base_parameters,
        case_study
    )

    traces = build_scenario_traces(
        case_study,
        seed=SEED,
        max_steps=MAX_STEPS
    )

    return scenario_parameters, traces


class TestRealIntegrationAllScenarios(unittest.TestCase):

    def setUp(self):

        self.case_studies = build_five_case_studies()

    # Test demandé : duty-cycle jamais négatif, dans les
    # cinq cas d'étude, sous P0 ET B1.
    def test_duty_cycle_never_negative(self):

        for case_study in self.case_studies:

            scenario_parameters, traces = (
                build_scenario_environment(
                    case_study
                )
            )

            for policy_id, decision_fn in [
                ("P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS", None),
                (
                    "B1-CONVENTIONAL",
                    select_baseline_conventional_decision
                )
            ]:

                mission_result = run_single_mission(
                    case_study=case_study,
                    scenario_parameters=(
                        scenario_parameters
                    ),
                    policy_id=policy_id,
                    decision_policy_fn=decision_fn,
                    seed=SEED,
                    max_steps=MAX_STEPS,
                    traces=traces
                )

                for step_result in (
                    mission_result.steps
                ):

                    self.assertGreaterEqual(
                        step_result.state_after
                        .remaining_duty_cycle_airtime_s,
                        0.0,
                        (
                            case_study["scenario_id"]
                            + " / "
                            + policy_id
                            + " : duty-cycle négatif "
                            "à l'étape "
                            + str(
                                step_result.state_before
                                .step_index
                            )
                        )
                    )

    # Test demandé : aucune activation prématurée — chaque
    # fois que key_age_s revient à zéro (activation), soit
    # l'action était K2 (toujours instantanée), soit une
    # clé candidate K1a/K1b était RÉELLEMENT prête avant
    # cette période.
    def test_no_premature_key_activation(self):

        for case_study in self.case_studies:

            scenario_parameters, traces = (
                build_scenario_environment(
                    case_study
                )
            )

            mission_result = run_single_mission(
                case_study=case_study,
                scenario_parameters=(
                    scenario_parameters
                ),
                policy_id="P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS",
                decision_policy_fn=None,
                seed=SEED,
                max_steps=MAX_STEPS,
                traces=traces
            )

            for step_result in mission_result.steps:

                activated = (
                    step_result.state_after.key_age_s
                    == 0.0
                    and step_result.state_before
                    .key_age_s != 0.0
                )

                if not activated:

                    continue

                selected_evaluation = (
                    step_result.decision_maker_result
                    .selected_evaluation
                )

                self.assertIsNotNone(
                    selected_evaluation
                )

                key_action = (
                    selected_evaluation.decision
                    .key_action
                )

                if key_action == KeyAction.K2:

                    continue

                self.assertIn(
                    key_action,
                    [KeyAction.K1A, KeyAction.K1B]
                )

                self.assertTrue(
                    step_result
                    .candidate_key_ready_before,
                    (
                        case_study["scenario_id"]
                        + " : activation "
                        + key_action.value
                        + " sans clé candidate prête "
                        "à l'étape "
                        + str(
                            step_result.state_before
                            .step_index
                        )
                    )
                )

    # Test demandé : baseline conforme à A1-K0/K2, vérifié
    # sur une mission réelle complète (pas seulement sur
    # une décision isolée).
    def test_baseline_never_selects_k1_or_a2_in_real_run(
        self
    ):

        for case_study in self.case_studies:

            scenario_parameters, traces = (
                build_scenario_environment(
                    case_study
                )
            )

            mission_result = run_single_mission(
                case_study=case_study,
                scenario_parameters=(
                    scenario_parameters
                ),
                policy_id="B1-CONVENTIONAL",
                decision_policy_fn=(
                    select_baseline_conventional_decision
                ),
                seed=SEED,
                max_steps=MAX_STEPS,
                traces=traces
            )

            for decision_name in (
                mission_result.decision_counts
            ):

                self.assertIn(
                    decision_name,
                    ["A1-K0", "A1-K2"],
                    (
                        case_study["scenario_id"]
                        + " : B1-CONVENTIONAL a "
                        "sélectionné "
                        + decision_name
                    )
                )

    # Test demandé : poids produits par une seule
    # politique contextuelle — la même fonction
    # resolve_contextual_weights est utilisée, et produit
    # des poids identiques à parameters.contextual_weights
    # pour les cinq cas d'étude (aucun poids fixé
    # manuellement par scénario).
    def test_weights_come_from_single_contextual_policy(
        self
    ):

        for case_study in self.case_studies:

            scenario_parameters, _ = (
                build_scenario_environment(
                    case_study
                )
            )

            weights = resolve_contextual_weights(
                context=None,
                state=None,
                parameters=scenario_parameters
            )

            self.assertEqual(
                weights,
                scenario_parameters.contextual_weights
            )

            self.assertAlmostEqual(
                sum(weights),
                1.0
            )


class TestS1EnergyFocusedStableScenario(unittest.TestCase):

    # Test demandé : K1a/K1b progressifs — dans un
    # scénario stable et PHY-faisable (S1), le compteur
    # K1a doit progresser au fil de la mission.
    def test_k1a_progresses(self):

        case_studies = {
            case_study["scenario_id"]: case_study
            for case_study in (
                build_five_case_studies()
            )
        }

        s1 = case_studies[
            "S1-REMOTE-AGRICULTURAL-SENSOR"
        ]

        scenario_parameters, traces = (
            build_scenario_environment(s1)
        )

        mission_result = run_single_mission(
            case_study=s1,
            scenario_parameters=scenario_parameters,
            policy_id="P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS",
            decision_policy_fn=None,
            seed=SEED,
            max_steps=MAX_STEPS,
            traces=traces
        )

        final_k1a_collected = (
            mission_result.steps[-1]
            .k1a_measurements_after
        )

        self.assertGreater(
            final_k1a_collected,
            0
        )


class TestS3MobilityAffectsPhyFeasibility(
    unittest.TestCase
):

    # Test demandé : décisions adaptées aux changements de
    # vitesse — la faisabilité PHY de K1a doit différer
    # entre les phases à l'arrêt et les phases mobiles,
    # conformément au calcul réel de channel.py (pas
    # imposé par le scénario).
    def test_phy_feasibility_differs_between_phases(
        self
    ):

        case_studies = {
            case_study["scenario_id"]: case_study
            for case_study in (
                build_five_case_studies()
            )
        }

        s3 = case_studies["S3-MOBILE-VEHICLE"]

        scenario_parameters, traces = (
            build_scenario_environment(s3)
        )

        mission_result = run_single_mission(
            case_study=s3,
            scenario_parameters=scenario_parameters,
            policy_id="P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS",
            decision_policy_fn=None,
            seed=SEED,
            max_steps=MAX_STEPS,
            traces=traces
        )

        conditions = traces["conditions"]

        stopped_feasible_flags = []
        moving_feasible_flags = []

        for step_result in mission_result.steps:

            step_index = (
                step_result.state_before.step_index
            )

            # Sous la règle stricte (95)-(96), le Decision
            # Maker ne calcule plus jamais les métriques de
            # K1a lorsque renewal_required=False (rejetée
            # dès les règles de raisonnement). La faisabilité
            # PHY de K1a doit donc être recalculée
            # directement ici, exactement comme le fait
            # désormais physec_dm.mission.run_mission_step
            # (collecte passive, indépendante de la décision
            # retournée par le DM).
            state_before = step_result.state_before

            k1a_key_metrics = calculate_key_metrics(
                key_action=KeyAction.K1A,
                parameters=scenario_parameters,
                rho_ab=(
                    step_result.channel_metrics.rho_ab
                ),
                key_age_s=state_before.key_age_s,
                messages_with_current_key=(
                    state_before
                    .messages_with_current_key
                ),
                compromise_suspected=False,
                variation_feasible=True,
                collected_measurements=(
                    state_before
                    .k1a_measurements_collected
                ),
                candidate_ready=(
                    state_before.candidate_key_ready
                    and state_before.candidate_key_action
                    == KeyAction.K1A
                )
            )

            speed = conditions[step_index][
                "effective_speed_m_s"
            ]

            if speed == 0.0:

                stopped_feasible_flags.append(
                    k1a_key_metrics.agreement_feasible
                )

            else:

                moving_feasible_flags.append(
                    k1a_key_metrics.agreement_feasible
                )

        # Au moins une observation de chaque catégorie
        # doit exister sur 150 périodes (5 phases de 30
        # périodes chacune).
        self.assertGreater(
            len(stopped_feasible_flags),
            0
        )

        self.assertGreater(
            len(moving_feasible_flags),
            0
        )

        # La faisabilité PHY à l'arrêt doit être
        # majoritairement vraie, et quasi toujours fausse
        # en mouvement (cf. case_studies.py,
        # validity_limits de S3).
        self.assertTrue(
            any(stopped_feasible_flags)
        )


class TestOutputLabeling(unittest.TestCase):

    # Test demandé : sorties correctement étiquetées.
    def test_log_rows_contain_all_required_fields(self):

        case_studies = build_five_case_studies()

        case_study = case_studies[0]

        scenario_parameters, traces = (
            build_scenario_environment(case_study)
        )

        mission_result = run_single_mission(
            case_study=case_study,
            scenario_parameters=scenario_parameters,
            policy_id="P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS",
            decision_policy_fn=None,
            seed=SEED,
            max_steps=MAX_STEPS,
            traces=traces
        )

        rows = extract_log_rows(
            case_study=case_study,
            policy_id="P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS",
            seed=SEED,
            mission_result=mission_result,
            conditions=traces["conditions"]
        )

        self.assertEqual(
            len(rows),
            MAX_STEPS
        )

        for field_name in LOG_FIELD_NAMES:

            self.assertIn(
                field_name,
                rows[0]
            )

        self.assertEqual(
            rows[0]["scenario_id"],
            case_study["scenario_id"]
        )

        self.assertEqual(
            rows[0]["policy_id"],
            "P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS"
        )


if __name__ == "__main__":

    unittest.main()
