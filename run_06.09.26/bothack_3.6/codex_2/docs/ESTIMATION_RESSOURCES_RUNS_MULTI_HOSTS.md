# BotHack 3.6.7 : ressources, parallélisme et exécution sur plusieurs hôtes

Évaluation effectuée le **18 septembre 2026** à partir du code et des résultats de `bothack_3.6/claude`, d'une inspection en lecture seule du worker `miniforum-worker` (`192.168.1.19`) et de la machine locale `SandboxVibing`.

## Verdict

Donner davantage de CPU à BotHack est utile, mais **multiplier immédiatement toutes les campagnes par six ne multipliera pas par six la vitesse d'obtention d'une ascension**.

Le bot est actuellement limité presque entièrement par un cœur Python par partie. Une machine dotée de 12 à 16 cœurs rapides et réellement disponibles pourrait faire tourner environ 12 parties simultanées et approcher un débit six fois supérieur aux deux parties actuelles. Le miniforum actuel ne possède pas cette capacité dédiée : il expose 8 vCPU, subit encore environ 19 à 24 % de temps CPU volé lors du relevé, et son processeur physique est un Ryzen 5 7545U à 6 cœurs et 12 threads selon AMD. Douze parties sur ce worker seraient fortement en concurrence.

Le meilleur usage immédiat des ressources est :

1. conserver **2 parties longues** sur le miniforum pendant le diagnostic des blocages actuels ;
2. utiliser la machine locale comme **worker secondaire de 1 à 2 jobs**, après avoir copié une release identique et fixé l'environnement ;
3. réserver les campagnes à 12 jobs à une machine dédiée de 12 à 16 cœurs rapides, surtout pour les campagnes de validation après correction des boucles de quête, d'objets et d'invocation ;
4. séparer les campagnes de découverte, de comparaison et d'évaluation afin de ne pas produire six fois la même erreur.

## 1. Profil réel d'une partie

Le worker actif exécutait deux runners. Chacun utilisait environ **98 à 99 % d'un vCPU** côté Python. Le processus NetHack associé consommait seulement **0,7 à 1,1 %** de CPU. Une partie occupait environ **57 à 152 Mio** de mémoire Python, auxquels s'ajoutaient environ 5 Mio pour NetHack.

Le goulet d'étranglement n'est donc ni le moteur C, ni la mémoire, ni le GPU. Il s'agit surtout des décisions Python : mise à jour du monde, exploration, recherches de chemin, inventaire et handlers.

Conséquences :

- une partie est essentiellement mono-cœur ;
- ajouter des cœurs permet de lancer d'autres parties indépendantes ;
- un processeur avec de meilleures performances par cœur accélère aussi chaque partie ;
- beaucoup de RAM n'apporte presque rien au-delà d'un seuil confortable ;
- un GPU n'est pas requis pour le bot symbolique actuel.

## 2. Machines observées

| Élément | Miniforum | Machine locale |
| --- | --- | --- |
| Nom observé | `miniforum-worker` | `SandboxVibing` |
| CPU annoncé à la VM | 8 vCPU, Ryzen 5 7545U | 4 vCPU, Ryzen 5 3500U |
| CPU physique de référence | 6 cœurs / 12 threads, Zen 4 + Zen 4c | Ancien processeur mobile, VM à 4 vCPU |
| Mémoire | 19 Gio, environ 18 Gio disponibles | 11 Gio, environ 9,8 Gio disponibles |
| Disque disponible | environ 121 Gio | environ 87 Gio |
| Python | 3.12.3 | 3.12.3 |
| GCC / glibc | GCC 13.3 / glibc 2.39 | GCC 13.3 / glibc 2.39 |
| Virtualisation | KVM | KVM |
| Charge utile proposée | 2 à 6 jobs selon mesure | 1 à 2 jobs |

Le miniforum n'était pas à court de mémoire. Sa charge moyenne était proche de 1,1 avec deux runners, mais `vmstat` mesurait environ 19 à 24 % de *steal time*. Cela signifie que l'hyperviseur ne donnait pas au système invité tout le CPU qu'il pensait avoir. Le chiffre historique d'environ 70 % n'était plus observé à cet instant, mais le worker n'était toujours pas équivalent à une machine dédiée.

La fiche AMD du Ryzen 5 7545U indique 6 cœurs, 12 threads et un TDP mobile configurable de 15 à 30 W. Les 8 « sockets » mono-thread affichés par la VM sont une topologie virtuelle, pas huit cœurs physiques dédiés. [Spécifications AMD Ryzen 5 7545U](https://www.amd.com/en/products/processors/laptop/ryzen/7000-series/amd-ryzen-5-7545u.html).

## 3. Débit actuel

Les quatre cycles disponibles sur le worker montrent une nette baisse de vitesse lorsque les parties deviennent profondes et que le code évolue :

| Cycle | Jobs | Parties terminées | Médiane tours/s | Intervalle observé |
| --- | ---: | ---: | ---: | ---: |
| `cyc-01` | 3 | 9 | 6,08 | 4,84–8,77 |
| `cyc-02` | 3 | 9 | 5,53 | 4,67–9,04 |
| `cyc-03` | 2 | 6 | 5,12 | 4,24–8,58 |
| `cyc-04`, relevé partiel | 2 | 4 | 4,89 | 2,81–8,24 |

Dans `cyc-04`, les deux parties ayant atteint la limite de quatre heures ont tourné en moyenne à 2,81 et 3,65 tours/s. Les parties terminées plus tôt sur blocage ont atteint 8,24 et 6,13 tours/s. La vitesse n'est donc pas constante pendant une partie : les états profonds et complexes coûtent davantage.

Les anciennes séries à 7 ou 8 jobs affichaient souvent 20 à 39 tours/s par résultat, mais elles utilisaient d'autres hashes de bot et de moteur, des objectifs parfois plus courts et des états moins complexes. Elles prouvent que le harnais peut lancer beaucoup de jobs ; elles ne prouvent pas que le code actuel retrouverait cette vitesse avec 8 jobs.

## 4. Que donnerait six fois plus de parties ?

Le parallélisme actuel est de deux. Six fois plus signifie douze parties simultanées.

### Sur une machine réellement capable de 12 jobs

Si chaque partie garde son débit et va jusqu'à la limite de quatre heures :

| Jobs | Parties maximales par jour, modèle idéal à 4 h | Facteur nominal |
| ---: | ---: | ---: |
| 2 | 12 | ×1 |
| 4 | 24 | ×2 |
| 6 | 36 | ×3 |
| 8 | 48 | ×4 |
| 12 | 72 | ×6 |

Certaines parties s'arrêtent avant quatre heures, donc le débit réel en nombre de résultats peut être supérieur. Inversement, contention, collecte des traces et longue traîne le réduisent.

### Sur le miniforum actuel

Avec 8 vCPU exposés et 19 à 24 % de temps volé, l'ordre de grandeur de CPU réellement disponible était proche de 6 à 6,5 vCPU. Deux parties en consomment déjà environ deux. Le plafond raisonnable sans mesure supplémentaire est donc :

- **4 jobs** : très probablement utile, débit total proche de ×1,8 à ×2 par rapport à 2 jobs ;
- **6 jobs** : possible pour une campagne de débit, gain plausible proche de ×2,5 à ×3, avec parties plus lentes ;
- **8 jobs** : machine saturée, à réserver à un benchmark contrôlé ;
- **12 jobs** : surabonnement important, aucun facteur ×6 attendu, davantage de limites en temps réel.

Ces valeurs sont des estimations fondées sur l'occupation mono-cœur et le temps volé, pas des benchmarks de concurrence du build actuel. Il faut mesurer 1, 2, 4 et 6 jobs sur un replay ou un scénario identique avant de modifier la cadence régulière.

### Sur une meilleure machine

Pour 12 parties simultanées stables, viser :

- 12 à 16 cœurs physiques récents avec forte performance mono-cœur ;
- 32 Gio de RAM, largement suffisants pour les runners actuels et les caches ;
- stockage NVMe ;
- Linux x86-64 avec environnement figé ;
- machine dédiée ou VM à vCPU garantis, avec *steal time* presque nul ;
- aucune dépense GPU spécifique.

Un processeur de bureau à 16 cœurs fournit une catégorie adaptée. À titre d'exemple matériel, le Ryzen 9 9950X dispose de 16 cœurs et 32 threads ; cette mention illustre la classe de machine et ne remplace pas un benchmark BotHack ni une comparaison de prix. [Spécifications officielles AMD](https://www.amd.com/en/products/processors/desktops/ryzen/9000-series/amd-ryzen-9-9950x.html).

## 5. Utiliser la machine locale

La machine locale a 4 vCPU, 11 Gio de RAM et un processeur hôte plus ancien. Elle peut raisonnablement ajouter **un ou deux jobs**.

Avec deux jobs locaux plus deux jobs miniforum, la concurrence nominale passe de 2 à 4. La machine locale sera probablement plus lente par partie. L'amélioration globale attendue est plutôt de l'ordre de **×1,4 à ×1,8** que ×2, tant qu'aucun benchmark identique ne fournit un chiffre plus précis.

Son meilleur rôle immédiat :

- scénarios courts et tests de compétences ;
- replays ciblés avec traces lourdes ;
- petite série de seeds fraîches indépendante ;
- comparaison d'une release entre deux hôtes ;
- ne pas concurrencer les tâches interactives importantes de cette machine.

Il ne faut pas lancer les campagnes depuis le binaire local actuel en les mélangeant aux résultats du worker : les hashes sont différents. Au relevé, le binaire local avait l'empreinte `3252c12c…`, tandis que celui du worker actif avait `2777f009…`. Le patch moteur et `mainbot.py` différaient également.

## 6. Les parties seront-elles différentes sur un autre hôte ?

### Réponse courte

Le changement de CPU ne devrait pas, à lui seul, modifier une logique essentiellement entière et synchrone. En revanche, l'état actuel du logiciel ne garantit pas des trajectoires identiques entre hôtes, ni même entre deux processus du même hôte.

### Causes confirmées

1. **Builds différents.** Les binaires local et distant n'ont pas le même hash.
2. **Hash Python non fixé.** `PYTHONHASHSEED` était absent de l'environnement du runner distant. Python choisit alors une graine aléatoire pour le hash de `str` et `bytes`. Le port impose explicitement l'ordre Clojure dans plusieurs endroits, mais il reste de nombreux usages d'ensembles et dictionnaires à auditer. La documentation Python confirme qu'une valeur entière fixe rend ces hashes répétables. [Documentation `PYTHONHASHSEED`](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONHASHSEED).
3. **Heure réelle NetHack.** Le moteur consulte la phase lunaire, le vendredi 13, la nuit et minuit. Ces valeurs influencent la chance et certains monstres. `ubirthday` dépend également de l'heure et intervient notamment dans le choix de certains noms de commerçants.
4. **Locales différentes.** Le worker utilisait `LANG=en_US.UTF-8` et la machine locale `LANG=C.UTF-8`. La plupart des décisions ne devraient pas en dépendre, mais une évaluation reproductible doit fixer la locale au lieu de le supposer.
5. **Limites au temps réel.** Une machine plus lente peut atteindre `max_seconds` avant le même tour. Le résultat devient alors différent même si toutes les décisions précédentes étaient identiques.
6. **Version Python et environnement.** Ils étaient proches lors du relevé, mais doivent rester dans le manifeste et l'image d'exécution.

### Ce qui est déjà favorable

- `NH_SEED` fixe le générateur du moteur et empêche les reseeds ordinaires du patch ;
- `bot_seed` initialise le générateur Python utilisé par la stratégie ;
- les deux machines sont x86-64, sous Ubuntu/KVM, Python 3.12.3, GCC 13.3 et glibc 2.39 ;
- les fichiers bones sont désactivés ;
- chaque partie possède son propre répertoire.

Ces éléments réduisent les divergences sans constituer une garantie complète.

## 7. Conditions pour mélanger proprement plusieurs hôtes

Avant de compter les résultats dans une même campagne :

1. construire une **release immuable** une seule fois ;
2. distribuer exactement le même binaire, les mêmes données NetHack et le même code Python ;
3. vérifier les hashes sur chaque hôte avant le lancement ;
4. fixer `PYTHONHASHSEED` à une valeur inscrite dans le manifeste ;
5. fixer `TZ=UTC` et `LC_ALL=C.UTF-8` ;
6. ajouter idéalement une option moteur de temps de jeu fixe, par exemple `NH_FIXED_TIME`, couvrant lune, jour, nuit et anniversaire ;
7. conserver `engine_seed` et `bot_seed` séparément ;
8. utiliser les mêmes options, aides, kit et limites en tours ;
9. ne pas utiliser la limite murale comme critère de comparaison fonctionnelle entre machines de vitesses différentes ;
10. enregistrer `host_id`, CPU, OS, image/release et limites dans chaque manifeste.

Sans temps moteur figé, deux exécutions peuvent rester des parties valides de la même politique, mais ne doivent pas être qualifiées de replay exact.

## 8. Test multi-hôte recommandé

Ce test doit précéder l'ajout permanent de la machine locale :

1. sélectionner 4 à 6 seeds représentatives ;
2. installer la même release sur les deux hôtes ;
3. fixer hash Python, locale et fuseau ;
4. exécuter des parcours courts, limités en tours plutôt qu'en secondes ;
5. comparer les actions et un hash périodique de l'observation publique ;
6. localiser la première divergence ;
7. mesurer tours/s et CPU avec 1 puis 2 jobs ;
8. n'agréger les campagnes que si les différences restantes sont comprises et déclarées.

Si les trajectoires divergent uniquement à cause de l'heure, implémenter le temps fixe. Si elles divergent dès les premières décisions, auditer en priorité l'ordre des collections et les différences de release.

## 9. Effet sur la progression vers l'ascension

Les cycles `cyc-01` à `cyc-04` disponibles au relevé totalisaient 28 résultats : **16 limites et 12 blocages**, sans ascension. Plusieurs parties atteignent des zones profondes ou le Livre, mais les causes reviennent : quête et Cloche, objets rituels, recherche sans issue, foule et absence de progression.

Cela conduit à trois effets distincts des ressources supplémentaires.

### Effet positif

- découvrir plus vite la fréquence des échecs ;
- tester plusieurs correctifs sur les mêmes seeds ;
- explorer davantage de seeds nouvelles ;
- obtenir plus vite un intervalle de confiance après une première victoire ;
- réduire l'effet des longues parties sur le calendrier.

### Effet faible ou négatif

- douze parties peuvent reproduire simultanément le même bug déterministe ;
- les analyses et corrections restent largement séquentielles ;
- davantage de traces peuvent dépasser la capacité humaine à les examiner ;
- une machine surchargée transforme des parties prometteuses en limites murales ;
- des builds différents rendent la comparaison confuse.

### Estimation de l'accélération scientifique

| Stade du projet | Gain de 6× plus de parties | Gain probable vers l'ascension |
| --- | --- | --- |
| Bug dominant connu et reproductible | Faible | ×1 à ×1,5 |
| Plusieurs causes rares à cartographier | Fort | ×3 à ×5 |
| Correctif à comparer sur seeds appariées | Moyen à fort | ×2 à ×4 |
| Politique stable, mesure du taux de victoire | Très fort | proche du débit matériel |
| Première ascension encore bloquée par le rituel | Limité | corriger le rituel vaut davantage que 6× les runs |

Ces facteurs sont des ordres de grandeur de productivité, pas une loi statistique. Avec une probabilité de victoire réellement nulle à cause d'un bug systématique, `6 × 0` reste zéro.

## 10. Organisation conseillée

### Maintenant

- Miniforum : 2 longues parties de développement.
- Machine locale : 1 ou 2 scénarios/replays ciblés, sur release identique.
- Seeds : majorité de cas connus pour vérifier les correctifs, minorité de seeds fraîches.
- Traces complètes : uniquement sur les replays ciblés pour maîtriser le disque.

### Après fiabilisation de l'invocation

- Miniforum : 4 jobs mesurés, puis éventuellement 6 si le débit total monte sans trop augmenter les limites.
- Machine locale : 1 ou 2 jobs indépendants.
- Comparaison : mêmes seeds, mêmes tours maximum, résultats regroupés par build et hôte.

### Pour une campagne d'évaluation

- machine dédiée de 12 à 16 cœurs ;
- 10 à 12 jobs au départ, les cœurs restants gardés pour le système et les longues pointes ;
- build figé, aucun correctif en cours de campagne ;
- seeds tenues à l'écart ;
- aucune interruption précoce destinée au développement ;
- publication de toutes les tentatives, y compris limites et erreurs d'infrastructure.

## 11. Décision finale

Il est judicieux de donner plus de ressources à BotHack, mais en deux étapes.

**Étape immédiate :** ajouter la machine locale comme worker secondaire limité à 1–2 jobs et tester la reproductibilité. Cela augmente le débit sans achat et révèle les différences d'environnement.

**Étape suivante :** utiliser une machine dédiée de 12–16 cœurs pour les grandes campagnes, lorsque le bot sait franchir de façon répétable les préconditions de l'invocation et que les blocages dominants possèdent des tests.

Augmenter seulement `--jobs` à 12 sur le miniforum actuel n'est pas recommandé. La mémoire le permet, mais le CPU réel et le temps volé ne permettent pas d'espérer un facteur six. Une meilleure machine apportera à la fois plus de parties parallèles et une meilleure vitesse par partie ; c'est cette combinaison qui peut réduire fortement le délai de validation après les prochains correctifs.

