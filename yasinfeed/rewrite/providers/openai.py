import json
import urllib.request
import urllib.error
from typing import Dict, Any
from yasinfeed.rewrite.providers.base import BaseAIProvider, AIConfigurationError, AICallError


class OpenAIProvider(BaseAIProvider):
    """
    OpenAI-compatible AI provider.
    Communicates with OpenAI or custom OpenAI-compatible proxy endpoints (like Ollama, LM Studio, etc.)
    using standard python urllib.request to avoid heavy third-party dependencies.
    """

    def validate_config(self) -> None:
        self.api_key = self.config.get("api_key")
        self.base_url = self.config.get("base_url") or "https://api.openai.com/v1"
        self.model = self.config.get("model") or "gpt-3.5-turbo"
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens")

        # Normalize trailing slash on base_url
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]

        # Note: Some OpenAI-compatible servers (like Ollama or local gateways) do not require API keys,
        # but official OpenAI does. We will raise an error if api_key is missing AND the url is official OpenAI.
        if not self.api_key and "api.openai.com" in self.base_url:
            raise AIConfigurationError("OpenAI API key is required when using official OpenAI base_url.")

    def generate(self, prompt: str, **kwargs) -> str:
        url = f"{self.base_url}/chat/completions"

        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            **kwargs
        }
        if self.max_tokens is not None:
            payload["max_tokens"] = self.max_tokens

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")

            with urllib.request.urlopen(req, timeout=30) as response:
                resp_data = json.loads(response.read().decode("utf-8"))

                choices = resp_data.get("choices")
                if not choices or len(choices) == 0:
                    raise AICallError("Received empty or malformed choice array from OpenAI API.")

                content = choices[0].get("message", {}).get("content")
                if content is None:
                    raise AICallError("Response message did not contain a 'content' field.")

                return content

        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8") if e.fp else str(e)
            raise AICallError(f"OpenAI API call failed with HTTP status {e.code}: {err_msg}") from e
        except urllib.error.URLError as e:
            raise AICallError(f"Failed to connect to OpenAI API endpoint: {e.reason}") from e
        except Exception as e:
            raise AICallError(f"An unexpected error occurred during OpenAI generation: {e}") from e
