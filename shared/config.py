"""Environment and model configuration."""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL: str = "claude-sonnet-4-6"
CHEAP_MODEL: str = "claude-haiku-4-5"
STRONG_MODEL: str = "claude-opus-4-7"


def get_api_key() -> str:
    """Return the Anthropic API key or exit with a helpful message."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key or key == "your-key-here":
        sys.stderr.write(
            "ANTHROPIC_API_KEY is not set.\n"
            "Copy .env.example to .env and add your key:\n"
            "    cp .env.example .env\n"
        )
        sys.exit(1)
    return key


ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
