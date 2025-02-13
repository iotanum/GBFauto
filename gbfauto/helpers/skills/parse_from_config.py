import logging
import os
import re

from dotenv import load_dotenv

_log = logging.getLogger(__name__)
SKILLS_MAP = {
    "a": 1,
    "b": 2,
    "c": 3,
    "d": 4,
}


async def _initialize_dotenv():
    """
    Initialize the dotenv file.
    """
    try:
        load_dotenv()
    except Exception as e:
        _log.error("An error occurred while initializing dotenv: %s", str(e))


async def _get_all_queues_from_config():
    """
    Get all queues from the config.
    """
    await _initialize_dotenv()
    try:
        return {
            key: value for key, value in os.environ.items() if key.startswith("QUEUE_")
        }
    except Exception as e:
        _log.error("An error occurred while getting all queues from config: %s", str(e))
        return {}


async def _parse_turn_queue(queue):
    """
    Parses a turn queue from the config.
    """
    if not queue:
        return []

    steps = []
    queue = queue.replace(" ", "").split(">")
    for idx, step in enumerate(queue):
        refresh = idx + 1 < len(queue) and queue[idx + 1] == "R"
        full_auto = idx + 1 < len(queue) and queue[idx + 1] == "FA"
        step_dict = {
            "character": int(step[0]),
            "skill": SKILLS_MAP.get(step[1]),
            "refresh": refresh,
            "full_auto": full_auto,
        }

        if refresh or full_auto:
            queue.pop(idx + 1)

        steps.append(step_dict)

    return steps


async def get_config_queues():
    """
    Parses all queues from configuration into a dictionary:
    {battle: {turn: [skills]}}.
    """
    all_queues = await _get_all_queues_from_config()
    parsed_dict = {}
    for key, value in all_queues.items():
        if not value:
            continue
        match = re.match(r"QUEUE_(\d+)_(\d+)", key)
        if match:
            battle, turn = map(int, match.groups())

            if battle not in parsed_dict:
                parsed_dict[battle] = {}

            parsed_dict[battle][turn] = {
                "steps": await _parse_turn_queue(value),
            }

    _log.debug(f"Parsed queues from config: {parsed_dict}")
    return parsed_dict
