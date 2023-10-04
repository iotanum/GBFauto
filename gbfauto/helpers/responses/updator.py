import logging

from gbfauto.common.enums import BattleEnums

_log = logging.getLogger(__name__)


class Updator:
    def __init__(self, responses):
        self.bot = responses.bot
        self.p_status = self.bot.p_status
        self.battle = self.bot.battle
        self.battle_common = self.bot.utils.battle_common

    @staticmethod
    async def _get_boss_id(hp_event):
        """
        Gets the boss ID from the HP event.

        Args:
            hp_event (dict): HP event containing boss information.

        Returns:
            int: The boss ID.
        """
        boss_id = hp_event.get("number") or hp_event.get("pos")

        if boss_id is not None:
            return int(boss_id) + 1 if "pos" in hp_event else int(boss_id)
        else:
            return 1  # Default value

    async def update_boss_hp(self, boss_hp_scenarios):
        """
        Updates the HP of bosses based on the provided scenarios.

        Args:
            boss_hp_scenarios (list or dict): Scenarios containing boss HP information.
        """
        try:
            bosses = {}

            if not isinstance(boss_hp_scenarios, list):
                boss_hp_scenarios = list(boss_hp_scenarios.values())

            for hp_event in boss_hp_scenarios:
                boss_id = await self._get_boss_id(hp_event)

                hp_current = int(hp_event["hp"])
                hp_max = int(hp_event["hpmax"])
                percent = round((hp_current / hp_max) * 100, 2)

                bosses[boss_id] = percent

            # Check if any boss has non-zero HP and update win conditions accordingly
            mob_killed = any(boss_hp > 0 for boss_hp in bosses.values())
            quest_done = mob_killed and await self.battle_common.is_final_battle()

            await self.update_win_conditions(mob_killed, quest_done)
            self.battle[BattleEnums.BOSS_HPS] = bosses

        except Exception as e:
            _log.error(f"Error while updating boss HP: {e}")

    async def update_q_ap_cost(self, q_ap_cost):
        """
        Updates the quest Action Point (AP) cost.

        Args:
            q_ap_cost (int): The new quest AP cost.
        """
        self.battle[BattleEnums.QUEST_AP_COST] = q_ap_cost
        _log.debug(f"Updating quest AP cost with '{q_ap_cost}'...")

    async def update_turn(self, turn, resp_url):
        """
        Updates the current turn.

        Args:
            turn (int): The new current turn value.
            resp_url (str): The response URL for logging purposes.
        """
        self.battle[BattleEnums.CURRENT_TURN] = turn
        _log.debug(f"Updating turn with '{turn}' from {resp_url}...")

    async def update_summon_availability(self, summon_enable):
        """
        Updates the summon availability.

        Args:
            summon_enable (int): The summon availability status (0 or 1).
        """
        summon_available = bool(int(summon_enable))
        self.battle[BattleEnums.SUMMON_AVAILABLE] = summon_available
        _log.debug(f"Updating summon availability with '{summon_available}'...")

    async def update_win_conditions(self, mob_killed, quest_done):
        """
        Updates the win conditions based on battle status.

        Args:
            mob_killed (bool): True if the mob is killed, False otherwise.
            quest_done (bool): True if the quest is done, False otherwise.
        """
        self.battle[BattleEnums.BOSS_KILLED] = mob_killed
        self.battle[BattleEnums.QUEST_DONE] = quest_done
        _log.debug(
            f"Updating win condition: Wave mob killed: '{mob_killed}', Quest done: '{quest_done}'..."
        )
