#!/usr/bin/env python3
"""Negative tests for the comparison verdict and the strict tap reader.

These exist because the previous comparator reported a success for two of the
cases below.  A campaign that counts false successes is worse than no campaign.
"""
import os
import struct
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import tapio                                       # noqa: E402
from tools import verdict as V                                # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("  ok   %s" % name)
    else:
        print("  FAIL %s %s" % (name, detail))
        FAILURES.append(name)


def check_manifest_accounting():
    """A DIVERGENCE must count as identical up to `first_divergence`.

    `common_prefix` is min(len(expected), len(got)) - how far the two streams
    *overlap*, not how far they agree.  Using it for the manifest's "identical"
    column reported a diverging run as 100 % identical, which overstates a whole
    campaign at once.
    """
    import json
    import subprocess
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with tempfile.TemporaryDirectory() as tmp:
        d = os.path.join(tmp, 'seed99999', 'replay')
        os.makedirs(d)
        json.dump({'status': 'GAME', 'keystrokes': 1000, 'output': 10,
                   'chunks': 2, 'attested_end': True,
                   'end_marker': 'You die...', 'player': 'x'},
                  open(os.path.join(tmp, 'seed99999', 'recording.json'), 'w'))
        json.dump({'expected_bytes': 1000, 'got_bytes': 1000,
                   'common_prefix': 1000, 'attested_end': True,
                   'first_divergence': 400, 'status': 'DIVERGENCE'},
                  open(os.path.join(d, 'verdict.json'), 'w'))
        subprocess.check_output(
            [sys.executable,
             os.path.join(root, 'tools', 'fidelity_manifest.py'), tmp],
            stderr=subprocess.DEVNULL)
        man = json.load(open(os.path.join(tmp, 'manifest.json')))
    row = man['rows'][0]
    check("divergence counts as identical only up to the divergence",
          row['identical_prefix'] == 400, "got %r" % (row['identical_prefix'],))
    check("campaign total does not use the overlap length",
          man['identical_keystrokes_total'] == 400,
          "got %r" % (man['identical_keystrokes_total'],))
    check("a divergence is not counted as a pass", man['passes'] == 0,
          "got %r" % (man['passes'],))


def rec(d, payload):
    return d + struct.pack('<I', len(payload)) + payload


def write(tmp, data):
    p = os.path.join(tmp, "t.log")
    open(p, 'wb').write(data)
    return p


def main():
    print("verdict:")
    v = V.compare(b"abc", b"abc", attested_end=True)
    check("equal streams + attested end -> PASS_COMPLETE",
          v['status'] == V.PASS_COMPLETE, v['status'])

    v = V.compare(b"abc", b"abc", attested_end=False)
    check("equal streams, cut-off capture -> PASS_CAPTURE",
          v['status'] == V.PASS_CAPTURE, v['status'])

    v = V.compare(b"abc", b"abd", attested_end=True)
    check("one byte substituted -> DIVERGENCE",
          v['status'] == V.DIVERGENCE and v['first_divergence'] == 2,
          str(v))

    v = V.compare(b"abc", b"abcd", attested_end=True)
    check("one extra byte -> PREFIX_ONLY (not a pass)",
          v['status'] == V.PREFIX_ONLY and v['status'] not in V.SUCCESS,
          v['status'])

    v = V.compare(b"abcd", b"abc", attested_end=True)
    check("strict prefix -> PREFIX_ONLY (not a pass)",
          v['status'] == V.PREFIX_ONLY, v['status'])

    v = V.compare(b"abc", b"abc", attested_end=True, timed_out=True)
    check("timeout never passes", v['status'] == V.TIMEOUT, v['status'])

    check("exit code 0 only for a success",
          V.EXIT_CODES[V.PASS_COMPLETE] == 0
          and V.EXIT_CODES[V.PASS_CAPTURE] == 0
          and all(V.EXIT_CODES[s] != 0 for s in
                  (V.PREFIX_ONLY, V.DIVERGENCE, V.TIMEOUT,
                   V.INVALID_TRACE, V.HARNESS_ERROR)))

    print("strict tap reader:")
    with tempfile.TemporaryDirectory() as tmp:
        good = rec(b'O', b"hello") + rec(b'I', b"y")
        p = write(tmp, good)
        recs = tapio.read_records(p)
        check("well-formed capture parses",
              len(recs) == 2 and tapio.keystrokes(recs) == b"y")

        p = write(tmp, good + rec(b'O', b"xxxx")[:6])
        try:
            tapio.read_records(p)
            check("truncated payload rejected", False, "no error raised")
        except tapio.TapError:
            check("truncated payload rejected", True)

        p = write(tmp, good + b"\x00\x01")
        try:
            tapio.read_records(p)
            check("trailing bytes rejected", False, "no error raised")
        except tapio.TapError:
            check("trailing bytes rejected", True)

        p = write(tmp, rec(b'X', b"nope"))
        try:
            tapio.read_records(p)
            check("invalid record type rejected", False, "no error raised")
        except tapio.TapError:
            check("invalid record type rejected", True)

        p = write(tmp, b"")
        try:
            tapio.read_records(p)
            check("empty capture rejected", False, "no error raised")
        except tapio.TapError:
            check("empty capture rejected", True)

        p = write(tmp, rec(b'O', b"You die...  "))
        check("attested end detected",
              tapio.attested_end(tapio.read_records(p)))
        p = write(tmp, rec(b'O', b"still playing"))
        check("cut-off capture not attested",
              not tapio.attested_end(tapio.read_records(p)))

    print("manifest accounting")
    check_manifest_accounting()

    print()
    if FAILURES:
        print("%d FAILED: %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("all verdict/tap-reader checks passed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
