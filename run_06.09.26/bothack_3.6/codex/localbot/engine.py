"""Synchronous, byte-acknowledged driver, also used by prepared tests."""
import json
import os
from pathlib import Path
import shutil
import time
from pybothack.iface import ShellInterface, Ttyrec
from pybothack.term import Terminal
from .protocol import Decoder, ProtocolError

ROOT=Path(__file__).resolve().parents[1]
class Engine:
    def __init__(self, directory, *, seed=1, aids=True, fixture=None):
        self.directory=Path(directory).resolve()
        self.directory.mkdir(parents=True,exist_ok=True)
        shutil.copytree(ROOT/'build/game',self.directory/'game')
        self.events=self.directory/'engine.jsonl';self.events.touch()
        env=os.environ.copy()
        env.pop('BH_FIXTURE',None)
        env.update(BH_GAME_DIR=str(self.directory/'game'),BH_EVENTS=str(self.events),BH_SEED=str(seed),
                   BH_KIT=str(int(aids)),BH_HUNGER=str(int(aids)),BH_INVINCIBLE=str(int(aids)))
        if fixture:env['BH_FIXTURE']=fixture
        self.manifest={'seed':seed,'fixture':fixture,'aids':aids,'full_from_start':fixture is None}
        (self.directory/'manifest.json').write_text(json.dumps(self.manifest,indent=2))
        self.iface=ShellInterface(str(ROOT/'scripts/game.sh'),env=env).start()
        self.decoder=Decoder();self.terminal=Terminal();self.pending=0;self.command=False
        self.queue=[];self.tty=Ttyrec(self.directory/'game.ttyrec')
        self.trace=(self.directory/'io.jsonl').open('w',buffering=1)
    def send(self,keys):
        self.pending+=len(keys)
        self.trace.write(json.dumps({'keys':keys})+'\n')
        self.iface.write(keys)
    def next(self,timeout=5):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            while self.queue:
                kind,before=self.queue.pop(0);self.terminal.feed(before)
                if kind==b'ack':
                    if self.pending<=0:raise ProtocolError('Unsolicited key acknowledgement')
                    self.pending-=1;continue
                if kind==b'command':self.command=True;continue
                screen=self.terminal.screen.display
                more=any('--More--' in line for line in screen)
                command=self.command and not more
                if not more:self.command=False
                if self.pending:continue
                observation={'command':command,'screen':screen,'cursor':[self.terminal.screen.cursor.x,self.terminal.screen.cursor.y]}
                self.trace.write(json.dumps(observation)+'\n')
                return observation
            if not self.iface.wait_readable(.05):continue
            data=self.iface.read(65536)
            if not data:return None
            self.tty.write(data);self.queue.extend(self.decoder.feed(data))
        raise TimeoutError('Engine input request timed out')
    def command_ready(self):
        for _ in range(100):
            o=self.next()
            if o is None:return None
            if o['command']:return o
            if any('--More--' in s for s in o['screen']):self.send(' ')
            elif any('(end)' in s or ' of ' in s and s.strip().startswith('(') for s in o['screen']):self.send(' ')
            else:raise ProtocolError('Unexpected prompt: '+o['screen'][0])
        raise ProtocolError('Too many intermediate pages')
    def result(self):
        events=[json.loads(s) for s in self.events.read_text().splitlines()]
        return next((e for e in reversed(events) if e['event'] in ('ascended','death','quit','panic','escaped')),None)
    def close(self):
        self.iface.stop();self.tty.close();self.trace.close()
    def __enter__(self):return self
    def __exit__(self,*exc):self.close()
