import os

env_content = """# ⚡⚡⚡ RailMind AI — Environment Variables ⚡⚡⚡

# 🚀 App Settings 🚀
APP_NAME=RailMind AI
DEBUG=True

# 🚀 Database 🚀
DATABASE_URL=sqlite:///./railmind.db

# 🚀 Redis (optional for local dev) 🚀
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=False

# 🚀 AI Settings 🚀
OPTIMIZER_MAX_SOLVE_TIME_SECONDS=5
MAX_BLOCKS_PER_SECTION_PER_DAY=2
MIN_GAP_BETWEEN_BLOCKS_MINUTES=30

# 🚀 NLP Settings 🚀
NLP_PROVIDER=nvidia

NVIDIA_API_KEY=
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=nvidia/nemotron-3-ultra-550b-a55b
NVIDIA_TIMEOUT_SECONDS=60

OLLAMA_BASE_URL=http://10.10.50.250:11434
OLLAMA_MODEL=qwen3:235b
OLLAMA_TIMEOUT_SECONDS=120
OLLAMA_FALLBACK_ENABLED=True
"""

with open('.env', 'w', encoding='utf-8') as f:
    f.write(env_content)

print(".env file restored successfully")
