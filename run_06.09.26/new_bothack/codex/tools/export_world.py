"""Export static original world blueprints; execution never needs Java."""
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.oracle import Oracle


if __name__ == '__main__':
    with Oracle() as oracle:
        data = oracle.call('world-data')
    (ROOT / 'bothack/data/world.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(f"Exported {len(data['blueprints'])} original blueprints")
