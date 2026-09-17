import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import tarfile
import uuid

ROOT=Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run_one(args, seed, batch):
    run=batch/f'seed-{seed}-{uuid.uuid4().hex[:6]}'
    run.mkdir(parents=True)
    shutil.copytree(ROOT/'build/game',run/'game')
    for name in ('record','logfile','xlogfile','perm'):
        (run/'game'/name).write_text('')
    (run/'engine.jsonl').touch()
    env=os.environ.copy()
    # Prepared scenes must never leak into a full-game campaign.
    env.pop('BH_FIXTURE',None)
    if args.scenario != 'full_from_start':
        env['BH_FIXTURE']=args.scenario
    env['BH_FAULT_PROMPT']=str(int(args.fault_prompt))
    env.update(BH_GAME_DIR=str(run/'game'),BH_SEED=str(seed),BH_EVENTS=str(run/'engine.jsonl'),
               BH_INVINCIBLE=str(int(not args.no_invincible)),BH_HUNGER=str(int(not args.no_hunger)),
               BH_KIT=str(int(not args.no_kit)), PYTHONHASHSEED='0')
    sources={str(p.relative_to(ROOT)):sha(p) for folder in ('localbot','pybothack','patches','scripts','config')
             for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in str(p)}
    with tarfile.open(run/'sources.tar.gz','w:gz') as archive:
        for source in sources:
            archive.add(ROOT/source,arcname=source)
    manifest={'engine':'NetHack 3.6.7','engine_sha256':sha(ROOT/'build/game/nethack'),
              'seed':seed,'aids':{k:env[k]=='1' for k in ('BH_INVINCIBLE','BH_HUNGER','BH_KIT')},
              'sources':sources,'python':sys.version,'started':time.time(),
              'limits':{'seconds':args.seconds,'turns':args.turns},'milestone':args.milestone,
              'fault_prompt':args.fault_prompt,'scenario':args.scenario,'seed_scope':'engine RNG and bot; calendar neutralized; scheduling not deterministic'}
    (run/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    with (run/'worker.log').open('w') as log:
        p=subprocess.Popen([sys.executable,'-m','localbot.worker',str(run),str(seed),str(args.seconds),str(args.turns),args.milestone],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            p.wait(timeout=args.seconds+15)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGTERM)
            p.wait(timeout=5)
            (run/'result.json').write_text(json.dumps({'outcome':'resource_limit','reason':'supervisor_wall_time','seed':seed}))
        finally:
            pidfile=run/'engine.pid'
            if pidfile.exists():
                try: os.kill(int(pidfile.read_text()),signal.SIGTERM)
                except ProcessLookupError: pass
    result=run/'result.json'
    if not result.exists():
        result.write_text(json.dumps({'outcome':'crash','reason':'worker_exit','returncode':p.returncode,'seed':seed}))
    r=json.loads(result.read_text());r['run']=str(run.relative_to(ROOT))
    return r

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--games',type=int,default=1)
    ap.add_argument('--seed',type=int,default=1)
    ap.add_argument('--seconds',type=float,default=120)
    ap.add_argument('--turns',type=int,default=10000)
    ap.add_argument('--milestone',choices=['minetown','ascension'],default='minetown')
    ap.add_argument('--no-invincible',action='store_true')
    ap.add_argument('--no-hunger',action='store_true')
    ap.add_argument('--no-kit',action='store_true')
    ap.add_argument('--scenario',choices=['full_from_start','astral-offer','hunger','death'],default='full_from_start')
    ap.add_argument('--fault-prompt',action='store_true',help='inject one unanswered direction prompt to test recovery')
    ap.add_argument('--label',default='local')
    args=ap.parse_args()
    if args.games<1 or args.seconds<=0 or args.turns<1: ap.error('limits must be positive')
    batch=ROOT/'runs'/f'{time.strftime("%Y%m%d-%H%M%S")}-{args.label}-{uuid.uuid4().hex[:4]}'
    batch.mkdir(parents=True)
    failures=Counter();results=[]
    for i in range(args.games):
        r=run_one(args,args.seed+i,batch);results.append(r);print(json.dumps(r),flush=True)
        (batch/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
        if r['outcome'] in ('blocked','crash'):
            signature=(r['outcome'],r['reason'],r.get('error'))
            failures[signature]+=1
            if failures[signature]>=2:
                print('Circuit breaker: repeated failure, batch stopped.',flush=True);break
if __name__=='__main__': main()
