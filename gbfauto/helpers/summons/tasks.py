import logging

from gbfauto.helpers.summons.validate_and_parse import (
    validate_and_parse_summons_from_config,
)
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

        # Start background tasks
        self.parse_summon_configuration.start()

    @background_task(interval=5)
    async def parse_summon_configuration(self):
        element, summons = await validate_and_parse_summons_from_config()

        if element and summons:
            key, value = list(element.items())[0]

            # -1 because the list starts at 0
            self.summons[SummonEnums.SUPPORT_ELEMENT_NUM] = key
            self.summons[SummonEnums.SUPPORT_ELEMENT] = value
            self.summons[SummonEnums.SUPPORT_SUMMONS_TO_PICK] = summons
