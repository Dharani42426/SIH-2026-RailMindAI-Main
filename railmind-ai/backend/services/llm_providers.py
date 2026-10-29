# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RailMind AI — LLM Provider Abstraction
# Primary: NVIDIA Nemotron 3 Ultra 550B via OpenAI-compatible API
# Secondary: Qwen3-235B via Ollama on College DGX
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import requests

logger = logging.getLogger("railmind.llm")


@dataclass
class LLMResponse:
    provider: str
    model: str
    content: str
    fallback_used: bool
    latency_ms: float


class LLMProviderError(Exception):
    def __init__(self, message: str, *, is_config_error: bool = False):
        super().__init__(message)
        self.is_config_error = is_config_error


class LLMTransientError(LLMProviderError):
    def __init__(self, message: str):
        super().__init__(message, is_config_error=False)


class LLMConfigError(LLMProviderError):
    def __init__(self, message: str):
        super().__init__(message, is_config_error=True)


class LLMProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...
    @property
    @abstractmethod
    def model_name(self) -> str: ...
    @abstractmethod
    def generate(self, messages: list[dict], **kwargs) -> LLMResponse: ...


class NvidiaProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str = "https://integrate.api.nvidia.com/v1",
                 model: str = "nvidia/nemotron-3-ultra-550b-a55b", timeout_seconds: int = 60):
        if not api_key:
            raise LLMConfigError("NVIDIA_API_KEY is not set. Get a free key at https://build.nvidia.com/")
        
        self._model = model
        self._timeout = timeout_seconds
        
        # Support comma-separated keys for round-robin
        keys = [k.strip() for k in api_key.split(",") if k.strip()]
        if not keys:
            raise LLMConfigError("NVIDIA_API_KEY is empty or invalid.")

        from openai import OpenAI
        self._clients = [
            OpenAI(base_url=base_url, api_key=k, timeout=float(timeout_seconds))
            for k in keys
        ]
        self._current_idx = 0
        import logging
        logger = logging.getLogger("railmind.llm")
        logger.info("[LLM] NvidiaProvider initialized with %d keys for round-robin. Model=%s", len(self._clients), model)

    @property
    def provider_name(self) -> str: return "nvidia"
    @property
    def model_name(self) -> str: return self._model

    def generate(self, messages: list[dict], **kwargs) -> LLMResponse:
        import time
        import logging
        logger = logging.getLogger("railmind.llm")
        start = time.perf_counter()
        
        # Round-robin selection
        client = self._clients[self._current_idx]
        key_idx = self._current_idx
        self._current_idx = (self._current_idx + 1) % len(self._clients)
        
        try:
            processed = self._prepare_messages(messages)
            completion = client.chat.completions.create(
                model=self._model, messages=processed,
                temperature=kwargs.get("temperature", 0.1),
                max_tokens=kwargs.get("max_tokens", 1024),
            )
            content = completion.choices[0].message.content or ""
            latency = (time.perf_counter() - start) * 1000
            logger.info("[LLM] Provider=NVIDIA Model=%s latency_ms=%.0f (key_idx=%d)", self._model, latency, key_idx)
            return LLMResponse(provider="nvidia", model=self._model, content=content,
                               fallback_used=False, latency_ms=latency)
        except LLMProviderError:
            raise
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            self._classify_and_raise(e, latency)

    def _prepare_messages(self, messages: list[dict]) -> list[dict]:
        processed = []
        system_found = False
        for msg in messages:
            if msg.get("role") == "system" and not system_found:
                system_found = True
                processed.append({"role": "system", "content": "detailed thinking off\n\n" + msg["content"]})
            else:
                processed.append(msg)
        if not system_found:
            processed.insert(0, {"role": "system", "content": "detailed thinking off"})
        return processed

    def _classify_and_raise(self, error: Exception, latency_ms: float):
        import logging
        logger = logging.getLogger("railmind.llm")
        from openai import AuthenticationError, RateLimitError, APIStatusError, APITimeoutError, APIConnectionError
        if isinstance(error, AuthenticationError):
            logger.error("[LLM] NVIDIA auth failed (401/403) — check NVIDIA_API_KEY. latency_ms=%.0f", latency_ms)
            raise LLMConfigError("NVIDIA authentication failed. Check NVIDIA_API_KEY.") from error
        if isinstance(error, APITimeoutError):
            logger.warning("[LLM] NVIDIA request timed out after %.0fms", latency_ms)
            raise LLMTransientError(f"NVIDIA request timed out ({latency_ms:.0f}ms)") from error
        if isinstance(error, APIConnectionError):
            logger.warning("[LLM] NVIDIA connection failed. latency_ms=%.0f", latency_ms)
            raise LLMTransientError("NVIDIA connection failed") from error
        if isinstance(error, RateLimitError):
            logger.warning("[LLM] NVIDIA rate limited (429). latency_ms=%.0f", latency_ms)
            raise LLMTransientError("NVIDIA rate limited (429)") from error
        if isinstance(error, APIStatusError):
            status = getattr(error, "status_code", None)
            logger.warning("[LLM] NVIDIA API error (%s). latency_ms=%.0f", status, latency_ms)
            raise LLMTransientError(f"NVIDIA API error ({status})") from error
        logger.warning("[LLM] NVIDIA unexpected error: %s latency_ms=%.0f", type(error).__name__, latency_ms)
        raise LLMTransientError(f"NVIDIA unexpected error: {type(error).__name__}") from error

# ─────────────────────────────────────────────────────────────────
class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://10.10.50.250:11434",
                 model: str = "qwen3:235b", timeout_seconds: int = 120):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout_seconds
        logger.info("[LLM] OllamaProvider initialized Model=%s BaseURL=%s Timeout=%ds", model, base_url, timeout_seconds)

    @property
    def provider_name(self) -> str: return "ollama"
    @property
    def model_name(self) -> str: return self._model

    def generate(self, messages: list[dict], **kwargs) -> LLMResponse:
        start = time.perf_counter()
        payload = {"model": self._model, "messages": messages, "stream": False,
                   "options": {"temperature": kwargs.get("temperature", 0.1)}, "think": False}
        url = f"{self._base_url}/api/chat"
        try:
            response = requests.post(url, json=payload, timeout=self._timeout)
            response.raise_for_status()
            content = response.json().get("message", {}).get("content", "")
            if not content:
                raise LLMTransientError("Empty response content from Ollama")
            latency = (time.perf_counter() - start) * 1000
            logger.info("[LLM] Provider=Ollama Model=%s latency_ms=%.0f", self._model, latency)
            return LLMResponse(provider="ollama", model=self._model, content=content,
                               fallback_used=False, latency_ms=latency)
        except LLMProviderError:
            raise
        except requests.exceptions.Timeout:
            latency = (time.perf_counter() - start) * 1000
            logger.warning("[LLM] Ollama timed out after %.0fms", latency)
            raise LLMTransientError(f"Ollama request timed out ({latency:.0f}ms)")
        except requests.exceptions.ConnectionError:
            latency = (time.perf_counter() - start) * 1000
            logger.warning("[LLM] Ollama connection failed (DGX unreachable?). latency_ms=%.0f", latency)
            raise LLMTransientError("Ollama connection failed (DGX unreachable)")
        except requests.exceptions.HTTPError as e:
            latency = (time.perf_counter() - start) * 1000
            status = e.response.status_code if e.response is not None else "unknown"
            logger.warning("[LLM] Ollama HTTP error (%s). latency_ms=%.0f", status, latency)
            raise LLMTransientError(f"Ollama HTTP error ({status})") from e
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            logger.warning("[LLM] Ollama unexpected error: %s latency_ms=%.0f", type(e).__name__, latency)
            raise LLMTransientError(f"Ollama unexpected error: {type(e).__name__}") from e


class LLMRouter:
    def __init__(self, primary: Optional[LLMProvider] = None, secondary: Optional[LLMProvider] = None,
                 fallback_enabled: bool = True, force_primary_failure: bool = False):
        self._primary = primary
        self._secondary = secondary
        self._fallback_enabled = fallback_enabled
        self._force_primary_failure = force_primary_failure
        providers = []
        if primary: providers.append(f"PRIMARY={primary.provider_name}/{primary.model_name}")
        if secondary: providers.append(f"SECONDARY={secondary.provider_name}/{secondary.model_name}")
        logger.info("[LLM] LLMRouter initialized — %s fallback=%s",
                    " | ".join(providers) if providers else "NO PROVIDERS",
                    "enabled" if fallback_enabled else "disabled")

    @property
    def primary(self) -> Optional[LLMProvider]: return self._primary
    @property
    def secondary(self) -> Optional[LLMProvider]: return self._secondary

    def generate(self, messages: list[dict], **kwargs) -> LLMResponse:
        primary_error = None
        if self._primary and not self._force_primary_failure:
            try:
                logger.info("[LLM] Routing to PRIMARY: %s", self._primary.provider_name)
                response = self._primary.generate(messages, **kwargs)
                logger.info("[LLM] PRIMARY request succeeded")
                return response
            except LLMProviderError as e:
                primary_error = e
                logger.warning("[LLM] PRIMARY failed: %s", e)
        elif self._force_primary_failure:
            logger.warning("[LLM] PRIMARY failure FORCED (test mode)")
            primary_error = LLMTransientError("Forced primary failure (test mode)")

        if self._secondary and self._fallback_enabled:
            try:
                logger.info("[LLM] Activating fallback — %s/%s", self._secondary.provider_name, self._secondary.model_name)
                response = self._secondary.generate(messages, **kwargs)
                response.fallback_used = True
                logger.info("[LLM] Fallback succeeded — latency_ms=%.0f", response.latency_ms)
                return response
            except LLMProviderError as e:
                logger.error("[LLM] SECONDARY also failed: %s", e)
                raise LLMProviderError(f"All LLM providers failed. Primary: {primary_error}. Secondary: {e}") from e

        if primary_error:
            raise primary_error
        raise LLMProviderError("No LLM providers configured")


def create_llm_router_from_settings() -> LLMRouter:
    from config import get_settings
    settings = get_settings()
    primary = None
    secondary = None
    nlp_provider = settings.NLP_PROVIDER.lower()

    if nlp_provider == "nvidia":
        try:
            primary = NvidiaProvider(api_key=settings.NVIDIA_API_KEY, base_url=settings.NVIDIA_BASE_URL,
                                    model=settings.NVIDIA_MODEL, timeout_seconds=settings.NVIDIA_TIMEOUT_SECONDS)
        except LLMConfigError as e:
            logger.warning("[LLM] NVIDIA not available: %s — will use Ollama if configured", e)

    if nlp_provider in ("nvidia", "ollama"):
        secondary = OllamaProvider(base_url=settings.OLLAMA_BASE_URL, model=settings.OLLAMA_MODEL,
                                   timeout_seconds=settings.OLLAMA_TIMEOUT_SECONDS)
        if nlp_provider == "nvidia" and primary is None:
            logger.info("[LLM] Promoting Ollama to primary (NVIDIA unavailable)")
            primary = secondary
            secondary = None

    fallback_enabled = getattr(settings, "OLLAMA_FALLBACK_ENABLED", True)
    force_failure = getattr(settings, "LLM_TEST_FORCE_PRIMARY_FAILURE", False)
    return LLMRouter(primary=primary, secondary=secondary, fallback_enabled=fallback_enabled,
                     force_primary_failure=force_failure)
