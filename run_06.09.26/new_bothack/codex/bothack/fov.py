"""Translation of BotHack's NHFov.java / Sorear FOV, GPL-2.0, 2026-09-06.

Uses the same 22-row output and interior transparency bounds as fov.clj.
"""


def update_fov(game, cursor):
    from .dungeon import curlvl
    from .level import pos
    from .tile import transparent
    grid = [[transparent(tile) for tile in row] for row in curlvl(game)['tiles']]
    return game | {'fov': calculate_fov(pos(cursor), grid)}


def in_fov(game, position):
    from .level import pos
    q = pos(position)
    return bool(game.get('fov') and game['fov'][q.y - 1][q.x])


def visible(game, position, level=None):
    from .dungeon import curlvl, lit
    return ('blind' not in (game['player'].get('state') or ())
            and in_fov(game, position) and lit(game['player'], level or curlvl(game), position))


def calculate_fov(start, transparent):
    x, y = start.x, start.y - 1
    visible = [[False] * 80 for _ in range(22)]

    def sign(value):
        return (value > 0) - (value < 0)

    def clear(dx, dy):
        ax, ay = x + dx, y + dy
        return 0 < ax < 79 and 0 < ay < 20 and bool(transparent[ay][ax])

    def see(dx, dy):
        ax, ay = x + dx, y + dy
        if ax >= 0 and ay >= 0:
            visible[ay][ax] = True

    def qpath(dx, dy):
        point = [0, 0]
        flip = abs(dx) > abs(dy)
        major, minor = (0, 1) if flip else (1, 0)
        dmajor, dminor = (dx, dy) if flip else (dy, dx)
        fminor = -abs(dmajor)
        for _ in range(2, abs(dmajor) + 1):
            fminor += 2 * abs(dminor)
            if fminor >= 0:
                fminor -= 2 * abs(dmajor)
                point[minor] += sign(dminor)
            point[major] += sign(dmajor)
            if not clear(*point):
                return False
        return True

    def quadrant(hs, row, left, right_mark):
        rail = 79 - x if hs == 1 else x
        while left <= right_mark:
            edge = left
            left_clear = clear(hs * left, row)
            while clear(hs * edge, row) == left_clear and (left_clear or edge <= right_mark + 1):
                edge += 1
            edge -= 1
            if left_clear:
                edge += 1
            edge = min(edge, rail)
            if not left_clear:
                if edge > right_mark:
                    edge = right_mark + 1 if clear(hs * right_mark, row - sign(row)) else right_mark
                for i in range(left, edge + 1):
                    see(hs * i, row)
                left = edge + 1
                continue
            if left != 0:
                while left <= edge:
                    if qpath(hs * left, row):
                        break
                    left += 1
                if left >= rail:
                    if left == rail:
                        see(left * hs, row)
                    return
                if left >= edge:
                    left = edge
                    continue
            if right_mark < edge:
                right = right_mark
                while right <= edge:
                    if not qpath(hs * right, row):
                        break
                    right += 1
                right -= 1
            else:
                right = edge
            if left <= right:
                if left == right == 0 and not clear(hs, row) and left != rail:
                    right = 1
                right = min(right, rail)
                for i in range(left, right + 1):
                    see(hs * i, row)
                quadrant(hs, row + sign(row), left, right)
                left = right + 1

    see(0, 0)
    xl, xr = 0, 0
    while True:
        xl -= 1
        see(xl, 0)
        if not clear(xl, 0):
            break
    while True:
        xr += 1
        see(xr, 0)
        if not clear(xr, 0):
            break
    if xr + x == 80:
        xr -= 1
    if xl + x < 0:
        xl += 1
    quadrant(-1, -1, 0, -xl)
    quadrant(1, -1, 0, xr)
    quadrant(-1, 1, 0, -xl)
    quadrant(1, 1, 0, xr)
    return visible
