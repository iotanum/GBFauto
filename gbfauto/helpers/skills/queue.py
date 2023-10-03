import logging
import os

from dotenv import load_dotenv

from gbfauto.helpers.skills.validate_and_parse import validate_and_parse
from gbfauto.common.tasks import background_task

_log = logging.getLogger(__name__)


class Queue:
    """
    Class to manage and validate game queues.
    """

    def __init__(self, bot):
        """
        Initialize the Queue instance.

        Args:
            bot: The bot instance associated with the skills.
        """
        self.bot = bot
        self.validate_and_parse_queues.start()
        self.queues = dict()

    async def _generate_queue_names(self):
        """
        Generate skills names based on battle and turn numbers.

        Returns:
            list: List of generated skills names.
        """
        max_battles = 101
        max_turns = 101

        temp_queues = [
            f"QUEUE_{battle}_{turn}"
            for battle in range(1, max_battles)
            for turn in range(1, max_turns)
        ]

        return temp_queues

    async def _unset_queues(self, temp_queues):
        """
        Unset existing skills names from the environment.

        Args:
            temp_queues (list): List of skills names to unset.
        """
        for queue in temp_queues:
            if os.getenv(queue):
                del os.environ[queue]

    async def _gather_queues_from_config(self):
        """
        Find and organize existing queues from the environment.

        Returns:
            dict: A dictionary representing the queues organized by battle and turn numbers.
        """
        temp_queues = await self._generate_queue_names()
        await self._unset_queues(temp_queues)

        load_dotenv(override=True)

        queues = {}
        found_queues = 0

        # Filter out non-existent queues and organize them into a dictionary
        for queue_name in temp_queues:
            if os.getenv(queue_name):
                battle, turn = map(int, queue_name.split("_")[1:])
                queue_value = os.getenv(queue_name)
                queues.setdefault(battle, {}).setdefault(turn, queue_value)
                found_queues += 1

        # _log.debug(f"Found '{found_queues}' queues in config.")

        return queues

    @background_task(interval=2)
    async def validate_and_parse_queues(self):
        """
        Validate and parse the queues.

        This function will process and validate the queues from the configuration.
        """
        self.queues = dict()
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
