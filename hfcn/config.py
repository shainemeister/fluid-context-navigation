"""
config.py

Central configuration for the HFCN reference implementation.

Intent:
Keep all tunable values in one place so the system is easy to
adapt for different models, data locations, or deployment styles
(local vs API).

This supports the core philosophy of minimal overhead and high readability.
"""
from pathlib import Path

# Root directory for all HFCN data (index.yaml + three categories)
DATA_ROOT: Path = Path(__file__).parent.parent / "hfcn_data"

# Default Ollama model to use
# Works well with local models (llama3.2, qwen2.5, phi4, etc.)
# Can be changed to any OpenAI-compatible endpoint later
DEFAULT_MODEL: str = "qwen2.5:7b"

# Whether to automatically log chat turns into temporal_memory shards
AUTO_LOG_CHAT: bool = True