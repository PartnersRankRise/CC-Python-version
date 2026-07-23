# Architecture Addendum: Multi-Provider LLM Support

**Supplements:** `BUILD_GUIDE.md`, `.cursorrules`, `QUICK_REFERENCE.md`  
**Sources:** gpt-researcher LLM docs, LangChain OpenRouter docs, LangChain Ollama docs  
**Scope:** Adds OpenRouter, LM Studio (self-hosted), and Ollama (self-hosted) as switchable LLM providers — for both the pipeline's `AnthropicProvider` equivalent and for gpt-researcher's internal research engine.

---

## 1. How the Provider System Works

There are two separate LLM integration points in this application:

```
┌─────────────────────────────────────────────────────────┐
│  Integration Point 1: Pipeline LLM (Stages 0–7)        │
│  Used for: onboarding, brief writing, drafting, QA      │
│  Class: LLMProvider (content_pipeline/llm/)             │
│  Currently: AnthropicProvider                           │
│  Adding: OpenRouterProvider, OllamaProvider,            │
│          LMStudioProvider                               │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Integration Point 2: gpt-researcher (Stage 1 only)     │
│  Used for: research gathering, source curation          │
│  Configured via: environment variables only             │
│  gptr reads SMART_LLM, FAST_LLM, STRATEGIC_LLM         │
│  and routes internally through langchain                │
└─────────────────────────────────────────────────────────┘
```

Both points can use different providers simultaneously. Example: Anthropic for pipeline stages + Ollama for gpt-researcher research. Or OpenRouter for everything.

---

## 2. gpt-researcher Provider Configuration

gpt-researcher reads its LLM configuration entirely from environment variables. No code changes required — just set the right env vars. The format is `provider:model-name` for all three LLM tiers.

### OpenRouter (via gpt-researcher)

```bash
# .env
OPENROUTER_API_KEY=sk-or-...
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_API_KEY=dummy_not_used           # required by some gptr internals; any value works

FAST_LLM=openrouter:google/gemini-2.0-flash-lite-001
SMART_LLM=openrouter:anthropic/claude-sonnet-4-5
STRATEGIC_LLM=openrouter:google/gemini-2.5-pro-exp-03-25
OPENROUTER_LIMIT_RPS=1                  # rate limit: 1 request/second

# OpenRouter does not support embeddings — use Google Gemini (free tier)
EMBEDDING=google_genai:models/text-embedding-004
GOOGLE_API_KEY=...                      # required for embedding only
```

Install the required langchain package:
```bash
pip install langchain-openrouter
```

### Ollama (self-hosted, via gpt-researcher)

```bash
# .env — local Ollama
OLLAMA_BASE_URL=http://localhost:11434

FAST_LLM=ollama:llama3.1:8b             # fast; good for sub-queries
SMART_LLM=ollama:llama3.1:70b           # smart; used by SourceCurator
STRATEGIC_LLM=ollama:llama3.1:70b       # planning

EMBEDDING=ollama:nomic-embed-text        # local embedding
EMBEDDING_PROVIDER=ollama
```

Install the required langchain package:
```bash
pip install langchain-ollama
```

### LM Studio (self-hosted, via gpt-researcher)

LM Studio exposes an OpenAI-compatible API. Use the `openai:` prefix with the model name exactly as it appears in LM Studio's loaded model list.

```bash
# .env — LM Studio running locally
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio               # any string; LM Studio ignores it

FAST_LLM=openai:lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF
SMART_LLM=openai:lmstudio-community/Meta-Llama-3.1-70B-Instruct-GGUF
STRATEGIC_LLM=openai:lmstudio-community/Meta-Llama-3.1-70B-Instruct-GGUF

# LM Studio also serves embeddings via the same OpenAI-compatible API
EMBEDDING=custom:nomic-ai/nomic-embed-text-v1.5
```

No additional packages needed — LM Studio uses the standard `openai` client.

---

## 3. Pipeline LLM Provider Architecture

The `LLMProvider` abstraction in `content_pipeline/llm/` needs to be extended to support all four providers. The key design decision: all providers expose the same two methods (`complete`, `complete_with_stream`), so stage services never need to know which provider is active.

### Updated `base_provider.py`

```python
# content_pipeline/llm/base_provider.py
from abc import ABC, abstractmethod
from typing import AsyncIterator
from enum import Enum

class ProviderType(Enum):
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"

class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str, system: str = "", **kwargs) -> str: ...

    @abstractmethod
    async def complete_with_stream(
        self, prompt: str, system: str = "", **kwargs
    ) -> AsyncIterator[str]: ...

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType: ...

    @property
    @abstractmethod  
    def model_name(self) -> str: ...
```

### `OpenRouterProvider`

OpenRouter uses the LangChain `ChatOpenRouter` class. The pipeline wraps it to match the `LLMProvider` interface.

```python
# content_pipeline/llm/openrouter_provider.py
from langchain_openrouter import ChatOpenRouter
from langchain_core.messages import HumanMessage, SystemMessage
from .base_provider import LLMProvider, ProviderType
import os

class OpenRouterProvider(LLMProvider):
    """
    Pipeline LLM provider via OpenRouter.
    OpenRouter gives access to Anthropic, Google, Meta, Mistral, and more
    through a single API key and endpoint.
    
    Recommended model assignments:
      SMART tasks (Stage 3 Writing, Stage 4 Humanization, Stage 6 QA):
        anthropic/claude-sonnet-4-5
      FAST tasks (Stage 5 SEO audits, Stage 2 Brief structure):
        google/gemini-2.0-flash-001
    """

    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 8192):
        self._model = model
        self._client = ChatOpenRouter(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=2,
            openrouter_provider={
                "data_collection": "deny",   # don't let providers train on pipeline content
            },
        )

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OPENROUTER

    @property
    def model_name(self) -> str:
        return self._model

    async def complete(self, prompt: str, system: str = "", **kwargs) -> str:
        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))
        response = await self._client.ainvoke(messages)
        return response.content

    async def complete_with_stream(
        self, prompt: str, system: str = "", **kwargs
    ):
        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))
        async for chunk in self._client.astream(messages):
            if chunk.content:
                yield chunk.content
```

### `OllamaProvider`

```python
# content_pipeline/llm/ollama_provider.py
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from .base_provider import LLMProvider, ProviderType
import os

class OllamaProvider(LLMProvider):
    """
    Pipeline LLM provider via self-hosted Ollama.
    
    Prerequisites:
    - Ollama running: `ollama serve`
    - Model pulled: `ollama pull llama3.1:70b`
    - OLLAMA_BASE_URL set (default: http://localhost:11434)
    
    Best for: local development, privacy-sensitive content,
    cost-free iteration on prompts.
    
    Caveat: Context window and instruction-following quality varies
    significantly by model. The pipeline's quality gates may need
    looser tolerances for some local models.
    """

    def __init__(
        self,
        model: str,
        base_url: str = None,
        temperature: float = 0.7,
        num_ctx: int = 8192,    # context window — increase for larger models
    ):
        self._model = model
        self._client = ChatOllama(
            model=model,
            base_url=base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=temperature,
            num_ctx=num_ctx,
        )

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OLLAMA

    @property
    def model_name(self) -> str:
        return self._model

    async def complete(self, prompt: str, system: str = "", **kwargs) -> str:
        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))
        response = await self._client.ainvoke(messages)
        return response.content

    async def complete_with_stream(self, prompt: str, system: str = "", **kwargs):
        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))
        async for chunk in self._client.astream(messages):
            if chunk.content:
                yield chunk.content
```

### `LMStudioProvider`

LM Studio exposes an OpenAI-compatible API. The pipeline uses the `anthropic` client for Anthropic and the standard `openai` client for LM Studio.

```python
# content_pipeline/llm/lmstudio_provider.py
from openai import AsyncOpenAI
from .base_provider import LLMProvider, ProviderType

class LMStudioProvider(LLMProvider):
    """
    Pipeline LLM provider via self-hosted LM Studio.
    LM Studio serves an OpenAI-compatible REST API at localhost:1234.
    
    Prerequisites:
    - LM Studio running with a model loaded
    - Server started in LM Studio (local server tab)
    - Model name matches exactly what LM Studio reports
    
    Note: LM Studio's model identifier includes the full GGUF path.
    Check the LM Studio UI for the exact model identifier string.
    
    Best for: local development with GUI model management,
    experimenting with quantized models, offline operation.
    """

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:1234/v1",
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ):
        self._model = model
        self._client = AsyncOpenAI(
            base_url=base_url,
            api_key="lm-studio",    # LM Studio ignores this value; any string works
        )
        self._temperature = temperature
        self._max_tokens = max_tokens

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.LM_STUDIO

    @property
    def model_name(self) -> str:
        return self._model

    async def complete(self, prompt: str, system: str = "", **kwargs) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        return response.choices[0].message.content

    async def complete_with_stream(self, prompt: str, system: str = "", **kwargs):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
```

### `LLMProviderFactory`

One factory class that reads configuration and constructs the right provider. Stage services never import individual provider classes directly.

```python
# content_pipeline/llm/provider_factory.py
import os
from .base_provider import LLMProvider, ProviderType
from .anthropic_provider import AnthropicProvider
from .openrouter_provider import OpenRouterProvider
from .ollama_provider import OllamaProvider
from .lmstudio_provider import LMStudioProvider

class LLMProviderFactory:
    """
    Constructs the correct LLMProvider from environment configuration.
    
    LLM_PROVIDER env var controls which provider is used for pipeline stages.
    This is separate from gpt-researcher's SMART_LLM/FAST_LLM env vars,
    which control the research engine only.
    
    Valid values for LLM_PROVIDER:
      anthropic    → AnthropicProvider (default)
      openrouter   → OpenRouterProvider
      ollama       → OllamaProvider
      lm_studio    → LMStudioProvider
    
    Model is set via PIPELINE_LLM_MODEL env var.
    Provider-specific vars (API keys, base URLs) follow each provider's convention.
    """

    @staticmethod
    def create_smart_provider() -> LLMProvider:
        """High-quality provider for complex tasks: writing, humanization, QA."""
        return LLMProviderFactory._create(
            provider_env="LLM_PROVIDER",
            model_env="PIPELINE_SMART_MODEL",
        )

    @staticmethod
    def create_fast_provider() -> LLMProvider:
        """Faster/cheaper provider for structured tasks: brief, SEO, onboarding."""
        return LLMProviderFactory._create(
            provider_env="LLM_PROVIDER",
            model_env="PIPELINE_FAST_MODEL",
        )

    @staticmethod
    def _create(provider_env: str, model_env: str) -> LLMProvider:
        provider_type = os.environ.get(provider_env, "anthropic").lower()
        model = os.environ.get(model_env, "")

        if provider_type == "anthropic":
            return AnthropicProvider(
                model=model or "claude-sonnet-4-6"
            )
        elif provider_type == "openrouter":
            return OpenRouterProvider(
                model=model or "anthropic/claude-sonnet-4-5"
            )
        elif provider_type == "ollama":
            return OllamaProvider(
                model=model or "llama3.1:70b",
                base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
                num_ctx=int(os.environ.get("OLLAMA_NUM_CTX", "8192")),
            )
        elif provider_type == "lm_studio":
            return LMStudioProvider(
                model=model or "lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF",
                base_url=os.environ.get("LM_STUDIO_BASE_URL", "http://localhost:1234/v1"),
            )
        else:
            raise ValueError(
                f"Unknown LLM_PROVIDER: '{provider_type}'. "
                f"Valid values: anthropic, openrouter, ollama, lm_studio"
            )
```

---

## 4. Updated Environment Variables

Replace the `LLM_PROVIDER` section in `.env.example`:

```bash
# ============================================================
# PIPELINE LLM PROVIDER
# Controls which LLM is used for pipeline stages (0-7)
# Separate from gpt-researcher's research engine (below)
# ============================================================

# Options: anthropic | openrouter | ollama | lm_studio
LLM_PROVIDER=anthropic

# Model for complex tasks (writing, humanization, QA)
PIPELINE_SMART_MODEL=claude-sonnet-4-6

# Model for structured tasks (brief, SEO, onboarding)
PIPELINE_FAST_MODEL=claude-haiku-4-5-20251001

# ============================================================
# ANTHROPIC (default pipeline provider)
# ============================================================
ANTHROPIC_API_KEY=sk-ant-...

# ============================================================
# OPENROUTER (alternative pipeline provider + gpt-researcher)
# ============================================================
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_LIMIT_RPS=1

# When LLM_PROVIDER=openrouter, set models like:
# PIPELINE_SMART_MODEL=anthropic/claude-sonnet-4-5
# PIPELINE_FAST_MODEL=google/gemini-2.0-flash-001

# ============================================================
# OLLAMA (self-hosted, alternative pipeline provider + gpt-researcher)
# ============================================================
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_NUM_CTX=8192

# When LLM_PROVIDER=ollama, set models like:
# PIPELINE_SMART_MODEL=llama3.1:70b
# PIPELINE_FAST_MODEL=llama3.1:8b

# ============================================================
# LM STUDIO (self-hosted, alternative pipeline provider)
# ============================================================
LM_STUDIO_BASE_URL=http://localhost:1234/v1

# When LLM_PROVIDER=lm_studio, set models like:
# PIPELINE_SMART_MODEL=lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF

# ============================================================
# GPT-RESEARCHER ENGINE (Stage 1 research gathering only)
# Uses provider:model format — independent of pipeline LLM
# ============================================================
RETRIEVER=tavily
TAVILY_API_KEY=tvly-...

# --- Option A: Use Anthropic for research engine (default) ---
# FAST_LLM=anthropic:claude-haiku-4-5-20251001
# SMART_LLM=anthropic:claude-sonnet-4-6
# STRATEGIC_LLM=anthropic:claude-sonnet-4-6

# --- Option B: Use OpenRouter for research engine ---
# OPENAI_BASE_URL=https://openrouter.ai/api/v1
# OPENAI_API_KEY=dummy_value
# FAST_LLM=openrouter:google/gemini-2.0-flash-lite-001
# SMART_LLM=openrouter:anthropic/claude-sonnet-4-5
# STRATEGIC_LLM=openrouter:google/gemini-2.5-pro-exp-03-25
# EMBEDDING=google_genai:models/text-embedding-004   # OpenRouter has no embedding support
# GOOGLE_API_KEY=...

# --- Option C: Use Ollama for research engine ---
# FAST_LLM=ollama:llama3.1:8b
# SMART_LLM=ollama:llama3.1:70b
# STRATEGIC_LLM=ollama:llama3.1:70b
# EMBEDDING=ollama:nomic-embed-text
# EMBEDDING_PROVIDER=ollama

# --- Option D: Use LM Studio for research engine ---
# OPENAI_BASE_URL=http://localhost:1234/v1
# OPENAI_API_KEY=lm-studio
# FAST_LLM=openai:lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF
# SMART_LLM=openai:lmstudio-community/Meta-Llama-3.1-70B-Instruct-GGUF
# STRATEGIC_LLM=openai:lmstudio-community/Meta-Llama-3.1-70B-Instruct-GGUF

MAX_SCRAPER_WORKERS=15
MAX_SEARCH_RESULTS_PER_QUERY=5
CURATE_SOURCES=false
```

---

## 5. Updated `pyproject.toml` Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.12"
fastapi = ">=0.111"
uvicorn = {extras = ["standard"], version = ">=0.29"}
supabase = ">=2.4"
anthropic = ">=0.28"
gpt-researcher = ">=0.10"
arq = ">=0.25"
pydantic = ">=2.7"
python-dotenv = ">=1.0"
openai = ">=1.30"                      # Used by LMStudioProvider + gpt-researcher internals

[tool.poetry.extras]
openrouter = ["langchain-openrouter"]
ollama = ["langchain-ollama"]
all-providers = ["langchain-openrouter", "langchain-ollama"]
```

Install extras as needed:
```bash
pip install "content-pipeline[openrouter]"   # adds OpenRouter support
pip install "content-pipeline[ollama]"        # adds Ollama support
pip install "content-pipeline[all-providers]" # adds all
```

Or directly:
```bash
pip install langchain-openrouter   # for OpenRouter
pip install langchain-ollama       # for Ollama
# LM Studio needs no extra packages — uses openai client already installed
```

---

## 6. Provider Capability Matrix

Not all providers are equal for all pipeline tasks. Use this to set expectations:

| Task | Anthropic | OpenRouter | Ollama (70B) | LM Studio (8B) |
|---|---|---|---|---|
| Stage 0 Onboarding (complex extraction) | ✅ Excellent | ✅ Excellent | ⚠️ Good | ⚠️ Variable |
| Stage 2 Brief (structured output) | ✅ Excellent | ✅ Excellent | ⚠️ Good | ❌ Unreliable |
| Stage 3 Writing (voice, style adherence) | ✅ Excellent | ✅ Excellent | ⚠️ Good | ❌ Limited |
| Stage 4 Humanization (nuance) | ✅ Excellent | ✅ Excellent | ⚠️ Variable | ❌ Limited |
| Stage 5 SEO (mechanical audit) | ✅ Excellent | ✅ Excellent | ✅ Good | ⚠️ Good |
| Stage 6 QA (checklist scoring) | ✅ Excellent | ✅ Excellent | ⚠️ Variable | ❌ Unreliable |
| Stage 7 Formatting (deterministic) | ✅ | ✅ | ✅ | ✅ |
| Research (gpt-researcher) | ✅ | ✅ | ⚠️ Slow | ⚠️ Slow |
| Cost per article | $$$  | $-$$$ | Free | Free |
| Privacy | Cloud | Cloud | 🔒 Local | 🔒 Local |

**Recommended configurations by use case:**

- **Production:** `LLM_PROVIDER=anthropic` for pipeline + `SMART_LLM=anthropic:...` for gptr
- **Cost optimization:** `LLM_PROVIDER=openrouter` (route cheap models for fast stages, expensive for smart stages)
- **Development/testing:** `LLM_PROVIDER=ollama` with llama3.1:70b; expect looser quality gate results
- **Offline/air-gapped:** `LLM_PROVIDER=lm_studio` for pipeline + `OPENAI_BASE_URL=localhost` for gptr; quality gates may need tuning

---

## 7. Quality Gate Tolerance for Local Models

Local models (Ollama, LM Studio) may not reliably pass all pipeline quality gates on the first attempt. Add a per-provider tolerance config to the application:

```python
# content_pipeline/config/provider_config.py

PROVIDER_QUALITY_TOLERANCES = {
    "anthropic": {
        "max_validation_retries": 1,        # tight — Anthropic usually passes first try
        "allow_partial_eeat": False,
        "min_insight_words": 100,
        "min_value_statement_words": 50,
    },
    "openrouter": {
        "max_validation_retries": 2,
        "allow_partial_eeat": False,
        "min_insight_words": 80,
        "min_value_statement_words": 40,
    },
    "ollama": {
        "max_validation_retries": 3,        # more retries for local models
        "allow_partial_eeat": True,         # accept partial E-E-A-T signals
        "min_insight_words": 50,            # lower bar
        "min_value_statement_words": 30,
    },
    "lm_studio": {
        "max_validation_retries": 3,
        "allow_partial_eeat": True,
        "min_insight_words": 40,
        "min_value_statement_words": 25,
    },
}
```

The `StageContract.run()` method reads tolerances from `LLMProviderFactory.current_tolerances()` before calling `_validate_output`. This means quality gate thresholds automatically adjust to match the provider being used.

---

## 8. Frontend Provider Selector

Add a provider configuration panel to the application settings UI:

```typescript
// frontend/app/settings/page.tsx

// Provider selector lets the operator switch providers without editing .env
// Settings are stored in Supabase (settings table) and override env vars at runtime

interface ProviderSettings {
  pipeline_provider: "anthropic" | "openrouter" | "ollama" | "lm_studio"
  pipeline_smart_model: string
  pipeline_fast_model: string
  gptr_smart_llm: string
  gptr_fast_llm: string
  gptr_embedding: string
}
```

Add the settings table to the database:

```sql
CREATE TABLE provider_settings (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  -- one row per deployment; singleton pattern
  pipeline_provider     TEXT NOT NULL DEFAULT 'anthropic',
  pipeline_smart_model  TEXT NOT NULL DEFAULT 'claude-sonnet-4-6',
  pipeline_fast_model   TEXT NOT NULL DEFAULT 'claude-haiku-4-5-20251001',
  gptr_smart_llm        TEXT NOT NULL DEFAULT 'anthropic:claude-sonnet-4-6',
  gptr_fast_llm         TEXT NOT NULL DEFAULT 'anthropic:claude-haiku-4-5-20251001',
  gptr_strategic_llm    TEXT NOT NULL DEFAULT 'anthropic:claude-sonnet-4-6',
  gptr_embedding        TEXT NOT NULL DEFAULT 'openai:text-embedding-3-small',
  updated_at            TIMESTAMPTZ DEFAULT NOW()
);
```

The `LLMProviderFactory` reads from this table first; env vars are the fallback. This allows operators to switch providers from the UI without restarting the server.

---

## 9. Updated Phase 1 Step (Addendum to BUILD_GUIDE.md)

**Add to Phase 1, Step 1.5 — LLM Provider:**

After creating `AnthropicProvider`, also create:
- `content_pipeline/llm/openrouter_provider.py` — `OpenRouterProvider`
- `content_pipeline/llm/ollama_provider.py` — `OllamaProvider`  
- `content_pipeline/llm/lmstudio_provider.py` — `LMStudioProvider`
- `content_pipeline/llm/provider_factory.py` — `LLMProviderFactory`

**Updated test for Step 1.5:**

```python
# tests/test_llm.py — add provider switching tests

def test_provider_factory_creates_anthropic_by_default(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    provider = LLMProviderFactory.create_smart_provider()
    assert provider.provider_type == ProviderType.ANTHROPIC

def test_provider_factory_creates_openrouter(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("PIPELINE_SMART_MODEL", "anthropic/claude-sonnet-4-5")
    provider = LLMProviderFactory.create_smart_provider()
    assert provider.provider_type == ProviderType.OPENROUTER
    assert provider.model_name == "anthropic/claude-sonnet-4-5"

def test_provider_factory_creates_ollama(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("PIPELINE_SMART_MODEL", "llama3.1:70b")
    provider = LLMProviderFactory.create_smart_provider()
    assert provider.provider_type == ProviderType.OLLAMA

def test_provider_factory_creates_lm_studio(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "lm_studio")
    provider = LLMProviderFactory.create_fast_provider()
    assert provider.provider_type == ProviderType.LM_STUDIO

@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY"), reason="No OpenRouter key")
async def test_openrouter_complete():
    provider = OpenRouterProvider(model="anthropic/claude-haiku-4-5")
    result = await provider.complete("Say hello in one sentence.")
    assert len(result) > 0

@pytest.mark.integration
@pytest.mark.skipif(not shutil.which("ollama"), reason="Ollama not installed")
async def test_ollama_complete():
    provider = OllamaProvider(model="llama3.1:8b")
    result = await provider.complete("Say hello in one sentence.")
    assert len(result) > 0
```

---

## 10. `.cursorrules` Additions

Add this section to `.cursorrules` after the "Tech Stack" section:

```
## LLM Provider System

The pipeline supports four LLM providers. All four implement the same LLMProvider interface.
Never hard-code a specific provider in stage services — always use LLMProviderFactory.

Provider selection: LLM_PROVIDER env var → "anthropic" | "openrouter" | "ollama" | "lm_studio"
Model selection: PIPELINE_SMART_MODEL and PIPELINE_FAST_MODEL env vars

gpt-researcher uses its OWN provider configuration (SMART_LLM, FAST_LLM, STRATEGIC_LLM env vars).
These are independent of the pipeline's LLM_PROVIDER setting.

When adding new provider code:
- New providers go in content_pipeline/llm/
- All providers implement LLMProvider ABC
- LLMProviderFactory is the only place provider selection logic lives
- Stage services receive an LLMProvider instance; they never know which provider it is

OpenRouter embedding note: OpenRouter does not support embeddings.
When using OpenRouter for gpt-researcher, set EMBEDDING to a different provider
(google_genai:models/text-embedding-004 is free and recommended).

LM Studio note: LM Studio is OpenAI-compatible. Use the openai: prefix in gpt-researcher
env vars, and use LMStudioProvider (which wraps the openai client) for pipeline stages.

Local model quality: Ollama and LM Studio models produce lower-quality output than
cloud models for complex pipeline stages. Quality gate thresholds auto-adjust via
PROVIDER_QUALITY_TOLERANCES. Expect more validation failures and retries with local models.
```

---

## 11. Quick Provider Switch Checklist

When switching providers, verify these before running a stage:

```bash
# Switching to OpenRouter
export LLM_PROVIDER=openrouter
export OPENROUTER_API_KEY=sk-or-...
export PIPELINE_SMART_MODEL=anthropic/claude-sonnet-4-5
export PIPELINE_FAST_MODEL=google/gemini-2.0-flash-001
# For gpt-researcher:
export OPENAI_BASE_URL=https://openrouter.ai/api/v1
export FAST_LLM=openrouter:google/gemini-2.0-flash-lite-001
export SMART_LLM=openrouter:anthropic/claude-sonnet-4-5
export EMBEDDING=google_genai:models/text-embedding-004
export GOOGLE_API_KEY=...
pip install langchain-openrouter  # if not already installed

# Switching to Ollama
export LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://localhost:11434
export PIPELINE_SMART_MODEL=llama3.1:70b
export PIPELINE_FAST_MODEL=llama3.1:8b
# Verify model is pulled:
ollama list  # should show llama3.1:70b
# For gpt-researcher:
export FAST_LLM=ollama:llama3.1:8b
export SMART_LLM=ollama:llama3.1:70b
export EMBEDDING=ollama:nomic-embed-text
pip install langchain-ollama  # if not already installed

# Switching to LM Studio
export LLM_PROVIDER=lm_studio
export LM_STUDIO_BASE_URL=http://localhost:1234/v1
export PIPELINE_SMART_MODEL=<exact model name from LM Studio UI>
# For gpt-researcher:
export OPENAI_BASE_URL=http://localhost:1234/v1
export OPENAI_API_KEY=lm-studio
export FAST_LLM=openai:<model-name>
export SMART_LLM=openai:<model-name>
# No extra packages needed
```

---

*Addendum version 1.0 — July 2026. Read alongside `BUILD_GUIDE.md` and `.cursorrules`. This addendum adds new files to `content_pipeline/llm/` and new environment variables to `.env.example`. No existing files from the main architecture documents are replaced — the `AnthropicProvider` remains the default; the new providers are additive.*
