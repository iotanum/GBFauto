import logging
import re
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
    _log.debug("Extracting summon data...")
    summon_data = []

    for summon in summon_options:
        name = summon.find("span", class_="js-summon-name").text
        level = int(summon.find("span", class_="txt-summon-level").text.split()[-1])
        friend_name = summon.find("span", class_="txt-supporter-name").text
        friend_lvl = int(
            summon.find("span", class_="txt-supporter-level").text.split()[-1]
        )
        is_friend = (
            "ico-friend" in summon.find("div", class_="prt-supporter-name")["class"]
        )

        summon_data.append(
            {
                "name": name,
                "level": level,
                "friend_name": friend_name,
                "friend_lvl": friend_lvl,
                "is_friend": is_friend,
                "element": summon,
            }
        )

    _log.debug(f"Summons successfully parsed!")
    return summon_data


async def get_best_summon(
    summons: List[BeautifulSoup], summons_from_config: List[str]
) -> Dict:
    """
    Find and print the best summon based on specified criteria.

    Args:
        summons (List[BeautifulSoup]): The BeautifulSoup object representing the HTML.
        summons_from_config (list[str]): The list of summons to pick from the config.
    """
    summon_data = await _extract_summon_data(summons)

    summon_data.sort(key=lambda x: (-x["is_friend"], -x["level"]))

    default_option = summon_data[0]
    best_option = None

    for pick in summons_from_config:
        for summon in summon_data:
            if pick.lower() in summon["name"].lower():
                best_option = summon
                break
        if best_option:
            break

    if best_option is None:
        best_option = default_option

    return best_option
