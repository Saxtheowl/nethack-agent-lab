# Slot 4 — run 4 (Claude4, style astra) — lawful female dwarven Valkyrie


## DEATH (T9315, Sokoban niv.4 = Dlvl 6, XL9, 22540 pts) — killed by a leocrotta
Chaîne : puzzle Sokoban 4b résolu (un rocher détruit à cause d'un giant mimic, dernier trou bouché avec scroll of earth). Une mountain nymph a ouvert la porte du zoo (50,25). J'ai combattu au goulot (couloir 51,25) avec hold.sh (min HP 42) : killer bees, lynx, golem, water elemental, wolf... tous tués, mais HP 109 -> ~60. Un CHAMELEON du zoo (gray dragon -> salamander -> hell hound -> ... -> leocrotta) : leocrotta = vitesse 18, 3 attaques 2d6 -> ~2 rounds par tour = jusqu'à 72 dégâts/tour. HP ~60 -> 0 entre deux vérifications du script. Prière disponible (dernière T5483) mais jamais utilisée : le script ne pouvait pas réagir.
Identités à la mort : amulet circulaire d = STRANGULATION (cursed !), pyramidal Q = ESP ; combat boots = elven boots ; scroll teleportation cursed ; tin werewolf meat blessed.

### Lessons (mort)
- NE PAS combattre un zoo (Sokoban) avec un script de combat automatique à seuil fixe : un monstre rapide à attaques multiples (leocrotta, soldier ants, chameleon qui se transforme) fait 50-70 dégâts entre deux contrôles. Au-dessous de ~70% HP face à un zoo : se retirer, Elbereth, se soigner AVANT de reprendre.
- CHAMELEON dans le zoo (« X turns into Y ») : le traiter comme le pire monstre possible ; farlook à chaque tour.
- Seuil de prière : prier dès HP < 1/7 max ; mais un script ne sait pas prier -> ne jamais laisser un script combattre sous 60% HP quand plusieurs monstres forts sont présents.
- AC5 était trop faible pour un zoo niveau 9 : il fallait d'abord améliorer l'armure (gloves/elven boots dans le sac non portés faute d'altar ; porter les objets de soldat testés).
- Amulet circulaire = strangulation cursed : bonne décision de ne pas porter sans BUC.
- Nymphs : 3 vols dans la partie (Minetown catastrophe, D9). Script de marche doit s'arrêter sur 'stole'.

## Current state
URGENT: MORTE T9315 — tuée par un LEOCROTTA (chameleon) au zoo de Sokoban niv.4 (Dlvl 6), XL9, 22540 points. Partie terminée, NE PAS relancer.

## Levels
D5: < 21,23, > 20,13, fountain 51,26 (l'autre 20,24 disparue: Excalibur).
D6: < 23,24, LEPRECHAUN HALL 62-70,14-18 (Elbereth GRAVÉ permanent 63,16), 174 zm à moi posés 52,18. Statue nymph 6,16.
D6 suite: > 72,27. Leprechauns invisibles restants (vol).
D7: < 61,26, > 9,13.
D8: < 4,26, > 9,12. Porte verrouillée 47,13 (non ouverte).
D9 = ORACLE: < 69,14, > 73,28, fountains centre 39-41,20-22, magic trap 15,23. Mountain nymph (a volé bronze ring) rôde.
Soko1 (1a) RÉSOLU T6869 ; items ramassés: jade ring l, 2 scrolls earth (ANDOVA BEGARIN o,p), tin q, food ration r, iridium wand t.
Soko2 (2a) RÉSOLU T7772 ; gray unicorn tuée -> unicorn horn v.
Soko3 (3b) RÉSOLU T8420 ; tiger eye ring N, food ration L, tripe F, cream pies, fortune cookie E.
D10 = BIG ROOM (très peuplé: soldier ants, démon &, centaur crossbow, shapeshifter, nymph). < vers D9 à 57,23 ; < SOKOBAN à 46,23 ; > 18,27.
D7 = MINETOWN : < 68,14, > 10,23, temple d'Odin (neutral, cross) altar 37,17, fountain 55,27, shops ( 51-53,16-17 et ! % 53-54,22-23, watchmen. Nymph rôde.
D1: < 35,25, > 50,14. Kitten perdu.
D2: < 42,26, > 40,16. Pas de branche Mines vue (ouest non exploré au nord-ouest?).
D3: < 47,24, > 36,21 (= MINES), > 3,22 (main), yellow mold 58,12, red mold 5,19.
D4: < 47,17 (vers D3 3,22), > 22,14. Explore fini.
Mines: D4 (mines 1) < 74,23 > 77,24.; D5 < 34,28 > 44,26 (anti-magic 39,22); D6 < 27,22 > 37,20

## Intrinsics
- cold res (Valk), FIRE RES (red naga T5890), stealth (Valk).

## Identified items
- copper wand = DIGGING (J, engrave-ID T4440). Maple wand K : non testé. H potion of speed. I scroll FOOBIE BLETCH ?. 
- murky potion = confusion (appelé conf). Scroll VAS CORP BET MANI = enchant weapon (lu). Runed wand = striking.
- Riding boots CURSED laissées sur l'altar Minetown (levitation/fumble probable).

## Lessons
- T4960 : un leprechaun INVISIBLE m'a pris 1476 zm ("purse feels lighter") sur D6. Les attaques 'miss wildly and stumble' = monstre invisible/déplacé.
- T3830-3860 CATASTROPHE : goto.sh ne s'arrêtait pas sur 'stole' -> la mountain nymph de Minetown a TOUT volé (ring mail, helm, shield, daggers, towel, potions, scrolls). AC 10. Tout script de marche doit s'arrêter sur steal/stole/seduce et sur n/l visible.
- T3830 : goto.sh/adjfight incluaient 'n' -> j'ai frappé une mountain nymph au contact, elle a volé mon +3 small shield. Retirer n et l des listes auto ; nymphs = daggers/wand à distance.
- Minetown : Excalibur dans la fountain de la ville = angry_guards (fountain.c) ! Et après l'avertissement du watchman, le prochain dryup assèche + fâche le watch. Fountain Minetown 55,27 AVERTIE : ne plus y toucher. Chercher une fountain hors ville.
- T1678 : ma boucle `for i..; do xa.sh` ne regardait pas la faim -> Fainting ; sauvée par prière. Toujours utiliser xx.sh (s'arrête sur hunger) ; manger/prier dès Weak.
- Boucles kick/fight : tester la ligne 07 seulement (l'historique des messages contient les vieux 'WHAMM'/'kill') -> jambe blessée en kickant le vide.
