# Easy NetHack Recreated

Reconstruction du dossier qui a probablement servi a construire le conteneur Docker `easy_win-nethack` actuellement lance sous le nom `super-nethack`.

Le conteneur observe:

- image: `easy_win-nethack:latest`
- entrypoint: `/opt/nethack/entrypoint.sh`
- SSH: port conteneur `22`, port hote `2222`
- volume persistant: `/data`
- service compose original: `nethack`

Demarrage:

```sh
docker compose up -d --build
ssh nethack@localhost -p 2222
```

Le mot de passe est vide, comme dans le conteneur observe. Les bots de wish se togglent depuis le menu SSH avec `b`.
