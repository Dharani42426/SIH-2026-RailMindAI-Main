import re

with open('services/llm_providers.py', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(r'class NvidiaProvider\(LLMProvider\):.*?(?=class OllamaProvider)', re.DOTALL)

new_code = """class NvidiaProvider(LLMProvider):
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
                processed.append({"role": "system", "content": "detailed thinking off\\n\\n" + msg["content"]})
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

# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
"""

if pattern.search(content):
    content = pattern.sub(new_code, content)
    with open('services/llm_providers.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replaced successfully")
else:
    print("Old code not found! Check for exact match.")
