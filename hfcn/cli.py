"""
cli.py

Command-line interface and host runtime for the HFCN platform.

Intent:
This module turns the excellent hfcn/ reference library into a real,
usable platform. It provides two primary user-facing commands:

- `hfcn init <name>`  → Scaffolds a fresh, correctly structured HFCN data workspace.
- `hfcn chat`         → Starts an interactive session with a local LLM (Ollama).
                         Implements the full pre-text / post-text loop:
                         - Loads full index.yaml via prompts.py
                         - On every turn: builds relevant context via context_builder
                         - Sends rich prompt to Ollama
                         - Parses exact TOOL_CALL: lines from the model
                         - Dispatches to operations.py functions
                         - Feeds results back into the conversation
                         - Auto-logs turns into temporal_memory/ shards (when enabled)

Design constraints (non-negotiable):
- Stay radically simple. No heavy CLI frameworks (argparse only or minimal).
- Reuse every existing module without modification where possible.
- The host must be model-agnostic (works with any OpenAI-compatible / Ollama endpoint).
- All path operations must be safe (never escape the DATA_ROOT).
- Every new function must have a clear "Intent" comment.

This is the missing piece that makes HFCN a complete, functioning platform
instead of just a beautiful reference implementation.
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import requests  # Only external dependency besides PyYAML (already used)

from . import config
from .index_manager import load_index, save_index
from .prompts import build_system_prompt
from .context_builder import build_relevant_context
from .operations import (
    navigate,
    expand_fractal,
    holographic_simulate,
    cross_reference,
    update_index_op,
)

# =============================================================================
# TOOL_CALL Parsing (strict and safe)
# =============================================================================

TOOL_CALL_PATTERN = re.compile(
    r'TOOL_CALL:\s*(\w+)\s*\(\s*([^\n]*?)\s*\)\s*$',
    re.MULTILINE
)


def parse_tool_call(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse a model-generated TOOL_CALL line into a structured dict.

    Intent:
    The model is instructed to output exactly:
        TOOL_CALL: operation_name(arg1="value", arg2="value")

    This parser must be extremely strict. We do *not* use eval or any
    code execution. We manually parse simple key="value" pairs.
    Any deviation → we treat it as normal model output (no execution).
    """
    match = TOOL_CALL_PATTERN.search(text)
    if not match:
        return None

    op_name = match.group(1).strip()
    args_str = match.group(2).strip()

    # Supported operations (whitelist)
    valid_ops = {
        "navigate": navigate,
        "expand_fractal": expand_fractal,
        "holographic_simulate": holographic_simulate,
        "cross_reference": cross_reference,
        "update_index": update_index_op,
    }

    if op_name not in valid_ops:
        return {"error": f"Unknown operation: {op_name}"}

    # Strict single-line arg parser + JSON-ish support for update_index(changes={...})
    # Intent: single-line only (no DOTALL) + manual parse; special-case update_index for complex changes without eval.
    args: Dict[str, Any] = {}
    if args_str:
        if op_name == "update_index":
            # support update_index(changes=JSON...) directly, even with commas in object
            m = re.search(r'changes\s*=\s*([\'"]?)(.*?)\1\s*$', args_str.strip())
            if m:
                raw = m.group(2)
                try:
                    import json
                    changes = json.loads(raw) if raw.strip().startswith("{") else {"raw": raw}
                    if isinstance(changes, dict):
                        return {"operation": op_name, "args": changes, "func": valid_ops[op_name]}
                except Exception:
                    pass
        # normal key="val" for other ops (single-line guaranteed)
        parts = re.split(r',\s*(?=(?:[^"]*"[^"]*")*[^"]*$)', args_str)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            m = re.match(r'(\w+)\s*=\s*["\'](.+?)["\']$', part)
            if m:
                args[m.group(1)] = m.group(2)

    return {"operation": op_name, "args": args, "func": valid_ops[op_name]}


def execute_tool_call(parsed: Dict[str, Any]) -> str:
    """Execute a validated tool call and return the string result for the model."""
    if "error" in parsed:
        return f"ERROR: {parsed['error']}"

    func = parsed["func"]
    args = parsed["args"]

    try:
        # All our operations accept simple string/ dict args
        if "update_index" in parsed["operation"]:
            result = func(args)  # changes dict
        else:
            result = func(**args)
        return str(result)
    except Exception as e:
        return f"ERROR executing {parsed['operation']}: {e}"


# =============================================================================
# Ollama Client (minimal, robust)
# =============================================================================

def call_ollama(
    model: str,
    messages: list[Dict[str, str]],
    temperature: float = 0.7,
    timeout: int = 120,
) -> str:
    """
    Call a local Ollama instance and return the assistant content.

    Intent:
    Keep the LLM integration as thin as possible. We only need
    /api/chat. We stream=False for simplicity in the first version.
    """
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }

    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "")
    except requests.exceptions.ConnectionError:
        return "ERROR: Cannot connect to Ollama. Is `ollama serve` running?"
    except Exception as e:
        return f"ERROR calling Ollama: {e}"


# =============================================================================
# Auto-Logging (implements the AUTO_LOG_CHAT config flag)
# =============================================================================

def log_chat_turn(role: str, content: str, data_root: Path) -> None:
    """
    Append a turn to the correct temporal_memory shard.

    Intent:
    When AUTO_LOG_CHAT is True, every user and assistant message is
    persisted as a timestamped Markdown file so it becomes part of the
    living chronological backbone. This gives the fractal context system
    real memory across sessions.
    """
    if not config.AUTO_LOG_CHAT:
        return

    now = datetime.utcnow()
    shard_dir = (
        data_root
        / "temporal_memory"
        / f"{now.year:04d}"
        / f"{now.month:02d}"
        / f"{now.day:02d}"
    )
    shard_dir.mkdir(parents=True, exist_ok=True)

    ts = now.strftime("%Y%m%d%H%M")
    filename = f"{ts}_{role}.md"

    header = f"# {'User' if role == 'user' else 'Assistant'} Message — {now.isoformat()}Z\n\n"
    (shard_dir / filename).write_text(header + content.strip() + "\n", encoding="utf-8")


# =============================================================================
# Main Chat Loop
# =============================================================================

def run_chat(model: str, data_root: Optional[Path] = None) -> None:
    """
    The heart of the HFCN platform — the interactive chat host.

    Intent:
    This function implements the complete pre-text / post-text contract
    described in the README and prompts.py. It is deliberately simple
    so that even smaller models can drive sophisticated context navigation.
    """
    if data_root is None:
        data_root = config.DATA_ROOT
    else:
        config.set_data_root(data_root)

    print(f"HFCN Platform — chatting with {model}")
    print("Type 'exit' or 'quit' to leave. The model can use TOOL_CALL to navigate context.\n")

    # Bootstrap the conversation with the full HFCN system prompt
    system_prompt = build_system_prompt(include_full_index=True)
    messages: list[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if user_input.lower() in {"exit", "quit", "/exit"}:
            print("Ending HFCN session.")
            break

        if not user_input:
            continue

        log_chat_turn("user", user_input, data_root)

        # === PRE-TEXT: enrich with relevant HFCN context ===
        relevant = build_relevant_context()
        full_user_message = user_input
        if "No highly relevant context" not in relevant:
            full_user_message = f"{relevant}\n\n{user_input}"

        messages.append({"role": "user", "content": full_user_message})

        # Call the model
        assistant_reply = call_ollama(model, messages)
        print(f"\nAssistant:\n{assistant_reply}\n")

        log_chat_turn("assistant", assistant_reply, data_root)

        messages.append({"role": "assistant", "content": assistant_reply})

        # === POST-TEXT: look for and execute TOOL_CALL ===
        parsed = parse_tool_call(assistant_reply)
        if parsed:
            tool_result = execute_tool_call(parsed)
            print(f"[TOOL RESULT]\n{tool_result}\n")

            # Feed the tool result back so the model can continue reasoning
            messages.append({
                "role": "user",
                "content": f"TOOL_RESULT for {parsed.get('operation', 'unknown')}:\n{tool_result}"
            })

            # Give the model one more turn to react to the tool result
            follow_up = call_ollama(model, messages)
            if follow_up.strip():
                print(f"Assistant (after tool):\n{follow_up}\n")
                log_chat_turn("assistant", follow_up, data_root)
                messages.append({"role": "assistant", "content": follow_up})


# =============================================================================
# Scaffolding Command (hfcn init)
# =============================================================================

def run_init(name: str, target_dir: Optional[Path] = None) -> None:
    """
    Create a brand new, correctly structured HFCN workspace.

    Intent:
    This makes it trivial for anyone to start their own Fluid Context
    Navigation project following the exact fractal pattern.
    """
    base = (target_dir or Path.cwd()) / name
    if base.exists():
        print(f"Error: {base} already exists.")
        return

    # Create the three category roots + a minimal index.yaml
    (base / "temporal_memory").mkdir(parents=True)
    (base / "categorical_frame" / "goals").mkdir(parents=True)
    (base / "categorical_frame" / "constraints").mkdir(parents=True)
    (base / "associative_nexus" / "clusters").mkdir(parents=True)

    index_content = {
        "index": {
            "version": "3.1",
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "mode": "Holographic Fractal Context Navigation",
            "current_state": {
                "focus": "new_project",
                "active_keywords": [],
                "current_zoom": "standard",
            },
            "navigation_index": {
                "Temporal_Memory": {
                    "summary": "Chronological backbone. All conversations are stored here as timestamped shards.",
                    "primary_entry_points": [],
                },
                "Categorical_Frame": {
                    "summary": "Semantic and psychological categories. Goals, constraints, knowledge.",
                    "primary_entry_points": [],
                },
                "Associative_Nexus": {
                    "summary": "Relational and holographic binding layer.",
                    "primary_entry_points": [],
                },
            },
            "available_operations": [
                "navigate(cue, zoom, depth)",
                "expand_fractal(cue, max_branches)",
                "holographic_simulate(slice_id, scenario)",
                "cross_reference(source, target)",
                "update_index(changes)",
            ],
            "holographic_guidance": [
                "Treat context as vivid, interactive simulation",
                "Zoom fractally while preserving coherence",
                "Expand from keywords associatively",
            ],
        }
    }

    import yaml
    (base / "index.yaml").write_text(
        yaml.dump(index_content, sort_keys=False, allow_unicode=True, default_flow_style=False),
        encoding="utf-8"
    )

    print(f"Created new HFCN workspace at: {base}")
    print("You can now run: hfcn chat --data " + str(base))


# =============================================================================
# CLI Entry Point
# =============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="hfcn",
        description="Holographic Fractal Context Navigation — the working platform",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # chat
    chat_p = subparsers.add_parser("chat", help="Start an interactive HFCN session with a local model")
    chat_p.add_argument("--model", default=config.DEFAULT_MODEL, help="Ollama model name")
    chat_p.add_argument("--data", type=Path, help="Path to HFCN data root (defaults to bundled hfcn_data)")

    # init
    init_p = subparsers.add_parser("init", help="Create a new HFCN data workspace")
    init_p.add_argument("name", help="Name of the new workspace directory")
    init_p.add_argument("--path", type=Path, help="Parent directory (default: current dir)")

    args = parser.parse_args()

    if args.command == "chat":
        run_chat(args.model, args.data)
    elif args.command == "init":
        run_init(args.name, args.path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
