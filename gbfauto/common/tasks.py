import logging
import asyncio
import threading

_log = logging.getLogger(__name__)


class BackgroundTaskManager:
    """Manages all background tasks within a single asyncio event loop in a separate thread."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._loop = asyncio.new_event_loop()
                cls._instance._thread = threading.Thread(
                    target=cls._instance._run_loop, daemon=True
                )
                cls._instance._thread.start()
        return cls._instance

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def create_task(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self._loop)


class BackgroundTask:
    """Runs a coroutine in a background thread at a fixed interval."""

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
        """Starts the background task."""
        manager = BackgroundTaskManager()
        if self._instance:
            args = (self._instance, *args)
        self._task = manager.create_task(self._run(*args, **kwargs))
        return self._task

    async def _run(self, *args, **kwargs):
        """Loop execution of the task at the specified interval."""
        count_iter = range(self.count) if self.count else iter(int, 1)
        for _ in count_iter:
            # Ensure that only one instance of the task runs at a time
            async with self._task_lock:
                try:
                    await self.coro(*args, **kwargs)
                except Exception as e:
                    _log.exception(f"Error in background task: {self.coro.__name__}")
                    _log.error(f"Error details: {e}")
            await asyncio.sleep(self.interval)  # Delay before next execution


def background_task(*, interval, count=None):
    """Decorator to create a BackgroundTask."""

    def decorator(func):
        return BackgroundTask(func, interval, count)

    return decorator
