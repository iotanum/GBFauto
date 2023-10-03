import logging
import asyncio
import re
import time

from gbfauto.common.utils import is_timeout

_log = logging.getLogger(__name__)


class Raids:
    def __init__(self, questing):
        self.bot = questing.bot
        self.utils = questing.bot.utils

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
            confirm = input(f"Confirm raid slot '{raid_slot}'? (y/n): ").lower()
            if confirm in ("y", "n"):
                return confirm == "y"
            else:
                _log.error("Invalid input. Please enter 'y' for yes or 'n' for no.")

    async def _assign_raid_slot(self):
        while True:
            raid_slot = await self._get_raid_filter()
            if raid_slot:
                _log.debug(f"Found raid slot '{raid_slot}'.")
                if await self._confirm_raid_slot(raid_slot):
                    return
            await asyncio.sleep(1)

    async def _get_raids(self):
        try:
            raids = await self.utils.bs(find=("div", {"id": "prt-search-list"}))
            raid = self.utils.bs(parser=raids, find=("div", {"class": "txt-raid-name"}))
            if raid:
                return raids
        except AttributeError:
            return

    async def _get_most_suitable_raid(self):
        raids_info = await self._get_raids()

        if not raids_info:
            return None

        raids = await self.utils.bs(
            parser=raids_info, find_all=("div", {"class": "prt-raid-info"})
        )

        most_suitable_raid_idx = None
        max_hp = float("-inf")

        for idx, raid in enumerate(raids, 1):
            hp_bar = await self.utils.bs(
                parser=raid, find=("div", {"class": "prt-raid-gauge-inner"})
            )
            hp_style = hp_bar["style"]
            raid_hp = int(re.search(r"\d+", hp_style).group())

            if raid_hp > max_hp:
                max_hp = raid_hp
                most_suitable_raid_idx = idx

        return most_suitable_raid_idx

    async def _refresh_raid_filter(self):
        pass
        # rfrsh_btn_class = "btn-search-refresh"
        # rfrsh_btn_ele = await self.bot.page.
        # rfrsh_btn_xpath = await get_xpath_from_ele()

    async def _get_best_raid(self):
        refresh_timeout = 60
        start = time.time()

        while True:
            if await is_timeout(start, refresh_timeout):
                await self.utils.refresh()
                start = time.time()

            raid_num = await self._get_most_suitable_raid()

            print(raid_num)
            # if raid_num:
            #     await self.pick_raid(raid_num)
            #     if not success:
            #         await self.bot.utils.go_to_locked_quest()
            #         continue
            #     return success
            # await self._refresh_raid_filter()
            await asyncio.sleep(0.2)

    async def do_raids(self):
        await self.bot.utils.wait_for_full_page_load()
        await self._assign_raid_slot()
        await self._get_best_raid()
