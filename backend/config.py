import os
import sys

OPENCODE_ZEN_API_KEY = os.environ.get("OPENCODE_ZEN_API_KEY", "")
OPENCODE_ZEN_BASE_URL = os.environ.get("OPENCODE_ZEN_BASE_URL", "https://opencode.ai/zen/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "nemotron-3-ultra-free")
MAX_FILE_SIZE = 10 * 1024 * 1024

if not OPENCODE_ZEN_API_KEY:
    print("WARNING: OPENCODE_ZEN_API_KEY is not set. The app will fail when calling the LLM.", file=sys.stderr)
