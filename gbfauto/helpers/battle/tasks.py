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
        self.battle_common = self.bot.utils.battle_common
        self.events_common = self.bot.utils.events_common

        # Start background tasks
        self.is_in_battle.start()
        self.enable_full_auto_in_loading_screen.start()

    @background_task(interval=0.2)
    async def is_in_battle(self):
        """
        Background task to check if the bot is in a battle.
        Screen in which you can do queues, skills, summons, etc.
        """
        if await self.battle_common.can_see_enemy_hp():
            self.battle[BattleEnums.IN_BATTLE] = True
            _log.debug("Updating 'in_battle' status to True")
        else:
            self.battle[BattleEnums.IN_BATTLE] = False
            self.battle[BattleEnums.FULL_AUTO] = False

    @background_task(interval=0.2)
    async def enable_full_auto_in_loading_screen(self):
        """
        Background task to enable full auto in the loading screen.
        """
        if not self.queues:
            return

        if not self.battle[BattleEnums.IN_BATTLE]:
            if await self.events_common.is_event_recent(EventEnums.START_EVENT):
                if not await self.battle_common.is_queue_this_turn():
                    _log.debug("Enabling full auto in loading screen...")
                    self.battle[BattleEnums.FULL_AUTO] = True
