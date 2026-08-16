"""
Contract tests for Yasin-AI public-contract provider (#52 / #54 CI).

Uses injected mock GenerationService — no live network / yasinai install required.
Uses unittest only (CI installs requirements.txt without pytest).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from unittest import TestCase
from unittest.mock import MagicMock, patch

from yasinfeed.rewrite.providers.base import AICallError, AIConfigurationError
from yasinfeed.rewrite.providers.factory import create_provider, PROVIDERS
from yasinfeed.rewrite.providers.yasinai_provider import (
    YasinAIProvider,
)
from yasinfeed.ai.router import AIRouter


@dataclass
class _FakeResult:
    success: bool
    text: str = ""
    error: Optional[str] = None


class TestYasinAIProvider(TestCase):
    def test_factory_registers_yasinai(self):
        self.assertIn("yasinai", PROVIDERS)
        self.assertIs(PROVIDERS["yasinai"], YasinAIProvider)

    def test_yasinai_generate_success(self):
        service = MagicMock()
        service.generate.return_value = _FakeResult(success=True, text="rewritten article")
        p = YasinAIProvider({"_generation_service": service, "model": "gpt-4o-mini"})
        out = p.generate("raw text")
        self.assertEqual(out, "rewritten article")
        self.assertTrue(service.generate.called)
        req = service.generate.call_args[0][0]
        self.assertEqual(req.prompt, "raw text")
        self.assertEqual(req.model, "gpt-4o-mini")

    def test_yasinai_generate_failure_raises(self):
        service = MagicMock()
        service.generate.return_value = _FakeResult(success=False, error="down")
        p = YasinAIProvider({"_generation_service": service})
        with self.assertRaises(AICallError):
            p.generate("x")

    def test_yasinai_rewrite_uses_title_content(self):
        service = MagicMock()
        service.generate.return_value = _FakeResult(success=True, text="ok")
        p = YasinAIProvider({"_generation_service": service})
        p.rewrite("T", "C")
        req = service.generate.call_args[0][0]
        self.assertIn("Title: T", req.prompt)
        self.assertIn("Content: C", req.prompt)

    def test_yasinai_missing_package_raises_config_error(self):
        with patch(
            "yasinfeed.rewrite.providers.yasinai_provider.is_yasinai_available",
            return_value=False,
        ):
            with self.assertRaises(AIConfigurationError):
                YasinAIProvider({})

    def test_create_provider_yasinai_with_injected_service(self):
        service = MagicMock()
        service.generate.return_value = _FakeResult(success=True, text="via factory")
        p = create_provider("yasinai", {"_generation_service": service})
        self.assertIsInstance(p, YasinAIProvider)
        self.assertEqual(p.generate("p"), "via factory")

    def test_ai_router_failover_to_next(self):
        bad = MagicMock()
        bad.rewrite.side_effect = RuntimeError("fail")
        good = MagicMock()
        good.rewrite.return_value = "ok"
        router = AIRouter([bad, good])
        self.assertEqual(router.rewrite("input"), "ok")

    def test_ai_router_all_fail_returns_original(self):
        bad = MagicMock()
        bad.rewrite.side_effect = RuntimeError("fail")
        router = AIRouter([bad])
        self.assertEqual(router.rewrite("original"), "original")

    def test_no_private_imports_in_yasinai_provider(self):
        source = (
            Path(__file__).resolve().parents[1]
            / "yasinfeed"
            / "rewrite"
            / "providers"
            / "yasinai_provider.py"
        )
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
            self.assertNotIn(forbidden, joined)


if __name__ == "__main__":
    import unittest

    unittest.main()
