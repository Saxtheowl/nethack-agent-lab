#!/usr/bin/env python3
"""Explicit statuses for a keystroke comparison.

The point of this module is that **only two statuses are a success**, and one
of them is weaker than it looks.  The old comparator printed "IDENTICAL over
the common prefix" and exited 0 when the two streams simply had different
lengths; that is not a reproduced game and must never be counted as one.
"""

PASS_COMPLETE = 'PASS_COMPLETE'   # every byte matched, and the game ended
PASS_CAPTURE = 'PASS_CAPTURE'     # every byte matched, but the capture was cut
PREFIX_ONLY = 'PREFIX_ONLY'       # agreed as far as one side went - not a pass
DIVERGENCE = 'DIVERGENCE'         # a byte differs
TIMEOUT = 'TIMEOUT'               # the run hit its wall clock
INVALID_TRACE = 'INVALID_TRACE'   # the recording is malformed
HARNESS_ERROR = 'HARNESS_ERROR'   # the comparison itself failed

SUCCESS = (PASS_COMPLETE, PASS_CAPTURE)

#: exit code per status, so a shell can branch without parsing text
EXIT_CODES = {PASS_COMPLETE: 0, PASS_CAPTURE: 0, PREFIX_ONLY: 3,
              DIVERGENCE: 4, TIMEOUT: 5, INVALID_TRACE: 6, HARNESS_ERROR: 7}


def compare(expected, got, attested_end=False, timed_out=False):
    """Compare two keystroke streams and return a structured verdict.

    `expected` is what the original sent, `got` what the port sent.
    """
    common = min(len(expected), len(got))
    div = next((i for i in range(common) if expected[i] != got[i]), None)
    res = {'expected_bytes': len(expected), 'got_bytes': len(got),
           'common_prefix': common, 'attested_end': bool(attested_end),
           'first_divergence': div}
    if div is not None:
        res['status'] = DIVERGENCE
        res['context_expected'] = repr(expected[max(0, div - 48):div + 24])
        res['context_got'] = repr(got[max(0, div - 48):div + 24])
    elif timed_out:
        res['status'] = TIMEOUT
    elif len(expected) != len(got):
        # one side simply stopped earlier: agreement so far, nothing more
        res['status'] = PREFIX_ONLY
        res['identical_prefix'] = common
    elif attested_end:
        res['status'] = PASS_COMPLETE
    else:
        res['status'] = PASS_CAPTURE
    return res


def exit_code(verdict):
    return EXIT_CODES.get(verdict.get('status'), HARNESS_ERROR and 7)


def format_verdict(v):
    lines = ["status: %s" % v['status'],
             "expected %d bytes, got %d bytes (common prefix %d)"
             % (v['expected_bytes'], v['got_bytes'], v['common_prefix']),
             "attested end of game: %s" % ("yes" if v['attested_end'] else "no")]
    if v.get('first_divergence') is not None:
        lines.append("first divergence at byte %d (%.1f%% of the expected "
                     "stream)" % (v['first_divergence'],
                                  100.0 * v['first_divergence']
                                  / max(1, v['expected_bytes'])))
        lines.append("  expected: %s" % v['context_expected'])
        lines.append("  got     : %s" % v['context_got'])
    if v['status'] == PREFIX_ONLY:
        lines.append("NOT a pass: the two runs cover different amounts of the "
                     "game; they merely agree over the shorter one.")
    if v['status'] == PASS_CAPTURE:
        lines.append("NOT a reproduced game: the recording itself was cut off "
                     "before the game ended.")
    return "\n".join(lines)
