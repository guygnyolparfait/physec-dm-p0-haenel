# Explication simple — à lire sans ouvrir le code

*Version finale, corrigée après deux relectures.*

## Ce que Haenel et al. a physiquement fait

Leur capteur essaie d'abord de reconnaître l'émetteur par son
« empreinte radio » (comme une empreinte digitale, mais radio). Si
ça ne marche pas, il bascule vers un code cryptographique classique
(un calcul de sécurité, comme un mot de passe secret). Ils ont
mesuré la consommation d'énergie réelle de ce système sur du vrai
matériel (un microcontrôleur, une puce radio) pendant 300 secondes,
avec un message toutes les 3 secondes.

Leur article dit aussi une chose importante : au tout début, le
protocole doit faire une « authentification complète » avant de
pouvoir utiliser l'empreinte radio couramment — ça coûte un peu plus
cher au démarrage. Ils ne donnent pas le chiffre exact de ce
surcoût de démarrage.

## Ce qui est simulé chez nous

On n'a pas leur matériel. On a construit une simulation dans notre
programme qui rejoue leur règle de décision (empreinte radio, puis
repli sur le code cryptographique si l'empreinte échoue), calibrée
sur les chiffres d'énergie qu'ils ont publiés. On appelle ça
**B5_HAENEL_CALIBRATED** — pas « B5-littéral » comme avant, parce
que ce nom donnait l'impression qu'on reproduisait leur protocole
exactement, y compris le détail du démarrage, ce qui n'est pas tout
à fait vrai.

## Ce que veut dire « microcontrôleur simulé »

On ne mesure jamais un vrai microcontrôleur MSP430 ou une vraie
puce radio CC110L. On utilise leurs fiches techniques officielles
(les documents que le fabricant publie, avec les vrais chiffres de
consommation électrique) pour calculer, sur le papier, combien
d'énergie coûterait chaque opération (émettre, recevoir, calculer).
C'est une reconstruction théorique, pas une mesure physique.

## Pourquoi Option A et Option B existent

- **Option A** : on prend directement les 4 chiffres que Haenel a
  publiés (en millijoules) et on calcule une formule simple qui les
  retrouve exactement. C'est une **calibration**, pas une preuve
  scientifique indépendante : puisqu'on ajuste la formule pour
  coller aux chiffres publiés, il est normal qu'elle les retrouve.
  Elle sert juste d'échelle commune pour comparer les politiques.
- **Option B** : on essaie de reconstruire le coût en détail
  (combien coûte d'émettre, de recevoir, de calculer) à partir des
  vraies fiches techniques des composants. Résultat honnête : ce
  modèle détaillé n'explique qu'une petite partie (moins de 15%
  selon le cas) du surcoût réel d'un repli vers le code
  cryptographique. Il manque quelque chose que Haenel ne précise
  pas dans son article (peut-être un temps d'attente de réponse
  radio) — on le dit clairement plutôt que de le cacher.

## Ce qui vient réellement du papier, ce qui est calibré, ce qui est supposé

- **Vient du papier** : les 4 chiffres d'énergie, le FRR (taux
  d'erreur de l'empreinte radio) testé à 5% et 10%, le FAR (taux
  de fausses acceptations d'un attaquant) de 0,2% — mesuré dans une
  AUTRE expérience du même article, liée explicitement au FRR de
  10% par une phrase du papier.
- **Calibré** : le coût moyen d'un repli vers le code
  cryptographique, ajusté pour retrouver exactement les chiffres
  publiés.
- **Supposé** : la taille des messages échangés, la vitesse de la
  radio, le coût du calcul cryptographique sur ce microcontrôleur
  précis — Haenel ne les donne pas, on teste une fourchette
  raisonnable plutôt que d'inventer un chiffre unique.

## Une correction importante : donner à P0 les VRAIES performances de Haenel

Avant cette dernière version, quand on demandait à P0 de choisir
entre l'empreinte radio et le code cryptographique, on utilisait le
taux d'erreur de NOTRE PROPRE modèle radio pour l'empreinte
(minuscule, ~0,008%), pas celui que Haenel a mesuré (0,2%). Ce
n'était pas la bonne comparaison. Corrigé : maintenant, P0 reçoit
directement le taux d'erreur PUBLIÉ par Haenel (0,2%) pour
l'empreinte radio. Le résultat ne change pas (P0 choisit toujours le
code cryptographique), mais la comparaison est maintenant la bonne.

## Pourquoi P0 choisit le code cryptographique sous poids égaux

On a vérifié en détail, avec du calcul, pas juste une impression :
avec seulement deux choix possibles, celui qui coûte moins cher en
énergie (l'empreinte radio) est exactement à égalité de score avec
celui qui est plus sûr (le code cryptographique), quand on donne le
même poids d'importance aux 4 critères (énergie, temps, sécurité,
qualité de la clé). En cas d'égalité stricte, une règle de
départage choisit celui qui a le taux d'erreur de sécurité le plus
bas — le code cryptographique. C'est mathématique, pas un réglage
qu'on a fait exprès.

## Pourquoi cela peut changer avec les poids — et à quel point c'est fragile

On a testé très finement : si on donne à peine plus d'importance à
l'énergie qu'à la sécurité (une différence de seulement 0,001 sur
une échelle de 0 à 1), P0 change d'avis et choisit l'empreinte
radio. Ce n'est donc PAS vrai de dire qu'il faudrait « beaucoup plus
» prioriser l'énergie — la frontière entre les deux choix est juste
à côté du point où on met les poids égaux.

## Pourquoi B5 consomme moins d'énergie dans ce scénario

Parce que B5 utilise l'empreinte radio la plupart du temps (elle
coûte moins cher), et ne bascule vers le code cryptographique que
de temps en temps (quand l'empreinte échoue). P0, lui, choisit
directement et systématiquement le code cryptographique — donc il
paie ce coût plus élevé à chaque message, pas seulement de temps en
temps.

![Figure — La courbe du haut (bleue) est celle de Haenel et al. : elle descend quand l'empreinte radio échoue moins souvent (le RFF est utilisé plus souvent, donc moins d'énergie dépensée). La courbe orange (B5) suit la même tendance. La ligne verte plate, c'est P0 : toujours au même niveau, celui du code cryptographique seul, quel que soit le taux d'échec de l'empreinte. C'est exactement ce contraste — une stratégie qui s'adapte contre un choix fixe — qui explique tout l'écart d'énergie de ce rapport.](results/haenel_comparison/figures/figure_1_energy_comparison.png)

## Pourquoi cela ne veut pas dire que B5 est "meilleur"

B5 consomme moins d'énergie ici, mais son taux d'erreur de sécurité
(0,2%) reste plus élevé que celui du code cryptographique (quasi
zéro). P0 fait un choix différent : il privilégie la sécurité
prouvée plutôt que l'économie d'énergie, dans ce compromis précis.
Ce n'est ni un échec de P0 ni une victoire de B5 — c'est un choix
différent, avec ses avantages et ses inconvénients, qu'on a
entièrement expliqué et vérifié.

## Les limites à connaître

- On n'a jamais mesuré de vrai matériel : tout est calculé à partir
  de fiches techniques et de valeurs publiées.
- Le résultat "P0 choisit toujours le code cryptographique sous
  poids égaux" est spécifique à ce scénario précis (deux choix
  seulement, pas d'attaquant simulé dans cette partie, gestion de
  clé désactivée) — il ne se généralise pas forcément aux autres
  scénarios du projet (qui restent la référence principale et n'ont
  pas été modifiés).
- Le test de sécurité renforcé (100 000 tentatives simulées) montre
  que P0 n'accepte aucune attaque, mais ce n'est PAS une preuve
  qu'il est plus sûr : son taux d'erreur théorique est tellement
  petit qu'il est normal de ne rien voir, même avec beaucoup
  d'essais. C'est une limite du volume de test, pas une découverte.
