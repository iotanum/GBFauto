import logging

from gbfauto.helpers.skills.buttons import Buttons

_log = logging.getLogger(__name__)


class Skills:
    def __init__(self, queue):
        self.bot = queue.bot
        self.utils = queue.bot.utils
        self.buttons = Buttons(self)

    async def _get_command_menu_locator(self, wait=False):
        command_menu_selector = "div.prt-command-top"
        locator = self.bot.page.locator(command_menu_selector)

        if wait:
            await locator.wait_for()
        return locator

    async def _is_in_command_menu(self):
        command_menu = await self._get_command_menu_locator()
        style = await command_menu.get_attribute("style")

        if style and "display: none" in style:
            return False
        return True

    async def _get_clicked_card(self):
        char_card_selector = '[class^="prt-command-chara"]'
        char_card_style_selector = '[style^="display: block"]'

        chara_card = self.bot.page.locator(
            f"{char_card_selector}{char_card_style_selector}"
        )
        if await chara_card.count() == 1:
            return chara_card

        summon_card_selector = "div.prt-command-summon.summon-show"
        summon_card = self.bot.page.locator(summon_card_selector)
        if await summon_card.count() > 0:
            return summon_card

    async def _is_correct_card(self, step):
        if not await self._is_in_command_menu():
            active_card = await self._get_clicked_card()
        else:
            return False

        character = str(step["character"])
        card_class = await active_card.get_attribute("class")
        if character in card_class:
            return active_card

        # if character is 5, then it means summon card
        if character == "5" and "summon" in card_class:
            return active_card

        return False

    async def _switch_to_card(self, step):
        if await self._is_correct_card(step):
            return

        character = step["character"]
        is_in_command_menu = await self._is_in_command_menu()
        if character == 5:
            if not is_in_command_menu:
                await self.buttons.press_back()
            return await self.buttons.press_summon_card()

        if is_in_command_menu:
            return await self.buttons.press_chara_card(character)
        else:
            return await self.buttons.switch_chara_card(character)

    async def _click_skill(self, step, card_ele):
        skill = step["skill"]
        await self.buttons.press_skill(skill, card_ele)

    async def do_queue(self, step):
        _log.debug(f"Trying to execute queue step: {step}")
        card_ele = await self._switch_to_card(step)
        await self._click_skill(step, card_ele)
        _log.debug(f"Queue step executed: {step}")
