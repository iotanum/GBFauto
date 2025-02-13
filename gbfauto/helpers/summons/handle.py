import logging

from gbfauto.helpers.summons.get_best_summon import get_best_summon
from gbfauto.common.enums import SummonEnums

_log = logging.getLogger(__name__)


class SummonHandle:
    def __init__(self, bot):
        self.bot = bot
        self.summons = bot.summons
        self.summons_common = bot.summons_common

    async def pick_summon(self, shitbox=False):
        # wait until the bot is in the summon selection screen
        await self.summons_common.is_in_summon_selection(shitbox)

        if not shitbox:
            await self.summons_common.click_support_element()

            summ_list = await self.summons_common.get_summon_list()
            summ = await get_best_summon(
                summ_list, self.summons[SummonEnums.SUPPORT_SUMMONS_TO_PICK]
            )

            await self.summons_common.click_best_summon(summ)

        return await self.summons_common.confirm_summon(shitbox)
