import logging
import asyncio
import re
import os

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
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
        self.popup = self.bot.popup
        self.battle = self.bot.battle

        self.raid_filter_assigned = False
        self.raid_uri = None
        self.navigated_to_raids = True
        self.raid_type = None
        self.filter_slot = None
        self.raid_list_ele_selector = None

        self.raid_filter_uri_regex = re.compile(
            r"(.*search/assist_list.*)|(.*quest/assist_list.*)"
        )

    async def _get_filter_response(self, assign_slot=False):
        async with self.bot.page.expect_response(
            self.raid_filter_uri_regex
        ) as resp_info:
            resp = await resp_info.value
            body = await get_response_body(resp)

            if assign_slot:
                self.raid_type = "raid" if "search" in resp.url else "event"
                self.raid_list_ele_selector = (
                    "#prt-search-list > div > div"
                    if self.raid_type == "raid"
                    else "[class='prt-assist-frame']"
                )
                self.filter_slot = resp.url.split("/")[-1][0]

            return body.get("assist_raids_data")

    async def _prompt_and_assign_filter_slot(self):
        while True:
            await self._get_filter_response(assign_slot=True)
            confirm = input(
                f"\nConfirm '{self.raid_type}' slot '{self.filter_slot}'? (y/n): "
            ).lower()
            if confirm in ("y", "n"):
                self.raid_filter_assigned = confirm == "y"
                return self.raid_filter_assigned
            _log.error("Invalid input. Please enter 'y' or 'n'.")

    async def _get_raids(self):
        return await self.utils.bs(
            find_all=("div", {"class": re.compile(r"btn-multi-raid lis-raid.*")})
        )

    async def _extract_hp_from_raid(self, raid):
        hp_bar = await self.utils.bs(
            parser=raid, find=("div", {"class": "prt-raid-gauge-inner"})
        )
        return int(re.search(r"\d+", hp_bar["style"]).group())

    async def _filter_best_raid(self, raids):
        load_dotenv(".env", override=True)
        upper_hp = int(os.getenv("RAIDS_UPPER_HP_LIMIT", 100))
        lower_hp = int(os.getenv("RAIDS_LOWER_HP_LIMIT", 0))

        best_raid = None
        best_hp = float("-inf")

        for raid in raids:
            hp = await self._extract_hp_from_raid(raid)
            if lower_hp <= hp <= upper_hp and hp >= best_hp:
                best_hp = hp
                best_raid = raid

        return best_raid

    async def _select_best_raid(self):
        raids = await self._get_raids()
        if not raids:
            _log.info("No raids found.")
            return None

        best_raid = await self._filter_best_raid(raids)
        if not best_raid:
            _log.info("No raids found within HP limits.")
            return None

        return await self.utils.bs(
            parser=best_raid, find=("div", {"class": "prt-button-cover"})
        )

    async def _handle_entry_popup(self, body):
        if "error" in body:
            _log.info("Raid already ended.")
            return True
        if popup := body.get("popup"):
            _log.info(f"Popup during join: {popup['body']}")
            return True
        return False

    async def _enter_raid(self, raid_ele):
        await self.utils.click(raid_ele)
        try:
            async with self.bot.page.expect_response(
                re.compile(".*quest/check_.*start.*")
            ) as resp_info:
                resp = await resp_info.value
                body = await get_response_body(resp)
                if await self._handle_entry_popup(body):
                    return False
            return True
        except PlaywrightTimeoutError:
            _log.warning("Timed out during raid entry.")
            return False

    async def _refresh_filter(self):
        selector = (
            "[class='btn-switch-list event active']"
            if self.raid_type == "event"
            else "[class='btn-search-refresh']"
        )
        try:
            refresh_btn = self.bot.page.locator(selector)
            if self.raid_type == "event":
                await asyncio.sleep(0.5)
            await refresh_btn.click()
            if not await self._get_filter_response():
                await refresh_btn.wait_for()
        except Exception as e:
            _log.error(f"Error refreshing filter: {e}")
            await self.utils.refresh(element=self.raid_list_ele_selector)

    async def _wait_for_battle_to_end(self):
        while not self.battle.get(BattleEnums.IN_BATTLE, False):
            if await self.events_common.is_event_recent(EventEnums.RESULT_SCREEN_EVENT):
                _log.info("Battle already finished. Returning to raids...")
                self.navigated_to_raids = False
                return
            await asyncio.sleep(0)

        while not await self.events_common.is_event_recent(
            EventEnums.RESULT_SCREEN_EVENT, timeout=3
        ):
            await asyncio.sleep(0)

        _log.info("Returning to raids screen...")
        self.navigated_to_raids = False

    async def do_raids(self):
        self.raid_uri = await self.utils.get_current_url()

        while True:
            self.bot.queue_from_config = await get_config_queues()

            if not self.navigated_to_raids:
                await self.utils.go_to_url(
                    self.raid_uri, ele=self.raid_list_ele_selector
                )
                self.navigated_to_raids = True

            if not self.raid_filter_assigned:
                await self._prompt_and_assign_filter_slot()

            if await self.ep_handler.use_ep():
                await self.utils.refresh(element=self.raid_list_ele_selector)
                continue

            raid_target = await self._select_best_raid()
            if not raid_target:
                await self._refresh_filter()
                continue

            if not await self._enter_raid(raid_target):
                await self.utils.refresh(element=self.raid_list_ele_selector)
                continue

            if await self.summon_handle.pick_summon():
                self.navigated_to_raids = False
                continue

            await self._wait_for_battle_to_end()

            self.bot.battle_count += 1
            _log.info(
                f"Total battles: {self.bot.battle_count}\n"
                f"Avg time per battle: {await self.bot.get_avg_time_per_battle()}s\n"
                f"Blue boxes: {self.p_status.get('blue_boxes', 0)}"
            )
