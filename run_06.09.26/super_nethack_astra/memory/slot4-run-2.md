# Emplacement 4, run 2 — journal (état le plus récent en haut)

STYLE ASTRA (memory/astra-style.md). Lire aussi slot4-run-1.md (mort : giant bat, boucle de combat sans HP).
Outils perso : slots/4/kk (touches répétées, arrêt HP/monstre), slots/4/ff (F+dir avec arrêt HP),
slots/4/xp (explore par tranches, arrêt monstre/HP/faim). NE JAMAIS utiliser `fight`.

## Current state
URGENT: T4342 Dlvl4 HP36(52) AC5 XL5, prayers T1659 et T4124 (prochaine sûre ~T5200+), pas de pet. TELEPATHY.
Porté: a blessed rustproof +1 EXCALIBUR, c blessed +3 small shield, k uncursed +0 ALCHEMY SMOCK (poison+acid res).
Sac: b +0 dagger, g dagger (lancer), q dart, l uncursed +0 elven cloak, t helmet (BUC ?), j golden potion, u black potion, m melon, i lichen corpse,
  gems: p violet, r 2 white. $331. Scrolls identifiés : ELBIB YLOH = remove curse, GARVEN DEH = identify,
  MAPIRO MAHAMA DIROMAT = teleportation (probable), READ ME = light.
FOOD CRITIQUE : seulement melon + lichen. Manger les corpses frais (pas de dwarf : cannibalisme).
D1: '<' 26,16, '>' 74,27.
D2: '<' 24,12, '>' 65,27, fountain 20,13, SINK 73,28, WEAPON SHOP 6-9,15-17 : PLATE MAIL 800 zm, tripe 20.
D3: '<' 61,12, '>' 18,26 (via porte cachée 24,16 puis porte 19,24), iron bars 37,23.
D4: '<' 6,15, '>' 50,15 (main), MINES '>' 75,18 (salle est), teleport trap 43,27, anti-magic 21,20, porte cachée 48,28.
D5: '<' 74,26, '>' 62,28.


## Lessons
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
