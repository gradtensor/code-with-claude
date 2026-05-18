"""Demo: parallel tool execution.

Asks one question that requires fetching the textile section, then running
three analyst tools concurrently on it. The trace at the end shows the
three extract_* calls starting at the same offset and finishing at
different times - real parallelism, not serial.
"""

from __future__ import annotations

import json
from pathlib import Path

from mcp import StdioServerParameters
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from shared.agent import Agent
from shared.mcp_adapter import MCPClient
from shared.tools.analyst import (
    extract_allocations_tool,
    extract_entities_tool,
    make_find_cross_references_tool,
)

QUESTION = (
    "For the textile sector, list the entities mentioned, the rupee allocations made, "
    "and any cross-references to other Budget sections. Call the relevant analyst tools "
    "in parallel after reading the textile section."
)

SYSTEM_PROMPT = (
    "You are a Budget analyst with access to MCP tools (list_budget_sections, "
    "read_budget_section) and analyst tools (extract_entities, extract_allocations, "
    "find_cross_references). For multi-faceted questions, fetch the relevant section "
    "first, then call the analyst tools IN PARALLEL in a single response. "
    "Do not call them one at a time across separate iterations."
)


def main() -> None:
    console = Console()
    all_sections = json.loads(Path("fixtures/budget-2026/sections/index.json").read_text())
    params = StdioServerParameters(
        command="uv", args=["run", "python", "capstone/v2-mcp/server.py"]
    )
    with MCPClient(params) as mcp:
        agent = Agent(
            system_prompt=SYSTEM_PROMPT,
            tools=list(mcp.tool_specs())
            + [
                extract_entities_tool,
                extract_allocations_tool,
                make_find_cross_references_tool(all_sections),
            ],
            max_iterations=8,
        )
        result = agent.run(QUESTION)

    console.print(Panel(result.final_text, title="Answer", border_style="green"))

    table = Table(title="Tool call timeline")
    table.add_column("Iter", justify="right")
    table.add_column("Tool")
    table.add_column("Started (ms from iter)", justify="right")
    table.add_column("Duration (ms)", justify="right")
    table.add_column("Status")
    for r in result.tool_calls:
        table.add_row(
            str(r.iteration),
            r.name,
            f"{r.started_at_ms:.0f}",
            f"{r.duration_ms:.0f}",
            "ERR: " + r.error if r.error else "OK",
        )
    console.print(table)

    # Group by iteration. Only iterations with 2+ tools are candidates for parallel
    # speedup. Serial-equivalent time is sum of durations; parallel wall clock is
    # the span from earliest start to latest finish within that iteration.
    by_iter: dict[int, list] = {}
    for r in result.tool_calls:
        by_iter.setdefault(r.iteration, []).append(r)
    console.print()
    for iteration, rs in sorted(by_iter.items()):
        if len(rs) < 2:
            continue
        total_serial = sum(r.duration_ms for r in rs)
        earliest_start = min(r.started_at_ms for r in rs)
        latest_end = max(r.started_at_ms + r.duration_ms for r in rs)
        wall = latest_end - earliest_start
        console.print(
            f"[bold]Iteration {iteration}:[/bold] {len(rs)} tools called in parallel. "
            f"Serial would take {total_serial:.0f}ms, parallel wall-clock {wall:.0f}ms, "
            f"speedup {total_serial / max(wall, 1):.2f}x"
        )

    console.print(
        f"\n[dim]in={result.input_tokens} out={result.output_tokens} "
        f"cost~${result.cost:.4f} {result.duration_ms:.0f}ms iters={result.iterations}[/dim]"
    )


if __name__ == "__main__":
    main()
