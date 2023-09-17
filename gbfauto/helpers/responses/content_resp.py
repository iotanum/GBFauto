import logging

from gbfauto.misc.utils import get_response_body, keys_exists


_log = logging.getLogger(__name__)


class ContentResponse:
    def __init__(self, responses):
        self.bot = responses.bot
        self.utils = responses.utils
        self.p_status = self.bot.events.p_status

    async def _parse_player_status(self, p_status, resp_url):
        _log.debug(f"Updating player status from {resp_url}...")

        if current_ep := await keys_exists(p_status, "now_battle_point"):
            _log.debug(f"Updating 'p_status' 'current_ep' with '{current_ep}'")
            self.p_status["current_ep"] = current_ep
            await self.utils.need_ep()

        if current_ap := await keys_exists(p_status, "now_action_point"):
            _log.debug(f"Updating 'p_status' 'current_ap' with '{current_ap}'")
            self.p_status["current_ap"] = current_ap
            await self.utils.need_ap()

    async def _update_player_status(self, r_body, resp):
        u_status_key = ["option", "user_status"]
        if u_status := await keys_exists(r_body, *u_status_key, resp_url=resp.url):
            await self._parse_player_status(u_status, resp.url)
            _log.debug(f"Player status: {self.p_status}")

    async def content_response_handler(self, resp):
        r_body = await get_response_body(resp)
        r_body = await self.utils._fix_content_response_body(r_body)

        # update user status in events
        await self._update_player_status(r_body, resp)
