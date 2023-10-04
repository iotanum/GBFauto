import logging

from gbfauto.common.utils import get_response_body, multiple_keys_exists


_log = logging.getLogger(__name__)


class ContentResponse:
    def __init__(self, responses):
        """
        Initializes the ContentResponse object.

        Args:
            responses: The parent responses object.
        """
        self.bot = responses.bot
        self.common = responses.common
        self.p_status = self.bot.p_status
        self.battle_common = self.bot.utils.battle_common

    @staticmethod
    async def _fix_content_response_body(r_body):
        """
        Removes 'data' key from the response body.

        Args:
            r_body (dict): The response body.

        Returns:
            dict: The modified response body.
        """
        exclude_keys = ["data"]
        return {k: r_body[k] for k in set(list(r_body.keys())) - set(exclude_keys)}

    async def _update_current_ep(self, p_status, resp):
        """
        Updates the current Event Points (EP) for the player.

        Args:
            p_status (dict): The player's status.
            resp: The response object.
        """
        nested_keys = [
            ["option", "status", "status", "now_battle_point"],
            ["option", "mydata_assets", "mydata", "status", "now_battle_point"],
            ["option", "user_status", "now_battle_point"],
        ]

        current_ep = await multiple_keys_exists(
            p_status, nested_keys, resp_url=resp.url
        )

        if current_ep is not None:
            _log.debug(f"Updating 'p_status' 'current_ep' with '{current_ep}'")
            self.p_status["current_ep"] = current_ep
            await self.battle_common.need_ep()

    async def _update_current_ap(self, p_status, resp):
        """
        Updates the current Action Points (AP) for the player.

        Args:
            p_status (dict): The player's status.
            resp: The response object.
        """
        nested_keys = [
            ["option", "status", "status", "now_action_point"],
            ["option", "mydata_assets", "mydata", "status", "now_action_point"],
            ["option", "user_status", "now_action_point"],
        ]

        current_ap = await multiple_keys_exists(
            p_status, nested_keys, resp_url=resp.url
        )

        if current_ap is not None:
            _log.debug(f"Updating 'p_status' 'current_ap' with '{current_ap}'")
            self.p_status["current_ap"] = current_ap
            await self.battle_common.need_ap()

    async def _update_player_status(self, r_body, resp):
        """
        Updates the player's status based on the response.

        Args:
            r_body (dict): The response body.
            resp: The response object.
        """
        _log.debug(f"Trying to update 'p_status' from '{resp.url}'")

        await self._update_current_ap(r_body, resp)
        await self._update_current_ep(r_body, resp)

    async def content_response_handler(self, resp):
        """
        Handles the content response.

        Args:
            resp: The response object.
        """
        r_body = await get_response_body(resp)
        r_body = await self._fix_content_response_body(r_body)

        # update user status in events
        await self._update_player_status(r_body, resp)

        _log.debug(f"Player status updated from {resp.url}")
        _log.debug(f"Player status: {self.p_status}")
