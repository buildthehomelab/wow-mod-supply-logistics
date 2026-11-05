/*
 * mod-supply-logistics: data, configuration and what each part does.
 *
 * Released under the MIT License.
 */

#include "SupplyLogistics.h"

#include "Chat.h"
#include "Config.h"
#include "Containers.h"
#include "Creature.h"
#include "DBCStores.h"
#include "DatabaseEnv.h"
#include "Item.h"
#include "Log.h"
#include "Mail.h"
#include "Map.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "QuestDef.h"
#include "Random.h"
#include "ReputationMgr.h"
#include "ScriptedGossip.h"
#include "Spell.h"
#include "SpellMgr.h"
#include "WorldSession.h"

#include <algorithm>
#include <set>
#include <unordered_map>

namespace SupplyLogistics
{
    std::vector<Title> const TITLES = {
        { 193, 271621, 171 },   // the Alchemist
        { 194, 271622, 164 },   // the Blacksmith
        { 195, 271624, 333 },   // the Enchanter
        { 196, 271625, 202 },   // the Engineer
        { 197, 271626, 165 },   // the Leatherworker
        { 198, 271627, 197 },   // the Tailor
    };

    uint32 const SEALED_WRITS[MAX_TIER + 1] = { 0, 262887, 262888, 262889, 262890 };

    namespace
    {
        constexpr uint32 TITLE_SKILL = 300;
        constexpr uint32 ACTION_RECEIPT = 1000;     // crate menu: put a receipt on it instead
        constexpr uint32 MAX_MENU_OPTIONS = 30;     // a 3.3.5a gossip window shows no more
        constexpr uint32 SKILL_HERBALISM = 182, SKILL_MINING = 186, SKILL_SKINNING = 393;
        constexpr uint32 SKILL_ALCHEMY = 171, SKILL_BLACKSMITHING = 164, SKILL_ENGINEERING = 202;
        constexpr uint32 SKILL_LEATHERWORKING = 165, SKILL_TAILORING = 197, SKILL_ENCHANTING = 333;

        // The camp NPCs (Forever's entries) and the flag each needs.
        struct CampNpc
        {
            uint32 entry;
            uint32 flags;
        };
        CampNpc const CAMP_NPCS[] = {
            { 256386, UNIT_NPC_FLAG_QUESTGIVER }, { 256390, UNIT_NPC_FLAG_QUESTGIVER },   // Inventory Intake
            { 256388, UNIT_NPC_FLAG_QUESTGIVER }, { 256391, UNIT_NPC_FLAG_QUESTGIVER },   // Contract Coordinator
            { 256384, UNIT_NPC_FLAG_VENDOR }, { 256389, UNIT_NPC_FLAG_VENDOR },           // Supply Officer
            { 256400, UNIT_NPC_FLAG_VENDOR }, { 256736, UNIT_NPC_FLAG_VENDOR },           // Kodo / Mule Handler
            { 256672, UNIT_NPC_FLAG_VENDOR }, { 256742, UNIT_NPC_FLAG_VENDOR },           // Uncertified Scribe
            { 248196, UNIT_NPC_FLAG_VENDOR }, { 256729, UNIT_NPC_FLAG_VENDOR },           // Alchemist
            { 248197, UNIT_NPC_FLAG_VENDOR }, { 256730, UNIT_NPC_FLAG_VENDOR },           // Blacksmith
            { 248198, UNIT_NPC_FLAG_VENDOR }, { 256731, UNIT_NPC_FLAG_VENDOR },           // Chef
            { 248199, UNIT_NPC_FLAG_VENDOR }, { 256732, UNIT_NPC_FLAG_VENDOR },           // Enchanter
            { 248200, UNIT_NPC_FLAG_VENDOR }, { 256733, UNIT_NPC_FLAG_VENDOR },           // Engineer
            { 248201, UNIT_NPC_FLAG_VENDOR }, { 256734, UNIT_NPC_FLAG_VENDOR },           // Leatherworker
            { 248202, UNIT_NPC_FLAG_VENDOR }, { 256735, UNIT_NPC_FLAG_VENDOR },           // Tailor
        };

        struct Config
        {
            bool enable = true;
            float crateChance = 4.0f;
            float writChance = 1.0f;
            float handInWritChance = 25.0f;
            float eliteChance = 10.0f;
            uint32 eliteMinLevel = 30;
            uint32 minLevel = 10;
            float professionWeight = 50.0f;
            bool campNpcFlags = true;
        } config;

        std::vector<Crate> crates;
        std::unordered_map<uint32, size_t> crateIndex;
        std::unordered_map<uint32, Writ> writs;
        std::unordered_map<uint32, uint32> questRep;        // quest -> reputation
        std::unordered_map<uint32, uint8> sealedTier;       // Sealed crate item -> tier (Elite: 5)
        std::unordered_map<uint32, std::set<uint32>> accountTitles;

        // The professions a crate kind is for: drops lean towards crates the player can fill.
        std::vector<uint32> KindSkills(uint8 kind)
        {
            switch (kind)
            {
                case KIND_HERBS:       return { SKILL_HERBALISM, SKILL_ALCHEMY };
                case KIND_ORE:         return { SKILL_MINING, SKILL_BLACKSMITHING, SKILL_ENGINEERING };
                case KIND_TEXTILES:    return { SKILL_TAILORING, SKILL_LEATHERWORKING, SKILL_SKINNING };
                case KIND_CURIOSITIES: return { SKILL_ENCHANTING };
                case KIND_FABRICS:     return { SKILL_TAILORING, SKILL_LEATHERWORKING };
                case KIND_INGOTS:      return { SKILL_MINING, SKILL_BLACKSMITHING, SKILL_ENGINEERING };
                case KIND_PARTS:       return { SKILL_ENGINEERING };
                default:               return {};
            }
        }

        bool HasAnySkill(Player* player, std::vector<uint32> const& skills)
        {
            return std::any_of(skills.begin(), skills.end(), [player](uint32 skill) { return player->HasSkill(skill); });
        }

        // The highest crate tier a player of this level can open (Forever's: 10, 10, 20 and 35).
        uint8 MaxTierForPlayer(uint8 level)
        {
            if (level >= 35)
                return 4;
            if (level >= 20)
                return 3;
            return 2;
        }

        uint8 TierForLevel(uint8 level)
        {
            if (level >= 40)
                return 4;
            if (level >= 30)
                return 3;
            if (level >= 20)
                return 2;
            return 1;
        }

        std::string ItemName(uint32 entry)
        {
            ItemTemplate const* proto = sObjectMgr->GetItemTemplate(entry);
            return proto ? proto->Name1 : "item " + std::to_string(entry);
        }

        void Say(Player* player, std::string const& text)
        {
            ChatHandler(player->GetSession()).SendSysMessage(text);
        }

        // Into the bags, or by mail when they're full.
        void GiveItem(Player* player, uint32 entry, uint32 count = 1)
        {
            ItemPosCountVec dest;
            if (player->CanStoreNewItem(NULL_BAG, NULL_SLOT, dest, entry, count) == EQUIP_ERR_OK)
            {
                if (Item* item = player->StoreNewItem(dest, entry, true))
                {
                    player->SendNewItem(item, count, true, false);
                    return;
                }
            }

            CharacterDatabaseTransaction trans = CharacterDatabase.BeginTransaction();
            MailDraft draft("Supply and Logistics", "Your bags were full, so this came by mail.");
            if (Item* item = Item::CreateItem(entry, count, player))
            {
                item->SaveToDB(trans);
                draft.AddItem(item);
            }
            draft.SendMailTo(trans, MailReceiver(player), MailSender(MAIL_NORMAL, 0, MAIL_STATIONERY_DEFAULT));
            CharacterDatabase.CommitTransaction(trans);
            Say(player, "Your bags are full: " + ItemName(entry) + " is in your mailbox.");
        }

        bool HasRoomFor(Player* player, uint32 entry, uint32 count = 1)
        {
            ItemPosCountVec dest;
            return player->CanStoreNewItem(NULL_BAG, NULL_SLOT, dest, entry, count) == EQUIP_ERR_OK;
        }

        // Taken out of the bags: the item a menu was opened on may be gone by the time an option is chosen.
        bool Carries(Player* player, uint32 entry, uint32 count = 1)
        {
            return entry && player->HasItemCount(entry, count, false);
        }

        Crate const* PickCrate(Player* player, uint8 tier)
        {
            std::vector<Crate const*> all, own;
            for (Crate const& crate : crates)
            {
                if (crate.tier != tier)
                    continue;
                all.push_back(&crate);
                if (HasAnySkill(player, KindSkills(crate.kind)))
                    own.push_back(&crate);
            }
            if (all.empty())
                return nullptr;
            if (!own.empty() && roll_chance_f(config.professionWeight))
                return Acore::Containers::SelectRandomContainerElement(own);
            return Acore::Containers::SelectRandomContainerElement(all);
        }

        Writ const* PickWrit(Player* player, uint8 tier, uint32 except = 0)
        {
            std::vector<Writ const*> all, own;
            for (auto const& [item, writ] : writs)
            {
                if (writ.tier != tier || item == except)
                    continue;
                all.push_back(&writ);
                if (player->HasSkill(writ.skill))
                    own.push_back(&writ);
            }
            if (all.empty())
                return nullptr;
            if (!own.empty() && roll_chance_f(config.professionWeight))
                return Acore::Containers::SelectRandomContainerElement(own);
            return Acore::Containers::SelectRandomContainerElement(all);
        }

        void GrantTitle(Player* player, Title const& title, bool on)
        {
            CharTitlesEntry const* entry = sCharTitlesStore.LookupEntry(title.id);
            if (!entry)
                return;
            if (on && !player->HasTitle(entry))
                player->SetTitle(entry);
            else if (!on && player->HasTitle(entry))
                player->SetTitle(entry, true);
        }
    }

    bool IsRealPlayer(Player* player)
    {
        return player && player->GetSession() && !IsBotSession(player->GetSession());
    }

    void LoadConfig()
    {
        config.enable = sConfigMgr->GetOption<bool>("SupplyLogistics.Enable", true);
        config.crateChance = sConfigMgr->GetOption<float>("SupplyLogistics.Crate.Chance", 4.0f);
        config.writChance = sConfigMgr->GetOption<float>("SupplyLogistics.Writ.Chance", 1.0f);
        config.handInWritChance = sConfigMgr->GetOption<float>("SupplyLogistics.Writ.HandInChance", 25.0f);
        config.eliteChance = sConfigMgr->GetOption<float>("SupplyLogistics.Elite.Chance", 10.0f);
        config.eliteMinLevel = sConfigMgr->GetOption<uint32>("SupplyLogistics.Elite.MinLevel", 30);
        config.minLevel = std::max<uint32>(1, sConfigMgr->GetOption<uint32>("SupplyLogistics.MinLevel", 10));
        config.professionWeight = sConfigMgr->GetOption<float>("SupplyLogistics.ProfessionWeight", 50.0f);
        config.campNpcFlags = sConfigMgr->GetOption<bool>("SupplyLogistics.CampNpcFlags", true);
    }

    bool Enabled()
    {
        return config.enable;
    }

    void LoadData()
    {
        crates.clear();
        crateIndex.clear();
        writs.clear();
        questRep.clear();
        sealedTier.clear();

        if (QueryResult result = WorldDatabase.Query("SELECT item, tier, crafted, kind, sealed FROM mod_supply_logistics_crate"))
        {
            do
            {
                Field* f = result->Fetch();
                Crate crate;
                crate.item = f[0].Get<uint32>();
                crate.tier = f[1].Get<uint8>();
                crate.crafted = f[2].Get<uint8>() != 0;
                crate.kind = f[3].Get<uint8>();
                crate.sealed = f[4].Get<uint32>();
                if (!crate.tier || crate.tier > MAX_TIER || !sObjectMgr->GetItemTemplate(crate.item)
                    || !sObjectMgr->GetItemTemplate(crate.sealed))
                {
                    LOG_ERROR("server.loading", "mod-supply-logistics: crate {} has a bad tier or item; left out", crate.item);
                    continue;
                }
                crateIndex[crate.item] = crates.size();
                sealedTier[crate.sealed] = crate.tier;
                crates.push_back(std::move(crate));
            } while (result->NextRow());
        }
        sealedTier[ITEM_SEALED_ELITE] = MAX_TIER + 1;

        if (QueryResult result = WorldDatabase.Query("SELECT crate, reagent, count FROM mod_supply_logistics_bundle ORDER BY crate, slot"))
        {
            do
            {
                Field* f = result->Fetch();
                auto it = crateIndex.find(f[0].Get<uint32>());
                uint32 reagent = f[1].Get<uint32>();
                if (it == crateIndex.end() || !sObjectMgr->GetItemTemplate(reagent))
                    continue;
                if (crates[it->second].bundles.size() < MAX_MENU_OPTIONS - 1)
                    crates[it->second].bundles.push_back({ reagent, f[2].Get<uint32>() });
            } while (result->NextRow());
        }

        if (QueryResult result = WorldDatabase.Query("SELECT writ, quest, tier, skill FROM mod_supply_logistics_writ"))
        {
            do
            {
                Field* f = result->Fetch();
                Writ writ;
                writ.item = f[0].Get<uint32>();
                writ.quest = f[1].Get<uint32>();
                writ.tier = f[2].Get<uint8>();
                writ.skill = f[3].Get<uint16>();
                if (!writ.tier || writ.tier > MAX_TIER || !sObjectMgr->GetItemTemplate(writ.item)
                    || !sObjectMgr->GetQuestTemplate(writ.quest))
                {
                    LOG_ERROR("server.loading", "mod-supply-logistics: writ {} has a bad tier, item or quest; left out", writ.item);
                    continue;
                }
                writs[writ.item] = writ;
            } while (result->NextRow());
        }

        if (QueryResult result = WorldDatabase.Query("SELECT quest, rep FROM mod_supply_logistics_quest"))
        {
            do
            {
                Field* f = result->Fetch();
                questRep[f[0].Get<uint32>()] = f[1].Get<uint32>();
            } while (result->NextRow());
        }

        for (uint32 faction : { FACTION_HORDE, FACTION_ALLIANCE })
        {
            FactionEntry const* entry = sFactionStore.LookupEntry(faction);
            if (!entry || entry->reputationListID < 0)
                LOG_ERROR("server.loading", "mod-supply-logistics: faction {} is missing from faction_dbc; no reputation "
                    "will be paid (run data/sql/db-world/mod_supply_logistics_dbc.sql)", faction);
        }

        LOG_INFO("server.loading", ">> mod-supply-logistics: {} crates, {} writs, {} paying quests", crates.size(), writs.size(),
            questRep.size());
    }

    Crate const* GetCrate(uint32 item)
    {
        auto it = crateIndex.find(item);
        return it == crateIndex.end() ? nullptr : &crates[it->second];
    }

    Writ const* GetWrit(uint32 item)
    {
        auto it = writs.find(item);
        return it == writs.end() ? nullptr : &it->second;
    }

    std::vector<Crate> const& AllCrates()
    {
        return crates;
    }

    // --- Drops ---------------------------------------------------------------------------------------

    void OnKillReward(Player* player, Unit* victim)
    {
        if (!config.enable || !IsRealPlayer(player) || player->GetLevel() < config.minLevel)
            return;
        Creature* creature = victim ? victim->ToCreature() : nullptr;
        if (!creature || creature->IsPet() || creature->IsTotem() || creature->IsSummon() || creature->GetOwnerGUID())
            return;
        Map* map = creature->GetMap();
        if (!map)
            return;

        // Dungeon and raid bosses: now and then an Elite crate, already sealed. (The kill rewarder's
        // own dungeon flag is set for groups only.)
        if (map->IsDungeon())
        {
            if (map->IsDungeon() && (creature->IsDungeonBoss() || creature->isWorldBoss())
                && creature->GetLevel() >= config.eliteMinLevel && roll_chance_f(config.eliteChance))
                GiveItem(player, ITEM_SEALED_ELITE);
            return;
        }

        // Anything else in the open world that is worth experience to this player.
        // (Dead players in range are rewarded too; for the open world they aren't.)
        if (map->Instanceable() || !player->IsAlive() || creature->GetLevel() < config.minLevel
            || !player->isHonorOrXPTarget(creature))
            return;
        uint8 tier = TierForLevel(creature->GetLevel());
        // A crate is capped at the tier the player can open; any Sealed Writ opens from level 10.
        if (roll_chance_f(config.crateChance))
            if (Crate const* crate = PickCrate(player, std::min(tier, MaxTierForPlayer(player->GetLevel()))))
                GiveItem(player, crate->item);
        if (roll_chance_f(config.writChance))
            GiveItem(player, SEALED_WRITS[tier]);
    }

    // --- Hand-ins ------------------------------------------------------------------------------------

    void GiveReputation(Player* player, int32 amount, uint32 questLevel)
    {
        uint32 faction = player->GetTeamId(true) == TEAM_HORDE ? FACTION_HORDE : FACTION_ALLIANCE;
        FactionEntry const* entry = sFactionStore.LookupEntry(faction);
        if (!entry || entry->reputationListID < 0 || amount <= 0)
            return;
        float gain = player->CalculateReputationGain(REPUTATION_SOURCE_REPEATABLE_QUEST, questLevel, float(amount), faction);
        if (gain > 0.0f)
            player->GetReputationMgr().ModifyReputation(entry, gain);
    }

    void OnQuestRewarded(Player* player, Quest const* quest)
    {
        if (!config.enable || !quest)
            return;
        auto rep = questRep.find(quest->GetQuestId());
        if (rep == questRep.end())
            return;
        GiveReputation(player, int32(rep->second), uint32(player->GetQuestLevel(quest)));

        // A Sealed crate brings a writ now and then.
        auto tier = sealedTier.find(quest->RequiredItemId[0]);
        if (tier != sealedTier.end() && roll_chance_f(config.handInWritChance))
            GiveItem(player, SEALED_WRITS[std::min<uint8>(tier->second, MAX_TIER)]);
    }

    // --- Waylaid Crate -------------------------------------------------------------------------------

    void ShowCrateMenu(Player* player, Item* item)
    {
        Crate const* crate = GetCrate(item->GetEntry());
        ClearGossipMenuFor(player);
        if (!crate)
            return;
        for (uint32 slot = 0; slot < crate->bundles.size(); ++slot)
        {
            Bundle const& bundle = crate->bundles[slot];
            uint32 have = player->GetItemCount(bundle.reagent, false);
            std::string text = std::to_string(bundle.count) + " " + ItemName(bundle.reagent)
                + " (you have " + std::to_string(have) + ")";
            AddGossipItemFor(player, have >= bundle.count ? GOSSIP_ICON_INTERACT_1 : GOSSIP_ICON_CHAT, text, GOSSIP_SENDER_MAIN, slot);
        }
        if (Carries(player, ITEM_RECEIPT))
            AddGossipItemFor(player, GOSSIP_ICON_MONEY_BAG, "Put a Forged Delivery Receipt on it and send it back empty",
                GOSSIP_SENDER_MAIN, ACTION_RECEIPT);
        SendGossipMenuFor(player, NPC_TEXT_CRATE, item->GetGUID());
    }

    void SelectCrateOption(Player* player, Item* item, uint32 action)
    {
        CloseGossipMenuFor(player);
        Crate const* crate = item ? GetCrate(item->GetEntry()) : nullptr;
        if (!crate || !Carries(player, crate->item))
            return;

        if (action == ACTION_RECEIPT)
        {
            if (!Carries(player, ITEM_RECEIPT))
                return;
            if (!HasRoomFor(player, ITEM_CONTAINER))
            {
                Say(player, "Make room in your bags first.");
                return;
            }
            player->DestroyItemCount(ITEM_RECEIPT, 1, true);
            player->DestroyItemCount(crate->item, 1, true);
            GiveItem(player, ITEM_CONTAINER);
            return;
        }

        if (action >= crate->bundles.size())
            return;
        Bundle const& bundle = crate->bundles[action];
        if (!Carries(player, bundle.reagent, bundle.count))
        {
            Say(player, "You need " + std::to_string(bundle.count) + " " + ItemName(bundle.reagent) + " to fill this crate.");
            return;
        }
        if (!HasRoomFor(player, crate->sealed))
        {
            Say(player, "Make room in your bags first.");
            return;
        }
        player->DestroyItemCount(bundle.reagent, bundle.count, true);
        player->DestroyItemCount(crate->item, 1, true);
        GiveItem(player, crate->sealed);
    }

    // --- Forged Delivery Receipt ---------------------------------------------------------------------

    void ShowReceiptMenu(Player* player, Item* item)
    {
        ClearGossipMenuFor(player);
        uint32 shown = 0;
        for (Crate const& crate : crates)
        {
            if (shown >= MAX_MENU_OPTIONS || !Carries(player, crate.item))
                continue;
            AddGossipItemFor(player, GOSSIP_ICON_INTERACT_1, ItemName(crate.item), GOSSIP_SENDER_MAIN, crate.item);
            ++shown;
        }
        if (!shown)
        {
            Say(player, "You have no Waylaid Crate to put the receipt on.");
            return;
        }
        SendGossipMenuFor(player, NPC_TEXT_RECEIPT, item->GetGUID());
    }

    void SelectReceiptOption(Player* player, uint32 action)
    {
        CloseGossipMenuFor(player);
        Crate const* crate = GetCrate(action);
        if (!crate || !Carries(player, crate->item) || !Carries(player, ITEM_RECEIPT))
            return;
        if (!HasRoomFor(player, ITEM_CONTAINER))
        {
            Say(player, "Make room in your bags first.");
            return;
        }
        player->DestroyItemCount(ITEM_RECEIPT, 1, true);
        player->DestroyItemCount(crate->item, 1, true);
        GiveItem(player, ITEM_CONTAINER);
    }

    // --- Writs ---------------------------------------------------------------------------------------

    void OpenSealedWrit(Player* player, Item* item)
    {
        uint8 tier = 0;
        for (uint8 t = 1; t <= MAX_TIER; ++t)
            if (SEALED_WRITS[t] == item->GetEntry())
                tier = t;
        Writ const* writ = tier ? PickWrit(player, tier) : nullptr;
        if (!writ)
            return;
        if (!HasRoomFor(player, writ->item))
        {
            Say(player, "Make room in your bags first.");
            return;
        }
        player->DestroyItemCount(item->GetEntry(), 1, true);
        GiveItem(player, writ->item);
    }

    void ShowQuillMenu(Player* player, Item* item)
    {
        ClearGossipMenuFor(player);
        uint32 shown = 0;
        for (auto const& [entry, writ] : writs)
        {
            if (shown >= MAX_MENU_OPTIONS || !Carries(player, entry))
                continue;
            AddGossipItemFor(player, GOSSIP_ICON_TRAINER, ItemName(entry), GOSSIP_SENDER_MAIN, entry);
            ++shown;
        }
        if (!shown)
        {
            Say(player, "You have no Craftsman's Writ to rewrite: an order you have taken can't be.");
            return;
        }
        SendGossipMenuFor(player, NPC_TEXT_QUILL, item->GetGUID());
    }

    void SelectQuillOption(Player* player, uint32 action)
    {
        CloseGossipMenuFor(player);
        Writ const* writ = GetWrit(action);
        uint32 quill = 0;
        for (uint32 entry : { 262896u, 90743u })
            if (Carries(player, entry))
                quill = entry;
        if (!writ || !quill || !Carries(player, writ->item))
            return;
        Writ const* next = PickWrit(player, writ->tier, writ->item);
        if (!next)
            return;
        player->DestroyItemCount(quill, 1, true);
        player->DestroyItemCount(writ->item, 1, true);
        GiveItem(player, next->item);
    }

    // Skill is counted the way the vendor's condition and the item's requirement count it: with permanent
    // (racial) bonuses, without temporary ones.
    // --- Certifications ------------------------------------------------------------------------------

    void LoadAccountTitles(Player* player)
    {
        // Merged, not replaced: an unlock still on its way to the database stays.
        uint32 account = player->GetSession()->GetAccountId();
        std::set<uint32>& titles = accountTitles[account];
        if (QueryResult result = CharacterDatabase.Query("SELECT title FROM mod_supply_logistics_title WHERE account = {}", account))
        {
            do
                titles.insert(result->Fetch()[0].Get<uint32>());
            while (result->NextRow());
        }
    }

    void OnSkillChanged(Player* player, uint32 skill, uint32 /*value*/)
    {
        auto it = accountTitles.find(player->GetSession()->GetAccountId());
        if (it == accountTitles.end())
            return;
        for (Title const& title : TITLES)
            if (title.skill == skill && it->second.count(title.id))
                GrantTitle(player, title, player->GetBaseSkillValue(title.skill) >= TITLE_SKILL);
    }

    void SyncTitles(Player* player)
    {
        auto it = accountTitles.find(player->GetSession()->GetAccountId());
        if (it == accountTitles.end())
            return;
        for (Title const& title : TITLES)
            if (it->second.count(title.id))
                GrantTitle(player, title, player->GetBaseSkillValue(title.skill) >= TITLE_SKILL);
    }

    void UseCertification(Player* player, Item* item)
    {
        auto title = std::find_if(TITLES.begin(), TITLES.end(), [item](Title const& t) { return t.item == item->GetEntry(); });
        if (title == TITLES.end())
            return;
        uint32 account = player->GetSession()->GetAccountId();
        std::set<uint32>& titles = accountTitles[account];
        if (titles.count(title->id))
        {
            Say(player, "Your account has this title already.");
            return;
        }
        titles.insert(title->id);
        CharacterDatabase.Execute("INSERT IGNORE INTO mod_supply_logistics_title (account, title) VALUES ({}, {})", account, title->id);
        player->DestroyItemCount(item->GetEntry(), 1, true);
        GrantTitle(player, *title, player->GetBaseSkillValue(title->skill) >= TITLE_SKILL);
        Say(player, "Title unlocked for every character on your account with 300 skill in the profession.");
    }

    // --- Camp NPCs -----------------------------------------------------------------------------------

    void SetTemplateNpcFlags()
    {
        if (!config.enable || !config.campNpcFlags)
            return;
        for (CampNpc const& npc : CAMP_NPCS)
            if (CreatureTemplate const* cinfo = sObjectMgr->GetCreatureTemplate(npc.entry))
                const_cast<CreatureTemplate*>(cinfo)->npcflag |= npc.flags;
    }

    void ReleaseItem(Player* player, Item* item)
    {
        ItemTemplate const* proto = item ? item->GetTemplate() : nullptr;
        if (!proto)
            return;
        if (SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(proto->Spells[0].SpellId))
            Spell::SendCastResult(player, spellInfo, 0, SPELL_FAILED_DONT_REPORT);
    }

    void SetNpcFlags(Creature* creature)
    {
        if (!config.enable || !config.campNpcFlags)
            return;
        for (CampNpc const& npc : CAMP_NPCS)
            if (npc.entry == creature->GetEntry())
                creature->SetNpcFlag(NPCFlags(npc.flags));
    }
}
