"""Faithful rewrite of bothack.frame (BotHack by krajj7).

A Frame is {'lines': [24 strings], 'colors': [24 x 80 color keys], 'cursor': pos}.
"""

# bothack.frame/colormap
colormap = [
    None, "red", "green", "brown", "blue",
    "magenta", "cyan", "gray",
    "bold", "orange", "bright-green", "yellow",
    "bright-blue", "bright-magenta", "bright-cyan", "white",
    "inverse", "inverse-red", "inverse-green", "inverse-brown",
    "inverse-blue", "inverse-magenta", "inverse-cyan", "inverse-gray",
    "inverse-bold", "inverse-orange", "inverse-bright-green", "inverse-yellow",
    "inverse-bright-blue", "inverse-bright-magenta", "inverse-bright-cyan",
    "inverse-white",
]

_inverse_set = {c for c in colormap if c and c.startswith("inverse")}

_non_inverse = {
    "inverse-bright-green": "bright-green", "inverse-green": "green",
    "inverse": None, "inverse-brown": "brown", "inverse-orange": "orange",
    "inverse-magenta": "magenta", "inverse-blue": "blue",
    "inverse-bright-cyan": "bright-cyan", "inverse-cyan": "cyan",
    "inverse-red": "red", "inverse-bold": "white",
    "inverse-bright-magenta": "bright-magenta", "inverse-yellow": "yellow",
    "inverse-bright-blue": "bright-blue", "inverse-gray": "gray",
    "inverse-white": "white",
}


def inverse_color(color):
    return color in _inverse_set


def non_inverse(color):
    return _non_inverse.get(color, color)


def nth_line(frame, n):
    return frame["lines"][n]


def botls(frame):
    return frame["lines"][22:]


def wrapped_cursor(frame):
    return frame["cursor"]["x"] == 0 and frame["cursor"]["y"] > 0


def cursor_line(frame):
    y = frame["cursor"]["y"] - 1 if wrapped_cursor(frame) else frame["cursor"]["y"]
    return frame["lines"][y]


def before_cursor(frame):
    if wrapped_cursor(frame):
        return cursor_line(frame)
    return cursor_line(frame)[:frame["cursor"]["x"]]


def before_cursor_endswith(frame, text):
    return before_cursor(frame).endswith(text)


def topline(frame):
    return frame["lines"][0].strip()


def extra_topline_cursor(frame):
    y = frame["cursor"]["y"]
    return (y == 1
            or (y == 2 and before_cursor_endswith(frame, "--More--"))
            or (y == 2 and topline(frame).startswith("You read:")))


def topline_cursor(frame):
    return frame["cursor"]["y"] == 0 or extra_topline_cursor(frame)


def topline_plus(frame):
    if extra_topline_cursor(frame):
        parts = [topline(frame)]
        if not wrapped_cursor(frame):
            parts.append(" ")
        for i in range(1, frame["cursor"]["y"] + 1):
            parts.append(frame["lines"][i].strip())
        return "".join(parts)
    return topline(frame)


def looks_engulfed(frame):
    cur = frame["cursor"]
    lines = frame["lines"]
    if 0 < cur["x"] < 79 and 1 < cur["y"] < 21:
        rb = cur["x"] - 1
        ra = cur["x"] + 1
        above = lines[cur["y"] - 1]
        at = lines[cur["y"]]
        below = lines[cur["y"] + 1]
        return ((cur["y"] == 1 or (above[rb:ra + 1] == "/-\\"))
                and (re_match(r"\|.\|", at[rb:ra + 1]) is not None)
                and (cur["y"] == 21 or (below[rb:ra + 1] == "\\-/")
                     or (below[rb:ra + 1] == "\\-/")))
    return False


def re_match(pattern, text):
    import re
    return re.search(pattern, text)