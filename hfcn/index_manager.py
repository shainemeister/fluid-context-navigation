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

from . import config


def _get_index_path() -> Path:
    """Dynamic so set_data_root() is respected at runtime (no reload)."""
    return config.DATA_ROOT / "index.yaml"


def load_index() -> dict:
    """Load the full index.yaml into memory."""
    index_path = _get_index_path()
    if not index_path.exists():
        return {"index": {}}
    with open(index_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"index": {}}


def save_index(index_data: dict) -> None:
    """Save the index back to disk (atomic write recommended in production)."""
    index_path = _get_index_path()
    with open(index_path, "w", encoding="utf-8") as f:
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

    # Cap associative_links (populated by cross_reference + update_index) to prevent bloat
    # Intent: small hard cap (50) keeps index.yaml tiny forever, per HFCN lightweight principle.
    links = index.setdefault("index", {}).setdefault("associative_links", [])
    if len(links) > 50:
        del links[:-50]

    # Example: also support adding new navigation entries if needed
    save_index(index)
    return index