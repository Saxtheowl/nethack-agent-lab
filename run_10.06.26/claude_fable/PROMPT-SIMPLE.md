# La demande, sans précisions techniques

Ton but est de créer un agent qui arrive à Minetown 80 % du temps (arriver
dans la ville, le premier tile de la ville compte), avec comme objectif
long terme de terminer NetHack.

Tu joueras sur NetHack 3.6.7, la version officielle, sans mode wizard ni
triche dans les parties comptées. Le personnage sera une Valkyrie.

## Les règles

Une seule modification favorable du jeu est autorisée : chaque partie
commence avec une **blessed greased +2 gray dragon scale mail**. Tout le
reste est le départ Valkyrie standard — pas de dagues bonus, pas de wands,
pas de rations en plus. Le butin trouvé en jeu est bien sûr utilisable.
Tu peux exploiter les mécaniques normales du jeu : Excalibur par trempage
dès le niveau 5 (regarde le wiki, c'est tout simple), la prière quand tu es
Weak (environ tous les 400 tours), etc.

## L'approche

Un autre agent a déjà travaillé sur ce problème avec une approche
« terminal » (pty + scraping d'écran) : son travail est dans le répertoire
frère `claude_fable`. Toi, tu dois **tenter une technique différente, en
parallèle**. Inspire-toi surtout de ce qui a été fait dans le run **gpt_5.6**
qui se trouve dans son propre répertoire juste à côté de celui-ci (remonte
d'un cran : `../gpt_5.6`, sois sûr de bien le trouver). Cet agent-là est
passé par le **NLE** (NetHack Learning Environment, maintenu, basé sur
3.6.7) avec un agent symbolique par-dessus, et il a obtenu de très bons
résultats — regarde son README, son code (`minetown_agent/`), ses scripts
d'installation et ses patches, et repars de ces techniques.

Regarde aussi sur internet où en est la recherche (le NLE et les techniques
que les gens ont essayées — autoascend, BotHack…) pour t'inspirer, mais
travaille uniquement dans ton répertoire et installe tout ce qu'il faut
dedans.

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
tes parties en local, en CLI dans le terminal (regarde le `mt-watch` de
gpt_5.6 : tableau des parties puis replay interactif du ttyrec).

Tiens-moi au courant du win rate et des causes principales d'échec, et
préviens-moi quand tu arrives à 80 % confirmé sur 100 parties.
