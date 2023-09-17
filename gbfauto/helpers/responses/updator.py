import logging


_log = logging.getLogger(__name__)


class Updator:
    def __init__(self, response):
        self.bot = response.bot
        self.p_status = self.bot.events.p_status
        self.battle = self.bot.events.battle

    async def update_boss_hp(self, boss_gauge_events):
        bosses = []
        for boss_id in boss_gauge_events.keys():
            boss_gauge_event = boss_gauge_events[boss_id]
            hp_current = int(boss_gauge_event["hp"])
            hp_max = int(boss_gauge_event["hpmax"])
            percent = round((hp_current / hp_max) * 100, 2)

            boss_hp = {boss_id: percent}
            bosses.append(boss_hp)
            _log.debug(f"Updating boss HP from scenario with '{boss_hp}'...")
        self.battle["bosses"] = bosses

    async def update_turn(self, turn, resp_url):
        self.battle["current_turn"] = turn
        _log.debug(f"Updating turn with '{turn}' from {resp_url}...")
