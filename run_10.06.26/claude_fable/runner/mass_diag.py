"""Mass-classify navigation failures from a directory of state.json files."""
import json
import glob
import sys
import collections

sys.path.insert(0, "bot")
from level import Level, MONSTER_CHARS, W, H


def load_level(lv, key):
    L = Level(key)
    for y in range(H):
        fgs = lv["fgs"][y].split(",")
        row = lv["chars"][y]
        for x in range(W):
            ch = row[x] if x < len(row) else " "
            t = L.tiles[y][x]
            if ch != " ":
                t.char = ch
                t.fg = fgs[x]
                t.seen = True
    L.visited = set(tuple(v) for v in lv.get("visited", []))
    for e in lv.get("blocked_edges", []):
        a, b, c = e
        cnt, tn = (c if isinstance(c, list) else [c, 0])
        L.blocked_edges[(tuple(a), tuple(b))] = (cnt, tn)
    for x, y, v in lv.get("peaceful", []):
        L.tiles[y][x].peaceful_until = v
    for x, y in lv.get("hard_bans", []):
        L.tiles[y][x].hard_ban = True
    return L


def classify(path):
    meta = json.load(open(path.replace("state.json", "meta.json")))
    res = meta.get("result", "")
    if not (res.startswith("abort") or res == "terminated"):
        return None
    d = json.load(open(path))
    branch, dlvl = d["branch"], d["dlvl"]
    key = f"{branch}:{dlvl}"
    if key not in d or d["hero"] is None:
        return ("no-state", res)
    lv = d[key]
    hero = tuple(d["hero"])
    turn = d["turn"]
    L = load_level(lv, (branch, dlvl))
    down = set(tuple(s) for s in lv.get("stairs_down", []))
    tried = set(tuple(s) for s in lv.get("tried_down", []))
    untried = down - tried

    f = L.frontier_path(hero, turn)
    fi = L.frontier_path(hero, turn, ignore_monsters=True)
    probes = L.probe_targets(hero, turn)
    spots = L.search_spots(hero, turn)

    if untried:
        p = L.path_to(hero, untried, turn)
        pi = L.path_to(hero, untried, turn, ignore_monsters=True)
        if p:
            return ("stairs-reachable!?", res)
        if pi:
            nx, ny = pi[0]
            t = L.tiles[ny][nx]
            return (f"stairs-blocked-by-{t.char}", res)
        return ("stairs-unreachable-hard", res)
    if f:
        return ("frontier-exists!?", res)
    if fi:
        nx, ny = fi[0]
        return (f"frontier-blocked-by-{L.tiles[ny][nx].char}", res)
    if probes:
        pp = L.path_to(hero, set(probes), turn)
        ppi = L.path_to(hero, set(probes), turn, ignore_monsters=True)
        if pp:
            return ("probe-reachable!?", res)
        if ppi:
            nx, ny = ppi[0]
            return (f"probe-blocked-by-{L.tiles[ny][nx].char}", res)
        return ("probe-unreachable-hard", res)
    if spots:
        sp = L.path_to(hero, set(spots), turn)
        if sp:
            return ("searching-legit", res)
        return ("spots-unreachable", res)
    return ("truly-exhausted", res)


def main(d):
    out = collections.Counter()
    examples = {}
    for p in sorted(glob.glob(d + "/*/state.json")):
        try:
            r = classify(p)
        except Exception as e:
            r = (f"err:{e}", "")
        if r is None:
            continue
        out[r[0]] += 1
        examples.setdefault(r[0], p)
    for k, v in out.most_common():
        print(f"{v:4d}  {k}   ex: {examples[k].split('/')[-2]}")


if __name__ == "__main__":
    main(sys.argv[1])
