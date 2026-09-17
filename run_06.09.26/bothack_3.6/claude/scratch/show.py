import json,sys
r=json.load(open(sys.argv[1]+'/result.json'))
for k in r:
    if k not in ('final_screen','engine_verdict','xlogfile'): print(k, '=', r[k] if k!='reason' else r[k][-600:])
print('\n'.join(r['final_screen'] or []))
