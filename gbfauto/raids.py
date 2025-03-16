import logging
import asyncio
import re
import os

from dotenv import load_dotenv

from gbfauto.helpers.summons.handle import SummonHandle
from gbfauto.common.enums import BattleEnums, EventEnums
from gbfauto.common.utils import get_response_body
from gbfauto.helpers.actions.ep import Ep
from gbfauto.helpers.skills.parse_from_config import get_config_queues


_log = logging.getLogger(__name__)


class Raids:
    def __init__(self, questing):
        self.bot = questing.bot
        self.utils = self.bot.utils
        self.summon_handle = SummonHandle(self.bot)
        self.p_status = self.bot.p_status
        self.ep_handler = Ep(self.bot)
        self.events_common = self.bot.events_common

        # For Signal Handling
        # self.keyboard_interrupted = self.bot.keyboard_interrupted

        # Common
        self.raid_filter_assigned = False
        self.popup = self.bot.popup
        self.battle = self.bot.battle
        self.raid_uri = None
        self.navigated_to_raids = True

    async def _get_raid_filter(self):
        try:
            raid_slot_ele = await self.utils.bs(
                find=("div", {"class": "prt-search-switch"})
            )
            active_raid_slot_ele = await self.utils.bs(
                parser=raid_slot_ele, find=("div", {"class": "active"})
            )
            return (
                active_raid_slot_ele.get("data-slot") if active_raid_slot_ele else None
            )
        except (TypeError, AttributeError, RuntimeError) as e:
            _log.error("An error occurred while getting raid filter: %s", str(e))
            return None

    async def _confirm_raid_slot(self, raid_slot):
        while True:
            confirm = input(f"\nConfirm raid slot '{raid_slot}'? (y/n): ").lower()
            if confirm in ("y", "n"):
                return confirm == "y"
            else:
                _log.error("\nInvalid input. Please enter 'y' for yes or 'n' for no.")

    async def _assign_raid_slot(self):
        while True:
            raid_slot = await self._get_raid_filter()
            if raid_slot:
                _log.debug(f"Found raid slot '{raid_slot}'.")
                if await self._confirm_raid_slot(raid_slot):
                    self.raid_filter_assigned = True
                    return
            await asyncio.sleep(1)

    async def _get_raids(self):
        class_regex = re.compile("btn-multi-raid lis-raid search.*")
        return await self.utils.bs(find_all=("div", {"class": class_regex}))

    async def _get_raid_hp(self, raid):
        hp_bar = await self.utils.bs(
            parser=raid, find=("div", {"class": "prt-raid-gauge-inner"})
        )
        return int(re.search(r"\d+", hp_bar["style"]).group())

    async def _get_most_suitable_raid(self):
        raids = await self._get_raids()

        if not raids:
            _log.info("No raids found.")
            return None

        best_raid = None
        best_hp = float("-inf")
        load_dotenv(".env", override=True)
        upper_hp_limit = int(os.getenv("RAIDS_UPPER_HP_LIMIT", 100))
        lower_hp_limit = int(os.getenv("RAIDS_LOWER_HP_LIMIT", 0))
        for raid in raids:
            raid_hp = await self._get_raid_hp(raid)

            # take the highest hp raid that is within the hp limits
            if raid_hp >= best_hp:
                if upper_hp_limit >= raid_hp >= lower_hp_limit:
                    _log.debug(
                        f"Found a raid within hp limits. (^{upper_hp_limit}, v{lower_hp_limit})"
                    )
                    best_hp = raid_hp
                    best_raid = raid

        if not best_raid:
            _log.info(
                f"No raids found within hp limits. (^{upper_hp_limit}, v{lower_hp_limit})"
            )
            return None

        clickable_ele = await self.utils.bs(
            parser=best_raid, find=("div", {"class": "prt-button-cover"})
        )

        return clickable_ele

    async def check_for_entry_popups(self, body):
        if "error" in body.keys():
            _log.info("Raid already ended, possibly.")
            return True
        if popup := body.get("popup"):
            _log.info(f"Popup while joining the raid: {popup['body']}")
            return True

    async def _try_entering_raid(self, raid_ele):
        await self.utils.click(raid_ele)

        quest_start_re = re.compile(".*quest/check_.*start.*")
        async with self.bot.page.expect_response(quest_start_re) as resp:
            response = await resp.value
            body = await get_response_body(response)
            popup = await self.check_for_entry_popups(body)
            if popup:
                return

        return True

    async def wait_for_battle_to_end(self):
        """
        Waits for the battle to end.
        """
        while not self.battle.get(BattleEnums.IN_BATTLE, False):
            if await self.events_common.is_event_recent(EventEnums.RESULT_SCREEN_EVENT):
                _log.info("Too slow, fellas. Returning to raid filters screen...")
                self.navigated_to_raids = False
                return

            await asyncio.sleep(0)

        while True:
            if await self.events_common.is_event_recent(
                EventEnums.RESULT_SCREEN_EVENT, timeout=3
            ):
                self.navigated_to_raids = False
                _log.info("Returning to raid filters screen...")
                return
            await asyncio.sleep(0)

    async def refresh_raid_filter(self):
        refresh_locator = self.bot.page.locator("[class='btn-search-refresh']")
        await refresh_locator.click()
        await refresh_locator.wait_for()

    async def do_raids(self):
        self.raid_uri = await self.bot.utils.get_current_url()
        raid_list_ele_selector = "#prt-search-list > div > div"

        while True:
            # update the queue from the config every battle start
            self.bot.queue_from_config = await get_config_queues()

            if not self.navigated_to_raids:
                await self.bot.utils.go_to_url(
                    self.raid_uri, ele=raid_list_ele_selector
                )
                self.navigated_to_raids = True

            if not self.raid_filter_assigned:
                await self._assign_raid_slot()

            used_ep = await self.ep_handler.use_ep()
            if used_ep:
                await self.utils.refresh(element=raid_list_ele_selector)
                continue

            raid_xpath = await self._get_most_suitable_raid()
            if not raid_xpath:
                await self.refresh_raid_filter()
                continue

            success_entry = await self._try_entering_raid(raid_xpath)
            if not success_entry:
                await self.utils.refresh(element=raid_list_ele_selector)
                continue

            popup = await self.summon_handle.pick_summon()
            if popup:
                self.navigated_to_raids = False
                continue

            await self.wait_for_battle_to_end()
            self.bot.battle_count += 1
            _log.info(
                f"Total battles: {self.bot.battle_count}\n"
                f"Avg time per battle: {await self.bot.get_avg_time_per_battle()}s\n"
                f"Blue boxes: {self.p_status.get('blue_boxes', 0)}"
            )
