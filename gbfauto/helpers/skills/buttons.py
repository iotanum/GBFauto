import logging

_log = logging.getLogger(__name__)


class Buttons:
    def __init__(self, skills):
        self.bot = skills.bot
        self.utils = skills.bot.utils

    async def _click(self, selector, wait_for_selector=None):
        battle_screen_locator = await self._get_battle_screen_locator()
        await battle_screen_locator.locator(selector).click()

        _log.debug(f"Queue clicked on '{selector}'")
        if wait_for_selector:
            wait_for_locator = battle_screen_locator.locator(wait_for_selector)
            _log.debug(f"Waiting for '{wait_for_selector}' to appear...")
            await wait_for_locator.wait_for()
            return wait_for_locator

    async def _get_battle_screen_locator(self):
        battle_screen_selector = "div.cnt-raid"
        return self.bot.page.locator(battle_screen_selector)

    async def press_back(self):
        back_btn_selector = "div.btn-command-back.display-off.display-on"
        await self._click(back_btn_selector)

    async def press_attack(self):
        attack_btn_selector = "div.btn-attack-start.display-on"
        await self._click(attack_btn_selector)

    async def press_summon_card(self):
        summ_card_selector = "div.prt-list-top.btn-command-summon.summon-on"
        summ_card_inside_selector = "div.prt-summon-list.opened"
        return await self._click(summ_card_selector, summ_card_inside_selector)

    async def press_chara_card(self, character):
        char_card_selector = f"div.lis-character{character - 1}.btn-command-character"
        char_card_inside_selector = f"div.prt-command-chara.chara{character}"
        return await self._click(char_card_selector, char_card_inside_selector)

    async def switch_chara_card(self, character):
        await self.press_back()
        return await self.press_chara_card(character)

    async def press_skill(self, skill, card_element):
        skill_btn_selector = "div.lis-ability btn-ability-available"
        locator = card_element.locator(skill_btn_selector)
        skill = await locator.all()[skill - 1]
        return await skill.click()
