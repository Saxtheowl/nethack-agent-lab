"""Run the Python bot for a while and dump its internal map for inspection."""
import argparse
import logging
import random
import sys

sys.path.insert(0, '.')
from pybothack.bothack import new_bh, run, start, stop, _load_config
from pybothack.dungeon import curlvl, branch_key
from pybothack.main import init_ui


def print_level(level, f=lambda t: t['glyph']):
    for row in level['tiles']:
        print("".join(str(f(t))[0] if f(t) else ' ' for t in row))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seconds', type=float, default=30)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--config', default='config/shell-config.edn')
    a = ap.parse_args()
    logging.basicConfig(level=logging.WARNING)
    bh = new_bh(config=_load_config(a.config), rng=random.Random(a.seed))
    init_ui(bh)
    try:
        start(bh)
        run(bh, max_seconds=a.seconds)
    finally:
        stop(bh)
    g = bh.game.deref()
    print("=== FRAME ===")
    print(g['frame'])
    print("=== GLYPHS ===")
    print_level(curlvl(g))
    print("=== FEATURES (first letter) ===")
    print_level(curlvl(g), lambda t: (t.get('feature') or ' '))
    print("=== branch:", branch_key(g), "dlvl:", g['dlvl'], "turn:", g['turn'])
    lvl = curlvl(g)
    print("stairs:", [(t['x'], t['y'], t['feature']) for t in
                      [x for row in lvl['tiles'] for x in row]
                      if t.get('feature') in ('stairs-down', 'stairs-up')])
    print("explore-cache:", g.get('explore-cache'))


main()
