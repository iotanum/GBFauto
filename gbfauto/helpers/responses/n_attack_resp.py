import logging

from gbfauto.common.utils import get_response_body
from gbfauto.common.enums import EventEnums

_log = logging.getLogger(__name__)


class NormalAttackResponse:
    def __init__(self, responses):
        """
        Initializes the NormalAttackResponse object.

        Args:
            responses: The parent responses object.
        """
        self.bot = responses.bot
        self.resp_common = responses.common
        self.events_common = self.bot.events_common
        self.battle = self.bot.battle

    async def _update_battle(self, r_body, resp):
        """
        Updates battle information based on the response.
        """
        await self.resp_common.update_turn(r_body, resp)
        await self.resp_common.update_summon_availability(r_body, resp)

    async def normal_attack_resp_handler(self, resp):
        """
        Handles the normal attack response.

        Args:
            resp: The response object.
        """
        r_body = await get_response_body(resp)
        await self.events_common.update_event_time(EventEnums.NORMAL_ATTACK_EVENT)
        await self.resp_common.update_popup_status(r_body, resp)
        await self.resp_common.update_battle_from_scenarios(r_body, resp)
        await self._update_battle(r_body, resp)

        _log.debug(f"Normal attack response handled from '{resp.url}'")
        _log.debug(f"Battle Status: {self.battle}")
