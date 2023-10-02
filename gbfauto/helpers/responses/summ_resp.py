import logging

from gbfauto.common.utils import get_response_body, keys_exists

_log = logging.getLogger(__name__)


class SummonResponse:
    """
    Class handling the response for a summon event.
    """

    def __init__(self, responses):
        """
        Initializes the SummonResponse instance.

        Args:
            responses: Response handler instance.
        """
        self.bot = responses.bot
        self.common = responses.common
        self.updator = responses.updator
        self.battle = self.bot.battle

    async def _update_win_conditions(self, win_event):
        """
        Updates win conditions based on battle status and summon event.

        Args:
            win_event: The win event information.
        """
        quest_done = False
        mob_killed = True if win_event else False

        if self.battle["current_battle"] == self.battle["total_battles"]:
            if mob_killed:
                quest_done = True

        await self.updator.update_win_conditions(mob_killed, quest_done)

    async def _update_boss_hp(self, r_body, resp):
        """
        Updates boss HP and win conditions based on the response.

        Args:
            r_body: The response body in dictionary format.
            resp: The response object.
        """
        if scenarios := await keys_exists(r_body, "scenario", resp_url=resp.url):
            boss_gauge_events = await self.common.gather_gauge_change_events(scenarios)
            await self.updator.update_boss_hp(boss_gauge_events)

            win_event = await self.common.gather_win_event(scenarios)
            await self._update_win_conditions(win_event)

    async def _update_turn(self, r_body, resp):
        """
        Updates the current turn based on the response.

        Args:
            r_body: The response body in dictionary format.
            resp: The response object.
        """
        nested_key = ["status", "turn"]
        if turn := await keys_exists(r_body, *nested_key, resp_url=resp.url):
            await self.updator.update_turn(turn, resp.url)

    async def _update_summon_availability(self, r_body, resp):
        """
        Updates summon availability based on the response.

        Args:
            r_body: The response body in dictionary format.
            resp: The response object.
        """
        nested_key = ["status", "summon_enable"]
        summon_enable = await keys_exists(r_body, *nested_key, resp_url=resp.url)

        # custom check because python evaluates 0 as false
        if isinstance(summon_enable, int):
            await self.updator.update_summon_availability(summon_enable)

    async def _update_battle(self, r_body, resp):
        """
        Updates battle information, win conditions, and summon availability based on the response.

        Args:
            r_body: The response body in dictionary format.
            resp: The response object.
        """
        await self._update_boss_hp(r_body, resp)
        await self._update_turn(r_body, resp)
        await self._update_summon_availability(r_body, resp)

    async def summon_response_handler(self, resp):
        """
        Handles the summon response.

        Args:
            resp: The response object.
        """
        r_body = await get_response_body(resp)
        await self._update_battle(r_body, resp)

        _log.debug(f"Battle info updated from {resp.url}")
        _log.debug(f"Battle info: {self.battle}")
