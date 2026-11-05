/*
 * mod-supply-logistics: WoW Forever's Supply and Logistics on a 3.3.5a server.
 *
 * Open-world mobs drop Waylaid Crates and Sealed Writs. A crate is filled with one bundle of goods and
 * becomes a Sealed crate, which the Inventory Intake at a trade camp takes for Merchant's Favor and
 * reputation with the player's side: Durotar Supply and Logistics (Horde) or the Azeroth Commerce
 * Authority (Alliance). A writ asks for a crafted item, delivered to the Contract Coordinator. Favor
 * buys mounts, a companion, account-wide profession titles and (later) recipes.
 *
 * Released under the MIT License.
 */

#ifndef MOD_SUPPLY_LOGISTICS_H
#define MOD_SUPPLY_LOGISTICS_H

#include "Define.h"

#include <type_traits>
#include <utility>
#include <vector>

class Creature;
class Item;
class Player;
class Quest;
class Unit;

namespace SupplyLogistics
{
    // Ids shared with tools/catalog.py.
    constexpr uint32 FACTION_HORDE = 2587;            // Durotar Supply and Logistics
    constexpr uint32 FACTION_ALLIANCE = 2586;         // Azeroth Commerce Authority
    constexpr uint32 ITEM_FAVOR = 90740;
    constexpr uint32 ITEM_SEALED_ELITE = 248769;
    constexpr uint32 ITEM_RECEIPT = 262902;
    constexpr uint32 ITEM_CONTAINER = 262917;
    constexpr uint32 NPC_TEXT_CRATE = 9531100;
    constexpr uint32 NPC_TEXT_RECEIPT = 9531101;
    constexpr uint32 NPC_TEXT_QUILL = 9531102;
    constexpr uint8 MAX_TIER = 4;                     // Artisan; Elite crates have no tier of their own

    // mod_supply_logistics_crate.kind
    enum CrateKind : uint8
    {
        KIND_HERBS = 1,
        KIND_ORE,
        KIND_TEXTILES,
        KIND_CURIOSITIES,
        KIND_FABRICS,
        KIND_INGOTS,
        KIND_PARTS,
    };

    struct Bundle
    {
        uint32 reagent;
        uint32 count;
    };

    struct Crate
    {
        uint32 item = 0;
        uint8 tier = 0;
        bool crafted = false;
        uint8 kind = 0;
        uint32 sealed = 0;
        std::vector<Bundle> bundles;
    };

    struct Writ
    {
        uint32 item = 0;
        uint32 quest = 0;
        uint8 tier = 0;
        uint16 skill = 0;
    };

    struct Title
    {
        uint32 id;
        uint32 item;
        uint16 skill;
    };

    // The six Certifications: CharTitles id, the item that unlocks it, the profession it needs.
    extern std::vector<Title> const TITLES;
    // Sealed Apprentice's to Artisan's Writ, by tier (index 0 unused).
    extern uint32 const SEALED_WRITS[MAX_TIER + 1];

    // Bot sessions: IsHeadless() on current playerbots cores, IsBot() on older ones, neither on a
    // core without playerbots.
    template <typename Session, typename = void>
    struct HasIsHeadless : std::false_type { };

    template <typename Session>
    struct HasIsHeadless<Session, std::void_t<decltype(std::declval<Session&>().IsHeadless())>> : std::true_type { };

    template <typename Session, typename = void>
    struct HasIsBot : std::false_type { };

    template <typename Session>
    struct HasIsBot<Session, std::void_t<decltype(std::declval<Session&>().IsBot())>> : std::true_type { };

    template <typename Session>
    bool IsBotSession(Session* session)
    {
        if constexpr (HasIsHeadless<Session>::value)
            return session->IsHeadless();
        else if constexpr (HasIsBot<Session>::value)
            return session->IsBot();
        else
            return false;
    }

    bool IsRealPlayer(Player* player);

    // --- Configuration and data (SupplyLogistics.cpp) ------------------------------------------------

    void LoadConfig();
    void LoadData();
    bool Enabled();

    Crate const* GetCrate(uint32 item);
    Writ const* GetWrit(uint32 item);
    std::vector<Crate> const& AllCrates();

    // --- What happens (SupplyLogistics.cpp) ---------------------------------------------------------

    // A creature this player is rewarded for has died: maybe a crate or a writ.
    void OnKillReward(Player* player, Unit* victim);
    // The player handed in a quest: reputation, and maybe a writ with a Sealed crate.
    void OnQuestRewarded(Player* player, Quest const* quest);
    // Gives the side's reputation: Durotar Supply and Logistics for the Horde races, the Azeroth
    // Commerce Authority for the Alliance's.
    void GiveReputation(Player* player, int32 amount, uint32 questLevel);

    // Item menus (Waylaid Crate, Forged Delivery Receipt, Forger's Quill).
    void ShowCrateMenu(Player* player, Item* crate);
    void SelectCrateOption(Player* player, Item* crate, uint32 action);
    void ShowReceiptMenu(Player* player, Item* receipt);
    void SelectReceiptOption(Player* player, uint32 action);
    void ShowQuillMenu(Player* player, Item* quill);
    void SelectQuillOption(Player* player, uint32 action);
    void OpenSealedWrit(Player* player, Item* sealed);
    void UseCertification(Player* player, Item* certification);

    // Titles: the account's Certifications, shown on characters with 300 skill.
    void LoadAccountTitles(Player* player);
    void SyncTitles(Player* player);
    // A skill has changed to `value` (skill-up, trainer or GM).
    void OnSkillChanged(Player* player, uint32 skill, uint32 value);
    // Unlocks the item a use spell left greyed out, when the script handled the use itself.
    void ReleaseItem(Player* player, Item* item);

    // The camp NPCs' jobs: quest giver or vendor flags, in their templates at startup (so a respawn
    // keeps them) and again when they spawn (in case the templates were reloaded).
    void SetTemplateNpcFlags();
    void SetNpcFlags(Creature* creature);
}

#endif
