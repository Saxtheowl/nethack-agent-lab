"""Test cases for the differential test against the original Clojure code."""

ITEM_LABELS = [
    "a blessed +1 long sword (weapon in hand)",
    "an uncursed +0 dwarvish mithril-coat (being worn)",
    "3 uncursed food rations",
    "a scroll labeled READ ME (unpaid, 80 zorkmids)",
    "the partly eaten Lord Surtur's corpse",
    "x - a wand of digging (0:4)",
    "a candelabrum (7 candles attached)",
    "the Candelabrum of Invocation (no candles attached)",
    "2 potions of holy water",
    "a potion of unholy water",
    "an uncursed very rusty thoroughly corroded pick-axe",
    "a blessed greased fixed +3 gray dragon scale mail",
    "5 cursed -2 daggers",
    "a lamp called lamp1",
    "an oil lamp named Bob",
    "a bag called bag2",
    "j - a lock pick (in quiver)",
    "a pair of iron shoes (being worn)",
    "a set of leather gloves (being worn)",
    "a chest (locked)",
    "an empty bag",
    "a large box",
    "17 rocks",
    "a lizard corpse",
    "an egg",
    "2 tins",
    "a wakizashi",
    "a gunyoki",
    "a tanko (being worn)",
    "a scroll labeled ZELGO MER (price 100 zorkmids)",
    "a ruby potion (unpaid, 150 zorkmids)",
    "an octagonal amulet (being worn)",
    "a diluted potion of see invisible",
    "the Amulet of Yendor named REAL",
    "a cheap plastic imitation of the Amulet of Yendor",
    "an uncursed magic marker (0:33)",
    "a +0 elven cloak (being worn)",
    "a partly used wax candle",
    "a brass lantern (lit)",
    "an unlabeled scroll",
    "a corroded orcish dagger (alternate weapon; not wielded)",
    "a silver dragon scale mail (being worn)",
    "2 blessed scrolls of remove curse",
    "a potion of water",
    "a crystal ball named wish",
    "a unicorn horn (weapon in hand)",
    "a food ration, no charge",
    "an apple (2 zorkmids)",
    "a gold piece",
    "42 gold pieces",
    "a boulder",
    "a statue of a gnome lord",
    "a figurine of a jackal",
    "a tripe ration",
    "a c - cursed clear potion",
    "an uncursed towel",
    "a very burnt scroll of magic mapping",
    "a thoroughly rotted leather armor",
    "a wand of wishing (1:3) named recharged",
    "the Excalibur (weapon in hand)",
]

MONSTER_DESCRIPTIONS = [
    "a peaceful dwarf",
    "a dwarf lord",
    "the Wizard of Yendor",
    "a giant eel",
    "Croesus",
    "a coyote - Famishus Vulgarus",
    "a tame little dog",
    "an invisible stalker",
    "a saddled pony",
    "Izchak",
    "a watchman",
    "the high priest",
    "a peaceful Woodland-elf",
    "a gnome called Fred",
    "a mimic or a strange object",
    "the ghost of Bob",
    "a Norn",
    "a guardian naga hatchling",
    "an aligned priest of Odin",
    "a minion of Huhetotl",
    "a large mimic",
    "a soldier ant",
    "a stripling",
    "a gnome lord",
    "Medusa",
    "a peaceful shopkeeper",
    "a black pudding",
    "a Green-elf",
]

ROOM_MESSAGES = [
    "Welcome to Xyzzy's general store!",
    "Welcome again to Izchak's lighting store!",
    "\"Hello Claudebot!  Welcome to Kadirli's delicatessen!\"",
    "Welcome to a hardware store!",
    "Hello Claudebot, welcome to Delphi!\"",
    "Invisible customers are not welcome!",
    "You hear the footsteps of a guard on patrol.",
    "Welcome to Havic's second-hand bookstore!",
    "Welcome to Fenouilledes' used armor dealership!",
]

TRAP_NAMES = [
    "magic portal", "level teleporter", "bear trap", "spiked pit", "web",
    "trap door", "land mine", "anti-magic field", "squeaky board", "hole",
]

STRENGTHS = ["18", "3", "18/01", "18/50", "18/99", "18/**", "6"]

BOTLS = [
    ("Claudebot the Stripling     St:18/03 Dx:11 Co:20 In:8 Wi:8 Ch:7  Lawful S:0     ",
     "Dlvl:1  $:0  HP:18(18) Pw:1(1) AC:6  Exp:1 T:1                                  "),
    ("Claudebot the Skirmisher    St:18/** Dx:14 Co:20 In:8 Wi:9 Ch:7  Lawful S:1234  ",
     "Dlvl:7  $:120  HP:44(56) Pw:5(5) AC:1  Exp:6 T:3050 Hungry Burdened             "),
    ("Bot the Fighter             St:18 Dx:12 Co:18 In:9 Wi:8 Ch:8  Neutral S:99      ",
     "Home 3  $:0  HP:60(60) Pw:12(12) AC:-3  Exp:9 T:9001 Conf Stun                  "),
    ("Bot the Hero                St:18/50 Dx:18 Co:18 In:9 Wi:8 Ch:8  Lawful S:500000",
     "Astral Plane  $:5000  HP:180(200) Pw:40(40) AC:-25  Exp:16 T:60000 Satiated     "),
    ("Bot the Lord                St:18/** Dx:18 Co:18 In:9 Wi:8 Ch:8  Lawful S:12345 ",
     "Fort Ludios  $:0  HP:10(200) Pw:0(40) AC:-25  HD:12 T:60000 FoodPois Ill Blind  "),
    ("Bot the Lady                St:18/** Dx:18 Co:18 In:9 Wi:8 Ch:8  Lawful S:12345 ",
     "End Game  $:0  HP:100(200) Pw:0(40) AC:-25  Xp:14/12345 T:61000 Weak Stressed   "),
]


MONSTER_NAMES = [
    "giant ant", "floating eye", "yellow mold", "black pudding",
    "brown pudding", "shopkeeper", "watchman", "Medusa", "Wizard of Yendor",
    "gnome lord", "dwarf", "soldier ant", "gas spore", "blue jelly",
    "ochre jelly", "spotted jelly", "rust monster", "disenchanter",
    "mind flayer", "master mind flayer", "leprechaun", "nymph",
    "water nymph", "giant eel", "kraken", "electric eel", "cockatrice",
    "chickatrice", "green slime", "Death", "Pestilence", "Famine",
    "Juiblex", "Asmodeus", "Orcus", "Vlad the Impaler", "high priest",
    "aligned priest", "long worm", "purple worm", "titan", "minotaur",
    "werewolf", "wererat", "vampire lord", "zruty", "xan", "gremlin",
    "winged gargoyle", "salamander", "Olog-hai", "grid bug", "newt",
    "lichen", "acid blob", "quivering blob", "gelatinous cube",
    "white unicorn", "large mimic", "small mimic", "giant mimic",
    "Croesus", "Norn", "Lord Surtur", "Ashikaga Takauji", "housecat",
    "kitten", "large dog", "shrieker", "violet fungus", "brown mold",
]


# (current-feature, glyph, color) triples for parse-tile
TILE_CASES = []
_FEATS = ("nil", "rock", "floor", "wall", "corridor", "door-closed",
          "door-open", "door-secret", "pit", "web", "trap", "pool",
          "stairs-down", "stairs-up", "altar", "fountain", "sink",
          "grave", "throne", "ice", "lava", "cloud", "drawbridge-raised")
_GLYPHS = [(".", "nil"), (".", "cyan"), (".", "brown"), ("#", "nil"),
                   ("#", "white"), ("|", "nil"), ("|", "brown"), ("-", "nil"),
                   ("-", "brown"), ("]", "nil"), ("]", "yellow"),
                   ("{", "nil"), ("{", "blue"), ("}", "green"), ("}", "red"),
                   ("}", "cyan"), ("}", "blue"), ("}", "brown"),
                   ("\\", "nil"), ("\\", "yellow"), ("_", "nil"),
                   ("_", "white"), ("~", "nil"), ("~", "brown"), ("^", "nil"),
                   ("<", "nil"), (">", "nil"), ("8", "nil"), ("8", "gray"),
                   ("@", "white"), ("d", "red"), ("I", "nil"), ("%", "nil"),
                   ("$", "yellow"), (")", "nil"), ("[", "nil"), ("*", "nil"),
                   ("`", "nil"), (" ", "nil"), ("m", "nil"), ("F", "yellow")]
for _cur in _FEATS:
    for _g, _c in _GLYPHS:
        TILE_CASES.append("%s,%s,%s" % (_cur, _g, _c))

FOV_MAPS = []
_ROOM = ["#" * 80] + \
    ["#" + "." * 20 + "#" * 59 for _ in range(8)] + \
    ["#" * 80 for _ in range(12)]
FOV_MAPS.append(("10,4", _ROOM))
_CORRIDOR = ["#" * 80 for _ in range(21)]
_CORRIDOR[10] = "#" + "." * 60 + "#" * 19
FOV_MAPS.append(("30,10", _CORRIDOR))
_MAZE = []
for _y in range(21):
    _row = "".join("." if (_x + _y) % 3 else "#" for _x in range(80))
    _MAZE.append(_row)
FOV_MAPS.append(("40,10", _MAZE))
FOV_MAPS.append(("2,2", _MAZE))
FOV_MAPS.append(("77,18", _MAZE))
_PILLARS = []
for _y in range(21):
    _PILLARS.append("".join("#" if (_x % 7 == 0 and _y % 5 == 0) else "."
                            for _x in range(80)))
FOV_MAPS.append(("39,10", _PILLARS))


# ---------------------------------------------------------------- navigation
# maps are 2 chars per cell: glyph + colour letter
# (n=nil r=red g=green b=brown B=blue m=magenta c=cyan G=gray w=white y=yellow)
_C = {'.': 'n', '#': 'n', '|': 'n', '-': 'n', ' ': 'n', '<': 'n', '>': 'n',
      '8': 'n', '^': 'n', '{': 'n', '_': 'n', '`': 'n', '%': 'n', ')': 'n',
      '[': 'n', '*': 'n', '$': 'y', '@': 'w', 'd': 'r', 'F': 'y', ']': 'y',
      '}': 'B', '~': 'n', 'I': 'n', '+': 'n'}


def _enc(rows):
    out = []
    for row in rows:
        row = (row + " " * 80)[:80]
        out.append("".join(ch + _C.get(ch, 'n') for ch in row))
    return ";".join(out)


_ROOM_MAP = [
    "                                                                                ",
    "     -------------------                                                        ",
    "     |.................|                                                        ",
    "     |.....$...........|                                                        ",
    "     |.......@.........|                                                        ",
    "     |.................+#####                                                   ",
    "     |........<........|    #                                                   ",
    "     -------------------    #                                                   ",
    "                            #                                                   ",
    "                            #########                                           ",
    "                                    #                                           ",
    "                     ---------------#--                                         ",
    "                     |.................|                                        ",
    "                     |......>..........|                                        ",
    "                     |.........d.......|                                        ",
    "                     |.................|                                        ",
    "                     -------------------                                        ",
    "                                                                                ",
    "                                                                                ",
    "                                                                                ",
    "                                                                                ",
]

_MAZE_MAP = []
for _y in range(21):
    _r = []
    for _x in range(80):
        if _x in (0, 79) or _y in (0, 20):
            _r.append(" ")
        elif (_x % 2 == 0) and (_y % 2 == 0):
            _r.append("|")
        elif (_x * 7 + _y * 13) % 5 == 0:
            _r.append("|")
        else:
            _r.append("#")
    _MAZE_MAP.append("".join(_r))
_MAZE_MAP[10] = _MAZE_MAP[10][:40] + "<" + _MAZE_MAP[10][41:]
_MAZE_MAP[5] = _MAZE_MAP[5][:20] + ">" + _MAZE_MAP[5][21:]

_SHOP_MAP = [
    "                                                                                ",
    "        ------------                                                            ",
    "        |..........|                                                            ",
    "        |...%%%....|                                                            ",
    "        |...@......]                                                            ",
    "        |..........|                                                            ",
    "        ------------                                                            ",
    "                                                                                ",
    "               ^     8    {    _    `    )    [                                 ",
    "                                                                                ",
    "     ---------------------                                                      ",
    "     |...................|                                                      ",
    "     |........>..........|                                                      ",
    "     |...................|                                                      ",
    "     ---------------------                                                      ",
    "                                                                                ",
    "                                                                                ",
    "                                                                                ",
    "                                                                                ",
    "                                                                                ",
    "                                                                                ",
]

NAV_CASES = []
for _pos, _rows in (("13,4", _ROOM_MAP), ("40,10", _MAZE_MAP),
                    ("12,4", _SHOP_MAP)):
    for _goal in ("stairs-down", "stairs-up", "explorable", "door", "unwalked",
                  "items"):
        for _opts in ("", "walking", "explored", "no-fight,no-autonav",
                      "adjacent", "prefer-items", "no-dig,no-kick"):
            NAV_CASES.append("%s|%s|%s|%s" % (_pos, _opts, _goal, _enc(_rows)))
for _pos, _goal, _rows in (("13,4", "30,13", _ROOM_MAP),
                           ("40,10", "20,5", _MAZE_MAP),
                           ("12,4", "9,12", _SHOP_MAP),
                           ("13,4", "60,3", _ROOM_MAP)):
    for _opts in ("", "walking", "adjacent", "explored"):
        NAV_CASES.append("%s|%s|%s|%s" % (_pos, _opts, _goal, _enc(_rows)))


# ------------------------------------------------- inventory / item strategy
_STARTING = "a:a +1 long sword (weapon in hand);b:a +0 dagger;" \
            "c:a +3 small shield (being worn);d:4 food rations"
_CANDIDATES = ("10 rocks;a +0 dagger;3 food rations;a gold piece;"
               "a scroll labeled TEMOV;an octagonal amulet;"
               "a rusty orcish dagger;12 darts;a pick-axe;"
               "an oil lamp;a chest;a large box;a wand of digging (0:4);"
               "a ruby potion;a lizard corpse;an unlabeled scroll;"
               "a cursed -1 long sword;a blessed +2 long sword;"
               "an uncursed skeleton key;7 wax candles;2 wax candles;"
               "a magic marker (0:22);a tin;an apple;a food ration;"
               "a cockatrice corpse;a newt corpse;a boulder;"
               "a +0 elven mithril-coat;a dwarvish iron helm")

INVENTORY_CASES = [
    _STARTING + "||" + _CANDIDATES,
    _STARTING + ";u:7 rocks||" + _CANDIDATES,
    _STARTING + ";u:17 rocks;e:5 daggers||" + _CANDIDATES,
    "a:a +1 long sword (weapon in hand);d:1 food ration||" + _CANDIDATES,
    ("a:a +1 long sword (weapon in hand);b:a pick-axe;"
     "c:a +3 small shield (being worn);d:12 food rations;"
     "e:a skeleton key;f:an oil lamp||" + _CANDIDATES),
    ("a:the Excalibur (weapon in hand);"
     "b:a blessed +3 gray dragon scale mail (being worn);"
     "c:a shield of reflection (being worn);d:4 food rations;"
     "e:a bag of holding;f:5 scrolls of identify||" + _CANDIDATES),
]


# ------------------------------------------------------------------- combat
_FIGHT_MAP = [
    "                                                                                ",
    "     -------------------                                                        ",
    "     |.................|                                                        ",
    "     |.................|                                                        ",
    "     |.................|                                                        ",
    "     |.................+#####                                                   ",
    "     |........<........|    #                                                   ",
    "     -------------------    #                                                   ",
    "                            #                                                   ",
    "                            #########                                           ",
    "                                    #                                           ",
    "                     ---------------#--                                         ",
    "                     |.................|                                        ",
    "                     |......>..........|                                        ",
    "                     |.................|                                        ",
    "                     |.................|                                        ",
    "                     -------------------                                        ",
    "                                                                                ",
    "                                                                                ",
    "                                                                                ",
    "                                                                                ",
]
_CORRIDOR_MAP = [
    "                                                                                ",
    "     -------------------                                                        ",
    "     |.................|                                                        ",
    "     |.................|                                                        ",
    "     |.................+####################                                    ",
    "     |.................|                   #                                    ",
    "     |........<........|                   #                                    ",
    "     -------------------                   #                                    ",
    "                                           #                                    ",
    "                                           #                                    ",
    "                                        ---+---                                 ",
    "                                        |.....|                                 ",
    "                                        |..>..|                                 ",
    "                                        |.....|                                 ",
    "                                        -------                                 ",
    "                                                                                ",
    "                                                                                ",
    "                                                                                ",
    "                                                                                ",
    "                                                                                ",
    "                                                                                ",
]

_INV_BASIC = ("a:a +1 long sword (weapon in hand);b:a +0 dagger;"
              "c:a +3 small shield (being worn);d:4 food rations")
_INV_RICH = ("a:a +1 long sword (weapon in hand);b:a pick-axe;"
             "c:a +3 small shield (being worn);d:2 food rations;"
             "e:a skeleton key;f:an oil lamp;g:a scroll labeled TEMOV;"
             "h:a ruby potion;i:an octagonal amulet;j:3 daggers;"
             "k:a cursed -1 orcish helm;l:a wand of digging (0:4);"
             "m:a large box;n:12 rocks")
_INV_HURT = ("a:a cursed -1 long sword (weapon in hand);"
             "b:a +0 dwarvish iron helm (being worn);d:1 food ration;"
             "e:a unicorn horn;f:2 scrolls of remove curse;"
             "g:a potion of healing")

COMBAT_CASES = []
for _pos, _hp, _mons, _rows in (
        ("13,4", "40/40/6", "14,4,sewer rat", _FIGHT_MAP),
        ("13,4", "8/40/6", "14,4,sewer rat", _FIGHT_MAP),
        ("13,4", "8/40/6", "14,4,sewer rat;12,4,jackal;13,5,giant bat",
         _FIGHT_MAP),
        ("13,4", "40/40/6", "14,4,sewer rat;12,4,jackal;13,5,giant bat;"
         "14,5,coyote", _FIGHT_MAP),
        ("13,4", "40/40/6", "14,4,floating eye", _FIGHT_MAP),
        ("13,4", "40/40/6", "14,4,yellow mold", _FIGHT_MAP),
        ("13,4", "40/40/6", "14,4,blue jelly", _FIGHT_MAP),
        ("13,4", "40/40/6", "14,4,leprechaun", _FIGHT_MAP),
        ("13,4", "40/40/6", "14,4,nymph", _FIGHT_MAP),
        ("13,4", "40/40/6", "14,4,shopkeeper", _FIGHT_MAP),
        ("13,4", "40/40/6", "16,4,sewer rat", _FIGHT_MAP),
        ("13,4", "40/40/6", "18,4,sewer rat;19,4,jackal", _FIGHT_MAP),
        ("13,4", "12/40/6", "18,4,soldier ant;19,4,soldier ant", _FIGHT_MAP),
        ("13,4", "40/40/6", "14,4,black pudding", _FIGHT_MAP),
        ("13,4", "40/40/6", "14,4,gas spore", _FIGHT_MAP),
        ("13,4", "40/40/6", "14,4,grid bug;12,4,newt", _FIGHT_MAP),
        ("44,9", "40/40/6", "44,8,sewer rat", _CORRIDOR_MAP),
        ("44,9", "9/40/6", "44,8,sewer rat;44,10,jackal", _CORRIDOR_MAP),
        ("44,9", "40/40/6", "", _CORRIDOR_MAP),
        ("13,4", "40/40/6", "", _FIGHT_MAP),
        ("13,4", "5/40/6", "", _FIGHT_MAP),
        ("13,4", "40/40/-14", "14,4,soldier ant;12,4,soldier ant",
         _FIGHT_MAP),
):
    COMBAT_CASES.append("%s|%s|%s|%s|%s"
                        % (_pos, _hp, _mons, _INV_BASIC, _enc(_rows)))
# maps with more than 8 monsters: Clojure promotes the {position => monster}
# map from a PersistentArrayMap to a PersistentHashMap at the 9th entry, and
# the iteration order changes with it
_MANY = ";".join("%d,%d,%s" % (x, y, n) for x, y, n in (
    (8, 2, "sewer rat"), (10, 2, "jackal"), (12, 2, "giant ant"),
    (14, 2, "kobold"), (16, 2, "newt"), (18, 2, "grid bug"),
    (8, 3, "gnome"), (10, 3, "hill orc"), (12, 3, "giant bat"),
    (14, 3, "coyote"), (16, 3, "dwarf"), (18, 3, "homunculus")))
_NINE = ";".join(_MANY.split(";")[:9])
for _n in (_NINE, _MANY):
    for _inv in (_INV_BASIC, _INV_RICH):
        COMBAT_CASES.append("%s|%s|%s|%s|%s"
                            % ("13,4", "40/40/6", _n, _inv, _enc(_FIGHT_MAP)))

for _inv in (_INV_RICH, _INV_HURT):
    for _pos, _hp, _mons, _rows in (
            ("13,4", "40/40/6", "", _FIGHT_MAP),
            ("13,4", "8/40/6", "14,4,sewer rat", _FIGHT_MAP),
            ("13,4", "40/40/6", "14,4,soldier ant;12,4,jackal", _FIGHT_MAP),
            ("44,9", "40/40/6", "", _CORRIDOR_MAP),
            ("13,4", "20/40/-3", "18,4,gnome lord", _FIGHT_MAP)):
        COMBAT_CASES.append("%s|%s|%s|%s|%s"
                            % (_pos, _hp, _mons, _inv, _enc(_rows)))

# make-excal: a fountain on the current level.  `{` is a sink when its colour
# is nil, so the fountain has to be coloured (blue) explicitly.
# row index i of the grid is terminal line y = i + 1
_FOUNTAIN_MAP = list(_FIGHT_MAP)
_FOUNTAIN_MAP[3] = _FOUNTAIN_MAP[3][:13] + "{" + _FOUNTAIN_MAP[3][14:]  # 13,4
_FOUNTAIN_MAP[5] = _FOUNTAIN_MAP[5][:16] + "{" + _FOUNTAIN_MAP[5][17:]  # 16,6


def _enc_fountain(rows):
    return _enc(rows).replace("{n", "{B")


for _inv in (_INV_BASIC, _INV_RICH, _INV_HURT):
    for _pos, _hp, _mons in (
            ("13,4", "40/40/-3", ""),        # standing on the fountain
            ("12,4", "40/40/-3", ""),        # next to it
            ("16,6", "40/40/-3", ""),        # a second fountain at 16,6
            ("13,4", "40/40/6", ""),         # ac too high -> no Excal attempt
            ("13,4", "40/40/-3", "14,4,soldier ant")):
        COMBAT_CASES.append("%s|%s|%s|%s|%s"
                            % (_pos, _hp, _mons, _inv,
                               _enc_fountain(_FOUNTAIN_MAP)))


# ------------------------------------------------------------------- excal
# make-excal / seek-fountain with a *known* Oracle level, which is the only
# way to reach seek-fountain's "navigate to a fountain on this level" branch:
# with no Oracle level in the dungeon the first clause always wins.
EXCAL_CASES = []
for _inv in (_INV_BASIC, _INV_RICH, _INV_HURT):
    for _omode in ("none", "seen", "seen-fountain",
                   "seen-prev-fountain"):
        for _pos, _ac in (("13,4", "-3"),      # standing on a fountain
                          ("12,4", "-3"),      # next to one
                          ("16,6", "-3"),      # standing on the second one
                          ("20,4", "-3"),      # in the room, away from both
                          ("13,4", "6")):      # AC too high, no Excal attempt
            EXCAL_CASES.append("%s|%s|%s|%s|%s"
                               % (_pos, _ac, _inv, _omode,
                                  _enc_fountain(_FOUNTAIN_MAP)))


# ---------------------------------------------------------------------- food
_CORPSES = ";".join(
    "a %s corpse" % n for n in
    ("newt", "wraith", "gnome", "dwarf", "jackal", "sewer rat", "kobold",
     "giant ant", "soldier ant", "floating eye", "gnome lord", "hill orc",
     "black pudding", "brown pudding", "cockatrice", "chickatrice",
     "green slime", "lizard", "yellow mold", "violet fungus", "quantum "
     "mechanic", "stalker", "giant bat", "bat", "little dog", "kitten",
     "werejackal", "wererat", "human", "elf", "giant", "Medusa",
     "leprechaun", "homunculus", "killer bee", "acid blob", "blue jelly",
     "brown mold", "gelatinous cube", "mind flayer", "titanothere",
     "winter wolf", "hell hound", "fire ant", "red mold", "gray ooze",
     "rock mole", "wolf", "warg", "gnome king")
) + ";4 food rations;a tin;an apple;a lizard corpse;a tripe ration;" \
    "a cursed newt corpse;an egg;a lichen corpse"

FOOD_CASES = []
for _race in ("dwarf", "orc", "human"):
    for _intr in ("", "poison", "poison,cold,fire", "cold,stealth"):
        for _str in ("18", "18/03", "18/**", "6"):
            FOOD_CASES.append("%s|%s|%s|%s" % (_race, _intr, _str, _CORPSES))


# --------------------------------------------------------------- menu order
# The bot answers a pick-up/loot menu with a *set* of letters, and the letters
# reach NetHack in the set's iteration order.  Clojure's PersistentHashSet
# iterates in hash order (Character.hashCode is the code point); Python's set
# order depends on the per-process string hash seed, so it must be imposed.
MENU_CASES = [
    "ab", "ba", "abc", "cba", "az", "Aa", "aA", "abcdefgh",
    "hgfedcba", "abcdefghijkl", "zyxwvutsrqpo", "aAbBcC",
    "$abc", "abc$", "0123456789", "acegikmoqsuwy",
    # `take-out-what` answers with strings like "3a" (count + slot), which
    # Clojure hashes as Strings, not Characters
    "1a,2b", "2b,1a", "1a,1b,1c", "12a,3b,1c", "1a,2a,3a",
    "1a,1b,1c,1d,1e,1f,1g,1h,1i,1j,1k,1l",
    "10q,2r,33s,4t", "10a,20b,30c",
]
# Note: a set mixing Characters and Strings is deliberately *not* tested.
# Clojure hashes \a (a Character) as its code point and "a" (a String) with
# murmur3, and the port tells them apart by length - correct for every set the
# bot builds, because `pick-up-what` / `loot-what` yield Characters and
# `take-out-what` yields count+slot Strings, and neither ever mixes the two.


# ---------------------------------------------------------------- map order
# `into {}` goes through a transient array map, which *appends*; a chain of
# persistent `assoc` calls *prepends*.  Same insertion sequence, opposite
# iteration order - and the bot uses both on (:monsters level).
MAPORDER_CASES = []
# `x:y` keys are Positions - the shape the bot actually uses for
# (:monsters level); bare words are Strings.  Single characters are avoided
# deliberately: Clojure would hash those as Characters, and the port tells
# Characters from Strings by length.
_POS9 = ",".join("%d:9" % x for x in range(8, 17))
_POS10 = _POS9 + ",17:9"
_POS12 = _POS10 + ",18:9,19:9"
# inventory slots are Characters, and the inventory map is built with `into`
# in the Inventory handler - so its iteration order (which `have` returns
# first) flips to hash order once the bot carries 9 items
_SLOTS9 = "a,b,c,d,e,f,g,h,i"
_SLOTS12 = _SLOTS9 + ",j,k,l"
for _how in ("into-char", "assoc-char"):
    for _ks in ("a,b", "a,b,c", "$,a,b,c", _SLOTS9, _SLOTS12,
                "a,b,c,d,e,f,g,h", "b,a,d,c"):
        MAPORDER_CASES.append("%s|%s" % (_how, _ks))

for _how in ("into", "assoc"):
    for _ks in ("k1,k2", "k1,k2,k3", "k3,k2,k1", "aa,bb,cc,dd,ee,ff,gg,hh,ii",
                "17:9,19:9", "19:9,17:9", "17:9,18:9,19:9",
                _POS9, _POS10, _POS12):
        MAPORDER_CASES.append("%s|%s" % (_how, _ks))


# ------------------------------------------------------- inventory ordering
# `choose-food` is (min-by nw-ratio …) and min-key keeps the *last* extreme,
# so with two food stacks of equal nutrition/weight the slot the bot eats is
# decided purely by the order (:inventory player) iterates in - which depends
# on how the map was built and on how many items it holds.
_INV_BASE = ("a:a +1 long sword (weapon in hand);b:a +0 dagger;"
             "c:an uncursed +3 small shield (being worn)")
INVORDER_CASES = [
    _INV_BASE + ";d:an uncursed food ration",
    _INV_BASE + ";d:an uncursed food ration;h:3 food rations",
    _INV_BASE + ";h:3 food rations;d:an uncursed food ration",
    "$:12 gold pieces;" + _INV_BASE + ";d:an uncursed food ration;"
    "e:an opera cloak;g:a +1 pair of leather gloves;i:a pair of mud boots;"
    "h:3 food rations",
    _INV_BASE + ";d:an uncursed food ration;e:an opera cloak;"
    "g:a +1 pair of leather gloves;h:3 food rations",
    _INV_BASE + ";d:2 food rations;e:a lizard corpse;f:a tin",
    "$:5 gold pieces;a:a food ration;b:a food ration;c:a food ration",
    _INV_BASE + ";d:an apple;e:a food ration;f:a lichen corpse",
]
