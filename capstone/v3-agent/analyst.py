"""Capstone v3: full Document Analyst agent.

Combines the v2 MCP server (list_budget_sections, read_budget_section) with
three SDK tools (extract_entities, extract_allocations, find_cross_references)
and runs them through the reusable Agent loop from shared.agent.

CLI modes:
  - default: interactive REPL.
  - --question "...": one-shot answer.
  - --question "..." --runs N: repeated runs for variance demos.
  - --show-trace: print every tool call with timings.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from mcp import StdioServerParameters
from rich.console import Console
from rich.panel import Panel

from shared.agent import Agent, ToolCallRecord
from shared.config import DEFAULT_MODEL
from shared.mcp_adapter import MCPClient
from shared.tools.analyst import (
    extract_allocations_tool,
    extract_entities_tool,
    make_find_cross_references_tool,
)
from shared.tracing import log_call

SECTIONS_INDEX = Path("fixtures/budget-2026/sections/index.json")
SERVER_PARAMS = StdioServerParameters(
    command="uv",
    args=["run", "python", "capstone/v2-mcp/server.py"],
)

SYSTEM_PROMPT = (
    "You are a senior analyst for the Indian Union Budget 2026-27.\n\n"
    "<goal>\n"
    "Answer the user's question with specifics: scheme names, allocations, sectoral impact. "
    "Ground every claim in section text you retrieve.\n"
    "</goal>\n\n"
    "<context>\n"
    "The Budget speech is split into 20 named sections accessible via the MCP server. "
    "You also have three analyst tools that wrap small LLM calls: extract_entities, "
    "extract_allocations, and find_cross_references. Use them in parallel where possible "
    "to keep latency low.\n"
    "</context>\n\n"
    "<action>\n"
    "1. Call list_budget_sections first to see what is available.\n"
    "2. Read the section(s) most relevant to the question.\n"
    "3. For sectoral questions, call find_cross_references to discover related sections, "
    "then read them.\n"
    "4. For numeric or entity-rich questions, run extract_entities and extract_allocations "
    "on the relevant text. You can call these in parallel.\n"
    "5. Synthesise a grounded answer. Quote ₹ amounts exactly. Cite section titles.\n"
    "Do not invent facts. If the speech does not say something, say so plainly.\n"
    "</action>\n\n"
    "<output>\n"
    "Plain prose with structured sections where useful. No JSON unless explicitly asked.\n"
    "</output>"
)


def _print_trace(records: list[ToolCallRecord], console: Console) -> None:
    if not records:
        return
    console.print("[dim]Tool calls:[/dim]")
    for r in records:
        marker = "[red]ERR[/red]" if r.error else "[green]OK[/green]"
        console.print(
            f"  {marker} {r.name:30s} start+{r.started_at_ms:6.0f}ms  took {r.duration_ms:6.0f}ms"
        )


def _run_one(agent: Agent, question: str, console: Console, show_trace: bool, stream: bool) -> Any:
    if stream:
        console.print()
        result = agent.run(question, stream=True, on_text=lambda d: console.print(d, end=""))
        console.print()
    else:
        result = agent.run(question, stream=False)
        console.print(Panel(result.final_text, title="Answer", border_style="green"))
    if show_trace:
        _print_trace(result.tool_calls, console)
    console.print(
        f"\n[dim]model={DEFAULT_MODEL} in={result.input_tokens} out={result.output_tokens} "
        f"cost~${result.cost:.4f} {result.duration_ms:.0f}ms "
        f"iters={result.iterations} tool_calls={len(result.tool_calls)}"
        f"{' summarised' if result.memory_summarised else ''}[/dim]"
    )
    log_call(
        model=DEFAULT_MODEL,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cost_estimate=result.cost,
        duration_ms=result.duration_ms,
        metadata={
            "script": "v3-agent",
            "question": question,
            "iterations": result.iterations,
            "tool_calls": len(result.tool_calls),
        },
    )
    return result


def _build_agent(mcp_tools: list, all_sections: list[dict]) -> Agent:
    tools = list(mcp_tools) + [
        extract_entities_tool,
        extract_allocations_tool,
        make_find_cross_references_tool(all_sections),
    ]
    return Agent(system_prompt=SYSTEM_PROMPT, tools=tools, max_iterations=10)


def _repl(agent: Agent, console: Console, show_trace: bool) -> None:
    console.print(
        "[bold]Budget Analyst v3[/bold]  (interactive). "
        "Type 'exit', 'quit', or Ctrl-D to leave. Memory persists across turns.\n"
    )
    turn = 0
    total_cost = 0.0
    total_tool_calls = 0
    while True:
        try:
            question = console.input("[bold cyan]> [/bold cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            break
        if not question:
            continue
        if question.lower() in {"exit", "quit", "q"}:
            break
        turn += 1
        result = _run_one(agent, question, console, show_trace=show_trace, stream=True)
        total_cost += result.cost
        total_tool_calls += len(result.tool_calls)
    console.print(
        f"\n[dim]Session: turns={turn} cost~${total_cost:.4f} tool_calls={total_tool_calls}[/dim]"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Budget Analyst v3 (full agent).")
    parser.add_argument("--question", type=str, default=None, help="One-shot question. Omit for REPL.")
    parser.add_argument("--runs", type=int, default=1, help="Repeat the same question N times.")
    parser.add_argument("--show-trace", action="store_true", help="Print every tool call.")
    parser.add_argument("--no-stream", action="store_true", help="Disable streaming.")
    args = parser.parse_args()

    console = Console()
    all_sections = json.loads(SECTIONS_INDEX.read_text())

    with MCPClient(SERVER_PARAMS) as mcp:
        mcp_tools = mcp.tool_specs()
        agent = _build_agent(mcp_tools, all_sections)
        if args.question is None:
            _repl(agent, console, args.show_trace)
            return
        for i in range(args.runs):
            if args.runs > 1:
                console.print(f"[dim]Run {i + 1}/{args.runs}[/dim]")
                agent.reset_memory()
            _run_one(agent, args.question, console, args.show_trace, stream=not args.no_stream)


if __name__ == "__main__":
    main()
