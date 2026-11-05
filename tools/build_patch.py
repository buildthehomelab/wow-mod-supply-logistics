#!/usr/bin/env python3
"""The client side of mod-supply-logistics: its rows for your realm's spell and item patch, and the
same rows for the server.

    python3 build_patch.py --patch patch-z80-spells-and-items.MPQ --client /path/to/3.3.5a/client \\
        --out new/patch-z80-spells-and-items.MPQ --sql ../data/sql/db-world/mod_supply_logistics_dbc.sql

--patch is the patch that carries your realm's Spell.dbc, Item.dbc, SkillLineAbility.dbc and
ItemExtendedCost.dbc. A patch MPQ replaces whole files, so the new rows go into its copies and every
other file is carried over unchanged. Faction.dbc, CharTitles.dbc and CurrencyTypes.dbc come from the
patch when it has them, else from the client's own (--client, its newest enUS locale patch), and the
patch gains them. What gets added (ids in catalog.py):

- Spell.dbc: the use spells of the crates, writs, receipt, quill and Certifications (dummies the
  module's item scripts answer), the Pack Kodo and Pack Mule mounts (from Great Brown Kodo and Swift
  Brown Steed) and the Minimule companion (from Mr. Wiggles). SkillLineAbility.dbc puts the last three
  on the Mounts and Companions lines, so they show in the Companions window.
- Item.dbc: every item of the module, so it has its icon everywhere.
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
from catalog import (COSTS, CURRENCY_BIT, CURRENCY_CATEGORY, CURRENCY_ID, FACTIONS, FAVOR, MOUNT_SPELLS,  # noqa: E402
                     PET_SPELLS, SKILL_COMPANIONS, SKILL_MOUNTS, TITLES, USE_SPELLS, items)

SPELL_FIELDS = 234
F_CATEGORY, F_ATTRIBUTES, F_ATTRIBUTES_LAST = 1, 4, 11
F_CAST_TIME, F_RECOVERY, F_CATEGORY_RECOVERY, F_INTERRUPT = 28, 29, 30, 31
F_DURATION, F_RANGE = 40, 46
F_EFFECT, F_DIE_SIDES, F_BASE_POINTS, F_TARGET_A, F_AURA, F_MISC = 71, 74, 80, 86, 95, 110
F_VISUAL, F_ICON, F_ACTIVE_ICON, F_NAME, F_SUBTEXT, F_DESCRIPTION, F_AURA_TEXT = 131, 133, 134, 136, 153, 170, 187
F_GCD_CATEGORY, F_GCD, F_FAMILY, F_SCHOOL = 205, 206, 208, 225
F_FAMILY_FLAGS = (209, 210, 211)
STRING_FIELDS = set(range(136, 152)) | set(range(153, 169)) | set(range(170, 186)) | set(range(187, 203))
FLOAT_FIELDS = {47, 77, 78, 79, 101, 102, 103, 119, 120, 121, 216, 217, 218, 229, 230, 231}
SIGNED_FIELDS = {0, 13, 15, 41, *range(52, 71), 74, 75, 76, 80, 81, 82, *range(110, 116), 224, 228}
EFFECT_DUMMY, TARGET_UNIT_CASTER, CAST_INSTANT, RANGE_SELF = 3, 1, 1, 1
DUMMY_TEMPLATE = 54710                      # MOLL-E: a plain instant spell to start from
LANG_MASK = 16712190                        # the enUS string plus the flags every stock row has
FACTION_FIELDS, TITLE_FIELDS, IEC_FIELDS, CURRENCY_FIELDS, ITEM_FIELDS, SLA_FIELDS = 57, 37, 16, 4, 8, 14
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


# --- Spell.dbc + SkillLineAbility.dbc -------------------------------------------------------------

def add_spells(files):
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

    def finish(row, name, description):
        row[F_NAME] = add_string(strings, name)
        row[F_DESCRIPTION] = add_string(strings, description)
        put(spells, row)
        made.append((row, name, description))
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
            lines.append((spell_id, skill))
    write_dbc(path, spells, strings, fields)
    write_dbc(abilities_path, abilities, ability_strings, ability_fields)
    return made, lines


# --- Item.dbc ------------------------------------------------------------------------------------

def add_items(files):
    path = dbc_path(files, "Item")
    rows, strings, fields = read_dbc(path)
    if fields != ITEM_FIELDS:
        sys.exit("Item.dbc has %d fields, not %d" % (fields, ITEM_FIELDS))
    ours = items()
    for i in ours:
        put(rows, [i["entry"], i["cls"], i["subclass"], UNSET, i["material"] & 0xFFFFFFFF, i["display"], 0, 0])
    write_dbc(path, rows, strings, fields)
    print("Item.dbc: %d items" % len(ours))


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
    for row, name, description in spells:
        values = [spell_value(i, v) for i, v in enumerate(row)]
        values[F_NAME], values[F_DESCRIPTION] = sql_str(name), sql_str(description)
        lines.append("(" + ", ".join(values) + ")")
    out.append("DELETE FROM `spell_dbc` WHERE `ID` IN (%s);" % ids(r[0] for r, _n, _d in spells))
    out.append("INSERT INTO `spell_dbc` VALUES\n" + ",\n".join(lines) + ";")
    out.append("DELETE FROM `skilllineability_dbc` WHERE `ID` IN (%s);" % ids(s for s, _k in abilities))
    out.append("INSERT INTO `skilllineability_dbc` (`ID`, `SkillLine`, `Spell`, `RaceMask`, `ClassMask`, `ExcludeRace`, "
               "`ExcludeClass`, `MinSkillLineRank`, `SupercededBySpell`, `AcquireMethod`, `TrivialSkillLineRankHigh`, "
               "`TrivialSkillLineRankLow`, `CharacterPoints_1`, `CharacterPoints_2`) VALUES\n"
               + ",\n".join("(%d, %d, %d, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0)" % (s, k, s) for s, k in abilities) + ";")
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
        for name in ("Spell", "SpellIcon", "Item", "SkillLineAbility", "ItemExtendedCost"):
            if not dbc_path(files, name):
                sys.exit("%s has no %s.dbc" % (args.patch, name))
        spells, abilities = add_spells(files)
        add_items(files)
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
