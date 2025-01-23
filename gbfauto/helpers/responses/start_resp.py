import logging

from gbfauto.common.utils import get_response_body, keys_exists
from gbfauto.common.enums import BattleEnums, EventEnums

_log = logging.getLogger(__name__)


class StartResponse:
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
        self.updator = responses.updator
        self.resp_common = responses.common
        self.battle = self.bot.battle
        self.events_common = self.bot.events_common

        self._b_info = [
            {BattleEnums.TOTAL_BATTLES: ["battle", "total"]},
            {BattleEnums.CURRENT_BATTLE: ["battle", "count"]},
            {BattleEnums.CURRENT_TURN: ["turn"]},
            {BattleEnums.BOSS_HPS: ["boss", "param"]},
        ]

    async def _update_battle_info(self, r_body, resp):
        """
        Updates battle information based on the response body.

        Args:
            r_body (dict): The response body in dictionary format.
            resp: The response object.
        """
        # Always update FULL_AUTO to false when you get a start.json resp
        self.battle[BattleEnums.FULL_AUTO] = False

        # Scan through _b_info and update battle info
        # includes: total_battles, current_battle, current_turn, bosses (hp, names, etc.)
        for p_info in self._b_info:
            k, nested_key = list(p_info.items())[0]
            if info := await keys_exists(r_body, *nested_key, resp_url=resp.url):
                if isinstance(info, list):
                    await self.resp_common.update_boss_hp(info)
                    continue

                self.battle[k] = int(info)

    async def _update_is_final_battle(self):
        await self.updator.update_final_battle()

    async def _update_battle(self, r_body, resp):
        """
        Updates battle information, win conditions, and summon availability based on the response.

        Args:
            r_body (dict): The response body in dictionary format.
            resp: The response object.
        """
        await self._update_is_final_battle()
        await self._update_battle_info(r_body, resp)
        await self.resp_common.update_summon_availability(r_body, resp)

    async def _check_for_popup(self, r_body):
        """
        Checks for a popup message and updates the event time if found.

        Args:
            r_body (dict): The response body.
        """
        if r_body.get("redirect"):
            _log.debug("'start.json' returned a redirect. Battle is over.")
            self.battle[BattleEnums.BOSS_HPS] = {}
            self.battle[BattleEnums.BOSS_KILLED] = True
            self.events_common.update_event_time(EventEnums.BATTLE_END_EVENT)

    async def start_response_handler(self, resp):
        """
        Handles the start response.

        Args:
            resp: The response object.
        """
        r_body = await get_response_body(resp)
        await self._check_for_popup(r_body)
        await self.events_common.update_event_time(EventEnums.START_EVENT)
        await self.resp_common.update_popup_status(r_body, resp)
        await self.resp_common.update_battle_from_scenarios(r_body, resp)
        await self._update_battle(r_body, resp)

        _log.debug(f"Start response handled from '{resp.url}'")
        _log.debug(f"Battle Status: {self.battle}")
