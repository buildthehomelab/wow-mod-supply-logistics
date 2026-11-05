# Supply and Logistics

An [AzerothCore](https://www.azerothcore.org/) (WotLK 3.3.5a) module that brings WoW Forever's
**Supply and Logistics** to a 3.3.5a server: Waylaid Crates and Sealed Writs that drop in the open
world, the **Merchant's Favor** currency, and two trade reputations, **Durotar Supply and
Logistics** for the Horde and the **Azeroth Commerce Authority** for the Alliance.

## How it plays

**Waylaid Crates.** Any open-world mob worth experience to you has a 4% chance to drop one. Each
player the kill rewards rolls on their own (a group's members in range too), at any level, so capped
characters get them as well. The mob's level sets the tier, capped at what you can open (Expert from
level 20, Artisan from 35):

| Mob level | Crate | Takes, for example |
| --- | --- | --- |
| 10-19 | Apprentice | 20 Peacebloom, or 20 Copper Ore, or 40 Linen Cloth |
| 20-29 | Journeyman | 10 Kingsblood, or 20 Iron Ore, or 20 Medium Leather |
| 30-39 | Expert | 20 Mithril Ore, or 40 Mageweave Cloth, or 20 Vision Dust |
| 40 and up | Artisan | 20 Thorium Ore, or 40 Runecloth, or 20 Dream Dust |

There are 30 crates: Herbs, Ore, Textiles and Curiosities hold gathered goods; Fabrics, Ingots and
Parts hold crafted ones. Half the time the crate is one that fits your professions (herbs for a
herbalist or alchemist, parts for an engineer, and so on). Bags full: it comes by mail.

**Filling and handing in.** Use a crate and pick one bundle from its label. The goods go in and it
becomes a **Sealed crate**, which the **Inventory Intake** at your faction's trade camp takes:

| Sealed crate | Favor | Reputation | Crafted (Fabrics, Ingots, Parts) |
| --- | --- | --- | --- |
| Apprentice | 20 | 150 | 30 Favor, 225 reputation |
| Journeyman | 35 | 250 | 52, 375 |
| Expert | 60 | 400 | 90, 600 |
| Artisan | 90 | 600 | 135, 900 |
| Elite | 200 | 1,000 | |

**Elite crates** come sealed: a dungeon or raid boss of level 30 or more gives each player there one
10% of the time, the dead included. Each Sealed crate handed in has a 25% chance to bring a Sealed Writ of its tier.

**Writs.** Mobs also drop **Sealed Writs** (1%, by the mob's level, uncapped: any opens from level 10). Opening one gives a **Craftsman's
Writ**, a customer's order for a crafted item, leaning towards your own crafting professions. Read it
to take the order (the writ is used up, and lost if you abandon the order), then bring the goods to the **Contract Coordinator**. 149 writs, for Alchemy, Blacksmithing,
Engineering, Leatherworking and Tailoring:

| Tier | Writs | Favor | Reputation |
| --- | --- | --- | --- |
| Apprentice | 18 | 20 | 75 |
| Journeyman | 27 | 20 | 75 |
| Expert | 60 | 35 | 125 |
| Artisan | 44 | 50 | 200 |

The reputation is Forever's own; the tier follows it (75 splits at the skill where the recipe turns
yellow, 150).

**Odds and ends.** A **Forged Delivery Receipt** (15 Favor) on a crate you can't fill turns it into a
Notarized Shipping Container, worth 50 reputation at the Inventory Intake. A **Forger's Quill** (15
Favor, Honored) rewrites a writ you haven't taken yet into another of its tier.

**Reputation.** Hand-ins pay your own side's faction only: the Horde races Durotar Supply and
Logistics, the Alliance races the Azeroth Commerce Authority. It sits under Horde or Alliance in the
reputation pane, with no spillover to or from the capitals, from Neutral: 3,000 to Friendly, 6,000 to Honored, 12,000 to Revered, 21,000 to
Exalted (42,000 in all, about 70 Artisan crates). The module pays it itself, so it follows the
server's reputation rates and racial bonuses like any quest reputation.

## What Favor buys

**Merchant's Favor** is a currency item in the Currency tab, per character, under Classic.

| From | Item | Favor | Needs |
| --- | --- | --- | --- |
| Supply Officer | Packmule Treat: the Minimule companion | 1,500 | Revered |
| Kodo Handler (Horde) | Reins of the Pack Kodo: a 100% ground mount | 6,000 | Exalted, Journeyman Riding |
| Mule Handler (Alliance) | Reins of the Pack Mule: a 100% ground mount | 6,000 | Exalted, Journeyman Riding |
| Uncertified Scribe | Forger's Quill | 15 | Honored |
| Uncertified Scribe | Forged Delivery Receipt | 15 | |
| Each profession vendor (shown at 300 skill) | Its Certification: the title "the Alchemist", "the Blacksmith", "the Enchanter", "the Engineer", "the Leatherworker" or "the Tailor" | 1,000 | 300 skill |

A **Certification** unlocks its title for every character on the account; a character shows it while
it has 300 skill in the profession, racial bonuses included (checked at login and whenever the skill
changes, so unlearning the profession takes it away). The chef sells
Forever's cooking supplies for coin.

**Not yet:** the 316 recipes the profession vendors sell for Favor in Forever (the prices are already
in the extended costs), the two tabards and the Advertising License (a shop-sign toy), which need
their art.

## Install

1. `git clone https://github.com/buildthehomelab/wow-mod-supply-logistics.git mod-supply-logistics`
   in your server's `modules` folder (the folder name sets the loader symbol), then rebuild.
2. The SQL in `data/sql` applies itself at the next start: `db-world` (items, quests, vendors, the
   module's tables, and the client tables' server copies in `mod_supply_logistics_dbc.sql`) and
   `db-characters` (the account titles).
3. **The client patch.** Players need the same spells, items, factions, titles, currency and prices,
   or the items show question marks, nothing can be used, prices are blank and the reputation and
   titles don't show. Add them to the patch that carries your realm's `Spell.dbc` and `Item.dbc`:

   ```bash
   python3 tools/build_patch.py --patch your-spell-patch.MPQ --client /path/to/3.3.5a/client \
       --out new/your-spell-patch.MPQ --sql data/sql/db-world/mod_supply_logistics_dbc.sql
   ```

   It needs StormLib (`STORMLIB`, default `/usr/local/lib/libstorm.dylib`). The `--sql` output is the
   committed file; write it again only if you change `tools/catalog.py`.
4. **The NPCs.** The module gives Forever's camp NPCs their jobs, but doesn't spawn them: create and
   spawn these creature entries with your own SQL, wherever your trade camps are. With
   `SupplyLogistics.CampNpcFlags = 1` the module adds their quest giver and vendor flags to their
   templates at startup and again when they spawn, so `npcflag` in your SQL can stay 0. Leave the
   spawns' own `creature.npcflag` at 0 too: a non-zero one replaces the template's at respawn.

| Job | Horde | Alliance |
| --- | --- | --- |
| Inventory Intake: Sealed crates, empty containers | 256386 | 256390 |
| Contract Coordinator: writs | 256388 | 256391 |
| Supply Officer | 256384 | 256389 |
| Kodo / Mule Handler | 256400 | 256736 |
| Uncertified Scribe | 256672 | 256742 |
| Alchemist, Blacksmith, Chef, Enchanter, Engineer, Leatherworker, Tailor | 248196-248202 | 256729-256735 |

To remove it: `data/sql/uninstall/`, by hand.

## Configuration

`conf/mod_supply_logistics.conf.dist`: the drop chances (`Crate.Chance`, `Writ.Chance`,
`Writ.HandInChance`, `Elite.Chance`), the lowest level (`MinLevel`, `Elite.MinLevel`), how much drops
lean towards your professions (`ProfessionWeight`), and `CampNpcFlags`. Favor and reputation per
hand-in are in `tools/catalog.py`; change them there and run `tools/build_data.py`.

## Tools

| File | Does |
| --- | --- |
| `tools/catalog.py` | Every id, item, spell, price and payout, for both builders |
| `tools/build_data.py` | Writes the world SQL and the uninstall SQL |
| `tools/build_patch.py` | Adds the client rows to a patch and writes their server copy |
| `tools/fetch_forever.py` | Rebuilds `data/*.tsv` from Forever's public data, for a newer Forever build |

## Ids

Forever's own ids where Forever has the thing: items 248682-248773, 262764-262917, 264011-264160,
271621-271627 and 284664; quests 91899-91907, 93862 and 94004-94360; factions 2586 and 2587; currency
3402. Its own: items, spells and extended costs 90740-90759 (Merchant's Favor is 90740: the server
indexes currencies by item id, so keep it low); creatures 9531100-9531101 and npc_text 9531100-9531102;
titles 193-198 (title bits 158-163); reputation indexes 108 and 109; currency bit 33.

`build_patch.py` takes Faction.dbc and CharTitles.dbc from your patch when it has them, and
CurrencyTypes.dbc from the client otherwise: if another of your patches ships its own copy of one of
these, build on that copy, or the patch loaded last hides the other's rows.

## Requirements

AzerothCore 3.3.5a. With [mod-playerbots](https://github.com/mod-playerbots/mod-playerbots), bots
get no crates or writs. Python 3 and StormLib for the client patch.

## Credits

- WoW Forever's Supply and Logistics, its names and text belong to Blizzard Entertainment.
- `data/writs.tsv` uses data from [Efficient Games](https://efficient.games)' EG Link output,
  licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Changed: the Craftsman's
  Writs, filtered and tiered, with the 3.3.5a recipe that makes each item.
- The crates' bundles come from Wowhead's WoW Forever tooltips, item ids from
  [Polestar](https://github.com/fitzforge/polestar)'s item names.
- Icon glyph from [Tabler Icons](https://tabler.io/icons) (MIT).

## License

MIT for the code and tools. `data/writs.tsv` is CC BY 4.0, as above.
