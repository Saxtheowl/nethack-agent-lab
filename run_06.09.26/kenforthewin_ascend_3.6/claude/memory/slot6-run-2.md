# Emplacement 6, run 2 — journal (état le plus récent en haut)

STYLE TARIRU V2 — PATIENCE (memory/tariru-style.md PUIS memory/style-tariru-v2.md, obligatoires ; objectifs durs : HP ≥ 50 %, AC ≤ 3 à T1500 / ≤ 0 à T3500 / ≤ −5 à T5000, rien sous Minetown avant AC ≤ 0, Dlvl ≤ 10 jusqu'à XL10 et AC ≤ −5)
Lire d'abord « DEATH » et « Lessons » de memory/slot6-run-1.md (mort T10049, soldier ants à Sokoban 3).
Jamais de boucle qui passe des tours sans vérifier les HP ET la faim (waitpet, rest, explore, scripts Sokoban).

## DEATH T11449, Sokoban niveau 4 (Dlvl6), XL8, HP max 97, AC-3 : "killed by a cobra"
Chaîne : Sokoban 1 (1b), 2 (2a), 3 (3a) résolus avec les solutions nethackwiki vérifiées par simulation
(slots/6/sokoplan.py, arrêt sur monstre/HP/faim à chaque touche). Sokoban 4 (4b) : 11 trous sur 18 remplis ;
2 giant mimics (dont un déguisé en boulder en trop), un zruty tué à la wand of cold, gremlin tué.
Un couatl PEACEFUL me suivait et bloquait les poussées ; j'ai écrit slots/6/sokoloop qui, sur « STOP monster A »,
« no move » ou « PLAN FAIL », faisait `n3s` (3 tours de recherche) puis réessayait, jusqu'à 40 fois,
SANS AUCUN contrôle de HP. Un cobra (caché : marqueur I derrière la boulder) m'a mordue pendant ces recherches :
81 -> 5 HP sans que je le voie, puis mort au moment où je reprenais la main. Prayer disponible (dernière T6584).
Leçons :
- JAMAIS de boucle qui passe des tours (s, n3s, retry) sans vérifier HP ET messages (« bites », « hits ») à CHAQUE tour.
  C'était la règle écrite en tête du journal ; je l'ai violée dans un script écrit à la hâte.
- Une boucle d'attente pour un peaceful doit s'arrêter dès qu'un AUTRE monstre est visible ou qu'un « I » apparaît.
- Avant toute action après un script long : lire la ligne HP d'abord. À HP 5/97 il fallait PRIER, pas attaquer.
- Sokoban 4 : les boulders « en trop » peuvent être des giant mimics ; un monstre immobile derrière une boulder
  (« You hear a monster behind the boulder ») = mimic : wand of striking brise la boulder, puis tuer le mimic.
- Positif : potions uncursed bues en lieu sûr = gain level + full healing ; unicorn horn (gray unicorn XL8 facile).

## Current state
URGENT: PARTIE TERMINÉE — morte T11449 (voir DEATH ci-dessus). Ne pas reprendre ce jeu.
Wielded: blessed rustproof +3 Excalibur. Worn: splint mail -1, dwarvish iron helm (hard hat), iron shoes, dwarvish cloak, small shield +3, old gloves (brûlés + pourris), amulette q spherical (uncursed, inconnue, pas d'effet visible).
Intrinsics: telepathy (floating eye), cold res (Valk).
Wands: i striking, p cold (marble, nommée), t lightning (oak). Rings: X agate (uncursed, inconnu).
Food: 1 food ration K, 1 slime mold h ; crocodile mangé T8990 (-> Hungry vers ~T9900). Horse corpse frais en 14,17 (T9278).
Potions: d ruby, C brown, v puce, o sky blue(uncursed x2), V brilliant blue, N dark green, R milky (tous inconnus). Scroll f PRIRUTSENIE (uncursed). Candles: 7 blessed + 1. $32.
Poids ~ limite : les couloirs diagonaux (« carrying too much to get through ») bloquent ; ne pas ramasser d'objets lourds.
Carte: Dlvl9 Oracle ('<' 12,15, '>' 27,24). Dlvl8 '>' 68,25, vault 13-14,26-27. Dlvl7 altar chaotique 44,17 + Elbereth brûlé. Dlvl4 ALTAR LAWFUL 70,14. Dlvl3 '>' 74,16 (porte secrète 71,25).
Mines : Dlvl6 Minetown watch hostile (captain mort) ; Dlvl8 master mind flayer ; Dlvl9 chameleon + mon large dog.
IDs: XOR OTA = teleportation, HAPAX LEGOMENON = magic mapping, ASHPD SODALG = enchant weapon.
Prochaine étape : Sokoban (monter ici). Outil planner : scripts/sokoban.py X Y PUSHES ; solutions nethackwiki « Sokoban Level 1a/1b ». Stopper tout script sur HP/faim.
Outils perso slots/6/ : auto (xp+hold), xp, hold (liste DANGER), wp, srest, elb (Elbereth relu), unstick (bear trap), follow (vault guard), map, dip, explore6.py.

## Lessons
- (voir slot6-run-1.md) Sous ~20 HP face à des monstres dangereux : prier si la prayer est probablement disponible.
- Outils perso : /tmp/claude-1000/soko_try.sh (Sokoban), xp6 (explore), hunt6 (attaque), map6 (carte).
- T3813 : FAINTING sans l'avoir vu : mes boucles (wp, t, go) ne regardaient pas la faim, et j'avais retiré « Hungry » des stops de xp/hold. Une Valkyrie mange ~1 nutrition/tour : food ration = ~800 tours. Noter T du dernier repas et manger dès « Hungry ».
- Excalibur à Minetown : la fontaine disparaît et le watch devient hostile (watch captain = 40 HP en 2 tours). Faire le dip HORS de Minetown (Dlvl1 fountain).
- Scroll of teleportation non testé = peut être cursed (level teleport). Tester à l'altar avant de compter dessus.
- explore/xp m'a ramenée À CÔTÉ du master mind flayer : quand un monstre mortel est sur le niveau, ne plus utiliser l'explore auto.
- T6581 : mangé un « wererat corpse » en répondant y sans lire → lycanthropy ; guérie par prayer T6584 (« You feel purified »). TOUJOURS lire le nom du corpse (were*, kobold, cockatrice...).
- Dlvl3 main : couloirs en diagonale « You are carrying too much to get through » (poids > 600) : j'ai dû poser mes affaires en 23,21.
- Dlvl8 main : vault 13-14,26-27 (plein d'or, j'y ai laissé mes 210 gold) ; teleporter 'ad aerarium' sous la salle fontaine du <.
- Le chameleon en arch-lich (Mines Dlvl9) a invoqué un umber hulk : fuir par l'escalier immédiatement.
- auto/xp : IGNNAME pour ignorer les monstres triviaux ; les statues et peacefuls sont filtrées par farlook (lent : ne pas lancer plus de 2 tours d'auto par appel de 110 s).
- Farlook ne dit pas toujours « tame » : vérifier la ligne PETS avant d'attaquer un d.
