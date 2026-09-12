"""Canonical JSON identical to the one produced by tools/cljcmp/oracle.clj,
so Clojure and Python answers can be compared as strings."""


def _esc(s):
    return '"' + (str(s).replace('\\', '\\\\').replace('"', '\\"')
                  .replace('\n', '\\n').replace('\t', '\\t')
                  .replace('\r', '\\r')) + '"'


def jsn(x):
    if x is None:
        return "null"
    if x is True:
        return "true"
    if x is False:
        return "false"
    if isinstance(x, str):
        return _esc(x)
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, int):
        return str(x)
    if isinstance(x, float):
        # Java prints the shortest round-tripping form; %.17g and repr() can
        # differ in the last digit, so normalise to 15 significant digits.
        return "%.10e" % x
    if isinstance(x, (set, frozenset)):
        return "[" + ",".join(jsn(v) for v in sorted(x, key=str)) + "]"
    if isinstance(x, dict):
        items = sorted(x.items(), key=lambda kv: str(kv[0]))
        return "{" + ",".join(_esc(k) + ":" + jsn(v) for k, v in items) + "}"
    if isinstance(x, (list, tuple)):
        return "[" + ",".join(jsn(v) for v in x) + "]"
    return _esc(x)
