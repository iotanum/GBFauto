import logging
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

_log = logging.getLogger(__name__)

BROWSER_OPTIONS = {
    "headless": False,
}
CONTEXT_OPTIONS = {
    "viewport": {"width": 560, "height": 760},
}

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
    browser = await pw.chromium.launch(**BROWSER_OPTIONS)
    context = await browser.new_context(**CONTEXT_OPTIONS)
    page = await context.new_page()
    await stealth_async(page)
    _log.debug("Engine launched!")
    return page
