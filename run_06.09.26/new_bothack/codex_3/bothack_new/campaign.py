import argparse, json, secrets
from pathlib import Path
from .session import Session
from .evidence import write_manifest, summarize

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--game",required=True); ap.add_argument("--runs",type=int,default=3); ap.add_argument("--seconds",type=float,default=300); ap.add_argument("--out",default="runs")
    a=ap.parse_args(argv); root=Path(a.out); root.mkdir(exist_ok=True)
    for i in range(a.runs):
        run=root / f"run-{i+1:04d}-{secrets.token_hex(4)}"; m=Session(a.game,run,a.seconds,user=f"bh{i+1:04d}").run(); write_manifest(run,m); print(json.dumps(m),flush=True)
    (root/"campaign.json").write_text(json.dumps(summarize(root),indent=2)+"\n",encoding="utf-8")
    return 0
if __name__ == "__main__": raise SystemExit(main())
