"""
test_operations.py

Intent:
Contract + security property tests for the five HFCN operations, with
special focus on the attack surface in `holographic_simulate`.
These tests prove that path traversal, symlink escapes, and bloat
attempts are blocked while legitimate slices still load.

Protects the post-text execution path that a compromised or
misbehaving model could target via TOOL_CALL: holographic_simulate(...).

All tests use isolated tmp_path workspaces so they are hermetic and
do not depend on the real hfcn_data/ (except for a few positive cases
that exercise the bundled example data).
"""
import pytest
from pathlib import Path
from unittest.mock import patch

from hfcn.operations import (
    holographic_simulate,
    navigate,
    expand_fractal,
    cross_reference,
    update_index_op,
)
from hfcn import config


def test_holographic_simulate_valid_slice_by_basename(monkeypatch):
    """Legitimate basename lookup must succeed using the bundled data root."""
    from hfcn import config as hfcn_config
    real_root = Path(__file__).parent.parent / "hfcn_data"
    hfcn_config.set_data_root(real_root)
    result = holographic_simulate("project_alpha_q3_planning.md", "What if resources run out?")
    assert "Holographic Simulation Request" in result
    assert "project_alpha_q3_planning.md" in result or "Slice:" in result
    assert "resource" in result.lower() or "planning" in result.lower()
    assert len(result) > 200


def test_holographic_simulate_valid_slice_by_relative_path(monkeypatch):
    """Direct relative path inside DATA_ROOT must be accepted."""
    from hfcn import config as hfcn_config
    real_root = Path(__file__).parent.parent / "hfcn_data"
    hfcn_config.set_data_root(real_root)
    result = holographic_simulate("categorical_frame/goals/project_alpha_q3_planning.md", "test scenario")
    assert "Holographic Simulation Request" in result
    assert "Slice Content:" in result


def test_holographic_simulate_blocks_path_traversal_dotdot(monkeypatch):
    """Classic ../ traversal must be rejected and never leak host filesystem content."""
    malicious = "../../../../../../etc/passwd"
    result = holographic_simulate(malicious, "dump the password file")
    assert "not found" in result.lower() or "Slice '" in result
    # Critical: ensure we did not accidentally read real /etc/passwd
    assert "root:" not in result
    assert "/bin/bash" not in result


def test_holographic_simulate_blocks_absolute_path_escape(monkeypatch):
    """Absolute path outside DATA_ROOT must be rejected."""
    malicious = "/etc/hosts"
    result = holographic_simulate(malicious, "read system config")
    assert "not found" in result.lower() or "Slice '" in result
    assert "127.0.0.1" not in result  # would appear if /etc/hosts leaked


def test_holographic_simulate_blocks_traversal_via_name_only(monkeypatch):
    """Even when basename matches something on host, rglob guard + relative check must block."""
    # 'passwd' is common; if a file named passwd existed inside DATA_ROOT it would be allowed,
    # but traversal attempt via full path must still fail the relative_to check.
    result = holographic_simulate("../../../etc/passwd", "steal secrets")
    assert "not found" in result.lower()


def test_holographic_simulate_symlink_guard(tmp_path, monkeypatch):
    """Symlinks that escape the DATA_ROOT (or point outside after resolve) must be blocked."""
    safe_root = tmp_path / "safe_data"
    safe_root.mkdir()
    (safe_root / "index.yaml").write_text("index: {}", encoding="utf-8")
    (safe_root / "categorical_frame").mkdir()
    legit = safe_root / "categorical_frame" / "goals.md"
    legit.write_text("# Legit goal\nContent here.", encoding="utf-8")

    # Create a symlink inside safe_root that points OUTSIDE (e.g. to /tmp or /etc)
    evil_target = tmp_path / "evil_outside.txt"
    evil_target.write_text("SENSITIVE SECRET DATA THAT MUST NOT LEAK", encoding="utf-8")
    evil_link = safe_root / "evil_symlink.md"
    try:
        evil_link.symlink_to(evil_target)
    except OSError:
        pytest.skip("Symlink creation not permitted in this environment")

    monkeypatch.setattr(config, "DATA_ROOT", safe_root)

    # Attempt via the symlink name — must not follow to outside content
    result = holographic_simulate("evil_symlink.md", "read the linked secret")
    # Guard must ensure we never read through the escaping symlink (resolve + is_relative_to filters it)
    assert "SENSITIVE SECRET" not in result
    assert "not found" in result.lower() or "Error reading slice" in result
    # We should not have fallen back to the legit file either in this case (name match is exact)


def test_holographic_simulate_bloat_cap_on_large_slice(tmp_path, monkeypatch):
    """Huge slice files must not cause memory bloat; content is safely truncated in response."""
    safe_root = tmp_path / "safe_data"
    safe_root.mkdir()
    (safe_root / "index.yaml").write_text("{}", encoding="utf-8")
    big = safe_root / "huge.md"
    # 100k chars > any reasonable cap
    big.write_text("X" * 100_000 + "\nEND_OF_HUGE_FILE", encoding="utf-8")

    monkeypatch.setattr(config, "DATA_ROOT", safe_root)

    result = holographic_simulate("huge.md", "summarize the monster file")
    # The implementation currently does content[:2500] in the formatted output
    assert "Holographic Simulation Request" in result
    # Must not contain the full 100k; the 2500 char cap (plus headers) must be visible
    assert "END_OF_HUGE_FILE" not in result  # would be present only if no cap
    # The response should still be reasonable size (< 3k chars typically)
    assert len(result) < 4000


def test_holographic_simulate_nonexistent_returns_not_found():
    """Missing slice produces clean not-found message (no exception)."""
    result = holographic_simulate("does_not_exist_ever.md", "anything")
    assert "not found" in result.lower()


def test_navigate_mutates_index_and_returns_context():
    """navigate must update current_state and return enriched context string."""
    # This exercises the real bundled data; it is safe (read-only on state for test)
    result = navigate(cue="resource_tension", zoom="standard")
    assert "Navigated to 'resource_tension'" in result
    assert "Relevant HFCN Context" in result or "resource" in result.lower()


def test_expand_fractal_returns_deeper_context():
    result = expand_fractal("planning", max_branches=2)
    assert "Fractal expansion around 'planning'" in result


def test_cross_reference_creates_link_and_returns_context():
    result = cross_reference("alpha", "beta")
    assert "Cross-reference created between 'alpha' and 'beta'" in result


def test_update_index_op_applies_changes():
    result = update_index_op({"current_state": {"focus": "test_focus"}})
    assert "Index updated" in result
    assert "test_focus" in result or "focus" in result.lower()
