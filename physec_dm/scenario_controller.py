# Ce module fournit, pour chaque période d'une mission, les
# conditions EXOGÈNES d'un cas d'étude (physec_dm/case_studies.py) :
# phase active, SNR observé, vitesse effective, criticité,
# tentative de Mallory, suspicion de compromission.
#
# Il NE CONTOURNE JAMAIS channel.py : il produit uniquement les
# ingrédients (snr_db, speed_m_s) déjà acceptés par
# physec_dm.mission.run_mission_step, qui les transmet ensuite à
# physec_dm.channel.calculate_channel_metrics pour le calcul réel
# de la corrélation, du Doppler et du KDR. Aucune corrélation, ni
# Doppler, ni KDR n'est calculé ici.
import numpy as np


# ================================================================
# 1. TRACES ALÉATOIRES COMMUNES (section 5 du protocole)
# ================================================================
#
# Pour une graine donnée, P0-PARETO-TCHEBYCHEFF-EQUAL-WEIGHTS et B1-CONVENTIONAL
# doivent observer exactement les mêmes réalisations aléatoires
# exogènes (mêmes tirages de criticité, d'attaque, de bruit de
# canal) : seule la DÉCISION prise diffère entre les deux
# politiques. Cette fonction construit une trace commune, unique
# par graine, indépendante de la politique évaluée.
def build_common_random_traces(
    seed,
    max_steps
):

    if max_steps <= 0:

        raise ValueError(
            "max_steps doit être strictement positif."
        )

    random_generator = np.random.default_rng(
        seed
    )

    return {
        # Comparé au seuil critical_message_probability de
        # la phase active pour tirer la criticité.
        "criticality_uniform": (
            random_generator.random(
                max_steps
            )
        ),

        # Comparé au seuil mallory_attempt_probability de
        # la phase active pour tirer la tentative
        # d'attaque.
        "attack_uniform": (
            random_generator.random(
                max_steps
            )
        ),

        # Variable centrée réduite : le SNR observé de
        # chaque période est mean_snr_db(phase) +
        # shadowing_std_db(phase) * shadowing_normal[step].
        # Partager cette variable RÉDUITE (plutôt que le
        # SNR déjà mis à l'échelle) permet à des phases de
        # moyenne ou d'écart-type différents de rester
        # comparables entre scénarios tout en réutilisant
        # la même réalisation sous-jacente.
        "shadowing_normal": (
            random_generator.standard_normal(
                max_steps
            )
        ),

        # Réservé aux événements aléatoires optionnels
        # qu'un futur cas d'étude pourrait ajouter (aucun
        # des cinq cas d'étude actuels ne l'utilise : leurs
        # événements sont déterministes, ancrés à une
        # fraction précise de la mission).
        "event_uniform": (
            random_generator.random(
                max_steps
            )
        )
    }


# ================================================================
# 2. RÉSOLUTION DE LA PHASE ACTIVE
# ================================================================


def resolve_progress_fraction(
    step_index,
    max_steps
):

    if max_steps <= 0:

        raise ValueError(
            "max_steps doit être strictement positif."
        )

    return (
        step_index
        / max_steps
    )


# Retourne la phase du cas d'étude active à une période donnée.
#
# Les fractions de phase sont des bornes [start_fraction,
# end_fraction) sur la progression de la mission ; la dernière
# phase couvre la borne fermée à droite (1.0 inclus).
def resolve_active_phase(
    case_study,
    step_index,
    max_steps
):

    progress_fraction = resolve_progress_fraction(
        step_index,
        max_steps
    )

    phases = case_study["phases"]

    for phase in phases:

        is_last_phase = (
            phase is phases[-1]
        )

        if (
            progress_fraction
            >= phase["start_fraction"]
        ) and (
            progress_fraction
            < phase["end_fraction"]
            or (
                is_last_phase
                and progress_fraction
                <= phase["end_fraction"]
            )
        ):

            return phase

    raise ValueError(
        "Aucune phase ne couvre la fraction de "
        "progression "
        + format(progress_fraction, ".4f")
        + " pour le cas d'étude "
        + case_study["scenario_id"]
        + "."
    )


# ================================================================
# 3. RÉSOLUTION DE LA VITESSE (rampes linéaires, cas S3)
# ================================================================
#
# effective_speed_m_s d'une phase peut être :
# - un nombre (vitesse constante sur toute la phase) ;
# - un triplet ("ramp", vitesse_debut, vitesse_fin), interpolé
#   linéairement selon la progression DANS la phase.
def resolve_effective_speed_m_s(
    phase,
    step_index,
    max_steps
):

    speed_value = phase["effective_speed_m_s"]

    if not isinstance(speed_value, tuple):

        return float(
            speed_value
        )

    _, start_speed_m_s, end_speed_m_s = speed_value

    progress_fraction = resolve_progress_fraction(
        step_index,
        max_steps
    )

    phase_span = (
        phase["end_fraction"]
        - phase["start_fraction"]
    )

    if phase_span <= 0:

        return float(
            end_speed_m_s
        )

    fraction_within_phase = (
        progress_fraction
        - phase["start_fraction"]
    ) / phase_span

    fraction_within_phase = min(
        max(
            fraction_within_phase,
            0.0
        ),
        1.0
    )

    interpolated_speed_m_s = (
        start_speed_m_s
        + fraction_within_phase
        * (
            end_speed_m_s
            - start_speed_m_s
        )
    )

    return float(
        interpolated_speed_m_s
    )


# ================================================================
# 4. ÉVÉNEMENTS PONCTUELS DU SCÉNARIO (cas S5)
# ================================================================


def resolve_compromise_suspected(
    case_study,
    phase,
    step_index,
    max_steps
):

    if phase["compromise_suspected_forced"]:

        return True

    progress_fraction = resolve_progress_fraction(
        step_index,
        max_steps
    )

    for event in case_study.get(
        "scenario_events",
        []
    ):

        if event["effect"] != "compromise_suspected":

            continue

        if (
            progress_fraction
            >= event["at_fraction"]
            and progress_fraction
            < event["clears_at_fraction"]
        ):

            return True

    return False


# ================================================================
# 5. CONDITIONS EXOGÈNES COMPLÈTES D'UNE PÉRIODE
# ================================================================


class ScenarioController:

    def __init__(
        self,
        case_study,
        seed,
        max_steps,
        common_traces=None
    ):

        self.case_study = case_study
        self.seed = seed
        self.max_steps = max_steps

        if common_traces is None:

            common_traces = (
                build_common_random_traces(
                    seed=seed,
                    max_steps=max_steps
                )
            )

        self.common_traces = common_traces

    # Retourne, pour une période donnée, toutes les
    # conditions exogènes nécessaires à
    # physec_dm.mission.run_mission_step : jamais une
    # corrélation, un Doppler ou un KDR (calculés
    # exclusivement par channel.py et key_generation.py).
    def resolve_period_conditions(
        self,
        step_index
    ):

        if step_index >= self.max_steps:

            raise ValueError(
                "step_index dépasse max_steps pour ce "
                "contrôleur de scénario."
            )

        phase = resolve_active_phase(
            self.case_study,
            step_index,
            self.max_steps
        )

        effective_speed_m_s = (
            resolve_effective_speed_m_s(
                phase,
                step_index,
                self.max_steps
            )
        )

        if phase["criticality_forced"] is not None:

            criticality = phase["criticality_forced"]

        else:

            criticality = (
                1
                if self.common_traces[
                    "criticality_uniform"
                ][step_index]
                < phase[
                    "critical_message_probability"
                ]
                else 0
            )

        mallory_attempted = bool(
            self.common_traces[
                "attack_uniform"
            ][step_index]
            < phase["mallory_attempt_probability"]
        )

        compromise_suspected = (
            resolve_compromise_suspected(
                self.case_study,
                phase,
                step_index,
                self.max_steps
            )
        )

        observed_snr_db = (
            phase["mean_snr_db"]
            + phase["shadowing_std_db"]
            * self.common_traces[
                "shadowing_normal"
            ][step_index]
        )

        return {
            "phase_name": phase["phase_name"],
            "observed_snr_db": float(
                observed_snr_db
            ),
            "real_snr_db": float(
                observed_snr_db
            ),
            "mean_snr_db": phase["mean_snr_db"],
            "shadowing_std_db": (
                phase["shadowing_std_db"]
            ),
            # background_radio_load réutilise
            # shadowing_std_db comme unique
            # représentation validée de la charge radio
            # de fond (voir case_studies.py, S4,
            # validity_limits : aucune consommation
            # directe du duty-cycle par du trafic tiers
            # n'est modélisée).
            "background_radio_load": (
                phase["shadowing_std_db"]
            ),
            "effective_speed_m_s": (
                effective_speed_m_s
            ),
            "criticality": criticality,
            "mallory_attempted": mallory_attempted,
            "compromise_suspected": (
                compromise_suspected
            )
        }
