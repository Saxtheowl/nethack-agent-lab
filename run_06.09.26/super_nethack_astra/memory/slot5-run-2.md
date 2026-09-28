# Emplacement 5, run 2 — journal (état le plus récent en haut)

## DEATH T7968, Dlvl 5 (donjon principal), XL7, 3417 pts : « killed by a gold golem »
Chaîne : une mountain nymph (T7440) vole la long sword + l'elven mithril-coat (AC -2 → 3) ; je me bats aux daggers.
En récupérant mes daggers lancées, j'enchaîne des helpers de déplacement (grab → scripts/t, puis mon slots/5/goto)
qui relancent le travel en boucle : un GOLD GOLEM (glyphe « ' ») me frappe pendant ~20 tours sans qu'aucun helper
ne s'arrête (goto ne reconnaissait pas « ' » comme monstre et faisait « s » ; t réessaie 3 fois sans regarder les HP).
Leçons :
- AUCUN helper de déplacement sans arrêt sur perte de HP : grab/t n'en ont pas → ne plus les utiliser en boucle ;
  goto doit s'arrêter dès que les HP baissent et reconnaître tous les glyphes de monstres (y compris ' & ; : et chiffres).
- Après chaque appel de helper, relire la ligne HP ; ne jamais enchaîner plusieurs helpers dans une même commande.
- Les nymphs volent même l'armure portée : les tuer AVANT (daggers) ; une porte piégée qui explose m'a immobilisée
  pendant le vol. Ne pas « search » longtemps dans une zone inexplorée sans Elbereth.
- La prayer comme nourriture + ring de poison res = faim rapide ; garder 2+ rations.

STYLE ASTRA (memory/astra-style.md). Lire les « Lessons » de slot5-run-1.md (mort T9719, fire ant) et des autres runs.
Règles clés tirées du run 1 :
- Toujours 2+ rations ; acheter la nourriture quand on n'a PAS faim (prix ×2..×4 sinon).
- Tuer nymphs/monkeys à distance ; ils volent l'armure portée.
- Sous 50 % HP face à un monstre rapide : fuir (escalier, Elbereth vérifié), ne pas rester au contact.
- Helpers perso : slots/5/gf (combat gardé), elb, rest2, goto (HP-safe, ne combat jamais), grab2 (HP-safe), doorfight, map. NE PAS utiliser slots/5/grab ni t en boucle.
  stop faim/HP), chase, map, ex, dip1, wait.

## Current state
ALERTE T7440 : une mountain nymph (porte piégée qui explose) a volé la LONG SWORD et l'ELVEN MITHRIL-COAT ! AC 3, je manie des daggers (v). La retrouver sur Dlvl 5 et la tuer aux daggers. Ruche de killer bees au SW près du '>' (16,24).
URGENT: T6720 Dlvl4 (altar) HP55(56) AC-2 XL6, LAST PRAYER T6896 (faim) → prochaine ~T7900. Pas de pet. $52.
Porté: a uncursed THOROUGHLY RUSTY +1 long sword (Skilled), c +3 small shield, p elven mithril, x iron shoes, I orcish helm,
E ring of POISON RESISTANCE (main gauche).
Sac: v 6 daggers (lancer : t v dir), (b dagger, o blessed elven dagger lancés et laissés dans la throne room D5 ?),
FOOD: B food ration. Scrolls: l IDENTIFY x1, r REMOVE CURSE, i 2 KO BATE, C TEMOV (unc), D ABRA KA DABRA (BLESSED), F ETAOIN SHRDLU (BLESSED).
G cursed dark potion. t ring of warning (unc). m key. gems.
MINETOWN = Mines D7 : temple altar 47,21, deli 50-52,20-22, general store 29-31,24-26 (porte 27,24), '<' 72,14 '>' 4,23.
ALTAR CO-ALIGNÉ (Tyr) Dlvl 4 en 73,13. D4 '<' 11,17 '>' 38,15 (main) '>' 73,23 (mines).
D5 main : '<' 67,15, throne room 70-76,21-26 nettoyée (throne 74,25, dwarvish cloak), '>' pas encore trouvé.
Objectif : Oracle (fountains) pour Excalibur ; bénir l'épée avant (holy water) si possible.

## Lessons
- T5329 : fountain D1 tarie au 4e #dip, épée thoroughly rusty (comme au run 1). Les objets BLESSED résistent souvent à la rouille (erode_obj : blessed && !rnl(4)) → bénir l'épée (holy water) AVANT de tremper, et préférer les 4 fountains de l'Oracle.
- T3743 : pony (kick+bite) m'a mise de 24 à 2 HP à XL3 ; garde de combat trop basse (14). À bas niveau : garde ≥ 60 % et Elbereth dès 50 %.
- Menus de pickup : envoyer les lettres une par une avec session.py keys --raw (le wrapper k envoie parfois 'ab' dans un « Search for: »).
- (run 2) D1 : salles fermées, portes cachées (76,19 ; 63,28) ; fountain 43,25 ; '>' 50,14. Prayer T844 (faim).
