#!/usr/bin/env python3
"""Rebuilds data/materials.tsv: WoW Forever's Scarce materials and what alchemists and engineers make
from them, which the camps' recipes ask for.

    python3 fetch_materials.py --wago <folder> --listfile <community-listfile.csv>

- The items (name, quality, level, stack, price, icon) and the crafts' reagents: Forever's client tables
  for build 1.60.1.70790 from wago.tools (w-<Table>.csv): ItemSparse, Item, SpellEffect, SpellReagents.
- Where they come from: Forever gives a Scarce material as a bonus with ordinary gathering. Wowhead's
  player data (2026-11-05) shows Pyrite from Copper, Tin, Silver and Iron veins, Bauxite from Gold and
  Mithril, Frilled Lichen from Earthroot, Mageroyal, Briarthorn, Bruiseweed, Stranglekelp, Wild
  Steelbloom and Kingsblood, at 0.1-0.5% a gather. Rosecap, Stranglevine and the Pristine leathers have
  no public numbers: SOURCES puts them by level, as the items' own levels (25, 45, 60) do. CHANCE is
  1-1.5%, the user's "about three times Forever's" (2026-11-05): two to ten times Wowhead's numbers.
- How the crafts are learned: Forever's trainers (Wowhead's spell pages: skill, cost, colours), in
  TRAINER. Viridian Dye also needs Forever's Fermenter camp object, which a 3.3.5a world has not.

The ids the module gives (craft spells, displays) are kept from the file's previous version.

Released under the MIT License.
"""

import argparse
import csv
import os
import sys

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
OUT = os.path.join(DATA, "materials.tsv")
BLOCK = (91950, 50)                      # craft spells (and their SkillLineAbility), displays
CHANCE = {"ore": 1.0, "herb": 1.5, "skin": 1.5}

LOW_HERBS = ["Earthroot", "Mageroyal", "Briarthorn", "Bruiseweed", "Stranglekelp", "Wild Steelbloom", "Kingsblood"]
MID_HERBS = ["Liferoot", "Fadeleaf", "Goldthorn", "Khadgar's Whisker", "Wintersbite", "Grave Moss"]
HIGH_HERBS = ["Firebloom", "Purple Lotus", "Arthas' Tears", "Sungrass", "Blindweed", "Ghost Mushroom", "Gromsblood",
              "Golden Sansam", "Dreamfoil", "Mountain Silversage", "Plaguebloom", "Icecap", "Black Lotus"]
# item: (kind, sources): node names, or the skinned creature's level range.
SOURCES = {
    249391: ("ore", ["Copper Vein", "Tin Vein", "Silver Vein", "Ooze Covered Silver Vein", "Iron Deposit",
                     "Ooze Covered Iron Deposit"]),  # Pyrite
    249425: ("ore", ["Gold Vein", "Ooze Covered Gold Vein", "Mithril Deposit", "Ooze Covered Mithril Deposit"]),  # Bauxite
    249399: ("herb", LOW_HERBS),                 # Frilled Lichen
    249424: ("herb", MID_HERBS),                 # Rosecap
    249274: ("herb", HIGH_HERBS),                # Stranglevine
    249427: ("skin", ["10-29"]),                 # Pristine Leather
    249428: ("skin", ["30-44"]),                 # Pristine Hide
    249429: ("skin", ["45-255"]),                # Pristine Scale: 45 and up
}
# craft spell: (skill, learned at, trainer cost in copper, yellow, grey), from Wowhead.
TRAINER = {
    1249630: (171, 40, 150, 50, 90),             # Cerulean Dye
    1249631: (171, 120, 1500, 130, 155),         # Magenta Dye
    1249632: (171, 215, 10000, 230, 270),        # Viridian Dye
    1249633: (171, 40, 150, 50, 90),             # Sulfuric Acid
    1249634: (202, 120, 500, 130, 155),          # Sandpaper
    1266917: (202, 215, 0, 215, 220),            # SAF-T Casing: Wowhead shows no cost; Forever's needs an anvil
}
COLUMNS = ["item", "name", "cls", "subclass", "quality", "item_level", "stack", "sell", "material", "icon",
           "description", "kind", "sources", "chance", "skill", "learn", "cost", "yellow", "grey", "reagents",
           "craft", "display"]


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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wago", required=True)
    ap.add_argument("--listfile", required=True)
    args = ap.parse_args()

    sparse, item = table(args.wago, "ItemSparse"), table(args.wago, "Item")
    reagents = table(args.wago, "SpellReagents", "SpellID")
    made = {}
    for e in table(args.wago, "SpellEffect", "SpellID", multi=True).values():
        for x in e:
            if x["Effect"] == "24" and int(x["SpellID"]) in TRAINER:
                made[int(x["SpellID"])] = int(x["EffectItemType"])
    if set(made) != set(TRAINER):
        sys.exit("Forever's tables lack crafts %s" % sorted(set(TRAINER) - set(made)))

    rows = []
    for entry, (kind, sources) in SOURCES.items():
        rows.append(dict(item=entry, kind=kind, sources=";".join(sources), chance=CHANCE[kind]))
    for spell, (skill, learn, cost, yellow, grey) in TRAINER.items():
        r = reagents[spell]
        parts = ["%s:%s" % (r["Reagent_%d" % i], r["ReagentCount_%d" % i]) for i in range(8) if int(r["Reagent_%d" % i])]
        rows.append(dict(item=made[spell], kind="craft", sources="", chance="", skill=skill, learn=learn, cost=cost,
                         yellow=yellow, grey=grey, reagents=",".join(parts)))
    for r in rows:
        p, i = sparse[r["item"]], item[r["item"]]
        r.update(name=p["Display_lang"], cls=i["ClassID"], subclass=i["SubclassID"], quality=p["OverallQualityID"],
                 item_level=p["ItemLevel"], stack=p["Stackable"], sell=p["SellPrice"], material=i["Material"],
                 icon=int(i["IconFileDataID"]), description=p["Description_lang"])
    want = {r["icon"] for r in rows}
    names = {}
    with open(args.listfile, encoding="utf-8", errors="replace") as f:
        for line in f:
            fid, _, name = line.rstrip("\n").partition(";")
            if fid.isdigit() and int(fid) in want:
                names[int(fid)] = os.path.splitext(os.path.basename(name))[0]
    if want - set(names):
        sys.exit("the listfile has no name for icon files %s" % sorted(want - set(names)))
    for r in rows:
        r["icon"] = names[r["icon"]]

    # Ids: kept from the previous file, new ones after the highest in the block.
    before = {}
    if os.path.exists(OUT):
        with open(OUT, newline="", encoding="utf-8") as f:
            before = {int(r["item"]): r for r in csv.DictReader(f, delimiter="\t")}
    base, size = BLOCK
    crafts = {int(b["craft"]) for b in before.values() if b.get("craft")}
    displays = {b["icon"]: int(b["display"]) for b in before.values() if b.get("display")}

    def next_free(used):
        n = max([x for x in used if base <= x < base + size] or [base - 1]) + 1
        if n >= base + size:
            sys.exit("the materials outgrew their block")
        used.add(n)
        return n

    for r in rows:
        old = before.get(r["item"], {})
        if r["kind"] == "craft":
            r["craft"] = old.get("craft") or next_free(crafts)
        else:
            r["craft"] = ""
    used = set(displays.values())
    for r in rows:
        if r["icon"] not in displays:
            displays[r["icon"]] = next_free(used)
        r["display"] = displays[r["icon"]]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLUMNS, delimiter="\t", lineterminator="\n", restval="")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("wrote %s: %d materials" % (OUT, len(rows)))


if __name__ == "__main__":
    main()
