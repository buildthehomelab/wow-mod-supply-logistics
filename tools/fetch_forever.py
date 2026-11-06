#!/usr/bin/env python3
"""Rebuilds data/crates.tsv, data/bundles.tsv and data/writs.tsv from WoW Forever's public data.

    python3 fetch_forever.py --eg <eg-link-output-wowf>/data/wowf/1.60.1.70790 \\
        --items <polestar>/data/item.jsonl --client /path/to/3.3.5a/client [--cache folder]

- Crates and their bundles: Wowhead's Forever item tooltips (nether.wowhead.com/forever/tooltip/item/<id>),
  which list every bundle a crate takes ("Fill the crate with any bundle from the following list").
- Writs: Efficient Games' EG Link output (CC BY 4.0), quests.enUS.json: each Craftsman's Writ quest,
  the item it asks for and the reputation it pays (the override is reputation x 100).
- Reagent and crafted item ids: the names in fitzforge/polestar's item.jsonl, which are Blizzard's own.
- A writ's professions and skill: the 3.3.5a client's Spell.dbc and SkillLineAbility.dbc, from the
  spells that create its item (skill2: a second profession with a recipe for it, or 0). Its tier (1 Apprentice to 4 Artisan) follows the reputation Forever pays
  for it (see writ_tier).

Only needed to refresh the data from a newer Forever build: the TSVs are committed. Needs Python 3,
StormLib for the client's tables (see dbcmpq.py) and network access for Wowhead.
"""

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dbcmpq  # noqa: E402

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

# Waylaid Crates: Forever's item ids. Herbs, Ore, Textiles and Curiosities hold gathered goods,
# Fabrics, Ingots and Parts crafted ones (which pay more).
CRATES = list(range(248682, 248700)) + list(range(248702, 248714))
CRAFTED = ("Fabrics", "Ingots", "Parts")
TIERS = {"Apprentice": 1, "Journeyman": 2, "Expert": 3, "Artisan": 4}
# Names polestar lists more than once: the one every recipe and vein uses.
NAME_OVERRIDES = {"Dark Iron Ore": 11370}
# Writ items Forever made for itself have no 3.3.5a recipe, so those writs are left out.
SKILLS = {171: "Alchemy", 164: "Blacksmithing", 202: "Engineering", 165: "Leatherworking", 197: "Tailoring"}
# Items a 3.3.5a recipe makes but nobody can learn it on an AzerothCore world database: no vendor,
# drop, trainer or quest teaches the recipe (checked 2026-11-05, with mod-individual-progression).
# A writ for one would be an order no player can fill, so it is left out too.
NOT_CRAFTABLE = {
    9060: "Plans: Inlaid Mithril Cylinder (10713) has no source",
    9061: "Recipe: Goblin Rocket Fuel (10644) has no source",
    18232: "Schematic: Field Repair Bot 74A (18235) teaches no spell and no trainer has it",
}
# polestar has Classic Era names; these items are named differently on a 3.3.5a server, and the
# writ and its quest should use the name the player sees on the item.
REALM_NAMES = {3388: "Strong Troll's Blood Elixir", 18645: "Gnomish Alarm-o-Bot"}
# A writ's tier follows Forever's three reputation rewards: 200 Artisan, 125 Expert, and 75 split
# into Apprentice and Journeyman at the skill where the recipe turns yellow.
JOURNEYMAN_FROM = 150


def writ_tier(rep, yellow):
    if rep >= 200:
        return 4
    if rep >= 125:
        return 3
    return 2 if yellow >= JOURNEYMAN_FROM else 1


def tooltip(item, cache):
    path = os.path.join(cache, "item_%d.json" % item)
    if not os.path.exists(path):
        url = "https://nether.wowhead.com/forever/tooltip/item/%d?dataEnv=0&locale=0" % item
        req = urllib.request.Request(url, headers={"User-Agent": "mod-supply-logistics fetch_forever.py"})
        with urllib.request.urlopen(req, timeout=30) as r, open(path, "wb") as f:
            f.write(r.read())
        time.sleep(0.3)
    data = json.load(open(path))
    text = re.sub(r"<br ?/?>", "\n", data.get("tooltip", ""))
    return data["name"], html.unescape(re.sub(r"<[^>]+>", "", text))


def item_ids(path):
    ids = {}
    for line in open(path):
        row = json.loads(line)
        ids.setdefault(row["name"], row["id"])
    ids.update(NAME_OVERRIDES)
    return ids


def crates(cache, ids):
    crate_rows, bundle_rows = [], []
    for item in CRATES:
        name, text = tooltip(item, cache)
        m = re.match(r"Waylaid Crate: (?:Earthly |Flowering )?(\w+) (\w+)$", name)
        if not m or m.group(1) not in TIERS:
            sys.exit("unexpected crate name %r" % name)
        level = int(re.search(r"Requires Level (\d+)", text).group(1))
        group = "crafted" if m.group(2) in CRAFTED else "gathered"
        crate_rows.append((item, TIERS[m.group(1)], group, m.group(2).lower(), level, name))
        bundles = re.findall(r"^- (\d+) (.+)$", text, re.M)
        if not bundles:
            sys.exit("%d lists no bundles" % item)
        for slot, (count, reagent) in enumerate(bundles):
            reagent = reagent.strip()
            if reagent not in ids:
                sys.exit("no item named %r (crate %d)" % (reagent, item))
            bundle_rows.append((item, slot, ids[reagent], int(count), reagent))
    return crate_rows, bundle_rows


def writs(eg, client, ids_by_name):
    tmp = os.path.join(DATA, "..", "tools", ".client")
    os.makedirs(tmp, exist_ok=True)
    tables = {}
    for name in ("Spell", "SkillLineAbility"):
        dst = os.path.join(tmp, name + ".dbc")
        if not os.path.exists(dst):
            dbcmpq.client_file(client, "enUS", "DBFilesClient\\%s.dbc" % name, dst)
        tables[name] = dbcmpq.read_dbc(dst)[0]
    creates = {}
    for r in tables["Spell"]:
        for e in range(3):
            if r[71 + e] == 24 and r[107 + e]:      # SPELL_EFFECT_CREATE_ITEM, EffectItemType
                creates.setdefault(r[107 + e], []).append(r[0])
    skill_of = {}
    for r in tables["SkillLineAbility"]:
        skill_of.setdefault(r[2], (r[1], r[11]))    # SkillLine, TrivialSkillLineRankLow (yellow)
    names = {v: k for k, v in ids_by_name.items()}
    quests = json.load(open(os.path.join(eg, "quests.enUS.json")))["quests"]
    rows, skipped = [], []
    for quest_id, q in quests.items():
        if not q["title"].startswith("Craftsman's Writ: "):
            continue
        writ = [o for o in q["objectives"] if 264000 <= o["objectId"] < 265000]
        made = [o for o in q["objectives"] if not 264000 <= o["objectId"] < 265000]
        if len(writ) != 1 or len(made) != 1:
            sys.exit("quest %s has objectives %r" % (quest_id, q["objectives"]))
        item = made[0]["objectId"]
        # Every profession with a recipe for it (Gordok Ogre Suit: Tailoring and Leatherworking).
        # In the client's spell order; the first is the writ's own.
        skills = list(dict.fromkeys(skill_of[s] for s in creates.get(item, []) if s in skill_of and skill_of[s][0] in SKILLS))
        if not skills:
            skipped.append((quest_id, q["title"], "no 3.3.5a recipe makes its item"))
            continue
        if item in NOT_CRAFTABLE:
            skipped.append((quest_id, q["title"], NOT_CRAFTABLE[item]))
            continue
        rep = q["rewards"]["reputation"][0]["override"] // 100
        tier = writ_tier(rep, skills[0][1])
        name = REALM_NAMES.get(item) or names.get(item, q["title"][len("Craftsman's Writ: "):])
        rows.append((int(quest_id), writ[0]["objectId"], item, made[0]["amount"], skills[0][0],
                     skills[1][0] if len(skills) > 1 else 0, skills[0][1], tier, rep, name))
    rows.sort(key=lambda r: r[1])
    for quest_id, title, why in skipped:
        print("left out %s %s: %s" % (quest_id, title, why))
    return rows


def write(name, header, rows):
    with open(os.path.join(DATA, name), "w") as f:
        f.write("\t".join(header) + "\n")
        for r in rows:
            f.write("\t".join(str(v) for v in r) + "\n")
    print("%s: %d rows" % (name, len(rows)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--eg", required=True, help="an EG Link build folder with quests.enUS.json")
    ap.add_argument("--items", required=True, help="polestar's data/item.jsonl")
    ap.add_argument("--client", required=True, help="a 3.3.5a client folder")
    ap.add_argument("--cache", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".wowhead"))
    args = ap.parse_args()
    os.makedirs(args.cache, exist_ok=True)
    ids = item_ids(args.items)
    crate_rows, bundle_rows = crates(args.cache, ids)
    write("crates.tsv", ["item", "tier", "group", "kind", "level", "name"], crate_rows)
    write("bundles.tsv", ["crate", "slot", "reagent", "count", "name"], bundle_rows)
    write("writs.tsv", ["quest", "writ", "item", "count", "skill", "skill2", "yellow", "tier", "rep", "name"],
          writs(args.eg, args.client, ids))


if __name__ == "__main__":
    main()
