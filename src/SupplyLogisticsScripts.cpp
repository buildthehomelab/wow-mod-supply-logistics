/*
 * mod-supply-logistics: the script hooks.
 *
 * Released under the MIT License.
 */

#include "SupplyLogistics.h"

#include "Creature.h"
#include "DBCStores.h"
#include "Item.h"
#include "KillRewarder.h"
#include "Player.h"
#include "ScriptMgr.h"

using namespace SupplyLogistics;

void AddSupplyLogisticsSignScripts();

namespace
{
    // Every use spell of the module is a dummy the client needs; returning true here means it is
    // never cast. ReleaseItem first (the item may be used up), or the client leaves it greyed out.
    class SupplyCrateItem : public ItemScript
    {
    public:
        SupplyCrateItem() : ItemScript("item_supply_waylaid_crate") { }

        bool OnUse(Player* player, Item* item, SpellCastTargets const& /*targets*/) override
        {
            ReleaseItem(player, item);
            if (Enabled())
                ShowCrateMenu(player, item);
            return true;
        }

        void OnGossipSelect(Player* player, Item* item, uint32 /*sender*/, uint32 action) override
        {
            SelectCrateOption(player, item, action);
        }
    };

    class SupplyReceiptItem : public ItemScript
    {
    public:
        SupplyReceiptItem() : ItemScript("item_supply_receipt") { }

        bool OnUse(Player* player, Item* item, SpellCastTargets const& /*targets*/) override
        {
            ReleaseItem(player, item);
            if (Enabled())
                ShowReceiptMenu(player, item);
            return true;
        }

        void OnGossipSelect(Player* player, Item* /*item*/, uint32 /*sender*/, uint32 action) override
        {
            SelectReceiptOption(player, action);
        }
    };

    class SupplyQuillItem : public ItemScript
    {
    public:
        SupplyQuillItem() : ItemScript("item_supply_quill") { }

        bool OnUse(Player* player, Item* item, SpellCastTargets const& /*targets*/) override
        {
            ReleaseItem(player, item);
            if (Enabled())
                ShowQuillMenu(player, item);
            return true;
        }

        void OnGossipSelect(Player* player, Item* /*item*/, uint32 /*sender*/, uint32 action) override
        {
            SelectQuillOption(player, action);
        }
    };

    class SupplySealedWritItem : public ItemScript
    {
    public:
        SupplySealedWritItem() : ItemScript("item_supply_sealed_writ") { }

        bool OnUse(Player* player, Item* item, SpellCastTargets const& /*targets*/) override
        {
            ReleaseItem(player, item);
            if (Enabled())
                OpenSealedWrit(player, item);
            return true;
        }
    };

    class SupplyCertificationItem : public ItemScript
    {
    public:
        SupplyCertificationItem() : ItemScript("item_supply_certification") { }

        bool OnUse(Player* player, Item* item, SpellCastTargets const& /*targets*/) override
        {
            ReleaseItem(player, item);
            if (Enabled())
                UseCertification(player, item);
            return true;
        }
    };

    class SupplyLogisticsPlayerScript : public PlayerScript
    {
    public:
        SupplyLogisticsPlayerScript() : PlayerScript("SupplyLogisticsPlayerScript", {
            PLAYERHOOK_ON_LOGIN,
            PLAYERHOOK_ON_REWARD_KILL_REWARDER,
            PLAYERHOOK_ON_PLAYER_COMPLETE_QUEST,
            PLAYERHOOK_ON_UPDATE_SKILL,
            PLAYERHOOK_ON_SET_SKILL,
        }) { }

        void OnPlayerLogin(Player* player) override
        {
            if (!IsRealPlayer(player))
                return;
            LoadAccountTitles(player);
            SyncTitles(player);
        }

        // Called for every player the kill rewards, the killer's group within range included, at
        // any level: crates are for capped players too.
        void OnPlayerRewardKillRewarder(Player* player, KillRewarder* rewarder, bool /*isDungeon*/, float& /*rate*/) override
        {
            OnKillReward(player, rewarder->GetVictim());
        }

        void OnPlayerCompleteQuest(Player* player, Quest const* quest) override
        {
            OnQuestRewarded(player, quest);
        }

        // Both run after the change, with the new value.
        void OnPlayerUpdateSkill(Player* player, uint32 skillId, uint32 /*value*/, uint32 /*max*/, uint32 /*step*/, uint32 newValue) override
        {
            OnSkillChanged(player, skillId, newValue);
        }

        void OnPlayerSetSkill(Player* player, uint32 skillId, uint32 /*value*/, uint32 /*max*/, uint32 /*step*/, uint32 newValue) override
        {
            OnSkillChanged(player, skillId, newValue);
        }
    };

    class SupplyLogisticsCreatureScript : public AllCreatureScript
    {
    public:
        SupplyLogisticsCreatureScript() : AllCreatureScript("SupplyLogisticsCreatureScript") { }

        void OnCreatureAddWorld(Creature* creature) override
        {
            SetNpcFlags(creature);
        }
    };

    class SupplyLogisticsWorldScript : public WorldScript
    {
    public:
        SupplyLogisticsWorldScript() : WorldScript("SupplyLogisticsWorldScript",
            { WORLDHOOK_ON_AFTER_CONFIG_LOAD, WORLDHOOK_ON_STARTUP }) { }

        void OnAfterConfigLoad(bool /*reload*/) override
        {
            LoadConfig();
        }

        void OnStartup() override
        {
            LoadData();
            SetTemplateNpcFlags();
        }
    };
}

void AddSupplyLogisticsScripts()
{
    new SupplyCrateItem();
    new SupplyReceiptItem();
    new SupplyQuillItem();
    new SupplySealedWritItem();
    new SupplyCertificationItem();
    new SupplyLogisticsPlayerScript();
    new SupplyLogisticsCreatureScript();
    new SupplyLogisticsWorldScript();
    AddSupplyLogisticsSignScripts();
}
