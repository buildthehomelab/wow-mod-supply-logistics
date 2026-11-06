#!/usr/bin/env python3
"""Rebuilds one profession's rows of data/recipes.tsv from WoW Forever's own tables.

    python3 fetch_recipes.py --wago <folder> --sells <wowhead_sells.json> --listfile <community-listfile.csv> \\
        --skill 185

- What the camps sell and for how much Favor: every camp NPC's Wowhead "sells" list
  (www.wowhead.com/forever/npc=<id>, the listview's data), saved as one JSON object keyed by NPC id.
- Everything else: Forever's client tables for build 1.60.1.70790 as wago.tools exports them
  (https://wago.tools/db2/<Table>/csv?build=1.60.1.70790, saved as w-<Table>.csv): ItemSparse, Item,
  ItemEffect, ItemXItemEffect, Spell, SpellName, SpellMisc, SpellDuration, SpellRadius, SpellRange,
  SpellAuraOptions, SpellTargetRestrictions, SpellEffect, SpellReagents, SkillLineAbility.
- Icon names: the community listfile (wowdev/wow-listfile), by IconFileDataID.

Rows for other professions are kept, so the professions can be fetched one at a time, and so are the
ids the module gave a recipe before (catalog.assign_ids gives the new ones). Only recipes
sold for Favor are written; the camps' stock recipes for coin are plain vendor rows (catalog.py).
A product this tool can't describe stops it, rather than guessing.

Released under the MIT License.
"""

import argparse
import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from catalog import ID_COLUMNS, assign_ids  # noqa: E402
import fetch_forever  # noqa: E402  (its Wowhead tooltip cache)

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
OUT = os.path.join(DATA, "recipes.tsv")
FAVOR_CURRENCY = 3402
HORDE_VENDORS = {248196, 248197, 248198, 248199, 248200, 248201, 248202}
ALLIANCE_VENDORS = {256729, 256730, 256731, 256732, 256733, 256734, 256735}
EFFECT_TRIGGER_SPELL, EFFECT_CREATE_ITEM, EFFECT_LEARN_SPELL, EFFECT_APPLY_AURA = 64, 24, 36, 6
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_MOD_STAT, AURA_PERIODIC_TRIGGER_SPELL_WITH_VALUE = 4, 3, 29, 227
EFFECT_SCHOOL_DAMAGE, EFFECT_TRIGGER_MISSILE, EFFECT_CREATE_AREATRIGGER = 2, 32, 179
TARGET_UNIT_CASTER, TARGET_CONE = 1, 104
PROC_TAKEN_PERIODIC = 0x80000
# Buff auras a 3.3.5a client and core share with Forever, as Forever's number -> ours. Retail's flat
# armor (674) is the old resistance aura on Physical.
BUFF_AURAS = {13: 13, 22: 22, 29: 29, 34: 34, 85: 85, 99: 99, 124: 124, 135: 135, 161: 161, 180: 180, 290: 290,
              674: 22}
ITEM_SUBCLASS_POTION, ITEM_SUBCLASS_ELIXIR = 1, 2
EFFECT_DUMMY, EFFECT_SUMMON, AURA_PROC_TRIGGER_SPELL, AURA_MOD_STUN = 3, 28, 42, 12
TARGET_DEST_AREA_ENEMY, TARGET_DEST_DEST, TARGET_DEST_CASTER = 16, 87, 18
TRIGGER_ON_EQUIP = 1
STOCK_SPELL_MAX = 80864                  # the 3.3.5a client's last spell: Forever reuses some as they are
# Recipes whose reagents come from Forever's Mount Hyjal (Heavy Thorium, Torbernite, Fel Crystal, Legionite,
# Azerothium, Pitchblende, Death Lotus, Marefoil): they wait for that zone (user 2026-11-06).
WAIT_FOR_HYJAL = {264232, 264234, 264235, 264237}
STAT_IDS = {"Agility": 3, "Strength": 4, "Intellect": 5, "Spirit": 6, "Stamina": 7}
GEAR_CLASSES = {2, 4}                    # weapons and armor: their tooltip numbers go in the gear column
TRIGGER_LEARN = 6
COLUMNS = ["skill", "recipe", "name", "favor", "sides", "learn", "yellow", "grey", "product", "product_name",
           "made", "reagents", "recipe_icon", "product_icon", "product_class", "product_subclass", "item_level",
           "required_level", "stack", "sell", "use", "use_text", "use_aura_text", "gear", "look", "product_quality"] + ID_COLUMNS


def table(folder, name, key="ID", multi=False):
    out = {}
    with open(os.path.join(folder, "w-%s.csv" % name), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = int(r[key])
            if multi:
                out.setdefault(k, []).append(r)
            else:
                out[k] = r
    return out


def icon_names(path, wanted):
    names = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            fid, _, name = line.rstrip("\n").partition(";")
            if fid.isdigit() and int(fid) in wanted:
                names[int(fid)] = os.path.splitext(os.path.basename(name))[0]
    missing = wanted - set(names)
    if missing:
        sys.exit("the listfile has no name for icon file %s" % sorted(missing))
    return names


def sold(sells_path):
    """{recipe item: (Favor, sides)} for the profession's recipes the camps sell for Favor."""
    sells = json.load(open(sells_path))
    found = {}
    for npc, data in sells.items():
        side = "H" if int(npc) in HORDE_VENDORS else "A" if int(npc) in ALLIANCE_VENDORS else None
        for s in data.get("sells", []):
            if s.get("classs") != 9 or side is None:
                continue
            favor = [n for _gold, currencies, _items in s["cost"] for cid, n in currencies if cid == FAVOR_CURRENCY]
            if not favor:
                continue
            item = s["id"]
            prev = found.get(item)
            if prev and prev[0] != favor[0]:
                sys.exit("recipe %d costs %d Favor at one camp and %d at the other" % (item, prev[0], favor[0]))
            found[item] = (favor[0], (prev[1] if prev else set()) | {side})
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wago", required=True, help="folder with the w-<Table>.csv exports")
    ap.add_argument("--sells", required=True, help="the camp NPCs' Wowhead sells lists")
    ap.add_argument("--listfile", required=True, help="community-listfile.csv")
    ap.add_argument("--skill", type=int, required=True, help="SkillLine id, e.g. 185 Cooking")
    ap.add_argument("--cache", help="folder for Wowhead tooltips (gear's armor, damage and stats; needed for gear)")
    args = ap.parse_args()

    sparse, item = table(args.wago, "ItemSparse"), table(args.wago, "Item")
    links = table(args.wago, "ItemXItemEffect", "ItemID", multi=True)
    item_effects = table(args.wago, "ItemEffect")
    effects = table(args.wago, "SpellEffect", "SpellID", multi=True)
    reagents = table(args.wago, "SpellReagents", "SpellID")
    abilities = table(args.wago, "SkillLineAbility", "Spell", multi=True)
    texts, names = table(args.wago, "Spell"), table(args.wago, "SpellName")
    # Each spell's normal-difficulty rows (a spell can have more, for heroic dungeons).
    misc = {k: [r for r in v if r["DifficultyID"] == "0"] or v
            for k, v in table(args.wago, "SpellMisc", "SpellID", multi=True).items()}
    cones = {k: [r for r in v if r["DifficultyID"] == "0"] or v
             for k, v in table(args.wago, "SpellTargetRestrictions", "SpellID", multi=True).items()}
    durations, radii = table(args.wago, "SpellDuration"), table(args.wago, "SpellRadius")
    ranges, aura_options = table(args.wago, "SpellRange"), table(args.wago, "SpellAuraOptions", "SpellID", multi=True)
    appearance_of = table(args.wago, "ItemModifiedAppearance", "ItemID", multi=True)
    appearances, displays = table(args.wago, "ItemAppearance"), table(args.wago, "ItemDisplayInfo")
    model_files = table(args.wago, "ModelFileData", "ModelResourcesID", multi=True)
    texture_files = table(args.wago, "TextureFileData", "MaterialResourcesID", multi=True)
    listfile = {}
    with open(args.listfile, encoding="utf-8", errors="replace") as f:
        for line in f:
            fid, _, name = line.rstrip("\n").partition(";")
            if fid.isdigit():
                listfile[int(fid)] = name

    def spell_reach(spell):
        return int(float(ranges[int(misc[spell][0]["RangeIndex"])]["RangeMax_0"]))

    def tooltip_text(entry):
        if not args.cache:
            sys.exit("item %d needs its Wowhead tooltip: pass --cache" % entry)
        os.makedirs(args.cache, exist_ok=True)
        _name, text = fetch_forever.tooltip(entry, args.cache)
        return text

    def appearance(entry):
        """(Forever's display id, its icon file id) from the item's default appearance."""
        rows_ = sorted(appearance_of.get(entry, []), key=lambda r: int(r.get("OrderIndex") or 0))
        if not rows_:
            return 0, 0
        a = appearances.get(int(rows_[0]["ItemAppearanceID"]), {})
        return int(a.get("ItemDisplayInfoID") or 0), int(a.get("DefaultIconFileDataID") or 0)

    def look(entry):
        """Forever's look: its display id, model and texture names (the client's display with the same
        model and texture stands in when the id is Forever's own)."""
        display, _icon = appearance(entry)
        if not display:
            return ""
        d = displays[display]
        model = texture = ""
        res = int(d.get("ModelResourcesID_0") or 0)
        if res and res in model_files:
            name = os.path.basename(listfile.get(int(model_files[res][0]["FileDataID"]), ""))
            model = re.sub(r"_(..[mf]|.._[mf])\.m2$", "", name, flags=re.I).replace(".m2", "") + ".mdx" if name else ""
        mat = int(d.get("ModelMaterialResourcesID_0") or 0)
        if mat and mat in texture_files:
            texture = os.path.splitext(os.path.basename(listfile.get(int(texture_files[mat][0]["FileDataID"]), "")))[0]
        return "%d|%s|%s" % (display, model, texture)

    def gear(entry):
        """What a weapon's or armor's row needs beyond the tables: Wowhead's tooltip numbers."""
        p, i = sparse[entry], item[entry]
        parts = []
        if int(i["ClassID"]) in GEAR_CLASSES:
            t = tooltip_text(entry)
            m = re.search(r"(\d+) Armor", t)
            if m:
                parts.append("armor=%s" % m.group(1))
            m = re.search(r"(\d+) - (\d+) Damage", t)
            if m:
                parts.append("dmg=%s-%s" % m.groups())
            m = re.search(r"Speed (\d+\.\d+)", t)
            if m:
                parts.append("delay=%d" % round(float(m.group(1)) * 1000))
            stats = ["%d:%s" % (STAT_IDS[s_], v) for v, s_ in re.findall(r"\+(\d+) (Stamina|Strength|Agility|Intellect|Spirit)", t)]
            if stats:
                parts.append("stats=" + ",".join(stats))
            m = re.search(r"Durability \d+ / (\d+)", t)
            if m:
                parts.append("dur=%s" % m.group(1))
            parts += ["inv=%s" % i["InventoryType"], "sheath=%s" % i["SheatheType"], "material=%s" % i["Material"]]
        for key, col in (("bond", "Bonding"), ("maxcount", "MaxCount"), ("totem", "TotemCategoryID")):
            if int(p[col] or 0):
                parts.append("%s=%s" % (key, p[col]))
        if int(p["RequiredSkill"] or 0):
            # Retail's per-expansion skill lines (2941 is Classic Engineering) are the profession here.
            skill = int(p["RequiredSkill"]) if int(p["RequiredSkill"]) < 1000 else args.skill
            parts.append("skill=%d:%s" % (skill, p["RequiredSkillRank"]))
        return " ".join(parts)

    def duration(spell):
        return int(durations[int(misc[spell][0]["DurationIndex"])]["Duration"])

    def radius(e):
        return int(float(radii[int(e["EffectRadiusIndex_0"])]["Radius"]))

    def amount(e):
        return int(float(e["EffectBasePointsF"]))

    def school(spell):
        return int(misc[spell][0]["SchoolMask"])

    def text(spell):
        """Forever's tooltip, in the tokens a 3.3.5a client knows ($w is $s there)."""
        t = texts.get(spell, {})
        out = [t.get(k, "").replace("$w", "$s").replace("$s~", "$s").replace("\r", "").replace("\n", " ")
               for k in ("Description_lang", "AuraDescription_lang")]
        return out

    def check_text(product, kind, both):
        """Kinds whose tooltip is Forever's may use only their own spell's tokens a 3.3.5a client reads."""
        if kind not in ("buff", "cone"):
            return
        for t in both:
            bad = [m for m in re.findall(r"\$[^\s.,;:)%]*", t) if not re.fullmatch(r"\$[sdtmo]\d?", m)]
            if bad:
                sys.exit("item %d: tooltip tokens %s" % (product, bad))

    def item_spells(entry):
        return [item_effects[int(x["ItemEffectID"])] for x in links.get(entry, [])]

    def spell_effects(spell):
        return sorted(effects.get(spell, []), key=lambda e: int(e["EffectIndex"]))

    def use_texts(product):
        uses = item_spells(product)
        return text(int(uses[0]["SpellID"])) if uses else ["", ""]

    def describe_use(product):
        """The product's use, in the terms catalog.py builds it from."""
        uses = item_spells(product)
        if not uses:
            return ""
        if len(uses) != 1:
            sys.exit("item %d has %d use spells" % (product, len(uses)))
        spell = int(uses[0]["SpellID"])
        effs = spell_effects(spell)
        # Forever's "Nutritious Drink": trigger a stock Drink, and after 10 seconds a Well Fed with a stat.
        if len(effs) == 2 and int(effs[0]["Effect"]) == EFFECT_TRIGGER_SPELL \
                and int(effs[1]["EffectAura"]) == AURA_PERIODIC_TRIGGER_SPELL_WITH_VALUE:
            drink = int(effs[0]["EffectTriggerSpell"])
            fed = spell_effects(int(effs[1]["EffectTriggerSpell"]))
            if len(fed) != 1 or int(fed[0]["EffectAura"]) != AURA_MOD_STAT:
                sys.exit("item %d: its Well Fed isn't a single stat" % product)
            stat = int(fed[0]["EffectMiscValue_0"])
            gain = int(float(effs[1]["EffectBasePointsF"]))
            return "drink %d stat %d %d" % (drink, stat, gain)
        kinds = [(int(e["Effect"]), int(e["EffectAura"]), int(e["ImplicitTarget_0"])) for e in effs]
        sub = int(item[product]["SubclassID"])
        # A buff on yourself: an elixir or a potion, every effect an aura we have too.
        if kinds and all(k[0] == EFFECT_APPLY_AURA and k[1] in BUFF_AURAS and k[2] == TARGET_UNIT_CASTER for k in kinds) \
                and sub in (ITEM_SUBCLASS_POTION, ITEM_SUBCLASS_ELIXIR):
            # Retail's armor aura is ours on Physical (school mask 1) whatever its misc says.
            auras = ["%d:%s:%d" % (BUFF_AURAS[int(e["EffectAura"])],
                                   1 if int(e["EffectAura"]) == 674 else e["EffectMiscValue_0"], amount(e)) for e in effs]
            return "buff %s %d %s" % ("elixir" if sub == ITEM_SUBCLASS_ELIXIR else "potion", duration(spell), " ".join(auras))
        # Dragonfire: a hit in a cone in front of you, and a burn on what it hits.
        if kinds == [(EFFECT_SCHOOL_DAMAGE, 0, TARGET_CONE), (EFFECT_APPLY_AURA, AURA_PERIODIC_DAMAGE, TARGET_CONE)]:
            degrees = int(float(cones.get(spell, [{}])[0].get("ConeDegrees") or 0))
            if not degrees:
                sys.exit("item %d: its cone has no width" % product)
            return "cone %d %d %d %d %d %d %d" % (duration(spell), radius(effs[0]), school(spell), amount(effs[0]),
                                                   amount(effs[1]), int(effs[1]["EffectAuraPeriod"]), degrees)
        # Caustic Smog: thrown at the ground, a cloud (an area trigger in Forever) whose damage spell has
        # the potion's name.
        if kinds and kinds[0][0] == EFFECT_TRIGGER_MISSILE:
            cloud = int(effs[0]["EffectTriggerSpell"])
            if [int(e["Effect"]) for e in spell_effects(cloud)] != [EFFECT_CREATE_AREATRIGGER]:
                sys.exit("item %d: the missile doesn't make an area" % product)
            ticks = [sid for sid, n in names.items() if n["Name_lang"] == names[spell]["Name_lang"]
                     and [int(e["EffectAura"]) for e in spell_effects(sid)] == [AURA_PERIODIC_DAMAGE]]
            if len(ticks) != 1:
                sys.exit("item %d: %d damage spells for its cloud" % (product, len(ticks)))
            tick = spell_effects(ticks[0])[0]
            reach = int(float(ranges[int(misc[spell][0]["RangeIndex"])]["RangeMax_0"]))
            return "cloud %d %d %d %d %d %d" % (duration(cloud), radius(effs[0]), school(ticks[0]), amount(tick),
                                                 int(tick["EffectAuraPeriod"]), reach)
        # Venomous Blood: doses on you; each bleed tick you take spreads one to an enemy near you, where
        # it does its damage when it runs out.
        # A satchel: worn, its thrown attacks throw a bomb at the target too.
        if int(uses[0]["TriggerType"]) == TRIGGER_ON_EQUIP:
            if kinds != [(EFFECT_APPLY_AURA, AURA_PROC_TRIGGER_SPELL, TARGET_UNIT_CASTER)]:
                sys.exit("item %d: its equip spell isn't a proc" % product)
            bomb = int(effs[0]["EffectTriggerSpell"])
            m = re.search(r"causing (\d+) to (\d+) (\w+) damage", tooltip_text(product))
            if not m:
                sys.exit("item %d: no bomb damage in its tooltip" % product)
            mask = int(aura_options.get(spell, [{}])[0].get("ProcTypeMask_0") or 0)
            return "satchel %d %d %d %s %s" % (mask, radius(spell_effects(bomb)[0]), school(bomb), m.group(1), m.group(2))
        # A stock spell the client has as it is (Cloaking, Slow Fall, Longsight), with Forever's charges and cooldown.
        if spell <= STOCK_SPELL_MAX:
            return "stock %d %s %s" % (spell, uses[0]["Charges"], uses[0]["CoolDownMSec"])
        # A bomb: Fire damage where it's thrown, maybe a short stun.
        if kinds and kinds[0] == (EFFECT_SCHOOL_DAMAGE, 0, TARGET_DEST_AREA_ENEMY) and len(kinds) <= 2:
            stun = duration(spell) if kinds[1:] == [(EFFECT_APPLY_AURA, AURA_MOD_STUN, TARGET_DEST_AREA_ENEMY)] else 0
            if len(kinds) == 2 and not stun:
                sys.exit("item %d: a bomb's second effect isn't a stun" % product)
            return "bomb %d %d %d %d %d" % (radius(effs[0]), school(spell), amount(effs[0]), stun, spell_reach(spell))
        # The Loot-A-Rang: the module's C++ loots a corpse within range.
        if kinds == [(EFFECT_DUMMY, 0, TARGET_DEST_CASTER)]:
            return "lootarang %d %s" % (spell_reach(spell), uses[0]["CoolDownMSec"])
        # The Compact Critter Carrier: a stable for hunters, set on the ground for a while.
        if kinds == [(EFFECT_SUMMON, 0, TARGET_DEST_DEST)]:
            return "carrier %d %d" % (duration(spell), spell_reach(spell))
        options = aura_options.get(spell, [{}])[0]
        if kinds == [(EFFECT_APPLY_AURA, AURA_DUMMY, TARGET_UNIT_CASTER)] * 2 \
                and int(options.get("ProcTypeMask_0") or 0) == PROC_TAKEN_PERIODIC:
            return "venom %d %s %d %d" % (duration(spell), options["CumulativeAura"], amount(effs[0]), amount(effs[1]))
        sys.exit("item %d: use spell %d isn't a kind this tool knows" % (product, spell))

    rows = []
    for recipe, (favor, sides) in sorted(sold(args.sells).items()):
        rs = sparse[recipe]
        if int(rs["RequiredSkill"]) != args.skill or recipe in WAIT_FOR_HYJAL:
            continue
        taught = [int(e["SpellID"]) for e in item_spells(recipe) if int(e["TriggerType"]) == TRIGGER_LEARN]
        if len(taught) != 1:
            sys.exit("recipe %d teaches %d spells" % (recipe, len(taught)))
        craft = taught[0]
        made = [e for e in spell_effects(craft) if int(e["Effect"]) == EFFECT_CREATE_ITEM]
        if len(made) != 1:
            sys.exit("spell %d makes %d items" % (craft, len(made)))
        # Some of Forever's crafts store 0 for "one".
        product, count = int(made[0]["EffectItemType"]), max(1, int(float(made[0]["EffectBasePointsF"])))
        ability = [a for a in abilities.get(craft, []) if int(a["SkillLine"]) == args.skill]
        if len(ability) != 1:
            sys.exit("spell %d has %d SkillLineAbility rows" % (craft, len(ability)))
        r = reagents[craft]
        parts = ["%s:%s" % (r["Reagent_%d" % i], r["ReagentCount_%d" % i]) for i in range(8) if int(r["Reagent_%d" % i])]
        ps = sparse[product]
        if not int(item[product]["IconFileDataID"]):          # gear: the icon is the appearance's
            item[product]["IconFileDataID"] = appearance(product)[1]
        use = describe_use(product)
        check_text(product, use.split(" ")[0], use_texts(product))
        rows.append({
            "skill": args.skill, "recipe": recipe, "name": rs["Display_lang"], "favor": favor,
            "sides": "both" if sides == {"A", "H"} else {"A": "alliance", "H": "horde"}[next(iter(sides))],
            "learn": rs["RequiredSkillRank"], "yellow": ability[0]["TrivialSkillLineRankLow"],
            "grey": ability[0]["TrivialSkillLineRankHigh"], "product": product, "product_name": ps["Display_lang"],
            "made": count, "reagents": ",".join(parts), "recipe_icon": int(item[recipe]["IconFileDataID"]),
            "product_icon": int(item[product]["IconFileDataID"]), "product_class": item[product]["ClassID"],
            "product_subclass": item[product]["SubclassID"], "item_level": ps["ItemLevel"],
            "required_level": ps["RequiredLevel"], "stack": ps["Stackable"], "sell": ps["SellPrice"],
            "use": use,
            "use_text": use_texts(product)[0], "use_aura_text": use_texts(product)[1],
            "gear": gear(product), "look": look(product), "product_quality": ps["OverallQualityID"],
        })
    if not rows:
        sys.exit("no recipes for skill %d" % args.skill)
    # Every reagent must be something this world has: a stock item, a Scarce material (data/materials.tsv)
    # or what another recipe makes.
    known = {int(r["product"]) for r in rows}
    for path in (OUT, os.path.join(DATA, "materials.tsv")):
        if os.path.exists(path):
            with open(path, newline="", encoding="utf-8") as f:
                known |= {int(r.get("product") or r.get("item")) for r in csv.DictReader(f, delimiter="\t")}
    for r in rows:
        missing = [x for x in r["reagents"].split(",") if int(x.split(":")[0]) > 56806 and int(x.split(":")[0]) not in known]
        if missing:
            sys.exit("recipe %d needs %s, which nothing here gives" % (r["recipe"], missing))
    names = icon_names(args.listfile, {r["recipe_icon"] for r in rows} | {r["product_icon"] for r in rows})
    for r in rows:
        r["recipe_icon"], r["product_icon"] = names[r["recipe_icon"]], names[r["product_icon"]]

    kept, before = [], {}
    if os.path.exists(OUT):
        with open(OUT, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                if int(r["skill"]) != args.skill:
                    kept.append(r)
                else:
                    before[int(r["recipe"])] = r
    gone = set(before) - {r["recipe"] for r in rows}
    if gone:
        sys.exit("recipes %s are no longer sold. Their ids are in players' hands: keep their rows (or move the "
                 "block's next free id past them) before removing anything" % sorted(gone))
    for r in rows:
        for col in ID_COLUMNS:
            r[col] = before.get(r["recipe"], {}).get(col, "")
    assign_ids(rows)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLUMNS, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for r in sorted(kept + rows, key=lambda r: (int(r["skill"]), int(r["recipe"]))):
            w.writerow(r)
    print("wrote %s: %d recipes for skill %d, %d others kept" % (OUT, len(rows), args.skill, len(kept)))


if __name__ == "__main__":
    main()
