"""Loader for the reference data extracted from the original Clojure sources
(see tools/cljdump/dumpdata.clj).  Using the original's own data avoids any
transcription drift in the 1722 item types, 376 monster types and the special
level blueprints."""
import json
import os

from .position import Pos

_HERE = os.path.dirname(os.path.abspath(__file__))


def _decode(x):
    if isinstance(x, dict):
        if '__set__' in x:
            return set(_decode(v) for v in x['__set__'])
        if '__map__' in x:
            d = {}
            for k, v in x['__map__']:
                d[_decode(k)] = _decode(v)
            if (len(d) == 2 and 'x' in d and 'y' in d
                    and isinstance(d['x'], int) and isinstance(d['y'], int)):
                return Pos(d['x'], d['y'])
            return d
        return {k: _decode(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_decode(v) for v in x]
    return x


def load(name):
    with open(os.path.join(_HERE, name), 'r') as f:
        return _decode(json.load(f))


DATA = load('_data.json')
LEVELDATA = load('_leveldata.json')

# 3.6.7 shuffled scroll labels, extracted from src/objects.c. Extend the
# candidate relation without inventing an identification for any appearance.
COMPAT367 = load('_compat367.json')
_added_scrolls = [a for a in COMPAT367['scroll_appearances'] if a not in DATA['scroll-appearances']]
DATA['scroll-appearances'].extend(_added_scrolls)
DATA['exclusive-appearances'].update(_added_scrolls)
for _item in DATA['items']:
    if any(a.startswith('scroll labeled ') for a in _item.get('appearances', ())):
        _item['appearances'].extend(_added_scrolls)
for _appearance in _added_scrolls:
    DATA['appearance-names'][_appearance] = list(DATA['appearance-names']['scroll labeled ZELGO MER'])
