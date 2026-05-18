"""Demo: graceful tool-error handling.

Registers a tool that always raises. The agent calls it, sees the error in
the tool_result block, and explains the failure to the user instead of
crashing with a stack trace.
"""

from __future__ import annotations

import json
from pathlib import Path

from mcp import StdioServerParameters
from rich.console import Console
from rich.panel import Panel

from shared.agent import Agent, ToolSpec
from shared.mcp_adapter import MCPClient


def _broken_handler(_args: dict) -> str:
    raise RuntimeError("simulated upstream failure: section database unreachable")


BROKEN_TOOL = ToolSpec(
    name="read_budget_section_alt",
    description=(
        "An alternative reader for Budget sections. Use this in place of read_budget_section "
        "to get a richer view of the section."
    ),
    input_schema={
        "type": "object",
        "properties": {"section_id": {"type": "string"}},
        "required": ["section_id"],
    },
    handler=_broken_handler,
)

SYSTEM_PROMPT = (
    "You are a Budget analyst. You have an alternative section reader called "
    "read_budget_section_alt that you should try first. If a tool fails, explain "
    "the failure to the user clearly and proceed with whatever tools still work."
)

QUESTION = (
    "Use read_budget_section_alt to get the textile section and summarise its key points."
)


def main() -> None:
    console = Console()
    params = StdioServerParameters(
        command="uv", args=["run", "python", "capstone/v2-mcp/server.py"]
    )
    with MCPClient(params) as mcp:
        agent = Agent(
            system_prompt=SYSTEM_PROMPT,
            tools=list(mcp.tool_specs()) + [BROKEN_TOOL],
            max_iterations=6,
        )
        result = agent.run(QUESTION)

    console.print(Panel(result.final_text, title="Answer", border_style="green"))
    console.print("[bold]Tool call records:[/bold]")
    for r in result.tool_calls:
        status = f"[red]ERR: {r.error}[/red]" if r.error else "[green]OK[/green]"
        console.print(f"  {r.name:30s} {status}")
    console.print(
        f"\n[dim]in={result.input_tokens} out={result.output_tokens} "
        f"cost~${result.cost:.4f} {result.duration_ms:.0f}ms iters={result.iterations}[/dim]"
    )


if __name__ == "__main__":
    main()
