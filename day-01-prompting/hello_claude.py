"""Smoke test for the Build with Claude setup. Streams a one-sentence answer."""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console

from shared.client import chat
from shared.config import DEFAULT_MODEL
from shared.tracing import log_call

PRICE_IN, PRICE_OUT = 3.0, 15.0  # Sonnet 4.6 USD per million tokens, rough.


def main() -> None:
    console = Console()
    prompt = "In one sentence, what is GCAO prompt engineering?"
    started = time.perf_counter()
    with chat(messages=[{"role": "user", "content": prompt}], stream=True) as stream:
        for text in stream.text_stream:
            console.print(text, end="")
        msg = stream.get_final_message()
    duration_ms = (time.perf_counter() - started) * 1000
    in_tok, out_tok = msg.usage.input_tokens, msg.usage.output_tokens
    cost = (in_tok * PRICE_IN + out_tok * PRICE_OUT) / 1_000_000
    console.print(f"\n\nmodel={DEFAULT_MODEL} in={in_tok} out={out_tok} cost~${cost:.6f} {duration_ms:.0f}ms")
    log_call(DEFAULT_MODEL, in_tok, out_tok, cost, duration_ms, {"script": "hello_claude"})


if __name__ == "__main__":
    main()
