"""
FailoverProvider — sequential try of rewrite backends.

Compatible with Yasin-AI-backed providers and legacy providers.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class FailoverProvider:
    def __init__(self, *providers: Any) -> None:
        self.providers = providers

    def rewrite(self, text: str) -> str:
        for p in self.providers:
            try:
                if hasattr(p, "rewrite"):
                    try:
                        return p.rewrite(text)
                    except TypeError:
                        return p.rewrite("", text)
                if hasattr(p, "generate"):
                    return p.generate(text)
            except Exception as exc:
                logger.warning("FailoverProvider: provider failed: %s", exc)
                continue
        return text
