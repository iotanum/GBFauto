import logging

from gbfauto.helpers.summons.get_best_summon import get_best_summon
from gbfauto.common.enums import SummonEnums

_log = logging.getLogger(__name__)


class SummonHandle:
    def __init__(self, bot):
        self.bot = bot
        self.utils = self.bot.utils
        self.summons = self.bot.summons
        self.summons_common = self.bot.summons_common
        self.popup = self.bot.popup

    async def pick_summon(self):
        # wait until the bot is in the summon selection screen
        await self.summons_common.is_in_summon_selection()

        await self.summons_common.click_support_element()

        summ_list = await self.summons_common.get_summon_list()
        summ = await get_best_summon(
            summ_list, self.summons[SummonEnums.SUPPORT_SUMMONS_TO_PICK]
        )

        await self.summons_common.click_best_summon(summ)
        return await self.summons_common.confirm_summon()
