import logging

from gbfauto.helpers.responses.utils import Utils
from gbfauto.helpers.responses.valid_responses import ValidResponses
from gbfauto.helpers.responses.content_resp import ContentResponse
from gbfauto.helpers.responses.ability_resp import AbilityResultResponse
from gbfauto.helpers.responses.start_resp import StartResponse
from gbfauto.helpers.responses.n_attack_resp import NormalAttackResponse
from gbfauto.helpers.responses.q_info_resp import QuestInfoResponse
from gbfauto.helpers.responses.updator import Updator


_log = logging.getLogger(__name__)


class Responses:
    def __init__(self, bot):
        self.bot = bot
        self.utils = Utils(self)
        self.updator = Updator(self)
        self.a_r_resp = AbilityResultResponse(self)
        self.start_resp = StartResponse(self)
        self.n_attack_resp = NormalAttackResponse(self)
        self.q_info_resp = QuestInfoResponse(self)
        self.content_resp = ContentResponse(self)

    async def handle(self, resp):
        valid_resp = await self.utils._filter(resp)
        if not valid_resp:
            return

        if ValidResponses.CONTENT in resp.url:
            await self.content_resp.content_response_handler(resp)
        elif ValidResponses.ABILITY_RESULT in resp.url:
            await self.a_r_resp.ability_result_handler(resp)
        elif ValidResponses.BATTLE_START in resp.url:
            await self.start_resp.start_response_handler(resp)
        elif ValidResponses.NORMAL_ATTACK in resp.url:
            await self.n_attack_resp.normal_attack_resp_handler(resp)
        elif ValidResponses.QUEST_INFO in resp.url:
            await self.q_info_resp.quest_info_response_handler(resp)
        else:
            _log.debug(f"Didn't find a valid response to handle for {resp.url}..")
            pass
