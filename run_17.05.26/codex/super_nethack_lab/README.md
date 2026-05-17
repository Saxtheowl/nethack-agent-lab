# Super NetHack BotHack Lab

Isolated lab for BotHack, the documented first NetHack 3.4.3 bot to ascend. The setup builds NetHack 3.4.3 in its own Docker image, clones BotHack, records ttyrec files, and serves a browser replay UI.

Sources used:

- NetHack Wiki documents that `smartbot3`, based on BotHack, first ascended on 2015-01-25: https://nethackwiki.com/wiki/Bot
- BotHack source and historical ttyrecs: https://github.com/krajj7/BotHack
- NetHack 3.4.3 nethack.alt.org source tree: https://www.alt.org/nethack/nh343-nao.git

## Start

```bash
cd super_nethack_lab
docker compose up --build
```

Services:

- SSH: `ssh botlab@localhost -p 2223` with password `botlab`
- Replay UI: http://localhost:8080

The compose project uses its own image, container name, ports and mounted folders, so it does not modify the existing `super-nethack` container.

## Import Known BotHack Ascension Replays

```bash
docker exec -it super-nethack-bothack-lab /opt/botlab_scripts/import-historical-ttyrecs.sh
```

This copies the BotHack repository ttyrecs into `recordings/` and known ascension ttyrecs into `wins/`, then refreshes the replay index.

## Run BotHack

One attempt:

```bash
docker exec -it super-nethack-bothack-lab /opt/botlab_scripts/run-bothack-once.sh
```

Keep attempting until 10 ascension directories exist:

```bash
docker exec -it super-nethack-bothack-lab /opt/botlab_scripts/run-until-10-wins.sh 10
```

Artifacts:

- `recordings/<run_id>/`: ttyrec and logs for every attempt
- `wins/<run_id>/`: copied artifacts for detected ascensions
- `seeds/<run_id>.json`: run metadata
- `logs/<run_id>.*.log`: BotHack process logs

Notes:

- BotHack's own docs target NetHack 3.4.3 with the nethack.alt.org patchset. This lab builds that NAO 3.4.3 tree, not a newer NetHack.
- Vanilla NetHack 3.4.3 does not expose a stable replay seed via the tty interface. For now, the replayable artifact is the ttyrec. The seed JSON explicitly records that limitation so the next step can patch 3.4.3 RNG seeding without mixing it into the replay UI work.
- The repository ttyrecs include two known ascension replays and are imported into `wins/`. The `run-until-10-wins.sh` script is ready for fresh attempts, but those long runs are intentionally not started by `docker compose up`.

## Replay UI

Open http://localhost:8080 and select a ttyrec. Controls:

- play/pause
- previous/next frame
- jump by 10 frames
- scrubber
- speed slider
- keyboard: Space, ArrowLeft/ArrowRight, Shift+ArrowLeft/Shift+ArrowRight

## Tests

Host-side parser tests:

```bash
cd super_nethack_lab
python3 -m pip install pyte pytest
pytest
```

Container-side:

```bash
docker exec -it super-nethack-bothack-lab env PYTHONPATH=/opt pytest /opt/tests
```
