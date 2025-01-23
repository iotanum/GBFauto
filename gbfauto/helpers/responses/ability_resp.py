import logging

from gbfauto.common.utils import get_response_body
from gbfauto.common.enums import EventEnums

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
        self.resp_common = responses.common
        self.events_common = self.bot.events_common
        self.battle = self.bot.battle

    async def _update_ability_result(self, r_body, resp):
        """
        Updates ability result based on the response.
        """
        await self.resp_common.update_turn(r_body, resp)
        await self.resp_common.update_summon_availability(r_body, resp)

    async def ability_result_handler(self, resp):
        """
        Handles the ability result response.

        Args:
            resp: The response object.
        """
        r_body = await get_response_body(resp)
        await self.events_common.update_event_time(EventEnums.ABILITY_EVENT)
        await self.resp_common.update_popup_status(r_body, resp)
        await self.resp_common.update_battle_from_scenarios(r_body, resp)
        await self._update_ability_result(r_body, resp)

        _log.debug(f"Ability response handled from '{resp.url}'")
        _log.debug(f"Battle Status: {self.battle}")
