"""
Cancellation token for cooperative long-running operation cancellation.

Provides both a threading.Event-backed token (for use inside worker threads)
and an asyncio.Event-backed token (for async code).
"""
import threading
import asyncio


class CancellationToken:
    """Thread-safe cancellation token backed by threading.Event."""

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def check(self) -> None:
        """Raise OperationCancelledError if cancelled."""
        if self.is_cancelled:
            raise OperationCancelledError("Operation was cancelled")

    def wait(self, timeout: float | None = None) -> bool:
        """Block until cancelled or timeout. Returns True if cancelled."""
        return self._event.wait(timeout=timeout)


class OperationCancelledError(Exception):
    """Raised when an operation is cancelled via CancellationToken."""
    pass


class AsyncCancellationToken:
    """Asyncio-compatible cancellation token backed by asyncio.Event."""

    def __init__(self) -> None:
        self._event = asyncio.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def check(self) -> None:
        if self.is_cancelled:
            raise OperationCancelledError("Operation was cancelled")

    async def wait(self) -> None:
        await self._event.wait()


def cancellation_token_from_threading(ct: CancellationToken) -> AsyncCancellationToken:
    """Create an AsyncCancellationToken that mirrors a CancellationToken."""
    act = AsyncCancellationToken()
    if ct.is_cancelled:
        act.cancel()
    return act
