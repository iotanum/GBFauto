import logging

from gbfauto.misc.utils import get_response_body, keys_exists


_log = logging.getLogger(__name__)


class StartResponse:
    def __init__(self, responses):
        self.bot = responses.bot
        self.utils = responses.utils
        self.battle = self.bot.events.battle
        self.b_info = [
            {"total_battles": ["battle", "total"]},
            {"current_battle": ["battle", "count"]},
            {"current_turn": ["turn"]},
            {"bosses": ["boss", "param"]},
        ]

    async def _update_boss_hp(self, bosses, k):
        self.battle[k] = []
        for boss in bosses:
            boss_id = int(boss["attr"])
            hp_current = int(boss["hp"])
            hp_max = int(boss["hpmax"])

            percent = round((hp_current / hp_max) * 100, 2)
            hp_info = {boss_id: percent}

            self.battle[k].append(hp_info)
            _log.debug(f"Updating boss hp with '{hp_info}'...")

            if hp_info:
                self.battle["boss_killed"] = False
                self.battle["quest_done"] = False

    async def _update_battle_info(self, r_body, resp):
        for p_info in self.b_info:
            k, nested_key = list(p_info.items())[0]
            if info := await keys_exists(r_body, *nested_key, resp_url=resp.url):
                _log.debug(f"Updating battle info for '{k}' with '{info}'...")

                if isinstance(info, list):
                    await self._update_boss_hp(info, k)
                    continue

                self.battle[k] = int(info)

    async def _update_win_conditions(self):
        quest_done = False
        boss_killed = False

        # empty "bosses" means no hp bars, means ded
        if self.battle["bosses"]:
            quest_done = False
            boss_killed = False

        if not self.battle["bosses"]:
            boss_killed = True

            # if last battle and boss killed, quest is done
            if await self.utils.is_final_battle():
                quest_done = True

        self.battle["boss_killed"] = boss_killed
        self.battle["quest_done"] = quest_done
        _log.debug(
            f"Updating win condition: Wave mob killed: '{boss_killed}', Quest done: '{quest_done}'..."
        )

    async def _update_battle(self, r_body, resp):
        _log.debug(f"Updating battle info from {resp.url}...")
        await self._update_battle_info(r_body, resp)
        await self._update_win_conditions()

        _log.debug(f"Battle info: {self.battle}")

    async def start_response_handler(self, resp):
        r_body = await get_response_body(resp)
        await self._update_battle(r_body, resp)
