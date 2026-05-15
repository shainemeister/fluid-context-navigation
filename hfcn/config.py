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


def set_data_root(path: Path | str) -> None:
    """
    Set a custom workspace root at runtime (called by CLI --data).

    Intent:
    Provides a clean, reload-free way for `hfcn chat --data ./foo` to switch
    the active HFCN data directory. Key modules must use qualified
    `config.DATA_ROOT` (or re-import inside functions) so they see updates
    without importlib.reload hacks. Keeps --data support tiny and aligned
    with radical simplicity.
    """
    global DATA_ROOT
    DATA_ROOT = Path(path).resolve()
