"""
operations.py

Minimal implementations of the five core HFCN operations.

Intent:
These are intentionally lightweight so even smaller local models
can reliably drive them. Each function returns a clean string
that gets fed back into the conversation during the post-text phase.

The model never has to implement the logic itself — it only decides
*when* and *how* to call these high-level operations.

This separation is key to keeping model thinking overhead low
while still giving the system powerful navigational capabilities.
"""
from typing import Dict, Any

from .index_manager import load_index, save_index, update_index

from .context_builder import build_relevant_context


def navigate(cue: str, zoom: str = "standard", depth: int = 2) -> str:
    """
    Move focus and return freshly built relevant context.

    This is the primary way the AI "navigates" the fractal space.
    It updates current_state and then calls the context builder.
    """
    idx = load_index()
    state = idx.setdefault("index", {}).setdefault("current_state", {})
    state["focus"] = cue
    state["current_zoom"] = zoom

    # Simple keyword extraction from cue
    import re
    new_kws = [w.strip() for w in re.findall(r'\b\w{3,}\b', cue.lower())
               if w not in state.get("active_keywords", [])]
    state["active_keywords"] = (state.get("active_keywords", []) + new_kws)[:6]

    save_index(idx)

    context = build_relevant_context(cue=cue, zoom=zoom, depth=depth)
    return f"Navigated to '{cue}' (zoom={zoom}).\n\n{context}"


def expand_fractal(cue: str, max_branches: int = 5) -> str:
    """Perform deeper associative + fractal expansion from a cue."""
    context = build_relevant_context(cue=cue, zoom="deep", depth=3, max_files=max_branches)
    return f"Fractal expansion around '{cue}':\n\n{context}"


def holographic_simulate(slice_id: str, scenario: str) -> str:
    """
    Prepare a vivid, interactive simulation on a specific context slice.

    The actual simulation happens when the model responds to this
    enriched input. This operation just loads the slice cleanly.
    """
    from pathlib import Path
    from .config import DATA_ROOT

    root = DATA_ROOT.resolve()

    # Direct candidate (supports full relative paths like "categorical_frame/goals/...")
    candidate = (DATA_ROOT / slice_id).resolve()
    if candidate.is_relative_to(root) and candidate.exists():
        slice_path = candidate
    else:
        # Safe rglob fallback: only by basename, never traverse out
        name = Path(slice_id).name
        if not name or name in {".", ".."}:
            return f"Slice '{slice_id}' not found."
        matches = [m for m in DATA_ROOT.rglob(name) if m.resolve().is_relative_to(root)]
        if matches:
            slice_path = matches[0]
        else:
            return f"Slice '{slice_id}' not found."

    try:
        content = slice_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return f"Error reading slice: {e}"

    return (
        f"## Holographic Simulation Request\n"
        f"**Slice:** {slice_id}\n"
        f"**Scenario:** {scenario}\n\n"
        f"**Slice Content:**\n{content[:2500]}\n\n"
        f"---\nNow simulate vividly and interactively as per HFCN guidance."
    )


def cross_reference(source: str, target: str) -> str:
    """Create or follow a relational link between two slices."""
    idx = load_index()
    links = idx.setdefault("index", {}).setdefault("associative_links", [])
    links.append({"source": source, "target": target})
    if len(links) > 50:
        del links[:-50]  # small cap to prevent index bloat
    save_index(idx)

    return (
        f"Cross-reference created between '{source}' and '{target}'.\n"
        f"Relevant context:\n"
        f"{build_relevant_context(cue=source, zoom='standard', depth=1)}\n"
        f"{build_relevant_context(cue=target, zoom='standard', depth=1)}"
    )


def update_index_op(changes: Dict[str, Any]) -> str:
    """Wrapper for the update_index operation (called via TOOL_CALL)."""
    new_index = update_index(changes)
    return f"Index updated. New focus: {new_index.get('index', {}).get('current_state', {}).get('focus', 'unknown')}"