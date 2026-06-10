# Wish All Classes

Variante du serveur NetHack qui prepare des parties arrivees au prompt `For what do you wish?` pour toutes les classes.

Objectif:

- 1 partie wish disponible par role NetHack
- roles couverts: Archeologist, Barbarian, Caveman, Healer, Knight, Monk, Priest, Ranger, Rogue, Samurai, Tourist, Valkyrie, Wizard
- menu SSH avec choix du role avant de rejoindre une partie wish
- binaire NetHack patche pour accepter `MAXPLAYERS=60`
- jusqu'a 13 bots concurrents, soit 1 generateur par role, avec un plafond de 55 sessions actives pour garder de la marge joueur

Demarrage:

```sh
docker compose up -d --build
ssh nethack@localhost -p 2223
```

Les bots se togglent depuis le menu SSH avec `b`. Le gestionnaire maintient le pool en continu tant que `/data/bots_enabled` existe.
