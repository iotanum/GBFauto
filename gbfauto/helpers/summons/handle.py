import logging

from gbfauto.helpers.summons.get_best_summon import get_best_summon
from gbfauto.common.enums import SummonEnums, BattleEnums

_log = logging.getLogger(__name__)


class SummonHandle:
    def __init__(self, bot):
        self.bot = bot
        self.summons = bot.summons
        self.summons_common = bot.summons_common
        self.battle = self.bot.battle

    async def pick_summon(self, shitbox=False):
        # Wait until the bot is in the summon selection screen
        await self.summons_common.is_in_summon_selection(shitbox)
        full_summon_process = not (
            self.battle.get(BattleEnums.AUTO_SELECT, False) or shitbox
        )

        # If shitbox or auto select is disabled - go through the whole process
        if full_summon_process:
            await self.summons_common.click_support_element()
            summ_list = await self.summons_common.get_summon_list()
            summ = await get_best_summon(
                summ_list, self.summons[SummonEnums.SUPPORT_SUMMONS_TO_PICK]
            )
            await self.summons_common.click_best_summon(summ)

        return await self.summons_common.confirm_summon(shitbox)
