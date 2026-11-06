#!/usr/bin/env python3
"""The client side of mod-supply-logistics: its rows for your realm's spell and item patch, and the
same rows for the server.

    python3 build_patch.py --patch patch-z80-spells-and-items.MPQ --client /path/to/3.3.5a/client \\
        --out new/patch-z80-spells-and-items.MPQ --sql ../data/sql/db-world/mod_supply_logistics_dbc.sql

--patch is the patch that carries your realm's Spell.dbc, SpellIcon.dbc, Item.dbc, ItemDisplayInfo.dbc,
SkillLineAbility.dbc and ItemExtendedCost.dbc. A patch MPQ replaces whole files, so the new rows go into its copies and every
other file is carried over unchanged. Faction.dbc, CharTitles.dbc and CurrencyTypes.dbc come from the
patch when it has them, else from the client's own (--client, its newest enUS locale patch), and the
patch gains them. What gets added (ids in catalog.py):

- Spell.dbc: the use spells of the crates, writs, receipt, quill and Certifications (dummies the
  module's item scripts answer), the Pack Kodo and Pack Mule mounts (from Great Brown Kodo and Swift
  Brown Steed) and the Minimule companion (from Mr. Wiggles). SkillLineAbility.dbc puts the last three
  on the Mounts and Companions lines, so they show in the Companions window. Also Sign Form (signs
  the Advertising License's forms: creates the completed ones) and the two signpost toys' spells
  (summon the post), which the server casts as they are.
- SpellIcon.dbc: the icons of those three, which the client has no row for.
- Item.dbc: every item of the module, so it has its icon everywhere.
- ItemDisplayInfo.dbc: the tabards (Forever's textures), the license applications and the toys.
- Spell.dbc and SkillLineAbility.dbc, for the recipes (data/recipes.tsv): each recipe's craft spell
  on its profession's line, and what its product does when used (a drink and its Well Fed).
- ItemDisplayInfo.dbc, for the recipes: an icon-only display for each recipe icon the client has no
  display for.
- Faction.dbc: Durotar Supply and Logistics (2587, under Horde) and the Azeroth Commerce Authority
  (2586, under Alliance), hidden from the other side's races.
- CharTitles.dbc: the six Certification titles.
- CurrencyTypes.dbc: Merchant's Favor in the Currency tab, under Classic.
- ItemExtendedCost.dbc: the prices in Favor, or the vendor window shows none and won't sell.

--sql writes the server's copy of every one of those rows (spell_dbc, skilllineability_dbc,
faction_dbc, chartitles_dbc, currencytypes_dbc, itemextendedcost_dbc). Running it again on its own
output changes nothing. Needs Python 3 and StormLib (see dbcmpq.py).

Released under the MIT License.
"""

import argparse
import os
import struct
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dbcmpq  # noqa: E402
from dbcmpq import add_string, read_dbc, string_at, write_dbc  # noqa: E402
from catalog import (BUFF_TEMPLATE, CLOUD_TEMPLATE, CONE_TEMPLATE, CRAFT_TEMPLATE, DRINK_ICON, DRINK_TEMPLATE,  # noqa: E402
                     ELIXIR_DURATION_MS, ICON_DISPLAYS, ITEM_CATEGORY, PROC_FLAG_TAKEN_PERIODIC,
                     RECIPE_BLOCKS, STAT_NAMES, WELL_FED_ICON, WELL_FED_TEMPLATE, buff_auras, elixir_group, new_displays,
                     material_crafts, product_kind, recipes)
from catalog import (COMPLETED_FORMS, COSTS, CURRENCY_BIT, CURRENCY_CATEGORY, CURRENCY_ID, FACTIONS, FAVOR,  # noqa: E402
                     FORM_CAST_TIME, FORM_TEMPLATE, ITEM_DISPLAYS, MOUNT_SPELLS, PET_SPELLS, SIGNPOST_CAST_TIME,
                     SIGNPOST_COOLDOWN, SIGNPOST_DURATION, SIGNPOST_RADIUS, SIGNPOSTS, SKILL_COMPANIONS, SKILL_MOUNTS,
                     SPELL_ICONS, SPELL_SIGN_FORM, SPELL_SIGNPOSTS, SUMMON_WILD, TARGET_DEST_CASTER_FRONT, TITLES,
                     USE_SPELLS, items)

SPELL_FIELDS = 234
F_CATEGORY, F_ATTRIBUTES, F_ATTRIBUTES_LAST = 1, 4, 11
F_CAST_TIME, F_RECOVERY, F_CATEGORY_RECOVERY, F_INTERRUPT = 28, 29, 30, 31
F_LEVELS, F_DURATION, F_RANGE = (37, 38, 39), 40, 46
F_REAGENTS, F_REAGENT_COUNTS = 52, 60
F_ITEM_TYPE, F_AMPLITUDE, F_TRIGGER, F_RADIUS = 107, 98, 116, 92
F_TARGETS, F_MECHANIC, F_PROC_FLAGS, F_PROC_CHANCE, F_STACK = 16, 3, 34, 35, 49
F_MAX_TARGETS, F_DAMAGE_CLASS, F_PREVENTION, F_DAMAGE_MULTIPLIER = 212, 213, 214, 216
ONE = 0x3F800000                            # 1.0f
F_DESCRIPTION_VARIABLES, F_DIFFICULTY = 232, 233
F_EFFECT, F_DIE_SIDES, F_BASE_POINTS, F_TARGET_A, F_AURA, F_MISC = 71, 74, 80, 86, 95, 110
F_VISUAL, F_ICON, F_ACTIVE_ICON, F_NAME, F_SUBTEXT, F_DESCRIPTION, F_AURA_TEXT = 131, 133, 134, 136, 153, 170, 187
F_GCD_CATEGORY, F_GCD, F_FAMILY, F_SCHOOL = 205, 206, 208, 225
F_FAMILY_FLAGS = (209, 210, 211)
STRING_FIELDS = set(range(136, 152)) | set(range(153, 169)) | set(range(170, 186)) | set(range(187, 203))
FLOAT_FIELDS = {47, 77, 78, 79, 101, 102, 103, 119, 120, 121, 216, 217, 218, 229, 230, 231}
SIGNED_FIELDS = {0, 13, 15, 41, *range(52, 71), 74, 75, 76, 80, 81, 82, *range(110, 116), 224, 228}
EFFECT_DUMMY, TARGET_UNIT_CASTER, CAST_INSTANT, RANGE_SELF = 3, 1, 1, 1
EFFECT_CREATE_ITEM, EFFECT_APPLY_AURA = 24, 6
AURA_MOD_STAT, AURA_PERIODIC_TRIGGER_SPELL, AURA_MOD_POWER_REGEN, AURA_PERIODIC_DUMMY = 29, 23, 85, 226
AURA_DUMMY, AURA_PERIODIC_DAMAGE, EFFECT_SCHOOL_DAMAGE, EFFECT_PERSISTENT_AREA_AURA = 4, 3, 2, 27
TARGET_UNIT_TARGET_ENEMY, TARGET_CONE_ENEMY, TARGET_DEST_DEST, TARGET_DEST_DYNOBJ_ENEMY = 6, 24, 87, 28
RANGE_ANYWHERE, SCHOOL_NATURE = 13, 8
SKILL_LEARNED_ON_SKILL_VALUE = 1
DUMMY_TEMPLATE = 54710                      # MOLL-E: a plain instant spell to start from
LANG_MASK = 16712190                        # the enUS string plus the flags every stock row has
DISPLAY_FIELDS, DISPLAY_ICON = 25, 5
DRINK_CATEGORY_ID = 59
FACTION_FIELDS, TITLE_FIELDS, IEC_FIELDS, CURRENCY_FIELDS, ITEM_FIELDS, SLA_FIELDS = 57, 37, 16, 4, 8, 14
IDI_FIELDS, ICON_FIELDS = 25, 2
F_RADIUS, F_ITEM_TYPE, F_MISC_B = 92, 107, 113
EFFECT_SUMMON, EFFECT_CREATE_ITEM = 28, 24
F_TOTEMS_AND_REAGENTS = range(50, 68)       # Totem[2], Reagent[8], ReagentCount[8]
HIDDEN = 0x04 | 0x08 | 0x10                 # FACTION_FLAG_HIDDEN | INVISIBLE_FORCED | PEACE_FORCED
OWN = 0x10                                  # PEACE_FORCED: never at war, shown once you have some
UNSET = 0xFFFFFFFF


def dbc_path(files, name):
    for archived, local in files.items():
        if archived.lower() == ("DBFilesClient\\%s.dbc" % name).lower():
            return local
    return None


def need(files, name, client, tmp):
    path = dbc_path(files, name)
    if path:
        return path
    if not client:
        sys.exit("the patch has no %s.dbc: pass --client to start from the client's" % name)
    path = os.path.join(tmp, name + ".dbc")
    dbcmpq.client_file(client, "enUS", "DBFilesClient\\%s.dbc" % name, path)
    files["DBFilesClient\\%s.dbc" % name] = path
    return path


def put(rows, row):
    for i, existing in enumerate(rows):
        if existing[0] == row[0]:
            rows[i] = row
            return
    rows.append(row)


def check_free(rows, row_id, strings, name_field, name, table):
    old = next((r for r in rows if r[0] == row_id), None)
    if old and name_field is not None and string_at(strings, old[name_field]) != name:
        sys.exit("%s row %d is taken by %r" % (table, row_id, string_at(strings, old[name_field])))


def effect_fields(index):
    per_effect = [71, 74, 77, 80, 83, 86, 89, 92, 95, 98, 101, 104, 107, 110, 113, 116, 119, 216, 229]
    return [base + index for base in per_effect] + [122 + index * 3 + i for i in range(3)]


def spell_icons(path):
    rows, strings, _ = read_dbc(path)
    return {string_at(strings, r[1]).split("\\")[-1].lower(): r[0] for r in rows}


def add_spell_icons(path):
    """SpellIcon.dbc rows for the icons the client has no row for (SPELL_ICONS); a row of the same id and
    name is left as it is."""
    rows, strings, fields = read_dbc(path)
    if fields != ICON_FIELDS:
        sys.exit("SpellIcon.dbc has %d fields, not %d" % (fields, ICON_FIELDS))
    for icon_id, name in SPELL_ICONS:
        path_name = "Interface\\Icons\\" + name
        old = next((r for r in rows if r[0] == icon_id), None)
        if old and string_at(strings, old[1]).lower() != path_name.lower():
            sys.exit("SpellIcon.dbc row %d is taken by %r" % (icon_id, string_at(strings, old[1])))
        put(rows, [icon_id, add_string(strings, path_name)])
    write_dbc(path, rows, strings, fields)
    print("SpellIcon.dbc: %d icons" % len(SPELL_ICONS))


# --- Spell.dbc + SkillLineAbility.dbc -------------------------------------------------------------

class Looks:
    """The client's durations, radii and ranges by value, and the spell icons the recipes need, given ids
    from their profession's block where the client has none."""

    def __init__(self, files, client_tables, icons):
        self.icons, self.files = icons, files
        f = lambda v: struct.unpack("<f", struct.pack("<I", v))[0]
        rows = lambda name: read_dbc(client_tables(name))[0]
        self.durations = {r[1]: r[0] for r in rows("SpellDuration") if r[2] == 0 and r[3] == r[1]}
        self.radii = {f(r[1]): r[0] for r in reversed(rows("SpellRadius")) if f(r[2]) == 0}
        self.ranges = {f(r[3]): r[0] for r in reversed(rows("SpellRange")) if f(r[1]) == 0 and f(r[3]) == f(r[4])}
        self.new_icons = []

    def duration(self, ms):
        if ms not in self.durations:
            sys.exit("SpellDuration.dbc has no %d ms" % ms)
        return self.durations[ms]

    def radius(self, yards):
        if float(yards) not in self.radii:
            sys.exit("SpellRadius.dbc has no %d yards" % yards)
        return self.radii[float(yards)]

    def range(self, yards):
        if float(yards) not in self.ranges:
            sys.exit("SpellRange.dbc has no %d yards" % yards)
        return self.ranges[float(yards)]

    def icon(self, name, skill):
        """A SpellIcon id for an icon name: the client's, or a new row from the profession's block."""
        if name.lower() not in self.icons:
            base, size = RECIPE_BLOCKS[skill]
            used = {i for i, _n in self.new_icons} | set(self.icons.values())
            at = next(i for i in range(base, base + size) if i not in used)
            self.new_icons.append((at, name))
            self.icons[name.lower()] = at
        return self.icons[name.lower()]


def add_recipe_spell_icons(files, new_icons):
    path = dbc_path(files, "SpellIcon")
    rows, strings, fields = read_dbc(path)
    for icon_id, name in new_icons:
        old = next((r for r in rows if r[0] == icon_id), None)
        if old and string_at(strings, old[1]).split("\\")[-1].lower() != name.lower():
            sys.exit("SpellIcon.dbc row %d is taken" % icon_id)
        put(rows, [icon_id, add_string(strings, "Interface\\Icons\\" + name)])
        print("SpellIcon.dbc %d %s" % (icon_id, name))
    write_dbc(path, rows, strings, fields)


def add_spells(files, client_tables):
    path = dbc_path(files, "Spell")
    spells, strings, fields = read_dbc(path)
    if fields != SPELL_FIELDS:
        sys.exit("Spell.dbc has %d fields, not %d" % (fields, SPELL_FIELDS))
    by_id = {r[0]: r for r in spells}
    icons = spell_icons(dbc_path(files, "SpellIcon"))
    made = []

    def start(spell_id, template, name):
        check_free(spells, spell_id, strings, F_NAME, name, "Spell.dbc")
        if template not in by_id:
            sys.exit("Spell.dbc row %d (template of %d) is missing" % (template, spell_id))
        row = list(by_id[template])
        row[0] = spell_id
        row[F_FAMILY] = 0
        for f in F_FAMILY_FLAGS:
            row[f] = 0
        for f in STRING_FIELDS:
            row[f] = 0
        return row

    def finish(row, name, description, aura_text=""):
        row[F_NAME] = add_string(strings, name)
        row[F_DESCRIPTION] = add_string(strings, description)
        if aura_text:
            row[F_AURA_TEXT] = add_string(strings, aura_text)
        put(spells, row)
        made.append((row, name, description, aura_text))
        print("Spell.dbc %d %s" % (row[0], name))

    for spell_id, name, description, icon in USE_SPELLS:
        if icon.lower() not in icons:
            sys.exit("SpellIcon.dbc has no %s" % icon)
        row = start(spell_id, DUMMY_TEMPLATE, name)
        row[F_CATEGORY] = 0
        for f in range(F_ATTRIBUTES, F_ATTRIBUTES_LAST + 1):
            row[f] = 0
        row[F_CAST_TIME], row[F_RECOVERY], row[F_CATEGORY_RECOVERY], row[F_INTERRUPT] = CAST_INSTANT, 0, 0, 0
        row[F_DURATION], row[F_RANGE] = 0, RANGE_SELF
        for index in (0, 1, 2):
            for f in effect_fields(index):
                row[f] = 0
        row[F_EFFECT], row[F_DIE_SIDES], row[F_TARGET_A] = EFFECT_DUMMY, 1, TARGET_UNIT_CASTER
        row[F_VISUAL], row[F_ICON], row[F_ACTIVE_ICON] = 0, icons[icon.lower()], 0
        row[F_GCD_CATEGORY], row[F_GCD] = 0, 0
        finish(row, name, description)

    # Sign Form: the template's create-item cast, making the completed forms, in Forever's 10 seconds.
    row = start(SPELL_SIGN_FORM, FORM_TEMPLATE, "Sign Form")
    if row[F_EFFECT] != EFFECT_CREATE_ITEM or row[F_EFFECT + 1] or row[F_EFFECT + 2]:
        sys.exit("Spell.dbc row %d isn't a plain create-item spell" % FORM_TEMPLATE)
    row[F_ITEM_TYPE] = COMPLETED_FORMS
    row[F_CAST_TIME] = FORM_CAST_TIME
    for f in F_TOTEMS_AND_REAGENTS:             # the template's own medallion: the forms need nothing
        row[f] = 0
    row[F_ICON] = icons["inv_letter_03"]
    finish(row, "Sign Form", "")

    # The signpost toys: summon the post 2 yards in front for a minute, on a 30 minute cooldown.
    for spell_id, post, name in zip(SPELL_SIGNPOSTS, SIGNPOSTS, ("Orcish Tradeskill Signpost", "Dwarven Tradeskill Signpost")):
        row = start(spell_id, DUMMY_TEMPLATE, name)
        row[F_CATEGORY] = 0
        for f in range(F_ATTRIBUTES, F_ATTRIBUTES_LAST + 1):
            row[f] = 0
        row[F_CAST_TIME], row[F_RECOVERY], row[F_CATEGORY_RECOVERY], row[F_INTERRUPT] = (
            SIGNPOST_CAST_TIME, SIGNPOST_COOLDOWN, 0, 15)
        row[F_DURATION], row[F_RANGE] = SIGNPOST_DURATION, RANGE_SELF
        for index in (0, 1, 2):
            for f in effect_fields(index):
                row[f] = 0
        row[F_EFFECT], row[F_DIE_SIDES], row[F_TARGET_A] = EFFECT_SUMMON, 1, TARGET_DEST_CASTER_FRONT
        row[F_RADIUS], row[F_MISC], row[F_MISC_B] = SIGNPOST_RADIUS, post, SUMMON_WILD
        # Forever gives both toys' spells the orcish icon.
        row[F_VISUAL], row[F_ICON], row[F_ACTIVE_ICON] = 0, icons["trade_archaeology_orc_bloodtext"], 0
        row[F_GCD_CATEGORY], row[F_GCD] = 133, 1500
        finish(row, name, "Display a sign for a profession you have learned for 30 min.")

    abilities_path = dbc_path(files, "SkillLineAbility")
    abilities, ability_strings, ability_fields = read_dbc(abilities_path)
    if ability_fields != SLA_FIELDS:
        sys.exit("SkillLineAbility.dbc has %d fields, not %d" % (ability_fields, SLA_FIELDS))
    lines = []
    for skill, group in ((SKILL_MOUNTS, MOUNT_SPELLS), (SKILL_COMPANIONS, PET_SPELLS)):
        for spell_id, template, creature, name, description, icon_from in group:
            row = start(spell_id, template, name)
            for index in (0, 1, 2):
                if row[F_AURA + index] == 78 or row[F_EFFECT + index] == 28:    # MOUNTED aura / SUMMON
                    row[F_MISC + index] = creature
            row[F_ICON] = by_id[icon_from][F_ICON]
            finish(row, name, description)
            old = next((r for r in abilities if r[0] == spell_id), None)
            if old and old[2] != spell_id:
                sys.exit("SkillLineAbility.dbc row %d is taken" % spell_id)
            put(abilities, [spell_id, skill, spell_id, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0])
            lines.append(next(a for a in abilities if a[0] == spell_id))

    looks = Looks(files, client_tables, icons)
    # The materials' crafts look like a recipe's craft to the code below: no recipe item, no use.
    crafts = [dict(craft=m["craft"], skill=m["skill"], reagents=m["reagents"], product=m["item"], made=1,
                   product_name=m["name"], use=[], grey=m["grey"], yellow=m["yellow"], recipe=m["item"])
              for m in material_crafts()]
    for r in recipes() + crafts:
        add_recipe_spells(r, by_id, icons, start, finish, looks)
        old = next((a for a in abilities if a[0] == r["craft"]), None)
        if old and old[2] != r["craft"]:
            sys.exit("SkillLineAbility.dbc row %d is taken" % r["craft"])
        # MinSkillLineRank 1 and AcquireMethod 0, as Forever's and the stock vendor recipes': the recipe
        # item asks for the skill. Trivial ranks: grey, then yellow.
        row = [r["craft"], r["skill"], r["craft"], 0, 0, 0, 0, 1, 0, 0, r["grey"], r["yellow"], 0, 0]
        put(abilities, row)
        lines.append(row)
    write_dbc(path, spells, strings, fields)
    write_dbc(abilities_path, abilities, ability_strings, ability_fields)
    add_recipe_spell_icons(files, looks.new_icons)
    return made, lines


def clear_effects(row):
    for index in (0, 1, 2):
        for f in effect_fields(index):
            row[f] = 0


def set_effect(row, index, effect, target, amount, aura=0, misc=0, period=0, trigger=0, radius=0, target_b=0):
    """One effect, as a 3.3.5a row holds it: the amount is base points + 1 die side."""
    row[F_EFFECT + index], row[F_TARGET_A + index], row[F_TARGET_A + 3 + index] = effect, target, target_b
    row[F_DIE_SIDES + index], row[F_BASE_POINTS + index] = 1, (amount - 1) & 0xFFFFFFFF
    row[F_AURA + index], row[F_MISC + index] = aura, misc & 0xFFFFFFFF
    row[F_AMPLITUDE + index], row[F_TRIGGER + index], row[F_RADIUS + index] = period, trigger, radius
    row[F_DAMAGE_MULTIPLIER + index] = ONE        # every target takes it all (a chain spell's falloff)


def potion_like(row, r, looks, icon_name):
    """What every product spell shares: instant, no cooldown of its own (the item's), its icon."""
    row[F_CATEGORY] = ITEM_CATEGORY[product_kind(r)][0]
    row[F_CAST_TIME], row[F_RECOVERY], row[F_CATEGORY_RECOVERY] = CAST_INSTANT, 0, 0
    row[F_STACK], row[F_PROC_FLAGS], row[F_MAX_TARGETS], row[F_MECHANIC] = 0, 0, 0, 0
    row[F_GCD_CATEGORY] = 0                       # an NPC template's own global cooldown group
    row[F_DESCRIPTION_VARIABLES], row[F_DIFFICULTY] = 0, 0       # and its heroic variant
    for f in F_LEVELS:
        row[f] = 0
    row[F_ICON] = looks.icon(icon_name, r["skill"])


def add_recipe_spells(r, by_id, icons, start, finish, looks):
    """A recipe's craft spell, and its product's use spells."""
    craft = start(r["craft"], CRAFT_TEMPLATE[r["skill"]], r["product_name"])
    for f in range(8):
        item, count = r["reagents"][f] if f < len(r["reagents"]) else (0, 0)
        craft[F_REAGENTS + f], craft[F_REAGENT_COUNTS + f] = item, count
    if craft[F_EFFECT] != EFFECT_CREATE_ITEM:
        sys.exit("craft template %d doesn't create an item" % CRAFT_TEMPLATE[r["skill"]])
    craft[F_ITEM_TYPE] = r["product"]
    craft[F_DIE_SIDES], craft[F_BASE_POINTS] = 1, r["made"] - 1
    finish(craft, r["product_name"], "")

    if not r["use"]:
        return
    kind = r["use"][0]
    if kind != "drink":
        return add_alchemy_spells(r, by_id, start, finish, looks)
    kind, stock_drink, _stat_word, stat, amount = r["use"]
    stock_drink, stat, amount = int(stock_drink), int(stat), int(amount)
    drink_id, fed_id = r["use_spells"]
    stock = by_id.get(stock_drink)
    if not stock or stock[F_AURA + 1] != AURA_PERIODIC_DUMMY:
        sys.exit("Spell.dbc %d isn't a stock drink with its amount in effect 2" % stock_drink)
    seconds = {85: 18, 86: 21, 106: 24, 205: 27, 9: 30}.get(stock[F_DURATION])
    if seconds is None:
        sys.exit("drink %d: unknown duration index %d" % (stock_drink, stock[F_DURATION]))

    # The drink: Brain Food's mana half with the stock drink's duration, levels and amount (per 5
    # seconds), and its periodic trigger pointed at our Well Fed.
    drink = start(drink_id, DRINK_TEMPLATE, "Nutritious Drink")
    if drink[F_AURA] != AURA_MOD_POWER_REGEN or drink[F_AURA + 1] != AURA_PERIODIC_TRIGGER_SPELL:
        sys.exit("drink template %d changed" % DRINK_TEMPLATE)
    drink[F_CATEGORY] = DRINK_CATEGORY_ID
    for f in F_LEVELS + (F_DURATION, F_VISUAL):       # the visual: drinking, not Brain Food's eating
        drink[f] = stock[f]
    drink[F_DIE_SIDES], drink[F_BASE_POINTS] = 1, stock[F_BASE_POINTS + 1]
    drink[F_TRIGGER + 1] = fed_id
    drink[F_ICON] = icons[DRINK_ICON]
    finish(drink, "Nutritious Drink",
           "Restores ${$m1/5*%d} mana over $d.  Must remain seated while drinking.  If you spend at least 10 "
           "seconds drinking you will become well fed and gain $%ds1 %s for $%dd."
           % (seconds, fed_id, STAT_NAMES[stat], fed_id),
           "Restores $/5;s1 mana per second.")

    # Well Fed: the stock one's buff (food-buff attribute, 15 minutes) with the stat in place of mana.
    fed = start(fed_id, WELL_FED_TEMPLATE, "Well Fed")
    if fed[F_AURA] != AURA_MOD_POWER_REGEN:
        sys.exit("Well Fed template %d changed" % WELL_FED_TEMPLATE)
    fed[F_AURA], fed[F_MISC] = AURA_MOD_STAT, stat
    fed[F_DIE_SIDES], fed[F_BASE_POINTS] = 1, amount - 1
    fed[F_ICON] = icons[WELL_FED_ICON]
    finish(fed, "Well Fed", "A tasty drink has made you Well Fed, increasing your %s by $s1." % STAT_NAMES[stat],
           "%s increased by $s1." % STAT_NAMES[stat])


def add_alchemy_spells(r, by_id, start, finish, looks):
    """Elixirs and potions (a buff on you), Dragonfire (a cone), Caustic Smog (a cloud), Venomous Blood."""
    kind, icon, name = r["use"][0], r["product_icon"], r["product_name"]
    spells = r["use_spells"]
    if kind == "buff":
        group = elixir_group(r) if r["use"][1] == "elixir" else "potion"
        row = start(spells[0], BUFF_TEMPLATE[group], name)
        clear_effects(row)
        for index, (aura, misc, amount) in enumerate(buff_auras(r)):
            # An elixir's first effect names its craft spell, as the stock ones: Mixology looks there.
            trigger = r["craft"] if index == 0 and r["use"][1] == "elixir" else 0
            set_effect(row, index, EFFECT_APPLY_AURA, TARGET_UNIT_CASTER, amount, aura=aura, misc=misc, trigger=trigger)
        row[F_FAMILY] = by_id[BUFF_TEMPLATE[group]][F_FAMILY]       # Potion, as the stock elixirs
        ms = ELIXIR_DURATION_MS if r["use"][1] == "elixir" else int(r["use"][2])
        row[F_DURATION] = looks.duration(ms)
        potion_like(row, r, looks, icon)
        return finish(row, name, r["use_text"], r["use_aura_text"])
    if kind == "cone":
        ms, yards, school, hit, tick, period, _degrees = (int(x) for x in r["use"][1:])
        row = start(spells[0], CONE_TEMPLATE, name)
        clear_effects(row)
        for f in range(F_ATTRIBUTES, F_ATTRIBUTES_LAST + 1):
            row[f] = 0
        row[F_INTERRUPT] = 0
        radius = looks.radius(yards)
        set_effect(row, 0, EFFECT_SCHOOL_DAMAGE, TARGET_CONE_ENEMY, hit, radius=radius)
        set_effect(row, 1, EFFECT_APPLY_AURA, TARGET_CONE_ENEMY, tick, aura=AURA_PERIODIC_DAMAGE, period=period,
                   radius=radius)
        row[F_DURATION], row[F_RANGE], row[F_SCHOOL] = looks.duration(ms), RANGE_SELF, school
        row[F_DAMAGE_CLASS], row[F_PREVENTION] = 0, 0           # as an item's damage, like a grenade's
        potion_like(row, r, looks, icon)
        return finish(row, name, r["use_text"], r["use_aura_text"])
    if kind == "cloud":
        ms, yards, school, tick, period, reach = (int(x) for x in r["use"][1:])
        row = start(spells[0], CLOUD_TEMPLATE, name)
        clear_effects(row)
        set_effect(row, 0, EFFECT_PERSISTENT_AREA_AURA, TARGET_DEST_DEST, tick, aura=AURA_PERIODIC_DAMAGE,
                   period=period, radius=looks.radius(yards), target_b=TARGET_DEST_DYNOBJ_ENEMY)
        row[F_DURATION], row[F_RANGE], row[F_SCHOOL] = looks.duration(ms), looks.range(reach), school
        potion_like(row, r, looks, icon)
        return finish(row, name, "Throw a fragile concoction at the target area, revealing a cloud of %s for $d. "
                      "Enemies standing within the cloud suffer $s1 Nature damage every $t1 sec." % name.replace(" Potion", ""), "")
    if kind == "venom":
        ms, doses, damage, yards = (int(x) for x in r["use"][1:])
        buff_id, dose_id, hit_id = spells
        buff = start(buff_id, BUFF_TEMPLATE["potion"], "Venomous Blood")
        clear_effects(buff)
        set_effect(buff, 0, EFFECT_APPLY_AURA, TARGET_UNIT_CASTER, damage, aura=AURA_DUMMY, trigger=dose_id)
        set_effect(buff, 1, EFFECT_APPLY_AURA, TARGET_UNIT_CASTER, yards, aura=AURA_DUMMY)
        buff[F_FAMILY] = by_id[BUFF_TEMPLATE["potion"]][F_FAMILY]
        buff[F_DURATION] = looks.duration(ms)
        potion_like(buff, r, looks, icon)
        buff[F_STACK], buff[F_PROC_FLAGS], buff[F_PROC_CHANCE] = doses, PROC_FLAG_TAKEN_PERIODIC, 100
        finish(buff, "Venomous Blood",
               "Gain %d doses of Venomous Blood. Whenever you suffer Bleed damage, one dose is spread to the nearest "
               "enemy within $s2 yds. Lasts up to $d.  A dose deals $s1 Nature damage when it expires." % doses,
               "Whenever you suffer Bleed damage, one dose is splashed onto the nearest enemy within $s2 yds.")
        dose = start(dose_id, BUFF_TEMPLATE["potion"], "Venomous Blood")
        clear_effects(dose)
        set_effect(dose, 0, EFFECT_APPLY_AURA, TARGET_UNIT_TARGET_ENEMY, damage, aura=AURA_DUMMY, trigger=hit_id)
        dose[F_FAMILY], dose[F_DURATION], dose[F_RANGE] = 0, looks.duration(ms), RANGE_ANYWHERE
        potion_like(dose, r, looks, icon)
        dose[F_STACK] = 99
        dose[F_CATEGORY], dose[F_VISUAL] = 0, 0       # not Speed's quaff on the enemy
        for f in range(F_ATTRIBUTES, F_ATTRIBUTES_LAST + 1):
            dose[f] = 0
        finish(dose, "Venomous Blood", "",
               "A nearby bleeding target has splashed Venomous Blood onto you.  When this effect expires, you will "
               "suffer $s1 Nature damage for each dose.")
        hit = start(hit_id, DUMMY_TEMPLATE, "Venomous Blood")
        clear_effects(hit)
        set_effect(hit, 0, EFFECT_SCHOOL_DAMAGE, TARGET_UNIT_TARGET_ENEMY, damage)
        hit[F_RANGE], hit[F_SCHOOL], hit[F_DURATION] = RANGE_ANYWHERE, SCHOOL_NATURE, 0
        hit[F_CAST_TIME], hit[F_ICON], hit[F_VISUAL] = CAST_INSTANT, looks.icon(icon, r["skill"]), 0
        return finish(hit, "Venomous Blood", "")
    sys.exit("recipe %d: no spells for %r" % (r["recipe"], kind))


# --- ItemDisplayInfo.dbc ---------------------------------------------------------------------------

def add_displays(files, client):
    """Icon-only display rows for the recipes' icons the client has none for; checks the ones reused,
    and with --client that every new one's icon file is in the client or the patch (else it shows as a
    question mark): our client's icons include Project Reforged HD's."""
    path = dbc_path(files, "ItemDisplayInfo")
    rows, strings, fields = read_dbc(path)
    if fields != DISPLAY_FIELDS:
        sys.exit("ItemDisplayInfo.dbc has %d fields, not %d" % (fields, DISPLAY_FIELDS))
    by_id = {r[0]: r for r in rows}
    for icon, display in ICON_DISPLAYS.items():
        r = by_id.get(display)
        if not r or string_at(strings, r[DISPLAY_ICON]).lower() != icon:
            sys.exit("ItemDisplayInfo.dbc %d isn't the icon %s" % (display, icon))
    for template_id in {t for _d, _i, t in new_displays()}:
        template = by_id.get(template_id)
        if not template or any(template[1:DISPLAY_ICON]):
            sys.exit("ItemDisplayInfo.dbc %d isn't an icon-only row" % template_id)
    blps = {"Interface\\Icons\\%s.blp" % icon for _d, icon, _t in new_displays()}
    lacking = {b for b in blps if b.lower() not in {f.lower() for f in files}}
    if client:
        lacking = dbcmpq.client_has(client, lacking)
    elif lacking:
        print("not checked without --client: %s" % ", ".join(sorted(lacking)))
        lacking = set()
    if lacking:
        sys.exit("no icon file for %s" % ", ".join(sorted(lacking)))
    for display, icon, template_id in new_displays():
        old = by_id.get(display)
        if old and string_at(strings, old[DISPLAY_ICON]).lower() != icon.lower():
            sys.exit("ItemDisplayInfo.dbc row %d is taken" % display)
        row = list(by_id[template_id])
        row[0], row[DISPLAY_ICON] = display, add_string(strings, icon)
        put(rows, row)
        print("ItemDisplayInfo.dbc %d %s" % (display, icon))
    write_dbc(path, rows, strings, fields)


# --- Item.dbc ------------------------------------------------------------------------------------

def add_items(files):
    path = dbc_path(files, "Item")
    rows, strings, fields = read_dbc(path)
    if fields != ITEM_FIELDS:
        sys.exit("Item.dbc has %d fields, not %d" % (fields, ITEM_FIELDS))
    ours = items()
    for i in ours:
        put(rows, [i["entry"], i["cls"], i["subclass"], UNSET, i["material"] & 0xFFFFFFFF, i["display"], i["inv_type"], 0])
    write_dbc(path, rows, strings, fields)
    print("Item.dbc: %d items" % len(ours))


def add_item_displays(path):
    """ItemDisplayInfo.dbc rows: an icon, and for the tabards their textures and geoset group."""
    rows, strings, fields = read_dbc(path)
    if fields != IDI_FIELDS:
        sys.exit("ItemDisplayInfo.dbc has %d fields, not %d" % (fields, IDI_FIELDS))
    for display, icon, textures, geoset, sound in ITEM_DISPLAYS:
        old = next((r for r in rows if r[0] == display), None)
        if old and string_at(strings, old[5]).lower() != icon.lower():
            sys.exit("ItemDisplayInfo.dbc row %d is taken by %r" % (display, string_at(strings, old[5])))
        row = [0] * fields
        row[0] = display
        row[5] = add_string(strings, icon)
        row[7] = geoset
        row[12] = sound
        for field, name in textures.items():
            row[field] = add_string(strings, name)
        put(rows, row)
    write_dbc(path, rows, strings, fields)
    print("ItemDisplayInfo.dbc %d-%d" % (min(d[0] for d in ITEM_DISPLAYS), max(d[0] for d in ITEM_DISPLAYS)))


# --- Faction, CharTitles, CurrencyTypes, ItemExtendedCost -----------------------------------------

def add_factions(path):
    rows, strings, fields = read_dbc(path)
    if fields != FACTION_FIELDS:
        sys.exit("Faction.dbc has %d fields, not %d" % (fields, FACTION_FIELDS))
    made = []
    for faction_id, rep_index, own, other, parent, name, description in FACTIONS:
        check_free(rows, faction_id, strings, 23, name, "Faction.dbc")
        taken = [r[0] for r in rows if r[1] == rep_index and r[0] != faction_id]
        if taken:
            sys.exit("Faction.dbc reputation index %d is taken by faction %d" % (rep_index, taken[0]))
        row = [0] * FACTION_FIELDS
        row[0], row[1] = faction_id, rep_index
        row[2], row[3] = own, other
        row[14], row[15] = OWN, HIDDEN
        row[18] = parent
        row[19] = row[20] = 0      # ParentFactionMod in/out 0.0: no spillover to or from the capitals
        row[21], row[22] = 5, 5     # like the stock factions
        row[23] = add_string(strings, name)
        row[39] = LANG_MASK
        row[40] = add_string(strings, description)
        row[56] = LANG_MASK
        put(rows, row)
        made.append((row, name, description))
        print("Faction.dbc %d %s" % (faction_id, name))
    write_dbc(path, rows, strings, fields)
    return made


def add_titles(path):
    rows, strings, fields = read_dbc(path)
    if fields != TITLE_FIELDS:
        sys.exit("CharTitles.dbc has %d fields, not %d" % (fields, TITLE_FIELDS))
    ours = {t[0] for t in TITLES}
    taken = [r[0] for r in rows if r[0] not in ours and r[36] in {t[1] for t in TITLES}]
    if taken:
        sys.exit("CharTitles.dbc rows %s already use our title bits" % taken)
    made = []
    for title_id, bit, _item, _skill, text in TITLES:
        check_free(rows, title_id, strings, 2, text, "CharTitles.dbc")
        row = [0] * fields
        row[0] = title_id
        row[2] = row[19] = add_string(strings, text)
        row[18] = row[35] = LANG_MASK
        row[36] = bit
        put(rows, row)
        made.append((row, text))
        print("CharTitles.dbc %d %s" % (title_id, text))
    write_dbc(path, rows, strings, fields)
    return made


def add_currency(path):
    rows, strings, fields = read_dbc(path)
    if fields != CURRENCY_FIELDS:
        sys.exit("CurrencyTypes.dbc has %d fields, not %d" % (fields, CURRENCY_FIELDS))
    for r in rows:
        if r[0] != CURRENCY_ID and (r[1] == FAVOR or r[3] == CURRENCY_BIT):
            sys.exit("CurrencyTypes.dbc row %d already uses item %d or bit %d" % (r[0], FAVOR, CURRENCY_BIT))
    row = [CURRENCY_ID, FAVOR, CURRENCY_CATEGORY, CURRENCY_BIT]
    put(rows, row)
    write_dbc(path, rows, strings, fields)
    print("CurrencyTypes.dbc %d Merchant's Favor" % CURRENCY_ID)
    return row


def add_costs(path):
    rows, strings, fields = read_dbc(path)
    if fields != IEC_FIELDS:
        sys.exit("ItemExtendedCost.dbc has %d fields, not %d" % (fields, IEC_FIELDS))
    made = []
    for cost_id, favor in sorted(COSTS.items()):
        old = next((r for r in rows if r[0] == cost_id), None)
        if old and old[4] not in (FAVOR, 0):
            sys.exit("ItemExtendedCost.dbc row %d is taken (item %d)" % (cost_id, old[4]))
        row = [cost_id, 0, 0, 0, FAVOR, 0, 0, 0, 0, favor, 0, 0, 0, 0, 0, 0]
        put(rows, row)
        made.append(row)
    write_dbc(path, rows, strings, fields)
    print("ItemExtendedCost.dbc %d-%d" % (min(COSTS), max(COSTS)))
    return made


# --- SQL -----------------------------------------------------------------------------------------

def sql_str(s):
    return "'" + s.replace("\\", "\\\\").replace("'", "''") + "'"


def spell_value(i, v):
    if i in STRING_FIELDS:
        return "''"
    if i in FLOAT_FIELDS:
        return "%g" % struct.unpack("<f", struct.pack("<I", v))[0]
    return str(struct.unpack("<i", struct.pack("<I", v))[0] if i in SIGNED_FIELDS else v)


def write_sql(path, spells, abilities, factions, titles, currency, costs):
    def ids(values):
        return ", ".join(str(v) for v in values)

    out = ["-- mod-supply-logistics: the rows the client also has. Generated by tools/build_patch.py from the",
           "-- same rows the client patch gets: run the tool again, don't edit this file.", ""]
    lines = []
    for row, name, description, aura_text in spells:
        values = [spell_value(i, v) for i, v in enumerate(row)]
        values[F_NAME], values[F_DESCRIPTION] = sql_str(name), sql_str(description)
        values[F_AURA_TEXT] = sql_str(aura_text)
        lines.append("(" + ", ".join(values) + ")")
    out.append("DELETE FROM `spell_dbc` WHERE `ID` IN (%s);" % ids(r[0] for r, _n, _d, _a in spells))
    out.append("INSERT INTO `spell_dbc` VALUES\n" + ",\n".join(lines) + ";")
    out.append("DELETE FROM `skilllineability_dbc` WHERE `ID` IN (%s);" % ids(a[0] for a in abilities))
    out.append("INSERT INTO `skilllineability_dbc` (`ID`, `SkillLine`, `Spell`, `RaceMask`, `ClassMask`, `ExcludeRace`, "
               "`ExcludeClass`, `MinSkillLineRank`, `SupercededBySpell`, `AcquireMethod`, `TrivialSkillLineRankHigh`, "
               "`TrivialSkillLineRankLow`, `CharacterPoints_1`, `CharacterPoints_2`) VALUES\n"
               + ",\n".join("(" + ", ".join(str(v) for v in a) + ")" for a in abilities) + ";")
    out.append("")

    def text_row(row, string_fields):
        values = []
        for i, v in enumerate(row):
            if i in string_fields:
                values.append(sql_str(string_fields[i]))
            elif any(i in range(f + 1, f + 16) for f in string_fields):
                values.append("''")
            else:
                values.append(str(v))
        return "(" + ", ".join(values) + ")"

    out.append("DELETE FROM `faction_dbc` WHERE `ID` IN (%s);" % ids(r[0] for r, _n, _d in factions))
    out.append("INSERT INTO `faction_dbc` VALUES\n" + ",\n".join(
        text_row(row, {23: name, 40: description}) for row, name, description in factions) + ";")
    out.append("DELETE FROM `chartitles_dbc` WHERE `ID` IN (%s);" % ids(r[0] for r, _t in titles))
    out.append("INSERT INTO `chartitles_dbc` VALUES\n" + ",\n".join(
        text_row(row, {2: text, 19: text}) for row, text in titles) + ";")
    out.append("DELETE FROM `currencytypes_dbc` WHERE `ID` = %d;" % currency[0])
    out.append("INSERT INTO `currencytypes_dbc` (`ID`, `ItemID`, `CategoryID`, `BitIndex`) VALUES (%s);"
               % ", ".join(str(v) for v in currency))
    out.append("DELETE FROM `itemextendedcost_dbc` WHERE `ID` IN (%s);" % ids(r[0] for r in costs))
    out.append("INSERT INTO `itemextendedcost_dbc` (`ID`, `HonorPoints`, `ArenaPoints`, `ArenaBracket`, `ItemID_1`, "
               "`ItemID_2`, `ItemID_3`, `ItemID_4`, `ItemID_5`, `ItemCount_1`, `ItemCount_2`, `ItemCount_3`, "
               "`ItemCount_4`, `ItemCount_5`, `RequiredArenaRating`, `ItemPurchaseGroup`) VALUES\n"
               + ",\n".join("(" + ", ".join(str(v) for v in r) + ")" for r in costs) + ";")
    out.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("wrote", path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--patch", required=True, help="your realm's spell and item patch")
    ap.add_argument("--client", help="a 3.3.5a client folder, for the tables the patch lacks")
    ap.add_argument("--out", help="the new patch")
    ap.add_argument("--sql", help="write the server's copy of the rows here")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        files = dbcmpq.unpack(args.patch, tmp)
        for name in ("Spell", "SpellIcon", "Item", "SkillLineAbility", "ItemExtendedCost", "ItemDisplayInfo"):
            if not dbc_path(files, name):
                sys.exit("%s has no %s.dbc" % (args.patch, name))
        add_spell_icons(dbc_path(files, "SpellIcon"))
        def client_tables(name):
            path = os.path.join(tmp, "client-" + name + ".dbc")
            if not os.path.exists(path):
                if not args.client:
                    sys.exit("the recipes need the client's %s.dbc: pass --client" % name)
                dbcmpq.client_file(args.client, "enUS", "DBFilesClient\\%s.dbc" % name, path)
            return path

        spells, abilities = add_spells(files, client_tables)
        add_items(files)
        add_item_displays(dbc_path(files, "ItemDisplayInfo"))
        add_displays(files, args.client)
        factions = add_factions(need(files, "Faction", args.client, tmp))
        titles = add_titles(need(files, "CharTitles", args.client, tmp))
        currency = add_currency(need(files, "CurrencyTypes", args.client, tmp))
        costs = add_costs(dbc_path(files, "ItemExtendedCost"))
        if args.out:
            dbcmpq.pack(args.out, [(local, archived) for archived, local in sorted(files.items())])
            print("%s: %d files, %.1f MB" % (args.out, len(files), os.path.getsize(args.out) / 1e6))
        if args.sql:
            write_sql(args.sql, spells, abilities, factions, titles, currency, costs)


if __name__ == "__main__":
    main()
