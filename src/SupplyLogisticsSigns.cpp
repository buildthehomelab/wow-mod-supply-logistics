/*
 * mod-supply-logistics: the Tradeskill Signpost toys (the Advertising License's reward).
 *
 * Using the toy casts its spell, which puts the signpost up in front of you for a minute (a plain timed summon,
 * owned by you). Talk to it to pick one of your professions: the post makes way for that profession's sign,
 * which stands for half an hour. A new sign takes your last one down. The Orcish sign is one model; a Dwarven
 * sign is the Ironforge signpost with a board hung on it where WoW Forever hangs it.
 *
 * Released under the MIT License.
 */

#include "SupplyLogistics.h"

#include "Creature.h"
#include "CreatureAI.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "ScriptedGossip.h"
#include "TemporarySummon.h"

#include <cmath>
#include <iterator>
#include <mutex>
#include <unordered_map>
#include <vector>

using namespace SupplyLogistics;

namespace
{
    // Ids shared with tools/catalog.py (SIGNPOSTS, SIGNS, TEXT_SIGNPOST, SIGN_SECONDS, BOARD_OFFSET, BOARD_TURN).
    constexpr uint32 POST_ORCISH = 262713;
    constexpr uint32 POST_DWARVEN = 262727;
    constexpr uint32 NPC_TEXT_SIGNPOST = 9531103;
    constexpr uint32 NPC_TEXT_SIGNPOST_NONE = 9531104;
    constexpr uint32 NPC_TEXT_SIGNPOST_NOT_YOURS = 9531105;
    constexpr Milliseconds SIGN_TIME = 30min;
    constexpr float BOARD_FORWARD = 0.0f, BOARD_LEFT = 1.0f, BOARD_UP = 0.04f, BOARD_TURN = 1.5707964f;

    struct Sign
    {
        uint32 skill;
        uint32 orcish;      // the Orcish sign
        uint32 dwarven;     // the Dwarven signpost
        uint32 board;       // the board on it
        char const* name;
    };

    Sign const SIGNS[] = {
        { 171, 262718, 262728, 9531103, "Alchemy" },
        { 164, 262720, 262729, 9531104, "Blacksmithing" },
        { 185, 262721, 262730, 9531105, "Cooking" },
        { 333, 262722, 262731, 9531106, "Enchanting" },
        { 202, 262723, 262732, 9531107, "Engineering" },
        { 165, 262724, 262733, 9531108, "Leatherworking" },
        { 197, 262725, 262734, 9531109, "Tailoring" },
    };

    // Each player's standing sign (one or two creatures), so a new one takes the last down. Gossip runs in the
    // map threads, so guarded.
    std::mutex signsLock;
    std::unordered_map<ObjectGuid, std::vector<ObjectGuid>> signsByPlayer;

    bool IsOwner(Player* player, Creature* post)
    {
        return post->IsSummon() && post->GetSummonerGUID() == player->GetGUID();
    }

    void TakeDownLastSign(Player* player)
    {
        std::vector<ObjectGuid> last;
        {
            std::lock_guard<std::mutex> guard(signsLock);
            auto it = signsByPlayer.find(player->GetGUID());
            if (it == signsByPlayer.end())
                return;
            last.swap(it->second);
            signsByPlayer.erase(it);
        }
        for (ObjectGuid const& guid : last)
            if (Creature* sign = ObjectAccessor::GetCreature(*player, guid))
                sign->DespawnOrUnsummon();
    }

    TempSummon* PutUp(Player* player, uint32 entry, float x, float y, float z, float o)
    {
        return player->SummonCreature(entry, x, y, z, o, TEMPSUMMON_TIMED_DESPAWN, uint32(SIGN_TIME.count()));
    }

    void PutUpSign(Player* player, Creature* post, Sign const& sign)
    {
        TakeDownLastSign(player);
        // Where the post stands, facing whoever chose the sign.
        float x = post->GetPositionX(), y = post->GetPositionY(), z = post->GetPositionZ();
        float o = post->GetAngle(player);
        std::vector<ObjectGuid> placed;
        if (post->GetEntry() == POST_ORCISH)
        {
            if (TempSummon* s = PutUp(player, sign.orcish, x, y, z, o))
                placed.push_back(s->GetGUID());
        }
        else if (post->GetEntry() == POST_DWARVEN)
        {
            if (TempSummon* s = PutUp(player, sign.dwarven, x, y, z, o))
                placed.push_back(s->GetGUID());
            // Forward and left of the post, as it faces.
            float bx = x + BOARD_FORWARD * std::cos(o) - BOARD_LEFT * std::sin(o);
            float by = y + BOARD_FORWARD * std::sin(o) + BOARD_LEFT * std::cos(o);
            if (TempSummon* s = PutUp(player, sign.board, bx, by, z + BOARD_UP, Position::NormalizeOrientation(o + BOARD_TURN)))
                placed.push_back(s->GetGUID());
        }
        post->DespawnOrUnsummon();
        std::lock_guard<std::mutex> guard(signsLock);
        signsByPlayer[player->GetGUID()] = std::move(placed);
    }

    // The post stands still, does nothing, and turns to whoever put it up.
    class SignpostAI : public NullCreatureAI
    {
    public:
        explicit SignpostAI(Creature* creature) : NullCreatureAI(creature) { }

        void IsSummonedBy(WorldObject* summoner) override
        {
            if (summoner)
                me->SetFacingToObject(summoner);
        }
    };

    class SupplySignpost : public CreatureScript
    {
    public:
        SupplySignpost() : CreatureScript("npc_supply_signpost") { }

        CreatureAI* GetAI(Creature* creature) const override
        {
            return new SignpostAI(creature);
        }

        bool OnGossipHello(Player* player, Creature* post) override
        {
            ClearGossipMenuFor(player);
            if (!IsOwner(player, post))
            {
                SendGossipMenuFor(player, NPC_TEXT_SIGNPOST_NOT_YOURS, post);
                return true;
            }
            bool any = false;
            for (uint32 i = 0; i < std::size(SIGNS); ++i)
                if (player->HasSkill(SIGNS[i].skill))
                {
                    AddGossipItemFor(player, GOSSIP_ICON_TRAINER, SIGNS[i].name, GOSSIP_SENDER_MAIN, i);
                    any = true;
                }
            SendGossipMenuFor(player, any ? NPC_TEXT_SIGNPOST : NPC_TEXT_SIGNPOST_NONE, post);
            return true;
        }

        bool OnGossipSelect(Player* player, Creature* post, uint32 /*sender*/, uint32 action) override
        {
            CloseGossipMenuFor(player);
            if (Enabled() && IsOwner(player, post) && post->IsAlive() && action < std::size(SIGNS)
                && player->HasSkill(SIGNS[action].skill))
                PutUpSign(player, post, SIGNS[action]);
            return true;
        }
    };
}

void AddSupplyLogisticsSignScripts()
{
    new SupplySignpost();
}
