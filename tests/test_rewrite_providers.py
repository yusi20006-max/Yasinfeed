import unittest
from unittest.mock import patch, MagicMock
import json
import urllib.error
from io import BytesIO

from yasinfeed.rewrite.providers.base import (
    BaseAIProvider,
    AIProviderError,
    AIConfigurationError,
    AICallError
)
from yasinfeed.rewrite.providers.dummy import DummyProvider
from yasinfeed.rewrite.providers.openai import OpenAIProvider
from yasinfeed.rewrite.providers.huggingface import HuggingFaceProvider
from yasinfeed.rewrite.providers.factory import create_provider, PROVIDERS
from yasinfeed.rewrite import RewriteModule


class TestAIProviders(unittest.TestCase):

    def test_base_provider_instantiation_raises(self):
        # BaseAIProvider cannot be instantiated directly due to abstract methods
        with self.assertRaises(TypeError):
            BaseAIProvider({})

    def test_dummy_provider(self):
        # Dummy provider should handle lack of configuration
        p = DummyProvider(None)
        p.validate_config()
        self.assertEqual(p.generate("Hello"), "[Dummy AI] processed prompt: Hello")

        # Custom prefix
        p2 = DummyProvider({"prefix": "[Test AI]"})
        self.assertEqual(p2.generate("World"), "[Test AI] processed prompt: World")

    def test_factory_invalid_provider(self):
        with self.assertRaises(AIConfigurationError) as ctx:
            create_provider("invalid_provider_name", {})
        self.assertIn("Unsupported AI provider", str(ctx.exception))

    def test_factory_valid_creation(self):
        p = create_provider("dummy", {"prefix": "[Custom]"})
        self.assertIsInstance(p, DummyProvider)
        self.assertEqual(p.generate("x"), "[Custom] processed prompt: x")

    def test_openai_validation(self):
        # Official base_url requires api_key
        with self.assertRaises(AIConfigurationError) as ctx:
            OpenAIProvider({"base_url": "https://api.openai.com/v1", "api_key": ""})
        self.assertIn("OpenAI API key is required", str(ctx.exception))

        # Proxy/Alternative URL does not strictly require api_key
        p = OpenAIProvider({"base_url": "http://localhost:11434/v1"})
        self.assertEqual(p.base_url, "http://localhost:11434/v1")

    @patch("urllib.request.urlopen")
    def test_openai_generate_success(self, mock_urlopen):
        # Mock successful JSON response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "This is rewritten content"
                    }
                }
            ]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        p = OpenAIProvider({
            "api_key": "test-key",
            "model": "gpt-4",
            "temperature": 0.5,
            "max_tokens": 100
        })
        res = p.generate("Raw text")
        self.assertEqual(res, "This is rewritten content")

    @patch("urllib.request.urlopen")
    def test_openai_generate_failures(self, mock_urlopen):
        # Case 1: Empty choices
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"choices": []}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        p = OpenAIProvider({"api_key": "test-key"})
        with self.assertRaises(AICallError) as ctx:
            p.generate("Raw text")
        self.assertIn("Received empty or malformed choice array", str(ctx.exception))

        # Case 2: HTTPError
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.openai.com/v1/chat/completions",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=BytesIO(b"Invalid API Key")
        )
        with self.assertRaises(AICallError) as ctx:
            p.generate("Raw text")
        self.assertIn("OpenAI API call failed with HTTP status 401: Invalid API Key", str(ctx.exception))

        # Case 3: URLError
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        with self.assertRaises(AICallError) as ctx:
            p.generate("Raw text")
        self.assertIn("Failed to connect to OpenAI API endpoint", str(ctx.exception))

    def test_huggingface_validation(self):
        # Requires API key
        with self.assertRaises(AIConfigurationError) as ctx:
            HuggingFaceProvider({"api_key": ""})
        self.assertIn("Hugging Face API key (api_key) is required", str(ctx.exception))

    @patch("urllib.request.urlopen")
    def test_huggingface_generate_success_list(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {"generated_text": "Prompt: Raw text\nResponse: Rewritten text"}
        ]).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        p = HuggingFaceProvider({
            "api_key": "hf-key",
            "model": "tiiuae/falcon-7b-instruct",
            "temperature": 0.8,
            "max_new_tokens": 50
        })
        res = p.generate("Prompt: Raw text\n")
        self.assertEqual(res, "Response: Rewritten text")

    @patch("urllib.request.urlopen")
    def test_huggingface_generate_success_dict(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "generated_text": "Standalone generated text"
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        p = HuggingFaceProvider({"api_key": "hf-key"})
        res = p.generate("Raw prompt")
        self.assertEqual(res, "Standalone generated text")

    @patch("urllib.request.urlopen")
    def test_huggingface_generate_failures(self, mock_urlopen):
        # Case 1: HF returning dict with error
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "error": "Model is loading"
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        p = HuggingFaceProvider({"api_key": "hf-key"})
        with self.assertRaises(AICallError) as ctx:
            p.generate("Prompt")
        self.assertIn("Hugging Face API error response: Model is loading", str(ctx.exception))

        # Case 2: Malformed response format
        mock_response.read.return_value = json.dumps({"unknown_key": "val"}).encode("utf-8")
        with self.assertRaises(AICallError) as ctx:
            p.generate("Prompt")
        self.assertIn("Malformed Hugging Face response format", str(ctx.exception))

    @patch("urllib.request.urlopen")
    def test_rewrite_module_integration(self, mock_urlopen):
        # Mock engine config to use OpenAI provider
        mock_engine = MagicMock()
        mock_engine.config = {
            "rewrite": {
                "provider": "openai",
                "openai": {
                    "api_key": "some-key",
                    "base_url": "https://api.openai.com/v1"
                }
            }
        }

        module = RewriteModule(mock_engine)
        self.assertTrue(module.initialize())
        self.assertTrue(module.start())

        # Test successful rewrite
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "Success content"}}]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        rewritten = module.rewrite_content("Test Title", "Raw content")
        self.assertEqual(rewritten, "Success content")

        # Test graceful fallback when provider raises an exception
        mock_urlopen.side_effect = urllib.error.URLError("Network down")
        fallback_res = module.rewrite_content("Failed Title", "Original text")
        self.assertEqual(fallback_res, "[Rewritten Failed - Fallback]: Original text")

        self.assertTrue(module.stop())


if __name__ == "__main__":
    unittest.main()
