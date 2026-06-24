"""
Shared helper for running blocking work with client-disconnect awareness.

Runs a blocking callable in a background thread.  Concurrently, an async
watchdog polls ``request.is_disconnected()``.  When the client disconnects,
the thread's ``threading.Event`` is set so the callable can stop early.
"""
import asyncio
import logging
import threading
from typing import Any, Callable, Optional

from fastapi import Request

logger = logging.getLogger(__name__)


class ClientDisconnected(Exception):
    """Raised inside route handlers when the client disconnects mid-request."""
    pass


async def run_with_disconnect_watch(
    request: Request,
    work: Callable[[threading.Event], Any],
    poll_interval: float = 0.5,
) -> Any:
    """Run *work(cancel_event)* in a thread, cancelling it if the client disconnects.

    Parameters
    ----------
    request:
        The incoming ``fastapi.Request`` — used for ``is_disconnected()`` polling.
    work:
        A synchronous callable that receives a ``threading.Event``.  The callable
        should periodically check ``cancel_event.is_set()`` and return early.
    poll_interval:
        How often (seconds) to poll ``request.is_disconnected()``.

    Returns
    -------
    The return value of *work*.

    Raises
    ------
    ClientDisconnected
        If the client disconnects before *work* finishes.
    """
    cancel_event = threading.Event()
    result: list = []
    exc_holder: list = []

    def _thread_target():
        try:
            result.append(work(cancel_event))
        except Exception as e:
            exc_holder.append(e)

    thread = threading.Thread(target=_thread_target, daemon=True)
    thread.start()

    async def _watcher():
        while thread.is_alive():
            if await request.is_disconnected():
                logger.info("Client disconnected — signalling cancellation")
                cancel_event.set()
                return
            await asyncio.sleep(poll_interval)

    watcher_task = asyncio.create_task(_watcher())

    try:
        thread.join(timeout=poll_interval)
        while thread.is_alive():
            thread.join(timeout=poll_interval)
            await asyncio.sleep(0)
    finally:
        if not watcher_task.done():
            watcher_task.cancel()

    if exc_holder:
        raise exc_holder[0]

    if cancel_event.is_set() and not result:
        raise ClientDisconnected()

    return result[0] if result else None
