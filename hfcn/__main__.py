"""
__main__.py

Intent:
Allows the HFCN platform to be executed directly as a module:
    python -m hfcn chat --model qwen2.5:7b

This is the standard Python entry point that calls the real CLI
implemented in cli.py. It exists purely for convenience and
discoverability — no logic lives here.
"""

from .cli import main

if __name__ == "__main__":
    main()
