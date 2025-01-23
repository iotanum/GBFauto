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
        self.utils = self.bot.utils
        self.battle_common = self.bot.battle_common

        self.minimum_ap = 50

    async def wait_for_ap_response(self):
        """
        Waits for the AP response.
        """

        uri_regex = re.compile(".*normal_item_list.*")
        async with self.bot.page.expect_response(uri_regex) as resp:
            await resp.value
            return True

    async def use_in_consumable_menu(self):
        consumables_url = "https://game.granbluefantasy.jp/#item/"

        await self.utils.go_to_url(consumables_url)
        await self.bot.page.query_selector("div.btn-item-tabs.items").click()

        while True:
            consumable_items = await self.utils.bs(
                find_all=("div", {"class": "lis-item se"})
            )
            if consumable_items:
                ep_ele = consumable_items[3]
                await self.utils.click(ep_ele)
                break

            await asyncio.sleep(0.1)

        while True:
            class_re = re.compile("pop-usual pop-normal .* pop-show")
            is_visible = await self.bot.page.query_selector(class_re).is_visible()
            if is_visible:
                use_item_ele = await self.utils.bs(
                    find=("div", {"class": "num-set use-item-num"})
                )
                options = await self.utils.bs(find_all="option", content=use_item_ele)
                last_ep_pill_ele = options[-1]

                await self.utils.click(last_ep_pill_ele)
                return True

    async def confirm_usage(self):
        """
        Confirms the usage of EP.
        """
        use_btn_class_name = re.compile("btn-use-item.*")
        use_btn_eles = await self.utils.bs(
            find_all=("div", {"class": use_btn_class_name})
        )
        berry_use_btn_ele = use_btn_eles[-1]
        await self.utils.click(berry_use_btn_ele)

        confirmed_popup_class_name = re.compile(
            "pop-usual pop-complete-recover-stamina .* pop-show.*"
        )
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
