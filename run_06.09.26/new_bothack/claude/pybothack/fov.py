"""Port of bothack.fov / NHFov.java (a transcription of Sorear's Perl
implementation of NetHack's FOV)."""
from .clj import assoc
from .tile import transparent


def _cmp(x, y):
    return (x > y) - (x < y)


class NHFov(object):
    def __init__(self, is_transparent):
        self.cbi = is_transparent
        self.visible = None
        self.x = 0
        self.y = 0

    def _clear(self, x, y):
        return self.cbi(self.x + x, self.y + y)

    def _cbo(self, x, y):
        if x >= 0 and y >= 0:
            self.visible[y][x] = True

    def _see(self, x, y):
        self._cbo(self.x + x, self.y + y)

    def _qpath(self, x, y):
        px = [0]
        py = [0]
        flip = abs(x) > abs(y)
        rmaj = px if flip else py
        rmin = py if flip else px
        dmaj = x if flip else y
        dmin = y if flip else x
        fmin = -abs(dmaj)
        for _ in range(2, abs(dmaj) + 1):
            fmin += 2 * abs(dmin)
            if fmin >= 0:
                fmin -= 2 * abs(dmaj)
                rmin[0] += _cmp(dmin, 0)
            rmaj[0] += _cmp(dmaj, 0)
            if not self._clear(px[0], py[0]):
                return False
        return True

    def _quadrant(self, hs, row, left, right_mark):
        rail = (79 - self.x) if hs == 1 else self.x
        while left <= right_mark:
            right_edge = left
            left_clear = self._clear(hs * left, row)
            while (self._clear(hs * right_edge, row) == left_clear
                   and (left_clear or right_edge <= right_mark + 1)):
                right_edge += 1
            right_edge -= 1
            if left_clear:
                right_edge += 1
            if right_edge >= rail:
                right_edge = rail

            if not left_clear:
                if right_edge > right_mark:
                    right_edge = (right_mark + 1
                                  if self._clear(hs * right_mark,
                                                 row - _cmp(row, 0))
                                  else right_mark)
                for i in range(left, right_edge + 1):
                    self._see(hs * i, row)
                left = right_edge + 1
                continue

            if left != 0:
                while left <= right_edge:
                    if self._qpath(hs * left, row):
                        break
                    left += 1
                if left >= rail:
                    if left == rail:
                        self._see(left * hs, row)
                    return
                if left >= right_edge:
                    left = right_edge
                    continue

            if right_mark < right_edge:
                right = right_mark
                while right <= right_edge:
                    if not self._qpath(hs * right, row):
                        break
                    right += 1
                right -= 1
            else:
                right = right_edge

            if left <= right:
                if (left == right and left == 0
                        and not self._clear(hs, row) and left != rail):
                    right = 1
                if right > rail:
                    right = rail
                for i in range(left, right + 1):
                    self._see(hs * i, row)
                self._quadrant(hs, row + _cmp(row, 0), left, right)
                left = right + 1

    def _trace(self):
        xl = 0
        xr = 0
        self._see(0, 0)
        while True:
            xl -= 1
            self._see(xl, 0)
            if not self._clear(xl, 0):
                break
        while True:
            xr += 1
            self._see(xr, 0)
            if not self._clear(xr, 0):
                break
        if xr + self.x == 80:
            xr -= 1
        if xl + self.x < 0:
            xl += 1
        self._quadrant(-1, -1, 0, -xl)
        self._quadrant(+1, -1, 0, xr)
        self._quadrant(-1, +1, 0, -xl)
        self._quadrant(+1, +1, 0, xr)

    def calculate_fov(self, startx, starty):
        self.visible = [[False] * 80 for _ in range(22)]
        self.x = startx
        self.y = starty
        self._trace()
        return self.visible


def update_fov(game, cursor):
    from .dungeon import curlvl
    level = curlvl(game)
    tiles = level['tiles']

    def is_transparent(x, y):
        if 0 < y < 20 and 0 < x < 79:
            return bool(transparent(tiles[y][x]))
        return False

    fov = NHFov(is_transparent).calculate_fov(cursor['x'], cursor['y'] - 1)
    return assoc(game, 'fov', fov)


def in_fov(game, pos):
    fov = game.get('fov')
    if not fov:
        return False
    return fov[pos['y'] - 1][pos['x']]


def visible(game, level_or_pos, pos=None):
    from .dungeon import curlvl, lit
    from .player import blind
    if pos is None:
        level, pos = curlvl(game), level_or_pos
    else:
        level = level_or_pos
    return (not blind(game['player']) and in_fov(game, pos)
            and lit(game['player'], level, pos))
