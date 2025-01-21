import logging

from gbfauto.common.utils import get_response_body, keys_exists
from gbfauto.common.enums import BattleEnums, EventEnums

_log = logging.getLogger(__name__)


class AbilityResultResponse:
    """
    Class handling the response for ability results.
    """

    def __init__(self, responses):
        """
        Initializes the AbilityResultResponse instance.

        Args:
            responses: Response handler instance.
        """
        self.bot = responses.bot
        self.common = responses.common
        self.updator = responses.updator
        self.battle = self.bot.battle
        self.events_common = self.bot.events_common

    async def _update_win_conditions(self, win_event):
        """
        Updates win conditions based on the win event.

        Args:
            win_event: Event indicating win condition.
        """
        mob_killed = bool(win_event)
        quest_done = mob_killed and self.battle[BattleEnums.FINAL_BATTLE]

        await self.updator.update_win_conditions(mob_killed, quest_done)

    async def _update_boss_hp(self, r_body, resp):
        """
        Updates boss health based on the response.

        Args:
            r_body (dict): The response body in dictionary format.
            resp: The response object.
        """
        scenarios = await keys_exists(r_body, "scenario", resp_url=resp.url)

        if scenarios:
            boss_gauge_events = await self.common.gather_gauge_change_events(scenarios)
            await self.updator.update_boss_hp(boss_gauge_events)

            win_event = await self.common.gather_win_event(scenarios)
            await self._update_win_conditions(win_event)

    async def _update_turn(self, r_body, resp):
        """
        Updates the turn based on the response.

        Args:
            r_body (dict): The response body in dictionary format.
            resp: The response object.
        """
        nested_key = ["status", "turn"]
        turn_value = await keys_exists(r_body, *nested_key, resp_url=resp.url)

        if turn_value:
            await self.updator.update_turn(turn_value, resp.url)

    async def _update_summon_availability(self, r_body, resp):
        """
        Updates summon availability based on the response.

        Args:
            r_body (dict): The response body in dictionary format.
            resp: The response object.
        """
        nested_key = ["status", "summon_enable"]
        summon_enable = await keys_exists(r_body, *nested_key, resp_url=resp.url)

        # custom check because Python evaluates 0 as false
        if isinstance(summon_enable, int):
            await self.updator.update_summon_availability(summon_enable)

    async def _update_event_time(self, event=EventEnums.ABILITY_EVENT):
        """
        Updates event time based on the response.
        """
        await self.events_common.update_event_time(event)

    async def _check_for_popup(self, r_body):
        """
        Checks for a popup message and updates the event time if found.

        Args:
            r_body (dict): The response body.
        """

        if await self.common.is_popup(r_body):
            if popup_body := r_body.get("popup"):
                _log.debug(f"Popup found in ability_resp resp: '{popup_body}'")
                await self._update_event_time(BattleEnums.BATTLE_POPUP)

    async def _update_ability_result(self, r_body, resp):
        """
        Updates ability result based on the response.

        Args:
            r_body (dict): The response body in dictionary format.
            resp: The response object.
        """
        await self._update_event_time()
        await self._update_boss_hp(r_body, resp)
        await self._update_turn(r_body, resp)
        await self._update_summon_availability(r_body, resp)

    async def ability_result_handler(self, resp):
        """
        Handles the ability result response.

        Args:
            resp: The response object.
        """
        r_body = await get_response_body(resp)
        await self._check_for_popup(r_body)
        await self._update_ability_result(r_body, resp)

        _log.debug(f"Battle info updated from {resp.url}")
        _log.debug(f"Battle info: {self.battle}")
