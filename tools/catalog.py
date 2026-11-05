"""Everything mod-supply-logistics adds, in one place: build_data.py writes the server's rows from it
and build_patch.py the client's, so the two can't disagree.

Ids: Forever's own where Forever has the thing (items, quests, factions, its currency 3402). Ours:
items, spells and extended costs 90740-90759 (the Favor item and the Alliance copies), creatures and
npc_text 9531100-9531199 (the Minimule, the mule mount, the menus), titles 193-198 (bits 158-163).

Released under the MIT License.
"""

import csv
import os

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

# The npc_text of the item menus (crate, receipt, quill).
TEXT_CRATE, TEXT_RECEIPT, TEXT_QUILL = 9531100, 9531101, 9531102

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
SPELL_PACK_KODO, SPELL_PACK_MULE, SPELL_MINIMULE = 90745, 90746, 90747
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
    (SPELL_PACK_KODO, 23249, 10636, "Pack Kodo", "Summons and dismisses a rideable pack kodo. This is a very fast mount.", 23249),
    (SPELL_PACK_MULE, 23229, 9531101, "Pack Mule", "Summons and dismisses a rideable pack mule. This is a very fast mount.", 23229),
]
PET_SPELLS = [
    (SPELL_MINIMULE, 28739, 9531100, "Minimule", "Right Click to summon and dismiss your Minimule.", 28739),
]
SKILL_MOUNTS, SKILL_COMPANIONS = 777, 778

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
RECEIPT, CONTAINER, CRATE_RETURN, RECEIPT_REP = 262902, 262917, 93862, 50
QUILLS = (262896, 90743)                         # Horde, Alliance
REINS = (262766, 90741)
TREATS = (284664, 90742)
MINIMULE = 9531100                                 # creature
MULE_MOUNT = 9531101                               # creature: the Pack Mule mount's one look

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
    "reins_mule": 13108,            # ability_mount_ridinghorse
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
        for k in ("quest", "writ", "item", "count", "skill", "yellow", "tier", "rep"):
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
                   bag_family=0, flags=0, maxcount=0, material=-1, sell=0)
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
    for w in writs():
        add(w["writ"], "Craftsman's Writ: " + w["name"], 12, 0, DISPLAY["writ"], 3, startquest=w["quest"],
            description="A customer's crafting order. Read it to take the order, then bring the goods to a Contract Coordinator.")

    add(RECEIPT, "Forged Delivery Receipt", 15, 0, DISPLAY["receipt"], 1, stackable=20, bonding=1,
        spell=SPELL_RECEIPT, script="item_supply_receipt")
    for side, (faction, item) in enumerate(zip((HORDE, ALLIANCE), QUILLS)):
        add(item, "Forger's Quill", 15, 0, DISPLAY["quill"], 1, stackable=20, bonding=1, rep_faction=faction,
            rep_rank=HONORED, spell=SPELL_QUILL, script="item_supply_quill")
    for title_id, _bit, item, skill, text in TITLES:
        add(item, "%s Certification" % PROFESSION_NAMES[skill], 15, 4, DISPLAY["certification"], 2, bonding=1,
            skill=skill, skill_rank=300, spell=SPELL_CERTIFY, script="item_supply_certification",
            description="Unlocks the title \"%s\" for your account." % text.replace("%s ", ""))
    for faction, item, spell, name, display in (
            (HORDE, REINS[0], SPELL_PACK_KODO, "Reins of the Pack Kodo", DISPLAY["reins_kodo"]),
            (ALLIANCE, REINS[1], SPELL_PACK_MULE, "Reins of the Pack Mule", DISPLAY["reins_mule"])):
        add(item, name, 15, 5, display, 4, bonding=1, rep_faction=faction, rep_rank=EXALTED, skill=762,
            skill_rank=150, spell=LEARN, spell2=spell, trigger2=6, level=40)
    for faction, item in zip((HORDE, ALLIANCE), TREATS):
        add(item, "Packmule Treat", 15, 2, DISPLAY["treat"], 2, bonding=1, rep_faction=faction, rep_rank=REVERED,
            spell=LEARN, spell2=SPELL_MINIMULE, trigger2=6, sell=1250)
    return out
