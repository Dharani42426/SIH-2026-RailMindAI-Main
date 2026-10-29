import re

with open('services/nlp_processor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1) Replace __init__ method body
old_init = '''    def __init__(self):
        """
        Initialize NLPProcessor with configuration from settings.

        Reads NLP_PROVIDER and Ollama settings from the app config.
        Safe to call with no arguments — backward compatible with existing code
        that does NLPProcessor().
        """
        try:
            from config import get_settings
            settings = get_settings()
            self._nlp_provider = settings.NLP_PROVIDER.lower()
            self._ollama_base_url = settings.OLLAMA_BASE_URL.rstrip("/")
            self._ollama_model = settings.OLLAMA_MODEL
            self._ollama_timeout = settings.OLLAMA_TIMEOUT_SECONDS
        except Exception:
            # If config is unavailable (e.g. in isolated unit tests),
            # default to pattern-only mode
            self._nlp_provider = "pattern"
            self._ollama_base_url = "http://127.0.0.1:11434"
            self._ollama_model = "qwen2.5:32b"
            self._ollama_timeout = 30

        self._logger = logging.getLogger("railmind.nlp")'''

new_init = '''    def __init__(self):
        """
        Initialize NLPProcessor with configuration from settings.

        Reads NLP_PROVIDER, NVIDIA, and Ollama settings from the app config.
        Creates the LLMRouter for primary/secondary failover.
        Safe to call with no arguments.
        """
        try:
            from config import get_settings
            settings = get_settings()
            self._nlp_provider = settings.NLP_PROVIDER.lower()
            self._ollama_base_url = settings.OLLAMA_BASE_URL.rstrip("/")
            self._ollama_model = settings.OLLAMA_MODEL
            self._ollama_timeout = settings.OLLAMA_TIMEOUT_SECONDS
        except Exception:
            self._nlp_provider = "pattern"
            self._ollama_base_url = "http://10.10.50.250:11434"
            self._ollama_model = "qwen3:235b"
            self._ollama_timeout = 120

        self._logger = logging.getLogger("railmind.nlp")

        # Initialize LLM Router for nvidia/ollama providers
        self._llm_router = None
        if self._nlp_provider in ("nvidia", "ollama"):
            try:
                from services.llm_providers import create_llm_router_from_settings
                self._llm_router = create_llm_router_from_settings()
            except Exception as e:
                self._logger.warning("LLM Router init failed, will use regex-only: %s", e)'''

content = content.replace(old_init, new_init)

# 2) Replace process_command method
old_process = '''    def process_command(self, command: str) -> dict:
        """
        Process a natural language command and return structured result.

        When NLP_PROVIDER is "ollama":
          1. Call Qwen3-235B via Ollama for intent + entity detection
          2. Run regex extraction in parallel
          3. Merge results (regex wins for deterministic matches)
          4. Falls back to regex-only on any Ollama failure

        When NLP_PROVIDER is "pattern" (default):
          Uses regex-only detection (original behavior)

        Returns:
        {
            "original_command": str,
            "intent": str,
            "entities": {"section": str, "department": str, ...},
            "api_action": str,
            "response_text": str,
        }
        """
        command_lower = command.lower().strip()

        if self._nlp_provider == "ollama":
            try:
                intent, llm_entities = self._detect_intent_with_ollama(command)
                regex_entities = self._extract_entities(command_lower)
                entities = self._merge_entities(regex_entities, llm_entities)
            except Exception as e:
                self._logger.warning(
                    "Ollama NLP failed, falling back to regex: %s", e
                )
                intent = self._detect_intent(command_lower)
                entities = self._extract_entities(command_lower)
        else:
            intent = self._detect_intent(command_lower)
            entities = self._extract_entities(command_lower)

        # Step 3: Map to API action
        api_action = self._map_to_api(intent, entities)

        # Step 4: Generate response
        response_text = self._generate_response(intent, entities)

        return {
            "original_command": command,
            "intent": intent,
            "entities": entities,
            "api_action": api_action,
            "response_text": response_text,
        }'''

new_process = '''    def process_command(self, command: str) -> dict:
        """
        Process a natural language command and return structured result.

        When NLP_PROVIDER is "nvidia":
          1. Call Nemotron via NVIDIA API (primary), Qwen via Ollama (fallback)
          2. Run regex extraction in parallel
          3. Merge results (regex wins for deterministic matches)
          4. Falls back to regex-only on any LLM failure

        When NLP_PROVIDER is "ollama":
          Uses Qwen via LLMRouter (same flow, Ollama as primary)

        When NLP_PROVIDER is "pattern" (default):
          Uses regex-only detection (original behavior)
        """
        command_lower = command.lower().strip()
        ai_engine = None

        if self._nlp_provider in ("nvidia", "ollama") and self._llm_router:
            try:
                intent, llm_entities, ai_engine = self._detect_intent_with_llm_router(command)
                regex_entities = self._extract_entities(command_lower)
                entities = self._merge_entities(regex_entities, llm_entities)
            except Exception as e:
                self._logger.warning(
                    "LLM NLP failed, falling back to regex: %s", e
                )
                intent = self._detect_intent(command_lower)
                entities = self._extract_entities(command_lower)
        else:
            intent = self._detect_intent(command_lower)
            entities = self._extract_entities(command_lower)

        api_action = self._map_to_api(intent, entities)
        response_text = self._generate_response(intent, entities)

        result = {
            "original_command": command,
            "intent": intent,
            "entities": entities,
            "api_action": api_action,
            "response_text": response_text,
        }
        if ai_engine:
            result["ai_engine"] = ai_engine
        return result'''

content = content.replace(old_process, new_process)

# 3) Add _detect_intent_with_llm_router method before _build_ollama_system_prompt
new_method = '''    def _detect_intent_with_llm_router(self, command: str) -> tuple:
        """
        Detect intent and extract entities using the LLM Router.

        Routes through NVIDIA Nemotron (primary) -> Qwen/Ollama (secondary).
        Returns: (intent, entities, ai_engine_string)
        Raises Exception on failure (caller falls back to regex).
        """
        system_prompt = self._build_ollama_system_prompt()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": command},
        ]

        response = self._llm_router.generate(messages, temperature=0.1)

        raw_content = response.content
        if not raw_content:
            raise ValueError("Empty response content from LLM")

        parsed = self._parse_llm_json(raw_content)
        intent = self._validate_intent(parsed)
        entities = self._validate_llm_entities(parsed)

        # Build ai_engine display string
        model_display = response.model
        if response.provider == 'nvidia':
            model_display = 'Nemotron 3 Ultra 550B'
        elif response.provider == 'ollama':
            model_display = 'Qwen3-235B'

        ai_engine = model_display
        if response.fallback_used:
            ai_engine += ' (fallback)'

        self._logger.info(
            "LLM NLP result: provider=%s model=%s fallback=%s latency=%.0fms",
            response.provider, response.model, response.fallback_used, response.latency_ms
        )

        return intent, entities, ai_engine

'''

# Insert before _build_ollama_system_prompt
content = content.replace(
    '    def _build_ollama_system_prompt(self)',
    new_method + '    def _build_ollama_system_prompt(self)'
)

with open('services/nlp_processor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK - nlp_processor.py updated successfully')
