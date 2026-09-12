"""Port of bothack.item."""
import re

from .clj import assoc, dissoc
from .itemid import (item_id, item_name, item_type, item_subtype, item_weight,
                     initial_ids, appearance_of, knowable_appearance,
                     know_price)
from .itemtype import (name_to_item, item_kinds, jap_to_eng,
                       plural_to_singular)
from .util import parse_int, re_first_group, re_first_groups, re_seq, str_kw

ITEM_FIELDS = [
    'slot', 'qty', 'buc', 'grease', 'poison', 'erosion1', 'erosion2', 'proof',
    'used', 'eaten', 'diluted', 'enchantment', 'name', 'generic', 'specific',
    'recharges', 'charges', 'candles', 'lit-candelabrum', 'lit', 'laid',
    'chained', 'quivered', 'offhand', 'offhand-wielded', 'wielded', 'worn',
    'cost1', 'cost2', 'cost3',
]

ITEM_RE = re.compile(
    r"^(?:([\w\#\$])\s[+-]\s)?\s*([Aa]n?|[Tt]he|\d+)?\s*"
    r"(blessed|(?:un)?cursed|(?:un)?holy)?\s*(greased)?\s*(poisoned)?\s*"
    r"((?:(?:very|thoroughly) )?(?:burnt|rusty))?\s*"
    r"((?:(?:very|thoroughly) )?(?:rotted|corroded))?\s*"
    r"(fixed|(?:fire|rust|corrode)proof)?\s*(partly used)?\s*"
    r"(partly eaten)?\s*(diluted)?\s*([+-]\d+)?\s*(?:(?:pair|set) of)?\s*"
    r"\b(.*?)\s*(?:called (.*?))?\s*(?:named (.*?))?\s*"
    r"(?:\((\d+):(-?\d+)\))?\s*(?:\((no|[1-7]) candles?(, lit| attached)\))?"
    r"\s*(\(lit\))?\s*(\(laid by you\))?\s*(\(chained to you\))?\s*"
    r"(\(in quiver\))?\s*(\(altern.*?\)?)?\s*(\(wielded i.*?\))?\s*"
    r"(\((?:weapo?n?|wield?e?d?).*?\)?)?\s*"
    r"(\((?:bei?n?g?|emb?e?d?d?e?d?|on?).*?\)?)?\s*"
    r"(?:\(unpaid, (\d+) zorkmids?\)|\((\d+) zorkmids?\)|"
    r", no charge(?:, .*)?|, (?:price )?(\d+) zorkmids( each)?(?:, .*)?)?"
    r"\.?\s*$")


def _erosion(s):
    if s and any(w in s for w in ("burnt", "rusty", "rotted", "corroded")):
        if "very" in s:
            return 2
        if "thoroughly" in s:
            return 3
        return 1
    return None


def parse_label(label):
    norm = re.sub(r'(?:the )?(.*) partly eaten corpse$',
                  r'partly eaten \1 corpse', label)
    m = ITEM_RE.match(norm)
    raw = {}
    if m:
        raw = dict(zip(ITEM_FIELDS, m.groups()))
    res = dict(raw)

    buc = re_first_group(r'^potions? of ((?:un)?holy) water$', res.get('name'))
    if buc:
        res['name'] = "potion of water"
        res['buc'] = "blessed" if buc == "holy" else "cursed"

    if res.get('name') is not None:
        res['name'] = re_first_group(r'([^(]*)( \(.*)?$', res['name'])
    if res.get('name') is not None:
        res['name'] = jap_to_eng.get(res['name'], res['name'])
        res['name'] = plural_to_singular.get(res['name'], res['name'])

    # (or (:lit res) (and (:lit-candelabrum res) (.contains ... "lit")))
    if res.get('lit'):
        pass
    elif res.get('lit-candelabrum') is None:
        res['lit'] = None
    else:
        res['lit'] = "lit" in res['lit-candelabrum']
    res['in-use'] = next((res[k] for k in ('wielded', 'worn')
                          if res.get(k) is not None), None)
    res['cost'] = next((res[k] for k in ('cost1', 'cost2', 'cost3')
                        if res.get(k) is not None), None)
    q = res.get('qty')
    res['qty'] = parse_int(q) if (q and re.search(r'[0-9]+', q)) else 1

    if raw.get('candles') is not None:
        res['candles'] = 0 if res['candles'] == "no" else parse_int(
            res['candles'])

    for k in ('buc', 'proof'):
        res[k] = str_kw(res.get(k))

    if (not res.get('buc')
            and (raw.get('charges') is not None
                 or raw.get('enchantment') is not None
                 or res.get('name') == "Amulet of Yendor")):
        res['buc'] = 'uncursed'

    for k in ('cost', 'enchantment', 'charges', 'recharges'):
        if res.get(k):
            res[k] = parse_int(res[k])

    e1, e2 = _erosion(res.get('erosion1')), _erosion(res.get('erosion2'))
    res['erosion'] = max(e1 or 0, e2 or 0)

    for k in ('cost1', 'cost2', 'cost3', 'lit-candelabrum', 'erosion1',
              'erosion2', 'slot'):
        res.pop(k, None)

    out = {'label': label}
    for k, v in res.items():          # (filter (comp some? val) res)
        if v is not None:
            out[k] = v
    return out


def label_to_item(label):
    return parse_label(label)


def slot_item(s, label=None):
    if label is None:
        g = re_first_groups(r'\s*(.)  ?[-+#] (.*)\s*$', s)
        if not g:
            return None
        return (g[0][0], label_to_item(g[1]))
    return (s, label_to_item(label))


# ------------------------------------------------------------- predicates
def safe_buc(item):
    return item.get('buc') in ('uncursed', 'blessed')


def cursed(item):
    return item.get('buc') == 'cursed'


def uncursed(item):
    return item.get('buc') == 'uncursed'


def noncursed(item):
    return item.get('buc') != 'cursed'


def blessed(item):
    return item.get('buc') == 'blessed'


def single(item):
    return item.get('qty') == 1


def corpse(item):
    return bool(re_seq(r' corpses?\b', item['name']))


def corpse_to_monster(item):
    i = name_to_item.get(item['name'])
    return i.get('monster') if i else None


def can_take(item):
    return item.get('cost') is None


def candle(item):
    return "candle" in item['name']


def _kindpred(kind):
    def p(item):
        return item_type(item) == kind
    p.__name__ = kind + '_p'
    return p


food_p = _kindpred('food')
armor_p = _kindpred('armor')
tool_p = _kindpred('tool')
weapon_p = _kindpred('weapon')
wand_p = _kindpred('wand')
ring_p = _kindpred('ring')
amulet_p = _kindpred('amulet')
scroll_p = _kindpred('scroll')
spellbook_p = _kindpred('spellbook')
potion_p = _kindpred('potion')
gem_p = _kindpred('gem')
statue_p = _kindpred('statue')
other_p = _kindpred('other')


def tin(item):
    return food_p(item) and bool(re_seq(r'\btins?\b', item['name']))


def shield(item):
    return item_subtype(item) == 'shield'


def gloves(item):
    return item_subtype(item) == 'gloves'


def boots(item):
    return item_subtype(item) == 'boots'


def container(item):
    return bool(re_seq(r'^bag\b|sack$|chest$|box$', item['name']))


def bag(item):
    return bool(re_seq(r'^bag\b|sack$', item['name']))


def know_contents(item):
    return (not container(item) or item['name'] == "bag of tricks"
            or item.get('items') is not None)


def boh(game_or_item, item=None):
    if item is None:
        return game_or_item['name'] == "bag of holding"
    return item_name(game_or_item, item) == "bag of holding"


def water(item):
    return item['name'] == "potion of water"


def holy_water(item):
    return water(item) and item.get('buc') == 'blessed'


def explorable_container(item):
    return (not know_contents(item) and not item.get('locked')
            and (noncursed(item) or not boh(item)))


CANDELABRUM = "Candelabrum of Invocation"
BELL = "Bell of Opening"
BOOK = "Book of the Dead"


def dagger(item):
    return "dagger" in item['name']


DAGGERS = set(i['name'] for i in item_kinds['weapon'] if dagger(i))


def ammo_p(item):
    return "arrow" in item['name'] or "bolt" in item['name']


def dart(item):
    return "dart" in item['name']


AMMO = set(i['name'] for i in item_kinds['weapon']
           if ammo_p(i) or dart(i))


def short_sword(item):
    return "short sword" in item['name']


def rocks(item):
    return item['name'] == "rock"


def egg(item):
    return bool(re_seq(r'\begg\b', item['name']))


def artifact(item):
    i = name_to_item.get(item.get('specific')) or name_to_item.get(item['name'])
    return bool(i.get('artifact')) if i else False


def nw_ratio(item):
    """Nutrition/weight ratio of item; ((fnil / 0) nutrition weight)."""
    from .itemtype import typekw as _typekw
    i = item_id(item)
    if _typekw(i) != 'food':
        return 0
    n, w = i.get('nutrition'), i.get('weight')
    if n is None:
        n = 0
    if w in (None, 0):
        return 0
    return n / w


def gold(item):
    return item['name'] == "gold piece"


def key_p(item):
    return "key" in item['name']


def price_id(game_or_item, item=None):
    if item is None:
        i = game_or_item
        return (not artifact(i) and not candle(i) and not container(i)
                and knowable_appearance(appearance_of(i))
                and (tool_p(i) or ring_p(i) or scroll_p(i) or wand_p(i)
                     or potion_p(i) or armor_p(i)))
    return price_id(item) and not know_price(game_or_item, item)


def wished(item):
    return item.get('specific') == "wish"


def safe(game, item):
    return bool(weapon_p(item) or tool_p(item)
                or ((safe_buc(item) or item.get('in-use') or wished(item))
                    and (item_id(game, item) or {}).get('safe')))


def shops_taking(item):
    t = item_type(item)
    res = {'armor': {'armor', 'weapon'}, 'weapon': {'armor', 'weapon'},
           'scroll': {'book'}, 'spellbook': {'book'}, 'amulet': {'gem'},
           'ring': {'gem'}}.get(t, {t})
    return set(res) | {'general'}


def enchantment(item):
    return item.get('enchantment') or 0


def charged(item):
    # (and (not= "empty" (:specific item)) (not ((fnil zero? 1) (:charges item))))
    # - an item with no :charges (a sword, a scroll) counts as charged.
    ch = item.get('charges')
    ch = 1 if ch is None else ch
    return item.get('specific') != "empty" and ch != 0


def recharged(item):
    # (or (= "recharged" (:specific item)) (not ((fnil zero? 0) (:recharges item))))
    rc = item.get('recharges')
    rc = 0 if rc is None else rc
    return item.get('specific') == "recharged" or rc != 0


def pick(item):
    return item['name'] in ("pick-axe", "dwarvish mattock")


def safe_enchant(item):
    if item.get('enchantment') is None:
        return False
    t = item_type(item)
    if t == 'weapon':
        return enchantment(item) < 6
    if t == 'armor':
        return enchantment(item) < 4
    return False


def two_handed(item):
    i = item_id(item)
    return bool(i and i.get('hands') == 2)
