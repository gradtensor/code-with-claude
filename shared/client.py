"""Anthropic client factory and a thin chat helper."""

from __future__ import annotations

from typing import Any, Iterable

from anthropic import Anthropic

from shared.config import DEFAULT_MODEL, get_api_key


def get_client() -> Anthropic:
    """Return an Anthropic client configured from the environment."""
    return Anthropic(api_key=get_api_key())


def chat(
    messages: list[dict[str, Any]],
    model: str | None = None,
    system: str | None = None,
    max_tokens: int = 1024,
    stream: bool = False,
) -> Any:
    """Send a message to Claude. Returns a Message or a streaming context."""
    client = get_client()
    kwargs: dict[str, Any] = {
        "model": model or DEFAULT_MODEL,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if system is not None:
        kwargs["system"] = system
    if stream:
        return client.messages.stream(**kwargs)
    return client.messages.create(**kwargs)
