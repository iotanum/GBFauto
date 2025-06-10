import logging
import os
import asyncio
import time
from dotenv import load_dotenv

from gbfauto.common.tasks import background_task
from gbfauto.common.enums import BattleEnums, EventEnums
from gbfauto.common.utils import is_timeout


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
        self.battle_common = self.bot.battle_common
        self.events_common = self.bot.events_common

        # Sub-attributes
        self.in_battle = False
        self.refreshed_on_event = {}
        self.last_hp_change_time = 0
        self.boss_hps = []
        self.cutoff_logged = False

        # Start background tasks
        self.is_in_battle.start()
        self.enable_full_auto_in_loading_screen.start()
        # self.do_queue.start()
        self.refresh_after_event.start()
        self.is_battle_hanged.start()

    async def event_refresh(self, always_refresh=False):
        """
        Checks if the bot needs to refresh.

        Returns:
            bool: True if the bot needs to refresh, False otherwise.
        """
        if r_event := await self.events_common.is_refresh_event_recent(
            always_refresh=always_refresh
        ):
            if not r_event == self.refreshed_on_event:
                _log.debug(f"Refresh event found! {r_event}")
                self.refreshed_on_event = r_event
                self.cutoff_logged = False
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
                self.battle[BattleEnums.IN_BATTLE] = True
                if not self.battle[BattleEnums.IN_BATTLE]:
                    _log.debug("Updating 'in_battle' status to True")
                return

        if self.battle.get(BattleEnums.IN_BATTLE, False):
            _log.debug("Updating 'in_battle' status to False")
        self.battle[BattleEnums.IN_BATTLE] = False
        self.last_hp_change_time = time.time()

    @background_task(interval=0.2)
    async def refresh_after_event(self):
        """
        Background task to enable full auto in battle.
        """
        while True:
            # Do not refresh if it's not the final battle
            total_battles = self.battle.get(BattleEnums.TOTAL_BATTLES, 0)
            current_battle = self.battle.get(BattleEnums.CURRENT_BATTLE, 0)
            if total_battles != current_battle:
                return

            load_dotenv(".env", override=True)
            fa_refresh_enabled = os.getenv("FA_REFRESH", False)
            if await self.battle_common.in_battle_url():
                # always refresh on summons and normal attacks
                await self.event_refresh(always_refresh=fa_refresh_enabled)

            await asyncio.sleep(0)

    @background_task(interval=0.1)
    async def enable_full_auto_in_loading_screen(self):
        """
        Background task to enable full auto in the loading screen.
        """
        if self.battle.get(BattleEnums.FULL_AUTO, False):
            return

        if not await self.battle_common.in_battle_url():
            return

        # Check for full-auto turn cutoff
        load_dotenv(".env", override=True)
        turn_cutoff = int(os.getenv("RAIDS_CUTOFF_TURN", 420))
        current_turn = self.battle.get(BattleEnums.CURRENT_TURN, 0)
        if current_turn >= turn_cutoff:
            if not self.cutoff_logged:
                _log.debug(
                    f"Current turn '{current_turn}' is greater than or equal to cutoff '{turn_cutoff}', disabling full auto."
                )
                self.cutoff_logged = True
            return

        await self.battle_common.enable_full_auto()

    @background_task(interval=0.1)
    async def do_queue(self):
        # if await self.events_common.is_event_recent(EventEnums.START_EVENT):
        # one step at a time
        await self.bot.queue.do_queue()

    @background_task(interval=5)
    async def is_battle_hanged(self):
        """
        Background task to check if the battle is hanged.
        """
        timeout = 10
        if await self.battle_common.in_battle_url():
            last_event_time = self.events[EventEnums.LATEST_EVENT]
            if await is_timeout(last_event_time, timeout):
                _log.info(
                    f"Battle hanged! Both last event and HP didn't change for {timeout}s, refreshing..."
                )
                self.cutoff_logged = False
                await self.utils.refresh()
