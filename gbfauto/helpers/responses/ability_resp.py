import logging

from gbfauto.common.utils import get_response_body, keys_exists
from gbfauto.common.enums import EventEnums
from dotenv import load_dotenv
import os

_log = logging.getLogger(__name__)


class AbilityResultResponse:
    """
    Class handling the response for ability results.
    """

    def __init__(self, responses):
        """
        Initializes the AbilityResultResponse instance.

        Args:
            responses: Response handler instance.
        """
        self.bot = responses.bot
        self.resp_common = responses.common
        self.events_common = self.bot.events_common
        self.battle = self.bot.battle

    async def _update_ability_result(self, r_body, resp):
        """
        Updates ability result based on the response.
        """
        await self.resp_common.update_turn(r_body, resp)
        await self.resp_common.update_summon_availability(r_body, resp)

    async def _get_refresh_skills_from_config(self):
        load_dotenv(".env", override=True)
        refresh_skills = os.getenv("REFRESH_ABILITIES", None)
        refresh_skills = refresh_skills.split(",") if refresh_skills else []
        return [skill.strip().lower() for skill in refresh_skills]

    async def _get_ability_name(self, r_body, resp):
        scenarios = await keys_exists(r_body, "scenario", resp_url=resp.url)

        if scenarios:
            ability_event = await self.resp_common.gather_event(scenarios, {"ability"})
            ability_name = ability_event.get("name")
            if ability_name:
                return ability_name.lower()

    async def _check_refresh_skill(self, r_body, resp):
        """
        Checks if the ability result is a refresh skill.
        """
        refresh_skills = await self._get_refresh_skills_from_config()

        ability_name = await self._get_ability_name(r_body, resp)
        if ability_name in refresh_skills:
            _log.debug(f"Refresh skill detected: {ability_name}")
            await self.events_common.update_event_time(EventEnums.ABILITY_REFRESH_EVENT)

    async def ability_result_handler(self, resp):
        """
        Handles the ability result response.

        Args:
            resp: The response object.
        """
        r_body = await get_response_body(resp)
        await self.events_common.update_event_time(EventEnums.ABILITY_EVENT)
        await self.resp_common.update_popup_status(r_body, resp)
        await self.resp_common.update_battle_from_scenarios(r_body, resp)
        await self._check_refresh_skill(r_body, resp)
        await self._update_ability_result(r_body, resp)

        _log.debug(f"Ability response handled from '{resp.url}'")
        _log.debug(f"Battle Status: {self.battle}")
