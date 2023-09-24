import logging

from gbfauto.misc.utils import get_response_body, keys_exists


_log = logging.getLogger(__name__)


class StartResponse:
    def __init__(self, responses):
        self.bot = responses.bot
        self.common = responses.common
        self.updator = responses.updator
        self.battle = self.bot.events.battle
        self._b_info = [
            {"total_battles": ["battle", "total"]},
            {"current_battle": ["battle", "count"]},
            {"current_turn": ["turn"]},
            {"bosses": ["boss", "param"]},
        ]

    async def _update_battle_info(self, r_body, resp):
        # scan through _b_info and update battle info
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
        quest_done = False
        mob_killed = False

        # empty "bosses" means no hp bars, means ded
        if self.battle["bosses"]:
            quest_done = False
            mob_killed = False

        if not self.battle["bosses"]:
            mob_killed = True

            # if last battle and boss killed, quest is done
            if await self.common.is_final_battle():
                quest_done = True

        await self.updator.update_win_conditions(mob_killed, quest_done)

    async def _update_summon_availability(self, r_body, resp):
        key = ["summon_enable"]
        summon_enable = await keys_exists(r_body, *key, resp_url=resp.url)

        # custom check because python evaluates 0 as false
        if isinstance(summon_enable, int):
            await self.updator.update_summon_availability(summon_enable)

    async def _update_battle(self, r_body, resp):
        _log.debug(f"Updating battle info from {resp.url}...")
        await self._update_battle_info(r_body, resp)
        await self._update_win_conditions()
        await self._update_summon_availability(r_body, resp)

    async def start_response_handler(self, resp):
        r_body = await get_response_body(resp)
        await self._update_battle(r_body, resp)

        _log.debug(f"Battle info updated from {resp.url}")
        _log.debug(f"Battle info: {self.battle}")
