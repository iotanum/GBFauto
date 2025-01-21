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
        self.common = responses.common
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

        if await self.common.is_popup(r_body):
            if r_body.get("redirect"):
                _log.debug("'start.json' returned a redirect. Battle is over.")
                self.battle[BattleEnums.BOSS_HPS] = {}
                self.battle[BattleEnums.BOSS_KILLED] = True
                return

        # Scan through _b_info and update battle info
        # includes: total_battles, current_battle, current_turn, bosses (hp, names, etc.)
        for p_info in self._b_info:
            k, nested_key = list(p_info.items())[0]
            if info := await keys_exists(r_body, *nested_key, resp_url=resp.url):
                _log.debug(f"Updating battle info for '{k}' with '{info}'...")

                if isinstance(info, list):
                    await self.updator.update_boss_hp(info)
                    continue

                self.battle[k] = int(info)

    async def _update_win_conditions(self):
        """
        Updates win conditions based on battle status.
        """
        mob_killed = not self.battle[BattleEnums.BOSS_HPS]
        quest_done = mob_killed and self.battle[BattleEnums.FINAL_BATTLE]
        await self.updator.update_win_conditions(mob_killed, quest_done)

    async def _update_summon_availability(self, r_body, resp):
        """
        Updates summon availability based on the response.

        Args:
            r_body (dict): The response body in dictionary format.
            resp: The response object.
        """
        key = ["summon_enable"]
        summon_enable = await keys_exists(r_body, *key, resp_url=resp.url)

        # Custom check because Python evaluates 0 as false
        if isinstance(summon_enable, int):
            await self.updator.update_summon_availability(summon_enable)

    async def _update_event_time(self, event=EventEnums.START_EVENT):
        """
        Updates event time based on the response.
        """
        await self.events_common.update_event_time(event)

    async def _update_is_final_battle(self):
        await self.updator.update_final_battle()

    async def _update_battle(self, r_body, resp):
        """
        Updates battle information, win conditions, and summon availability based on the response.

        Args:
            r_body (dict): The response body in dictionary format.
            resp: The response object.
        """
        _log.debug(f"Updating battle info from {resp.url}...")
        await self._update_event_time()
        await self._update_is_final_battle()
        await self._update_battle_info(r_body, resp)
        await self._update_win_conditions()
        await self._update_summon_availability(r_body, resp)

    async def start_response_handler(self, resp):
        """
        Handles the start response.

        Args:
            resp: The response object.
        """
        r_body = await get_response_body(resp)
        await self._update_battle(r_body, resp)

        _log.debug(f"'start' response handler, updated from {resp.url}")
        _log.debug(f"'start' response handler, battle info: {self.battle}")
