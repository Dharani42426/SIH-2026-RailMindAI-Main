import re

with open('services/nlp_processor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace __init__ using regex to handle the weird character
init_pattern = re.compile(
    r'    def __init__\(self\):.*?self\._logger = logging\.getLogger\("railmind\.nlp"\)', 
    re.DOTALL
)

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

content = init_pattern.sub(new_init, content)

with open('services/nlp_processor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("init replaced successfully")
