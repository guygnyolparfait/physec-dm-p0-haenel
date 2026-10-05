# Script d'exploration (jetable, hors dépôt) pour l'étape 8 :
# vérifier empiriquement, avec le VRAI code de decision_maker.py,
# le diagnostic epsilon-au-dénominateur signalé par ChatGPT sur
# une copie du projet.
#
# N'écrit rien dans le dépôt. Sert uniquement à produire des
# chiffres réels avant toute décision de correction.

import sys
import types

sys.path.insert(0, "/home/parfait/physec_dm")

from physec_dm.decision_maker import (
    calculate_tchebycheff_score,
    calculate_ideal_and_nadir_points,
    calculate_pareto_front,
    select_from_pareto_front,
    objective_vector_dominates
)

from physec_dm.models import (
    AuthenticationAction,
    Decision,
    DecisionEvaluation,
    KeyAction
)

EPS = 1e-12          # parameters.tchebycheff_epsilon réel
SCORE_TOL = 1e-12    # parameters.score_tolerance réel (main.py / scientific_config.py)


def make_evaluation(name_suffix, objective_vector, far, energy, latency):

    decision = Decision(AuthenticationAction.A1, KeyAction.K0)

    evaluation = DecisionEvaluation(decision)
    evaluation.objective_vector = objective_vector

    evaluation.authentication_metrics = types.SimpleNamespace(far=far)
    evaluation.cost_metrics = types.SimpleNamespace(
        expected_energy_j=energy,
        normalized_latency=latency
    )

    # on force un nom distinct pour le tie-break lexicographique
    evaluation.decision.get_name = lambda: "D_" + name_suffix

    return evaluation


print("=" * 70)
print("CAS A -- span normal (échelle réaliste des objectifs)")
print("=" * 70)

# Deux décisions non dominées, construites pour être en EXACT tie
# sous la formule PURE (sans epsilon) : score = max_k w_k*(f-ideal)/span
# avec poids égaux (0.25 chacun), 4 objectifs.
#
# Front (ideal/nadir) fixés artificiellement :
ideal = [0.15, 0.001, -1.0, -1.0]
nadir = [0.25, 0.01, -0.9, -0.9]
weights = [0.25, 0.25, 0.25, 0.25]

# D1 est pire sur l'énergie (dim0), D2 est pire sur la latence (dim1),
# choisies pour que leur score PUR (sans epsilon) soit rigoureusement
# égal à 0.025 (= 0.25 * (span/span)) sur leur dimension qui domine
# le max, et plus petit ailleurs.
span0 = nadir[0] - ideal[0]   # 0.10
span1 = nadir[1] - ideal[1]   # 0.009

f1 = [ideal[0] + span0, ideal[1], ideal[2], ideal[3]]  # pire seulement sur dim0
f2 = [ideal[0], ideal[1] + span1, ideal[2], ideal[3]]  # pire seulement sur dim1

score1_pure = weights[0] * (f1[0]-ideal[0]) / span0
score2_pure = weights[1] * (f2[1]-ideal[1]) / span1
print("score pur D1 (dim energie) =", score1_pure)
print("score pur D2 (dim latence) =", score2_pure)
print("egaux sous la formule pure :", score1_pure == score2_pure)

score1_code = calculate_tchebycheff_score(f1, weights, ideal, nadir, EPS)
score2_code = calculate_tchebycheff_score(f2, weights, ideal, nadir, EPS)
print("score CODE REEL (avec epsilon) D1 =", repr(score1_code))
print("score CODE REEL (avec epsilon) D2 =", repr(score2_code))
print("difference =", score1_code - score2_code)
print("|difference| <= score_tolerance (1e-12) ?", abs(score1_code - score2_code) <= SCORE_TOL)
print("|difference| <= score_tolerance (1e-12), strict ?", abs(score1_code - score2_code) < SCORE_TOL)

print()
print("=" * 70)
print("CAS B -- ideal == nadir sur une dimension (span nul)")
print("=" * 70)

ideal_b = [0.2, 0.005, -1.0, -0.95]
nadir_b = [0.2, 0.005, -0.9, -0.90]  # dims 0 et 1 : span=0
f_b = [0.2, 0.005, -0.95, -0.92]

score_b = calculate_tchebycheff_score(f_b, weights, ideal_b, nadir_b, EPS)
print("score avec span nul sur dims 0 et 1 :", score_b)
print("(numerateur dims 0/1 attendu = 0 car f=ideal=nadir -> 0/eps = 0, pas de division par zero)")

print()
print("=" * 70)
print("CAS C -- span tres petit (mais non nul), proche de epsilon")
print("=" * 70)

for tiny_span in [1e-6, 1e-9, 1e-12, 1e-15]:
    ideal_c = [0.2, 0.0, -1.0, -1.0]
    nadir_c = [0.2 + tiny_span, 0.0, -0.9, -0.9]
    f_c = [0.2 + tiny_span, 0.0, -1.0, -1.0]  # pire cas complet sur dim0
    score_c = calculate_tchebycheff_score(f_c, weights, ideal_c, nadir_c, EPS)
    exact_no_eps = weights[0] * (f_c[0]-ideal_c[0]) / tiny_span if tiny_span != 0 else float("nan")
    print(
        "span=%.1e  score_code=%.15f  score_pur_sans_eps=%.15f  ratio_code/pur=%.10f"
        % (tiny_span, score_c, exact_no_eps, score_c/exact_no_eps if exact_no_eps else float("nan"))
    )

print()
print("=" * 70)
print("CAS D -- egalite EXACTE de vecteurs objectifs (D1==D2 en tout point)")
print("=" * 70)

f_d1 = [0.2, 0.005, -0.95, -0.92]
f_d2 = list(f_d1)  # copie exacte
ideal_d = [0.15, 0.001, -1.0, -0.98]
nadir_d = [0.25, 0.01, -0.9, -0.90]

score_d1 = calculate_tchebycheff_score(f_d1, weights, ideal_d, nadir_d, EPS)
score_d2 = calculate_tchebycheff_score(f_d2, weights, ideal_d, nadir_d, EPS)
print("score D1 == score D2 (vecteurs objectifs identiques) ?", score_d1 == score_d2, score_d1, score_d2)

print()
print("=" * 70)
print("CAS E -- select_from_pareto_front() : la decision finale change-t-elle ?")
print("=" * 70)

eval1 = make_evaluation("ENERGY_WORST", f1, far=0.001, energy=0.20, latency=0.003)
eval2 = make_evaluation("LATENCY_WORST", f2, far=0.001, energy=0.16, latency=0.0055)

pareto_front = [eval1, eval2]

selected, ideal_pt, nadir_pt, w = select_from_pareto_front(
    pareto_front=pareto_front,
    contextual_weights=weights,
    epsilon=EPS,
    score_tolerance=SCORE_TOL
)

print("Score final D1 (energie pire) :", eval1.tchebycheff_score)
print("Score final D2 (latence pire) :", eval2.tchebycheff_score)
print("Decision selectionnee :", selected.decision.get_name())
print(
    "-> Si les deux scores etaient VRAIMENT egaux (formule pure), le "
    "tie-break (FAR puis energie puis latence puis nom) aurait du "
    "s'appliquer et choisir D2 (energie 0.16 < 0.20). Verifions si "
    "c'est bien D2 qui sort, ou si l'ecart induit par epsilon a "
    "court-circuite le tie-break en departageant directement sur le "
    "score."
)
