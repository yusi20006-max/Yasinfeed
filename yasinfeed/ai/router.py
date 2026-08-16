"""
AIRouter — ordered provider failover for rewrite operations.

Prefer registering a Yasin-AI-backed provider (rewrite.providers.yasinai_provider)
when the yasinai package is available. Domain feed logic stays in YasinFeed.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


class AIRouter:
    def __init__(self, providers: Optional[List[Any]] = None) -> None:
        self.providers: List[Any] = list(providers or [])

    def register(self, p: Any) -> None:
        self.providers.append(p)

    def rewrite(self, text: str) -> str:
        for p in self.providers:
            try:
                if hasattr(p, "rewrite") and callable(getattr(p, "rewrite")):
                    try:
                        return p.rewrite(text)
                    except TypeError:
                        return p.rewrite("", text)
                if hasattr(p, "generate") and callable(getattr(p, "generate")):
                    return p.generate(text)
            except Exception as exc:
                logger.warning("AIRouter provider failed, trying next: %s", exc)
                continue
        return text

    @classmethod
    def from_config(cls, rewrite_config: Optional[dict] = None) -> "AIRouter":
        """Build router from rewrite config block; prefers yasinai when selected."""
        from yasinfeed.rewrite.providers.factory import create_provider

        cfg = rewrite_config or {}
        name = (cfg.get("provider") or "dummy").strip().lower()
        provider_cfg = cfg.get(name, {}) if isinstance(cfg.get(name), dict) else {}
        if name in ("yasin-ai",) and not provider_cfg:
            provider_cfg = cfg.get("yasinai", {}) or {}

        router = cls()
        try:
            primary = create_provider(name, provider_cfg)
            router.register(primary)
        except Exception as exc:
            logger.error("Failed to create primary AI provider '%s': %s", name, exc)

        for extra in cfg.get("failover", []) or []:
            if not isinstance(extra, dict):
                continue
            extra_name = (extra.get("provider") or "").strip().lower()
            extra_cfg = extra.get("config") or {}
            if not extra_name:
                continue
            try:
                router.register(create_provider(extra_name, extra_cfg))
            except Exception as exc:
                logger.warning("Skipping failover provider '%s': %s", extra_name, exc)

        return router
