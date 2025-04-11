import logging
import time
import os

from dotenv import load_dotenv
from gbfauto.common.enums import EventEnums, BattleEnums

_log = logging.getLogger(__name__)


class EventsCommon:
    def __init__(self, bot):
        """
        Initializes the EventsCommon instance.

        Args:
            utils: Utility functions instance.
        """
        self.bot = bot
        self.events = self.bot.events

    async def _update_latest_event_time(self) -> None:
        """
        Updates the latest event time.
        """
        self.events[EventEnums.LATEST_EVENT] = time.time()
        _log.debug("Updating latest event time with current time.")

    async def update_event_time(self, event: EventEnums) -> None:
        """
        Updates given response event time.

        Args:
            event (EventEnums): The event to update the time for.

        """
        self.events[event] = time.time()
        _log.debug(f"Updating '{event}' event time with current time.")
        await self._update_latest_event_time()

    async def is_event_recent(self, event: EventEnums, timeout=1):
        """
        Checks if the event is recent based on a time threshold.

        Args:
            event (EventEnums): The event to check.
            timeout (int): The time threshold to check against.

        Returns:
            bool: True if the event is recent, False otherwise.
        """
        try:
            event_time = time.time() - self.events[event]
            if event_time and event_time < timeout:
                # Remove the event if it's recent
                return self.events.pop(event)
        except KeyError:
            return False

    async def is_refresh_event_recent(
        self, always_refresh=False, timeout=3
    ) -> bool | dict:
        """
        Checks if the refresh event is recent based on a time threshold.

        Returns:
            bool: True if the refresh event is recent, False otherwise.
        """
        load_dotenv(".env", override=True)
        summ_refresh_enabled = os.getenv("REFRESH_ON_SUMMON_CALL", True)

        refresh_events = [
            BattleEnums.BATTLE_POPUP,
            EventEnums.NORMAL_ATTACK_EVENT,
            EventEnums.SUMMON_EVENT,
            EventEnums.ABILITY_REFRESH_EVENT,
        ]

        # FA_REFRESH is enabled
        if always_refresh:
            refresh_events.append(EventEnums.ABILITY_EVENT)

        # remove if explicitly disabled
        if not summ_refresh_enabled:
            refresh_events.remove(EventEnums.SUMMON_EVENT)

        for event in refresh_events:
            if event_time := await self.is_event_recent(event, timeout=timeout):
                return {event: event_time}

        return False
