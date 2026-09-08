#!/usr/bin/env python3
"""Compare the keystrokes two bots sent while playing the same deterministic
game (two tools/pty_tap.py recordings), and return an explicit verdict.

Exit code is the verdict's: 0 only for PASS_COMPLETE / PASS_CAPTURE.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import tapio                                        # noqa: E402
from tools import verdict as V                                 # noqa: E402


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: compare_taps.py <original.tap> <port.tap> [--json]")
    try:
        a = tapio.read_records(sys.argv[1])
        b = tapio.read_records(sys.argv[2])
    except tapio.TapError as e:
        print("status: %s\n%s" % (V.INVALID_TRACE, e))
        return V.EXIT_CODES[V.INVALID_TRACE]
    v = V.compare(tapio.keystrokes(a), tapio.keystrokes(b),
                  attested_end=tapio.attested_end(a))
    v['original_output_bytes'] = len(tapio.output(a))
    v['port_output_bytes'] = len(tapio.output(b))
    if '--json' in sys.argv:
        print(json.dumps(v, indent=2))
    else:
        print(V.format_verdict(v))
    return V.EXIT_CODES[v['status']]


if __name__ == '__main__':
    sys.exit(main())
