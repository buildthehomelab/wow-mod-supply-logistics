"""Everything mod-supply-logistics adds, in one place: build_data.py writes the server's rows from it
and build_patch.py the client's, so the two can't disagree.

Ids: Forever's own where Forever has the thing (items, quests, creatures, factions, its currency 3402).
Ours: items, spells, spell icons, item displays and extended costs 90740-90759 (the Favor item, the
Alliance copies), creatures and npc_text 9531100-9531199 (the mule, the mounts' looks, the dwarven sign
boards, the menus), creature displays and models 95310-95339 (data/looks.tsv, the art), titles 193-198
(bits 158-163).

Released under the MIT License.
"""

import csv
import os

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

# The npc_text of the item menus (crate, receipt, quill) and of the signpost toy's menu.
TEXT_CRATE, TEXT_RECEIPT, TEXT_QUILL = 9531100, 9531101, 9531102
TEXT_SIGNPOST, TEXT_SIGNPOST_NONE, TEXT_SIGNPOST_NOT_YOURS = 9531103, 9531104, 9531105

# --- Factions --------------------------------------------------------------------------------------

HORDE, ALLIANCE = 2587, 2586
HORDE_RACES, ALLIANCE_RACES = 690, 1101          # orc undead tauren troll blood elf / the rest
FACTIONS = [
    # id, reputation index, own races, other races, parent header, name, description
    (HORDE, 108, HORDE_RACES, ALLIANCE_RACES, 67, "Durotar Supply and Logistics",
     "The Horde's robust supply network fuels its rapid expansion across Kalimdor and beyond."),
    (ALLIANCE, 109, ALLIANCE_RACES, HORDE_RACES, 469, "Azeroth Commerce Authority",
     "The Alliance's merchants keep its armies and cities supplied, from Stormwind to the farthest outpost."),
]
REVERED, HONORED, EXALTED = 6, 5, 7               # ReputationRank

# --- The currency ----------------------------------------------------------------------------------

FAVOR = 90740          # low: the server indexes CurrencyTypes by item id
CURRENCY_ID, CURRENCY_BIT, CURRENCY_CATEGORY = 3402, 33, 4   # Forever's id; category 4 = Classic

# --- Spells ----------------------------------------------------------------------------------------

SPELL_FILL, SPELL_OPEN_WRIT, SPELL_CERTIFY, SPELL_RECEIPT, SPELL_QUILL = 90740, 90741, 90742, 90743, 90744
SPELL_PACK_KODO, SPELL_MINIMULE = 90745, 90747
SPELL_SIGN_FORM, SPELL_SIGNPOSTS = 90748, (90749, 90750)    # the forms; the Orcish and Dwarven toys
LEARN = 55884                                     # the stock "learn this companion or mount" trigger

# The use spells: a dummy on yourself. The module's item scripts do the work and the spell is never
# cast; the client needs it for the tooltip's "Use:" line and to let the item be used at all.
USE_SPELLS = [
    (SPELL_FILL, "Fill Crate", "Fill the crate with one of the bundles on its label, and seal it.", "INV_Crate_04"),
    (SPELL_OPEN_WRIT, "Open Writ", "Tear open the envelope to reveal the writ.", "INV_Misc_Note_02"),
    (SPELL_CERTIFY, "Certification",
     "Permanently unlock this profession's title for all characters on your account. Characters that "
     "wish to display it must have 300 skill in the profession.", "INV_Scroll_05"),
    (SPELL_RECEIPT, "Forged Delivery Receipt",
     "Slap a forged delivery receipt onto a Waylaid Crate you can't fill, so you can return it to your "
     "faction's trade representative for 50 reputation.", "INV_Misc_Note_01"),
    (SPELL_QUILL, "Rewrite Writ", "Rewrite an undesired Craftsman's Writ, resulting in a random writ from the same tier.",
     "INV_Feather_04"),
]
# (spell, template, creature the effect summons or mounts, name, description, spell icon template)
MOUNT_SPELLS = [
    (SPELL_PACK_KODO, 23249, 9531102, "Pack Kodo", "Summons and dismisses a rideable pack kodo. This is a very fast mount.", 23249),
]
PET_SPELLS = [
    (SPELL_MINIMULE, 28739, 9531100, "Minimule", "Right Click to summon and dismiss your Minimule.", 28739),
]
SKILL_MOUNTS, SKILL_COMPANIONS = 777, 778

# Spell icons the client lacks, as SpellIcon.dbc rows: (id, the icon's name under Interface\\Icons).
SPELL_ICONS = [(90748, "INV_Letter_03"), (90749, "Trade_Archaeology_Orc_BloodText")]
# The Advertising License's forms: a 10 second cast (SpellCastTimes 7, Forever's) that turns the pile
# of forms into the completed ones. Copies Attach Medallion to Shaft, a plain create-item cast.
FORM_TEMPLATE, FORM_CAST_TIME = 9594, 7
# The signpost toys: summon the post in front of you for a minute (SpellDuration 3), a 1 second cast
# (SpellCastTimes 4), 30 minutes' cooldown, as Forever's. SummonProperties 64 is a plain timed summon,
# owned by whoever cast it; the spell's radius (SpellRadius 7, 2 yards) is how far in front.
SIGNPOST_CAST_TIME, SIGNPOST_DURATION, SIGNPOST_RADIUS, SIGNPOST_COOLDOWN = 4, 3, 7, 1800000
SUMMON_WILD, TARGET_DEST_CASTER_FRONT = 64, 47

# --- Prices ----------------------------------------------------------------------------------------

# ItemExtendedCost id -> Favor. Forever's prices, the recipes' (for later) included.
COSTS = {90740 + i: favor for i, favor in enumerate(
    [15, 30, 45, 60, 90, 120, 180, 200, 240, 270, 360, 1000, 1200, 1500, 6000])}
COST_ID = {favor: cost_id for cost_id, favor in COSTS.items()}

# --- Titles ----------------------------------------------------------------------------------------

# (title id, title bit, item, skill, text): Forever's Certifications, unlocked for the account.
TITLES = [
    (193, 158, 271621, 171, "%s the Alchemist"),
    (194, 159, 271622, 164, "%s the Blacksmith"),
    (195, 160, 271624, 333, "%s the Enchanter"),
    (196, 161, 271625, 202, "%s the Engineer"),
    (197, 162, 271626, 165, "%s the Leatherworker"),
    (198, 163, 271627, 197, "%s the Tailor"),
]
PROFESSION_NAMES = {171: "Alchemy", 164: "Blacksmithing", 333: "Enchanting", 202: "Engineering", 165: "Leatherworking",
                    197: "Tailoring"}

# --- NPCs (Forever's entries; the camps' own SQL spawns them) --------------------------------------

NPC = {
    "intake": (256386, 256390),           # Dokimi / Marcy Baker, Inventory Intake: the Sealed crates
    "coordinator": (256388, 256391),      # Jornah / Elaine Compton, Contract Coordinator: the writs
    "officer": (256384, 256389),          # Gishah / Tamelyn Aldridge, Supply Officer
    "handler": (256400, 256736),          # Okamache, Kodo Handler / Huey Sunnydale, Mule Handler
    "scribe": (256672, 256742),           # Kurvelk Shadowhoof / Dianne Softstep, Uncertified Scribe
    "chef": (248198, 256731),             # Aza'bek / Kalsey Sanden
}
# Profession vendors, Horde then Alliance, by skill: they sell the Certification (and later the recipes).
PROFESSION_VENDORS = {171: (248196, 256729), 164: (248197, 256730), 333: (248199, 256732), 202: (248200, 256733),
                      165: (248201, 256734), 197: (248202, 256735)}
# The chef's goods are stock items for coin, as Forever's (its Thick Logs are left out: no such item).
CHEF_GOODS = [159, 2678, 2692, 3713, 4470, 4471, 4536, 10284, 11291]

# --- Crates ----------------------------------------------------------------------------------------

# Crate kinds as the module's table stores them; the C++ (CrateKind) has the same numbers.
KINDS = {"herbs": 1, "ore": 2, "textiles": 3, "curiosities": 4, "fabrics": 5, "ingots": 6, "parts": 7}
TIER_NAMES = {1: "Apprentice", 2: "Journeyman", 3: "Expert", 4: "Artisan", 5: "Elite"}
# Sealed crates: Forever has three sets of five; we use the first for gathered goods and Elite, the
# second for crafted goods. (item, quest): Forever's quests, the third set's are unused.
SEALED = {
    ("gathered", 1): (248765, 91899), ("gathered", 2): (248766, 91900), ("gathered", 3): (248767, 91901),
    ("gathered", 4): (248768, 91902), ("gathered", 5): (248769, 91903),
    ("crafted", 1): (248770, 91904), ("crafted", 2): (248771, 91905), ("crafted", 3): (248772, 91906),
    ("crafted", 4): (248773, 91907),
}
# Favor and reputation per Sealed crate, by tier. Crafted crates pay half again as much.
CRATE_PAY = {1: (20, 150), 2: (35, 250), 3: (60, 400), 4: (90, 600), 5: (200, 1000)}
CRAFTED_BONUS = 1.5
# Writs: Favor by Forever's reputation for the writ (75 / 125 / 200).
WRIT_FAVOR = {75: 20, 125: 35, 200: 50}

SEALED_WRITS = {1: 262887, 2: 262888, 3: 262889, 4: 262890}
# Writs an earlier version added, for items nobody can craft (see fetch_forever.py NOT_CRAFTABLE):
# (quest, writ item). Their rows are still deleted, so a server that ran that version is left clean.
RETIRED_WRITS = [(94265, 264065), (94269, 264069), (94339, 264139)]
RECEIPT, CONTAINER, CRATE_RETURN, RECEIPT_REP = 262902, 262917, 93862, 50
QUILLS = (262896, 90743)                         # Horde, Alliance
REINS = 262766                                     # both sides, as Forever's Mule Handler sells it too
TREATS = (284664, 90742)
MINIMULE = 9531100                                 # creature
PACK_KODO = 9531102                                # creature: the Pack Kodo mount's one look

# --- Tabards and the signpost toy ------------------------------------------------------------------

TABARDS = (262764, 262765)              # Horde, Alliance: Exalted, at the Supply Officer
LICENSES = (270887, 270888)             # Advertising License Application: Honored, at the Supply Officer
LICENSE_QUESTS = (95819, 95816)         # "Sign Me Up!": the application starts it, the Contract Coordinator ends it
FORMS, COMPLETED_FORMS = 270896, 270897
SIGNPOST_TOYS = (270870, 270868)        # Orcish Tradeskill Signpost (Horde), Dwarven (Alliance)
SIGNPOSTS = (262713, 262727)            # creatures: the post a toy puts up for a minute
# The professions a sign can advertise: (skill, Orcish sign, Dwarven sign, the Dwarven sign's board).
# Forever's creatures; the boards are ours (Forever hangs them on the post with a spell visual kit).
SIGNS = [
    (171, 262718, 262728, 9531103),     # Alchemy
    (164, 262720, 262729, 9531104),     # Blacksmithing
    (185, 262721, 262730, 9531105),     # Cooking
    (333, 262722, 262731, 9531106),     # Enchanting
    (202, 262723, 262732, 9531107),     # Engineering
    (165, 262724, 262733, 9531108),     # Leatherworking
    (197, 262725, 262734, 9531109),     # Tailoring
]
SIGN_SECONDS = 1800                     # a chosen sign stands half an hour, as Forever's
# Where Forever hangs a Dwarven board on its post: (forward, left, up) in yards, turned a quarter left.
BOARD_OFFSET, BOARD_TURN = (0.0, 1.0, 0.04), 1.5707964

# Creature displays (data/looks.tsv; tools/build_art.py converts Forever's models into them).
LOOK = {"pack_kodo": 95310, "minimule": 95311, "orc_post": 95313, "dwarf_post": 95321}

# The Pack Mule mount, taken out on 2026-11-05 (Forever has none: the Alliance rides the Pack Kodo too). Its rows are
# still deleted, and build_patch.py takes them out of the client's tables.
RETIRED_MULE_ITEM, RETIRED_MULE_SPELL, RETIRED_MULE_CREATURE = 90741, 90746, 9531101
ORC_SIGN_LOOKS, DWARF_BOARD_LOOKS = 95314, 95322           # then one per SIGNS row, in its order

# Item displays the client lacks: (id, icon, {ItemDisplayInfo texture field: name}, geoset group, sound).
# The tabards' textures are Forever's: torso upper, torso lower, and the belt over the legs.
TU, TL, LU = 18, 19, 20
ITEM_DISPLAYS = [
    (90750, "INV_Tabard_MerchantHordeC60", {TU: "Tabard_MerchantHordeC60_TU", TL: "Tabard_MerchantHordeC60_TL",
                                            LU: "Tabard_MerchantHordeC60_LU"}, 1, 7),
    (90751, "INV_Tabard_MerchantAllianceC60", {TU: "Tabard_MerchantAllianceC60_TU",
                                               TL: "Tabard_MerchantAllianceC60_TL",
                                               LU: "Tabard_MerchantAllianceC60_LU"}, 1, 7),
    (90752, "INV_Misc_NoteScript2a", {}, 0, 0),
    (90753, "INV_Misc_NoteScript2b", {}, 0, 0),
    (90754, "Trade_Archaeology_Orc_BloodText", {}, 0, 0),
    (90755, "INV_Shield_1H_Ironforge_C_01", {}, 0, 0),
]
# Forever's files behind them (file ids in its build 1.60.1.70790), for tools/build_art.py. An icon
# the client already has is left out of the patch.
SECTION_FOLDERS = {TU: "TorsoUpperTexture", TL: "TorsoLowerTexture", LU: "LegUpperTexture"}
ART_TEXTURES = {
    "Tabard_MerchantHordeC60_TU": 7941400, "Tabard_MerchantHordeC60_TL": 7941399,
    "Tabard_MerchantHordeC60_LU": 7941398, "Tabard_MerchantAllianceC60_TU": 7941107,
    "Tabard_MerchantAllianceC60_TL": 7941106, "Tabard_MerchantAllianceC60_LU": 7941105,
}
ART_ICONS = {
    "INV_Tabard_MerchantHordeC60": 7941397, "INV_Tabard_MerchantAllianceC60": 7941108,
    "INV_Misc_NoteScript2a": 1505958, "INV_Misc_NoteScript2b": 1505959,
    "Trade_Archaeology_Orc_BloodText": 441148, "INV_Shield_1H_Ironforge_C_01": 4882765, "INV_Letter_03": 133459,
}


def art_files():
    """{file name in the client: Forever's file id}: the tabards' textures and every icon above."""
    out = {"Item\\TextureComponents\\%s\\%s_U.blp" % (SECTION_FOLDERS[field], name): ART_TEXTURES[name]
           for _id, _icon, textures, _g, _s in ITEM_DISPLAYS for field, name in textures.items()}
    out.update({"Interface\\Icons\\%s.blp" % icon: fd for icon, fd in ART_ICONS.items()})
    return out

# Item display ids (ItemDisplayInfo) whose icon matches Forever's, or the nearest the client has.
DISPLAY = {
    "favor": 13849,                 # racial_dwarf_findtreasure, Forever's own
    "crate": 67129,                 # inv_crate_07
    "sealed_gathered": 11448,       # inv_crate_04 (Forever's inv_crate_08 isn't in the client)
    "sealed_crafted": 57183,        # inv_crate_09
    "sealed_elite": 7918,           # inv_crate_06
    "container": 7914,              # inv_crate_01
    "sealed_writ": 7743,            # inv_misc_note_02
    "writ": 7798,                   # inv_misc_note_01
    "receipt": 58169,               # inv_letter_18
    "quill": 414303,                # inv_icon_feather01a, Forever's
    "certification": 54524,         # inv_scroll_15
    "treat": 21115,                 # inv_misc_food_54
    "reins_kodo": 29447,            # ability_mount_kodo_03
    "tabard_horde": 90750, "tabard_alliance": 90751,
    "license_horde": 90752, "license_alliance": 90753,
    "forms": 3019,                  # inv_letter_03, Forever's
    "toy_orc": 90754, "toy_dwarf": 90755,
}


def read_tsv(name):
    with open(os.path.join(DATA, name), newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def crates():
    rows = read_tsv("crates.tsv")
    for r in rows:
        for k in ("item", "tier", "level"):
            r[k] = int(r[k])
    return rows


def bundles():
    rows = read_tsv("bundles.tsv")
    for r in rows:
        for k in ("crate", "slot", "reagent", "count"):
            r[k] = int(r[k])
    return rows


def writs():
    rows = read_tsv("writs.tsv")
    for r in rows:
        for k in ("quest", "writ", "item", "count", "skill", "skill2", "yellow", "tier", "rep"):
            r[k] = int(r[k])
    return rows


def sealed_pay(group, tier):
    favor, rep = CRATE_PAY[tier]
    if group == "crafted":
        favor, rep = int(favor * CRAFTED_BONUS), int(rep * CRAFTED_BONUS)
    return favor, rep


def items():
    """Every item the module adds, as dicts with the item_template columns it sets."""
    out = []

    def add(entry, name, cls, subclass, display, quality, **kw):
        row = dict(entry=entry, name=name, cls=cls, subclass=subclass, display=display, quality=quality,
                   stackable=1, bonding=0, description="", spell=0, trigger=0, spell2=0, trigger2=0,
                   level=0, skill=0, skill_rank=0, rep_faction=0, rep_rank=0, startquest=0, script="",
                   bag_family=0, flags=0, maxcount=0, material=-1, sell=0, buy=0, inv_type=0, item_level=0, charges=0)
        row.update(kw)
        out.append(row)

    add(FAVOR, "Merchant's Favor", 10, 0, DISPLAY["favor"], 1, stackable=2147483647, bonding=1, bag_family=8192,
        description="Worth a considerable amount of gold, and so used as an interim currency among "
                    "high-traffic merchant organizations.")

    bundle_text = {}
    for b in bundles():
        bundle_text.setdefault(b["crate"], []).append("%d %s" % (b["count"], b["name"]))
    for c in crates():
        add(c["item"], c["name"], 15, 0, DISPLAY["crate"], 2 if c["group"] == "crafted" else 1, stackable=5,
            level=c["level"], spell=SPELL_FILL, script="item_supply_waylaid_crate",
            description="Takes one bundle: " + ", ".join(bundle_text[c["item"]][:-1]) + " or "
                        + bundle_text[c["item"]][-1] + ".")

    for (group, tier), (item, _quest) in sorted(SEALED.items(), key=lambda kv: kv[1]):
        display = DISPLAY["sealed_elite"] if tier == 5 else DISPLAY["sealed_" + group]
        quality = 4 if tier == 5 else (3 if group == "crafted" else 2)
        add(item, "Sealed %s Crate" % TIER_NAMES[tier], 12, 0, display, quality, stackable=5, bonding=1,
            description="Deliver the completed crate to your faction's trade representative.")
    add(CONTAINER, "Notarized Shipping Container", 12, 0, DISPLAY["container"], 1, stackable=5, bonding=1,
        description="An empty crate that should be returned to your faction's local trade representatives "
                    "in the interest of reducing future shipping costs.")

    for tier, item in SEALED_WRITS.items():
        add(item, "Sealed %s's Writ" % TIER_NAMES[tier], 15, 0, DISPLAY["sealed_writ"], 3, stackable=20, level=10,
            spell=SPELL_OPEN_WRIT, script="item_supply_sealed_writ",
            description="A pending crafting order intercepted in transit. The order inside is for a %s craftsman."
                        % TIER_NAMES[tier].lower())
    # A writ is tradable, as Forever's. It is also its quest's first objective, and the core keeps a
    # quest's starting item only when it is a required item with a MaxCount: so one of each at a time.
    for w in writs():
        add(w["writ"], "Craftsman's Writ: " + w["name"], 12, 0, DISPLAY["writ"], 3, startquest=w["quest"], maxcount=1,
            level=10, description="A pending crafting order. Read it to take the order, then bring it and the goods "
                                  "to a Contract Coordinator.")

    add(RECEIPT, "Forged Delivery Receipt", 15, 0, DISPLAY["receipt"], 1, stackable=20, bonding=1,
        spell=SPELL_RECEIPT, script="item_supply_receipt")
    for side, (faction, item) in enumerate(zip((HORDE, ALLIANCE), QUILLS)):
        add(item, "Forger's Quill", 15, 0, DISPLAY["quill"], 1, stackable=20, bonding=1, rep_faction=faction,
            rep_rank=HONORED, spell=SPELL_QUILL, script="item_supply_quill")
    for title_id, _bit, item, skill, text in TITLES:
        add(item, "%s Certification" % PROFESSION_NAMES[skill], 15, 4, DISPLAY["certification"], 2, bonding=1,
            skill=skill, skill_rank=300, spell=SPELL_CERTIFY, script="item_supply_certification",
            description="Unlocks the title \"%s\" for your account." % text.replace("%s ", ""))
    # The mount and the Minimule need no reputation, as Forever's (its items name no faction). Both sides' handlers
    # sell the one Reins of the Pack Kodo; each side's Supply Officer sells its own Packmule Treat.
    add(REINS, "Reins of the Pack Kodo", 15, 5, DISPLAY["reins_kodo"], 4, bonding=1, skill=762, skill_rank=150,
        spell=LEARN, spell2=SPELL_PACK_KODO, trigger2=6, level=40)
    for item in TREATS:
        add(item, "Packmule Treat", 15, 2, DISPLAY["treat"], 2, bonding=1, spell=LEARN, spell2=SPELL_MINIMULE,
            trigger2=6, sell=1250)

    # Forever's tabards: cloth, unique, item level 20.
    for faction, item, name, display in (
            (HORDE, TABARDS[0], "Durotar Supply and Logistics Tabard", DISPLAY["tabard_horde"]),
            (ALLIANCE, TABARDS[1], "Azeroth Commerce Authority Tabard", DISPLAY["tabard_alliance"])):
        add(item, name, 4, 0, display, 1, bonding=1, rep_faction=faction, rep_rank=EXALTED, maxcount=1,
            inv_type=19, material=7, buy=50000, sell=12500, item_level=20)
    # The Advertising License: the application starts "Sign Me Up!" and is handed in with the completed
    # forms (a required item with a max count, so taking the quest keeps it).
    for faction, item, quest, toy, display in (
            (HORDE, LICENSES[0], LICENSE_QUESTS[0], "Orcish", DISPLAY["license_horde"]),
            (ALLIANCE, LICENSES[1], LICENSE_QUESTS[1], "Dwarven", DISPLAY["license_alliance"])):
        add(item, "Advertising License Application", 15, 4, display, 3, bonding=1, rep_faction=faction,
            rep_rank=HONORED, startquest=quest, maxcount=1,
            description="Contains information and instructions as to how to acquire your very own %s "
                        "Tradeskill Sign toy." % toy)
    add(FORMS, "Massive Pile of Forms", 12, 0, DISPLAY["forms"], 1, bonding=4, maxcount=1, spell=SPELL_SIGN_FORM,
        charges=-1)
    add(COMPLETED_FORMS, "Massive Pile of Completed Forms", 12, 0, DISPLAY["forms"], 1, bonding=4, maxcount=1)
    # The toys: kept in the bags (the client has no toy box), used on a 30 minute cooldown.
    for item, spell, name, display in (
            (SIGNPOST_TOYS[0], SPELL_SIGNPOSTS[0], "Orcish Tradeskill Signpost", DISPLAY["toy_orc"]),
            (SIGNPOST_TOYS[1], SPELL_SIGNPOSTS[1], "Dwarven Tradeskill Signpost", DISPLAY["toy_dwarf"])):
        add(item, name, 15, 0, display, 3, bonding=1, spell=spell, description="Open for business!")
    return out
