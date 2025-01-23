import logging
import asyncio

from gbfauto.raids import Raids
from gbfauto.generic_quests import GenericQuest

_log = logging.getLogger(__name__)


class Questing:
    def __init__(self, bot):
        """
        Initializes the Questing instance.

        Args:
            bot: Bot instance.
        """
        self.bot = bot
        self.utils = self.bot.utils
        self.quest_url = None
        self.raids = Raids(self)
        self.generic_q = GenericQuest(self)

        # For Signal Handling
        # self.keyboard_interrupted = self.bot.keyboard_interrupted

        self.url_action_mapping = {
            "#quest/assist": self.handle_raids,
            "#quest/supporter": self.handle_generic_quest,
        }

    async def wait_for_repeatable_quest(self) -> None:
        """
        Waits for the player to enter a quest and continuously checks for actions based on the current URL.
        """
        if not self.quest_url:
            _log.info("Waiting for you to enter a quest...")

        while True:
            current_url = await self.utils.get_current_url()

            for url, action_function in self.url_action_mapping.items():
                if url in current_url:
                    await action_function()

            await asyncio.sleep(1)

    async def handle_raids(self) -> None:
        """
        Handles raids action.
        """
        _log.info("Locked on to raids.")
        await self.raids.do_raids()

    async def handle_generic_quest(self) -> None:
        """
        Handles generic quest action.
        """
        _log.info("Locked on to generic quest.")
        await self.generic_q.do_quest()
