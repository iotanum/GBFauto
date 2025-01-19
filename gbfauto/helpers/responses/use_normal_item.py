import logging

from gbfauto.common.utils import get_response_body

_log = logging.getLogger(__name__)


class UseNormalItemResponse:
    """
    Class handling the response for the start of a battle.
    """

    def __init__(self, responses):
        """
        Initializes the StartResponse instance.

        Args:
            responses: Response handler instance.
        """
        self.bot = responses.bot
        self.p_status = self.bot.p_status
        self.battle = self.bot.battle
        self.battle_common = self.bot.battle_common

    async def _update_current_ep(self, r_body):
        """
        Updates the current Event Points (EP) for the player.

        Args:
            r_body (dict): The player's status.
        """
        current_ep = r_body.get("after", None)

        if current_ep is not None:
            _log.debug(f"Updating 'p_status' 'current_ep' with '{current_ep}'")
            self.p_status["current_ep"] = current_ep
            await self.battle_common.need_ep()

    async def handler(self, resp):
        """
        Handles the start response.

        Args:
            resp: The response object.
        """
        r_body = await get_response_body(resp)
        await self._update_current_ep(r_body)

        _log.debug(f"Player status updated from {resp.url}")
        _log.debug(f"Play status: {self.p_status}")
