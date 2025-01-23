import logging

from gbfauto.common.enums import BattleEnums

_log = logging.getLogger(__name__)


class Updator:
    def __init__(self, responses):
        self.bot = responses.bot
        self.p_status = self.bot.p_status
        self.battle = self.bot.battle

    async def update_q_ap_cost(self, q_ap_cost):
        """
        Updates the quest Action Point (AP) cost.

        Args:
            q_ap_cost (int): The new quest AP cost.
        """
        self.battle[BattleEnums.QUEST_AP_COST] = q_ap_cost
        _log.debug(f"Updating quest AP cost with '{q_ap_cost}'...")

    async def update_final_battle(self):
        current_battle = self.battle.get(BattleEnums.CURRENT_BATTLE, 0)
        total_battles = self.battle.get(BattleEnums.TOTAL_BATTLES)
        if current_battle == total_battles:
            _log.debug("Final battle detected!")
            self.battle[BattleEnums.FINAL_BATTLE] = True
        else:
            self.battle[BattleEnums.FINAL_BATTLE] = False
