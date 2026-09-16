#!/usr/bin/env python3
"""Rejouer un ttyrec avec navigation avant ET arriere.

`ttyplay` ne sait pas reculer : il lit le flux dans un seul sens.  Ce lecteur
reconstruit l'ecran avec pyte (deja une dependance du portage) et garde des
images-cles periodiques, ce qui permet de sauter dans les deux sens sans
relire les 115 Mo depuis le debut.

    tools/replay_ascension.py <fichier.ttyrec> [--frame N] [--fin]

Touches :
    ESPACE      lecture / pause
    ->  ou  l   avancer d'une trame            <-  ou  h   reculer d'une trame
    f           avancer de 10 trames           b           reculer de 10
    F           avancer de 100                 B           reculer de 100
    n           avancer de 1000                p           reculer de 1000
    g           debut                          G           fin (l'ascension)
    +  /  -     accelerer / ralentir la lecture
    t           sauter a un tour NetHack (T:...)
    q           quitter
"""
import argparse
import copy
import os
import struct
import sys
import termios
import time
import tty

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pyte                                                    # noqa: E402

KEYFRAME_EVERY = 2000          # images-cles : compromis memoire / vitesse de saut


def load(path):
    """Decoupe le ttyrec en (timestamp, payload) sans tout garder en RAM deux fois."""
    d = open(path, 'rb').read()
    frames, off = [], 0
    while off + 12 <= len(d):
        s, u, l = struct.unpack('<III', d[off:off + 12])
        off += 12
        frames.append((s + u / 1e6, d[off:off + l]))
        off += l
    return frames


class Player(object):
    def __init__(self, frames):
        self.frames = frames
        self.i = 0
        self.speed = 1.0
        self.playing = False
        self.screen = pyte.Screen(80, 24)
        self.stream = pyte.ByteStream(self.screen)
        self.keys = {}             # index -> etat de l'ecran
        self._snapshot(0)

    def _snapshot(self, idx):
        self.keys[idx] = copy.deepcopy(self.screen.buffer)

    def seek(self, target, progress=False):
        """Positionne l'ecran sur la trame `target`, en avant ou en arriere."""
        target = max(0, min(len(self.frames) - 1, target))
        if target >= self.i:
            start = self.i                      # avancer : on continue
        else:
            base = max((k for k in self.keys if k <= target), default=0)
            self.screen.reset()
            self.screen.buffer.clear()
            self.screen.buffer.update(copy.deepcopy(self.keys[base]))
            start = base
        span = target - start
        for j in range(start, target):
            self.stream.feed(self.frames[j][1])
            if (j + 1) % KEYFRAME_EVERY == 0 and (j + 1) not in self.keys:
                self._snapshot(j + 1)
            # un premier parcours complet traite 115 Mo : sans retour visuel
            # l'outil parait fige pendant trois minutes
            if progress and span > 20000 and (j - start) % 20000 == 0:
                sys.stderr.write("\r  positionnement %3.0f%%"
                                 % (100.0 * (j - start) / span))
                sys.stderr.flush()
        if progress and span > 20000:
            sys.stderr.write("\r  positionnement 100%\n")
        self.i = target

    def render(self):
        lines = self.screen.display
        out = ["\x1b[H\x1b[2J"]
        out.extend(lines)
        t0, t1 = self.frames[0][0], self.frames[self.i][0]
        pct = 100.0 * self.i / max(1, len(self.frames) - 1)
        out.append("\x1b[7m trame %d/%d  %5.1f%%  t+%s  vitesse x%g  %s \x1b[0m"
                   % (self.i, len(self.frames) - 1, pct,
                      time.strftime('%H:%M:%S', time.gmtime(t1 - t0)),
                      self.speed, "LECTURE" if self.playing else "PAUSE"))
        out.append("ESPACE play/pause  <-/-> 1  f/b 10  F/B 100  n/p 1000  "
                   "g/G debut/fin  t tour  +/- vitesse  q quitter")
        sys.stdout.write("\r\n".join(out) + "\r\n")
        sys.stdout.flush()

    def find_turn(self, want):
        """Cherche la premiere trame ou la ligne d'etat montre T:>=want."""
        import re
        scr = pyte.Screen(80, 24)
        st = pyte.ByteStream(scr)
        for j, (_, payload) in enumerate(self.frames):
            st.feed(payload)
            if j % 50:
                continue
            m = re.search(r'T:(\d+)', scr.display[23] + scr.display[22])
            if m and int(m.group(1)) >= want:
                return j
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ttyrec')
    ap.add_argument('--frame', type=int, default=0)
    ap.add_argument('--fin', action='store_true', help="commencer a la fin")
    a = ap.parse_args()

    sys.stderr.write("chargement de %s ...\n" % a.ttyrec)
    frames = load(a.ttyrec)
    sys.stderr.write("%d trames\n" % len(frames))
    p = Player(frames)
    # Les dernieres trames sont l'effacement d'ecran de NetHack : viser un peu
    # avant, la ou le texte d'ascension est encore affiche.
    start = max(0, len(frames) - 3000) if a.fin else a.frame
    if start:
        sys.stderr.write("positionnement (premier parcours : ~3 min sur 7 h de jeu)\n")
    p.seek(start, progress=True)

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        p.render()
        while True:
            if p.playing:
                import select
                r, _, _ = select.select([sys.stdin], [], [], 0.02)
                if not r:
                    if p.i < len(frames) - 1:
                        dt = (frames[p.i + 1][0] - frames[p.i][0]) / p.speed
                        time.sleep(min(dt, 0.05))
                        p.seek(p.i + 1)
                        p.render()
                    else:
                        p.playing = False
                    continue
            c = sys.stdin.read(1)
            if c == '\x1b':                       # fleches
                n1 = sys.stdin.read(1)
                c = {'C': 'l', 'D': 'h', 'A': 'F', 'B': 'B'}.get(
                    sys.stdin.read(1), '') if n1 == '[' else ''
            if c == 'q':
                break
            elif c == ' ':
                p.playing = not p.playing
            elif c in 'l':
                p.seek(p.i + 1)
            elif c in 'h':
                p.seek(p.i - 1)
            elif c == 'f':
                p.seek(p.i + 10)
            elif c == 'b':
                p.seek(p.i - 10)
            elif c == 'F':
                p.seek(p.i + 100)
            elif c == 'B':
                p.seek(p.i - 100)
            elif c == 'n':
                p.seek(p.i + 1000)
            elif c == 'p':
                p.seek(p.i - 1000)
            elif c == 'g':
                p.seek(0)
            elif c == 'G':
                p.seek(len(frames) - 1)
            elif c == '+':
                p.speed = min(1000.0, p.speed * 2)
            elif c == '-':
                p.speed = max(0.125, p.speed / 2)
            elif c == 't':
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
                try:
                    want = int(input("\r\naller au tour T: "))
                    j = p.find_turn(want)
                    if j is not None:
                        p.seek(j)
                except (ValueError, EOFError):
                    pass
                tty.setcbreak(fd)
            p.render()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        sys.stdout.write("\x1b[?25h\r\n")


if __name__ == '__main__':
    main()
