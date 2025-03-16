import logging
import asyncio

_log = logging.getLogger(__name__)


class BackgroundTask:
    """Runs a coroutine in a background loop at a fixed interval."""

    def __init__(self, func, interval, count=None):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(
                f"Expected coroutine function, not {type(func).__name__!r}."
            )
        self.coro = func
        self.interval = interval
        self.count = count
        self._task = None
        self._instance = None
        self._task_lock = asyncio.Lock()

    def __get__(self, instance, owner):
        """Ensures proper method binding when used in a class."""
        if instance is None:
            return self
        self._instance = instance
        return self

    def start(self, *args, **kwargs):
        """Starts the background task inside the main event loop."""
        loop = asyncio.get_running_loop()  # Use the main Playwright loop
        if self._instance:
            args = (self._instance, *args)
        self._task = loop.create_task(self._run(*args, **kwargs))
        return self._task

    async def _run(self, *args, **kwargs):
        """Loop execution of the task at the specified interval."""
        count_iter = range(self.count) if self.count else iter(int, 1)
        for _ in count_iter:
            async with self._task_lock:  # Prevent race conditions
                try:
                    await self.coro(*args, **kwargs)
                except Exception as e:
                    _log.exception(f"Error in background task: {self.coro.__name__}")
                    _log.error(f"Error details: {e}")
            await asyncio.sleep(self.interval)  # Controlled timing


def background_task(*, interval, count=None):
    """Decorator to create a BackgroundTask."""

    def decorator(func):
        return BackgroundTask(func, interval, count)

    return decorator
