import logging
from typing import List, Dict, Union

from bs4 import BeautifulSoup

_log = logging.getLogger(__name__)


async def _extract_summon_data(
    summon_options: List[BeautifulSoup],
) -> List[Dict[str, Union[str, int, bool, None]]]:
    """
    Extract summon data from a BeautifulSoup object.

    Args:
        summon_options List[BeautifulSoup]: A list of summon options.

    Returns:
        List[Dict[str, Union[str, int, bool, None]]]: A list of dictionaries containing summon data.
    """
    _log.debug("Extracting summon data.")

    return [
        {
            "name": summon.find("span", class_="js-summon-name").text,
            "level": int(
                summon.find("span", class_="txt-summon-level").text.split()[-1]
            ),
            "friend_name": summon.find("span", class_="txt-supporter-name").text,
            "friend_lvl": int(
                summon.find("span", class_="txt-supporter-level").text.split()[-1]
            ),
            "is_friend": "ico-friend"
            in summon.find("div", class_="prt-supporter-name")["class"],
            "element": summon,
        }
        for summon in summon_options
    ]


async def get_best_summon(
    summons: List[BeautifulSoup], summons_from_config: List[str]
) -> Dict:
    """
    Find the best summon based on specified criteria.

    Args:
        summons (List[BeautifulSoup]): The BeautifulSoup object representing the HTML.
        summons_from_config (list[str]): The list of summons to pick from the config.

    Returns:
        Dict[str, Union[str, int, bool, None]]: The best summon option.
    """
    summon_data = await _extract_summon_data(summons)
    _log.debug("Successfully extracted summon data.")

    # Primary sort: Level descending, Secondary sort: Friend descending
    summon_data.sort(key=lambda x: (-x["level"], -x["is_friend"]))

    best_option = next(
        (
            summon
            for pick in summons_from_config
            for summon in summon_data
            if pick.lower() in summon["name"].lower()
        ),
        None,
    )
    _log.debug(f"Best summon option: {best_option}")

    # Fallback to the first and highest level summon if no matches found
    return best_option or summon_data[0]
