# Holographic Fractal Context Navigation (HFCN)

**Fluid Context Navigation (FCN)** is the human-intuitive concept.  
**Holographic Fractal Context Navigation (HFCN)** is the formal technical system the AI operates in.

This architecture delivers a minimal, precise, and scalable foundation for dynamic context management in AI systems. It prioritizes low cognitive load, keyword-first navigation, fractal self-similarity, and associative expansion while keeping instruction overhead very low.

---

## Overview

HFCN treats context as a living, navigable, self-similar space built on three ideas:

- **Minimal Semantic Structure** — Only three high-level categories.
- **Fractal Self-Similarity** — Consistent patterns that support coherent zooming at any scale.
- **Holographic Qualities** — Vivid, interactive, and reconstructive context handling.

**Core Priorities**
- Human + AI readability
- Low token overhead
- Keyword-first entry followed by associative expansion
- Strong chronological backbone via sharded `temporal_memory`
- Clear separation between the lightweight `index.yaml` control panel and deeper content

---

## Architecture & Core Concepts

### High-Level Structure

```
index.yaml                     ← Lightweight AI navigation surface (always loaded)
├── Temporal_Memory/           ← Chronological backbone + raw sources (sharded by timestamp)
├── Categorical_Frame/         ← Semantic & psychological categories (self-similar)
└── Associative_Nexus/         ← Relational & holographic binding layer
```

### The Three Categories

| Category            | Purpose                              | Example Content                     |
|---------------------|--------------------------------------|-------------------------------------|
| **Temporal_Memory** | Living chronological record         | Timestamped chat logs & events     |
| **Categorical_Frame** | Semantic & psychological structure | Goals, constraints, knowledge      |
| **Associative_Nexus** | Relational & cross-cutting links   | Clusters, long-range associations  |

The structure is deliberately **self-similar**: the same navigation patterns work at the top level and deep inside any category.

### Key Design Principles
- **Minimalism** — Maximum of three top-level categories.
- **Keyword-First + Expansion** — Start with keywords, then widen the lens associatively.
- **Lazy Loading** — Heavy content is loaded on demand, not all at once.
- **Readability First** — YAML + simple files preferred over complex systems.
- **Separation of Concerns** — `index.yaml` is the thin control surface; content lives in the directory tree.

---

## The index.yaml Control Panel

`index.yaml` is the single most important file. It is kept deliberately small so it can be loaded **in full** inside the system prompt at the start of every session.

It acts as the AI’s persistent “mental map” and contains:

- `current_state` — Current focus, active keywords, and zoom level.
- `navigation_index` — Lightweight entry points into the three categories (with keywords that trigger loading).
- `available_operations` — The small set of high-level functions the AI can call.
- `holographic_guidance` — Short behavioral rules the model internalizes.

Because it is small and high-signal, the model can re-read or update it cheaply. All meaningful state changes go through the `update_index` operation.

**Example location in this repo:** `hfcn_data/index.yaml`

---

## Pre-text / Post-text Navigation Flow

A core structural pattern is the clean separation between **pre-text** and **post-text**:

**Pre-text (before model call)**
- User message arrives.
- `context_builder` performs keyword + associative search across the three categories.
- Relevant excerpts are injected as "Relevant HFCN Context".
- The model receives a compact, high-signal context slice + the full `index.yaml`.

**Post-text (after model response)**
- If the model outputs a `TOOL_CALL: operation(...)` line, it is parsed and executed.
- The result is fed back into the conversation naturally.
- The model continues without the user managing context manually.

This design lets the AI navigate and expand context fluidly while staying in a natural conversational flow.

---

## Core Operations

The system exposes five high-level operations:

- `navigate(cue, zoom, depth)` — Move focus and retrieve relevant context.
- `expand_fractal(cue, max_branches)` — Perform deeper associative expansion.
- `holographic_simulate(slice_id, scenario)` — Run vivid simulation on a context slice.
- `cross_reference(source, target)` — Create or follow relational links.
- `update_index(changes)` — Persist lightweight updates to `index.yaml`.

These are designed to be called with minimal prompting once the model is operating in HFCN mode.

---

## Reference Implementation

A complete, working reference implementation is included in this repository under the `hfcn/` directory. It follows the architecture described above while prioritizing **radical simplicity and low overhead**.

### Key Modules

| Module                  | Purpose                                      | Key File in Repo                     |
|-------------------------|----------------------------------------------|--------------------------------------|
| `prompts.py`            | Builds the powerful upfront system prompt   | `hfcn/prompts.py`                   |
| `context_builder.py`    | Fractal "lens widener" (pre-text enrichment) | `hfcn/context_builder.py`           |
| `index_manager.py`      | Load/save/update the central `index.yaml`   | `hfcn/index_manager.py`             |
| `operations.py`         | Implementations of the five core operations | `hfcn/operations.py`                |
| `config.py`             | Central configuration                        | `hfcn/config.py`                    |

All modules contain detailed comments explaining their intent and design decisions.

### Data Example

A ready-to-use data structure is provided in `hfcn_data/` following the exact layout described in this document, including:
- Timestamped `temporal_memory` shards
- Sample content in all three categories
- A fully populated `index.yaml`

### Philosophy
Simplification increases efficiency. Keyword-first navigation + recursive directory walking replaces complex retrieval systems while remaining fully human-inspectable. The model focuses on reasoning; the thin Python layer handles structure and context assembly.

---

## Project Layout

```
fluid-context-navigation/
├── README.md
├── hfcn_data/                    ← Example data following the architecture
│   ├── index.yaml
│   ├── temporal_memory/          ← Sharded by YYYYMMDDhhmm
│   ├── categorical_frame/
│   └── associative_nexus/
└── hfcn/                         ← Well-documented Python implementation
    ├── __init__.py
    ├── config.py
    ├── index_manager.py
    ├── context_builder.py
    ├── prompts.py
    └── operations.py
```

---

## The HFCN Platform (Recommended)

The original reference implementation has been evolved — through a dedicated team of specialized AI agents — into a complete, runnable, and self-improving platform while preserving every principle of **radical simplicity**, **fractal self-similarity**, and **low cognitive overhead**.

### Quick Start

```bash
# Install the platform in development mode
pip install -e .

# Create a brand new, correctly structured HFCN workspace
hfcn init my-research-project

# Start an interactive session with any local Ollama model
hfcn chat --model qwen2.5:7b --data ./my-research-project
```

Inside the chat the model can fluidly navigate context using the five core operations:

```
TOOL_CALL: navigate(cue="resource_tension", zoom="deep")
TOOL_CALL: expand_fractal(cue="planning_tension", max_branches=6)
TOOL_CALL: holographic_simulate(slice_id="project_alpha_q3_planning.md", scenario="board presentation")
```

The host automatically:
- Injects the full `index.yaml` + relevant context (pre-text)
- Parses and safely executes `TOOL_CALL` lines (post-text)
- Auto-logs every turn into `temporal_memory/`
- Keeps the entire experience natural and conversational

### Multi-Agent Collaboration System

This repository ships with a powerful multi-agent skill platform located in `.grok/skills/`:

| Skill                | Role                                      | When to Use |
|----------------------|-------------------------------------------|-------------|
| `/coding-audit`      | Philosophy enforcer (simplicity, fractal structure, Intent comments) | Code quality & design reviews |
| `/security-audit`    | Threat modeling for LLM-driven file operations & TOOL_CALL surfaces | Security reviews |
| `/coding-expert`     | Deep HFCN architect and final decision authority | Architectural guidance |
| `/coder`             | Minimal, high-fidelity implementation     | Writing new features |
| `/tester`            | Contract + security regression testing (31 tests, all green) | Verification |

These agents were used **to build the platform itself** following the mission documented in [`.grok/skills/hfcn-platform-scenario.md`](.grok/skills/hfcn-platform-scenario.md).

You can invoke them directly in this environment or spawn them as sub-agents for parallel work.

### Running Tests

```bash
python3 -m pytest -q
# 31 passed
```

The test suite includes high-signal contract tests, security property tests (path traversal, symlink escapes, TOOL_CALL injection), and mocked end-to-end host loop verification.

### Using the Original Reference Library

If you prefer to build your own host or integrate HFCN into another system:

1. Clone this repository.
2. Ensure Ollama is running and pull a model.
3. Explore `hfcn_data/` to see the fractal structure.
4. Import modules from `hfcn/` (`prompts.py`, `context_builder.py`, `operations.py`, etc.).
5. Implement your own pre-text / post-text loop following the patterns in `cli.py`.

The reference library remains extremely clean and well-documented for this purpose.

---

## Future Directions

- Self-improvement of the platform through the built-in multi-agent system (`/coder`, `/tester`, `/coding-audit`, etc.)
- Richer tool integration and external memory backends while staying minimal
- Training protocols and prompt packs to help models internalize HFCN mode faster
- Visualizations of the live fractal context space
- Packaging and distribution as a proper Python package on PyPI

---

**This architecture represents a deliberate move toward minimal, precise, and cognitively aligned context systems — now with a complete, agent-driven platform on top.**

The combination of the elegant reference library + the multi-agent collaboration skills + the runnable `hfcn` host gives you both a powerful tool *and* the means to continue evolving it while strictly preserving the original philosophy.

Start with:

```bash
hfcn init my-project
hfcn chat --model qwen2.5:7b
```

Then bring in the agents with `/coding-expert`, `/coder`, or `/security-audit` whenever you want to extend or harden the system.

For questions or contributions, refer to the ongoing development of Fluid Context Navigation and Holographic Fractal Context Navigation — now actively maintained by both humans and specialized AI agents.