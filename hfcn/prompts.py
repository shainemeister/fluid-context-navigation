"""
prompts.py

Builds the powerful system prompt that loads ALL resources upfront.

Intent:
This is what makes the AI "just know" the entire HFCN structure
and behave correctly with almost zero extra instructions from the user.

By injecting the full index.yaml + philosophy + operation format
at the very beginning, we achieve:
- Continuously rolling context
- Natural conversational feel (like Grok / ChatGPT / Gemini)
- Minimal model "thinking" overhead
- Strong internalization of HFCN mode

This is the foundation of the pre-text / post-text design.
"""
from .index_manager import load_index


def build_system_prompt(include_full_index: bool = True) -> str:
    """
    Returns the master system prompt for HFCN mode.

    The full index.yaml is embedded so the model has the complete
    navigation surface available from the first token.
    """
    index = load_index()
    index_str = ""
    if include_full_index:
        import yaml
        index_str = yaml.dump(index, sort_keys=False, allow_unicode=True, default_flow_style=False)

    prompt = f"""You are operating in **Holographic Fractal Context Navigation (HFCN)** mode.

You have access to a living, navigable, self-similar context architecture.

### Your Navigation Surface (index.yaml)
This is your primary control panel. It is always up-to-date:

```yaml
{index_str}
```

### Core Philosophy
- Treat context as vivid, interactive, and reconstructive.
- Navigate via keywords first, then widen the lens fractally.
- Keep responses natural and conversational.
- Use TOOL_CALL when you need deeper context or to persist state.
- Minimize your own thinking overhead by relying on pre-loaded structure.

### Available Operations
You can call these by outputting exactly:
TOOL_CALL: operation_name(arg1="value", arg2="value")

Supported: navigate, expand_fractal, holographic_simulate, cross_reference, update_index

You are now fully initialized in HFCN mode. The user does not need to explain the system.
Begin.
"""
    return prompt.strip()