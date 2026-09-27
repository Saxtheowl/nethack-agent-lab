# Emplacement 7, run 1 — journal (état le plus récent en haut)

STYLE ASTRA (memory/astra-style.md, obligatoire) : la méthode d'origine qui a gagné, sans BotHack.
Lire aussi les « Lessons » de memory/run-1..run-4, slot2-run-1, slot3-run-1.
Jamais de boucle qui passe des tours sans vérifier les HP (waitpet, rest, explore).

## Current state
URGENT: T10123 Minetown (Mines D7, sur l'altar 37,17) HP90(90) AC2 XL8 Fast, last prayer T9870 (faim) → next OK ~T10900+.
Wield a: blessed rustproof +1 EXCALIBUR (Expert). Worn: T elven mithril-coat (-1, décursé holy water), V +1 faded pall (elven cloak), p +0 orcish helm, t +0 snow boots. TELEPATHY.
Food: 1 uncursed food ration (Y). $26. Scrolls: g blessed ZELGO MER (= create monster), N blessed blank.
IDs : VE FORBRYDERNE=magic mapping, ASHPD SODALG=amnesia (lu T10089, carte oubliée), PRATYAVAYAH=charging, ZELGO MER=create monster, LOREM IPSUM=enchant armor, YUM YUM=confuse monster, VELOX NEB (maudit, laissé)=?
Potions : white=speed, pink=acid, puce=oil, murky=levitation, ruby=sleeping, swirly=healing, sky blue=gain level, clear bénie=holy water, dark/effervescent maudits laissés sur l'altar.
Wands: q slow monster, d light, I oak (rechargée, inconnue), O spiked, W glass (inconnues, pas de msg à l'engrave). Rings non essayés : o bronze, f ruby (uncursed).
Daggers : b +0, R 2 elven (uncursed). Shield volé par la mountain nymph de D10.
Tout BUC-testé uncursed (altar neutre Minetown 37,17) : i 2 orcish daggers, b dagger ; scrolls f VE FORBRYDERNE, j PRATYAVAYAH, z ASHPD SODALG ;
potions h white, r pink, w puce, x murky, J ruby ; ring o bronze ; wands q iridium (=slow monster), I oak (no engrave msg).
Laissés sur l'altar : cursed dark potion, cursed jade ring. Gems C orange, D red, E 3 violet, F 2 white (non testées).
Minetown (D7 Mines, 'Grotto-like', dwarf qui creuse) : temple Odin (neutre) 37,17 ; Morven clothing 44-47,19 (elven cloak 'faded pall' 107zm, wands maple 200, silver 267, forked 356) ;
Tjiwidej deli 51-55,22-23 (food ration 60zm, dark potion 67). Mines '<' 70,15, '>' 14,14.
Large dog laissé sur main Dlvl 7 (depuis T5071).
D1 fountain asséchée. D2 sink 52,19. D3 sink 68,14. D4 '<' 66,14, Mines '>' 38,23, main '>' 57,26 (fountain D4 disparue).
D5: '<' 29,22, '>' 16,27, fountains 17,26 62,13 75,18. D6: '<' 31,25, '>' 75,24, fountain 30,26. D7: '<' 56,14, level teleport trap vers 38,25.

## Lessons
- Nymph endormie : ne pas l'attaquer au corps-à-corps si elle peut survivre à 1 coup ; elle a volé le +3 small shield (T9480). Préférer la fuir ou la tuer à distance.
- Sokoban = niveau SOUS l'Oracle (dungeon.def : CHAINBRANCH oracle +1 up).
- Level teleport trap (3.6.7) : disparaît après usage (deltrap dans level_tele_trap) ; le dog reste derrière.
- Rothe : 3 attaques, jusqu'à 14/tour ; Elbereth dès la moitié des HP (il le respecte).
- Were (jackal/rat) en forme animale : morsure = lycanthropy (prayer la guérit). En forme @ : le tuer vite.
- `grab '('` ramasse aussi les coffres (chest 600 poids → Burdened) : ne jamais grab '(' sans farlook.
- Rester en dessous : en number_pad le préfixe de compte est `n` (n10s), pas `10s`.
- Travel/`,` : vérifier la position après t/go ; le travel a échoué et `,` a ramassé les bottes maudites (2 fois).
- Test par le familier : « steps reluctantly over » = maudit ; un objet que le chien ramasse/porte = non maudit.
