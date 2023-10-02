import logging
from gbfauto.common.utils import get_response_body, keys_exists

_log = logging.getLogger(__name__)


class QuestInfoResponse:
    def __init__(self, responses):
        """
        Initializes the QuestInfoResponse object.

        Args:
            responses: The parent responses object.
        """
        self.bot = responses.bot
        self.common = responses.common
        self.battle = self.bot.battle

    async def _update_quest_ap_cost(self, r_body, resp):
        """
        Updates the action point (AP) cost for the quests.

        Args:
            r_body (dict): The response body.
            resp: The response object.
        """
        if quests := await keys_exists(r_body, "episode", resp_url=resp.url):
            for quest in quests:
                if ap_cost := quest.get("use_action_point"):
                    ap_cost = int(ap_cost)
                    await self.common.update_q_ap_cost(ap_cost)

    async def _update_quest_info(self, r_body, resp):
        """
        Updates quest information based on the response.

        Args:
            r_body (dict): The response body.
            resp: The response object.
        """
        # Update quest AP cost
        await self._update_quest_ap_cost(r_body, resp)

    async def quest_info_response_handler(self, resp):
        """
        Handles the quest info response.

        Args:
            resp: The response object.
        """
        r_body = await get_response_body(resp)
        await self._update_quest_info(r_body, resp)

        _log.debug(f"Quest info updated from {resp.url}")
        _log.debug(f"Quest info: {self.battle}")
