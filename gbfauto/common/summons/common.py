import logging
import re
import asyncio

from gbfauto.common.enums import SummonEnums
from gbfauto.common.utils import get_response_body

_log = logging.getLogger(__name__)


class SummonsCommon:
    def __init__(self, bot):
        """
        Initializes the BattleCommon instance.

        Args:
            utils: Utility functions instance.
        """
        self.bot = bot
        self.utils = self.bot.utils
        self.summons = self.bot.summons
        self.p_status = self.bot.p_status
        self.events_common = self.bot.events_common

    async def is_in_summon_selection_url(self) -> bool:
        """
        Checks if the bot is in a summon selection screen.

        Returns:
            bool: True if in a summon selection screen, False otherwise.
        """
        possible_uri = re.compile(".*quest\/supporter.*")
        current_url = await self.utils.get_current_url()

        match = re.search(possible_uri, current_url)
        if match:
            return True

    async def get_summon_list(self):
        """
        Gets the list of summons.

        Returns:
            list: List of summons.
        """
        regex = re.compile(r"prt-supporter-attribute.*selected")
        active_summon_ele = await self.utils.bs(find=("div", {"class": regex}))
        summon_options = await self.utils.bs(
            parser=active_summon_ele,
            find_all=("div", {"class": "btn-supporter lis-supporter"}),
        )

        return summon_options

    async def can_select_summon(self):
        """
        Checks if the summon selection screen is visible.

        Returns:
            bool: True if visible, False otherwise.
        """
        locator = "[class~='prt-supporter-attribute'][class*='type'][class~='selected']"
        is_visible = await self.bot.page.locator(locator).is_visible()
        return is_visible

    async def is_supp_ele_clicked(self, supp_ele):
        """
        Checks if the support element is clicked.

        Returns:
            bool: True if clicked, False otherwise.
        """
        class_name = f"icon-supporter-type-{supp_ele} btn-type selected"
        clicked = await self.utils.bs(find=("div", {"class": class_name}))
        return clicked

    async def click_support_element(self):
        """
        Clicks the support element.
        """
        supp_ele = self.summons[SummonEnums.SUPPORT_ELEMENT_NUM]
        ele_bar = await self.utils.bs(find=("div", {"id": "prt-type"}))
        regex = re.compile(r"icon-supporter-type-.*btn-type")
        all_eles = await self.utils.bs(
            parser=ele_bar, find_all=("div", {"class": regex})
        )
        await self.utils.click(all_eles[supp_ele - 1], timeout=1)
        return await self.is_supp_ele_clicked(supp_ele)

    async def is_summon_clicked(self):
        """
        Checks if a summon is clicked.

        Returns:
            bool: True if clicked, False otherwise.
        """
        summon_clicked = False
        while True:
            _log.debug("Checking if summon is clicked.")
            if not summon_clicked:
                uri_regex = re.compile(".*rest/quest/decks_info.*")
                async with self.bot.page.expect_response(uri_regex) as resp:
                    await resp.value
                    summon_clicked = True

            if summon_clicked:
                class_re = re.compile("pop-deck supporter.*")
                style_re = re.compile("display: block;.*")
                visible = await self.utils.bs(
                    find=("div", {"class": class_re, "style": style_re})
                )
                if visible:
                    return True

            await asyncio.sleep(1)

    async def click_best_summon(self, best_summon):
        """
        Clicks the best summon.
        """
        await self.utils.click(best_summon["element"], timeout=1.5)

        return await self.is_summon_clicked()

    async def check_for_popups(self):
        uri_regex = re.compile(".*deck_data_create.*")
        try:
            async with self.bot.page.expect_response(uri_regex) as resp:
                response = await resp.value
                body = await get_response_body(response)
                print(body, "body, check_for_popups")
                if not body.get("error", True):
                    _log.info("Raid ended popup.")
                    return True
                if popup := body.get("popup"):
                    if "is full" in popup.get("body").lower():
                        _log.info(body["popup"])
                    return True
        except Exception as e:
            _log.error(f"Error: {str(e)}")
            return False

    async def confirm_summon(self):
        """
        Clicks "confirm" for the summon.
        """
        regex = re.compile("btn-usual-ok.*")
        confirm_ele = await self.utils.bs(find=("div", {"class": regex}))

        await self.utils.click(confirm_ele)

        return await self.check_for_popups()

    async def is_in_summon_selection(self):
        supp_screen_resp = None
        while True:
            if not supp_screen_resp:
                uri_regex = re.compile(".*quest/content/supporter.*")
                async with self.bot.page.expect_response(uri_regex) as resp:
                    await resp.value
                    supp_screen_resp = True

            if supp_screen_resp:
                if await self.is_in_summon_selection_url():
                    if await self.can_select_summon():
                        return True

            await asyncio.sleep(0.1)
