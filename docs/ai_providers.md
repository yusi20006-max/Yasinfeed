# AI Provider System Layer

YasinFeed includes a highly modular, decoupled AI provider system inside the `yasinfeed/rewrite` module. It defines a standard interface and supports multiple interchangeable backends without loading heavy, bloated third-party dependencies (like `openai` or `huggingface_hub` Python SDKs). This ensures lightweight compatibility with environments such as Linux and Android Termux.

---

## Architectural Layout

```
yasinfeed/rewrite/
├── __init__.py           # RewriteModule (orchestrates execution & fallback)
└── providers/
    ├── __init__.py
    ├── base.py           # Provider Interface and Exception Classes
    ├── dummy.py          # Lightweight Dummy / Dry-Run Provider
    ├── factory.py        # Factory function mapping names to classes
    ├── huggingface.py    # Hugging Face Serverless Inference API Provider
    └── openai.py         # OpenAI-compatible API Provider (urllib-based)
```

---

## Standard Provider Interface

All AI providers must inherit from `BaseAIProvider` inside `yasinfeed/rewrite/providers/base.py` and implement its abstract methods:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAIProvider(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}
        self.validate_config()

    @abstractmethod
    def validate_config(self) -> None:
        """Raises AIConfigurationError if any config parameters are invalid or missing."""
        pass

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Sends generation request to the provider. Raises AICallError if failed."""
        pass
```

### Exception System
- `AIProviderError`: Base exception for all provider issues.
- `AIConfigurationError`: Raised during configuration/initialization validation.
- `AICallError`: Raised during network calls or inference issues.

---

## Supported Providers

### 1. `dummy` (Default)
The offline provider does not make any network requests. It processes prompts locally by prefixing or echoing the prompt.
- **Config parameters:**
  - `prefix` (optional): Prefix added to the mocked output.

### 2. `openai`
Communicates with standard OpenAI API (`https://api.openai.com/v1`) or any OpenAI-compatible API endpoints (such as Local Ollama, LM Studio, vLLM, etc.) using Python's pure-standard library `urllib.request`.
- **Config parameters:**
  - `api_key` (required for official OpenAI, optional for local endpoints)
  - `base_url` (defaults to `https://api.openai.com/v1`)
  - `model` (defaults to `gpt-3.5-turbo`)
  - `temperature` (defaults to `0.7`)
  - `max_tokens` (optional)

### 3. `huggingface`
Uses Hugging Face's serverless Inference API using Python's pure-standard library `urllib.request`.
- **Config parameters:**
  - `api_key` (required Hugging Face User Access Token)
  - `model` (defaults to `meta-llama/Llama-3-8b-instruct`)
  - `api_url` (defaults to `https://api-inference.huggingface.co/models/{model}`)
  - `temperature` (optional)
  - `max_new_tokens` (optional)

---

## Configuration

Options are configured under the `rewrite` namespace in `config/config.yaml`.

```yaml
rewrite:
  provider: "dummy" # "dummy", "openai", or "huggingface"
  openai:
    api_key: "your-openai-api-key"
    base_url: "https://api.openai.com/v1"
    model: "gpt-3.5-turbo"
    temperature: 0.7
    max_tokens: null
  huggingface:
    api_key: "your-hf-token"
    model: "meta-llama/Llama-3-8b-instruct"
    api_url: null
    temperature: null
    max_new_tokens: null
```

---

## Error Handling & Graceful Fallback

In production, if any `AIProviderError` occurs during content rewriting inside the `RewriteModule`, the engine captures the exception, logs a warning, and gracefully falls back to the original text:

```python
[Rewritten Failed - Fallback]: original content here
```

This prevents external network or rate-limit failures from crashing the periodic background scheduler loops or pipeline runs.
