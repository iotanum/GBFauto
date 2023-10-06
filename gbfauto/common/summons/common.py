import re

from gbfauto.common.utils import get_xpath_from_ele
from gbfauto.common.enums import SummonEnums


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

    async def is_in_summon_selection_url(self) -> bool:
        """
        Checks if the bot is in a summon selection screen.

        Returns:
            bool: True if in a summon selection screen, False otherwise.
        """
        possible_urls = ["supporter"]
        current_url = await self.utils.get_current_url()
        return any(url in current_url for url in possible_urls)

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
        summon_list = await self.get_summon_list()
        first_summon_ele = summon_list[0]
        first_summon_xpath = await get_xpath_from_ele(first_summon_ele, debug=False)

        visible = await self.bot.page.locator(first_summon_xpath).is_visible()
        if visible:
            return summon_list

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

        await self.utils.click(all_eles[supp_ele])

    async def click_best_summon(self):
        """
        Clicks the best summon.
        """
        best_summon = self.summons[SummonEnums.BEST_SUMMON]
        await self.utils.click(best_summon["element"])

    async def confirm_summon(self):
        """
        Clicks "confirm" for the summon.
        """
        regex = re.compile(r"btn-usual-ok.*")
        confirm_ele = await self.utils.bs(find=("div", {"class": regex}))

        await self.utils.click(confirm_ele)
