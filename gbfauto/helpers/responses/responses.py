import logging

from gbfauto.helpers.responses.common import Common
from gbfauto.helpers.responses.valid_responses import ValidResponses
from gbfauto.helpers.responses.content_resp import ContentResponse
from gbfauto.helpers.responses.ability_resp import AbilityResultResponse
from gbfauto.helpers.responses.start_resp import StartResponse
from gbfauto.helpers.responses.n_attack_resp import NormalAttackResponse
from gbfauto.helpers.responses.q_info_resp import QuestInfoResponse
from gbfauto.helpers.responses.updator import Updator
from gbfauto.helpers.responses.summ_resp import SummonResponse
from gbfauto.helpers.responses.check_multi_start import CheckMultiStart
from gbfauto.helpers.responses.use_normal_item import UseNormalItemResponse

_log = logging.getLogger(__name__)


class Responses:
    """
    Class for handling various responses in the game.
    """

    def __init__(self, events):
        """
        Initializes the Responses object.

        Args:
            events: The parent events instance.
        """
        self.bot = events.bot
        self.events = events
        self.common = Common(self)
        self.updator = Updator(self)
        self.ability_result_resp = AbilityResultResponse(self)
        self.start_resp = StartResponse(self)
        self.normal_attack_resp = NormalAttackResponse(self)
        self.quest_info_resp = QuestInfoResponse(self)
        self.content_resp = ContentResponse(self)
        self.summon_resp = SummonResponse(self)
        self.check_multi_start = CheckMultiStart(self)
        self.use_normal_item_resp = UseNormalItemResponse(self)

    @staticmethod
    async def _filter(resp):
        """
        Filters unwanted responses.

        Args:
            resp: The response to filter.

        Returns:
            bool: True if the response is valid, False otherwise.
        """
        if valid := await ValidResponses.is_valid(resp):
            _log.debug(f"[EVENT][RESPONSE]: {resp.url}")
            return valid

    async def handle(self, resp):
        """
        Handles the response based on the URL.

        Args:
            resp: The response to handle.
        """
        if not await self._filter(resp):
            return

        handlers = {
            ValidResponses.CONTENT: self.content_resp.content_response_handler,
            ValidResponses.ABILITY_RESULT: self.ability_result_resp.ability_result_handler,
            ValidResponses.BATTLE_START: self.start_resp.start_response_handler,
            ValidResponses.NORMAL_ATTACK: self.normal_attack_resp.normal_attack_resp_handler,
            ValidResponses.QUEST_INFO: self.quest_info_resp.quest_info_response_handler,
            ValidResponses.SUMMON: self.summon_resp.summon_response_handler,
            ValidResponses.CHECK_MULTI_START: self.check_multi_start.check_multi_start_handler,
            ValidResponses.USE_NORMAL_ITEM: self.use_normal_item_resp.handler,
        }

        handler = None
        for url_keyword, handler_func in handlers.items():
            if url_keyword in resp.url:
                handler = handler_func
                break

        if handler:
            await handler(resp)
        else:
            _log.debug(f"Didn't find a valid response to handle for {resp.url}..")
