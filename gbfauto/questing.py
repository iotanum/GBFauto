import logging
import asyncio

from gbfauto.raids import Raids

_log = logging.getLogger(__name__)


class Questing:
    def __init__(self, bot):
        self.bot = bot
        self.utils = self.bot.utils
        self.quest_url = None
        self.raids = Raids(self)

    async def wait_for_repeatable_quest(self):
        if not self.quest_url:
            _log.info("Waiting for you to enter a quest...")

        while True:
            current_url = await self.utils.get_current_url()
            action_map = {
                # "#quest/supporter": self.handle_generic_quest,
                # "#coopraid/room/": self.handle_coop_quest,
                # "#replicard/supporter": self.handle_sandbox_quest,
                "#quest/assist": self.handle_raids,
            }

            for url in action_map:
                if url in current_url:
                    action_function = action_map[url]
                    await action_function()

            await asyncio.sleep(1)

    async def handle_raids(self):
        _log.info("Locked on to raids.")
        await self.raids.do_raids()
