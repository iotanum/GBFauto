import logging

from gbfauto.helpers.responses.responses import Responses
from gbfauto.helpers.requests.requests import ValidRequests


_log = logging.getLogger(__name__)


class Events:
    def __init__(self, bot):
        self.bot = bot
        self.events = dict()
        self.p_status = dict()
        self.battle = dict()
        self.responses = None

    async def on_dialog(self, dialog):
        _log.debug(f"[EVENT][DIALOG]: {dialog.message}")
        await dialog.dismiss()

    async def on_console(self, console):
        _log.debug(f"[EVENT][CONSOLE]: {console.text}")

    async def on_page(self, page):
        _log.debug(f"[EVENT][PAGE]: {page.url}")

    async def on_request(self, request):
        if ValidRequests.is_valid(request.url):
            _log.debug(f"[EVENT][REQUEST]: {request.url}")

    async def on_response(self, response):
        await self.responses.handle(response)

    async def get(self, event):
        try:
            return self.events[event]
        except KeyError:
            return False

    async def initialize_events(self):
        _log.debug("Initializing events...")
        self.bot.bot.on("dialog", self.on_dialog)
        # self.bot.bot.on("console", self.on_console)
        self.bot.context.on("page", self.on_page)
        self.bot.bot.on("request", self.on_request)
        self.bot.bot.on("response", self.on_response)
        self.responses = Responses(self.bot)
        self.events = self
        _log.debug("Events initialized!")
