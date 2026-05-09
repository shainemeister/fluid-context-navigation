"""
index_manager.py

Single source of truth for reading and writing the central index.yaml.

Intent:
- All state changes (focus, keywords, links, etc.) go through this module.
- Guarantees the AI always has a consistent, up-to-date navigation surface.
- Keeps the index small, human-readable, and atomic.
- Supports the "lightweight control panel" principle of HFCN.

This is one of the most critical modules because index.yaml is loaded
in full at the start of every session.
"""
from pathlib import Path
import yaml

from .config import DATA_ROOT

INDEX_PATH: Path = DATA_ROOT / "index.yaml"


def load_index() -> dict:
    """Load the full index.yaml into memory."""
    if not INDEX_PATH.exists():
        return {"index": {}}
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"index": {}}


def save_index(index_data: dict) -> None:
    """Save the index back to disk (atomic write recommended in production)."""
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        yaml.dump(index_data, f, sort_keys=False, allow_unicode=True, default_flow_style=False)


def update_index(changes: dict) -> dict:
    """
    Apply lightweight changes to the index (e.g. new focus or keywords).

    This is the operation the AI calls via TOOL_CALL when it wants to
    persist new state. Keeps token usage extremely low.
    """
    index = load_index()
    # Merge changes into current_state or navigation_index
    current = index.setdefault("index", {}).setdefault("current_state", {})
    current.update(changes.get("current_state", {}))

    # Example: also support adding new navigation entries if needed
    save_index(index)
    return index