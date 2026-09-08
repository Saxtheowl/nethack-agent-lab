"""Compare Python terminal snapshots with JTA on an actual recorded game."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bothack.terminal import Terminal, read_ttyrec
from tools.oracle import Oracle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ttyrec", type=Path)
    parser.add_argument("--records", type=int, default=500)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/terminal-parity.json")
    args = parser.parse_args()
    terminal = Terminal()
    mismatches = []
    total = 0
    with Oracle() as oracle, args.ttyrec.open("rb") as stream:
        oracle.call("terminal-reset")
        for record in read_ttyrec(stream):
            actual = json.loads(json.dumps(asdict(terminal.feed(record.payload))))
            expected = oracle.call("terminal-feed", record.payload.decode("latin1"))
            total += 1
            if actual != expected:
                mismatches.append({"record": total, "actual": actual, "expected": expected})
                if len(mismatches) >= 3:
                    break
            if args.records and total >= args.records:
                break
    report = {"file": str(args.ttyrec), "sha256": hashlib.sha256(args.ttyrec.read_bytes()).hexdigest(),
              "records_checked": total, "mismatches": mismatches}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"records_checked": total, "mismatches": len(mismatches)}))
    return bool(mismatches)


if __name__ == "__main__":
    raise SystemExit(main())
