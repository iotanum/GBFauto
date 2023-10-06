import logging

from gbfauto.helpers.summons.validate_and_parse import (
    validate_and_parse_summons_from_config,
)
from gbfauto.helpers.summons.get_best_summon import get_best_summon
from gbfauto.common.tasks import background_task
from gbfauto.common.enums import SummonEnums

_log = logging.getLogger(__name__)


class SummonsTasks:
    def __init__(self, bot):
        """
        Initializes the SummonsTasks instance.

        Args:
            bot: Bot instance.
        """
        self.bot = bot
        self.utils = self.bot.utils
        self.summons = self.bot.summons
        self.summons_common = self.bot.summons_common

        # Sub-attributes
        self.best_summon_found = False
        self.in_summ_msg_done = False
        self.supp_ele_set = False
        self.best_summon_clicked = False
        self.summon_confirmed = False

        # Start background tasks
        self.parse_summon_configuration.start()
        self.is_in_summon_selection.start()
        self.assign_best_summon.start()
        self.set_supp_element.start()
        self.click_best_summon.start()
        self.confirm_summon.start()

    @background_task(interval=0.2)
    async def is_in_summon_selection(self):
        """
        Background task to check if the bot is in a summon selection screen.
        Screen in which you can select summons.
        """

        if await self.summons_common.is_in_summon_selection_url():
            if await self.summons_common.can_select_summon():
                self.summons[SummonEnums.IN_SUMMON_SELECTION] = True

                if not self.in_summ_msg_done:
                    _log.debug("Updating 'in_summon_selection' status to True")
                    self.in_summ_msg_done = True
        else:
            self.summons[SummonEnums.IN_SUMMON_SELECTION] = False
            self.best_summon_found = False

            if self.in_summ_msg_done:
                _log.debug("Updating 'in_summon_selection' status to False")
                self.in_summ_msg_done = False

    @background_task(interval=5)
    async def parse_summon_configuration(self):
        element, summons = await validate_and_parse_summons_from_config()

        if element and summons:
            key, value = list(element.items())[0]

            # -1 because the list starts at 0
            self.summons[SummonEnums.SUPPORT_ELEMENT_NUM] = key - 1
            self.summons[SummonEnums.SUPPORT_ELEMENT] = value
            self.summons[SummonEnums.SUPPORT_SUMMONS_TO_PICK] = summons

    @background_task(interval=0.2)
    async def assign_best_summon(self):
        """
        Background task to get the best possible summon when in summon selection screen.
        """
        if self.summons[SummonEnums.IN_SUMMON_SELECTION]:
            if not self.best_summon_found and self.supp_ele_set:
                _log.debug("Trying to get the best summon...")
                summ_list = await self.summons_common.get_summon_list()

                summ = await get_best_summon(
                    summ_list, self.summons[SummonEnums.SUPPORT_SUMMONS_TO_PICK]
                )

                self.summons[SummonEnums.BEST_SUMMON] = summ
                self.best_summon_found = True
                _log.debug(f"Finished getting the best summon, {summ}")
        else:
            if self.best_summon_found and self.supp_ele_set:
                _log.debug("Resetting best summon...")
                self.best_summon_found = False

    @background_task(interval=0.2)
    async def set_supp_element(self):
        try:
            if self.summons[SummonEnums.IN_SUMMON_SELECTION]:
                if not self.supp_ele_set:
                    _log.debug("Trying to set support element...")

                    await self.summons_common.click_support_element()
                    self.supp_ele_set = True
                    _log.debug(
                        f"Finished setting support element, {self.summons[SummonEnums.SUPPORT_ELEMENT]}"
                    )
            else:
                if self.supp_ele_set:
                    _log.debug("Resetting support element...")
                    self.supp_ele_set = False
        except KeyError:
            pass

    @background_task(interval=0.2)
    async def click_best_summon(self):
        """
        Background task to click the best summon.
        """
        if self.summons[SummonEnums.IN_SUMMON_SELECTION]:
            if best_summon := self.summons.get(SummonEnums.BEST_SUMMON):
                if not self.best_summon_clicked:
                    _log.debug(f"Trying to click best summon... {best_summon}")
                    await self.summons_common.click_best_summon()
                    self.best_summon_clicked = True
                    _log.debug(f"Clicked on best summon. {best_summon}")
        else:
            if self.best_summon_clicked:
                self.best_summon_clicked = False

    @background_task(interval=0.2)
    async def confirm_summon(self):
        """
        Background task to confirm the summon.
        """
        if self.summons[SummonEnums.IN_SUMMON_SELECTION]:
            if not self.summon_confirmed:
                _log.debug("Trying to confirm summon...")
                await self.summons_common.confirm_summon()
                self.best_summon_clicked = False
                _log.debug("Confirmed summon.")
        else:
            if self.summon_confirmed:
                self.summon_confirmed = False
