import logging
import time
from gbfauto.common.enums import EventEnums
import typing

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

    async def _get_event_time(self, event: EventEnums) -> typing.Optional[float]:
        """
        Gets the time difference between the current time and the specified event time.

        Args:
            event (EventEnums): The event to retrieve the time for.

        Returns:
            float: Time difference in seconds, or None if the event is not found.
        """
        try:
            return time.time() - self.events[event]
        except KeyError:
            return None

    async def is_event_recent(self, event: EventEnums) -> bool:
        """
        Checks if the event is recent based on a time threshold.

        Args:
            event (EventEnums): The event to check.

        Returns:
            bool: True if the event is recent, False otherwise.
        """
        event_time = await self._get_event_time(event)
        return event_time is not None and event_time < 1

    async def is_refresh_event_recent(self, na=False) -> bool | dict:
        """
        Checks if the refresh event is recent based on a time threshold.

        Returns:
            bool: True if the refresh event is recent, False otherwise.
        """
        refresh_events = [
            EventEnums.NORMAL_ATTACK_EVENT,
            EventEnums.ABILITY_EVENT,
            EventEnums.SUMMON_EVENT,
        ]

        if na:
            normal_atk_event = EventEnums.NORMAL_ATTACK_EVENT
            if await self.is_event_recent(normal_atk_event):
                return {normal_atk_event: await self._get_event_time(normal_atk_event)}
        else:
            for event in refresh_events:
                if await self.is_event_recent(event):
                    return {event: await self._get_event_time(event)}
