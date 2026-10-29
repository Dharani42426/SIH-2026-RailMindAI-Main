from config import get_settings
from services.llm_providers import create_llm_router_from_settings
import logging

logging.basicConfig(level=logging.DEBUG)

settings = get_settings()
print("Keys:", settings.NVIDIA_API_KEY)
try:
    router = create_llm_router_from_settings()
    print("Router created successfully")
    resp = router.generate_with_fallback([{"role": "user", "content": "hello"}])
    print("Response:", resp)
except Exception as e:
    import traceback
    traceback.print_exc()
