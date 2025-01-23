import re
import asyncio

from gbfauto.common.utils import get_xpath_from_ele


class Ap:
    def __init__(self, bot):
        """
        Initializes the Ap instance.

        Args:
            bot: Bot instance.
        """
        self.bot = bot
        self.p_status = self.bot.p_status
        self.utils = self.bot.utils
        self.battle_common = self.bot.battle_common

        self.minimum_ap = 50

    async def use_in_consumable_menu(self):
        consumables_url = "https://game.granbluefantasy.jp/#item"

        items_tab_selector = "div.btn-item-tabs.items"
        await self.utils.go_to_url(consumables_url, ele=items_tab_selector)
        await self.bot.page.locator(items_tab_selector).click()

        while True:
            consumable_items = await self.utils.bs(
                find_all=("div", {"class": "lis-item se"})
            )
            if consumable_items:
                ep_ele = consumable_items[1]
                await self.utils.click(ep_ele)
                break

            await asyncio.sleep(0.1)

        class_re = re.compile("pop-usual pop-normal.*pop-show")
        while True:
            popup_ele = await self.utils.bs(find=("div", {"class": class_re}))
            if popup_ele:
                use_item_ele = await self.utils.bs(
                    find=("select", {"class": re.compile(".*use-item-num")})
                )
                await self.utils.click(use_item_ele)

                options = await self.utils.bs(
                    find_all=("option", {"value": True}), parser=use_item_ele
                )
                if options:
                    last_ap_pot_ele = options[-1]
                    dropdown_ele_xpath = await get_xpath_from_ele(use_item_ele)
                    locator = self.bot.page.locator(dropdown_ele_xpath)
                    await locator.select_option(value=last_ap_pot_ele.text)
                    return True

            await asyncio.sleep(0.1)

    async def confirm_usage(self):
        """
        Confirms the usage of EP.
        """
        use_btn_class_name = re.compile("btn-usual-use.*")
        use_btn_eles = await self.utils.bs(
            find_all=("div", {"class": use_btn_class_name})
        )
        ap_use_btn_ele = use_btn_eles[-1]
        await self.utils.click(ap_use_btn_ele)

        confirmed_popup_class_name = re.compile("pop-usual pop-normal.*pop-show.*")
        confirmed_popup_style = re.compile("display: block;.*")
        while True:
            is_visible = await self.utils.bs(
                find=(
                    "div",
                    {
                        "class": confirmed_popup_class_name,
                        "style": confirmed_popup_style,
                    },
                )
            )
            if is_visible:
                self.p_status["current_ap"] = 999
                return True

            await asyncio.sleep(0.1)

    async def use_ap(self):
        """
        Uses EP if the current EP is greater than the minimum EP.
        """
        current_ep = self.bot.p_status.get("current_ap", 0)

        if current_ep > self.minimum_ap:
            return

        await self.use_in_consumable_menu()
        return await self.confirm_usage()
