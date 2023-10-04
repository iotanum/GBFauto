import logging

from gbfauto.events import Events
from gbfauto.login import Login
from gbfauto.questing import Questing
from gbfauto.skills import Skills
from gbfauto.common.utils import Utils
from gbfauto.helpers.battle.tasks import BattleTasks

_log = logging.getLogger(__name__)


class Bot:
    """
    Class representing the main automation bot for the game.
    """

    def __init__(self, engine):
        """
        Initializes the Bot instance.

        Args:
            engine: The automation engine instance.
        """
        self.page = engine
        self.context = self.page.context

        # Sub-attributes
        self.events = dict()
        self.p_status = dict()
        self.battle = dict()
        self.queues = dict()

        # Main attributes
        self.utils = Utils(self)
        self.events_module = Events(self)
        self.skills = Skills(self)
        self.login = Login(self)
        self.questing = Questing(self)
        self.battle_tasks = BattleTasks(self)

    async def initialize_questing(self):
        """
        Initializes the questing process for the bot.
        """
        await self.questing.wait_for_repeatable_quest()
        _log.debug("Questing initialized!")

    async def run(self):
        """
        Runs the automation for the bot.
        """
        await self.events_module.initialize_events()
        await self.login.login()
        await self.questing.wait_for_repeatable_quest()
