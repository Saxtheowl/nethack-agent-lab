# Emplacement 4, run 2 — journal (état le plus récent en haut)

STYLE ASTRA (memory/astra-style.md). Lire aussi slot4-run-1.md (mort : giant bat, boucle de combat sans HP).
Outils perso : slots/4/kk (touches répétées, arrêt HP/monstre), slots/4/ff (F+dir avec arrêt HP),
slots/4/xp (explore par tranches, arrêt monstre/HP/faim). NE JAMAIS utiliser `fight`.

## Current state
URGENT: T8129 Dlvl7 HP65(65) AC2 XL8 Fast, AMULET OF LIFE SAVING (C), prayers ..., T6229, T7410 (prochaine ~T8500+). TELEPATHY. $331. Food: M 3 food rations.
Porté: a blessed rustproof +1 EXCALIBUR, c blessed +3 small shield, k uncursed +0 ALCHEMY SMOCK (brûlé/pourri, poison+acid res), t helmet + P ring mail (BUC inconnu, mis T8129 ; N = scroll of remove curse en secours).
Sac: b +0 dagger, g dagger (lancer), q dart, l uncursed +0 elven cloak, t helmet (BUC ?), j golden potion, u black potion, K cyan potion, M 2 food rations, L 8 darts, F elven dagger, m melon, i lichen corpse,
  gems: p violet, r 2 white. $331. Scrolls identifiés : ELBIB YLOH = remove curse, GARVEN DEH = identify,
  MAPIRO MAHAMA DIROMAT = teleportation (probable), READ ME = light, EIRIS SAZUN IDISI = genocide (lu T6973 : water nymph).
FOOD CRITIQUE : seulement melon + lichen. Manger les corpses frais (pas de dwarf : cannibalisme).
D1: '<' 26,16, '>' 74,27.
D2: '<' 24,12, '>' 65,27, fountain 20,13, SINK 73,28, WEAPON SHOP 6-9,15-17 : PLATE MAIL 800 zm, tripe 20.
D3: '<' 61,12, '>' 18,26 (via porte cachée 24,16 puis porte 19,24), iron bars 37,23.
D4: '<' 6,15, '>' 50,15 (main), MINES '>' 75,18 (salle est), teleport trap 43,27, anti-magic 21,20, porte cachée 48,28.
D5: '<' 74,26, '>' 62,28, brown pudding (ne pas frapper au fer) vers 20,14. Sokoban '<' PAS TROUVÉ après ~15 recherches (murs E/N/S cherchés) — abandonné pour l'instant. Vault quelque part.
D6 = ORACLE (Delphi) : '<' 14,13, '>' 68,15.
D7: '<' 18,18, '>' 28,19, SOKOBAN '<' 61,20 (l'entrée Sokoban est au niveau SOUS l'Oracle, pas au-dessus !).
Mines: D5 '>' 24,27 ; D6 '>' 10,16, FIRE TRAP 30,18 ; D7 = MINETOWN : '<' 13,14, '>' 68,14, delicatessen (Patjitan) 51-53,25-26, general store (Tuktoyaktuk) 40-41,24-26 porte 40,23 (orcish cloak 67), 2e deli Baliga 45-46,19-21, HARDWARE Nosnehpets 28-29,24-26 (PICK-AXE 67 zm, lamp 89, camera 267), temple pas trouvé (foule de peacefuls). sink 48,25, fountain 37,27.


## Lessons
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
