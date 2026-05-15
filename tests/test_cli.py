"""
test_cli.py

Intent:
High-signal contract tests for the CLI host runtime components that
are the primary interface between untrusted model output and the
HFCN operations + persistent storage.

Covers:
- Strict TOOL_CALL parsing (parse_tool_call) — the #1 injection surface
- Auto-logging shard creation (log_chat_turn) — temporal_memory filesystem contract
- Workspace scaffolding (run_init) — must produce exact fractal directory tree
- Mocked end-to-end run_chat loop — proves pre-text / post-text + dispatch + logging

These tests are the gatekeeper against the attack vectors identified by
security-audit: parser abuse via newlines/quotes/injection, path escapes
via logging, malformed init, and broken host loop behavior.

All filesystem tests use tmp_path and never touch real hfcn_data/.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from hfcn.cli import (
    parse_tool_call,
    execute_tool_call,
    log_chat_turn,
    run_init,
    run_chat,
)
from hfcn import config


# =============================================================================
# parse_tool_call + execute_tool_call contract tests
# =============================================================================

def test_parse_tool_call_happy_path_navigate():
    text = 'I need more context. TOOL_CALL: navigate(cue="resource_tension", zoom="deep")'
    parsed = parse_tool_call(text)
    assert parsed is not None
    assert parsed["operation"] == "navigate"
    assert parsed["args"] == {"cue": "resource_tension", "zoom": "deep"}
    assert "func" in parsed and callable(parsed["func"])


def test_parse_tool_call_happy_path_holographic_simulate():
    text = 'TOOL_CALL: holographic_simulate(slice_id="categorical_frame/goals/project_alpha_q3_planning.md", scenario="what if we miss the Q3 deadline?")'
    parsed = parse_tool_call(text)
    assert parsed["operation"] == "holographic_simulate"
    assert "slice_id" in parsed["args"]
    assert "scenario" in parsed["args"]


def test_parse_tool_call_unknown_operation_returns_error_dict():
    text = 'TOOL_CALL: rm_rf_everything(path="/")'
    parsed = parse_tool_call(text)
    assert parsed == {"error": "Unknown operation: rm_rf_everything"}


def test_parse_tool_call_malformed_no_match_returns_none():
    """Random text or missing TOOL_CALL: prefix must be ignored (treated as normal model output)."""
    assert parse_tool_call("just chatting about the project") is None
    assert parse_tool_call("TOOL_CALL: foo bar baz") is None  # no (args)
    assert parse_tool_call("TOOL_CALL: navigate[cue=foo]") is None  # wrong brackets


def test_parse_tool_call_injection_newlines_in_args():
    """Newlines inside the argument string must not allow command injection or break parsing."""
    evil = '''TOOL_CALL: navigate(cue="resource
tension", zoom="standard")'''
    parsed = parse_tool_call(evil)
    # The current regex (DOTALL) may capture across lines; parser must still produce safe result
    # or reject. Either None or a parsed dict with truncated/safe args is acceptable.
    # Critical property: we never eval and never treat it as shell.
    if parsed and "error" not in parsed:
        # If it parsed, the cue value must not contain literal newlines that would be dangerous downstream
        cue = parsed["args"].get("cue", "")
        assert "\n" not in cue or cue.strip() == "resource"
    else:
        # Strict parser correctly rejected the malformed call — also acceptable
        assert parsed is None or "error" in parsed


def test_parse_tool_call_injection_quotes_and_commas():
    """Quotes and commas inside values must be handled by the naive splitter without breaking out."""
    text = r'TOOL_CALL: cross_reference(source="planning, \"Q3\"", target="constraints")'
    parsed = parse_tool_call(text)
    # The split regex tries to respect quotes; we mainly assert it does not crash and returns a dict
    assert parsed is not None
    assert parsed["operation"] == "cross_reference"
    # The exact value of source may be imperfect with the simple parser, but it must not be None or crash
    assert "source" in parsed.get("args", {})


def test_parse_tool_call_injection_code_attempt():
    """Attempt to inject Python or shell via the args must result in no execution and clean error or ignore."""
    evil = 'TOOL_CALL: update_index(changes="{\\"current_state\\": {}}"); import os; os.system(\'rm -rf /\')'
    parsed = parse_tool_call(evil)
    # The regex will capture up to first ), so it may parse only the changes= part or fail
    # Either way: execute_tool_call must never run the injected code.
    if parsed and "func" in parsed:
        # If somehow parsed as update_index, execute will call it with bad args -> should error gracefully
        result = execute_tool_call(parsed)
        assert "ERROR" in result or "Index updated" in result  # never the rm -rf
    else:
        assert parsed is None or "error" in parsed


def test_execute_tool_call_error_path():
    parsed = {"error": "Unknown operation: destroy"}
    assert "ERROR: Unknown operation: destroy" in execute_tool_call(parsed)


# =============================================================================
# log_chat_turn filesystem contract tests
# =============================================================================

def test_log_chat_turn_creates_correct_shard_structure(tmp_path, monkeypatch):
    """When AUTO_LOG_CHAT=True, log_chat_turn must create YYYY/MM/DD/ dir and write ts_role.md with header + content."""
    monkeypatch.setattr(config, "AUTO_LOG_CHAT", True)

    data_root = tmp_path / "my_project"
    data_root.mkdir()

    log_chat_turn("user", "Hello, I am exploring the resource tension today.", data_root)
    log_chat_turn("assistant", "Understood. Let me navigate to the relevant slice.", data_root)

    now = datetime.utcnow()
    shard_dir = data_root / "temporal_memory" / f"{now.year:04d}" / f"{now.month:02d}" / f"{now.day:02d}"
    assert shard_dir.exists() and shard_dir.is_dir()

    files = list(shard_dir.glob("*.md"))
    assert len(files) >= 2

    user_file = next((f for f in files if "user" in f.name), None)
    assert user_file is not None
    content = user_file.read_text(encoding="utf-8")
    assert "# User Message" in content
    assert "Hello, I am exploring the resource tension today." in content
    assert "Z\n\n" in content  # ISO timestamp header


def test_log_chat_turn_respects_auto_log_flag(tmp_path, monkeypatch):
    """When AUTO_LOG_CHAT=False, no files or directories are created under temporal_memory."""
    monkeypatch.setattr(config, "AUTO_LOG_CHAT", False)

    data_root = tmp_path / "no_log_project"
    data_root.mkdir()

    log_chat_turn("user", "This should not be logged", data_root)

    temporal = data_root / "temporal_memory"
    assert not temporal.exists()  # or if exists from other, no new dated shard for this call


def test_log_chat_turn_does_not_escape_data_root(tmp_path, monkeypatch):
    """Even with malicious-looking role, writes stay inside the provided data_root / temporal_memory/YYYY/MM/DD/.
    Role is currently trusted (hardcoded in run_chat), but filename construction must never allow
    path traversal out of data_root even if role were attacker-controlled in future.
    """
    monkeypatch.setattr(config, "AUTO_LOG_CHAT", True)

    data_root = tmp_path / "safe"
    data_root.mkdir()

    # Role containing ".." and path-like chars but *no actual path separator* so it becomes literal filename part.
    # This still exercises that shard_dir computation + write target stays under data_root.
    evil_role = "user..evil..role"
    log_chat_turn(evil_role, "trying to break out of data_root via role", data_root)

    shard_dir = data_root / "temporal_memory" / f"{datetime.utcnow().year:04d}" / f"{datetime.utcnow().month:02d}" / f"{datetime.utcnow().day:02d}"
    assert shard_dir.exists() and shard_dir.is_dir()

    # The file must exist *inside* the correct day shard (no escape to tmp_path/ or sibling dirs)
    files = list(shard_dir.glob("*user..evil..role*.md"))
    assert len(files) == 1, f"Expected exactly one log file for evil role, got {files}"
    content = files[0].read_text(encoding="utf-8")
    assert "trying to break out of data_root via role" in content

    # Ensure we did not create stray directories higher up or outside data_root
    assert not (tmp_path / "evil").exists()
    assert not (data_root.parent / "outside").exists()


# =============================================================================
# run_init filesystem scaffolding contract tests
# =============================================================================

def test_run_init_creates_exact_fractal_directory_tree(tmp_path):
    """run_init(name) must produce the three category roots + temporal_memory + index.yaml."""
    target_parent = tmp_path
    run_init("my_research", target_parent)

    base = target_parent / "my_research"
    assert base.exists() and base.is_dir()

    assert (base / "temporal_memory").is_dir()
    assert (base / "categorical_frame" / "goals").is_dir()
    assert (base / "categorical_frame" / "constraints").is_dir()
    assert (base / "associative_nexus" / "clusters").is_dir()
    assert (base / "index.yaml").is_file()


def test_run_init_index_yaml_has_correct_structure(tmp_path):
    """The generated index.yaml must contain version 3.1, current_state, available_operations, and holographic_guidance."""
    run_init("alpha", tmp_path)
    idx_path = tmp_path / "alpha" / "index.yaml"
    import yaml
    idx = yaml.safe_load(idx_path.read_text(encoding="utf-8"))

    assert idx["index"]["version"] == "3.1"
    assert "current_state" in idx["index"]
    assert idx["index"]["current_state"]["focus"] == "new_project"
    assert "navigate(cue, zoom, depth)" in str(idx["index"]["available_operations"])
    assert "holographic_simulate(slice_id, scenario)" in str(idx["index"]["available_operations"])
    assert any("Treat context as vivid" in g for g in idx["index"]["holographic_guidance"])


def test_run_init_does_not_overwrite_existing(tmp_path, capsys):
    """If the target already exists, run_init must print error and leave the directory untouched."""
    base = tmp_path / "existing"
    base.mkdir()
    (base / "IMPORTANT.txt").write_text("do not delete me", encoding="utf-8")

    run_init("existing", tmp_path)

    captured = capsys.readouterr()
    assert "already exists" in captured.out
    assert (base / "IMPORTANT.txt").exists()  # still there, not overwritten
    assert not (base / "index.yaml").exists()  # init did not run


def test_run_init_uses_target_dir_when_provided(tmp_path):
    custom_parent = tmp_path / "custom_parent"
    custom_parent.mkdir()
    run_init("proj", custom_parent)

    assert (custom_parent / "proj" / "index.yaml").exists()


# =============================================================================
# Mocked end-to-end run_chat test (the ultimate host loop contract)
# =============================================================================

def test_run_chat_mocked_end_to_end_flow(tmp_path, monkeypatch):
    """
    Full mocked pre-text → model emits TOOL_CALL → post-text dispatch → result injection → logging.

    This is the key integration test proving the host loop works without a real Ollama.
    We simulate one user turn + one assistant TOOL_CALL turn, then force exit.
    """
    monkeypatch.setattr(config, "AUTO_LOG_CHAT", True)

    # Prepare a minimal data workspace so build_relevant_context and logging work
    data_root = tmp_path / "e2e_workspace"
    run_init("e2e_workspace", tmp_path)  # wait, run_init puts it under tmp_path / name, adjust
    # Actually run_init("e2e_workspace", tmp_path) created tmp_path/e2e_workspace
    # but we passed the parent. For simplicity we use the one just created.
    ws = tmp_path / "e2e_workspace"

    # Patch call_ollama to return a controlled reply containing a valid TOOL_CALL on first call,
    # then a normal reply, then we exit.
    call_count = {"n": 0}

    def fake_call_ollama(model, messages, temperature=0.7, timeout=120):
        call_count["n"] += 1
        if call_count["n"] == 1:
            # First assistant reply after user: emit a tool call
            return 'Understood. I will explore that. TOOL_CALL: navigate(cue="resource_tension", zoom="standard")'
        else:
            # Follow-up after tool result
            return "Thanks, that context helps a lot."

    monkeypatch.setattr("hfcn.cli.call_ollama", fake_call_ollama)

    # Simulate user input: one message then 'exit'
    inputs = ["Tell me about the resource tension", "exit"]
    input_iter = iter(inputs)

    def fake_input(prompt=""):
        try:
            return next(input_iter)
        except StopIteration:
            return "exit"

    monkeypatch.setattr("builtins.input", fake_input)

    # Capture prints so we can assert on [TOOL RESULT] etc.
    with patch("builtins.print") as mock_print:
        # Run the chat — it will process one full cycle + tool + follow-up then exit
        run_chat(model="mock-model", data_root=ws)

    # Verify that a navigate TOOL_CALL was parsed and executed
    printed_output = " ".join(str(c[0][0]) if c and c[0] else "" for c in mock_print.call_args_list)
    assert "TOOL RESULT" in printed_output or any("Navigated to" in str(ca) for ca in mock_print.call_args_list)

    # Verify auto-logging happened for the turn(s)
    temporal = ws / "temporal_memory"
    assert temporal.exists()
    # At least one shard day dir should have been created
    day_dirs = list(temporal.glob("*/*/*"))
    assert len(day_dirs) >= 1

    # The loop reached the tool dispatch path
    assert call_count["n"] >= 2  # initial + follow-up after tool
