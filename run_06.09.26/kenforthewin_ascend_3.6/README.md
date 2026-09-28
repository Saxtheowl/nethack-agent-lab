# kenforthewin_ascend_3.6

Reproduction « pure » de [kenforthewin/nethack_astra](https://github.com/kenforthewin/nethack_astra)
(une IA qui joue à NetHack 3.6.7 touche par touche, jusqu'à l'ascension), avec plusieurs IA côte à côte :

- `claude/` — les parties jouées par Claude (orchestrateur + agents), le harnais, le recorder, le site
  (http://127.0.0.1:8766/) et la documentation (`claude/doc/guide.html`, servi sur /guide).
- `codex/` — l'espace de travail de Codex. Codex joue sa propre partie via l'emplacement 4 du harnais de
  `claude/` : voir `claude/doc/agent-externe.md`.

L'ancien chemin `run_06.09.26/super_nethack_astra` est un lien symbolique vers `claude/` (compatibilité).
