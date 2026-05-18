"""Day 2 baseline: stuff the entire Budget speech into every prompt.

The point is the failure mode. Same question, same model, N runs.
Watch variance, watch the tokens, watch the cost.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel

from shared.client import chat
from shared.config import DEFAULT_MODEL
from shared.tracing import log_call

PRICE_IN, PRICE_OUT = 3.0, 15.0  # Sonnet 4.6 USD per million tokens, rough.

SPEECH = Path("fixtures/budget-2026/budget_speech.txt")

SYSTEM_PROMPT = (
    "You are a senior analyst for the Indian Union Budget. "
    "Answer the user's question grounded in the speech text provided below. "
    "Be specific. Cite numbers and scheme names from the text. "
    "Do not invent facts. If the speech does not say something, say so plainly.\n\n"
    "BUDGET SPEECH:\n"
    "{speech}"
)


def _call(question: str, label: str) -> tuple[str, int, int, float, float]:
    """One chat call. Returns (text, in_tok, out_tok, cost, duration_ms)."""
    speech = SPEECH.read_text()
    system = SYSTEM_PROMPT.format(speech=speech)
    started = time.perf_counter()
    msg = chat(
        messages=[{"role": "user", "content": question}],
        system=system,
        max_tokens=2048,
    )
    duration_ms = (time.perf_counter() - started) * 1000
    text = msg.content[0].text
    in_tok, out_tok = msg.usage.input_tokens, msg.usage.output_tokens
    cost = (in_tok * PRICE_IN + out_tok * PRICE_OUT) / 1_000_000
    log_call(
        model=DEFAULT_MODEL,
        input_tokens=in_tok,
        output_tokens=out_tok,
        cost_estimate=cost,
        duration_ms=duration_ms,
        metadata={"script": "stuff_everything", "label": label, "question": question},
    )
    return text, in_tok, out_tok, cost, duration_ms


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stuff the entire Budget speech into every prompt."
    )
    parser.add_argument("question", help="The question to ask.")
    parser.add_argument("--runs", type=int, default=1, help="Run the same question N times.")
    args = parser.parse_args()

    console = Console()
    results: list[tuple[str, int, int, float, float]] = []
    for i in range(args.runs):
        console.print(f"[dim]Run {i + 1}/{args.runs}...[/dim]")
        results.append(_call(args.question, f"run_{i + 1}"))

    if args.runs == 1:
        text, in_tok, out_tok, cost, ms = results[0]
        console.print(Panel(text, title="Answer", border_style="cyan"))
        console.print(
            f"\nmodel={DEFAULT_MODEL} in={in_tok} out={out_tok} cost~${cost:.4f} {ms:.0f}ms"
        )
        return

    panels = [
        Panel(text, title=f"Run {i + 1}", border_style="cyan", width=80)
        for i, (text, *_rest) in enumerate(results)
    ]
    console.print(Columns(panels))

    console.print()
    total_in = sum(r[1] for r in results)
    total_out = sum(r[2] for r in results)
    total_cost = sum(r[3] for r in results)
    total_ms = sum(r[4] for r in results)
    for i, (_text, in_tok, out_tok, cost, ms) in enumerate(results):
        console.print(
            f"Run {i + 1}: in={in_tok} out={out_tok} cost=${cost:.4f} {ms:.0f}ms"
        )
    console.print(
        f"Total: in={total_in} out={total_out} cost=${total_cost:.4f} {total_ms:.0f}ms"
    )


if __name__ == "__main__":
    main()
