# Path permet de construire simplement
# le dossier dans lequel les résultats seront enregistrés.
from pathlib import Path


# Parameters contient toutes les constantes
# et tous les paramètres de la modélisation.
from physec_dm.parameters import (
    Parameters
)


# run_campaign exécute les scénarios,
# les politiques et les graines.
#
# aggregate_campaign_results prépare
# un résumé lisible des résultats.
from physec_dm.campaign import (
    aggregate_campaign_results,
    run_campaign
)


# ================================================================
# 1. PARAMÈTRES DE LA CAMPAGNE COURTE DE VÉRIFICATION
# ================================================================


# Cette fonction construit les paramètres
# de la première campagne courte.
#
# IMPORTANT :
#
# Les valeurs ajoutées ici servent uniquement
# à vérifier que toute la chaîne du programme fonctionne.
#
# Elles ne doivent pas encore être présentées
# comme des valeurs scientifiques finales dans le rapport.
#
# Les paramètres scientifiques définitifs seront validés
# pendant l'étape suivante consacrée aux résultats.
def build_smoke_parameters():

    parameters = Parameters()

    # ------------------------------------------------------------
    # Paramètres du défi-réponse
    # ------------------------------------------------------------

    # Valeur provisoire utilisée uniquement
    # pour exécuter la campagne courte.
    parameters.challenge_response_latency_s = 4.0

    # Nombre provisoire de cycles du MAC.
    parameters.mac_cycles = 32000

    # ------------------------------------------------------------
    # Paramètres de génération et de gestion de clé
    # ------------------------------------------------------------

    # La campagne courte considère que la condition
    # de variabilité est satisfaite.
    #
    # Cette valeur devra ensuite être reliée
    # à une métrique scientifique validée.
    parameters.variation_feasible = True

    # Échéance minimale provisoire.
    parameters.minimum_deadline_s = 1.0

    # Coût provisoire de réconciliation.
    parameters.reconciliation_cycles_per_bit = 100

    # Coût provisoire de l'amplification
    # de confidentialité.
    parameters.privacy_amplification_cycles = 6400

    # Énergie provisoire des messages
    # de réconciliation.
    parameters.reconciliation_message_energy_j = 0.005

    # Latence provisoire des messages
    # de réconciliation.
    parameters.reconciliation_message_latency_s = 0.5

    # Niveau de sécurité provisoire de K2.
    parameters.security_strength_bits = 128

    # Identifiant explicite indiquant
    # que le protocole K2 reste provisoire.
    parameters.k2_protocol_id = (
        "DEVELOPMENT_ONLY"
    )

    # ------------------------------------------------------------
    # Énergie de base
    # ------------------------------------------------------------

    # Les quatre valeurs suivantes permettent
    # de lancer un test fonctionnel.
    #
    # Elles devront être remplacées par des valeurs
    # mesurées ou correctement sourcées.
    parameters.sensing_energy_j = 0.001
    parameters.application_energy_j = 0.002
    parameters.receive_windows_energy_j = 0.003
    parameters.sleep_energy_j = 0.004

    # ------------------------------------------------------------
    # Probabilités de mission
    # ------------------------------------------------------------

    # 20 % des messages sont critiques
    # dans la campagne courte.
    parameters.critical_message_probability = 0.20

    # Mallory tente une attaque
    # avec une probabilité de 10 % par période.
    parameters.mallory_attempt_probability = 0.10

    # ------------------------------------------------------------
    # Paramètres numériques du Decision Maker
    # ------------------------------------------------------------

    # Ces tolérances sont uniquement numériques.
    #
    # Elles évitent de traiter une très petite erreur
    # d'arrondi comme une différence scientifique.
    parameters.score_tolerance = 1e-12
    parameters.dominance_tolerance = 1e-12

    # Poids égaux pour le test fonctionnel :
    #
    # énergie, latence, authentification, clé.
    #
    # Ils ne constituent pas encore
    # la politique scientifique définitive.
    parameters.contextual_weights = [
        0.25,
        0.25,
        0.25,
        0.25
    ]

    return parameters


# ================================================================
# 2. SCÉNARIO DE VÉRIFICATION
# ================================================================


# Cette fonction définit un seul scénario court.
#
# Le but n'est pas encore de produire les courbes finales.
#
# Le but est de vérifier :
# - le lancement ;
# - l'exécution de plusieurs périodes ;
# - l'export des fichiers CSV.
def build_smoke_scenarios():

    scenarios = [
        {
            # Identifiant du scénario.
            "scenario_id": "S-SMOKE",

            # Le SNR est rendu déterministe
            # pour faciliter la première vérification.
            "parameter_overrides": {
                "mean_snr_db": 5.0,
                "shadowing_std_db": 0.0
            },

            # Le SNR réel est identique
            # au SNR observé.
            "real_snr_bias_db": 0.0,

            # La condition de variabilité est considérée
            # satisfaite uniquement pour ce test fonctionnel.
            "variation_feasible": True,

            # Aucune suspicion aléatoire de compromission
            # pendant cette première campagne.
            "compromise_probability": 0.0,

            # Options spécifiques de la mission.
            "mission_options": {
                # Cinq périodes suffisent
                # pour une première vérification.
                "max_steps": 5,

                # Le profil RFF est disponible.
                "rff_profile_available": True,

                # Le budget est volontairement large
                # pour éviter qu'un problème de duty-cycle
                # empêche la vérification fonctionnelle.
                "initial_duty_cycle_airtime_s": 10.0,
                "maximum_duty_cycle_airtime_s": 10.0,
                "duty_cycle_recharge_s": 10.0
            }
        }
    ]

    return scenarios


# ================================================================
# 3. POLITIQUE DE VÉRIFICATION
# ================================================================


# Cette fonction définit une seule politique.
#
# Les quatre objectifs reçoivent le même poids.
#
# La comparaison de plusieurs politiques
# sera réalisée pendant la campagne scientifique finale.
def build_smoke_policies():

    policies = [
        {
            "policy_id": "P-SMOKE-BALANCED",

            "contextual_weights": [
                0.25,
                0.25,
                0.25,
                0.25
            ],

            "fallback_mode": "refuse"
        }
    ]

    return policies


# ================================================================
# 4. GRAINE DE VÉRIFICATION
# ================================================================


# Une seule graine suffit pour le test court.
#
# Les résultats scientifiques utiliseront
# plusieurs graines.
def build_smoke_seeds():

    return [
        123
    ]


# ================================================================
# 5. VALIDATION AVANT LE LANCEMENT
# ================================================================


# Cette fonction vérifie que la campagne courte
# possède toutes les informations nécessaires.
def validate_smoke_configuration(
    parameters,
    scenarios,
    policies,
    seeds
):

    # Parameters.validate retourne :
    # - une liste d'erreurs ;
    # - une liste d'avertissements.
    errors, warnings = parameters.validate(
        require_complete=True
    )

    # Une campagne ne doit pas être lancée
    # si des paramètres obligatoires manquent.
    if len(errors) > 0:

        raise ValueError(
            "La configuration contient des erreurs : "
            + " | ".join(errors)
        )

    if scenarios is None or len(scenarios) == 0:

        raise ValueError(
            "Au moins un scénario est requis."
        )

    if policies is None or len(policies) == 0:

        raise ValueError(
            "Au moins une politique est requise."
        )

    if seeds is None or len(seeds) == 0:

        raise ValueError(
            "Au moins une graine est requise."
        )

    # On vérifie les poids de chaque politique.
    for policy in policies:

        weights = policy.get(
            "contextual_weights"
        )

        if weights is None or len(weights) != 4:

            raise ValueError(
                "Chaque politique doit contenir "
                "quatre poids contextuels."
            )

        if any(
            weight < 0
            for weight in weights
        ):

            raise ValueError(
                "Les poids ne peuvent pas être négatifs."
            )

        if abs(
            sum(weights) - 1.0
        ) > parameters.tchebycheff_epsilon:

            raise ValueError(
                "La somme des poids doit être égale à 1."
            )

    return True


# ================================================================
# 6. AFFICHAGE DU RÉSUMÉ
# ================================================================


# Cette petite fonction transforme None
# en texte lisible dans le terminal.
def format_summary_value(
    value
):

    if value is None:

        return "non défini"

    if isinstance(
        value,
        float
    ):

        return format(
            value,
            ".6f"
        )

    return str(
        value
    )


# Cette fonction affiche un résumé
# après l'exécution de la campagne.
def print_campaign_summary(
    campaign_result
):

    aggregate_rows = aggregate_campaign_results(
        campaign_result
    )

    print()
    print(
        "============================================================"
    )
    print(
        "RÉSUMÉ DE LA CAMPAGNE"
    )
    print(
        "============================================================"
    )

    print(
        "Identifiant :",
        campaign_result.campaign_id
    )

    print(
        "Nombre de missions :",
        len(
            campaign_result.mission_results
        )
    )

    print(
        "Dossier de résultats :",
        campaign_result.output_directory
    )

    for row in aggregate_rows:

        print()
        print(
            "Scénario :",
            row["scenario_id"]
        )

        print(
            "Politique :",
            row["policy_id"]
        )

        print(
            "Durée observée moyenne (s) :",
            format_summary_value(
                row[
                    "observed_lifetime_s_mean"
                ]
            )
        )

        print(
            "Énergie moyenne par message généré (J) :",
            format_summary_value(
                row[
                    "energy_per_generated_message_j_mean"
                ]
            )
        )

        print(
            "FAR empirique moyenne :",
            format_summary_value(
                row[
                    "false_acceptance_rate_mean"
                ]
            )
        )

        print(
            "Taux moyen de refus légitime :",
            format_summary_value(
                row[
                    "legitimate_refusal_rate_mean"
                ]
            )
        )

        print(
            "Fraction de missions censurées :",
            format_summary_value(
                row[
                    "censored_fraction"
                ]
            )
        )

    print()
    print(
        "Les fichiers CSV ont été enregistrés."
    )


# ================================================================
# 7. LANCEMENT DE LA CAMPAGNE COURTE
# ================================================================


# Cette fonction prépare et lance
# la première campagne de vérification.
def run_smoke_campaign(
    output_directory="results/smoke"
):

    parameters = build_smoke_parameters()

    scenarios = build_smoke_scenarios()
    policies = build_smoke_policies()
    seeds = build_smoke_seeds()

    validate_smoke_configuration(
        parameters=parameters,
        scenarios=scenarios,
        policies=policies,
        seeds=seeds
    )

    output_directory = Path(
        output_directory
    )

    campaign_result = run_campaign(
        base_parameters=parameters,
        campaign_id="CAMP-SMOKE-01",
        scenarios=scenarios,
        policies=policies,
        seeds=seeds,
        output_directory=(
            output_directory
        ),
        max_steps=5,
        variation_feasible=True,
        export_results=True
    )

    return campaign_result


# ================================================================
# 8. POINT D'ENTRÉE DU PROGRAMME
# ================================================================


# Cette fonction est appelée lorsque l'utilisateur
# lance la commande :
#
# ./.venv/bin/python3 main.py
def main():

    print(
        "Lancement de la campagne courte de vérification."
    )

    print(
        "Les valeurs provisoires de cette campagne "
        "ne sont pas encore des résultats scientifiques finaux."
    )

    campaign_result = run_smoke_campaign()

    print_campaign_summary(
        campaign_result
    )

    return campaign_result


# Cette condition empêche le programme
# de se lancer automatiquement lorsqu'il est importé
# par les tests.
if __name__ == "__main__":

    main()
