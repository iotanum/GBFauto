from gbfauto.common.enums import BattleEnums
import typing


class BattleCommon:
    def __init__(self, utils):
        """
        Initializes the BattleCommon instance.

        Args:
            utils: Utility functions instance.
        """
        self.bot = utils.bot
        self.utils = utils
        self.battle = self.bot.battle
        self.queues = self.bot.queues
        self.p_status = self.bot.p_status

    async def get_current_battle(self) -> typing.Any:
        """
        Get the current battle information.

        Returns:
            Any: Current battle information.
        """
        return self.battle[BattleEnums.CURRENT_BATTLE]

    async def get_current_turn(self) -> typing.Any:
        """
        Get the current turn information.

        Returns:
            Any: Current turn information.
        """
        return self.battle[BattleEnums.CURRENT_TURN]

    async def is_final_battle(self) -> bool:
        """
        Checks if the current battle is the final battle.

        Returns:
            bool: True if it's the final battle, False otherwise.
        """
        return self.battle.get("current_battle") == self.battle.get("total_battles", 0)

    async def need_ap(self):
        """
        Checks if Action Points (AP) are needed for the battle.

        Updates the 'need_ap' flag in battle information.
        """
        q_ap_cost = self.battle.get("q_ap_cost", 0)
        current_ap = self.p_status.get("current_ap", 0)

        need_ap = current_ap < q_ap_cost
        self.battle["need_ap"] = need_ap

    async def need_ep(self):
        """
        Checks if Event Points (EP) are needed for the battle.

        Updates the 'need_ep' flag in battle information.
        """
        q_ep_cost = self.battle.get("q_ep_cost", 0)
        current_ep = self.p_status.get("current_ep", 0)

        need_ep = current_ep < q_ep_cost
        self.battle["need_ep"] = need_ep

    async def is_queue_this_turn(self):
        """
        Checks if there's a queue in the current turn.
        """
        if not self.queues:
            return False

        current_turn = await self.get_current_turn()
        current_battle = await self.get_current_battle()
        try:
            return self.queues[current_battle][current_turn]
        except KeyError:
            return False

    async def can_see_enemy_hp(self) -> bool:
        """
        Checks if enemy HP information is visible.

        Returns:
            bool: True if visible, False otherwise.
        """
        hp_ele = await self.utils.bs(
            find=(
                "div",
                {
                    "class": "btn-enemy-gauge prt-enemy-percent alive",
                    "style": "display: block;",
                },
            )
        )
        return hp_ele
