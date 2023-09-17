import logging

from gbfauto.misc.utils import get_response_body, keys_exists


_log = logging.getLogger(__name__)


class NormalAttackResponse:
    def __init__(self, responses):
        self.bot = responses.bot
        self.utils = responses.utils
        self.updator = responses.updator
        self.battle = self.bot.events.battle

    async def _update_win_conditions(self, win_event):
        mob_killed = True if win_event else False
        quest_done = (
            self.battle["current_battle"] == self.battle["total_battles"] and mob_killed
        )

        self.battle["boss_killed"] = mob_killed
        self.battle["quest_done"] = quest_done
        _log.debug(
            f"Updating win condition: Wave mob killed: '{mob_killed}', Quest done: '{quest_done}'..."
        )

    async def _update_battle(self, r_body, resp):
        # update boss hp and win condition from scenario
        if scenarios := await keys_exists(r_body, "scenario", resp_url=resp.url):
            boss_gauge_events = await self.utils.gather_gauge_change_events(scenarios)
            await self.updator.update_boss_hp(boss_gauge_events)

            win_event = await self.utils.gather_win_event(scenarios)
            await self._update_win_conditions(win_event)

        # update turn from scenario
        nested_key = ["status", "turn"]
        if turn := await keys_exists(r_body, *nested_key, resp_url=resp.url):
            await self.updator.update_turn(turn, resp.url)

        _log.debug(f"Battle info updated from {resp.url}")
        _log.debug(f"Battle info: {self.battle}")

    async def normal_attack_resp_handler(self, resp):
        r_body = await get_response_body(resp)
        await self._update_battle(r_body, resp)
