import logging
import asyncio

from gbfauto.helpers.summons.handle import SummonHandle
from gbfauto.common.enums import EventEnums
from gbfauto.helpers.actions.ap import Ap


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

    async def do_quest(self):
        self.quest_uri = await self.bot.utils.get_current_url()

        while True:
            used_ap = await self.ap_handler.use_ap()
            if used_ap:
                self.navigated_to_quest_uri = False
                continue

            if not self.navigated_to_quest_uri:
                await self.bot.utils.go_to_url(
                    self.quest_uri,
                )
                self.navigated_to_quest_uri = True

            popup = await self.summon_handle.pick_summon()
            if popup:
                await self.utils.refresh()
                continue

            await self.wait_for_battle_to_end()
            self.bot.battle_count += 1
            _log.info(
                f"Total battles: {self.bot.battle_count}\n"
                f"Avg time per battle: {await self.bot.get_avg_time_per_battle()}s"
            )
