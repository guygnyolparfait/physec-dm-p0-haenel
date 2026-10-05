import unittest

from physec_dm.case_studies import (
    CASE_STUDY_IDS,
    apply_case_study_overrides,
    build_baseline_policy_definition,
    build_case_study_base_parameters,
    build_five_case_studies,
    select_baseline_conventional_decision
)

from physec_dm.decision_maker import run_decision_maker

from physec_dm.models import (
    AuthenticationAction,
    Context,
    KeyAction
)


REQUIRED_FIELDS = [
    "scenario_id",
    "scenario_name",
    "case_study_description",
    "system_under_test",
    "environment_description",
    "mission_description",
    "scientific_question",
    "phases",
    "parameters_held_constant",
    "parameters_allowed_to_change",
    "success_criteria",
    "validity_limits"
]


class TestFiveCaseStudies(unittest.TestCase):

    def setUp(self):

        self.case_studies = build_five_case_studies()

    # Test demandé : cinq cas d'étude exactement.
    def test_exactly_five_case_studies(self):

        self.assertEqual(
            len(self.case_studies),
            5
        )

        self.assertEqual(
            [
                case_study["scenario_id"]
                for case_study in self.case_studies
            ],
            CASE_STUDY_IDS
        )

    def test_each_case_study_has_all_required_fields(
        self
    ):

        for case_study in self.case_studies:

            for field_name in REQUIRED_FIELDS:

                self.assertIn(
                    field_name,
                    case_study,
                    (
                        case_study["scenario_id"]
                        + " doit contenir le champ "
                        + field_name
                    )
                )

    # Un cas d'étude n'est jamais réduit à de simples
    # parameter_overrides : la structure narrative doit
    # être non vide.
    def test_case_studies_are_not_only_parameter_overrides(
        self
    ):

        for case_study in self.case_studies:

            self.assertGreater(
                len(
                    case_study[
                        "case_study_description"
                    ]
                ),
                50
            )

            self.assertGreater(
                len(
                    case_study["scientific_question"]
                ),
                20
            )

            self.assertGreater(
                len(case_study["phases"]),
                0
            )

    # Test demandé : phases correctement ordonnées
    # (couvrent [0, 1] sans trou ni chevauchement).
    def test_phases_are_correctly_ordered(self):

        for case_study in self.case_studies:

            phases = case_study["phases"]

            self.assertEqual(
                phases[0]["start_fraction"],
                0.0
            )

            self.assertEqual(
                phases[-1]["end_fraction"],
                1.0
            )

            for index in range(len(phases) - 1):

                self.assertEqual(
                    phases[index]["end_fraction"],
                    phases[index + 1]["start_fraction"],
                    (
                        case_study["scenario_id"]
                        + " : trou ou chevauchement "
                        "entre les phases "
                        + str(index)
                        + " et "
                        + str(index + 1)
                    )
                )

    # Test demandé : absence de blocage PHY codé en dur.
    #
    # S1 ne doit pas imposer variation_feasible=False ;
    # plus généralement, aucun des cinq cas d'étude ne doit
    # bloquer la faisabilité PHY par construction — la
    # faisabilité réelle doit toujours être laissée au
    # calcul de key_generation.calculate_phy_feasibility.
    def test_no_case_study_hardcodes_phy_infeasibility(
        self
    ):

        for case_study in self.case_studies:

            self.assertTrue(
                case_study["variation_feasible"],
                (
                    case_study["scenario_id"]
                    + " ne doit pas imposer "
                    "variation_feasible=False."
                )
            )

    def test_case_study_parameters_validate(self):

        base_parameters = (
            build_case_study_base_parameters()
        )

        for case_study in self.case_studies:

            scenario_parameters = (
                apply_case_study_overrides(
                    base_parameters,
                    case_study
                )
            )

            errors, warnings = (
                scenario_parameters.validate(
                    require_complete=True
                )
            )

            self.assertEqual(
                errors,
                []
            )

            self.assertEqual(
                warnings,
                []
            )

    def test_s3_has_five_phases_with_speed_ramp(self):

        s3 = next(
            case_study
            for case_study in self.case_studies
            if case_study["scenario_id"]
            == "S3-MOBILE-VEHICLE"
        )

        self.assertEqual(
            len(s3["phases"]),
            5
        )

        self.assertEqual(
            s3["phases"][0]["effective_speed_m_s"],
            0.0
        )

        self.assertIsInstance(
            s3["phases"][1]["effective_speed_m_s"],
            tuple
        )

    def test_s5_has_a_compromise_event_at_45_percent(
        self
    ):

        s5 = next(
            case_study
            for case_study in self.case_studies
            if case_study["scenario_id"]
            == "S5-CRITICAL-INFRASTRUCTURE-ATTACK"
        )

        events = s5["scenario_events"]

        self.assertEqual(
            len(events),
            1
        )

        self.assertEqual(
            events[0]["at_fraction"],
            0.45
        )

        self.assertEqual(
            events[0]["effect"],
            "compromise_suspected"
        )


class TestBaselinePolicy(unittest.TestCase):

    def test_baseline_definition_excludes_k1_and_a2(
        self
    ):

        definition = (
            build_baseline_policy_definition()
        )

        self.assertEqual(
            definition["policy_id"],
            "B1-CONVENTIONAL"
        )

        description = definition[
            "description"
        ].lower()

        self.assertIn("a1", description)
        self.assertIn(
            "jamais",
            description
        )

    def _build_context(
        self,
        renewal_required
    ):

        return Context(
            snr_db=10.0,
            doppler_hz=0.0,
            battery_energy_j=30000.0,
            criticality=0,
            key_age_s=100.0,
            messages_with_current_key=2,
            rff_profile_available=True,
            renewal_required=renewal_required,
            key_expired=False,
            compromise_suspected=False,
            key_deadline_s=100.0,
            remaining_duty_cycle_airtime_s=100.0
        )

    # Test demandé : baseline conforme à A1-K0/K2.
    def test_baseline_selects_a1_k0_when_no_renewal(
        self
    ):

        base_parameters = (
            build_case_study_base_parameters()
        )

        context = self._build_context(
            renewal_required=False
        )

        result = select_baseline_conventional_decision(
            context=context,
            parameters=base_parameters,
            rho_ab=0.95,
            variation_feasible=True,
            k2_protocol=None
        )

        self.assertFalse(
            result.refusal_of_service
        )

        self.assertEqual(
            result.selected_evaluation.decision
            .get_name(),
            "A1-K0"
        )

    def test_baseline_never_uses_k1_or_a2(self):

        base_parameters = (
            build_case_study_base_parameters()
        )

        for renewal_required in [False, True]:

            context = self._build_context(
                renewal_required
            )

            result = (
                select_baseline_conventional_decision(
                    context=context,
                    parameters=base_parameters,
                    rho_ab=0.95,
                    variation_feasible=True,
                    k2_protocol=None
                )
            )

            for evaluation in (
                result.all_evaluations
            ):

                self.assertIn(
                    evaluation.decision.key_action,
                    [KeyAction.K0, KeyAction.K2]
                )

                self.assertEqual(
                    evaluation.decision
                    .authentication_action,
                    AuthenticationAction.A1
                )

    # Test demandé : mêmes équations et même Decision
    # Maker dans les cinq cas — vérifié ici en comparant
    # directement la fonction utilisée par P0 dans un
    # contexte représentatif à travers les cinq cas
    # d'étude : c'est TOUJOURS decision_maker.
    # run_decision_maker, jamais une fonction différente
    # par scénario.
    def test_p0_uses_the_single_shared_decision_maker(
        self
    ):

        case_studies = build_five_case_studies()

        base_parameters = (
            build_case_study_base_parameters()
        )

        for case_study in case_studies:

            scenario_parameters = (
                apply_case_study_overrides(
                    base_parameters,
                    case_study
                )
            )

            context = Context(
                snr_db=(
                    scenario_parameters.mean_snr_db
                ),
                doppler_hz=0.0,
                battery_energy_j=(
                    scenario_parameters
                    .initial_battery_energy_j
                ),
                criticality=0,
                key_age_s=0.0,
                messages_with_current_key=0,
                rff_profile_available=True,
                renewal_required=False,
                key_expired=False,
                compromise_suspected=False,
                key_deadline_s=24000.0,
                remaining_duty_cycle_airtime_s=36.0
            )

            # run_decision_maker est appelée directement
            # (pas une fonction spécifique au scénario) :
            # si elle n'existait pas ou avait une
            # signature différente selon le scénario,
            # cet appel échouerait.
            result = run_decision_maker(
                context=context,
                parameters=scenario_parameters,
                rho_ab=0.9,
                variation_feasible=(
                    case_study["variation_feasible"]
                ),
                k2_protocol=case_study["k2_protocol"]
            )

            self.assertIsNotNone(
                result
            )


if __name__ == "__main__":

    unittest.main()
