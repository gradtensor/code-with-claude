# Capstone v3: full agent

The v3 capstone replaces v2's single-pass tool-use loop with a full Agent class that supports parallel tool calls, conversation memory, streaming, and graceful error handling. It also adds three SDK-native analyst tools alongside the existing v2 MCP server.

## What changed from v2-mcp

| | v2-mcp | v3-agent |
|---|---|---|
| Loop | Single-script tool-use loop | Reusable `Agent` class (`shared/agent.py`) |
| Tools | 2 MCP tools | 2 MCP tools + 3 SDK tools (entities, allocations, cross-refs) |
| Parallelism | Sequential | ThreadPoolExecutor for tool calls in one response |
| Memory | None | Conversation history across turns, summarised when over budget |
| Streaming | None | Final answer streams via SDK streaming API |
| Errors | Crash on tool failure | `is_error: True` in tool_result, model recovers |
| Modes | One-shot CLI | Interactive REPL + one-shot + variance runs |

The MCP server (`capstone/v2-mcp/server.py`) is unchanged. v3-agent uses it as-is. The adapter that bridges MCP's async session to the Agent's sync tool handlers lives at `shared/mcp_adapter.py`.

## Files

- `analyst.py` - the v3-agent CLI. Builds an Agent with 5 tools (2 MCP + 3 analyst) and runs it interactively, one-shot, or in repeated runs.

## How to run

### Interactive REPL

```
uv run python capstone/v3-agent/analyst.py
```

Type questions, get answers, type follow-ups that reference previous answers. Memory persists across turns within the session. Type "exit", "quit", or press Ctrl-D to leave.

### One-shot

```
uv run python capstone/v3-agent/analyst.py --question "How does this Budget affect the textile industry?"
```

### One-shot with full tool-call trace

```
uv run python capstone/v3-agent/analyst.py --question "What are the R&D allocations?" --show-trace
```

The trace prints each tool call's start time (offset within its iteration) and duration. Identical start times mean the tools ran in parallel.

### Variance demo

```
uv run python capstone/v3-agent/analyst.py --question "..." --runs 3
```

Memory is reset between runs. Each run starts clean. Useful for surfacing answer variance on the same question.

### Disable streaming

```
uv run python capstone/v3-agent/analyst.py --question "..." --no-stream
```

By default the final answer streams. Pass `--no-stream` if you want the answer in a rich panel at the end instead. The non-streaming path is also more readable in piped output.

## What's next

Day 4 refactors the single-agent design into multiple specialised agents that route work between themselves (the workflow patterns). The Agent class from `shared/agent.py` stays the same; what changes is how many of them exist and how they hand off.
