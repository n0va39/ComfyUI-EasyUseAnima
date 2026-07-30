from __future__ import annotations

import asyncio
import threading
import weakref


FILE_IO_MAX_IN_FLIGHT = 4
_FILE_IO_LIMITERS_LOCK = threading.Lock()
_FILE_IO_LIMITERS: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()


def file_io_limiter() -> asyncio.Semaphore:
    loop = asyncio.get_running_loop()
    with _FILE_IO_LIMITERS_LOCK:
        limiter_ref = _FILE_IO_LIMITERS.get(loop)
        limiter = limiter_ref() if limiter_ref is not None else None
        if limiter is None:
            limiter = asyncio.Semaphore(FILE_IO_MAX_IN_FLIGHT)
            # A contended Semaphore binds itself to the event loop. Store only
            # a weak value so the registry cannot root a closed loop through
            # registry -> semaphore -> loop. Active/waiting calls and worker
            # callbacks keep their limiter alive until the real work finishes.
            _FILE_IO_LIMITERS[loop] = weakref.ref(limiter)
        return limiter


def release_file_io_slot(
    limiter: asyncio.Semaphore,
    worker: asyncio.Task,
) -> None:
    limiter.release()
    if worker.cancelled():
        return
    # Retrieve failures even when the request that submitted the worker was
    # cancelled. A live caller still receives the same exception from await.
    worker.exception()


async def run_file_io(function, /, *args, **kwargs):
    limiter = file_io_limiter()
    await limiter.acquire()
    worker = asyncio.create_task(asyncio.to_thread(function, *args, **kwargs))
    worker.add_done_callback(
        lambda completed, owned_limiter=limiter: release_file_io_slot(
            owned_limiter,
            completed,
        )
    )
    return await asyncio.shield(worker)


__all__ = (
    "FILE_IO_MAX_IN_FLIGHT",
    "file_io_limiter",
    "release_file_io_slot",
    "run_file_io",
)
