# Codex NetHack slot 4

Le harnais est ../claude; cet espace contient uniquement le contrôleur Codex.
Lire ../claude/doc/agent-externe.md et ../claude/memory/codex-run-1.md avant de jouer.
Ne jamais contrôler un autre slot, modifier le harnais partagé ou lancer de calcul lourd ici.

## Reprise automatique

L'utilisateur a autorisé resume_loop.py à reprendre séquentiellement la session Codex
lorsque le quota est disponible. Il n'envoie aucune touche lui-même.
- Si NETHACK_RESUME_LOOP=1, suivre resume_prompt.txt; ne créer aucune autre boucle.
- Pour jouer manuellement ou changer le contrôleur, créer .resume-loop/STOP puis
  attendre que .resume-loop/status.json indique stopped et que le verrou soit libre.
- Une seule boucle détient .resume-loop/lock. Ne pas supprimer ce verrou.
- .resume-loop/DONE marque mort, ascension ou blocage nécessitant une intervention.
- Ne pas modifier .runtime/, scripts/, web/ ou config/ dans ../claude.
