import logging
import asyncio
import inspect
import sys
import traceback

_log = logging.getLogger(__name__)


class BackgroundTask:
    """
    A class representing a background task that can be used as a decorator or directly instantiated.

    Args:
        func (coroutine function): The coroutine function to be executed as a background task.
        interval (float): The time interval (in seconds) at which the task should run.
        count (int, optional): The number of times the task should be repeated. None for indefinite repetition.

    Raises:
        TypeError: If func is not a coroutine function.
    """

    def __init__(self, func, interval, count=None):
        self.coro = func
        self.interval = interval
        self.count = count
        self._task = None
        self._current_loop = 0
        self._injected = None

        if not inspect.iscoroutinefunction(self.coro):
            raise TypeError(
                f"Expected coroutine function, not {type(self.coro).__name__!r}."
            )

    def __get__(self, obj, objtype):
        """
        Descriptor method to allow using the background task as a decorator.

        Args:
            obj (object): The instance the method is bound to.
            objtype (type): The type of the instance.

        Returns:
            BackgroundTask: A new BackgroundTask instance or self if accessed from the class directly.
        """

        if obj is None:
            return self

        copy = BackgroundTask(
            self.coro,
            interval=self.interval,
            count=self.count,
        )
        copy._injected = obj
        setattr(obj, self.coro.__name__, copy)
        return copy

    async def __call__(self, *args, **kwargs):
        """
        Calls the coroutine function associated with the background task.

        Args:
            *args: Variable-length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Any: The result of the coroutine function.
        """

        if self._injected is not None:
            args = (self._injected, *args)

        return await self.coro(*args, **kwargs)

    def start(self, *args, **kwargs):
        """
        Starts the background task.

        Args:
            *args: Variable-length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            asyncio.Task: The asyncio Task representing the background task.
        """

        if self._injected is not None:
            args = (self._injected, *args)

        self._task = asyncio.create_task(self._loop(*args, **kwargs))
        return self._task

    async def _loop(self, *args, **kwargs):
        """
        The main loop for the background task.

        Args:
            *args: Variable-length argument list.
            **kwargs: Arbitrary keyword arguments.
        """

        while True:
            await asyncio.sleep(self.interval)

            try:
                if self._current_loop == self.count:
                    break

                await self.coro(*args, **kwargs)
                self._current_loop += 1

            except Exception as e:
                _log.error(
                    f"Background task '{self.coro.__name__}' failed: {type(e).__name__}, {e}"
                )
                continue


def background_task(*, interval, count=None):
    """
    A decorator to create a BackgroundTask with the specified interval and count.

    Args:
        interval (float): The time interval (in seconds) at which the task should run.
        count (int, optional): The number of times the task should be repeated. None for indefinite repetition.

    Returns:
        callable: A decorator function.
    """

    def decorator(func):
        return BackgroundTask(func, interval=interval, count=count)

    return decorator
