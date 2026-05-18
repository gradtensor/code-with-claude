"""Day 2: MCP-enabled Budget analyst.

Spawns the budget MCP server as a subprocess over stdio, discovers its
tools, and runs a minimal tool-use loop with Claude. The model decides
which sections to read based on the user's question. The full speech is
never stuffed into the prompt.

Compared to stuff_everything.py:
  - Input context is the system prompt plus tool definitions plus the
    sections the model chose to read (usually 1 to 4 of 20).
  - Cost is dramatically lower for the same question.
  - Variance is dramatically lower because the model is grounded in the
    specific section text it requested.
"""

from __future__ import annotations

import argparse
import asyncio
import time
from typing import Any

from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel

from shared.config import DEFAULT_MODEL, get_api_key
from shared.tracing import log_call

PRICE_IN, PRICE_OUT = 3.0, 15.0  # Sonnet 4.6 USD per million tokens, rough.
MAX_ITERATIONS = 10

SYSTEM_PROMPT = (
    "You are a senior analyst for the Indian Union Budget 2026-27. "
    "You have access to tools that let you list sections of the Budget speech "
    "and read the text of any specific section.\n\n"
    "Always start by calling list_budget_sections to see what is available. "
    "Then read only the sections relevant to the user's question. "
    "Do not invent facts. Cite scheme names and numbers from the section text."
)

SERVER_PARAMS = StdioServerParameters(
    command="uv",
    args=["run", "python", "capstone/v2-mcp/server.py"],
)


def _mcp_to_anthropic_tools(mcp_tools: list) -> list[dict]:
    """Translate MCP Tool objects into the Anthropic SDK's tool schema."""
    return [
        {
            "name": t.name,
            "description": t.description or "",
            "input_schema": t.inputSchema,
        }
        for t in mcp_tools
    ]


def _truncate(text: str, limit: int = 200) -> str:
    text = text.replace("\n", " ").strip()
    return text if len(text) <= limit else text[: limit - 1] + "..."


async def _run_once(
    client: Anthropic,
    session: ClientSession,
    tools: list[dict],
    question: str,
    label: str,
    show_trace: bool,
    console: Console,
) -> tuple[str, int, int, float, float, list[dict]]:
    """One question -> one final answer. Returns text, tokens, cost, ms, trace."""
    messages: list[dict[str, Any]] = [{"role": "user", "content": question}]
    trace: list[dict] = []
    in_total = 0
    out_total = 0
    started = time.perf_counter()

    for iteration in range(MAX_ITERATIONS):
        msg = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )
        in_total += msg.usage.input_tokens
        out_total += msg.usage.output_tokens

        if msg.stop_reason != "tool_use":
            text = "".join(b.text for b in msg.content if b.type == "text")
            duration_ms = (time.perf_counter() - started) * 1000
            cost = (in_total * PRICE_IN + out_total * PRICE_OUT) / 1_000_000
            log_call(
                model=DEFAULT_MODEL,
                input_tokens=in_total,
                output_tokens=out_total,
                cost_estimate=cost,
                duration_ms=duration_ms,
                metadata={
                    "script": "with_mcp",
                    "label": label,
                    "question": question,
                    "iterations": iteration + 1,
                    "tool_calls": len(trace),
                },
            )
            return text, in_total, out_total, cost, duration_ms, trace

        messages.append({"role": "assistant", "content": msg.content})
        tool_results: list[dict] = []
        for block in msg.content:
            if block.type != "tool_use":
                continue
            if show_trace:
                console.print(
                    f"[yellow]tool[/yellow] {block.name}({block.input})"
                )
            try:
                result = await session.call_tool(block.name, arguments=block.input)
                result_text = "\n".join(
                    c.text for c in result.content if hasattr(c, "text")
                )
                is_error = False
            except Exception as e:
                result_text = f"ERROR: {e}"
                is_error = True
            trace.append(
                {"tool": block.name, "input": block.input, "result_preview": _truncate(result_text)}
            )
            if show_trace:
                console.print(f"[dim]  -> {_truncate(result_text)}[/dim]")
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_text,
                    "is_error": is_error,
                }
            )
        messages.append({"role": "user", "content": tool_results})

    raise RuntimeError(f"hit MAX_ITERATIONS={MAX_ITERATIONS} without a final answer")


async def _amain(question: str, runs: int, show_trace: bool) -> None:
    console = Console()
    client = Anthropic(api_key=get_api_key())

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = (await session.list_tools()).tools
            tools = _mcp_to_anthropic_tools(mcp_tools)
            if show_trace:
                console.print(
                    f"[dim]discovered {len(tools)} tools: "
                    f"{', '.join(t['name'] for t in tools)}[/dim]\n"
                )

            results = []
            for i in range(runs):
                console.print(f"[dim]Run {i + 1}/{runs}...[/dim]")
                result = await _run_once(
                    client, session, tools, question, f"run_{i + 1}", show_trace, console
                )
                results.append(result)

    if runs == 1:
        text, in_tok, out_tok, cost, ms, _trace = results[0]
        console.print(Panel(text, title="Answer", border_style="green"))
        console.print(
            f"\nmodel={DEFAULT_MODEL} in={in_tok} out={out_tok} cost~${cost:.4f} {ms:.0f}ms"
        )
        return

    panels = [
        Panel(text, title=f"Run {i + 1}", border_style="green", width=80)
        for i, (text, *_rest) in enumerate(results)
    ]
    console.print(Columns(panels))

    console.print()
    total_in = sum(r[1] for r in results)
    total_out = sum(r[2] for r in results)
    total_cost = sum(r[3] for r in results)
    total_ms = sum(r[4] for r in results)
    for i, (_t, in_tok, out_tok, cost, ms, _trace) in enumerate(results):
        console.print(
            f"Run {i + 1}: in={in_tok} out={out_tok} cost=${cost:.4f} {ms:.0f}ms"
        )
    console.print(
        f"Total: in={total_in} out={total_out} cost=${total_cost:.4f} {total_ms:.0f}ms"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MCP-enabled Budget analyst. The model picks which sections to read."
    )
    parser.add_argument("question", help="The question to ask.")
    parser.add_argument("--runs", type=int, default=1, help="Run the same question N times.")
    parser.add_argument(
        "--show-trace",
        action="store_true",
        help="Print each tool call and a preview of its result.",
    )
    args = parser.parse_args()
    asyncio.run(_amain(args.question, args.runs, args.show_trace))


if __name__ == "__main__":
    main()
