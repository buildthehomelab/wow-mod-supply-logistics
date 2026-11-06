/*
 * mod-supply-logistics: the script hooks.
 *
 * Released under the MIT License.
 */

#include "SupplyLogistics.h"

#include "CellImpl.h"
#include "Creature.h"
#include "DBCStores.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Item.h"
#include "KillRewarder.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"

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
            PLAYERHOOK_ON_BEFORE_BUY_ITEM_FROM_VENDOR,
        }) { }

        // item = 0 tells the core the purchase was handled (here: refused).
        void OnPlayerBeforeBuyItemFromVendor(Player* player, ObjectGuid /*vendorguid*/, uint32 /*vendorslot*/, uint32& item,
            uint8 /*count*/, uint8 /*bag*/, uint8 /*slot*/) override
        {
            if (RefuseCertificationBuy(player, item))
                item = 0;
        }

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
            LoadScarceConfig();
        }

        void OnStartup() override
        {
            LoadData();
            LoadScarce();
            SetTemplateNpcFlags();
        }
    };

    class SupplyLogisticsMiscScript : public MiscScript
    {
    public:
        SupplyLogisticsMiscScript() : MiscScript("SupplyLogisticsMiscScript", { MISCHOOK_ON_AFTER_LOOT_TEMPLATE_PROCESS }) { }

        void OnAfterLootTemplateProcess(Loot* loot, LootTemplate const* tab, LootStore const& store, Player* lootOwner,
            bool /*personal*/, bool /*noEmptyError*/, uint16 /*lootMode*/) override
        {
            OnLootFilled(loot, tab, store, lootOwner);
        }
    };
}

// The nearest unit the owner may attack with a spell (not an unflagged player of the other faction,
// not one behind a wall).
class NearestValidEnemy
{
public:
    NearestValidEnemy(Unit* owner, SpellInfo const* spell, float range) : _owner(owner), _spell(spell), _range(range) { }

    bool operator()(Unit* u)
    {
        if (u == _owner || !u->IsAlive() || !_owner->IsWithinDistInMap(u, _range) || !_owner->IsValidAttackTarget(u, _spell)
            || !_owner->IsWithinLOSInMap(u))
            return false;
        _range = _owner->GetDistance(u);
        return true;
    }

private:
    Unit* _owner;
    SpellInfo const* _spell;
    float _range;
};

// Potion of Venomous Blood (Forever's Alchemy recipe). The potion's buff holds its doses (the spell's
// stack amount); each bleed tick you take moves one to the nearest enemy within its second effect's
// yards, as its first effect's trigger spell. Ids come from the spells, which tools/catalog.py writes.
class spell_supply_venomous_blood : public AuraScript
{
    PrepareAuraScript(spell_supply_venomous_blood);

    // Drunk: all the doses. Not when the aura comes back at login, or a relog would refill them.
    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Player* player = GetTarget()->ToPlayer())
            if (player->GetSession()->PlayerLoading())
                return;
        GetAura()->SetStackAmount(GetSpellInfo()->StackAmount);
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        DamageInfo* damage = eventInfo.GetDamageInfo();
        return damage && damage->GetDamage() && damage->GetSpellInfo()
            && (damage->GetSpellInfo()->GetAllEffectsMechanicMask() & (1ULL << MECHANIC_BLEED));
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        Unit* owner = GetTarget();
        uint32 doseSpell = GetSpellInfo()->Effects[EFFECT_0].TriggerSpell;
        SpellInfo const* dose = sSpellMgr->GetSpellInfo(doseSpell);
        float range = float(GetSpellInfo()->Effects[EFFECT_1].CalcValue());
        Unit* victim = nullptr;
        NearestValidEnemy check(owner, dose, range);
        Acore::UnitLastSearcher<NearestValidEnemy> searcher(owner, victim, check);
        Cell::VisitObjects(owner, searcher, range);
        // A dose is used up only when it lands.
        if (victim && dose && owner->CastSpell(victim, doseSpell, true, nullptr, aurEff) == SPELL_CAST_OK)
            ModStackAmount(-1);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_supply_venomous_blood::HandleApply, EFFECT_0, SPELL_AURA_DUMMY,
            AURA_EFFECT_HANDLE_REAL);
        DoCheckProc += AuraCheckProcFn(spell_supply_venomous_blood::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_supply_venomous_blood::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// A dose on an enemy: when it runs out, each stack deals its first effect's amount as the trigger
// spell's damage, from whoever spread it.
class spell_supply_venomous_blood_dose : public AuraScript
{
    PrepareAuraScript(spell_supply_venomous_blood_dose);

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (GetTargetApplication()->GetRemoveMode() != AURA_REMOVE_BY_EXPIRE)
            return;
        Unit* caster = GetCaster();
        if (!caster || !GetTarget()->IsAlive())
            return;
        // Per dose: the spell's amount, not the aura's (the core already multiplies that by the stacks).
        int32 damage = GetSpellInfo()->Effects[EFFECT_0].CalcValue(caster) * GetStackAmount();
        caster->CastCustomSpell(GetTarget(), GetSpellInfo()->Effects[EFFECT_0].TriggerSpell, &damage, nullptr, nullptr, true);
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_supply_venomous_blood_dose::HandleRemove, EFFECT_0,
            SPELL_AURA_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

void AddSupplyLogisticsScripts()
{
    RegisterSpellScript(spell_supply_venomous_blood);
    RegisterSpellScript(spell_supply_venomous_blood_dose);
    new SupplyCrateItem();
    new SupplyReceiptItem();
    new SupplyQuillItem();
    new SupplySealedWritItem();
    new SupplyCertificationItem();
    new SupplyLogisticsPlayerScript();
    new SupplyLogisticsCreatureScript();
    new SupplyLogisticsWorldScript();
    AddSupplyLogisticsSignScripts();
    new SupplyLogisticsMiscScript();
}
