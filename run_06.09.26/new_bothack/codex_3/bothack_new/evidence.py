import json
from pathlib import Path

def write_manifest(run_dir: Path, manifest: dict) -> None:
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def summarize(root: Path) -> dict:
    rows = []
    for path in sorted(root.glob("*/manifest.json")):
        rows.append(json.loads(path.read_text(encoding="utf-8")))
    return {"runs":len(rows), "ascensions":sum(x.get("status") == "ascension_candidate" for x in rows), "statuses":{s:sum(x.get("status") == s for x in rows) for s in sorted({x.get("status") for x in rows})}, "entries":rows}
