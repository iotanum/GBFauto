import logging
import os

from dotenv import load_dotenv

from gbfauto.common.tasks import background_task
from gbfauto.common.enums import BattleEnums

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
        self.full_auto_enabled = False
        self.refreshed_on_event = {}

        # Start background tasks
        self.is_in_battle.start()
        self.enable_full_auto_in_loading_screen.start()
        self.refresh_after_event.start()
        self.battle_done.start()

    async def already_refresh(self, r_event):
        """
        Checks if the bot already refreshed this turn.

        Returns:
            bool: True if the bot already refreshed this turn, False otherwise.
        """
        refreshed = await self.battle_common.refreshed_on_this_event(
            r_event, self.refreshed_on_event
        )
        return refreshed

    async def need_refresh(self, na=False):
        """
        Checks if the bot needs to refresh.

        Returns:
            bool: True if the bot needs to refresh, False otherwise.
        """
        if self.battle[BattleEnums.IN_BATTLE]:
            if r_event := await self.events_common.is_refresh_event_recent(na=na):
                if not await self.already_refresh(r_event):
                    self.refreshed_on_event = r_event
                    await self.utils.refresh()

    async def is_boss_dead(self):
        """
        Checks if the boss is dead.

        Returns:
            bool: True if the boss is dead, False otherwise.
        """
        boss_hps = await self.battle_common.get_enemy_hp()
        if boss_hps:
            all_dead = all(hp == 0 for hp in boss_hps)
            if all_dead:
                _log.info("All boss HPs are 0, boss is dead!")
            return all_dead

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
            self.battle[BattleEnums.IN_BATTLE] = False

            if self.in_battle:
                _log.debug("Updating 'in_battle' status to False")
                self.in_battle = False

    @background_task(interval=0.2)
    async def refresh_after_event(self):
        """
        Background task to enable full auto in battle.
        """
        load_dotenv(".env", override=True)
        enabled = os.getenv("FA_REFRESH", False)
        if not enabled:
            # Always refresh after normal attacks
            await self.need_refresh(na=True)
            return

        await self.need_refresh()

    @background_task(interval=0.2)
    async def battle_done(self):
        """
        Background task to check if the battle is done.
        """
        if self.battle.get(BattleEnums.BOSS_KILLED, False) or await self.is_boss_dead():
            self.battle[BattleEnums.IN_BATTLE] = False
            self.battle[BattleEnums.BOSS_KILLED] = False

            if await self.battle_common.in_battle_url():
                _log.debug("Battle is done, refreshing...")
                await self.utils.refresh()

    @background_task(interval=0.1)
    async def enable_full_auto_in_loading_screen(self):
        """
        Background task to enable full auto in the loading screen.
        """
        if await self.battle_common.in_battle_url():
            if not self.battle.get(BattleEnums.FULL_AUTO, False):
                if not await self.battle_common.is_queue_this_turn():
                    await self.battle_common.enable_full_auto()
