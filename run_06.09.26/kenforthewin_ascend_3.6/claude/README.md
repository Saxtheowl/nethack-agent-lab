# kenforthewin_ascend_3.6 / claude

Reproduction locale, « pure », de [kenforthewin/nethack_astra](https://github.com/kenforthewin/nethack_astra) :
un LLM (Claude, via Claude Code) joue lui-même NetHack 3.6.7 vanilla, touche par
touche, jusqu'à l'ascension. Pas de bot, pas d'aide, pas de mode wizard, pas de
save-scum.

- `engine/build.sh` : NetHack 3.6.7 officiel (tty + curses) dans `engine/install`.
- `scripts/` : harnais d'Astra (MIT, voir `upstream/`) adapté au local :
  tmux + ttyrec au lieu de SSH/Hardfought, ledger haché simple.
- `memory/` : journaux de campagne (lire `session.md` d'abord).

Regarder :
- navigateur : `python3 scripts/session.py viewer` puis http://127.0.0.1:8766/
- terminal en direct : `python3 scripts/session.py attach` (lecture seule)
- après coup : `ttyplay runs/<date>.ttyrec`
