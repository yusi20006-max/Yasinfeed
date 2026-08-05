import json
import urllib.request
import urllib.error
from typing import Dict, Any
from yasinfeed.rewrite.providers.base import BaseAIProvider, AIConfigurationError, AICallError


class HuggingFaceProvider(BaseAIProvider):
    """
    Hugging Face Serverless Inference API provider.
    Utilizes standard Python urllib.request for network communications to remain
    compatible with Termux and minimal environments.
    """

    def validate_config(self) -> None:
        self.api_key = self.config.get("api_key")
        self.model = self.config.get("model") or "meta-llama/Llama-3-8b-instruct"
        self.api_url = self.config.get("api_url") or f"https://api-inference.huggingface.co/models/{self.model}"
        self.temperature = self.config.get("temperature")
        self.max_new_tokens = self.config.get("max_new_tokens")

        if not self.api_key:
            raise AIConfigurationError("Hugging Face API key (api_key) is required.")

    def generate(self, prompt: str, **kwargs) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # Hugging Face Inference API payload structure
        # Standard input is usually {"inputs": prompt, "parameters": {...}}
        parameters = {}
        if self.temperature is not None:
            parameters["temperature"] = self.temperature
        if self.max_new_tokens is not None:
            parameters["max_new_tokens"] = self.max_new_tokens

        # Merge other arbitrary parameters passed in kwargs
        if kwargs:
            parameters.update(kwargs)

        payload = {
            "inputs": prompt
        }
        if parameters:
            payload["parameters"] = parameters

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(self.api_url, data=data, headers=headers, method="POST")

            with urllib.request.urlopen(req, timeout=30) as response:
                resp_data = json.loads(response.read().decode("utf-8"))

                # Hugging Face usually returns a list of dictionaries with 'generated_text'
                if isinstance(resp_data, list) and len(resp_data) > 0:
                    generated_text = resp_data[0].get("generated_text")
                    if generated_text is not None:
                        # Sometimes Hugging Face returns the original prompt inside the response.
                        # It is common to strip the original prompt if it prefixes the response.
                        if generated_text.startswith(prompt):
                            generated_text = generated_text[len(prompt):].strip()
                        return generated_text
                    else:
                        raise AICallError("Hugging Face API response did not contain 'generated_text' in the list.")
                elif isinstance(resp_data, dict):
                    if "generated_text" in resp_data:
                        generated_text = resp_data["generated_text"]
                        if generated_text.startswith(prompt):
                            generated_text = generated_text[len(prompt):].strip()
                        return generated_text
                    elif "error" in resp_data:
                        raise AICallError(f"Hugging Face API error response: {resp_data['error']}")

                raise AICallError(f"Malformed Hugging Face response format: {resp_data}")

        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8") if e.fp else str(e)
            raise AICallError(f"Hugging Face Inference API call failed with HTTP status {e.code}: {err_msg}") from e
        except urllib.error.URLError as e:
            raise AICallError(f"Failed to connect to Hugging Face Inference API: {e.reason}") from e
        except Exception as e:
            raise AICallError(f"An unexpected error occurred during Hugging Face generation: {e}") from e
