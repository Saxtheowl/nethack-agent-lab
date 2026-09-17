"""Port of bothack.itemtype + the data of bothack.itemdata.

The item table (1722 entries with the defaults of each defitemtype already
merged) comes verbatim from the original Clojure sources.
"""
from ._load import DATA
from .montype import name_to_monster

items = DATA['items']

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
