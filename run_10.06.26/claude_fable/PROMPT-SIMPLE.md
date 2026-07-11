# La demande, sans précisions techniques

Ton but est de créer un agent qui arrive à Minetown 80 % du temps (arriver
dans la ville, le premier tile de la ville compte), avec comme objectif
long terme de terminer NetHack.

Tu joueras sur NetHack 3.6.7, la version officielle, sans mode wizard ni
triche dans les parties comptées. Le personnage sera une Valkyrie.

Tu as le droit de modifier le code source du jeu pour que chaque partie
commence avec certains objets : notamment une blessed greased +2 gray dragon
scale mail. Tu peux aussi obtenir Excalibur dès le niveau 5 (regarde sur le
wiki comment faire, c'est tout simple), et souviens-toi que quand tu es Weak
à cause de la faim, tu peux prier environ tous les 400 tours.

Regarde sur internet où en est la recherche (le NLE et les techniques que
les gens ont essayées) pour t'inspirer, mais travaille uniquement dans ton
répertoire et installe tout ce qu'il faut dedans.

Essaye de jouer toi-même à NetHack pour voir comment obtenir un bon winrate,
essaye plein de choses différentes et sois large dans tes réflexions. Ne sois
pas trop minutieux en exploration : trouve vite les escaliers et les éléments
essentiels, il y a toujours une porte cachée quelque part.

Quand tu auras trouvé une bonne logique pour ton processus d'entraînement,
tu utiliseras Vast AI pour louer des machines et tester en masse, avec un
budget maximum de 2 dollars — utilise l'instance à fond ou de la manière la
plus optimale, garde-la tant que tu itères activement et détruis-la quand il
n'y a plus de batch à lancer.

Pour te connecter à Vast AI : le CLI `vastai` est déjà installé sur la
machine (~/.local/bin/vastai) et la clé API est en place dans
~/.config/vastai/vast_api_key (le CLI la lit automatiquement — teste avec
`vastai show user`). Pour l'accès SSH aux instances louées, attache la clé
publique ~/.ssh/id_ed25519.pub avec `vastai attach ssh <id_instance>`.

Fais aussi un petit système sympa pour que je puisse voir quelques-unes de
tes parties en local, je te dirai ce qui ne va pas.

Tiens-moi au courant du win rate et des causes principales d'échec, et
préviens-moi quand tu arrives à 80 %.
