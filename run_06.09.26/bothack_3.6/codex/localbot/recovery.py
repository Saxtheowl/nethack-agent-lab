"""Progress-based recovery for short navigation cycles."""
from collections import deque
from pybothack.action import typekw
from pybothack.delegator import Handler
from pybothack.handlers import register_handler
from pybothack.util import PRIORITY_TOP
from pybothack.clj import assoc

class CycleDetector:
    def __init__(self, window=64):
        self.window=deque(maxlen=window)
    def observe(self, action, game):
        p=game['player']
        self.window.append((game.get('branch-id'),game.get('dlvl'),p.get('x'),p.get('y'),typekw(action),game.get('turn')))
        if len(self.window)<self.window.maxlen:return False
        cells={x[:4] for x in self.window}
        kinds={x[4] for x in self.window}
        # Do not mistake a fight, long rest, or repeated search for a path cycle.
        cycling=len(cells)<=4 and kinds <= {'move','look','autotravel','farlook'} and 'move' in kinds
        if cycling:self.window.clear()
        return cycling

def install(bh,emit):
    detector=CycleDetector()
    def chosen(action):
        game=bh.game.deref()
        if detector.observe(action,game):
            until=(game.get('turn') or 0)+80
            bh.game.swap(assoc,'recovery-items-until',until,'explore-cache',None)
            emit('cycle_recovery',until=until,position=game['player'],method='temporarily_skip_optional_item_detours')
    register_handler(bh,PRIORITY_TOP-3,Handler(action_chosen=chosen))
