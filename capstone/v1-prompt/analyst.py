"""Capstone v1: prompt-only Document Analyst.

Reads a plain text document, runs the GCAO-engineered analyst template
against it, and returns a validated AnalysisResult wrapping the analysis
and the call usage. No tools, no agent loop, no retrieval - just a
well-engineered prompt.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel

from shared.client import chat
from shared.config import DEFAULT_MODEL
from shared.prompts import DOCUMENT_ANALYST_V1
from shared.tracing import log_call

# Rough Sonnet 4.6 pricing, USD per million tokens.
PRICE_IN, PRICE_OUT = 3.0, 15.0


class DocumentAnalysis(BaseModel):
    """Structured analysis of a single document."""

    entities: list[str]
    summary: str
    key_points: list[str]
    risks: list[str]


class Usage(BaseModel):
    """Per-call usage metadata returned alongside an analysis."""

    input_tokens: int
    output_tokens: int
    cost: float
    duration_ms: float


class AnalysisResult(BaseModel):
    """An analyse() call's full result: the analysis plus the call's usage."""

    analysis: DocumentAnalysis
    usage: Usage


def _strip_fences(text: str) -> str:
    """Strip accidental markdown fences from a JSON response."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return text


def analyze(document_text: str) -> AnalysisResult:
    """Analyse a document. Returns the analysis and the call's usage."""
    system, user = DOCUMENT_ANALYST_V1.render_system_and_user(document_text)
    started = time.perf_counter()
    msg = chat(
        messages=[{"role": "user", "content": user}],
        system=system,
        max_tokens=4096,
    )
    duration_ms = (time.perf_counter() - started) * 1000
    raw = _strip_fences(msg.content[0].text)
    analysis = DocumentAnalysis.model_validate(json.loads(raw))
    in_tok, out_tok = msg.usage.input_tokens, msg.usage.output_tokens
    cost = (in_tok * PRICE_IN + out_tok * PRICE_OUT) / 1_000_000
    log_call(
        model=DEFAULT_MODEL,
        input_tokens=in_tok,
        output_tokens=out_tok,
        cost_estimate=cost,
        duration_ms=duration_ms,
        metadata={"task": "analyze", "doc_chars": len(document_text)},
    )
    usage = Usage(
        input_tokens=in_tok,
        output_tokens=out_tok,
        cost=cost,
        duration_ms=duration_ms,
    )
    return AnalysisResult(analysis=analysis, usage=usage)


def _render(analysis: DocumentAnalysis, console: Console) -> None:
    """Pretty-print a DocumentAnalysis using rich panels."""
    console.print(Panel(analysis.summary, title="Summary", border_style="cyan"))
    console.print(
        Panel(
            "\n".join(f"- {e}" for e in analysis.entities) or "(none)",
            title="Entities",
            border_style="blue",
        )
    )
    console.print(
        Panel(
            "\n".join(f"- {k}" for k in analysis.key_points) or "(none)",
            title="Key points",
            border_style="green",
        )
    )
    console.print(
        Panel(
            "\n".join(f"- {r}" for r in analysis.risks) or "(none)",
            title="Risks",
            border_style="red",
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Document Analyst v1 (prompt-only).")
    parser.add_argument("file", type=Path, help="Path to a plain text document.")
    args = parser.parse_args()
    console = Console()
    text = args.file.read_text()
    result = analyze(text)
    _render(result.analysis, console)
    u = result.usage
    console.print(
        f"\nmodel={DEFAULT_MODEL} in={u.input_tokens} out={u.output_tokens} "
        f"cost~${u.cost:.6f} {u.duration_ms:.0f}ms"
    )


if __name__ == "__main__":
    main()
