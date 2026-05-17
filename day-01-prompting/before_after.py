"""Before vs after: ad-hoc prompt against the GCAO-engineered template.

Runs the same input through two prompts and prints the outputs side by side.
The point is the teaching moment, not the absolute numbers: structured
prompts produce structured outputs you can act on programmatically.
"""

from __future__ import annotations

import time
from pathlib import Path

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel

from shared.client import chat
from shared.config import DEFAULT_MODEL
from shared.prompts import DOCUMENT_ANALYST_V1
from shared.tracing import log_call

PRICE_IN, PRICE_OUT = 3.0, 15.0  # Sonnet 4.6 USD per million tokens, rough.

AD_HOC_PROMPT = "Analyse this document and tell me what's important."

SAMPLE = (
    Path(__file__).resolve().parent.parent
    / "capstone"
    / "v1-prompt"
    / "sample_input.txt"
)


def _call(system: str | None, user: str, label: str) -> tuple[str, int, int, float, float]:
    """Run one chat call and return (text, in_tok, out_tok, cost, duration_ms)."""
    started = time.perf_counter()
    msg = chat(
        messages=[{"role": "user", "content": user}],
        system=system,
        max_tokens=4096,
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
        metadata={"script": "before_after", "label": label},
    )
    return text, in_tok, out_tok, cost, duration_ms


def _is_json(text: str) -> bool:
    stripped = text.strip()
    return stripped.startswith("{") and stripped.endswith("}")


def main() -> None:
    console = Console()
    document = SAMPLE.read_text()

    console.print("[dim]Running ad-hoc prompt...[/dim]")
    before_user = f"{AD_HOC_PROMPT}\n\n{document}"
    before_text, b_in, b_out, b_cost, b_ms = _call(None, before_user, "ad_hoc")

    console.print("[dim]Running GCAO template...[/dim]\n")
    system, user = DOCUMENT_ANALYST_V1.render_system_and_user(document)
    after_text, a_in, a_out, a_cost, a_ms = _call(system, user, "gcao")

    console.print(
        Columns(
            [
                Panel(
                    before_text,
                    title="Before: ad-hoc prompt",
                    border_style="red",
                    width=80,
                ),
                Panel(
                    after_text,
                    title="After: GCAO template",
                    border_style="green",
                    width=80,
                ),
            ]
        )
    )

    console.print()
    console.print(f"Before: in={b_in} out={b_out} cost=${b_cost:.6f} {b_ms:.0f}ms")
    console.print(f"After:  in={a_in} out={a_out} cost=${a_cost:.6f} {a_ms:.0f}ms")
    console.print()

    pct_diff = ((len(after_text) - len(before_text)) / max(len(before_text), 1)) * 100
    tok_diff = (a_in + a_out) - (b_in + b_out)
    before_shape = "structured JSON" if _is_json(before_text) else "unstructured prose"
    after_shape = "structured JSON" if _is_json(after_text) else "unstructured prose"
    console.print(
        f"GCAO output is {pct_diff:+.0f}% longer, used {tok_diff:+d} more tokens, "
        f"{after_shape} vs {before_shape}."
    )


if __name__ == "__main__":
    main()
