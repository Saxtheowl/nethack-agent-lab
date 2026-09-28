# Slot 6 — run 3 (Claude6, game Claude6-2026-09-27.16:31:20) — style tariru_v2 (Patience)

URGENT: PARTIE TERMINÉE — morte T1824 Dlvl3 ("killed by a wand", shopkeeper Yildizeli). Ne pas reprendre ce jeu.

## DEATH T1824, Dlvl3, XL2, HP 16->0 /31, AC6 : killed by a wand (wand of striking du shopkeeper)
Porte verrouillée '+' au bout d'un couloir (67,14) sur Dlvl3 : je l'ai enfoncée à coups de pied (k6) SANS regarder
ce qu'il y avait derrière. C'était la porte d'une ARMOR SHOP. Porte cassée depuis l'extérieur -> "How dare you break my door?",
shopkeeper en hot pursuit : wand of striking 31->16, puis 16->0 le tour suivant. Pour apaiser un shopkeeper en colère
sans dette il faut 1000 gold (shk.c dopay) ; j'en avais 60. Scroll inconnu lu en urgence = confuse monster.
Prayer jamais utilisée (inutile contre un shk de toute façon).

## Règles perso (leçons runs 1-2)
- Aucune boucle qui passe des tours sans contrôle HP/faim/"stole" à chaque tour. sokoloop retiré.
- HP < 1/7 max et prayer OK -> PRIER. HP < 60% -> reculer.
- Lire le nom des corpses. Pas d'Excalibur dans une fontaine de Minetown. Tuer les nymphs à distance.
- BUC-test avant de compter sur un objet (scroll teleport!).

## Journal

## Lessons
- NE JAMAIS kicker une porte verrouillée sans savoir ce qu'il y a derrière. Une porte fermée au bout d'un couloir
  vers une pièce inconnue peut être une SHOP ("Closed for inventory" ou shopkeeper derrière). Avant de kicker :
  lire la porte (`:` n'aide pas) -> essayer #force/unlocking tool, ou frapper à côté : chercher un autre accès, ou
  simplement IGNORER la pièce. Si on doit kicker, avoir >= 400-500 gold et se tenir ADJACENT à la porte (on reçoit
  alors "Pay?" si on a assez d'argent : shk.c pay_for_damage), sinon c'est la mort à bas niveau.
- Une Valkyrie a faim vite en début de partie : food ration mangée en 2 fois T858/T1454, Hungry de nouveau à T1777.
  Manger les corpses frais sûrs (jackal, fox, newt) dès qu'on n'est pas Satiated ; garder la ration pour l'urgence ;
  Weak sans nourriture -> prier (timeout initial ~300).
- Outils : xp/explore6 ne franchit pas les portes ; `slots/6/w ./auto` doit être lancé avec timeout long ; t/grab
  se font interrompre par des monstres (vérifier la position après).
- Dlvl3 de ce jeu : 2 escaliers '>' (22,26 et 45,27) -> entrée des Mines ici ; fountain 59,26.
