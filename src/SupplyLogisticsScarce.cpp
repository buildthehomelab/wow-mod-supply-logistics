/*
 * mod-supply-logistics: Scarce materials, WoW Forever's bonus drops with gathering and skinning.
 *
 * The table mod_supply_logistics_scarce names, for each material, the gathering nodes (by name) or
 * the skinned creatures' levels it comes with. When a real player's loot is filled from a node of
 * those names, or from skinning a creature of those levels (by leather, not herbs, ore or parts), each
 * material rolls its chance and joins the loot. Loot tables themselves are not changed, so other
 * modules' loot SQL can't drop them, a loot reload doesn't lose them, and bots get none (as with the
 * crates).
 *
 * Released under the MIT License.
 */

#include "SupplyLogistics.h"

#include "Config.h"
#include "Creature.h"
#include "DatabaseEnv.h"
#include "GameObject.h"
#include "Log.h"
#include "ObjectAccessor.h"
#include "LootMgr.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Random.h"

#include <unordered_map>
#include <unordered_set>

namespace SupplyLogistics
{
    namespace
    {
        enum ScarceKind : uint8
        {
            SCARCE_NODE = 1,
            SCARCE_SKIN = 2,
        };

        struct Drop
        {
            uint32 item;
            float chance;
        };

        struct Band
        {
            uint8 low, high;
            Drop drop;
        };

        // By gathering node entry (names resolved at startup; a loot reload doesn't change them), and
        // by the skinned creature's level, read at loot time.
        std::unordered_map<uint32, std::vector<Drop>> nodeDrops;
        std::vector<Band> skinBands;
        float rate = 1.0f;

        constexpr uint32 OTHER_SKINNING = CREATURE_TYPE_FLAG_SKIN_WITH_HERBALISM | CREATURE_TYPE_FLAG_SKIN_WITH_MINING
            | CREATURE_TYPE_FLAG_SKIN_WITH_ENGINEERING;

        void Roll(Loot* loot, Drop const& d)
        {
            if (roll_chance_f(d.chance * rate))
                loot->AddItem(LootStoreItem(d.item, 0, 100.0f, false, LOOT_MODE_DEFAULT, 0, 1, 1));
        }
    }

    void LoadScarceConfig()
    {
        rate = std::max(0.0f, sConfigMgr->GetOption<float>("SupplyLogistics.Scarce.Rate", 100.0f)) / 100.0f;
    }

    void LoadScarce()
    {
        nodeDrops.clear();
        skinBands.clear();

        std::unordered_map<std::string, std::vector<Drop>> byNode;
        if (QueryResult result = WorldDatabase.Query("SELECT item, kind, node, min_level, max_level, chance FROM mod_supply_logistics_scarce"))
            do
            {
                Field* f = result->Fetch();
                uint32 item = f[0].Get<uint32>();
                if (!sObjectMgr->GetItemTemplate(item))
                {
                    LOG_ERROR("module", "mod-supply-logistics: Scarce material {} is not an item", item);
                    continue;
                }
                Drop drop{ item, f[5].Get<float>() };
                if (f[1].Get<uint8>() == SCARCE_NODE)
                    byNode[f[2].Get<std::string>()].push_back(drop);
                else
                    skinBands.push_back({ f[3].Get<uint8>(), f[4].Get<uint8>(), drop });
            } while (result->NextRow());

        std::unordered_set<std::string> found;
        for (auto const& [entry, go] : *sObjectMgr->GetGameObjectTemplates())
        {
            auto itr = byNode.find(go.name);
            if (itr == byNode.end() || go.type != GAMEOBJECT_TYPE_CHEST || !go.GetLootId()
                || !LootTemplates_Gameobject.HaveLootFor(go.GetLootId()))
                continue;
            found.insert(go.name);
            nodeDrops[entry] = itr->second;
        }
        for (auto const& [name, _drops] : byNode)
            if (!found.count(name))
                LOG_ERROR("module", "mod-supply-logistics: no gathering node named '{}' has loot", name);

        LOG_INFO("module", ">> mod-supply-logistics: Scarce materials on {} gathering nodes and {} skinning level bands",
            nodeDrops.size(), skinBands.size());
    }

    void OnLootFilled(Loot* loot, LootTemplate const* tab, LootStore const& store, Player* owner)
    {
        if (!loot || !tab || !Enabled() || !rate || !IsRealPlayer(owner))
            return;
        ObjectGuid source = loot->sourceWorldObjectGUID;
        if (&store == &LootTemplates_Gameobject && source.IsGameObject())
        {
            auto itr = nodeDrops.find(source.GetEntry());
            if (itr != nodeDrops.end())
                for (Drop const& d : itr->second)
                    Roll(loot, d);
        }
        else if (&store == &LootTemplates_Skinning && source.IsCreatureOrVehicle())
        {
            // Leather skinning only: not a creature an herbalist, miner or engineer loots this way.
            Creature* creature = ObjectAccessor::GetCreature(*owner, source);
            if (!creature || (creature->GetCreatureTemplate()->type_flags & OTHER_SKINNING))
                return;
            uint8 level = creature->GetLevel();
            for (Band const& b : skinBands)
                if (level >= b.low && level <= b.high)
                    Roll(loot, b.drop);
        }
    }
}
