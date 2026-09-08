"""Load the data extracted verbatim from the original BotHack (_data.json).

The JSON is produced by tools/cljdump/dumpdata.clj which serialises the
original item types, monster types, level blueprints and sokoban solutions.
"""

import json
import os

_DATA = None


def load():
    global _DATA
    if _DATA is None:
        path = os.path.join(os.path.dirname(__file__), "_data.json")
        with open(path, "r") as f:
            _DATA = json.load(f)
    return _DATA


def data():
    return load()