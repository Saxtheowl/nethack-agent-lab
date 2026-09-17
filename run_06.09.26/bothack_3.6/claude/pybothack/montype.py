"""Port of bothack.montype - monster type data and lookups.

The monster table itself is the one from the original (extracted verbatim).
"""
import re

from ._load import DATA
from .util import re_first_groups, re_seq

RANGED = {'spit', 'breath', 'gaze'}       # ranged attack types

monster_types = DATA['monster-types']


def _add_missing_36():
    """Monsters of 3.6.7 monst.c absent from the BotHack data (farlook on a
    Kop raised "Failed to parse monster description" and the bot examined
    the same Kop Kaptain forever, ca-w05 g012)."""
    have = {m['name'] for m in monster_types}

    def kop(name, lvl, spd, mr, sides, dices, color, gen, strong):
        tags = {'humanoid', 'human', 'wander', 'hostile', 'male', 'collect',
                'infravisible'}
        if strong:
            tags.add('strong')
        return {'tags': tags, 'color': color, 'ac': 10, 'speed': spd,
                'difficulty': lvl + 2, 'resistances': set(), 'name': name,
                'alignment': mr, 'mr': 10 if lvl < 3 else 20,
                'resistances-conferred': set(), 'size': 'human',
                'weight': 1450, 'glyph': 'K', 'sounds': 'arrest',
                'attacks': [{'type': 'weapon', 'damage-type': 'physical',
                             'dices': dices, 'sides': sides}],
                'nutrition': 200, 'gen-flags': gen}
    extra = [
        kop("Keystone Kop", 1, 6, 9, 4, 1, 'blue',
            {'genocidable', 'lgroup', 'not-generated'}, False),
        kop("Kop Sergeant", 2, 8, 10, 6, 1, 'blue',
            {'genocidable', 'sgroup', 'not-generated'}, True),
        kop("Kop Lieutenant", 3, 10, 11, 8, 1, 'cyan',
            {'genocidable', 'not-generated'}, True),
        kop("Kop Kaptain", 4, 12, 12, 6, 2, 'magenta',
            {'genocidable', 'not-generated'}, True),
    ]
    for base, name, changes in (
            ('Lord Sato', 'Twoflower',
             {'ac': 10, 'mr': 20, 'alignment': 0, 'color': 'white',
              'difficulty': 22,
              'tags_add': {'close'}, 'tags_del': {'approach'}}),
            ('acolyte', 'guide',
             {'color': 'white', 'difficulty': 8,
              'attacks': [{'type': 'weapon', 'damage-type': 'physical',
                           'dices': 1, 'sides': 6},
                          {'type': 'magic', 'damage-type': 'spell',
                           'dices': 0, 'sides': 0}]})):
        src = next((m for m in monster_types if m['name'] == base), None)
        if src is None:
            continue
        m = dict(src, name=name)
        tags = set(src['tags']) | changes.pop('tags_add', set())
        tags -= changes.pop('tags_del', set())
        m['tags'] = tags
        m.update(changes)
        extra.append(m)
    for m in extra:
        if m['name'] not in have:
            monster_types.append(m)


_add_missing_36()
shopkeepers = DATA['shopkeepers']
# NetHack 3.6.7 shknam.c: every shopkeeper name (the 3.4.3 list lacks the
# new ones, e.g. Minetown's "AlliWar Wickson", so farlook could not type them)
SHOPKEEPERS_367 = ['Abisko', 'Abitibi', 'Adjama', 'Akalapi', 'Akhalataki', 'Aklavik', 'Akranes', 'Aksaray', 'Akureyri', 'Alaca', 'AlliWar Wickson', 'Aned', 'Angmagssalik', 'Annootok', 'Ardjawinangun', 'Artvin', 'Asidonhopo', 'Avasaksa', 'Ayancik', 'Azura', 'Babadag', 'Baliga', 'Ballingeary', 'Balya', 'Bandjar', 'Banjoewangi', 'Bayburt', 'Beddgelert', 'Beinn a Ghlo', 'Berbek', 'Berhala', 'Bicaz', 'Birecik', 'Blaze', 'Bnowr Falr', 'Bojolali', 'Bordeyri', 'Boyabai', 'Braemar', 'Breanna', 'Breezy', 'Brienz', 'Brig', 'Brzeg', 'Budereyri', 'Burglen', 'Caergybi', 'Cahersiveen', 'Cannich', 'Carignan', 'Cazelon', 'Changdu', 'Chibougamau', 'Chicoutimi', 'Cire Htims', 'Clonegal', 'Corignac', 'Corsh', 'Cubask', 'Culdaff', 'Curig', 'Dark Eery', 'Demirci', 'Dharma', 'Djasinga', 'Djombang', 'Dobrinishte', 'Donmyar', 'Dorohoi', 'Drepung', 'Droichead Atha', 'Drumnadrochit', 'Dunfanaghy', 'Dunvegan', 'Eauze', 'Echourgnac', 'Eed-morra', 'Eforie', 'Ekim-p', 'Elan Lapinski', 'Elm', 'Enniscorthy', 'Ennistymon', 'Enontekis', 'Enrobwem', 'Ermenak', 'Erreip', 'Ettaw-noj', "Evad'kh", 'Eygurande', 'Eymoutiers', 'Eypau', 'Falo', 'Fauske', 'Feather', 'Fenouilledes', 'Fetesti', 'Feyfer', 'Fleac', 'Flims', 'Flugi', "Ga'er", 'Gairloch', 'Ganden', 'Gaziantep', 'Gellivare', 'Gheel', 'Glenbeigh', 'Gliwice', 'Gomel', 'Gorlowka', 'Guizengeard', 'Gweebarra', 'Gyantse', 'Haparanda', 'Haskovo', 'Havic', 'Haynin', 'Hebiwerie', 'Hoboken', 'Holmavik', 'Hradec Kralove', 'Htargcm', 'Hyeghu', 'Imbyze', 'Inishbofin', 'Inniscrone', 'Inuvik', 'Inverurie', 'Iskenderun', 'Ivrajimsal', 'Jasmine', 'Jiangji', 'Jiu', 'Jonzac', 'Jumilhac', 'Juyn', 'Kabalebo', 'Kachzi Rellim', 'Kadirli', 'Kahztiy', 'Kajaani', 'Kalecik', 'Kanturk', 'Karangkobar', 'Kars', 'Kautekeino', 'Kediri', 'Kerloch', 'Kesh', 'Kilgarvan', 'Kilmihil', 'Kiltamagh', 'Kinnegad', 'Kinojevis', 'Kinsky', 'Kipawa', 'Kirikkale', 'Kirklareli', 'Kittamagh', 'Kivenhoug', 'Klodzko', 'Konosja', 'Kopasker', 'Krnov', 'Kyleakin', 'Kyzyl', 'Labouheyre', 'Laguiolet', 'Lahinch', 'Lapu', 'Lechaim', 'Lerignac', 'Leuk', 'Lexa', 'Lez-tneg', 'Lhasa', 'Linzhi', 'Liorac', 'Lisnaskea', 'Llandrindod', 'Llanerchymedd', 'Llanfair-ym-muallt', 'Llanrwst', 'Llardom', 'Lochnagar', 'Lom', 'Lonzac', 'Lovech', 'Ludus', 'Lugnaquillia', 'Lulea', 'Luna', 'Maesteg', 'Maganasipi', 'Makharadze', 'Makin', 'Malasgirt', 'Malazgirt', 'Mallwyd', 'Mamaia', 'Manlobbi', 'Massis', 'Matagami', 'Matray', 'Melac', 'Melody', 'Midyat', 'Monbazillac', 'Moonjava', 'Morven', 'Moy', 'Mron', 'Mured-oog', 'Nairn', 'Nallihan', 'Narodnaja', 'Nedraawi-nav', 'Nehoiasu', 'Nehpets', 'Nenagh', 'Nenilukah', 'Neuvicq', 'Ngebel', 'Nhoj-lee', 'Nieb', 'Niknar', 'Niod', 'Nisipitu', 'Niskal', 'Nivram', 'Njalindoeng', 'Njezjin', 'Nosalnef', "Nosid-da'r", 'Noskcirdneh', 'Noslo', 'Nosnehpets', 'Oeloe', 'Oguhmk', 'Olycan', 'Oryahovo', 'Ossipewsk', 'Ouiatchouane', 'Pakka Pakka', 'Pameunpeuk', 'Panagyuritshte', 'Papar', 'Parbalingga', 'Pasawahan', 'Patjitan', 'Pemboeang', 'Pengalengan', 'Pernik', 'Pervari', 'Petal', 'Picq', 'Polatli', 'Pons', 'Pontarfynach', 'Possogroenoe', 'Queyssac', 'Raciborz', 'Rastegaisa', 'Rath Luirc', 'Razboieni', 'Rebrol-nek', 'Regien', 'Rellenk', 'Renrut', 'Rewuorb', 'Rhaeader', 'Rhiannon', 'Rhydaman', 'Rikaze', 'Rouffiac', 'Rovaniemi', 'Sablja', 'Sadelin', 'Samoe', 'Sarangan', 'Sarnen', 'Saujon', 'Schuls', 'Semai', 'Senna Hut', 'Sgurr na Ciche', 'Shigatse', 'Siboga', 'Sighisoara', 'Siirt', 'Silistra', 'Sipaliwini', 'Siverek', 'Skibbereen', 'Slanic', 'Sliven', 'Smolyan', 'Sneem', 'Snivek', 'Sperc', 'Starla', 'Stewe', 'Storr', 'Svaving', 'Swidnica', 'Syktywkar', 'Tapper', 'Tefenni', 'Tegal', 'Telloc Cyaj', 'Terwen', 'Thun', 'Tipor', 'Tirebolu', 'Tirgu Neamt', 'Tjibarusa', 'Tjisolok', 'Tjiwidej', 'Tonbar', 'Touverac', 'Trahnil', 'Trallwng', 'Tranquilla', 'Trenggalek', 'Tringanoe', 'Troyan', 'Tsedong', 'Tsew-mot', 'Tsjernigof', 'Tsurphu', 'Tuktoyaktuk', 'Tulovo', 'Turriff', 'Uist', 'Upernavik', 'Urignac', 'Vals', 'Vanzac', 'Varjag Njarga', 'Varvara', 'Vaslui', 'Vergt', 'Voulgezac', 'Walbrzych', 'Weliki Oestjoeg', 'Windsong', 'Wirix', 'Wonotobo', 'Y-Fenni', 'Y-crad', 'Yad', 'Yao-hang', 'Yawolloh', 'Ydna-s', 'Yelpur', 'Yildizeli', 'Yl-rednow', 'Ymla', 'Ypey', 'Yr Wyddgrug', 'Ytnu-haled', 'Zarnesti', 'Zennia', 'Zhangmu', 'Zimnicea', 'Zlatna', 'Zlaw', 'Zoe', 'Zonguldak', 'Zora', 'Zum Loch']
if isinstance(shopkeepers, set):
    shopkeepers.update(SHOPKEEPERS_367)
else:
    shopkeepers = set(shopkeepers) | set(SHOPKEEPERS_367)
role_ranks = DATA['role-ranks']


def passive_type(monster):
    atks = monster.get('attacks') or []
    return all(a.get('type') == 'passive' for a in atks)


def corrosive_type(montype):
    """Corrodes weapon passively when hit?"""
    for a in (montype.get('attacks') or []):
        if a.get('type') == 'passive' and a.get('damage-type') in ('corrode',
                                                                   'acid'):
            return True
    return False


def has_drowning_attack(m):
    if not m:
        return False
    return any(a.get('damage-type') == 'wrap' for a in (m.get('attacks') or []))


# {glyph => {color => MonsterType}}, only unambiguous
def _build_appearance_map():
    m = {}
    for mon in monster_types:
        g = m.setdefault(mon['glyph'], {})
        g[mon['color']] = ':ambiguous' if mon['color'] in g else mon
    res = {}
    for glyph, colors in m.items():
        res[glyph] = {c: mon for c, mon in colors.items()
                      if mon != ':ambiguous'}
    res.setdefault(' ', {})
    res[' '][None] = res.get('X', {}).get(None)
    return res


appearance_to_monster = _build_appearance_map()

_by_name = {}
for _m in monster_types:
    _by_name[_m['name']] = _m
    _by_name[_m['name'].lower()] = _m


def name_to_monster(name):
    if name is None:
        return None
    return _by_name.get(name.lower())


_by_rank = {}
for _role, _ranks in role_ranks.items():
    for _r in _ranks:
        _by_rank[_r] = _role


def rank_to_monster(desc):
    if desc is None:
        return None
    return _by_rank.get(desc.lower())


def _strip_modifier(desc):
    # (condp #(.startsWith ^String %2 %1) desc
    #   "invisible " (subs desc 10)
    #   "saddled " (subs desc 8)
    #   desc)
    #
    # `condp` takes the FIRST matching clause and there is no combined
    # "saddled invisible " case, so a saddled invisible pony loses only the
    # "saddled " and stays "invisible pony".  This port used to carry an extra
    # ("saddled invisible ", 18) entry ahead of these two, which stripped both
    # and left "pony" - a description the original never produces.
    for pre, n in (("invisible ", 10), ("saddled ", 8)):
        if desc.startswith(pre):
            return desc[n:]
    return desc


def _strip_disposition(desc):
    if desc.startswith("tame "):
        return desc[5:]
    if desc.startswith("peaceful "):
        desc = desc[9:]
    # 3.6 minions: "renegade Angel of Loki" (big-w02 g033 farlook loop)
    if desc.startswith("renegade "):
        return desc[9:]
    if desc.startswith("guardian "):
        return desc if " naga" in desc else desc[9:]
    return desc


def _strip_article(desc):
    for pre, n in (("a ", 2), ("an ", 3), ("the ", 4), ("your ", 5)):
        if desc.startswith(pre):
            return desc[n:]
    return desc


def by_description(text):
    """Return MonsterType by farlook description."""
    desc = _strip_modifier(_strip_disposition(_strip_article(text)))
    ghost_or_called = re_seq(r'ghost|called', desc)

    if desc == "tail of a peaceful long worm":
        return name_to_monster("long worm tail")
    if re_seq(r'^(?:the )?high priest(?:ess)?$', desc):
        return name_to_monster("high priest")
    if desc == "mimic":
        return name_to_monster("large mimic")   # could be any mimic really
    if not re_seq(r'Minion of Huhetotl| Yendor', desc) and not ghost_or_called:
        g = re_first_groups(r'(.*) of (.*)', desc)
        if g:
            d2 = g[0]
            if re_seq(r'poohbah|priest|priestess', d2):
                r = (name_to_monster("high priest") if "high " in d2
                     else name_to_monster("aligned priest"))
            elif d2.startswith("guardian "):
                r = name_to_monster(d2[9:])
            else:
                r = name_to_monster(d2)
            if r is None:
                raise ValueError("Failed to parse monster-of description: "
                                 + text)
            return r
    if (not ghost_or_called and "Neferet the Green" not in desc
            and "Vlad the Impaler" not in desc):
        g = re_first_groups(r'(.*) the (.*)', desc)
        if g:
            r = name_to_monster(_strip_modifier(g[1]))
            if r is not None:
                return r
    g = re_first_groups(r'(.*) called (.*)', desc)
    if g:
        r = name_to_monster(g[0])
        if r is not None:
            return r
    if re_seq(r"'?s? ghost", desc):
        r = name_to_monster("ghost")
        if r is not None:
            return r
    if "coyote - " in desc:
        r = name_to_monster("coyote")
        if r is not None:
            return r
    if desc in shopkeepers:
        r = name_to_monster("shopkeeper")
        if r is not None:
            return r
    r = name_to_monster(desc)
    if r is not None:
        return r
    r = rank_to_monster(desc)
    if r is not None:
        return r
    raise ValueError("Failed to parse monster description: " + text)
