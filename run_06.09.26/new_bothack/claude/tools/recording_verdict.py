#!/usr/bin/env python3
"""Judge a recording of the original: is it a *game* or a truncated capture?

A recording is only usable as evidence of a whole game if the capture attests
an end (death screen, possessions/attributes listing, quit).  Everything else
is a prefix, and a prefix can never yield PASS_COMPLETE - saying so here keeps
a wall-clock-capped run from being counted as a game later.

Also correlates with NetHack's own xlogfile entry for the player, which is the
only end-of-game record that does not come from the bot or from our capture.

    tools/recording_verdict.py TAP SEED PLAYER XLOGFILE OUT.json
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import tapio                                        # noqa: E402


KEEP = ('points', 'deathlev', 'maxlvl', 'hp', 'maxhp', 'turns', 'death',
        'role', 'race', 'align', 'starttime', 'endtime')


def xlog_entry(path, name, window):
    """The xlogfile line for this player whose endtime falls inside the
    recording's wall-clock window.

    Matching by name alone is not enough: var/ is shared, so a name can carry
    entries from earlier runs, and the wrong entry silently misattributes a
    game's turn count.  The window comes from the capture file's own ctime and
    mtime.

    `death` is the useful discriminator: a killed process (our wall-clock cap
    firing before the game ended) is logged by NAO's hangup path as
    `death=a trickery` with the pre-death hp, while a game that really ended
    carries its death reason and a non-positive hp.
    """
    if not os.path.exists(path):
        return None
    lo, hi = window
    found = None
    for line in open(path, errors='replace'):
        fields = dict(kv.split('=', 1) for kv in line.strip().split(':')
                      if '=' in kv)
        if fields.get('name') != name:
            continue
        try:
            endtime = int(fields.get('endtime', -1))
        except ValueError:
            continue
        if lo - 5 <= endtime <= hi + 5:
            found = fields          # last one inside the window wins
    if found is None:
        return None
    entry = {k: found.get(k) for k in KEEP}
    entry['matched_by'] = 'name + endtime inside the recording window'
    entry['killed_not_ended'] = found.get('death') == 'a trickery'
    return entry


def main():
    tap, seed, name, xlog, out = sys.argv[1:6]
    rec = {'seed': int(seed), 'player': name, 'tap': tap}
    try:
        records = tapio.read_records(tap)
    except (tapio.TapError, IOError) as e:
        rec.update(status='INVALID_TRACE', error=str(e))
    else:
        marker = tapio.end_marker(records)
        rec.update(keystrokes=len(tapio.keystrokes(records)),
                   output=len(tapio.output(records)),
                   chunks=sum(1 for kind, _ in records if kind == 'O'),
                   attested_end=marker is not None,
                   end_marker=marker.decode('latin-1') if marker else None,
                   status='GAME' if marker else 'TRUNCATED')
    # the recording's wall-clock window, from the capture file itself
    try:
        st = os.stat(tap)
        window = (int(st.st_ctime) - 1, int(st.st_mtime) + 1)
    except OSError:
        window = (0, 1 << 62)
    entry = xlog_entry(xlog, name, window)
    if entry:
        rec['xlog'] = entry
    with open(out, 'w') as fh:
        fh.write(json.dumps(rec, indent=1, sort_keys=True) + '\n')
    print('recording: status=%s keystrokes=%s output=%s chunks=%s end=%r'
          % (rec.get('status'), rec.get('keystrokes'), rec.get('output'),
             rec.get('chunks'), rec.get('end_marker')))
    if entry:
        print('  xlogfile: turns=%s points=%s maxlvl=%s hp=%s death=%s'
              % (entry.get('turns'), entry.get('points'), entry.get('maxlvl'),
                 entry.get('hp'), entry.get('death')))
    # exit 0 for a game, 1 for a prefix: callers can branch on it
    return 0 if rec.get('status') == 'GAME' else 1


if __name__ == '__main__':
    sys.exit(main())
