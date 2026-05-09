"""
HFCN Package

Holographic Fractal Context Navigation (HFCN) reference implementation.

This package provides the core modules for a minimal, low-overhead
Fluid Context Navigation system built on Python + Ollama.

Modules:
- config.py          : Configuration (data root, model, etc.)
- index_manager.py   : Load, save, and update the central index.yaml
- context_builder.py : Fractal "lens widener" - keyword + associative context retrieval
- operations.py      : Implementations of the five core HFCN operations
- prompts.py         : Builds the powerful upfront system prompt

Philosophy:
Radical simplicity. The model does reasoning. The thin Python layer
handles structure, state, and smart context assembly.
"""