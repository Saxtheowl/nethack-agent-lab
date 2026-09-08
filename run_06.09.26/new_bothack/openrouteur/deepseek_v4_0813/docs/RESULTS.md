# Résultats des tests et essais

## Environnement de référence

- **NetHack 3.4.3-NAO** compilé localement (`upstream/nh343/nethack.343-nao`,
  ~6,8 Mo), source <https://github.com/altorg/NetHack> au commit `b60bd44c`
  (déc. 2014). Script : `tools/build_nethack343_nao.sh`.
- **BotHack original** compilé avec JDK8 + lein (Java 17 provoque une erreur de
  compilation de la dépendance `multiset` ; Java 8 est requis, comme documenté
  par l'auteur).
- Le `bothack.nethackrc` de l'original est utilisé tel quel.

## Tests différentiels contre l'original (oracle Clojure)

`JDK8_HOME=$PWD/.local/jdk8 BOTHACK_ORACLE=1 python3 -m pytest -q`

```
8 passed in ~12s
```

Le test différentiel couvre **857 cas** : 8 positions × distances/manhattan/
towards/adjacent/in-direction/neighbors, `effective-str`, 26 étiquettes d'objets
× (parse-label, item-type, item-subtype, item-weight, appearance-of, corpse,
container), 10 types de monstres, et 25 glyphes × 6 couleurs × (monster?, item?,
monster-glyph?). **Tous identiques à l'original.**

Preuve machine : `artifacts/pytest.xml` (JUnit).

## Essai réel de la cible (sans mode wizard)

`python3 tools/pty_smoke.py` lance la vraie partie via un pty et pilote les menus
de début puis quelques déplacements. Sortie capturée dans `artifacts/smoke-run.txt`
(extrait) :

```
smoketest1788723121, welcome to NetHack!  You are a lawful dwarven Valkyrie.
... AC:6  Exp:1 T:5 ... It's a wall. ... What do you want to eat? [d or ?*]
```

Cela démontre que la cible historique se lance, que le `nethackrc` de BotHack
fonctionne avec ce build (rôle/race forcés, lignes d'état aux lignes 23–24,
touches de déplacement), et que l'I/O terminal (frame ANSI) est exploitable.
**Ce n'est pas une ascension** et ne valide pas le portage du moteur.

## Ce qui n'est PAS démontré ici

- Aucune partie complète jouée par le portage Python (le moteur n'est pas porté).
- Aucune ascension, ni de l'original, ni du portage.
- Aucune mesure de taux de victoire (le `xlogfile` n'est pas encore exploité par
  le portage).
