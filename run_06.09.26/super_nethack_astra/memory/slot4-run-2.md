# Emplacement 4, run 2 — journal (état le plus récent en haut)

STYLE ASTRA (memory/astra-style.md). Lire aussi slot4-run-1.md (mort : giant bat, boucle de combat sans HP).
Outils perso : slots/4/kk (touches répétées, arrêt HP/monstre), slots/4/ff (F+dir avec arrêt HP),
slots/4/xp (explore par tranches, arrêt monstre/HP/faim). NE JAMAIS utiliser `fight`.

## DEATH (T20602, Dlvl 27 Medusa, XL11, 72576 pts) — drowned in deep water
Chaîne : D26 exploration auto (xloop) -> l'explorateur m'a fait entrer au contact d'un ARCH-LICH (touch of death possible, pas de MR, life saving NON portée), HP 92->47 en un tour (frost + psi). Fuite correcte : wand of digging vers le bas -> Dlvl 27 = Medusa (arrivée près du '<', entourée d'eau). Une trentaine de RAVENS : Elbereth gravé OK mais il s'est effacé ; aveuglée, 4 ravens autour, HP 36. J'ai re-zappé digging vers le bas pour fuir au Castle : la case touchait l'eau -> « the hole fills with water » -> je suis tombée dans une piscine, aveuglée, cases voisines = eau ou ravens -> impossible de ramper -> noyée. L'amulet of life saving était dans le sac, pas au cou.
### Lessons (mort)
- NE JAMAIS creuser (wand/pick) vers le bas sur une case ADJACENTE à de l'eau/moat/lave : dig.c fillholetyp() transforme le trou en POOL et on se noie (surtout aveugle/encerclé). Sur Medusa, creuser seulement loin de toute eau, ou pas du tout.
- En danger sur un niveau d'eau : enfiler d'abord les LEVITATION BOOTS (W s) -> ni noyade ni eels, puis fuir en flottant.
- Porter l'amulet of life saving dès qu'on descend sous Dlvl ~20 sans magic resistance ? Arbitrage reflection/life saving : sans MR, un arch-lich ou un master lich tue d'un touch of death ; reflection ne protège pas des sorts. Idéalement GDSM/cloak of MR avant les liches.
- L'auto-exploration (xloop/xa.sh) m'amène au contact de monstres inconnus : sous Dlvl 25, farlook chaque lettre avant de continuer ; arrêter l'auto-explore dès qu'un L, un & ou un H apparaît.
- Les ravens (Medusa-4 en a des dizaines) aveuglent et entourent ; Elbereth dans la poussière s'efface vite. Il fallait remonter le '<' tout proche AVANT d'être à 36 HP.
- Les leprechauns : un seul rescapé a volé 6600 zm ; tuer tout le hall avant de ramasser et garder l'or loin.

## Current state
URGENT: MORT T20602 — noyée ("drowned in deep water") sur Dlvl 27 = niveau de MEDUSA, XL11, 72576 points. Partie terminée, NE PAS relancer (décision de l'utilisateur).
D10: '<' 72,27, '>' 5,25, fountain 6,23, LEPRECHAUN HALL 69-74,12-15 (quelques l restants avec ~1000 zm dont les miens ; un l a une wand of teleportation). Scroll TEMOV = teleportation (vu lu par un l). Potion milky = invisibility probable (bue par un l).
D22: TEMPLE DE TYR (LAWFUL, co-aligné) altar 74,26, priest peaceful. '<' 56,27, '>' 67,18, trap door 55,25, graves 55,26 55,28 69,17.
D24: '<' 7,26, '>' 22,15, altar LAWFUL 74,15 (pas de priest ?), fountain 52,22. Exploré T19425.
D23: '<' 54,27, '>' 46,13, fountain 66,20 (Medusa = D24 probablement).
D21: '<' 53,17, '>' 41,27, boulders 37,16 et 30,18, piège ^ 29,25.
D20: '<' 60,24, '>' 49,18, leprechaun (a volé ~700 zm).
D19: '<' 26,23, '>' 8,22.
D18: arrivée 41,26 (trou), '<' 67,27, '>' 52,14. Ogre king invisible tué. Mind flayer tué, gray unicorn tuée 36,24 (horn laissée).
D17 = ROGUE LEVEL : '<' 45,27 ; creusé à 60,18.
D16: '<' 24,13, '>' 76,22, BEEHIVE 65-71,13-15 vidée (queen bee tuée), dwarf king peaceful. Pièges ^ 38,24.
D15: '>' 44,26 ; arrivée 10,13 (succubus tuée). D14: '<' 61,25, '>' non trouvé (creusé à 26,22).
D13: '<' 43,16, '>' 34,25 (harp G ramassée à côté). 
D11: '<' 5,14, trap door quelque part vers l'est (tombée vers D12). D12 = QUEST PORTAL (magic portal 11,13 (small mimic tué à côté ; fountain 10,13 ; land mine 8,12 → pit)) : '<' 54,12, '>' 39,18, sink 53,25, throne room pas encore vue (ogre king tué). Home quête : fire ants + fire giants, retour à XL14.
Porté: a blessed rustproof +1 EXCALIBUR, c blessed +3 small shield, k uncursed +0 ALCHEMY SMOCK (brûlé/pourri, poison+acid res), n ORCISH HELM (D16, remplace le helmet détruit T15975) + Z orcish chain mail +1 (Mordor orc D16), d iron shoes (dwarf D16, BUC ?) → AC-4.
Sac: F elven dagger, W orcish dagger, L 8 darts, l uncursed elven cloak, Q wand of lightning, X wand of striking, R iron ring, Y topaz ring,
  S+T scrolls of earth, N scroll of remove curse, v scroll of teleportation, potions u black, K cyan x2, O effervescent, D stethoscope, w lock pick,
  gems p violet, r 5 white, y 2 yellowish brown. M 7 food rations, V lizard corpse.
Scrolls identifiés : ELBIB YLOH = remove curse, GARVEN DEH = identify, MAPIRO = teleportation, READ ME = light,
  EIRIS SAZUN IDISI = genocide (lu T6973 : water nymph), ZLORFIK = earth. Potion murky = gain level (vue).
Manger les corpses frais (pas de dwarf : cannibalisme ; pas de nymph : teleportitis ; pas de were*).
D1: '<' 26,16, '>' 74,27.
D2: '<' 24,12, '>' 65,27, fountain 20,13, SINK 73,28, WEAPON SHOP 6-9,15-17 : PLATE MAIL 800 zm, tripe 20.
D3: '<' 61,12, '>' 18,26 (via porte cachée 24,16 puis porte 19,24), iron bars 37,23.
D4: '<' 6,15, '>' 50,15 (main), MINES '>' 75,18 (salle est), teleport trap 43,27, anti-magic 21,20, porte cachée 48,28.
D5: '<' 74,26, '>' 62,28, brown pudding (ne pas frapper au fer) vers 20,14. Sokoban '<' PAS TROUVÉ après ~15 recherches (murs E/N/S cherchés) — abandonné pour l'instant. Vault quelque part.
D6 = ORACLE (Delphi) : '<' 14,13, '>' 68,15.
D8: '<' 7,22 (reste du niveau caché, creusé vers le bas depuis 7,19). D9: arrivée 69,13 ; trap door 76,24 (salle 72-77,23-26 via porte cachée 76,22).
D7: '<' 18,18, '>' 28,19, SOKOBAN '<' 61,20 (Sokoban ENTIÈREMENT résolu, prize = amulet of reflection) (l'entrée Sokoban est au niveau SOUS l'Oracle, pas au-dessus !).
Mines: D5 '>' 24,27 ; D6 '>' 10,16, FIRE TRAP 30,18 ; D7 = MINETOWN : '<' 13,14, '>' 68,14, delicatessen (Patjitan) 51-53,25-26, general store (Tuktoyaktuk) 40-41,24-26 porte 40,23 (orcish cloak 67), 2e deli Baliga 45-46,19-21, HARDWARE Nosnehpets 28-29,24-26 (PICK-AXE 67 zm, lamp 89, camera 267), TEMPLE d'Odin (cross-aligned) 50-53,20-23, porte 49,22, altar 52,21, priestess (protection achetée T10959). sink 48,25, fountain 37,27.


## Lessons
- T17863 : xa.sh/adjfight a frappé un FLOATING EYE (tué par chance, pas paralysée). Retiré e, j, F de la liste des glyphes de xa.sh/restfight.sh : les traiter à la main (darts).
- T18130 potions bues au temple : pink = ENLIGHTENMENT (Luck positive, "You can safely pray", piously aligned), fizzy = confusion, swirly = gain energy, black = sleeping. Aucune levitation. Rings h,S,U,Y portés sans message (pas levitation).
- ANALYSE Castle (dat/castle.des) : entrée ouest = antechamber 8 soldiers + lieutenant, puis THRONE ROOM (27 monstres L,N,E,H,M,O,R,T,X,Z) avant tout accès aux tours (wand of wishing dans un coin au hasard) et aux trap doors. Impossible à XL11. Il faut levitation/water walking pour la porte arrière est (door 56,08). Medusa-2 : île d arrivée NON diggable + titan. Medusa-1 : arrivée diggable. Perseus : levitation boots 25% (75% en medusa-2). Plan : trouver levitation (throne D12 : wish possible en s asseyant, Luck>0).
- T19521 : snow boots = LEVITATION BOOTS (trouvées cursed D25 18,15 ; boots cursed = souvent fumbling/levitation). Remove curse lu en les portant, puis retirées.
- T18983 : rock troll (halberd) = ~17 dégâts/tour ; il ressuscite (même pendant qu on le mange). Wand of sleep vide. Le tuer plusieurs fois = ~200 XP par mort.
- Fort Ludios : portal dans le vault 2x2 de D20 (5,26). Chambre d arrivée vue sans porte ; alarme réveille tout.
- T19784 D25 : rust traps (6,16 / 7,18) : iron shoes very rusty, orcish helm thoroughly rusty -> AC -5 à -2. L explorateur marche sur les pièges.
- T20019 : brass wand = undead turning ; copper ring = warning ; steel ring = POLYMORPH CONTROL. Leprechaun hall D25 (70-76,24-28) : 10693 zm, puis un leprechaun rescapé a tout revolé (il fuit tant qu il a plus d or que moi). Garder l or dans un sac / ne pas le porter près de leprechauns.
- Plan Medusa : amulet of reflection portée. Pas de lévitation/water walking : option = creuser vers le bas sur le niveau de Medusa (pas de hardfloor, vérifié dat/medusa.des + Can_dig_down) → arrivée aléatoire au Castle (DANGEREUX à XL10) ; mieux vaut d abord monter XL/AC. Helpers : xa.sh (1 tour d explore + combat adjacent), pick.py MOTIF X,Y..., chase.py N GLYPHE, holdfight.sh, restfight.sh CIBLE, digeast.sh DIR N (creuser en ligne).
- Potions identifiées T16296 : cyan = speed, effervescent = extra healing (B reste), magenta = gain ability, emerald = fruit juice/see invisible, (s) = healing.
- T15975 : lu un scroll inconnu SANS cloak (enlevé pour le protéger) → destroy armor a pris le HELMET (pas la body armor). Garder le cloak le moins précieux sur soi quand on lit un inconnu, ou accepter la perte. Scroll KERNOD WEL = destroy armor, FNORD = magic mapping, ring diamond = cold resistance.
- T15540 Dlvl18 : MIND FLAYER au corps à corps (tentacules bloquées par le helmet, In 13 intacte). adjfight ne gérait pas --More-- (">>") : corrigé (Enter auto). Garder TOUJOURS un casque.
- T15028 : F (fight) sur un dwarf PEACEFUL ne demande PAS confirmation : adjfight.py regarde maintenant chaque cible (look) et saute les peaceful.
- T12260 : j'ai posé 766 zm près du < pour combattre un leprechaun hall : un leprechaun a tout ramassé. Sur un niveau à leprechauns, garder l'or sur soi (ou dans un sac), jamais par terre. Les l réveillés fuient avec l'or : inutile de les poursuivre.
- slots/4/adjfight.py GLYPHES [n] : frappe (F) le monstre adjacent dont le glyphe est dans la liste, arrêt HP<60%/grosse perte/prompt.
- slots/4/auto.sh N : explore+combat automatique (arrêt sur danger/peaceful/HP<50%/statut). slots/4/rest_elb.sh N CIBLE : repos par n10s avec contrôles. En number_pad, le compte se tape n10s (pas 10s).
- xp/explore dit « no reachable frontier » à l'arrivée par trou/trap door : explorer à la main (portes cachées) ou creuser.
- Orc shaman : psi bolt + stun ; attendre la fin du stun avant de frapper.
- Prize Sokoban : il n'était plus dans le placard (Elbereth + scroll of scare monster, 43,27) : un monstre humain (werejackal @ / hobgoblin) l'avait pris ; retrouvé dans la pile de sa mort (51,25). Les monstres HUMAINS et PEACEFUL ignorent le scroll of scare monster. J'ai tué 2 gnomes peaceful pour rien.
- Gas spore (e gris) : tuer à distance (darts) quand aucun peaceful n'est à côté.
- Giant mimic (fausse "boulder" dans le zoo) : 2x3d6 ; lent (speed 3), le tuer vite.
- Zoo Soko T9950 : une nymph a volé l'amulet of life saving pendant que j'étais endormi (ma propre sleep ray a rebondi sur la porte ouest et m'a touchée). Ne JAMAIS zapper sleep le long d'une ligne courte qui rebondit vers moi. Sokoban = no-teleport : la nymph reste, on la tue et on récupère.
- Zoo : un chameleon (rust monster/gargoyle/white dragon...), wargs (2d6, rapides) : combattre depuis le couloir 51,25 (une seule case adjacente), pas depuis l'embrasure (attaques diagonales possibles).
- Soko 4b : solution wiki + slots/4/wiki2plan_gen.py (carte étiquetée + liste de coups en fichiers) ; reprise après interruption : soko_where.py (index par comparaison du plateau) puis soko_resume.py (recalcule la marche).
- Soko 3b T9161 : j'ai ajouté un "2" de trop en recollant un chemin à la main → rocher coincé dans le coin ; rattrapé avec un scroll of earth lu À CÔTÉ du dernier trou (le rocher tombé plugge le trou). Ne jamais retaper un chemin à la main : recalculer avec reach/path.
- Soko 3b : la porte finale (49,23) était verrouillée : lock pick w (apply, 8, y).
- Sokoban niv.3 : récupérer la solution wiki (Sokoban_Level_3a/3b selon la carte) puis wiki2plan (adapter étiquettes/positions).
- Solutions wiki : WebFetch nethackwiki.com/wiki/Sokoban_Level_Xy (map étiquetée + coups) → slots/4/wiki2plan.py (simulation+chemins) → soko_exec.py. Marche bien.
- Sokoban niv.2 (soko3-2, 16 rochers/12 trous) : glouton par étapes se bloque ; slots/4/soko_solve2.py (A* + cases mortes) lancé sur le worker.
- Sokoban : slots/4/soko_solve.py (solve_fill) calculé via slots/4/onworker (pas en local : RAM), exécuté par slots/4/soko_exec.py MAP OX OY NEED plan.json [--from N --max M] ; écran x=col+33, y=row+15 pour soko 1.
- Ne pas attaquer/zapper depuis une case Elbereth (« hypocrite », -1 alignement).
- Sokoban = escalier montant du niveau Oracle+1 (j'ai perdu ~1500 tours à chercher au-dessus).
- T7406 : werejackal (d) m'a mordue pendant un search → lycanthropie (« You feel feverish ») ; guérie par prayer T7410. Tuer les were* à distance / en premier, ne pas faire de search long quand un d rôde.
- Dans Minetown, les moves bruts vers un peaceful donnent « Really attack? » : kk répond n et s'arrête ; « Call a ... : » (potion vue) mange les touches : kk s'arrête si le curseur est en ligne ≤9.
- Prochain objectif : Sokoban (niveau au-dessus de l'Oracle). Revenir à Minetown avec de l'or : pick-axe 67, plate mail D2 800.
- T4720-4820 Dlvl7 : des monkeys ont volé elven cloak, dagger b, scroll of teleportation, 4 white gems, violet gems. Les tuer à vue, ne pas les laisser adjacents.
- Fire trap Dlvl6 30,18 : potions bouillies, max HP -7, smock brûlé.
- slots/4/xp (explore) se bloque souvent (« no reachable frontier ») : effacer la clé du niveau dans .runtime/explore-4.json ou naviguer avec go.
- Lire les scrolls inconnus : enlever d'abord cloak+shield (destroy armor).
- slots/4/elb grave Elbereth et vérifie.
- T1659 : repos sur Elbereth avec kk sans test de faim → Fainting ! (kk teste maintenant Hungry/Weak). Prayer T1659 OK.
- Giant bat : 2 morsures/tour ; à HP bas, Elbereth tout de suite (marche contre B).
- Combat : un coup, relire. Prier sous 1/7 HP (prayer timeout initial ~300).
- Bear trap : sortir en diagonale.
- Food : Valkyrie a faim vite ; manger les corpses frais sûrs.
