import logging

from gbfauto.common.utils import keys_exists
from gbfauto.common.enums import BattleEnums, EventEnums


_log = logging.getLogger(__name__)


class Common:
    """
    Class containing common helper functions for response handling.
    """

    def __init__(self, responses):
        """
        Initializes the Common instance.

        Args:
            responses: Response handler instance.
        """
        self.bot = responses.bot
        self.p_status = self.bot.p_status
        self.battle = self.bot.battle
        self.events_common = self.bot.events_common

    # Various checks  -------------------------------------------------
    async def is_correct_event(self, event, event_type=None):
        """
        Checks if the event_type from event is correct.
        """
        return isinstance(event, dict) and event.get("cmd") in event_type

    async def gather_event(self, scenario, event_type, return_all=False):
        """
        Gathers the correct event from the given scenario.
        """
        events = []
        for event in scenario:
            if await self.is_correct_event(event, event_type):
                _log.debug(f"Event '{event_type}' found: '{event.get('cmd')}'")
                events.append(event)
                if not return_all:
                    return event

        return events

    @staticmethod
    async def _get_boss_id(hp_event):
        """
        Gets the boss ID from the HP event.

        Args:
            hp_event (dict): HP event containing boss information.

        Returns:
            int: The boss ID.
        """
        boss_id = hp_event.get("number") or hp_event.get("pos")

        if boss_id is not None:
            return int(boss_id) + 1 if "pos" in hp_event else int(boss_id)
        else:
            return 1  # Default value

    async def update_boss_hp(self, boss_hp_scenarios):
        """
        Updates the HP of bosses based on the provided scenarios.

        Args:
            boss_hp_scenarios (list or dict): Scenarios containing boss HP information.
        """
        try:
            bosses = {}

            if not isinstance(boss_hp_scenarios, list):
                boss_hp_scenarios = list(boss_hp_scenarios.values())

            for hp_event in boss_hp_scenarios:
                boss_id = await self._get_boss_id(hp_event)

                hp_current = int(hp_event["hp"])
                hp_max = int(hp_event["hpmax"])
                percent = round((hp_current / hp_max) * 100, 2)

                bosses[boss_id] = percent

            self.battle[BattleEnums.BOSS_HPS] = bosses

        except Exception as e:
            _log.error(f"Error while updating boss HP: {e}")

    async def update_battle_from_scenarios(self, r_body, resp):
        scenarios = await keys_exists(r_body, "scenario", resp_url=resp.url)

        if scenarios:
            boss_gauge_events = await self.gather_event(
                scenarios, {"boss_gauge"}, return_all=True
            )
            await self.update_boss_hp(boss_gauge_events)

            win_event = await self.gather_event(scenarios, {"win", "finished"})
            if win_event:
                self.battle[BattleEnums.BOSS_KILLED] = True
                self.battle[BattleEnums.BOSS_HPS] = {}
                await self.events_common.update_event_time(EventEnums.BATTLE_END_EVENT)

    async def update_popup_status(self, r_body, resp):
        """
        Checks for a popup message and updates the event time if found.
        """
        if len(r_body.keys()) == 1:
            if popup_body := r_body.get("popup"):
                if "processing" in popup_body:
                    _log.debug(f"'Processing' popup in {resp.url} resp: '{popup_body}'")
                    await self.events_common.update_event_time(BattleEnums.BATTLE_POPUP)

    async def update_turn(self, r_body, resp):
        """
        Updates the turn based on the response.

        Args:
            r_body (dict): The response body in dictionary format.
            resp: The response object.
        """
        nested_key = ["status", "turn"]
        turn_value = await keys_exists(r_body, *nested_key, resp_url=resp.url)

        if turn_value:
            self.battle[BattleEnums.CURRENT_TURN] = turn_value

    async def update_summon_availability(self, r_body, resp):
        """
        Updates summon availability based on the response.

        Args:
            r_body (dict): The response body in dictionary format.
            resp: The response object.
        """
        nested_key = ["status", "summon_enable"]
        summon_enable = await keys_exists(r_body, *nested_key, resp_url=resp.url)

        # custom check because Python evaluates 0 as false
        if isinstance(summon_enable, int):
            self.battle[BattleEnums.SUMMON_AVAILABLE] = bool(summon_enable)
