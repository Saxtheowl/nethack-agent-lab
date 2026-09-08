#!/usr/bin/env python3
"""Replay a recorded game (tools/pty_tap.py log) of the ORIGINAL BotHack into
the Python port and compare, byte for byte, the keystrokes both bots send.

The port sees exactly the same terminal output, in exactly the same chunks, so
any difference in the produced keystrokes is a behavioural difference.  Both
bots use the same deterministic RNG (see tools/cljcmp/runner.clj).
"""
import argparse
import logging
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pybothack.bothack import new_bh, start, stop            # noqa: E402
from pybothack.delegator import Handler                      # noqa: E402
from pybothack.handlers import register_handler              # noqa: E402
from pybothack.util import LCG, PRIORITY_TOP                 # noqa: E402
from pybothack.action import typekw                          # noqa: E402


def read_tap(path):
    """Strict: a truncated or malformed capture must not look like a short
    valid one (tools/tapio.py)."""
    from tools import tapio
    return tapio.read_records(path)


class ReplayInterface(object):
    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.pos = 0
        self.writes = []

    def start(self):
        return self

    def read(self, n=256):
        if self.pos >= len(self.chunks):
            return b''
        c = self.chunks[self.pos]
        self.pos += 1
        return c

    def write(self, data):
        if isinstance(data, str):
            data = data.encode('latin-1')
        self.writes.append(data)

    def wait_readable(self, timeout):
        return self.pos < len(self.chunks)

    def alive(self):
        return self.pos < len(self.chunks)

    def stop(self):
        pass


def _dump_state(bh, pos):
    from pybothack.dungeon import curlvl, at_curlvl
    from pybothack.pathing import explorable_tile, isolated
    from pybothack.position import neighbors, Pos
    from pybothack.tile import walkable, boulder, blank
    g = bh.game.deref()
    lvl = curlvl(g)
    print("=== state at action, player=(%s,%s) turn=%s"
          % (g['player']['x'], g['player']['y'], g['turn']))
    for row in lvl['tiles']:
        print("".join(t['glyph'] for t in row))
    print("--- explorable tiles:", [(t['x'], t['y']) for t in
                                    [x for r in lvl['tiles'] for x in r]
                                    if explorable_tile(lvl, t)][:20])
    if pos:
        x, y = [int(v) for v in pos.split(',')]
        t = at_curlvl(g, Pos(x, y))
        print("--- tile", (x, y), {k: v for k, v in t.items()
                                   if k not in ('items', 'deaths', 'tags')})
        print("    explorable:", explorable_tile(lvl, t),
              "isolated:", isolated(lvl, t))
        for n in neighbors(lvl, t):
            print("     nbr", (n['x'], n['y']), 'seen', n.get('seen'),
                  'feature', n.get('feature'), 'glyph', repr(n['glyph']))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tap_log')
    ap.add_argument('--seed', type=int, default=12345)
    ap.add_argument('--report', default=None)
    ap.add_argument('--keys-out', default=None)
    ap.add_argument('--actions-out', default=None)
    ap.add_argument('--dump-at', type=int, default=None,
                    help="dump the level around the player when action N is "
                         "chosen")
    ap.add_argument('--dump-pos', default=None)
    ap.add_argument('--expected-keys', default=None,
                    help="compare against this keystroke dump instead of the "
                         "'I' records of the tap log (use the original's "
                         "replay capture for an apples-to-apples comparison)")
    ap.add_argument('--log', default='ERROR')
    ap.add_argument('--trace-rng', default=None,
                    help="write every LCG draw (value, caller) to this file")
    ap.add_argument('--max-actions', type=int, default=None,
                    help="stop the replay after this many chosen actions")
    ap.add_argument('--log-messages', default=None,
                    help="log every game message the port received, tagged "
                         "with the action index")
    ap.add_argument('--verdict-out', default=None,
                    help="write the structured verdict (JSON) here")
    a = ap.parse_args()
    logging.basicConfig(level=getattr(logging, a.log.upper()),
                        format='%(levelname)s %(name)s %(message)s')

    if a.trace_rng:
        LCG.trace = []
    recs = read_tap(a.tap_log)
    out_chunks = [c for d, c in recs if d == 'O']
    if a.expected_keys:
        expected = open(a.expected_keys, 'rb').read()
    else:
        expected = b"".join(c for d, c in recs if d == 'I')

    iface = ReplayInterface(out_chunks)
    config = {'bot': 'mainbot', 'interface': 'shell', 'nh-command': 'replay',
              'no-exit': True}
    bh = new_bh(config=config, rng=LCG(a.seed))
    bh.iface = iface
    bh.delegator.set_writer(iface.write)
    actions = []
    _rng_marks = []

    def _record(act):
        if a.dump_at is not None and len(actions) == a.dump_at:
            _dump_state(bh, a.dump_pos)
        detail = ""
        if typekw(act) == 'autotravel':
            detail = " pos=(%d,%d) path=%s" % (
                act['pos']['x'], act['pos']['y'],
                [(p['x'], p['y']) for p in (act.get('path') or ())])
        elif act.get('dir'):
            detail = " dir=%s" % act['dir']
        # Stringify (and truncate) here: the reason lists hold whole tile and
        # monster maps, and keeping thousands of them alive is hundreds of MB.
        reasons = [str(r)[:120] for r in (act.get('reason') or ())]
        actions.append((typekw(act), reasons + [detail]))
        if a.trace_rng:
            _rng_marks.append((len(actions), len(LCG.trace)))
        if a.max_actions is not None and len(actions) >= a.max_actions:
            bh._stop = True
    register_handler(bh, PRIORITY_TOP - 1, Handler(action_chosen=_record))

    if a.log_messages:
        # The port's own UI logger only exists in main.py, so a replay was
        # blind to what the game actually said - which is the first thing you
        # need when the two bots disagree about what a Look revealed.
        msg_log = open(a.log_messages, 'w')

        def _off():
            # keystroke offset: the only index that aligns with the original's
            # stream, since the two bots count actions differently (Repeated)
            return sum(len(w) for w in iface.writes)

        def _msg(text):
            msg_log.write("@%d [%d] topline: %s\n"
                          % (_off(), len(actions), text))

        def _msg_lines(lines):
            msg_log.write("@%d [%d] lines: %s\n"
                          % (_off(), len(actions), lines))
        register_handler(bh, PRIORITY_TOP - 1,
                         Handler(message=_msg, message_lines=_msg_lines))

    bh.delegator.started()
    bh.delegator.drain()
    n = 0
    try:
        while iface.pos < len(out_chunks) and not bh._stop:
            data = iface.read()
            if not data:
                break
            n += 1
            bh.terminal.feed(data)
            bh.delegator.redraw(bh.terminal.frame())
    except Exception:                                     # noqa: BLE001
        logging.exception("replay aborted after %d chunks", n)

    if a.actions_out:
        with open(a.actions_out, 'w') as f:
            for t, reason in actions:
                f.write("%s\t%s\n" % (t, " | ".join(reason or ())))
    if a.trace_rng:
        marks = dict((n, i) for i, n in _rng_marks)
        with open(a.trace_rng, 'w') as f:
            for i, (idx, v, where) in enumerate(LCG.trace):
                f.write("%6d  %6d  %s%s\n"
                        % (idx, v, where,
                           "   <- after action %d" % marks[i]
                           if i in marks else ""))
    got = b"".join(iface.writes)
    if a.keys_out:
        with open(a.keys_out, 'wb') as f:
            f.write(got)
    common = min(len(got), len(expected))
    div = None
    for i in range(common):
        if got[i] != expected[i]:
            div = i
            break
    if div is None and len(got) != len(expected):
        div = common

    from tools import tapio, verdict as V
    v = V.compare(expected, got, attested_end=tapio.attested_end(recs),
                  timed_out=bool(a.max_actions
                                 and len(actions) >= a.max_actions))
    v['chunks_replayed'] = n
    v['chunks_total'] = len(out_chunks)
    v['port_actions'] = len(actions)
    if a.verdict_out:
        import json
        with open(a.verdict_out, 'w') as f:
            json.dump(v, f, indent=2)

    lines = []
    lines.append("status: %s" % v['status'])
    lines.append("chunks replayed: %d/%d" % (n, len(out_chunks)))
    lines.append("keystrokes: original %d bytes, port %d bytes"
                 % (len(expected), len(got)))
    lines.append("actions chosen by the port: %d" % len(actions))
    if div is None:
        lines.append("IDENTICAL: the port produced the same %d keystroke bytes"
                     % len(got))
    else:
        lines.append("first divergence at keystroke byte %d (%.1f%% of the "
                     "original's stream)" % (div, 100.0 * div / max(1, len(expected))))
        lines.append("  original: %r" % expected[max(0, div - 40):div + 20])
        lines.append("  port    : %r" % got[max(0, div - 40):div + 20])
    # difflib is quadratic in memory on long streams and a full game is
    # ~100 KB per side; the leading-prefix length is the result that matters,
    # the similarity ratio is only a comfort metric.
    limit = int(os.environ.get('REPLAY_DIFFLIB_LIMIT', '40000'))
    if max(len(expected), len(got)) <= limit:
        import difflib
        sm = difflib.SequenceMatcher(None, expected, got, autojunk=False)
        lines.append("keystroke-stream similarity: %.2f%%" % (100 * sm.ratio()))
        blocks = [b for b in sm.get_matching_blocks() if b.size > 0]
        lines.append("matching blocks: %d (longest %d bytes)"
                     % (len(blocks), max([b.size for b in blocks] or [0])))
    else:
        lines.append("keystroke-stream similarity: not computed (streams over "
                     "%d bytes; set REPLAY_DIFFLIB_LIMIT to override)" % limit)
    if actions:
        lines.append("last actions: %s"
                     % ", ".join(t for t, _ in actions[-8:]))
    report = "\n".join(lines)
    print(report)
    if a.report:
        with open(a.report, 'w') as f:
            f.write(report + "\n")
    stop(bh)
    from tools import verdict as _V
    return _V.EXIT_CODES[v['status']]


if __name__ == '__main__':
    sys.exit(main())
