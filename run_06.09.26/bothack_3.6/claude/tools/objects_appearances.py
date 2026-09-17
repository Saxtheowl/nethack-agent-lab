"""Random appearances per object class in objects.c (3.4.3 vs 3.6.7)."""
import re
import sys


def calls(path, macro):
    s = open(path).read()
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    out = []
    for m in re.finditer(r'\b%s\(' % macro, s):
        i = m.end()
        depth = 1
        j = i
        while depth and j < len(s):
            if s[j] == '(':
                depth += 1
            elif s[j] == ')':
                depth -= 1
            j += 1
        body = s[i:j - 1]
        if body.strip().startswith('name') or '#define' in s[max(0, m.start()-9):m.start()]:
            continue
        args = [a.strip() for a in re.split(r',(?![^(]*\))', body)]
        out.append(args)
    return out


def appearances(path):
    idx = {'SCROLL': 1, 'POTION': 1, 'RING': 2, 'WAND': 1, 'AMULET': 1,
           'SPELL': 1}
    res = {}
    for macro, k in idx.items():
        vals = []
        for a in calls(path, macro):
            if len(a) > k and a[k].startswith('"'):
                vals.append((a[0].strip('"'), a[k].strip('"')))
        res[macro] = vals
    return res


if __name__ == '__main__':
    a = appearances(sys.argv[1])
    b = appearances(sys.argv[2])
    for m in a:
        da = set(d for _n, d in a[m])
        db = set(d for _n, d in b[m])
        print(m, len(da), len(db), "only-new:", sorted(db - da),
              "only-old:", sorted(da - db))
