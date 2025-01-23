import logging
import asyncio
import re

from gbfauto.helpers.summons.handle import SummonHandle
from gbfauto.common.enums import BattleEnums, EventEnums
from gbfauto.common.utils import get_response_body
from gbfauto.helpers.actions.ep import Ep


_log = logging.getLogger(__name__)


class GenericQuest:
    def __init__(self, questing):
        self.bot = questing.bot
        self.utils = self.bot.utils
        self.summon_handle = SummonHandle(self.bot)
        self.p_status = self.bot.p_status
        self.ep_handler = Ep(self.bot)
        self.events_common = self.bot.events_common

        # Common
        self.battle = self.bot.battle
        self.quest_uri = None
        self.navigated_to_quest_uri = True

    async def wait_for_battle_to_end(self):
        """
        Waits for the battle to end.
        """
        while not self.battle[BattleEnums.IN_BATTLE]:
            _log.debug("Waiting for battle to start...")
            if await self.events_common.is_event_recent(EventEnums.BATTLE_END_EVENT):
                _log.info("Too slow, fellas. Returning to raid filters screen...")
                self.navigated_to_quest_uri = False
                return

            await asyncio.sleep(0.1)

        while True:
            _log.debug("Waiting for battle to end...")
            if await self.events_common.is_event_recent(EventEnums.BATTLE_END_EVENT):
                self.navigated_to_quest_uri = False
                _log.info("Returning to raid filters screen...")
                return
            await asyncio.sleep(0.1)

    async def do_quest(self):
        self.quest_uri = await self.bot.utils.get_current_url()

        while True:
            if not self.navigated_to_quest_uri:
                await self.bot.utils.go_to_url(
                    self.quest_uri
                )
                self.navigated_to_quest_uri = True

            used_ep = await self.ep_handler.use_ep()
            if used_ep:
                self.navigated_to_quest_uri = False
                continue

            popup = await self.summon_handle.pick_summon()
            if popup:
                self.navigated_to_quest_uri = False
                continue

            await self.wait_for_battle_to_end()
            self.bot.battle_count += 1
            _log.info(
                f"Total battles: {self.bot.battle_count}\n"
                f"Avg time per battle: {await self.bot.get_avg_time_per_battle()}s"
            )
