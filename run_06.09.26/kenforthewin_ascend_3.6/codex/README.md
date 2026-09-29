# Reprise NetHack Codex

Contrôleur séquentiel du slot 4, joueur Codex, run 1. La partie et les calculs
lourds restent sur miniforum-worker. Ce contrôleur léger tourne sur le PC où
le compte Codex est déjà connecté, sans copier ses identifiants.

`resume_loop.py` lit `account/rateLimits/read` sans inférence. Si le quota est
épuisé, il attend puis revérifie au maximum toutes les cinq minutes. Si le
quota est disponible, il lance une session Codex dédiée puis reprend toujours
son identifiant exact. Les décisions NetHack restent prises par le modèle.
Pas de rachat, de consommation de crédits de reset, de changement de compte
ou de modèle. La configuration de modèle Codex existante est conservée.

Un verrou empêche plusieurs boucles. STOP interrompt la session active; DONE
termine la boucle après mort, ascension ou blocage humain. Trois erreurs
techniques successives hors quota arrêtent aussi la boucle, avec le motif dans
le statut. Aucun redémarrage automatique après mort. Ne pas jouer manuellement
pendant que la boucle contrôle le slot.

- Direct : http://127.0.0.1:8766/ (Partie 4).
- État : `cat .resume-loop/status.json`
- Journal du contrôleur : `.resume-loop/runner.log`
- Sessions : `.resume-loop/*.jsonl` (privées; ne pas publier).
- Journal de jeu : `../claude/memory/codex-run-1.md`
- Arrêter : `touch .resume-loop/STOP`, puis attendre `phase: stopped`.
- Tester le quota sans jouer : `python3 resume_loop.py --check`

Le contrôleur utilise une session tmux isolée, socket `codex-slot4-auto`, session
`resume`. Il survit à la fermeture de cette conversation, mais pas à un reboot.
Il nécessite que ce PC reste allumé et connecté, et que le worker soit accessible.
