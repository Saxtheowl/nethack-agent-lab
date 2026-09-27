# Emplacement 6, run 1 — journal (état le plus récent en haut)

STYLE TARIRU (memory/tariru-style.md, obligatoire)
Lire aussi les « Lessons » de memory/run-1..run-4, slot2-run-1, slot3-run-1.
Jamais de boucle qui passe des tours sans vérifier les HP (waitpet, rest, explore).

## Current state
URGENT: T3832 Mines Dlvl11 (tombée par trap door depuis Minetown D8) XL5 HP50/54 AC3 $690, SANS familier
(dog laissé Mines D6 ; magic whistle G pour le rappeler quand même niveau). Prayer faite T2826 (prochaine >= ~T3900-4000, idéalement T4000+).
FAIM: ~150 nutrition, reste 1 tripe. Minetown D8: general store (Budereyri) avec fortune cookie 21zm, 2 slime molds 102zm,
zinc wand 300zm (base 150/200) ; lighting shop 37-38,17-19 ; temple de Loki (chaotique) pas encore trouvé ; '>' 71,19.
Portés: studded leather t, +3 small shield. Non testés: B dwarvish cloak, E iron shoes, D dagger (quiver) -> altar Minetown.
Scrolls: u identify, v ASHPD SODALG (base 100), I VE FORBRYDERNE (base 50 ? = light?). Potions: q puce (base 50), r/H fizzy (base 100?), A brilliant blue.
Spellbook purple vendu 263 (niveau 7). D4 Mines '>' 20,24 ; D5 = Oracle ; Sokoban '<' à trouver sur D4.

## Lessons
- Mines: trap doors fréquentes (3 chutes !). explore/travel marchent dessus : pas de parade sauf chercher (s) ; garder le whistle pour le chien.
- Pour tester le curse par le chien, il doit marcher DESSUS : peut prendre des dizaines de tours ; sinon altar.
- Red mold: son feu passif touche même quand on RATE (−8 HP). Ne l'attaquer que HP pleins ; tuer à distance si possible.
- explore.py rate souvent les portes ("no reachable frontier") : ouvrir/traverser la porte à la main.
- scripts/session.py sans NH_SLOT affiche le slot 1 : toujours slots/6/session.
