from __future__ import annotations

import asyncio
import threading
from concurrent.futures import Future, ThreadPoolExecutor


class PromptTranslationRouteExecutor:
    """Run one translation at a time without queueing timed-out requests."""

    def __init__(
        self,
        *,
        busy_error_type,
        cancelled_error_type,
        timeout_error_type,
    ):
        self._busy_error_type = busy_error_type
        self._cancelled_error_type = cancelled_error_type
        self._timeout_error_type = timeout_error_type
        self._lock = threading.RLock()
        self._executor: ThreadPoolExecutor | None = None
        self._in_flight: Future | None = None
        self._closed = False

    @property
    def has_in_flight(self) -> bool:
        with self._lock:
            return self._in_flight is not None and not self._in_flight.done()

    def submit(self, function, *args) -> Future:
        with self._lock:
            if self._closed:
                raise RuntimeError("Prompt translation worker is shut down.")
            if self._in_flight is not None and not self._in_flight.done():
                raise self._busy_error_type()
            if self._executor is None:
                self._executor = ThreadPoolExecutor(
                    max_workers=1,
                    thread_name_prefix="easyuse-anima-translation",
                )
            future = self._executor.submit(function, *args)
            self._in_flight = future
        future.add_done_callback(self._release)
        return future

    def _release(self, future: Future) -> None:
        with self._lock:
            if self._in_flight is future:
                self._in_flight = None

    async def execute(self, function, *args, timeout_seconds: float):
        future = self.submit(function, *args)
        wrapped_future = asyncio.wrap_future(future)
        try:
            done, _pending = await asyncio.wait(
                (wrapped_future,),
                timeout=timeout_seconds,
            )
        except asyncio.CancelledError as exc:
            # Waiting stops immediately, while admission remains occupied until
            # the bounded sync worker really exits.
            wrapped_future.cancel()
            raise self._cancelled_error_type() from exc
        if not done:
            wrapped_future.cancel()
            raise self._timeout_error_type()
        return wrapped_future.result()

    def shutdown(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            executor = self._executor
            self._executor = None
        if executor is not None:
            executor.shutdown(wait=False, cancel_futures=True)


__all__ = ("PromptTranslationRouteExecutor",)
