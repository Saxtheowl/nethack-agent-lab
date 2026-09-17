import collections
import json
import logging
import os
from pathlib import Path
import random
import sys
import time
import traceback
from pybothack.bothack import new_bh, start, stop, unpause
from pybothack.main import init_ui
from pybothack.handlers import register_handler
from pybothack.delegator import Handler
from pybothack.util import PRIORITY_TOP
from pybothack.action import typekw

ROOT = Path(__file__).resolve().parents[1]


def play(run, seed, seconds, turns, milestone):
    run = Path(run)
    logging.basicConfig(filename=run/'bot.log', level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(name)s %(message)s')
    bh = new_bh(config={'bot': 'mainbot', 'interface': 'shell', 'no-exit': True,
                       'nh-command': str(ROOT/'scripts/game.sh'),
                       'ttyrec': True, 'ttyrec-path': str(run/'game.ttyrec')},
                rng=random.Random(seed))
    init_ui(bh)
    output = (run/'trace.jsonl').open('w', buffering=1)
    begin = time.monotonic()
    last_choice = begin
    recovery_at = begin
    recovery_count = 0
    recovery_progress = None
    counts = collections.Counter()
    action_no = 0
    end = {'outcome': 'crash', 'reason': 'worker_incomplete'}
    engine = {}
    seen_minetown = False
    recovery_turn = None
    def emit(kind, **kw):
        output.write(json.dumps({'event': kind, 'elapsed': round(time.monotonic()-begin, 3), **kw}, default=str)+'\n')
    inflight = 0
    from .recovery import install
    install(bh, emit)
    original_write = bh.iface.write
    def write(data):
        nonlocal inflight
        inflight += len(data)
        emit('keys', data=data)
        original_write(data)
    bh.iface.write = write
    bh.delegator.set_writer(write)
    def chosen(a):
        nonlocal last_choice, action_no
        last_choice = time.monotonic()
        action_no += 1
        g = bh.game.deref()
        p = g.get('player') or {}
        emit('action', number=action_no, action=typekw(a), reason=a.get('reason'),
             turn=g.get('turn'), dlvl=g.get('dlvl'), x=p.get('x'), y=p.get('y'), hp=p.get('hp'))
    register_handler(bh, PRIORITY_TOP-2, Handler(action_chosen=chosen))
    from .protocol import JSONTail
    events = (run/'engine.jsonl').open('r')
    event_tail = JSONTail(events)
    from .protocol import Decoder
    decoder = Decoder()
    command_pending = False
    injected = False
    suppress_prompt = False
    last_signature = None
    signature_since = begin
    try:
        start(bh)
        (run/'engine.pid').write_text(str(bh.iface.pid))
        while not bh._stop:
            now = time.monotonic()
            for e in event_tail.poll():
                engine = e
                seen_minetown |= bool(e.get('minetown'))
                if recovery_turn is not None and e.get('turn', 0) > recovery_turn:
                    emit('recovery_succeeded', before_turn=recovery_turn, after_turn=e['turn'])
                    recovery_turn = None
                if e['event'] in ('ascended','death','panic','quit','escaped'):
                    assisted = any(os.getenv(k)=='1' for k in ('BH_KIT','BH_HUNGER','BH_INVINCIBLE'))
                    outcome = {'ascended':'assisted_ascension' if assisted else 'ascension',
                               'death':'death','panic':'crash','quit':'quit','escaped':'escaped'}[e['event']]
                    if os.getenv('BH_FIXTURE') and e['event'] == 'ascended':
                        outcome = 'fixture_ascension'
                    end = {'outcome':outcome,'reason':'engine_result','engine_result':e}
                    break
            if end.get('reason') == 'engine_result':
                break
            if milestone == 'minetown' and seen_minetown:
                end = {'outcome':'milestone','reason':'engine_minetown'}
                break
            if now-begin >= seconds or engine.get('turn',0) >= turns:
                end = {'outcome':'resource_limit','reason':'wall_time' if now-begin >= seconds else 'turns'}
                break
            sig = tuple(engine.get(k) for k in ('turn','dnum','dlevel','x','y'))
            if sig != last_signature:
                last_signature, signature_since = sig, now
            # Recovery runs on this reader thread, never races the scraper.
            idle = now-last_choice > 8 or now-signature_since > 12
            if idle and now-recovery_at > 8:
                progress = (engine.get('turn'),engine.get('dnum'),engine.get('dlevel'))
                if progress != recovery_progress:
                    recovery_count = 0
                    recovery_progress = progress
                recovery_count += 1
                recovery_at = now
                emit('recovery', attempt=recovery_count, engine=engine,
                     screen=bh.terminal.screen.display)
                if recovery_count > 3:
                    end = {'outcome':'blocked','reason':'recovery_exhausted'}
                    break
                suppress_prompt = False
                bh.scraper.reset(None)
                bh.delegator.set_inhibition(False)
                bh.delegator.write(chr(27))
                recovery_turn = engine.get('turn', 0)
            if not bh.iface.wait_readable(.1):
                continue
            data = bh.iface.read(256)
            if not data:
                end = {'outcome':'crash','reason':'engine_eof_without_result'}
                break
            bh.ttyrec.write(data)
            for kind, before in decoder.feed(data):
                bh.terminal.feed(before)
                if kind == b'ack':
                    if inflight <= 0:
                        raise RuntimeError("Unsolicited engine key acknowledgement")
                    inflight -= 1
                    continue
                if kind == b'command':
                    command_pending = True
                    continue
                if inflight:
                    command_pending = False
                    continue
                frame = bh.terminal.frame()
                from pybothack.scraper import _more_prompt_p
                if command_pending and _more_prompt_p(frame):
                    # parse() can flush a pending --More-- before reading its
                    # command. The command boundary remains pending after it.
                    bh.delegator.redraw(frame)
                    continue
                if command_pending:
                    command_pending = False
                    if os.getenv('BH_FAULT_PROMPT') == '1' and not injected:
                        injected = True
                        suppress_prompt = True
                        emit('fault_injection', fault='unanswered_direction')
                        bh.delegator.write('o')
                        continue
                    bh.scraper.reset(None)
                    from pybothack.scraper import parse_botls
                    from pybothack.frame import botls, topline
                    msg = topline(frame)
                    if msg:
                        bh.delegator.message(msg)
                    bh.delegator.botl(parse_botls(botls(frame)))
                    bh.delegator.know_position(frame)
                    bh.delegator.full_frame(frame)
                elif not suppress_prompt:
                    bh.delegator.redraw(frame)

    except BaseException as exc:
        emit('exception', error=repr(exc), traceback=traceback.format_exc())
        end = {'outcome':'crash','reason':type(exc).__name__,'error':str(exc)}
        logging.exception('worker failed')
    finally:
        emit('final_screen', screen=bh.terminal.screen.display)
        stop(bh)
        end.update(seed=seed, actions=action_no, elapsed=time.monotonic()-begin,
                   progression={'minetown':seen_minetown,'last_engine':engine})
        (run/'result.json').write_text(json.dumps(end,indent=2)+'\n')
        events.close()
        output.close()
    return end

if __name__ == '__main__':
    print(json.dumps(play(sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]),sys.argv[5])))
