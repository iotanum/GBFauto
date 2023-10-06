import logging
import asyncio
import re


_log = logging.getLogger(__name__)


class Raids:
    def __init__(self, questing):
        self.bot = questing.bot
        self.utils = questing.bot.utils

        # For Signal Handling
        self.keyboard_interrupted = self.bot.keyboard_interrupted

        # Common
        self.raid_filter_assigned = False

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
        return await self.utils.bs(
            find_all=("div", {"class": "btn-multi-raid lis-raid search"})
        )

    async def _get_most_suitable_raid(self):
        raids = await self._get_raids()

        if not raids:
            return None

        best_raid = None
        best_hp = float("-inf")

        for idx, raid in enumerate(raids, 0):
            hp_bar = await self.utils.bs(
                parser=raid, find=("div", {"class": "prt-raid-gauge-inner"})
            )

            raid_hp = int(re.search(r"\d+", hp_bar["style"]).group())

            if raid_hp > best_hp:
                best_hp = raid_hp
                best_raid = raids[idx]

        clickable_ele = await self.utils.bs(
            parser=best_raid, find=("div", {"class": "prt-button-cover"})
        )

        return clickable_ele

    async def _try_entering_raid(self, raid_ele):
        await self.utils.click(raid_ele)

    async def do_raids(self):
        while True:
            # if not self.raid_filter_assigned:
            #     await self._assign_raid_slot()
            #
            # raid_xpath = await self._get_most_suitable_raid()
            # if not raid_xpath:
            #     _log.info("No raids found. Refreshing...")
            #     await self.utils.refresh(wait_to_load=True)
            #     continue
            #
            # await self._try_entering_raid(raid_xpath)
            await asyncio.sleep(60606006606)

            if self.keyboard_interrupted:
                _log.info("Done! Exiting raids...")
                self.bot.utils.go_to_main()
                break
