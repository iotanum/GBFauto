import re
import asyncio

from gbfauto.common.utils import get_xpath_from_ele, get_response_body


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

    async def navigate_to_items_menu(self):
        items_url = "https://game.granbluefantasy.jp/#item"
        await self.utils.go_to_url(items_url)

    async def click_on_consumable(self):
        items_tab_selector = "div.btn-item-tabs.items"
        await self.bot.page.locator(items_tab_selector).click()

    async def click_on_ap_pots(self):
        while True:
            consumable_items = await self.utils.bs(
                find_all=("div", {"class": "lis-item se"})
            )
            if consumable_items:
                ep_ele = consumable_items[1]
                await self.utils.click(ep_ele)
                break

            await asyncio.sleep(0.1)
        await self.wait_for_usage_popup()

    async def wait_for_usage_popup(self):
        popup_class_re = re.compile("pop-usual (pop-normal|pop-recover).*pop-show")
        while True:
            popup_ele = await self.utils.bs(find=("div", {"class": popup_class_re}))
            if popup_ele:
                return True

            await asyncio.sleep(0.1)

    async def click_on_half_elixir_list(self):
        use_item_ele = await self.utils.bs(
            find_all=("select", {"class": re.compile(".*use-item-num")})
        )
        half_elixir_list = use_item_ele[-1]
        await self.utils.click(half_elixir_list)
        return half_elixir_list

    async def click_on_last_elixir_from_list(self, list_element):
        options = await self.utils.bs(
            find_all=("option", {"value": True}), parser=list_element
        )
        last_ap_pot_ele = options[-1]
        dropdown_ele_xpath = await get_xpath_from_ele(list_element)
        locator = self.bot.page.locator(dropdown_ele_xpath)
        await locator.select_option(value=last_ap_pot_ele.text)

    async def use_in_consumable_menu(self):
        await self.navigate_to_items_menu()
        await self.click_on_consumable()

        await self.click_on_ap_pots()
        list_element = await self.click_on_half_elixir_list()
        await self.click_on_last_elixir_from_list(list_element)

    async def click_on_use_btn(self):
        use_btn_class_name = re.compile("btn-usual-use|btn-use-item.*")
        use_btn_eles = await self.utils.bs(
            find_all=("div", {"class": use_btn_class_name})
        )
        ap_use_btn_ele = use_btn_eles[-1]
        await self.utils.click(ap_use_btn_ele)

    async def confirm_in_items_menu(self):
        await self.click_on_use_btn()

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

    async def handle_shitbox_confirm_response(self):
        uri_regex = re.compile(".*recover_aap_by_item.*")
        async with self.bot.page.expect_response(uri_regex) as resp:
            body = await get_response_body(await resp.value)
            self.p_status["current_ap"] = body.get("after_aap_value")

    async def use_in_shitbox(self):
        await self.wait_for_usage_popup()
        list_element = await self.click_on_half_elixir_list()
        await self.click_on_last_elixir_from_list(list_element)

    async def confirm_in_shitbox_team_selection(self):
        await self.click_on_use_btn()
        await self.handle_shitbox_confirm_response()

    async def confirm_usage(self, shitbox=False):
        if not shitbox:
            return await self.confirm_in_items_menu()

        await self.confirm_in_shitbox_team_selection()
        return True

    async def use_ap(self, shitbox=False):
        """
        Uses EP if the current EP is greater than the minimum EP.
        """
        if shitbox:
            if not self.bot.p_status.get("need_aap", False):
                return
        else:
            current_ep = self.bot.p_status.get("current_ap", 0)

            if current_ep > self.minimum_ap:
                return

        if shitbox:
            await self.use_in_shitbox()
        else:
            await self.use_in_consumable_menu()

        return await self.confirm_usage(shitbox=shitbox)
