import typing
import logging

from gbfauto.common.enums import BattleEnums


_log = logging.getLogger(__name__)


class BattleCommon:
    def __init__(self, bot):
        """
        Initializes the BattleCommon instance.

        Args:
            bot: Utility functions instance.
        """
        self.bot = bot
        self.utils = self.bot.utils
        self.battle = self.bot.battle
        self.queues = self.bot.queues
        self.p_status = self.bot.p_status

    async def in_battle_url(self) -> bool:
        """
        Checks if the bot is in a battle url.

        Returns:
            bool: True if in a battle url, False otherwise.
        """
        possible_urls = ["#raid", "#raid_multi"]
        current_url = await self.utils.get_current_url()
        return any(url in current_url for url in possible_urls)

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

    async def refresh_from_queue_this_turn(self):
        """
        Checks if there's a refresh queue in the current turn.
        """
        if not self.queues:
            return False

        current_turn = await self.get_current_turn()
        current_battle = await self.get_current_battle()
        try:
            return self.queues[current_battle][current_turn]["refresh"]
        except KeyError:
            return False

    async def can_see_enemy_hp(self) -> bool:
        """
        Checks if enemy HP information is visible.

        Returns:
            bool: True if visible, False otherwise.
        """
        hp_ele = await self.bot.page.query_selector(
            "div.btn-enemy-gauge.prt-enemy-percent.alive[style*='display: block;']"
        )
        return hp_ele is not None

    async def get_enemy_hp(self) -> typing.List[int]:
        """
        Gets the enemy HP information.

        Returns:
            list: List of enemy HPs.
        """
        if await self.can_see_enemy_hp():
            hp_eles = await self.bot.page.query_selector_all(
                "span.txt-gauge-value[id*='enemy-hp']"
            )
            return [int(await hp_ele.text_content()) for hp_ele in hp_eles]

    async def enable_full_auto(self):
        """
        Enables full auto mode in the most efficient way using Playwright.
        """
        fa_ele = self.bot.page.locator("div.txt-auto-setting")
        if await fa_ele.is_visible():
            enabled_ele = fa_ele.locator(
                "div.btn-ready-auto.anim-simple-fadein"
            )
            if enabled_ele:
                # Sadly need to enable the key here to get the maximum responsiveness out of the bot
                _log.debug(f"Updating '{BattleEnums.FULL_AUTO}' status to True in helper function.")
                self.battle[BattleEnums.FULL_AUTO] = True

            await fa_ele.click(force=True)

    async def refreshed_on_this_event(self, event, refreshed_event):
        """
        Checks if the bot refreshed on this event.

        Args:
            event (dict): The event to check.
            refreshed_event (dict): The refreshed event.

        Returns:
            bool: True if refreshed on this event, False otherwise.
        """
        return refreshed_event == event
