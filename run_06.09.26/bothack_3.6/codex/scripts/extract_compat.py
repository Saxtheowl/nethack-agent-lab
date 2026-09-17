"""Regenerate version-specific observable data from the pinned C source."""
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'vendor/NetHack-NetHack-3.6.7_Released/src/objects.c').read_text()
labels=re.findall(r'SCROLL\((?:"[^"]*"|None),\s*"([^"]+)"',s)
labels=[f'scroll labeled {x}' for x in labels if x not in ('stamped','unlabeled')]
(ROOT/'pybothack/_compat367.json').write_text(json.dumps({'scroll_appearances':labels},indent=2)+'\n')
