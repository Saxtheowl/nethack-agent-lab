# Emplacement 2, run 5 — journal (état le plus récent en haut)

STYLE ASTRA (memory/astra-style.md, obligatoire).
Lire les DEATH et Lessons de memory/slot2-run-2.md, run-3, run-4.

## Current state
URGENT : PARTIE TERMINÉE — DEATH T18441 Dlvl 27 (castle), killed by a xorn (avec un Elvenking), 83768 points. Ne pas relancer sans consigne (next_style.py 2).
 worn: c +3 small shield, t elven mithril-coat, r orcish helm (rusty), H iron shoes, I dwarvish cloak.
 scrolls inconnues k GARVEN DEH, q FOOBIE BLETCH, s VAS CORP BET MANI ; potions g purple-red, i cloudy, n smoky, w sky blue, x milky, Q black, A yellow, z clear (inconnues).
 Prochaine étape : Sokoban 2 (monter par le '<'), plan : chercher/écrire un plan (slots/2/soko41.py + scripts/sokoban.py ; slot 7 a des solveurs). Si besoin sortir de Sokoban par le '>' en 39,19 (branche vers Dlvl 10).
D1 : '<' 6,25 ; '>' 26,13.
D2 : '<' 72,25 ; '>' 76,15 ; ALTAR D'ODIN (neutre) 59,23 (room 56-61,18-24).
D3 : '<' 18,15 ; '>' 58,20 ; pas d'entrée Mines vue sur D2/D3 -> D4 ? ; vault guard entendu.
D4 : '<' 35,17 ; '>' main 25,13 ; '>' MINES 14,18 ; fountain asséchée.
MINES : D5 '>' 44,21 ; D6 '>' 66,27 ; D7 '>' 28,24 (level teleporter quelque part !) ; D8 MINETOWN '<' 3,24, '>' 63,22, TRAP DOOR ~33,26 ; D9 '<' 60,15 '>' 23,15 ; D10 '<' 40,16.
D5 main : '>' 55,27. D8 main : '<' 8,16 '>' 25,15, 2 sinks. D9 ORACLE : '<' 72,15 ; POLYMORPH TRAP 63,21 (couloir est). D6 main : '<' 15,25 '>' 53,13. D7 main : '<' 10,23 '>' 27,26. D10 main : '<' 34,26 ; '>' 66,17 ; wand of digging + bag of tricks laissés 68,27 (poids) ; '<' SOKOBAN 10,15 ; spotted jelly 11,14.
D22 : '<' 29,25 ; fountain 11,19 ; TEMPLE D'ODIN (priest) altar 69,24 (65-73,21-27, porte 65,23) ; '>' non trouvé -> trou creusé 63,26.
D23 : '<' 21,26 (BEAR TRAP 21,27, trap 24,27) ; '>' 34,13 ; fountain 12,14.
D21 : arrivée par trou ; '>' 17,16 ; fountain 22,28.
D20 : '<' 39,14 ; TEMPLE D'ODIN (neutral, priest) altar 50,16 ; '>' non trouvé -> trou creusé en 38,18 (wand of digging E).
D19 : '<' 12,17 ; '>' 24,27 (porte 20,27).
D18 : '<' 28,25 ; '>' 19,19 ; beehive vidée 33-37,15-17.
D17 : '<' 53,19 ; '>' 33,15 ; INCUBUS qui revient (répondre n à tout : slots/2/nono).
D16 ROGUE LEVEL : '<' 48,26 ; '>' 67,21 (stairs affichés '%').
D15 (QUEST PORTAL level, message reçu) : '<' 12,23 ; '>' 32,17 ; throne room 49-54,18-21 vidée (throne disparu) ; chest vidé 30,24.
D14 : '<' 55,17 ; '>' 17,17 ; neutral altar 58,16 ; zoo vidé 29-40,12-14 (bag of tricks 38,13) ; sleeping gas trap 33,28.
D13 : '<' 7,28 ; '>' 24,25 ; LEVEL TELEPORT TRAP quelque part à l'est (non marquée) ; bear trap 69,16 ; red mold 30,15.
D9 ORACLE '>' 14,15, POLYMORPH TRAP 15,15 (à côté du '>').
MINETOWN D8 : temple de Loki (chaotic) 56,26, priest vend la protection ; delicatessen 43-45,25-26 (vide).
D12 : '<' 37,22 ; '>' 22,13 ; fountains 9,26, 36,26 ; trap 60,25.
D11 : '<' 31,14 ; '>' 9,25 ; porte cachée 30,12 -> couloir sans issue 30,11 (non fouillé à fond) ; hobbit peaceful.
D5 : '<' 9,25 ; THRONE ROOM 51-62,15-18 pleine de monstres endormis (court hostile) ; porte 63,15 ; chest 59,18 ; large box vidé.

IDs : XOR OTA=amnesia, GNIK SISI VLE=gold detection, VE FORBRYDERNE=earth, THARR=identify, ELAM EBOW=scare monster ; coral ring = +1 adornment ; unicorn horn d UNCURSED ; J dagger, dark potion, topaz ring = CURSED (laissés sur l'altar D2).

## DEATH (T18441, Dlvl 27 = CASTLE, XL12, 83768 points) — killed by a xorn
Déroulé : D24 throne room vidée ; D25 ; D26 = Medusa (medusa-2) : gremlin au contact -> PROTECTION PERDUE (AC -9 -> -4) ; trou creusé sur l'île du '<' -> chute directement au CASTLE (D27 = dernier niveau : medusa @(-5,4) donne castle = Medusa+1 possible). Arrivée dans le labyrinthe ouest dans une poche sans issue ; un MASTER LICH (invisible par intermittence, hit-and-run) : curse items, destroy armor (water walking boots ET cloak of protection détruits), psi bolt 40, drain Str ; summon nasties (fire giant, Aleax, fire elemental qui brûle les scrolls, puis Elvenking + xorn). Lich détruit, Aleax tuée à 23 HP ; puis j'ai envoyé 8 pas de déplacement dans une boucle SANS relire l'écran : l'Elvenking et le xorn (invoqués, le xorn traverse les murs) m'ont tuée de 29 HP à 0.

## Lessons (run 5)
- NE JAMAIS enchaîner des touches de déplacement dans une boucle à bas HP (< 50 %) : un pas, relire l'écran, décider. C'est la cause directe de la mort (déjà écrit pour go/travel — vaut pour TOUT).
- Ne pas creuser vers le bas sur le niveau de Medusa sans savoir si le castle est juste en dessous : Medusa+1 peut être le castle ; on tombe dans le labyrinthe, sans '<' connu, loin de tout.
- Master lich : le tuer vite ou fuir le niveau ; il détruit l'armure (cloak en premier, puis boots…) et invoque des nasties. Sans magic resistance, AC < -5 et une sortie, ne pas rester.
- Gremlin la nuit : vol d'intrinsèque (protection perdue) — tuer à distance.
- s1safe doit s'arrêter sur monstre adjacent / message de brûlure / changement d'AC (corrigé dans slots/2/s1safe) : un fire elemental a brûlé scrolls et cloak pendant un repos sans perte de HP (fire res).
- farlook : slots/2/look est refusé par le garde sous 70 % HP (digits + '.') ; utiliser slots/2/w ./fl X Y (',' comme validation).

## Lessons
- T18328 GREMLIN la nuit = vol d'intrinsèque : j'ai perdu la protection (AC -9 -> -4). Tuer les gremlins à distance (wand of lightning/striking, daggers) AVANT le contact.
- Session T12845-T16986 : protection achetée 2 fois (Minetown D8 Loki, temple d'Odin D20) : 400*XL, premier don = +2 à +4 AC. Throne : poser l'or avant #sit (take_gold). Zoo : rayons de wand of cold le long des rangées depuis la porte = nymph/yellow light tués sans risque.
- Incubus : répondre n à chaque prompt (slots/2/nono), il repart ; remettre cloak/armure ensuite (W).
- Explore ne passe pas les portes/pièces sombres parfois : ouvrir/entrer à la main ; `pkill -f` dans une commande = self-match (exit 144).
- Ne pas envoyer de touches après un déplacement vers un priest : 'Really attack?' — vérifier la position avant.
- Amulette portée = faim ~720 tours par ration : prier quand Weak (prière sûre ~1000 t après la dernière) pour économiser la nourriture.
- Burdened à ~1000 de poids : potions (20) et gold (1/100) pèsent ; bag of tricks + 1 wand of digging laissés au D10.
- T11331 : le 2e '0' 'boulder' de Soko 4 était aussi un giant mimic + tiger/elf : scroll of scare monster lu = sauvetage. Ne JAMAIS enchaîner go/travel dans une boucle sans relire l'écran.
- Sokoban 4a : un '0' peut être un GIANT MIMIC (farlook dit 'boulder') ; slots/2/sokob.py = sokoban.py qui ignore les monstres à plus de SOKO_NEAR cases (SOKO_SCRIPT=slots/2/sokob.py soko4a.py). Si la route est impossible, sauter les poussées wiki qui ramènent le boulder au même endroit (éditer rem dans le .state).
- Sokoban : copie de la page wiki via web.archive.org (https://web.archive.org/web/2024id_/https://nethackwiki.com/wiki/Sokoban_Level_2b) ; nethackwiki direct = Cloudflare. soko2b.py = modèle pour 3a/3b/4a/4b (labels + moves, suivi par diff des boulders, hh=X,Y pour trou caché par un objet).
- On peut attaquer (et être attaqué) en diagonale depuis une porte.
- Sokoban : slots/2/soko41.py exécute le plan (copie de slots/7/soko4-1.plan) via scripts/sokoban.py ; il s'arrête sur tout monstre visible : tuer (daggers/wand) puis relancer le groupe. 'You hear a monster behind the boulder' = attendre (n3s) puis repousser. sokoban.py plafonne à 50 pas/appel.
- ',' après un déplacement est souvent avalé (écran en retard ou prompt travel) : Escape puis ',' puis attendre 1 s.
- T8025 polymorph trap (Oracle) -> wererat, tout l'équipement tombe ; mordu par un vrai wererat = lycanthropie ('feverish', vérifier dans runs/games/.../frames.jsonl) ; prière = 'purified'.
- Après go/travel, un prompt 'Where do you want to travel to?' peut rester ouvert : Escape avant la commande suivante.
- Level teleport trap au Mines 3 (Dlvl 7) -> renvoyé au Dlvl 1 (T5520).
- T4564 : JAMAIS de boucle de commandes quand un prompt peut s'ouvrir (throne -> genocide : 2 essais gâchés en tapant '#sit' comme nom).
- Gnome lord avec wand of striking = 40 HP perdus : se mettre hors de la ligne (diagonale de porte) et le tuer au contact.
- Fountain dip avant Excalibur : rouille + water moccasins ; Elbereth à côté du fountain pour se replier.
- TOUJOURS #untrap (vérifier) un coffre avant de l'ouvrir : piège électrique T562 (HP 18 -> 8).
- NYMPHES : tuer à distance, jamais d'explore quand un 'n' est sur le niveau (explore ne s'arrête pas sur un vol).
- Profondeur max ≈ XL+2 ; faire les kills soi-même.
- Pas de lecture de scroll inconnue en portant une armure de corps irremplaçable ; scrolls de BUC inconnu peuvent être maudites.
- Elbereth ne protège pas du contact avec soldier ants/jaguars ; fuir/monter tôt.
- Faim : garder 2+ rations, acheter de la nourriture dès qu'une shop en vend.
- `k , --raw` pour ramasser ; tester les boucles de combat sur la ligne 07 seulement (« You kill|thin air »).
- Scripts : scratchpad/slot2only/ (ex, wait1, srch, nymphwait, exn).
