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

## Getting Started

1. Clone this repository.
2. Ensure Ollama is running and pull a model (e.g. `qwen2.5:7b`, `llama3.2`, `phi4`).
3. Explore `hfcn_data/` to see the structure in action.
4. Use the modules in `hfcn/` as a foundation for your own implementation or chat interface.
5. Extend with a CLI, WebUI, or API as needed.

The implementation is designed to work immediately with local models while remaining easy to scale to stronger ones.

---

## Future Directions

- Richer tool integration for the core operations
- Training protocols to accelerate HFCN mode internalization
- User-facing visualizations of the fractal structure
- Integration with external memory systems

---

**This architecture represents a deliberate move toward minimal, precise, and cognitively aligned context systems.**

A practical reference implementation with real files and well-documented code is available in this repository so you can start using and evolving HFCN immediately.

For questions or contributions, refer to the ongoing development of Fluid Context Navigation and Holographic Fractal Context Navigation.