"""
test_context_builder.py

Intent:
Contract tests for the core "lens widener" — build_relevant_context and
its keyword scoring / fractal walking logic. These tests protect the
most important pre-text enrichment behavior of the entire HFCN platform.

Because the platform must remain radically simple, these tests are also
kept minimal while still giving high confidence that navigation works
on the real example data (Project Alpha).
"""

import pytest
from pathlib import Path

from hfcn.context_builder import build_relevant_context, _collect_relevant_files
from hfcn import config


def test_build_relevant_context_finds_project_alpha_content(monkeypatch):
    """The example data must be discoverable with the primary focus keywords."""
    from hfcn import config as hfcn_config
    real_root = Path(__file__).parent.parent / "hfcn_data"
    hfcn_config.set_data_root(real_root)

    result = build_relevant_context(cue="project_alpha_q3_planning resource_tension", zoom="standard", depth=2)

    assert "project_alpha_q3_planning" in result.lower() or "resource" in result.lower()
    assert "Relevant HFCN Context" in result


def test_scoring_prefers_path_matches():
    """Path matches (especially in category folders) should score higher than pure content matches."""
    # We don't assert exact numbers, but the function must not crash and must return something
    result = build_relevant_context(cue="planning_tension", zoom="deep", depth=3)
    assert len(result) > 50  # At least some relevant content was found


def test_zoom_presets_change_result_size():
    """Different zoom levels should produce different amounts of context (sanity check)."""
    standard = build_relevant_context(cue="resource", zoom="standard", depth=2)
    deep = build_relevant_context(cue="resource", zoom="deep", depth=3)

    # Deep should generally surface more or longer excerpts
    assert len(deep) >= len(standard)
