# Emplacement 7, run 1 — journal (état le plus récent en haut)

STYLE ASTRA (memory/astra-style.md, obligatoire) : la méthode d'origine qui a gagné, sans BotHack.
Lire aussi les « Lessons » de memory/run-1..run-4, slot2-run-1, slot3-run-1.
Jamais de boucle qui passe des tours sans vérifier les HP (waitpet, rest, explore).

## Current state
DEATH T33013 Dlvl27 (Castle, maze ouest 7,14) : tué par un MINOTAUR. 145318 points (meilleur score). Enchaînement : jabberwock collé sur Dlvl26 → wand of digging vers le bas → atterrissage aléatoire dans le maze du Castle JUSTE à côté d'un minotaur (ignore Elbereth, ~42 HP/tour). Prière à HP 10 réussie (T33012), puis 2 rounds du minotaur (141→93→0) dans le même tour. PARTIE TERMINÉE — ne pas relancer ici.
Sokoban TERMINÉ (4 niveaux ; prize = bag of holding). Helpers slots/7 : spush (s'arrête sur blocage/prompt frais), soko_wiki.py, doorfight N MINHP (combat au contact, regex corrigée), trav KEYS X Y (travel brut quand le héros n'est pas '@').
Tout BUC-testé uncursed (altar neutre Minetown 37,17) : i 2 orcish daggers, b dagger ; scrolls f VE FORBRYDERNE, j PRATYAVAYAH, z ASHPD SODALG ;
potions h white, r pink, w puce, x murky, J ruby ; ring o bronze ; wands q iridium (=slow monster), I oak (no engrave msg).
Laissés sur l'altar : cursed dark potion, cursed jade ring. Gems C orange, D red, E 3 violet, F 2 white (non testées).
Minetown (D7 Mines, 'Grotto-like', dwarf qui creuse) : temple Odin (neutre) 37,17 ; Morven clothing 44-47,19 (elven cloak 'faded pall' 107zm, wands maple 200, silver 267, forked 356) ;
Tjiwidej deli 51-55,22-23 (food ration 60zm, dark potion 67). Mines '<' 70,15, '>' 14,14.
Large dog laissé sur main Dlvl 7 (depuis T5071).
D1 fountain asséchée. D2 sink 52,19. D3 sink 68,14. D4 '<' 66,14, Mines '>' 38,23, main '>' 57,26 (fountain D4 disparue).
D5: '<' 29,22, '>' 16,27, fountains 17,26 62,13 75,18. D6: '<' 31,25, '>' 75,24, fountain 30,26. D7: '<' 56,14, level teleport trap vers 38,25.

Dlvl26 (sous Medusa) : '<' 9,18 = remonte sur l'ÎLE DE MEDUSA (regard = pétrification ; jamais sans être Blind/reflection) ; '>' 4,25. White unicorn peaceful (co-aligné : lancer des gems = Luck). Scroll XOR OTA = enchant weapon (cursed, jeté) ; KIRJE = food detection ; Z = scroll called confuse (BUC inconnu : si cursed => Conf rnd(100)). Orange = blindness, golden = gain energy.
Castle (castle.des) : drawbridge fermé ; il faut passtune / force bolt / striking / opening, ou lévitation. Salle du trône : L N E H M O R T X Z + 4 D ; ~15 soldats ; wand of wishing dans une tour d'angle. Level teleport vers un niveau > fond du Dungeon => Valley (find_hell) sans passer le Castle.

## Lessons
- MORT : ne JAMAIS s'échapper en creusant/tombant vers le Castle : on atterrit au hasard dans le maze (minotaurs !). Le Castle n'est pas un refuge. Pour fuir un gros monstre sur Dlvl26 : l'escalier (connu) ou la plateforme scare monster, pas un trou.
- Minotaur : ~42 HP/tour (jusqu'à 76), ignore Elbereth ; seule la scroll of scare monster l'arrête. Avec une arme faible, fuir à vue ; une prière ne donne qu'environ 3 rounds.
- La scroll of scare monster posée au sol est la meilleure défense de cette partie : ne jamais s'en éloigner loin avec une arme faible ; les sorties (manger, chercher une gem) m'ont exposé au water elemental, au jabberwock, au mumak puis au minotaur.
- Elbereth en 3.6.7 : les monstres coincés l'ignorent souvent (le jabberwock et la gargoyle ont frappé à travers) ; il s'use à chaque coup reçu.
- (slot 2, mort au Castle) Creuser vers le bas sur Medusa = tomber dans le Castle, parfois dans une poche murée du maze ouest. Master lich : maudit, désintègre, summon (fire elemental brûle les scrolls) → le tuer vite ou quitter. Jamais plusieurs pas d'affilée à <50% HP (Elvenking + xorn). Gremlin au contact vole les intrinsics : tuer à distance.
- Scroll of scare monster posée sous soi = plateforme : même les @ (Elvenking) n'attaquent pas au contact ; mais les elfes tirent à l'arc.
- Fire elemental : passif de feu à CHAQUE coup de mêlée (~20-30 HP) et fait bouillir les potions. Sans fire resistance : Elbereth + distance, ou éviter.
- Camper près d'un escalier sans surveiller les 'n' : une nymph a volé Excalibur (T30156). Toute nymph visible = la tuer à distance AVANT qu'elle soit adjacente ; ne jamais laisser l'arme principale seule exposée (garder une arme de secours).
- Incubus/succubus : les prompts 'Shall I remove...' consomment les touches ; il retire l'armure et vole l'or. Le tuer à distance ou fuir.
- Tuer un priest co-aligné : 'Thou dost profane my shrine' est juste l'éclair (ghod_hitsu) ; u.ugangr N'augmente PAS. Luck −2 (murderer), protection perdue. Un seul sacrifice frais remet la Luck à 0 si la prayer timeout est 0.
- Sacrifier sans message alors qu'on attend un clover = Luck déjà à 10.
- !!! NE JAMAIS filtrer un farlook par 'elf' ou 'human' : TOUS les @ s'affichent « a human or elf (…) ». Tester le nom exact du monstre ET l'absence de 'peaceful'/'priest'. Tuer la priestess co-alignée = Luck −7, dieu fâché, protection et télépathie perdues.
- Level teleport CONFUS avec teleport control : teleport.c fait 'Oops' si rnl(5)≠0 → 80% d'échec à Luck 0. Seul un scroll of teleportation CURSED (non confus) donne un contrôle sûr. Luck ≥8 → ~80% de succès.
- FAUX (corrigé T26068) : lire confuse monster NE rend PAS confus une Valkyrie (youmonst.data = PM_VALKYRIE, S_HUMAN, même dwarf) : juste 'hands glow red'. Sources de confusion : umber hulk (regard d(3,4) tours), booze/confusion potion, cursed confuse monster, rotten food (1/4), trône.
- Un cadeau du dieu (sacrifice) remet la prayer timeout à rnz(350) : les sacrifices suivants font 'hopeful feeling' (réduisent la timeout) au lieu de monter la Luck.
- Alchimie : fruit juice + potion of speed = booze. Au deli de Minetown, une potion à prix de base 50 = fruit juice ou booze.
- Creuser (pick-axe/mattock) à côté de l'eau : fillholetyp testé 2 fois (fosse puis trou) → (1/(n+1))².
- Medusa creuser : dig.c fillholetyp → trou rempli avec proba n/(n+1) (n = cases d'eau voisines). Toujours vérifier les charges du wand AVANT (le mien était vide : 'Nothing happens' puis '>' = « You can't go down here »). Wrest = 1/121 par essai (40 essais ici).
- Or de vault : object detection révèle les vaults (carré 2×2 de $) ; wand of digging jusque dedans, ramasser, ressortir avant 30 tours.
- Un altar dans une salle sombre peut être un temple avec prêtre INVISIBLE : lire les messages en entrant.
- Medusa-4 : impossible de creuser vers le bas depuis la zone d'arrivée (eau dans chaque 3×3 : le trou se remplit, on tombe dans l'eau, le bag prend l'eau). Toujours vérifier medusa.des (script BFS) AVANT de zapper. Zapper digging vers le bas SUR un escalier : le rayon rebondit.
- Trap doors fréquentes aux Dlvl 19-21 : elles m'ont fait descendre 2 fois sans le vouloir. Au-dessus de Medusa, marcher sur des cases inconnues peut faire tomber sur son niveau (arrivée côté sûr heureusement).
- Rope golem/golems sans esprit : invisibles à la télépathie quand je suis Blind ; 'It hits/choked' = frapper la case 'I'.
- Potions sky blue = gain level (bues ×2), wraith corpse = +1 XL : toujours manger les wraiths frais.
- HARNAIS (2026-09-27) : session.py refuse toute touche (sauf Escape) si HP a baissé de 1/5 du max sous le dernier niveau acquitté ET < 60% max ("HP ALARM ... Key refused"). Alors : arrêter les boucles, lire l écran, décider (prier si HP<1/7, fuir, soigner), puis `slots/7/session ack-hp` (jamais dans une boucle).
- Chameleon : change de forme (master lich → stun, puis monkey qui vole le helm). Le tuer vite ; ne pas manger son corpse.
- Rogue level (Dlvl 15) : symboles Rogue (']' armure, ':' nourriture, '%' escalier, '*' or) ; le fantôme gardait food rations + plate mail (cursed 3/4, extralev.c). Couloirs cachés : chercher aux culs-de-sac.
- Don au priest co-aligné ≥400×XL (sans protection déjà) : +2 à +4 AC d'un coup.
- Polymorph trap Dlvl12 : forme grande = mithril + cape détruites. Sans magic resistance, marcher sur les '^' inconnus est dangereux ; farlook/éviter les traps, chercher la MR en priorité.
- doorfight : la regex prenait le "b" de "blank" pour un monstre (attaque dans le vide pendant que le rust monster rouillait le helm, AC2→5). Corrigé : exiger "X(" après le chiffre.
- 'I' inamovible derrière un boulder = souvent un piercer caché ; les projectiles passent au-dessus des boulders (seule la heavy iron ball s'arrête) ; une pioche/mattock appliquée sur un boulder le brise (même en Sokoban, -1 luck).
- Brown pudding : Excalibur (fer) le divise ; sa morsure pourrit la cape.
- Sokoban : les mimics (giant/small) se déguisent en boulders et les black lights invisibles bloquent les poussées ; spush doit s'arrêter sur 'Perhaps that's why'/'in vain' (fait) et sur un menu 'Things that are here' (un tas d'objets consomme la touche suivante). Un script qui continue après un blocage = chute dans un hole ou boulder poussé de travers.
- Scroll of earth lue à côté d'un hole : le boulder tombe et le bouche (flooreffects).
- Nymph endormie : ne pas l'attaquer au corps-à-corps si elle peut survivre à 1 coup ; elle a volé le +3 small shield (T9480). Préférer la fuir ou la tuer à distance.
- Sokoban = niveau SOUS l'Oracle (dungeon.def : CHAINBRANCH oracle +1 up).
- Level teleport trap (3.6.7) : disparaît après usage (deltrap dans level_tele_trap) ; le dog reste derrière.
- Rothe : 3 attaques, jusqu'à 14/tour ; Elbereth dès la moitié des HP (il le respecte).
- Were (jackal/rat) en forme animale : morsure = lycanthropy (prayer la guérit). En forme @ : le tuer vite.
- `grab '('` ramasse aussi les coffres (chest 600 poids → Burdened) : ne jamais grab '(' sans farlook.
- Rester en dessous : en number_pad le préfixe de compte est `n` (n10s), pas `10s`.
- Travel/`,` : vérifier la position après t/go ; le travel a échoué et `,` a ramassé les bottes maudites (2 fois).
- Test par le familier : « steps reluctantly over » = maudit ; un objet que le chien ramasse/porte = non maudit.
