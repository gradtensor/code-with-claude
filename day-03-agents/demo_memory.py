"""Demo: conversation memory across turns.

Runs a 4-turn conversation. Turn 2 says "you mentioned" - that resolves only
if the agent remembers turn 1. Turn 4 asks for a summary covering all of
textile, customs, and SEZ context discussed earlier.

Prints the final messages-state at the end so the reader can see what
accumulated and whether memory summarisation kicked in.
"""

from __future__ import annotations

import json
from pathlib import Path

from mcp import StdioServerParameters
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from shared.agent import Agent
from shared.mcp_adapter import MCPClient
from shared.tools.analyst import (
    extract_allocations_tool,
    extract_entities_tool,
    make_find_cross_references_tool,
)

TURNS = [
    "How does this Budget affect the textile industry?",
    "What about the customs duty changes you mentioned - which products are affected?",
    "And the SEZ provisions - are they only for textiles or general?",
    "Summarise everything we discussed about textiles.",
]

SYSTEM_PROMPT = (
    "You are a Budget analyst with access to MCP tools and analyst tools. "
    "Maintain conversational context across turns. When the user asks a follow-up "
    "that refers to something you said earlier, answer based on what you said, "
    "fetching more sections only if you need new information."
)


def _summarise_message(m: dict) -> str:
    role = m["role"]
    content = m["content"]
    if isinstance(content, str):
        snippet = content[:160] + ("..." if len(content) > 160 else "")
        return f"{role}: {snippet}"
    pieces = []
    for block in content:
        btype = getattr(block, "type", None) or (block.get("type") if isinstance(block, dict) else None)
        if btype == "text":
            text = getattr(block, "text", None) or block.get("text", "")
            pieces.append(f"text({len(text)}c)")
        elif btype == "tool_use":
            name = getattr(block, "name", None) or block.get("name", "?")
            pieces.append(f"tool_use({name})")
        elif btype == "tool_result":
            c = getattr(block, "content", None) or block.get("content", "")
            length = len(c) if isinstance(c, str) else len(str(c))
            pieces.append(f"tool_result({length}c)")
    return f"{role}: " + ", ".join(pieces)


def main() -> None:
    console = Console()
    all_sections = json.loads(Path("fixtures/budget-2026/sections/index.json").read_text())
    params = StdioServerParameters(
        command="uv", args=["run", "python", "capstone/v2-mcp/server.py"]
    )

    with MCPClient(params) as mcp:
        # Tight memory budget on purpose so summarisation fires on a 4-turn run.
        agent = Agent(
            system_prompt=SYSTEM_PROMPT,
            tools=list(mcp.tool_specs())
            + [
                extract_entities_tool,
                extract_allocations_tool,
                make_find_cross_references_tool(all_sections),
            ],
            max_iterations=8,
            memory_token_budget=4000,
        )

        total_cost = 0.0
        summarisation_events = 0
        for i, question in enumerate(TURNS, start=1):
            console.print(Rule(f"Turn {i}: {question}"))
            result = agent.run(question)
            console.print(Panel(result.final_text, title=f"Turn {i} answer", border_style="green"))
            console.print(
                f"[dim]in={result.input_tokens} out={result.output_tokens} "
                f"cost=${result.cost:.4f} tool_calls={len(result.tool_calls)} "
                f"summarised={result.memory_summarised}[/dim]"
            )
            total_cost += result.cost
            if result.memory_summarised:
                summarisation_events += 1

        console.print(Rule("Final messages-state"))
        console.print(f"[dim]{len(agent.messages)} messages in history[/dim]")
        for i, m in enumerate(agent.messages):
            console.print(f"  [{i:2d}] {_summarise_message(m)}")
        if agent._history_summary:
            console.print(Rule("Accumulated history summary (injected into system prompt)"))
            console.print(Panel(agent._history_summary, border_style="yellow"))
        console.print(
            f"\n[bold]Session: turns={len(TURNS)} "
            f"summarisation_events={summarisation_events} "
            f"total_cost=${total_cost:.4f}[/bold]"
        )


if __name__ == "__main__":
    main()
