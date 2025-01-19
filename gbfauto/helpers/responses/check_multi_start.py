import logging

from gbfauto.common.utils import get_response_body, keys_exists, get_xpath_from_ele


_log = logging.getLogger(__name__)


class CheckMultiStart:
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
        self.popups = self.bot.popup
        self.utils = self.bot.utils

    async def _is_popup(self, r_body):
        """
        Checks if the response body contains a popup.

        Args:
            r_body (dict): The response body.
        """
        return await keys_exists(r_body, "popup")

    async def _get_ele_for_popup(self):
        """
        Gets the element for the popup.

        Returns:
            str: The xpath for the popup.
        """
        popup_ok_btn_ele = await self.utils.bs(find=("div", {"class": "btn-usual-ok"}))

        return await get_xpath_from_ele(popup_ok_btn_ele, debug=False)

    async def _handle_popup(self, r_body):
        """
        Handles the popup if it exists.

        Args:
            r_body (dict): The response body.
        """
        if popup := await self._is_popup(r_body):
            if "already ended" in popup.get("body"):
                self.popup = await self._get_ele_for_popup()
                _log.info(popup.get("body"))

    async def check_multi_start_handler(self, resp):
        """
        Handles the check_multi_start result response.

        Args:
            resp: The response object.
        """
        r_body = await get_response_body(resp)
        await self._handle_popup(r_body)

        _log.debug(f"Battle info updated from {resp.url}")
