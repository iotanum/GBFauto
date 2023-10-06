import logging

from gbfauto.common.tasks import background_task
from gbfauto.common.enums import EventEnums, BattleEnums

_log = logging.getLogger(__name__)


class BattleTasks:
    def __init__(self, bot):
        """
        Initializes the BattleTasks instance.

        Args:
            bot: Bot instance.
        """
        self.bot = bot
        self.utils = self.bot.utils
        self.battle = self.bot.battle
        self.events = self.bot.events
        self.queues = self.bot.queues
        self.battle_common = self.bot.battle_common
        self.events_common = self.bot.events_common

        # Sub-attributes
        self.in_battle = False
        self.full_auto = False

        # Start background tasks
        self.is_in_battle.start()
        self.enable_full_auto_in_loading_screen.start()

    @background_task(interval=0.2)
    async def is_in_battle(self):
        """
        Background task to check if the bot is in a battle.
        Screen in which you can do queues, skills, summons, etc.
        """
        if await self.battle_common.in_battle_url():
            if await self.battle_common.can_see_enemy_hp():
                if not self.in_battle:
                    self.battle[BattleEnums.IN_BATTLE] = True
                    self.in_battle = True
                    _log.debug("Updating 'in_battle' status to True")
        else:
            if self.in_battle:
                _log.debug("Updating 'in_battle' status to False")
                self.battle[BattleEnums.IN_BATTLE] = False
                self.battle[BattleEnums.FULL_AUTO] = False
                self.in_battle = False

    @background_task(interval=0.2)
    async def enable_full_auto_in_loading_screen(self):
        """
        Background task to enable full auto in the loading screen.
        """
        if self.queues:
            return

        if await self.battle_common.in_battle_url():
            if await self.events_common.is_event_recent(EventEnums.START_EVENT):
                if not await self.battle_common.is_queue_this_turn():
                    if not self.full_auto:
                        _log.debug("Enabling full auto in loading screen...")
                        await self.battle_common.enable_full_auto()
                        self.full_auto = True
                        self.battle[BattleEnums.FULL_AUTO] = True
                        _log.info("Enabled full auto in loading screen!")
        else:
            if self.full_auto:
                self.battle[BattleEnums.FULL_AUTO] = False
                self.full_auto = False
