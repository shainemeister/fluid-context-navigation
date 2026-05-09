"""
context_builder.py

The heart of Fractal Navigation / "lens widening".

Intent:
This module implements the core HFCN behavior:
"Keyword-first entry, then widen the lens associatively across
the three self-similar categories."

It is called during the **pre-text** phase to automatically enrich
the model’s context with relevant excerpts before every response.

Design goals:
- Extremely low overhead (no embeddings, pure Python + string matching)
- Human-inspectable and debuggable
- Self-similar: works the same at top level or deep in a category
- Returns compact, high-signal excerpts ready for prompt injection
"""
from pathlib import Path
from typing import List, Dict, Any

import yaml

from .config import DATA_ROOT


def build_relevant_context(
    cue: str = "",
    zoom: str = "standard",
    depth: int = 2,
    max_files: int = None
) -> str:
    """
    Build compact, high-signal context from the fractal data structure.

    This is the main pre-text enrichment function.
    It walks the three categories and scores files based on keyword
    matches in both the file path and content.
    """
    if not cue:
        cue = _get_current_focus_keywords()

    keywords = [k.strip().lower() for k in cue.lower().split() if len(k.strip()) > 2]

    # Simple zoom presets (tunable)
    zoom_settings = {
        "standard": {"max_files": 6, "include_content_chars": 800},
        "deep":     {"max_files": 12, "include_content_chars": 1200},
        "wide":     {"max_files": 8, "include_content_chars": 600},
    }
    settings = zoom_settings.get(zoom, zoom_settings["standard"])
    max_files = max_files or settings["max_files"]
    content_chars = settings["include_content_chars"]

    relevant: List[Dict[str, Any]] = []
    categories = ["temporal_memory", "categorical_frame", "associative_nexus"]

    for category in categories:
        cat_path = DATA_ROOT / category
        if cat_path.exists():
            _collect_relevant_files(cat_path, keywords, relevant, max_depth=depth)

    relevant.sort(key=lambda x: x["score"], reverse=True)
    relevant = relevant[:max_files]

    if not relevant:
        return f"No highly relevant context found for cue: '{cue}'."

    lines = [f"## Relevant HFCN Context (cue: {cue}, zoom: {zoom})\n"]
    for item in relevant:
        lines.append(f"**Source:** {item['path']}")
        if item.get("excerpt"):
            lines.append(f"**Excerpt:** {item['excerpt'][:content_chars]}...")
        lines.append("")
    return "\n".join(lines).strip()


def _collect_relevant_files(
    base_path: Path,
    keywords: List[str],
    results: List[Dict],
    max_depth: int = 2,
    current_depth: int = 0
):
    """Recursive directory walker with simple relevance scoring."""
    if current_depth > max_depth:
        return

    for item in base_path.iterdir():
        if item.is_dir():
            _collect_relevant_files(item, keywords, results, max_depth, current_depth + 1)
            continue

        if item.suffix.lower() not in {".md", ".txt", ".yaml", ".yml"}:
            continue

        score = 0
        path_str = str(item.relative_to(DATA_ROOT)).lower()

        for kw in keywords:
            if kw in path_str:
                score += 3

        try:
            content = item.read_text(encoding="utf-8", errors="ignore")[:2000].lower()
            for kw in keywords:
                if kw in content:
                    score += 2
        except Exception:
            pass

        if score > 0:
            excerpt = content[:600].strip().replace("\n", " ") if 'content' in locals() else ""
            results.append({
                "path": str(item.relative_to(DATA_ROOT)),
                "score": score,
                "excerpt": excerpt
            })


def _get_current_focus_keywords() -> str:
    """Fallback: pull active keywords from current index state."""
    try:
        from .index_manager import load_index
        idx = load_index()
        state = idx.get("index", {}).get("current_state", {})
        kws = state.get("active_keywords", [])
        focus = state.get("focus", "")
        return " ".join(kws + [focus]) if kws or focus else "general context"
    except Exception:
        return "general context"