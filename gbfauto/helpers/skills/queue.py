import logging

from gbfauto.helpers.skills.skills import Skills

_log = logging.getLogger(__name__)


class Queue:
    """
    Class to manage and validate from config queues.
    """

    def __init__(self, bot):
        """
        Initialize the Queue instance.

        Args:
            bot: The bot instance.
        """
        self.bot = bot
        self.skills = Skills(self)
        self.battle = self.bot.battle
        self.battle_common = self.bot.battle_common

    async def _is_queue_this_battle(self):
        current_battle = await self.battle_common.get_current_battle()
        return self.bot.queue_from_config.get(current_battle, None)

    async def _is_queue_this_turn(self, battle_queues):
        current_turn = await self.battle_common.get_current_turn()
        return battle_queues.get(current_turn, None)

    async def _remove_step_from_queue(self, step):
        current_battle = await self.battle_common.get_current_battle()
        current_turn = await self.battle_common.get_current_turn()

        self.bot.queue_from_config[current_battle][current_turn]["steps"].remove(step)
        _log.debug(f"Removed step from queue: {step}")

    async def do_queue(self):
        if not self.bot.queue_from_config:
            return

        battle_queues = await self._is_queue_this_battle()
        if not battle_queues:
            return

        turn_queue_list = await self._is_queue_this_turn(battle_queues)
        if not turn_queue_list:
            return

        step = turn_queue_list["steps"][0]
        await self.skills.do_queue(step)
        await self._remove_step_from_queue(step)
        _log.debug(f"Current queue: {self.bot.queue_from_config}")
