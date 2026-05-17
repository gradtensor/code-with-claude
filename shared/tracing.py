"""Minimal JSONL tracing. Replaced by Langfuse in Day 7."""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterator

TRACE_DIR = Path("traces")


def _trace_file() -> Path:
    TRACE_DIR.mkdir(exist_ok=True)
    return TRACE_DIR / f"{date.today().isoformat()}.jsonl"


def log_call(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost_estimate: float,
    duration_ms: float,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Append a single call record to today's trace file."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_estimate": cost_estimate,
        "duration_ms": duration_ms,
        "metadata": metadata or {},
    }
    with _trace_file().open("a") as f:
        f.write(json.dumps(record) + "\n")


@contextmanager
def trace(name: str) -> Iterator[dict[str, Any]]:
    """Time a block and write a trace record on exit."""
    started = time.perf_counter()
    ctx: dict[str, Any] = {"name": name}
    try:
        yield ctx
    finally:
        duration_ms = (time.perf_counter() - started) * 1000
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "name": name,
            "duration_ms": duration_ms,
            "metadata": ctx,
        }
        with _trace_file().open("a") as f:
            f.write(json.dumps(record) + "\n")
