import logging

from gbfauto.misc.utils import get_response_body, keys_exists


_log = logging.getLogger(__name__)


class QuestInfoResponse:
    def __init__(self, responses):
        self.bot = responses.bot
        self.utils = responses.utils
        self.battle = self.bot.events.battle
        self.p_status = self.bot.events.p_status

    async def _update_quest_ap_cost(self, quests):
        for quest in quests:
            if ap_cost := quest.get("use_action_point"):
                self.battle["q_ap_cost"] = int(ap_cost)
                _log.debug(f"Updated 'q_ap_cost' in 'battle' with '{ap_cost}'")

    async def _update_quest_info(self, r_body, resp):
        if quests := await keys_exists(r_body, "episode", resp_url=resp.url):
            await self._update_quest_ap_cost(quests)

        _log.debug(f"Battle info updated from {resp.url}")
        _log.debug(f"Battle info: {self.battle}")

    async def quest_info_response_handler(self, resp):
        r_body = await get_response_body(resp)
        await self._update_quest_info(r_body, resp)
