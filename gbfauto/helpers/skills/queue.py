import logging
import os

from dotenv import load_dotenv

from gbfauto.helpers.skills.validate_and_parse import validate_and_parse
from gbfauto.common.tasks import background_task

_log = logging.getLogger(__name__)


class Queue:
    """
    Class to manage and validate from config queues.
    """

    def __init__(self, skills):
        """
        Initialize the Queue instance.

        Args:
            skills: The skills instance associated with the bot.
        """
        self.bot = skills.bot
        self.queues = self.bot.queues
        self.temp_queues = [
            f"QUEUE_{battle}_{turn}"
            for battle in range(1, 101)
            for turn in range(1, 101)
        ]

        self.validate_and_parse_queues.start()

    async def _unset_queues(self) -> None:
        """
        Unset existing queues from the environment.
        """
        for queue in self.temp_queues:
            if os.getenv(queue):
                del os.environ[queue]

    async def _gather_queues_from_config(self) -> dict:
        """
        Find and organize existing queues from the environment.

        Returns:
            dict: A dictionary representing the queues organized by battle and turn numbers.
        """
        await self._unset_queues()

        load_dotenv(override=True)

        queues = {}
        found_queues = 0

        # Filter out non-existent queues and organize them into a dictionary
        for queue_name in self.temp_queues:
            if os.getenv(queue_name):
                battle, turn = map(int, queue_name.split("_")[1:])
                queue_value = os.getenv(queue_name)
                queues.setdefault(battle, {}).setdefault(turn, queue_value)
                found_queues += 1

        # _log.debug(f"Found '{found_queues}' queues in config.")

        return queues

    @background_task(interval=2)
    async def validate_and_parse_queues(self) -> None:
        """
        Validate and parse the queues.

        This function will process and validate the queues from the configuration.
        """
        self.queues.clear()

        queues = await self._gather_queues_from_config()
        for battle, turns in queues.items():
            for turn, queues in turns.items():
                queue = queues.split(" > ")
                for step in queue:
                    char, action, target, refresh = await validate_and_parse(step)

                    self.queues.setdefault(battle, {}).setdefault(turn, [])

                    self.queues[battle][turn].append(
                        {
                            "char": char,
                            "action": action,
                            "target": target,
                            "refresh": refresh,
                        }
                    )

        # _log.debug(f"Finished validating and parsing queues: {self.queues}")
