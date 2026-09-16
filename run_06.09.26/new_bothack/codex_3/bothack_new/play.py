import argparse, json, time
from pathlib import Path
from .session import Session
from .evidence import write_manifest

def main(argv=None):
    ap=argparse.ArgumentParser(description="Run the independent BotHack ascension prototype")
    ap.add_argument("--game", required=True); ap.add_argument("--seconds", type=float, default=300); ap.add_argument("--runs", default="runs")
    a=ap.parse_args(argv); stamp=time.strftime("%Y%m%dT%H%M%SZ")
    run=Path(a.runs) / stamp
    result=Session(a.game, run, a.seconds, user="bh"+stamp[-10:]).run(); write_manifest(run,result); print(json.dumps(result, indent=2)); return 0
if __name__ == "__main__": raise SystemExit(main())
