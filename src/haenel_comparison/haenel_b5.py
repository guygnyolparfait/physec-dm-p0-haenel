# ================================================================
# B5_HAENEL_CALIBRATED : transposition stochastique CALIBRÉE du
# banc d'essai ÉNERGÉTIQUE de Haenel et al. (Section 6.3)
# ================================================================
#
# NOMMAGE (corrigé le 25/09/2026, relecture) : ce module s'appelait
# auparavant "B5-littéral", ce qui suggérait une "reproduction
# littérale/exacte" du protocole. Ce n'est pas le cas : Haenel et
# al. (Section 6.3.3, Fig. 11) indique explicitement que le
# protocole hybride commence par une authentification complète
# ("Due to the first full authentication, the hybrid protocol was
# a little more energy-demanding at the start of the experiment"),
# un effet que ce module ne modélise PAS au niveau du tirage
# message par message (voir la convention explicite dans
# run_haenel_experiment_a.py, qui l'ajoute séparément au niveau de
# la campagne). Ce module reste donc une TRANSPOSITION STOCHASTIQUE
# CALIBRÉE sur le FRR publié -- jamais une reproduction bit-for-bit
# du protocole réel.
#
# ATTENTION — NE PAS CONFONDRE avec
# physec_dm.case_studies.select_b5_haenel_rff_then_mac_decision :
#
#   - Ce B5-là (existant, utilisé dans run_b5_haenel_comparison.py
#     sur les scénarios S1-S5) rejette A2 selon l'ADMISSIBILITÉ
#     RÉELLE du FAR dans le contexte du scénario (déterministe,
#     fondé sur notre modèle de canal).
#
#   - CE module (haenel_b5.py, B5_HAENEL_CALIBRATED) rejette A2
#     selon un TIRAGE STOCHASTIQUE calibré directement sur le FRR
#     PUBLIÉ par Haenel et al. dans leur propre banc d'essai
#     énergétique (u ~ Uniform(0,1) ; rejet si u < FRR). Il ne
#     regarde jamais le contexte radio : c'est une transposition
#     calibrée de LEUR protocole de mesure (Section 6.3.1), pas de
#     notre modèle de canal, et pas une reproduction exacte
#     (voir NOMMAGE ci-dessus).
#
# Les deux coexistent délibérément : ils répondent à deux
# questions scientifiques différentes (voir __init__.py et
# HAENEL_COMPARISON_README.md).

from dataclasses import dataclass, field

import numpy as np


@dataclass
class HaenelMessageEvent:
    """Le résultat d'un seul message simulé façon Haenel et al."""

    message_index: int
    frr: float
    u: float
    rff_rejected: bool          # True = "fallback" vers le MAC
    chosen_auth: str            # "A2" (RFF accepté) ou "A1" (repli MAC)


def simulate_haenel_reference_messages(frr, n_messages, seed):
    """Transpose, de façon calibrée (PAS littérale -- voir en-tête
    du fichier), la règle RFF-puis-MAC de Haenel et al. sur
    n_messages, avec un rejet RFF stochastique calibré sur le FRR
    publié.

    frr : taux de faux rejet (False Rejection Rate) à simuler.
        - None  -> MAC_ONLY : aucun essai RFF, chaque message part
          directement en MAC (Section 6.3.1).
        - 0.0   -> RFF_ONLY : aucun repli, le RFF "accepte" toujours
          le message légitime (théorique, "no fall back").
        - 0.05 / 0.10 -> cas HYBRID publiés.
    n_messages : nombre de messages simulés (100 pour reproduire
        le banc d'essai des 300 s / 3 s).
    seed : graine explicite pour la reproductibilité (Common
        Random Numbers avec P0 lorsque c'est pertinent).

    Retourne la liste des HaenelMessageEvent, un par message.
    """

    if n_messages <= 0:
        raise ValueError(
            "n_messages doit être strictement positif."
        )

    rng = np.random.default_rng(seed)

    events = []

    for message_index in range(n_messages):

        if frr is None:
            # MAC_ONLY : pas de tentative RFF du tout.
            u = None
            rff_rejected = True
            chosen_auth = "A1"

        else:
            u = float(rng.uniform(0.0, 1.0))
            rff_rejected = u < frr
            chosen_auth = "A1" if rff_rejected else "A2"

        events.append(
            HaenelMessageEvent(
                message_index=message_index,
                frr=frr,
                u=u,
                rff_rejected=rff_rejected,
                chosen_auth=chosen_auth,
            )
        )

    return events


def summarize_haenel_events(events):
    """Statistiques agrégées sur une liste de HaenelMessageEvent :
    nombre de messages, nombre de replis MAC, taux de repli
    observé (à comparer au FRR théorique dans les tests)."""

    n_messages = len(events)
    n_fallback = sum(1 for event in events if event.rff_rejected)
    n_rff_direct = n_messages - n_fallback

    observed_fallback_rate = (
        n_fallback / n_messages if n_messages > 0 else None
    )

    return {
        "n_messages": n_messages,
        "n_fallback_mac": n_fallback,
        "n_rff_direct": n_rff_direct,
        "observed_fallback_rate": observed_fallback_rate,
    }
