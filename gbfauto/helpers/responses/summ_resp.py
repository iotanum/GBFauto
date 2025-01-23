import logging

from gbfauto.common.utils import get_response_body
from gbfauto.common.enums import EventEnums

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
        self.resp_common = responses.common
        self.events_common = self.bot.events_common
        self.battle = self.bot.battle

    async def _update_battle(self, r_body, resp):
        """
        Updates battle information, win conditions, and summon availability based on the response.

        Args:
            r_body: The response body in dictionary format.
            resp: The response object.
        """
        await self.resp_common.update_turn(r_body, resp)
        await self.resp_common.update_summon_availability(r_body, resp)

    async def summon_response_handler(self, resp):
        """
        Handles the summon response.

        Args:
            resp: The response object.
        """
        r_body = await get_response_body(resp)
        await self.events_common.update_event_time(EventEnums.SUMMON_EVENT)
        await self.resp_common.update_popup_status(r_body, resp)
        await self.resp_common.update_battle_from_scenarios(r_body, resp)
        await self._update_battle(r_body, resp)

        _log.debug(f"Summon response handled from '{resp.url}'")
        _log.debug(f"Battle Status: {self.battle}")
