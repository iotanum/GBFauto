import logging

from gbfauto.helpers.responses.valid_responses import ValidResponses


_log = logging.getLogger(__name__)


class Common:
    def __init__(self, responses):
        self.bot = responses.bot
        self.p_status = self.bot.events.p_status
        self.battle = self.bot.events.battle

    # Various checks  -------------------------------------------------
    async def is_gauge_change_event(self, event):
        return isinstance(event, dict) and event["cmd"] == "boss_gauge"

    async def is_win_event(self, event):
        return isinstance(event, dict) and (
            event["cmd"] == "win" or event["cmd"] == "finished"
        )

    async def is_final_battle(self):
        return self.battle["current_battle"] == self.battle["total_battles"]

    async def need_ap(self):
        q_ap_cost = self.battle.get("q_ap_cost", 0)
        need_ap = self.p_status["current_ap"] < q_ap_cost
        self.battle["need_ap"] = need_ap
        return need_ap

    async def need_ep(self):
        q_ep_cost = self.battle.get("q_ep_cost", 0)
        need_ep = self.p_status["current_ep"] < q_ep_cost
        self.battle["need_ep"] = need_ep
        return need_ep

    # Various checks end ---------------------------------------------

    async def gather_win_event(self, scenario):
        for event in scenario:
            if await self.is_win_event(event):
                _log.debug(f"Win event found: '{event['cmd']}'")
                return event

    async def gather_gauge_change_events(self, scenario):
        boss_gauge_events = list()
        for event in scenario:
            if await self.is_gauge_change_event(event):
                _log.debug(f"Boss gauge change event found for boss '{event['pos'] + 1}'")
                boss_gauge_events.append(event)
        return boss_gauge_events
