import logging
import os

from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

_log = logging.getLogger(__name__)

CONTEXT_OPTIONS = {
    "viewport": {"width": 560, "height": 760},
}
BROWSER_OPTIONS = {
    "headless": False,
    "handle_sigint": False,
    "user_data_dir": os.path.join(os.getcwd(), "browser_user_data"),
    "args": [
        "--hide-crash-restore-bubble",
    ],
    "ignore_default_args": ["--enable-automation", "--mute-audio"],
    "chromium_sandbox": True,
}

AUTH_PAGE = "http://game.granbluefantasy.jp/#authentication"
_log.debug(f"Engine configuration: {BROWSER_OPTIONS}, {CONTEXT_OPTIONS}")


async def _browser_events(browser):
    """
    Defines browser event handling, such as 'disconnected'.

    Args:
        browser: The browser instance.
    """
    browser.on("disconnected", lambda: _log.debug("Engine disconnected!"))


async def launch_engine():
    """
    Launches the Playwright engine and returns a page object.

    Returns:
        page: The Playwright page object.
    """
    _log.debug("Launching engine...")
    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        **BROWSER_OPTIONS, **CONTEXT_OPTIONS
    )
    page = context.pages[0]
    await page.goto(AUTH_PAGE)
    await stealth_async(page)
    _log.debug("Engine launched!")
    return page
