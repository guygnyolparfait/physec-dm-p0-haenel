# Genere la version ANGLAISE des 5 figures de comparaison des quatre
# objectifs, pour l'article anglais uniquement (ne touche pas au
# PowerPoint ni au rapport, qui restent en francais).
#
# Reutilise integralement la meme logique de lecture/agregation que
# generate_v2_comparison_figures.py (memes lignes du meme journal
# results/five_case_studies_v2_complex_adaptive/five_case_studies_v2_log.csv,
# memes calculs de moyenne/IC95) : seul le texte affiche sur la
# figure change de langue (voir lang="en" dans
# figure_four_objectives_comparison_v2). Aucune valeur numerique
# n'est recalculee differemment.
from generate_v2_comparison_figures import main

if __name__ == "__main__":

    main(lang="en")
