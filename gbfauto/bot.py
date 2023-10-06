import logging
import os

from gbfauto.events import Events
from gbfauto.login import Login
from gbfauto.questing import Questing
from gbfauto.skills import Skills
from gbfauto.common.utils import Utils

from gbfauto.helpers.battle.tasks import BattleTasks
from gbfauto.helpers.summons.tasks import SummonsTasks

from gbfauto.common.battle.common import BattleCommon
from gbfauto.common.events.common import EventsCommon
from gbfauto.common.summons.common import SummonsCommon

_log = logging.getLogger(__name__)


class Bot:
    """
    Class representing the main automation bot for the game.
    """

    def __init__(self, engine, signal_handler):
        """
        Initializes the Bot instance.

        Args:
            engine: The automation engine instance.
        """
        self.page = engine
        self.context = self.page.context

        # For Signal Handling
        self.keyboard_interrupted = signal_handler.keyboard_interrupt

        # Sub-attributes
        self.events = dict()
        self.p_status = dict()
        self.summons = dict()
        self.battle = dict()
        self.queues = dict()

        # Common attributes
        self.utils = Utils(self)
        self.events_common = EventsCommon(self)
        self.summons_common = SummonsCommon(self)
        self.battle_common = BattleCommon(self)

        # Main attributes
        self.events_module = Events(self)
        self.skills = Skills(self)
        self.login = Login(self)
        self.questing = Questing(self)

        # Background task attributes
        self.battle_tasks = BattleTasks(self)
        self.summon_tasks = SummonsTasks(self)

    async def _is_logged_in(self):
        """
        Checks if the context is available.

        Returns:
            bool: True if the context is available, False otherwise.
        """

        context_dir = "browser_user_data"
        context_exists = os.path.exists(context_dir)
        if context_exists:
            _log.debug(
                "Looks like browser data exists. I'll assume that you're already logged in."
            )
            return True

    async def run(self):
        """
        Runs the automation for the bot.
        """
        await self.events_module.initialize_events()

        if not await self._is_logged_in():
            _log.debug("Logging in...")
            await self.login.login()
        await self.questing.wait_for_repeatable_quest()
