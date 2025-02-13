import logging
import asyncio

from gbfauto.helpers.summons.handle import SummonHandle
from gbfauto.common.enums import EventEnums
from gbfauto.helpers.actions.ap import Ap
from gbfauto.helpers.skills.parse_from_config import get_config_queues

_log = logging.getLogger(__name__)


class GenericQuest:
    def __init__(self, questing):
        self.bot = questing.bot
        self.utils = self.bot.utils
        self.summon_handle = SummonHandle(self.bot)
        self.p_status = self.bot.p_status
        self.ap_handler = Ap(self.bot)
        self.events_common = self.bot.events_common

        # Common
        self.battle = self.bot.battle
        self.quest_uri = None
        self.navigated_to_quest_uri = True

    async def wait_for_battle_to_end(self):
        """
        Waits for the battle to end.
        """
        while True:
            _log.debug("Waiting for battle to end...")
            if await self.events_common.is_event_recent(EventEnums.RESULT_SCREEN_EVENT):
                self.navigated_to_quest_uri = False
                _log.info("Returning to the quest screen...")
                return
            await asyncio.sleep(0.5)

    async def handle_ap_usage(self, shitbox):
        used_ap = await self.ap_handler.use_ap(shitbox=shitbox)
        if used_ap:
            self.navigated_to_quest_uri = False
            return True

    async def navigate_to_quest_uri(self):
        if not self.navigated_to_quest_uri:
            await self.bot.utils.go_to_url(
                self.quest_uri,
            )
            self.navigated_to_quest_uri = True

    async def do_quest(self, shitbox=False):
        self.quest_uri = await self.bot.utils.get_current_url()

        while True:
            # update the queue from the config every battle start
            self.bot.queue_from_config = await get_config_queues()

            if not shitbox:
                ap_used = await self.handle_ap_usage(shitbox)
                if ap_used:
                    continue

            await self.navigate_to_quest_uri()

            popup = await self.summon_handle.pick_summon(shitbox=shitbox)
            if popup:
                if shitbox:
                    await self.handle_ap_usage(shitbox)
                await self.utils.refresh()
                continue

            await self.wait_for_battle_to_end()
            self.bot.battle_count += 1
            _log.info(
                f"Total battles: {self.bot.battle_count}\n"
                f"Avg time per battle: {await self.bot.get_avg_time_per_battle()}s"
            )
