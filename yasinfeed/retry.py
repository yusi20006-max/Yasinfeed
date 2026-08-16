"""Retry helper with exponential backoff."""

from __future__ import annotations

import logging
import time
from typing import Callable, Optional, TypeVar

T = TypeVar("T")

logger = logging.getLogger("yasinfeed.retry")


def retry(
    fn: Callable[[], T],
    retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    *,
    exceptions: tuple = (Exception,),
    logger_: Optional[logging.Logger] = None,
) -> T:
    """
    Call ``fn`` up to ``retries`` times with exponential backoff.

    Raises the last exception if all attempts fail.
    """
    if retries < 1:
        raise ValueError("retries must be >= 1")
    log = logger_ or logger
    last_exc: Optional[BaseException] = None
    for i in range(retries):
        try:
            return fn()
        except exceptions as exc:
            last_exc = exc
            if i == retries - 1:
                break
            wait = delay * (backoff ** i)
            log.warning(
                "retry %s/%s failed (%s); sleeping %.2fs",
                i + 1,
                retries,
                exc,
                wait,
            )
            time.sleep(wait)
    assert last_exc is not None
    raise last_exc
