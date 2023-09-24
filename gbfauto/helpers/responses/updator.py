import logging


_log = logging.getLogger(__name__)


class Updator:
    def __init__(self, response):
        self.bot = response.bot
        self.p_status = self.bot.events.p_status
        self.battle = self.bot.events.battle

    async def update_boss_hp(self, boss_info):
        bosses = []

        if isinstance(boss_info, list):
            bosses_iterable = boss_info
        else:
            bosses_iterable = list(boss_info.values())

        # parse and update boss hp tailored for list and dict from json examples above
        for boss in bosses_iterable:
            boss_id = 0
            if "number" in boss.keys():
                boss_id = int(boss["number"])
            if "pos" in boss.keys():
                boss_id = int(boss["pos"]) + 1

            hp_current = int(boss["hp"])
            hp_max = int(boss["hpmax"])
            percent = round((hp_current / hp_max) * 100, 2)

            boss_hp = {boss_id: percent}
            bosses.append(boss_hp)

            if boss_hp:
                await self.update_win_conditions(False, False)
            _log.debug(f"Updating boss HP from scenario with '{boss_hp}'...")
        self.battle["bosses"] = bosses

    async def update_turn(self, turn, resp_url):
        self.battle["current_turn"] = turn
        _log.debug(f"Updating turn with '{turn}' from {resp_url}...")

    async def update_summon_availability(self, summon_enable):
        summon_available = True if int(summon_enable) == 1 else False
        self.battle["summon_available"] = summon_available
        _log.debug(f"Updating summon availability with '{summon_available}'...")

    async def update_win_conditions(self, mob_killed, quest_done):
        self.battle["boss_killed"] = mob_killed
        self.battle["quest_done"] = quest_done
        _log.debug(
            f"Updating win condition: Wave mob killed: '{mob_killed}', Quest done: '{quest_done}'..."
        )
