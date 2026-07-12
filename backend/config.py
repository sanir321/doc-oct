import os
# ponytail: no hardcoded secret — require env var (Railway sets it)
OPENCODE_ZEN_API_KEY = os.environ.get("OPENCODE_ZEN_API_KEY", "")
OPENCODE_ZEN_BASE_URL = "https://opencode.ai/zen/v1"
LLM_MODEL = "nemotron-3-ultra-free"
MAX_FILE_SIZE = 10 * 1024 * 1024
UPLOAD_DIR = "uploads"
