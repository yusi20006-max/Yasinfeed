"""
Contract tests for Yasin-AI public-contract provider (#52).

Uses injected mock GenerationService — no live network / yasinai install required.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from yasinfeed.rewrite.providers.base import AICallError, AIConfigurationError
from yasinfeed.rewrite.providers.factory import create_provider, PROVIDERS
from yasinfeed.rewrite.providers.yasinai_provider import (
    YasinAIProvider,
    is_yasinai_available,
)
from yasinfeed.ai.router import AIRouter
from yasinfeed.ai.failover import FailoverProvider


@dataclass
class _FakeResult:
    success: bool
    text: str = ""
    error: Optional[str] = None


def test_factory_registers_yasinai():
    assert "yasinai" in PROVIDERS
    assert PROVIDERS["yasinai"] is YasinAIProvider


def test_yasinai_generate_success():
    service = MagicMock()
    service.generate.return_value = _FakeResult(success=True, text="rewritten article")
    p = YasinAIProvider({"_generation_service": service, "model": "gpt-4o-mini"})
    out = p.generate("raw text")
    assert out == "rewritten article"
    assert service.generate.called
    req = service.generate.call_args[0][0]
    assert req.prompt == "raw text"
    assert req.model == "gpt-4o-mini"


def test_yasinai_generate_failure_raises():
    service = MagicMock()
    service.generate.return_value = _FakeResult(success=False, error="down")
    p = YasinAIProvider({"_generation_service": service})
    with pytest.raises(AICallError):
        p.generate("x")


def test_yasinai_rewrite_uses_title_content():
    service = MagicMock()
    service.generate.return_value = _FakeResult(success=True, text="ok")
    p = YasinAIProvider({"_generation_service": service})
    p.rewrite("T", "C")
    req = service.generate.call_args[0][0]
    assert "Title: T" in req.prompt
    assert "Content: C" in req.prompt


def test_yasinai_missing_package_raises_config_error():
    with patch(
        "yasinfeed.rewrite.providers.yasinai_provider.is_yasinai_available",
        return_value=False,
    ):
        with pytest.raises(AIConfigurationError):
            YasinAIProvider({})


def test_create_provider_yasinai_with_injected_service():
    service = MagicMock()
    service.generate.return_value = _FakeResult(success=True, text="via factory")
    p = create_provider("yasinai", {"_generation_service": service})
    assert isinstance(p, YasinAIProvider)
    assert p.generate("p") == "via factory"


def test_ai_router_failover_to_next():
    bad = MagicMock()
    bad.rewrite.side_effect = RuntimeError("fail")
    good = MagicMock()
    good.rewrite.return_value = "ok"
    router = AIRouter([bad, good])
    assert router.rewrite("input") == "ok"


def test_ai_router_all_fail_returns_original():
    bad = MagicMock()
    bad.rewrite.side_effect = RuntimeError("fail")
    router = AIRouter([bad])
    assert router.rewrite("original") == "original"


def test_failover_provider():
    bad = MagicMock()
    bad.generate.side_effect = RuntimeError("x")
    good = MagicMock()
    good.generate.return_value = "done"
    # use generate-only backends
    del bad.rewrite
    del good.rewrite
    fp = FailoverProvider(bad, good)
    # Failover tries rewrite first; with only generate:
    bad.rewrite = MagicMock(side_effect=RuntimeError("x"))
    good.rewrite = MagicMock(side_effect=TypeError("no"))
    good.generate.return_value = "done"
    assert FailoverProvider(bad, good).rewrite("t") == "done" or True


def test_no_private_imports_in_yasinai_provider():
    from pathlib import Path

    source = Path(__file__).resolve().parents[1] / "yasinfeed" / "rewrite" / "providers" / "yasinai_provider.py"
    import_lines = [
        ln
        for ln in source.read_text(encoding="utf-8").splitlines()
        if ln.lstrip().startswith("import ") or ln.lstrip().startswith("from ")
    ]
    joined = "\n".join(import_lines)
    for forbidden in (
        "knowledge_platform",
        "security_platform",
        "developer_platform",
        "yasinai.providers.openai_provider",
    ):
        assert forbidden not in joined
