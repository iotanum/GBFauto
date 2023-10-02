import logging
from gbfauto.helpers.responses.responses import Responses
from gbfauto.helpers.requests.requests import ValidRequests

_log = logging.getLogger(__name__)


class Events:
    """
    Class for handling various events during bot operation.
    """

    def __init__(self, bot):
        """
        Initializes the Events instance.

        Args:
            bot: The bot instance.
        """
        self.bot = bot
        self.events = dict()
        self.p_status = dict()
        self.battle = dict()
        self.responses = Responses(self)

    async def on_dialog(self, dialog):
        """
        Handles the dialog event.

        Args:
            dialog: The dialog object.
        """
        _log.debug(f"[EVENT][DIALOG]: {dialog.message}")
        await dialog.dismiss()

    async def on_page(self, page):
        """
        Handles the page event.

        Args:
            page: The page object.
        """
        _log.debug(f"[EVENT][PAGE]: {page.url}")

    async def on_request(self, request):
        """
        Handles the request event.

        Args:
            request: The request object.
        """
        if ValidRequests.is_valid(request.url):
            _log.debug(f"[EVENT][REQUEST]: {request.url}")

    async def on_response(self, response):
        """
        Handles the response event.

        Args:
            response: The response object.
        """
        await self.responses.handle(response)

    async def initialize_events(self):
        """
        Initializes event handlers.

        Sets up event handlers for page, dialog, request, and response events.
        """
        _log.debug("Initializing events...")
        self.bot.context.on("page", self.on_page)
        self.bot.page.on("dialog", self.on_dialog)
        self.bot.page.on("request", self.on_request)
        self.bot.page.on("response", self.on_response)
        _log.debug("Events initialized!")
