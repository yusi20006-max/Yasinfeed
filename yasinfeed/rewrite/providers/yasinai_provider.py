"""
YasinAIProvider — BaseAIProvider backed by Yasin-AI public contracts v1.

Consumes ONLY:
  - yasinai.contracts (GenerationRequest)
  - yasinai.services (GenerationService)

Must NOT import private Yasin-AI packages (knowledge_platform, etc.).
"""

from __future__ import annotations

import logging
import os
from types import SimpleNamespace
from typing import Any, Dict, Optional

from yasinfeed.rewrite.providers.base import (
    AICallError,
    AIConfigurationError,
    BaseAIProvider,
)

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    "You are a professional content editor for news feeds. "
    "Rewrite and improve the following article for clarity and engagement. "
    "Preserve meaning, facts, and any important entities. "
    "Output only the rewritten article text."
)


def is_yasinai_available() -> bool:
    try:
        import yasinai  # noqa: F401
        from yasinai.contracts import GenerationRequest  # noqa: F401
        from yasinai.services import GenerationService  # noqa: F401

        return True
    except ImportError:
        return False


def _ensure_openai_env(api_key: Optional[str]) -> None:
    if api_key and not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = api_key


def _build_request(
    *,
    prompt: str,
    model: Optional[str],
    max_tokens: int,
    temperature: float,
    system_prompt: Optional[str],
    provider: Optional[str],
) -> Any:
    try:
        from yasinai.contracts import GenerationRequest

        return GenerationRequest(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
            provider=provider,
            metadata={"source": "yasinfeed"},
        )
    except ImportError:
        return SimpleNamespace(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
            provider=provider,
            metadata={"source": "yasinfeed"},
        )


class YasinAIProvider(BaseAIProvider):
    """
    Canonical AI path for YasinFeed rewrite/generation.

    Config keys (under rewrite.yasinai):
      api_key, model, temperature, max_tokens, system_prompt, provider
    """

    def validate_config(self) -> None:
        self.api_key = self.config.get("api_key") or os.environ.get("OPENAI_API_KEY") or ""
        self.model = self.config.get("model") or "gpt-4o-mini"
        self.temperature = float(self.config.get("temperature", 0.7))
        max_tokens = self.config.get("max_tokens")
        self.max_tokens = int(max_tokens) if max_tokens is not None else 2048
        self.system_prompt = self.config.get("system_prompt") or DEFAULT_SYSTEM_PROMPT
        self.preferred_provider = self.config.get("provider")  # optional pin (openai/local/...)
        self._generation_service = self.config.get("_generation_service")  # test injection

        _ensure_openai_env(self.api_key)

        if self._generation_service is None and not is_yasinai_available():
            raise AIConfigurationError(
                "Yasin-AI package is not installed. Install Yasin-AI v1.1.4+ "
                "or set rewrite.provider to dummy/openai/huggingface."
            )

    def _service(self) -> Any:
        if self._generation_service is not None:
            return self._generation_service
        from yasinai.services import GenerationService

        return GenerationService()

    def generate(self, prompt: str, **kwargs) -> str:
        if not (prompt or "").strip():
            return prompt or ""

        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        model = kwargs.get("model", self.model)
        system_prompt = kwargs.get("system_prompt", self.system_prompt)

        try:
            request = _build_request(
                prompt=prompt,
                model=model,
                max_tokens=int(max_tokens),
                temperature=float(temperature),
                system_prompt=system_prompt,
                provider=self.preferred_provider,
            )
            result = self._service().generate(request)
        except AICallError:
            raise
        except Exception as exc:
            logger.error("Yasin-AI generation failed: %s", exc, exp_info=True if False else True)
            raise AICallError(f"Yasin-AI generation failed: {exc}") from exc

        if not getattr(result, "success", False):
            err = getattr(result, "error", "unknown error")
            raise AICallError(f"Yasin-AI generation unsuccessful: {err}")

        text = (getattr(result, "text", None) or "").strip()
        if not text:
            raise AICallError("Yasin-AI returned empty text")
        return text

    def rewrite(self, title: str, content: str) -> str:
        prompt = f"Title: {title}\nContent: {content}"
        return self.generate(prompt)
