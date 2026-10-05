# Module de comparaison isolé : transposition calibrée du banc
# d'essai énergétique publié par Haenel et al. (Sensors 2021), puis
# substitution de leur règle RFF-puis-MAC par notre Decision Maker
# P0, dans une transposition du même scénario énergétique, sur une
# échelle énergétique commune, avec les paramètres manquants
# explicitement traités comme hypothèses (jamais "dans exactement
# les mêmes conditions" : certaines variables nécessaires à P0 ne
# sont pas publiées par Haenel et al.).
#
# CE MODULE EST VOLONTAIREMENT SÉPARÉ des campagnes S1-S5
# (physec_dm/case_studies.py, run_five_case_studies*.py) et ne
# les modifie jamais. Il ne réutilise pas non plus le B5 déjà
# présent dans case_studies.py (select_b5_haenel_rff_then_mac_decision),
# qui répond à une question différente : comment une règle
# "façon Haenel" se comporte-t-elle dans NOS scénarios S1-S5,
# avec un rejet de A2 déterminé par l'admissibilité FAR réelle
# du contexte.
#
# Ici, la question est différente : reproduisons-nous les
# CHIFFRES PUBLIÉS par Haenel et al. sur LEUR propre protocole
# de mesure (300 s, 100 messages, rejet RFF stochastique
# calibré sur leur FRR mesuré) ? Voir HAENEL_COMPARISON_README.md
# pour le détail de cette distinction.
