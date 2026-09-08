# BotHack Python

Portage **en cours**, ciblant **NetHack 3.4.3-NAO**. Le moteur Python reste incomplet et **n’a pas réalisé d’ascension**. L’original Clojure sert uniquement de référence aux tests et aux parties de comparaison.

```sh
cd codex # depuis la racine commune aux agents
uv sync --extra dev
uv run python -m bothack status
uv run python -m bothack item 'a blessed +1 long sword (weapon in hand)'
uv run python -m pytest
```

Pour préparer le jeu et les tests comparatifs :

```sh
uv run python tools/bootstrap.py --oracle --game --local-build-tools
BOTHACK_ORACLE=1 uv run python -m pytest
uv run python tools/run_original.py --timeout 180
```

Linux, Python 3.12+, `uv`, Git, GCC, Make, en-têtes ncurses. Les outils locaux flex/bison utilisent les paquets Debian/Ubuntu sans droits administrateur. Le premier téléchargement nécessite Internet.

[Documentation détaillée](docs/PORTAGE.md) · [Consigne commune aux agents](PROMPT.md) · [Licence GPLv2](LICENSE)
