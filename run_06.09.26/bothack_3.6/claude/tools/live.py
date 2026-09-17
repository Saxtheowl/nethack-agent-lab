"""Print live.json of running games: python3 tools/live.py runs/mt-s03 runs/scen/x"""
import glob, json, os, sys
paths = []
for a in sys.argv[1:] or ['runs']:
    if os.path.exists(os.path.join(a, 'live.json')):
        paths.append(a)
    else:
        paths += sorted(os.path.dirname(p) for p in glob.glob(os.path.join(a, '*', 'live.json')))
for p in paths:
    if os.path.exists(os.path.join(p, 'result.json')):
        r = json.load(open(os.path.join(p, 'result.json')))
        print("%-26s DONE %-12s T=%-6s %s" % (p[-26:], r.get('outcome'), r.get('turns'), (r.get('reason') or '').strip().splitlines()[-1][:110] if r.get('reason') else ''))
        continue
    try:
        d = json.load(open(os.path.join(p, 'live.json')))
    except Exception as e:
        print(p, e); continue
    la = d.get('last_action') or {}
    print("%-26s t=%-5s T=%-6s %-10s xl=%-2s hp=%s/%s maxd=%s stages=%s notes=%s last=%s %s" % (
        p[-26:], d['t'], d['turn'], d['lvl'], d['xl'], d['hp'], d['hpmax'], d['max_depth'],
        list(d['stages']), {k: v for k, v in d['notes'].items() if k not in ('assist', 'scenario')},
        la.get('act'), (la.get('why') or [''])[0][:60]))
