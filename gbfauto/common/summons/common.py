import logging
import re
import asyncio

from gbfauto.common.enums import SummonEnums, EventEnums
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
        possible_uri = re.compile(".*(quest|replicard)/supporter.*")
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

    async def update_consumables_status(self):
        """
        Updates the consumables status using Playwright.
        """
        while True:
            consumables_ele = self.bot.page.locator("div.txt-stamina")

            if await consumables_ele.count() > 0:
                consumables_text = await consumables_ele.inner_text()
                consumables_ele = consumables_ele.locator("span.txt-stamina-after")
                if await consumables_ele.count() > 0:
                    if "AP" in consumables_text:
                        consumables_text = await consumables_ele.inner_text()
                        self.p_status["current_ap"] = int(consumables_text.strip())
                        _log.debug(f"Updating AP from summon screen: {self.p_status}")
                        return
                    if "EP" in consumables_text:
                        consumables_text = await consumables_ele.inner_text()
                        self.p_status["current_ep"] = int(consumables_text.strip())
                        _log.debug(f"Updating EP from summon screen: {self.p_status}")
                        return
            await asyncio.sleep(0.1)

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

            await asyncio.sleep(0.5)

    async def click_best_summon(self, best_summon):
        """
        Clicks the best summon.
        """
        await self.utils.click(best_summon["element"], timeout=1.5)

        return await self.is_summon_clicked()

    async def check_for_popups(self, shitbox):
        if shitbox:
            await self.update_aap_info_from_shitbox_resp()
            if self.p_status["need_aap"]:
                return True

        uri_regex = re.compile(".*deck_data_create|create_quest.*")
        try:
            async with self.bot.page.expect_response(uri_regex) as resp:
                body = await get_response_body(await resp.value)

                if body:
                    _log.debug(f"A popup after confirming the summon: {body}")
                if "error" in body.keys():
                    _log.info("Raid already ended, possibly.")
                    return True
                if popup := body.get("popup"):
                    if "is full" in popup.get("body").lower():
                        _log.info(body["popup"])
                    if "verification" in popup.get("body").lower():
                        _log.info("!!! Verification popup !!!")
                        await self.bot.captcha.handler()
                    return True
        except Exception as e:
            _log.error(f"Error: {str(e)}")
            return False

    async def update_aap_info_from_shitbox_resp(self):
        uri_regex = re.compile(".*user_aap_recovery_info.*")
        async with self.bot.page.expect_response(uri_regex) as resp:
            body = await get_response_body(await resp.value)
            current_aap = body.get("aap")
            consume_aap = body.get("consume_aap")
            self.p_status["current_ap"] = current_aap
            self.p_status["need_aap"] = current_aap < consume_aap

    async def confirm_summon(self, shitbox):
        await self.update_consumables_status()
        confirm_ele = self.bot.page.locator('[class^="btn-usual-ok"]')
        await confirm_ele.click()

        return await self.check_for_popups(shitbox)

    async def is_in_summon_selection(self, shitbox):
        while True:
            if await self.events_common.is_event_recent(
                EventEnums.SUMMON_SCREEN_EVENT, timeout=3
            ):
                _log.debug(
                    "Found an event for summon_screen, continuing with the process."
                )
                if await self.is_in_summon_selection_url():
                    if await self.can_select_summon() or shitbox:
                        return True

            await asyncio.sleep(0.1)
