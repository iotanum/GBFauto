import logging
import os

from typing import List, Dict

from dotenv import load_dotenv

_log = logging.getLogger(__name__)


async def _get_support_info_from_config() -> tuple[int, str]:
    load_dotenv(override=True)
    element = int(os.getenv("SUPPORT_ELEMENT"))
    summons = os.getenv("SUPPORT_SUMMONS_TO_PICK")

    if element is None or summons is None:
        _log.error(
            "SUPPORT_ELEMENT or SUPPORT_SUMMONS_TO_PICK is not set in the environment!"
        )

    return element, summons


async def _validate_support_element(support_element: int) -> Dict[int, str]:
    """
    Validate the support element choice.

    Args:
        support_element (int): The chosen support element.

    Returns:
        dict: The validated support element choice.
    """
    valid_elements_map = {
        1: "Fire",
        2: "Water",
        3: "Earth",
        4: "Wind",
        5: "Light",
        6: "Dark",
        7: "Misc",
    }

    if support_element not in valid_elements_map:
        _log.error(
            f"Invalid support element choice. Choose from {list(valid_elements_map.keys())}"
        )

    return {support_element: valid_elements_map[support_element]}


async def _parse_support_summons_to_pick(support_summons_to_pick: str) -> List[str]:
    """
    Parse the support summons to pick configuration.

    Args:
        support_summons_to_pick (str): Comma-separated list of desired summon names.

    Returns:
        List[str]: List of summon names to pick.
    """
    return [
        summon.strip()
        for summon in support_summons_to_pick.split(",")
        if summon.strip()
    ]


async def validate_and_parse_summons_from_config() -> tuple:
    support_element, support_summons_to_pick = await _get_support_info_from_config()
    validated_support_element = await _validate_support_element(support_element)
    parsed_support_summons = await _parse_support_summons_to_pick(
        support_summons_to_pick
    )

    return validated_support_element, parsed_support_summons
