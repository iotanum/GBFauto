import logging

from gbfauto.helpers.responses.valid_responses import ValidResponses

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

    # Various checks  -------------------------------------------------

    async def is_gauge_change_event(self, event):
        """
        Checks if the event is a boss gauge change event.

        Args:
            event: The event to check.

        Returns:
            bool: True if it's a boss gauge change event, False otherwise.
        """
        return isinstance(event, dict) and event.get("cmd") == "boss_gauge"

    async def is_win_event(self, event):
        """
        Checks if the event indicates a win.

        Args:
            event: The event to check.

        Returns:
            bool: True if it's a win event, False otherwise.
        """
        return isinstance(event, dict) and event.get("cmd") in {"win", "finished"}

    async def is_final_battle(self):
        """
        Checks if the current battle is the final battle.

        Returns:
            bool: True if it's the final battle, False otherwise.
        """
        return self.battle.get("current_battle") == self.battle.get("total_battles", 0)

    async def need_ap(self):
        """
        Checks if Action Points (AP) are needed for the battle.

        Updates the 'need_ap' flag in battle information.
        """
        q_ap_cost = self.battle.get("q_ap_cost", 0)
        current_ap = self.p_status.get("current_ap", 0)

        need_ap = current_ap < q_ap_cost
        self.battle["need_ap"] = need_ap

    async def need_ep(self):
        """
        Checks if Event Points (EP) are needed for the battle.

        Updates the 'need_ep' flag in battle information.
        """
        q_ep_cost = self.battle.get("q_ep_cost", 0)
        current_ep = self.p_status.get("current_ep", 0)

        need_ep = current_ep < q_ep_cost
        self.battle["need_ep"] = need_ep

    # Various checks end ---------------------------------------------

    async def gather_win_event(self, scenario):
        """
        Gathers the win event from the given scenario.

        Args:
            scenario (list): List of events in the scenario.

        Returns:
            dict or None: The win event if found, None otherwise.
        """
        for event in scenario:
            if await self.is_win_event(event):
                _log.debug(f"Win event found: '{event.get('cmd')}'")
                return event

    async def gather_gauge_change_events(self, scenario):
        """
        Gathers boss gauge change events from the given scenario.

        Args:
            scenario (list): List of events in the scenario.

        Returns:
            list: List of boss gauge change events.
        """
        boss_gauge_events = [
            event for event in scenario if await self.is_gauge_change_event(event)
        ]
        boss_positions = [event.get("pos") + 1 for event in boss_gauge_events]
        _log.debug(f"Boss gauge change events found for bosses: {boss_positions}")
        return boss_gauge_events
