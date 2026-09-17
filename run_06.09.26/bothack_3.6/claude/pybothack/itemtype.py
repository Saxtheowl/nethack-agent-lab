"""Port of bothack.itemtype + the data of bothack.itemdata.

The item table (1722 entries with the defaults of each defitemtype already
merged) comes verbatim from the original Clojure sources.
"""
from ._load import DATA
from .montype import name_to_monster

items = DATA['items']

# objects.c 3.6.7 adds globs (pudding/ooze/slime corpses are globs now).
# Declared as 'other' so that BotHack knows them (it chased the unknown
# "small glob of black pudding" forever) but never considers eating them
# (a glob of green slime would slime the hero).
for _g in ("gray ooze", "brown pudding", "black pudding", "green slime"):
    items.append({'kind': 'other', 'name': "glob of " + _g,
                  'plural': "globs of " + _g, 'glyph': '%', 'price': 6,
                  'weight': 20, 'stackable': False, 'material': 'flesh'})

# objects.c 3.6.7 "novel" (appearance "paperback", xname "paperback book",
# unique appearance): unknown to BotHack, its map glyph was never remembered
# and the shop square stayed "new items" forever (ca-w05 g011).  Declared as
# 'other': reading it is flavour only.
for _n, _pl in (("paperback book", "paperback books"), ("novel", "novels")):
    items.append({'kind': 'other', 'name': _n, 'plural': _pl, 'glyph': '+',
                  'price': 20, 'weight': 1, 'stackable': False,
                  'material': 'paper'})

# ---- NetHack 3.6.7 appearance differences (objects.c), found with
# tools/objects_appearances.py: 16 more random scroll labels, and the
# "leather" spellbook is now "leathery".  Everything else is identical.
SCROLL_LABELS_36 = [
    "ETAOIN SHRDLU", "LOREM IPSUM", "FNORD", "KO BATE", "ABRA KA DABRA",
    "ASHPD SODALG", "ZLORFIK", "GNIK SISI VLE", "HAPAX LEGOMENON",
    "EIRIS SAZUN IDISI", "PHOL ENDE WODAN", "GHOTI", "MAPIRO MAHAMA DIROMAT",
    "VAS CORP BET MANI", "XOR OTA", "STRC PRST SKRZ KRK"]


def _patch_appearances_36():
    extra = ["scroll labeled " + l for l in SCROLL_LABELS_36]
    for lst_name in ('scroll-appearances',):
        lst = DATA[lst_name]
        for a in extra:
            if a not in lst:
                lst.append(a)
    for it in items:
        apps = it.get('appearances')
        if not apps:
            continue
        if "scroll labeled FOOBIE BLETCH" in apps:
            for a in extra:
                if a not in apps:
                    apps.append(a)
        if "leather spellbook" in apps:
            apps[apps.index("leather spellbook")] = "leathery spellbook"
    lst = DATA['spellbook-appearances']
    if "leather spellbook" in lst:
        lst[lst.index("leather spellbook")] = "leathery spellbook"
    order = DATA['appearance-names']
    if "scroll labeled FOOBIE BLETCH" in order:
        for a in extra:
            order.setdefault(a, list(order["scroll labeled FOOBIE BLETCH"]))
    if "leather spellbook" in order:
        order["leathery spellbook"] = order.pop("leather spellbook")
    # the new appearances are exclusive (one object each) like the ones they
    # parallel; otherwise BotHack treated them as shared, #called the type
    # "scroll labeled KO BATE1" and lost track of the object (ca-w06 g008,
    # g009: "scroll called scroll labeled KO BATE1" chased forever)
    # plural forms ("2 scrolls labeled PHOL ENDE WODAN") were missing too:
    # the stack was an unknown item type (full-w01 g001, g004)
    gp = DATA['generic-plurals']
    for a in extra:
        gp.setdefault(a.replace("scroll labeled", "scrolls labeled", 1), a)
    if "leather spellbooks" in gp:
        gp.pop("leather spellbooks")
    gp.setdefault("leathery spellbooks", "leathery spellbook")
    ex = DATA['exclusive-appearances']
    for a in extra:
        ex.add(a)
    if "leather spellbook" in ex:
        ex.discard("leather spellbook")
        ex.add("leathery spellbook")


_patch_appearances_36()

# objects.c 3.6.7: weights of kicking boots and water walking boots swapped
for _it in items:
    if _it.get('name') == 'kicking boots':
        _it['weight'] = 50
    elif _it.get('name') == 'water walking boots':
        _it['weight'] = 15

# The dump stores itemtype :monster as a name; re-link to the MonsterType map.
for _i in items:
    if _i.get('monster') is not None:
        _i['monster'] = name_to_monster(_i['monster'])
# 'kind' is our own addition and must not take part in item-type merging
ITEM_KIND = {}
for _i in items:
    ITEM_KIND[id(_i)] = _i.pop('kind')

item_kinds = {}
for _i in items:
    item_kinds.setdefault(ITEM_KIND[id(_i)], []).append(_i)

name_to_item = {}
for _i in items:
    name_to_item[_i['name']] = _i
for _i in items:
    if _i.get('fullname'):
        name_to_item[_i['fullname']] = _i

blind_plurals = DATA['blind-plurals']
generic_plurals = DATA['generic-plurals']
jap_to_eng = DATA['jap->eng']
exclusive_appearances = DATA['exclusive-appearances']

scroll_appearances = DATA['scroll-appearances']
potion_appearances = DATA['potion-appearances']
amulet_appearances = DATA['amulet-appearances']
spellbook_appearances = DATA['spellbook-appearances']
wands_appearances = DATA['wands-appearances']
ring_appearances = DATA['ring-appearances']
armor_appearances = DATA['armor-appearances']
stone_gems = DATA['stone-gems']
gem_gems = DATA['gem-gems']

plural_to_singular = dict(blind_plurals)
plural_to_singular.update(generic_plurals)
for _i in items:
    if _i.get('plural'):
        plural_to_singular[_i['plural']] = _i['name']


def typekw(itemtype):
    """The item's kind - kept outside the item maps so that they stay
    byte-identical to the original's records (item-id merges by key set)."""
    if not itemtype:
        return None
    return ITEM_KIND.get(id(itemtype), itemtype.get('kind'))


def name_item(name):
    return name_to_item.get(name)


# Record field lists of the defitemtype records - needed to build the "blind
# appearance" pseudo item types with all fields present but nil.
RECORD_FIELDS = {
    'spellbook': ['name', 'glyph', 'price', 'weight', 'level', 'time', 'ink',
                  'skill', 'direction', 'emergency'],
    'amulet': ['name', 'glyph', 'price', 'weight', 'material', 'edible'],
    'weapon': ['name', 'plural', 'glyph', 'price', 'weight', 'sdam', 'ldam',
               'to-hit', 'hands', 'material', 'stackable'],
    'wand': ['name', 'glyph', 'price', 'weight', 'max-charges', 'zaptype'],
    'gem': ['name', 'plural', 'glyph', 'price', 'weight', 'hardness',
            'appearance', 'material', 'stackable'],
    'armor': ['name', 'glyph', 'price', 'weight', 'ac', 'mc', 'material',
              'subtype'],
    'food': ['name', 'plural', 'glyph', 'price', 'weight', 'nutrition',
             'vegan', 'vegetarian', 'material', 'unsafe', 'stackable'],
    'other': ['name', 'plural', 'glyph', 'price', 'weight', 'stackable',
              'material'],
    'tool': ['name', 'plural', 'glyph', 'price', 'weight', 'subtype',
             'material', 'charge', 'stackable'],
    'statue': ['name', 'glyph', 'price', 'weight', 'subtype', 'material',
               'monster'],
    'scroll': ['name', 'plural', 'glyph', 'price', 'weight', 'ink',
               'stackable'],
    'ring': ['name', 'glyph', 'price', 'weight', 'chargeable'],
    'potion': ['name', 'plural', 'glyph', 'price', 'weight', 'material',
               'stackable'],
}


def blank_itemtype(kind, glyph):
    d = {f: None for f in RECORD_FIELDS[kind]}
    d['glyph'] = glyph
    ITEM_KIND[id(d)] = kind
    return d
