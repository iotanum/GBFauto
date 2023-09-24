import logging

from gbfauto.misc.utils import get_response_body, keys_exists


_log = logging.getLogger(__name__)


class SummonResponse:
    def __init__(self, responses):
        self.bot = responses.bot
        self.common = responses.common
        self.updator = responses.updator
        self.battle = self.bot.events.battle

    async def _update_win_conditions(self, win_event):
        quest_done = False
        mob_killed = True if win_event else False

        if self.battle["current_battle"] == self.battle["total_battles"]:
            if mob_killed:
                quest_done = True

        await self.updator.update_win_conditions(mob_killed, quest_done)

    async def _update_boss_hp(self, r_body, resp):
        if scenarios := await keys_exists(r_body, "scenario", resp_url=resp.url):
            boss_gauge_events = await self.common.gather_gauge_change_events(scenarios)
            await self.updator.update_boss_hp(boss_gauge_events)

            win_event = await self.common.gather_win_event(scenarios)
            await self._update_win_conditions(win_event)

    async def _update_turn(self, r_body, resp):
        nested_key = ["status", "turn"]
        if turn := await keys_exists(r_body, *nested_key, resp_url=resp.url):
            await self.updator.update_turn(turn, resp.url)

    async def _update_summon_availability(self, r_body, resp):
        nested_key = ["status", "summon_enable"]
        summon_enable = await keys_exists(r_body, *nested_key, resp_url=resp.url)

        # custom check because python evaluates 0 as false
        if isinstance(summon_enable, int):
            await self.updator.update_summon_availability(summon_enable)

    async def _update_battle(self, r_body, resp):
        await self._update_boss_hp(r_body, resp)
        await self._update_turn(r_body, resp)
        await self._update_summon_availability(r_body, resp)

        _log.debug(f"Battle info updated from {resp.url}")
        _log.debug(f"Battle info: {self.battle}")

    async def summon_response_handler(self, resp):
        r_body = await get_response_body(resp)
        await self._update_battle(r_body, resp)
