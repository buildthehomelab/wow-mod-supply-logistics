"""Everything mod-supply-logistics adds, in one place: build_data.py writes the server's rows from it
and build_patch.py the client's, so the two can't disagree.

Ids: Forever's own where Forever has the thing (items, quests, creatures, factions, its currency 3402).
Ours: items, spells, spell icons, item displays and extended costs 90740-90759 (the Favor item, the
Alliance copies), creatures and npc_text 9531100-9531199 (the mule, the mounts' looks, the dwarven sign
boards, the menus), creature displays and models 95310-95339 (data/looks.tsv, the art), titles 193-198
(bits 158-163),
and for the recipes spells, SkillLineAbility, items and ItemDisplayInfo 91100-91999 (RECIPE_BLOCKS).

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
SPELL_PACK_KODO, SPELL_PACK_MULE, SPELL_MINIMULE = 90745, 90746, 90747
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
    (SPELL_PACK_MULE, 23229, 9531101, "Pack Mule", "Summons and dismisses a rideable pack mule. This is a very fast mount.", 23229),
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
REINS = (262766, 90741)                            # Pack Kodo (both sides, as Forever), Pack Mule (Horde)
TREATS = (284664, 90742)
MINIMULE = 9531100                                 # creature
MULE_MOUNT = 9531101                               # creature: the Pack Mule mount's one look
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
LOOK = {"pack_kodo": 95310, "minimule": 95311, "pack_mule": 95312, "orc_post": 95313, "dwarf_post": 95321}
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
    "reins_mule": 13108,            # ability_mount_ridinghorse
    "tabard_horde": 90750, "tabard_alliance": 90751,
    "license_horde": 90752, "license_alliance": 90753,
    "forms": 3019,                  # inv_letter_03, Forever's
    "toy_orc": 90754, "toy_dwarf": 90755,
}


# --- Recipes ---------------------------------------------------------------------------------------

# data/recipes.tsv (fetch_recipes.py): Forever's recipes the camps sell for Favor, a profession at a
# time. Forever's ids for the recipe and what it makes. Ours, by profession, each in its own block of
# 91100-91999 (spells, SkillLineAbility, items and ItemDisplayInfo count separately): the craft spell
# (also its SkillLineAbility id), the product's use spells, the Alliance copy of a rank-gated recipe,
# and displays for icons the client has no display for. They are stored in recipes.tsv once given
# (assign_ids), so a later fetch never moves them: players' learned spells and bags hold these ids.
RECIPE_BLOCKS = {185: (91100, 50), 171: (91150, 100)}   # Cooking 91100-91149, Alchemy 91150-91249; the rest in PLAN.md
SKILL_ALCHEMY = 171
SKILL_COOKING = 185
RECIPE_SUBCLASS = {185: 5, 171: 6}
# Ids up to here are the client's own items: a recipe whose product is one gets no item row of ours.
STOCK_ITEM_MAX = 56806                 # the 3.3.5a client's last item
# Rank gates. Forever's tables have none on the items (its vendors gate them), and Wowhead shows
# none, so the rank follows the price: a profession's cheapest recipes need nothing, its next tier
# Friendly, the rest Honored.
FRIENDLY = 4
RANK_BY_PRICE_TIER = [0, FRIENDLY, HONORED]
# Stock recipes the camp chefs sell for coin, as Forever's do.
CHEF_RECIPES = [21099, 21219]          # Smoked Sagefish, Sagefish Delight
# Templates in the client's Spell.dbc. Craft spells copy a stock recipe of the profession; drinks copy
# Brain Food's mana half (a plain regen aura plus a periodic trigger into Well Fed: a stock drink's
# own ids are hard-coded in the core, so copying one of those would restore nothing), with the
# duration and amount of the stock drink Forever's triggers.
CRAFT_TEMPLATE = {185: 25704, 171: 17571, 202: 3918}   # Smoked Sagefish (at a fire), Mongoose, Rough Blasting Powder
DRINK_TEMPLATE, WELL_FED_TEMPLATE = 25703, 25694
DRINK_ICON, WELL_FED_ICON = "inv_drink_07", "inv_misc_food_01"     # Forever's (132794, 133943)
STAT_NAMES = {4: "Spirit"}
WELL_FED_GROUP = 1001                  # spell_group: stock Well Fed buffs replace each other
# Alchemy. Elixirs are battle or guardian elixirs, as the stock ones (spell_group 1 and 2: one of
# each at a time): guardian if every effect is health, armor, regeneration, Stamina, Intellect or
# Spirit, battle otherwise (strength, agility, power, healing, crit). They last an hour, as the stock
# ones (user 2026-11-05; Forever's last 30 minutes). Potions and the thrown or drunk specials share
# the stock potion cooldown.
BATTLE_ELIXIR, GUARDIAN_ELIXIR = 1, 2
GUARDIAN_AURAS, GUARDIAN_STATS, AURA_MOD_STAT_ID = {22, 34, 85, 161}, {2, 3, 4}, 29
ELIXIR_DURATION_MS = 3600000
BUFF_TEMPLATE = {BATTLE_ELIXIR: 17538, GUARDIAN_ELIXIR: 11396, "potion": 53908}   # Mongoose, Greater Intellect, Speed
CONE_TEMPLATE = 23461                  # Flame Breath: a hit and a burn in a cone
CLOUD_TEMPLATE = 67594                 # Poison Bottle: a cloud on the ground, its green smoke
ITEM_CATEGORY = {"drink": (59, 1000), "elixir": (79, 3000), "potion": (4, 60000)}
VENOM_SCRIPTS = ("spell_supply_venomous_blood", "spell_supply_venomous_blood_dose")
PROC_FLAG_TAKEN_PERIODIC, PROC_SPELL_TYPE_DAMAGE = 0x80000, 1
# Our spells for a product's use, by kind: a drink and its Well Fed; a buff; Dragonfire's cone; Caustic
# Smog's cloud; Venomous Blood's doses, the dose it spreads and the damage a dose does when it runs out.
USE_SPELL_COUNT = {"drink": 2, "buff": 1, "cone": 1, "cloud": 1, "venom": 3}
# Icons the client already has an icon-only ItemDisplayInfo row for. Any other icon gets a new row
# (a copy of ICON_DISPLAY_TEMPLATE, a drink: its pickup sound suits drinks and potions, pick another
# template for professions whose products aren't liquids). The smoothies' recoloured drinks are in
# every client already: Project Reforged HD's patch-I has them, under Forever's names.
ICON_DISPLAYS = {"inv_scroll_03": 1102, "inv_drink_21": 40652}
ICON_DISPLAY_TEMPLATE = 40652
RECIPE_LEARNING = 483                  # every stock recipe's first spell
DRINK_CATEGORY = 59                    # the stock drinks' shared cooldown
USED_UP = -1                           # spellcharges: the item goes when used, as stock consumables
# Stored once given, like the rank: a recipe someone bought never changes what it needs.
ID_COLUMNS = ["rank", "craft", "use_spells", "alliance_item", "recipe_display", "product_display"]
INT_COLUMNS = ("skill", "recipe", "favor", "learn", "yellow", "grey", "product", "made", "product_class",
               "product_subclass", "item_level", "required_level", "stack", "sell")


def _ints(text):
    return [int(x) for x in text.split()] if text else []


def recipe_ranks(group):
    """{recipe: rank} for one profession's rows: the rank follows the recipe's price tier."""
    prices = sorted({int(r["favor"]) for r in group})
    return {int(r["recipe"]): RANK_BY_PRICE_TIER[min(prices.index(int(r["favor"])), len(RANK_BY_PRICE_TIER) - 1)]
            for r in group}


def gated_both_sides(r):
    return bool(int(r["rank"])) and r["sides"] == "both"


def assign_ids(rows):
    """Gives every row the ids it lacks, from its profession's block, after the ones already used.
    Rows are fetch_recipes.py's (strings); ids already in a row are kept."""
    by_skill = {}
    for r in rows:
        by_skill.setdefault(int(r["skill"]), []).append(r)
    for skill, group in by_skill.items():
        base, size = RECIPE_BLOCKS[skill]
        ranks = recipe_ranks(group)
        for r in group:
            if r.get("rank") in (None, ""):
                r["rank"] = ranks[int(r["recipe"])]
        spells = {x for r in group for x in [int(r.get("craft") or 0)] + _ints(r.get("use_spells", "")) if x}
        items = {int(r["alliance_item"]) for r in group if r.get("alliance_item") not in (None, "", "0")}
        icons = {}
        for r in group:
            for col in ("recipe", "product"):
                if r.get(col + "_display"):
                    icons[r[col + "_icon"]] = int(r[col + "_display"])

        def next_free(used):
            n = max([x for x in used if base <= x < base + size] or [base - 1]) + 1
            if n >= base + size:
                raise ValueError("skill %d outgrew its block %d-%d" % (skill, base, base + size - 1))
            used.add(n)
            return n

        for r in group:                         # craft spells first, then use spells, as first given
            if not r.get("craft"):
                r["craft"] = next_free(spells)
        for r in group:
            want = USE_SPELL_COUNT.get(r["use"].split()[0], 0) if r["use"] else 0
            have = _ints(r.get("use_spells", ""))
            if len(have) != want:
                if have:
                    raise ValueError("recipe %s: its use spells %s don't fit its use %r" % (r["recipe"], have, r["use"]))
                r["use_spells"] = " ".join(str(next_free(spells)) for _ in range(want))
            if gated_both_sides(r) and r.get("alliance_item") in (None, "", "0"):
                r["alliance_item"] = next_free(items)
            r.setdefault("alliance_item", 0)
            r["alliance_item"] = r["alliance_item"] or 0
            for col in ("recipe", "product"):
                icon = r[col + "_icon"]
                if icon not in icons:
                    icons[icon] = ICON_DISPLAYS.get(icon) or next_free(set(icons.values()))
                r[col + "_display"] = icons[icon]
    return rows


def recipes():
    """The recipes with every id the module gives them, in data/recipes.tsv order. Checks the ids;
    gives none (fetch_recipes.py does, through assign_ids)."""
    rows = read_tsv("recipes.tsv")
    by_skill = {}
    for r in rows:
        for k in INT_COLUMNS + ("rank", "craft", "alliance_item", "recipe_display", "product_display"):
            r[k] = int(r[k])
        r["use_spells"] = _ints(r["use_spells"])
        r["use"] = r["use"].split() if r["use"] else []
        r["reagents"] = [tuple(int(x) for x in part.split(":")) for part in r["reagents"].split(",")]
        if len(r["reagents"]) > 8:
            raise ValueError("recipe %d has more than 8 reagents" % r["recipe"])
        if r["recipe"] <= STOCK_ITEM_MAX:
            raise ValueError("recipe %d is a stock item: sell it for coin (CHEF_RECIPES) instead" % r["recipe"])
        by_skill.setdefault(r["skill"], []).append(r)
    seen_spells, seen_items, icon_of = set(), set(), {}
    for skill, group in by_skill.items():
        base, size = RECIPE_BLOCKS[skill]

        def ours(x, what, r):
            if not base <= x < base + size:
                raise ValueError("recipe %d: %s %d is outside skill %d's block" % (r["recipe"], what, x, skill))

        for r in group:
            if r["rank"] not in RANK_BY_PRICE_TIER:
                raise ValueError("recipe %d: rank %d" % (r["recipe"], r["rank"]))
            if r["use"] and r["use"][0] not in USE_SPELL_COUNT:
                raise ValueError("recipe %d: unknown use %r" % (r["recipe"], r["use"]))
            if len(r["use_spells"]) != (USE_SPELL_COUNT[r["use"][0]] if r["use"] else 0):
                raise ValueError("recipe %d: run fetch_recipes.py, its use spells are missing" % r["recipe"])
            for x in [r["craft"]] + r["use_spells"]:
                ours(x, "spell", r)
                if x in seen_spells:
                    raise ValueError("spell %d is given twice" % x)
                seen_spells.add(x)
            if gated_both_sides(r) != bool(r["alliance_item"]):
                raise ValueError("recipe %d: its Alliance copy doesn't match its rank and sides" % r["recipe"])
            if r["alliance_item"]:
                ours(r["alliance_item"], "item", r)
                if r["alliance_item"] in seen_items:
                    raise ValueError("item %d is given twice" % r["alliance_item"])
                seen_items.add(r["alliance_item"])
            for col in ("recipe", "product"):
                icon, display = r[col + "_icon"], r[col + "_display"]
                if icon in ICON_DISPLAYS:
                    if display != ICON_DISPLAYS[icon]:
                        raise ValueError("recipe %d: icon %s isn't display %d" % (r["recipe"], icon, display))
                else:
                    ours(display, "display", r)
                if icon_of.setdefault(display, icon) != icon:
                    raise ValueError("display %d has two icons" % display)
    return rows


def new_displays():
    """(display id, icon, template display) for the ItemDisplayInfo rows the recipes and materials add."""
    seen = {}
    for r in recipes():
        for icon, display in ((r["recipe_icon"], r["recipe_display"]), (r["product_icon"], r["product_display"])):
            if icon not in ICON_DISPLAYS:
                seen[display] = (icon, ICON_DISPLAY_TEMPLATE)
    for m in materials():
        seen[m["display"]] = (m["icon"], MATERIAL_DISPLAY_TEMPLATE[m["cls"], m["subclass"]])
    return sorted((d, icon, template) for d, (icon, template) in seen.items())


# --- Scarce materials ------------------------------------------------------------------------------

# data/materials.tsv (fetch_materials.py): Forever's Scarce materials, bonus drops with gathering and
# skinning (the module's C++ adds them to the loot), and the dyes, acid and sandpaper alchemists and
# engineers learn to make from them at their trainers. Forever's item ids; ours in 91950-91999.
MATERIAL_BLOCK = (91950, 50)
SCARCE_KINDS = {"ore": 1, "herb": 1, "skin": 2}     # mod_supply_logistics_scarce.kind: 1 a node, 2 skinning
# Icon-only displays to copy, by item class and subclass: each carries its kind's pickup sound.
MATERIAL_DISPLAY_TEMPLATE = {(7, 7): 4681, (7, 9): 7396, (7, 6): 7382, (7, 11): 7349, (7, 1): 7137}
# Ore, Herb, Leather, Red Dye's liquid, Rough Blasting Powder's part
# The bags they fit in, as the stock ones of each kind: Mining, Herb, Leatherworking (leather and dyes),
# Engineering.
MATERIAL_BAG_FAMILY = {(7, 7): 1024, (7, 9): 32, (7, 6): 8, (7, 11): 8, (7, 1): 128}


def materials():
    rows = read_tsv("materials.tsv")
    for r in rows:
        for k in ("item", "cls", "subclass", "quality", "item_level", "stack", "sell", "material", "display"):
            r[k] = int(r[k])
        for k in ("skill", "learn", "cost", "yellow", "grey", "craft"):
            r[k] = int(r[k]) if r[k] else 0
        r["chance"] = float(r["chance"]) if r["chance"] else 0.0
        r["sources"] = r["sources"].split(";") if r["sources"] else []
        r["reagents"] = [tuple(int(x) for x in p.split(":")) for p in r["reagents"].split(",")] if r["reagents"] else []
        base, size = MATERIAL_BLOCK
        for x in ([r["craft"]] if r["craft"] else []) + [r["display"]]:
            if not base <= x < base + size:
                raise ValueError("material %d: id %d outside its block" % (r["item"], x))
        if (r["kind"] == "craft") != bool(r["craft"]):
            raise ValueError("material %d: a craft id only for crafted materials" % r["item"])
    return rows


def scarce_sources():
    """(item, kind, node name, min level, max level, chance) for the module's table."""
    out = []
    for m in materials():
        if m["kind"] == "skin":
            for band in m["sources"]:
                low, high = (int(x) for x in band.split("-"))
                out.append((m["item"], SCARCE_KINDS["skin"], "", low, high, m["chance"]))
        elif m["kind"] in SCARCE_KINDS:
            out += [(m["item"], SCARCE_KINDS[m["kind"]], node, 0, 0, m["chance"]) for node in m["sources"]]
    return out


def material_crafts():
    return [m for m in materials() if m["kind"] == "craft"]


def buff_auras(r):
    """(aura, misc, amount) of a buff recipe's product."""
    return [tuple(int(x) for x in a.split(":")) for a in r["use"][3:]]


def elixir_group(r):
    guardian = all(a in GUARDIAN_AURAS or (a == AURA_MOD_STAT_ID and m in GUARDIAN_STATS) for a, m, _n in buff_auras(r))
    return GUARDIAN_ELIXIR if guardian else BATTLE_ELIXIR


def product_kind(r):
    """drink, elixir or potion: what the product's cooldown and stacking follow."""
    if not r["use"]:
        return None
    if r["use"][0] == "drink":
        return "drink"
    if r["use"][0] == "buff" and r["use"][1] == "elixir":
        return "elixir"
    return "potion"


def spell_groups():
    """(spell_group id, spell): Well Fed buffs with the stock Well Fed, elixirs with their kind."""
    out = []
    for r in recipes():
        if r["use"] and r["use"][0] == "drink":
            out.append((WELL_FED_GROUP, r["use_spells"][1]))
        elif product_kind(r) == "elixir":
            out.append((elixir_group(r), r["use_spells"][0]))
    return sorted(out)


def script_names():
    """(spell, ScriptName) for the products the module's C++ drives."""
    out = []
    for r in recipes():
        if r["use"] and r["use"][0] == "venom":
            out += list(zip(r["use_spells"][:2], VENOM_SCRIPTS))
    return sorted(out)


def proc_spells():
    """Venomous Blood's buffs, which proc on bleed ticks taken."""
    return sorted(r["use_spells"][0] for r in recipes() if r["use"] and r["use"][0] == "venom")


def cone_degrees():
    """(spell, degrees) for the cones: Forever's width, not the target type's 24."""
    return sorted((r["use_spells"][0], int(r["use"][7])) for r in recipes() if r["use"] and r["use"][0] == "cone")


def no_bonus_spells():
    """Damage spells that don't grow with spell power (Forever's coefficients are 0)."""
    out = []
    for r in recipes():
        kind = r["use"][0] if r["use"] else None
        if kind in ("cone", "cloud"):
            out.append(r["use_spells"][0])
        elif kind == "venom":
            out.append(r["use_spells"][2])
    return sorted(out)


def recipe_vendor_items(side):
    """(recipe item, Favor) each camp's profession vendor sells, by skill."""
    out = {}
    for r in recipes():
        if r["sides"] not in ("both", ("horde", "alliance")[side]):
            continue
        item = r["alliance_item"] if side == 1 and r["alliance_item"] else r["recipe"]
        out.setdefault(r["skill"], []).append((item, r["favor"]))
    return out


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
                   bag_family=0, flags=0, maxcount=0, material=-1, sell=0, buy=0, inv_type=0, item_level=0, category=0,
                   category_cooldown=-1, charges=0)
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
    # The mounts and the Minimule need no reputation, as Forever's (its items name no faction); each side's
    # handler or Supply Officer sells its own copy.
    for item, spell, name, display in (
            (REINS[0], SPELL_PACK_KODO, "Reins of the Pack Kodo", DISPLAY["reins_kodo"]),
            (REINS[1], SPELL_PACK_MULE, "Reins of the Pack Mule", DISPLAY["reins_mule"])):
        add(item, name, 15, 5, display, 4, bonding=1, skill=762, skill_rank=150, spell=LEARN, spell2=spell,
            trigger2=6, level=40, charges=USED_UP)
    for item in TREATS:
        add(item, "Packmule Treat", 15, 2, DISPLAY["treat"], 2, bonding=1, spell=LEARN, spell2=SPELL_MINIMULE,
            trigger2=6, sell=1250, charges=USED_UP)

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

    # Recipes: learned on use (the stock 483 "Learning" plus the craft spell, as every stock recipe),
    # bound on pickup as Forever's. A gated one needs its side's trade faction at that rank.
    products = set()
    for r in recipes():
        teach = dict(cls=9, subclass=RECIPE_SUBCLASS[r["skill"]], display=r["recipe_display"], quality=1,
                     bonding=1, flags=64, spell=RECIPE_LEARNING, spell2=r["craft"], trigger2=6, skill=r["skill"],
                     skill_rank=r["learn"], item_level=1, description="", charges=USED_UP)
        horde_side = r["sides"] in ("both", "horde")
        add(r["recipe"], r["name"], rep_faction=(HORDE if horde_side else ALLIANCE) if r["rank"] else 0,
            rep_rank=r["rank"], **teach)
        if r["alliance_item"]:
            add(r["alliance_item"], r["name"], rep_faction=ALLIANCE, rep_rank=r["rank"], **teach)
        # The product: one row however many recipes make it; a stock item keeps its own.
        if r["product"] <= STOCK_ITEM_MAX or r["product"] in products:
            continue
        products.add(r["product"])
        product = dict(level=r["required_level"], item_level=r["item_level"], stackable=r["stack"], sell=r["sell"])
        kind = product_kind(r)
        if kind:
            category, cooldown = ITEM_CATEGORY[kind]
            product.update(spell=r["use_spells"][0], category=category, category_cooldown=cooldown,
                           material=7 if kind == "drink" else 3, charges=USED_UP)
        add(r["product"], r["product_name"], r["product_class"], r["product_subclass"], r["product_display"], 1,
            **product)
    # Scarce materials and what's made from them: trade goods, as Forever's.
    for m in materials():
        add(m["item"], m["name"], m["cls"], m["subclass"], m["display"], m["quality"], stackable=m["stack"],
            sell=m["sell"], item_level=m["item_level"], material=m["material"], description=m["description"],
            bag_family=MATERIAL_BAG_FAMILY[m["cls"], m["subclass"]])
    if len({i["entry"] for i in out}) != len(out):
        raise ValueError("an item id is given twice")
    return out
