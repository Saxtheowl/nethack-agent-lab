# JEV_RAW

Jev selects direct NetHack actions.  BotHack supplies observation parsing,
action encoding, prompt/menu handling, supervision and evidence, but none of
`mainbot`'s strategic `choose_action` handlers are loaded.

Run: `python3 JEV_RAW/run.py --out runs/raw-42 --seed 42 --goal minetown`.

