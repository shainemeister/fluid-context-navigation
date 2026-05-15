# Real Scenario: Transform HFCN Reference into Complete Functioning Platform

**Mission Owner**: The multi-agent team (coding-audit + security-audit + coding-expert + coder + tester) working together.

**Project**: fluid-context-navigation (this repo)

**Current State (as of this document)**:
- Excellent, heavily documented reference library (`hfcn/`)
- Working example data (`hfcn_data/`) with Project Alpha Q3 planning tension
- No runnable platform: no CLI, no chat host loop, no Ollama integration, no auto-logging implementation, no tests

**Goal — "Complete and Functioning Platform" Definition**:
When this scenario is finished, a user must be able to do the following with zero extra explanation:

```bash
# 1. Initialize a new HFCN workspace (or use the existing hfcn_data)
hfcn init my-research

# 2. Start a real interactive HFCN session with a local model
hfcn chat --model qwen2.5:7b --data ./my-research

# Inside the chat the model can naturally say:
# "I need to explore the resource tension. TOOL_CALL: navigate(cue="resource_tension", zoom="deep")"

# 3. The host loop must:
#    - Inject full index.yaml + Relevant HFCN Context (pre-text)
#    - Parse the TOOL_CALL
#    - Execute the operation using the existing operations.py
#    - Feed the result back
#    - Auto-log the turn into temporal_memory/YYYY/MM/DD/...
#    - Continue the conversation fluidly

# 4. All core behaviors must be protected by a green pytest suite
pytest
```

## Phase Plan (the agents must drive this to completion)

### Phase 0 — Alignment (coding-expert leads)
- All agents read the full README, the session plan.md, and this scenario.
- coding-expert issues the architectural blueprint for the minimal host + CLI.

### Phase 1 — Audits (coding-audit + security-audit in parallel)
- coding-audit produces the philosophy compliance report on the current `hfcn/` code and any proposed new files.
- security-audit produces the threat model + minimal mitigations (especially for the future TOOL_CALL parser and file operations).

### Phase 2 — Core Host Loop (coder + tester tight loop)
- Implement `hfcn/cli.py` with `chat` and `init` subcommands.
- Implement a clean Ollama client wrapper (stdlib + requests).
- Implement a strict, safe `TOOL_CALL` parser.
- Implement auto-logging to temporal shards.
- Tester writes the contract tests in parallel and forces fixes until green.

### Phase 3 — Polish & Verification (full team)
- coding-expert reviews the final architecture.
- Full end-to-end test with a real local model (qwen2.5:7b or equivalent) successfully using `navigate` and `expand_fractal` on the Project Alpha data.
- Update README with "Running the Platform" section.
- Update `hfcn_data/index.yaml` current_state to reflect the new platform milestone.
- All tests green, all audits clean, no philosophy violations.

### Phase 4 — Optimization & Ship
- Remove any dead code or over-engineering discovered during the build.
- Make sure the entire platform still feels "HFCN" — low overhead, keyword-first, fractal.
- The team (via the user or an orchestrator) declares the platform complete only when the above "Goal" section is demonstrably true in the terminal.

## Collaboration Protocol for This Scenario
- Use `/coding-audit`, `/security-audit`, `/coding-expert`, `/coder`, `/tester` slash commands or spawn them as subagents (`spawn_subagent` with appropriate instructions referencing this scenario).
- Always produce structured handoff reports.
- The **coder** and **tester** must operate in a fast ping-pong loop.
- **coding-expert** has veto power on any decision that would dilute the original vision.
- The team must not stop until the platform is *actually usable* by a human with a local LLM and the existing `hfcn_data/` example.

This document is the single source of truth for the current build mission. Update it (or have the agents update the index.yaml "platform" section) as phases complete.

**Status**: Platform build in progress — agents are now authorized to execute the full scenario.
