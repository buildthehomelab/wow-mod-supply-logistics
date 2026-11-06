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
to take the order, then bring the writ and the goods to the **Contract Coordinator**. As in Forever,
the writ stays in your bags until the hand-in: abandon the order and you can read it again. A writ
can be traded or put on the auction house, one of each at a time (a Sealed Writ never opens into one you hold or have
taken). No profession is needed to fill one: the goods can come from anyone. 146 writs, for Alchemy,
Blacksmithing, Engineering, Leatherworking and Tailoring:

| Tier | Writs | Favor | Reputation |
| --- | --- | --- | --- |
| Apprentice | 18 | 20 | 75 |
| Journeyman | 27 | 20 | 75 |
| Expert | 58 | 35 | 125 |
| Artisan | 43 | 50 | 200 |

The reputation is Forever's own; the tier follows it. Forever calls all its 75-reputation writs
Journeyman; here they split at the skill where the recipe turns yellow (150), so the Sealed
Apprentice's Writ has orders of its own. Forever's writs are dailies; these can be repeated at once.
Left out: Distilled Firewater (Forever's own item), and Goblin Rocket Fuel, Inlaid Mithril Cylinder
and Field Repair Bot 74A: no vendor, drop, trainer or quest teaches their recipes in an AzerothCore
world database (checked with mod-individual-progression installed).

**Odds and ends.** A **Forged Delivery Receipt** (15 Favor) on a crate you can't fill turns it into a
Notarized Shipping Container, worth 50 reputation at the Inventory Intake. A **Forger's Quill** (15
Favor, Honored) rewrites a writ whose order you haven't taken into another of its tier.

**Reputation.** Hand-ins pay your own side's faction only: the Horde races Durotar Supply and
Logistics, the Alliance races the Azeroth Commerce Authority. It sits under Horde or Alliance in the
reputation pane, with no spillover to or from the capitals, from Neutral: 3,000 to Friendly, 6,000 to Honored, 12,000 to Revered, 21,000 to
Exalted (42,000 in all, about 70 Artisan crates). The module pays it itself, so it follows the
server's reputation rates and racial bonuses like any quest reputation.

## What Favor buys

**Merchant's Favor** is a currency item in the Currency tab, per character, under Classic.

| From | Item | Favor | Needs |
| --- | --- | --- | --- |
| Supply Officer | Packmule Treat: the Minimule companion | 1,500 | |
| Supply Officer | Advertising License Application (see below) | 1,200 | Honored |
| Supply Officer | Durotar Supply and Logistics Tabard (Horde), Azeroth Commerce Authority Tabard (Alliance) | 200 | Exalted |
| Kodo Handler (Horde), Mule Handler (Alliance) | Reins of the Pack Kodo: a 100% ground mount | 6,000 | Journeyman Riding |
| Uncertified Scribe | Forger's Quill | 15 | Honored |
| Uncertified Scribe | Forged Delivery Receipt | 15 | |
| Each profession vendor (shown at 300 skill) | Its Certification: the title "the Alchemist", "the Blacksmith", "the Enchanter", "the Engineer", "the Leatherworker" or "the Tailor" | 1,000 | 300 skill |

A **Certification** unlocks its title for every character on the account; a character shows it while
it has 300 skill in the profession, racial bonuses included (checked at login and whenever the skill
changes, so unlearning the profession takes it away). The chef sells
Forever's cooking supplies for coin.

The Pack Kodo, the Minimule (Forever's pack mule), the tabards and the signposts are WoW Forever's own
art, converted for 3.3.5a (see The client patch, below). As in Forever, both sides ride the Pack Kodo.

**The Advertising License.** The application starts "Sign Me Up!" and comes with a Massive Pile of
Forms. Use the pile to sign them (10 seconds), then bring the completed forms and the application to the
**Contract Coordinator**. The reward is a **Tradeskill Signpost**: Orcish for the Horde, Dwarven for the
Alliance, kept in your bags (30 minutes' cooldown). Using it puts the signpost up in front of you for a
minute; talk to it and pick one of your professions (Alchemy, Blacksmithing, Cooking, Enchanting,
Engineering, Leatherworking or Tailoring), and that profession's sign stands there for half an hour.
Only the one who put it up can choose, and a new sign takes your last one down.

**Not yet:** the 316 recipes the profession vendors sell for Favor in Forever (the prices are already
in the extended costs).

## Install

1. `git clone https://github.com/buildthehomelab/wow-mod-supply-logistics.git mod-supply-logistics`
   in your server's `modules` folder (the folder name sets the loader symbol), then rebuild.
2. The SQL in `data/sql` applies itself at the next start: `db-world` (items, quests, vendors, the
   module's tables, and the client tables' server copies in `mod_supply_logistics_dbc.sql`) and
   `db-characters` (the account titles).
3. **The client patch.** Players need the same spells, items, factions, titles, currency and prices,
   or the items show question marks, nothing can be used, prices are blank and the reputation and
   titles don't show. Add them to the patch that carries your realm's `Spell.dbc`, `SpellIcon.dbc`, `Item.dbc`,
   `ItemDisplayInfo.dbc`, `SkillLineAbility.dbc` and `ItemExtendedCost.dbc`:

   ```bash
   python3 tools/build_patch.py --patch your-spell-patch.MPQ --client /path/to/3.3.5a/client \
       --out new/your-spell-patch.MPQ --sql data/sql/db-world/mod_supply_logistics_dbc.sql
   ```

   It needs StormLib (`STORMLIB`, default `/usr/local/lib/libstorm.dylib`). The `--sql` output is the
   committed file; write it again only if you change `tools/catalog.py`.

   The models, the tabards' textures and the icons the client lacks come from WoW Forever's own build,
   in a patch of their own with the CreatureDisplayInfo.dbc and CreatureModelData.dbc rows they need:

   ```bash
   python3 tools/build_art.py --creatures /path/to/wow-mod-retail-creatures --cache /path/to/forever-cache \
       --dbc /path/to/creature-dbcs --client /path/to/3.3.5a/client --work /tmp/art --out new/your-art-patch.MPQ
   ```

   It runs [wow-mod-retail-creatures](https://github.com/buildthehomelab/wow-mod-retail-creatures)' converter
   on this repo's `pack.json` and `data/looks.tsv`, reading Forever's files from Blizzard's CDN. `--dbc`
   holds the CreatureDisplayInfo.dbc, CreatureModelData.dbc, AnimationData.dbc and ParticleColor.dbc your
   players have (from the patch that ships them last, if any), and the art patch has to load after that
   one. Ship it with the module's SQL: the Minimule and both mounts use its looks.
   `data/sql/db-world/mod_supply_logistics_art.sql` is its server copy; write it again only if you
   change `data/looks.tsv`.
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
| `tools/build_art.py`, `pack.json`, `data/looks.tsv` | Converts Forever's models and adds the tabards' textures and icons: the art patch and its server copy |
| `tools/fetch_forever.py` | Rebuilds `data/*.tsv` from Forever's public data, for a newer Forever build |

## Ids

Forever's own ids where Forever has the thing: items 248682-248773, 262764-262917, 264011-264160,
270868-270897, 271621-271627 and 284664; quests 91899-91907, 93862, 94004-94360, 95816 and 95819;
creatures 262713-262734 (the signposts and signs); factions 2586 and 2587; currency 3402. Its own: items,
spells, spell icons, item displays and extended costs 90740-90759 (Merchant's Favor is 90740: the server
indexes currencies by item id, so keep it low); creatures 9531100-9531109 and npc_text 9531100-9531105;
creature displays and models 95310-95339; titles 193-198 (title bits 158-163); reputation indexes 108 and
109; currency bit 33.

`build_patch.py` takes Faction.dbc and CharTitles.dbc from your patch when it has them, and
CurrencyTypes.dbc from the client otherwise: if another of your patches ships its own copy of one of
these, build on that copy, or the patch loaded last hides the other's rows.

## Requirements

AzerothCore 3.3.5a. With [mod-playerbots](https://github.com/mod-playerbots/mod-playerbots), bots
get no crates or writs. Python 3 and StormLib for the client patch; for the art patch also a checkout of
wow-mod-retail-creatures (with its `model_fdid` looks) and network access to Blizzard's CDN and
wago.tools.

## Credits

- WoW Forever's Supply and Logistics, its names, text, models and textures belong to Blizzard
  Entertainment. The art patch is built from Blizzard's own files; none are in this repo.
- `data/writs.tsv` uses data from [Efficient Games](https://efficient.games)' EG Link output,
  licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Changed: the Craftsman's
  Writs, filtered and tiered, with the 3.3.5a recipe that makes each item.
- The crates' bundles come from Wowhead's WoW Forever tooltips, item ids from
  [Polestar](https://github.com/fitzforge/polestar)'s item names.
- Icon glyph from [Tabler Icons](https://tabler.io/icons) (MIT).

## License

MIT for the code and tools. `data/writs.tsv` is CC BY 4.0, as above.
