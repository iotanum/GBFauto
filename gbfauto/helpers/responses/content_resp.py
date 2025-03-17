import logging
import re
import asyncio

import playwright

from gbfauto.common.enums import BattleEnums, EventEnums
from gbfauto.common.utils import get_response_body, multiple_keys_exists


_log = logging.getLogger(__name__)


class ContentResponse:
    def __init__(self, responses):
        """
        Initializes the ContentResponse object.

        Args:
            responses: The parent responses object.
        """
        self.bot = responses.bot
        self.common = responses.common
        self.p_status = self.bot.p_status
        self.battle_common = self.bot.battle_common
        self.events_common = self.bot.events_common
        self.battle = self.bot.battle

    @staticmethod
    async def _fix_content_response_body(r_body):
        """
        Removes 'data' key from the response body.

        Args:
            r_body (dict): The response body.

        Returns:
            dict: The modified response body.
        """
        exclude_keys = ["data"]
        return {k: r_body[k] for k in set(list(r_body.keys())) - set(exclude_keys)}

    async def _update_current_ep(self, p_status, resp):
        """
        Updates the current Event Points (EP) for the player.

        Args:
            p_status (dict): The player's status.
            resp: The response object.
        """
        nested_keys = [
            ["option", "status", "status", "now_battle_point"],
            ["option", "mydata_assets", "mydata", "status", "now_battle_point"],
            ["option", "user_status", "now_battle_point"],
        ]

        current_ep = await multiple_keys_exists(
            p_status, nested_keys, resp_url=resp.url
        )

        if current_ep is not None:
            _log.debug(f"Updating 'p_status' 'current_ep' with '{current_ep}'")
            self.p_status["current_ep"] = current_ep
            await self.battle_common.need_ep()

    async def _update_current_ap(self, p_status, resp):
        """
        Updates the current Action Points (AP) for the player.

        Args:
            p_status (dict): The player's status.
            resp: The response object.
        """
        nested_keys = [
            ["option", "status", "status", "now_action_point"],
            ["option", "mydata_assets", "mydata", "status", "now_action_point"],
            ["option", "user_status", "now_action_point"],
        ]

        current_ap = await multiple_keys_exists(
            p_status, nested_keys, resp_url=resp.url
        )

        if current_ap is not None:
            _log.debug(f"Updating 'p_status' 'current_ap' with '{current_ap}'")
            self.p_status["current_ap"] = current_ap
            await self.battle_common.need_ap()

    async def _update_player_status(self, r_body, resp):
        """
        Updates the player's status based on the response.

        Args:
            r_body (dict): The response body.
            resp: The response object.
        """
        _log.debug(f"Trying to update 'p_status' from '{resp.url}'")

        await self._update_current_ap(r_body, resp)
        await self._update_current_ep(r_body, resp)

    async def _update_event_time(self, event=EventEnums.BATTLE_END_EVENT):
        """
        Updates event time based on the response.
        """
        await self.events_common.update_event_time(event=event)

    async def _update_blue_box_count(self, r_body, resp):
        """
        Updates the blue box count.
        """
        # "11" is the key for blue boxes in reward_list
        nested_keys = [["option", "result_data", "rewards", "reward_list", "11"]]

        blue_boxes = await multiple_keys_exists(r_body, nested_keys, resp_url=resp.url)

        # set a default upon first encounter
        if not self.p_status.get("blue_boxes"):
            self.p_status["blue_boxes"] = 0

        if blue_boxes:
            self.p_status["blue_boxes"] += len(blue_boxes.keys())

    async def _update_battle_status(self, r_body, resp):
        """
        Updates the battle status based on the response.

        Args:
            r_body (dict): The response body.
            resp: The response object.
        """
        _log.debug(f"Trying to update 'battle_status' from '{resp.url}'")

        # if it's a result response, update required keys for battle
        result_resp_regex = re.compile(".*result.*/content.*")
        if result_resp_regex.match(resp.url):
            self.battle[BattleEnums.BOSS_KILLED] = True
            self.battle[BattleEnums.BOSS_HPS] = {}

            # should wait until everythign is done?
            async with asyncio.TaskGroup() as tg:
                if "empty" not in resp.url:
                    tg.create_task(self._update_blue_box_count(r_body, resp))
                tg.create_task(self._update_event_time())
                tg.create_task(
                    self._update_event_time(event=EventEnums.RESULT_SCREEN_EVENT)
                )

    async def _update_summon_resp_status(self, r_body, resp):
        """
        Updates summon response status based on the response.

        Args:
            r_body (dict): The response body.
            resp: The response object.
        """
        _log.debug(f"Trying to update 'summon_screen_resp' from '{resp.url}'")

        result_resp_regex = re.compile(".*quest/content/supporter.*")
        if result_resp_regex.match(resp.url):
            await self._update_event_time(event=EventEnums.SUMMON_SCREEN_EVENT)

    async def _check_for_popup(self, r_body):
        """
        Checks for a popup message and updates the event time if found.

        Args:
            r_body (dict): The response body.
        """

        if len(r_body.keys()) == 1:
            if popup_body := r_body.get("popup"):
                _log.debug(f"Popup found in content resp: '{popup_body}'")
                await self._update_event_time(BattleEnums.BATTLE_POPUP)

    async def content_response_handler(self, resp):
        """
        Handles the content response.

        Args:
            resp: The response object.
        """
        try:
            r_body = await get_response_body(resp)
            r_body = await self._fix_content_response_body(r_body)

            # update user status in events
            await self._check_for_popup(r_body)
            await self._update_player_status(r_body, resp)
            await self._update_battle_status(r_body, resp)
            await self._update_summon_resp_status(r_body, resp)

            _log.debug(f"'Content' response handler, updated from '{resp.url}'")
            _log.debug(f"'Content' response handler, player status: {self.p_status}")
            _log.debug(f"'Content' response handler, battle status: {self.battle}")
        except playwright._impl._api_types.Error:
            _log.debug(f"Error while handling content response from {resp.url}")
