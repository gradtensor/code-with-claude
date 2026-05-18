# Day 3: Building agentic applications with the Claude API

Day 2 stopped at a half-agent: one tool-use loop, one response. Day 3 turns that into a production-shaped agent: parallel tool calls, conversation memory, streaming, graceful error handling, and a mix of MCP tools alongside SDK-native tools.

## What this teaches

- A reusable `Agent` class (`shared/agent.py`) that future days will compose into workflow patterns.
- Parallel tool execution with `ThreadPoolExecutor`. Multiple tool calls in one model response run concurrently.
- Conversation memory across turns, with summarisation when the running history exceeds a token budget.
- Streaming the final response while still capturing tool calls and usage.
- Tool error handling: a failing tool returns `is_error: True` in its `tool_result` block, and the model recovers in the next iteration.
- The MCP-to-SDK adapter (`shared/mcp_adapter.py`) that lets the agent treat MCP tools and Anthropic SDK tools identically.
- Three new analyst tools that wrap LLM calls themselves: `extract_entities`, `extract_allocations`, `find_cross_references`.

## The three demos

Each demo isolates one Day 3 capability.

**`demo_parallel.py`** - asks one question that requires fetching the textile section and then running three analyst tools on it. The trace prints a tool-call timeline and computes the wall-clock-versus-serial speedup. Same agent, same tools, parallelism is visible.

```
uv run python day-03-agents/demo_parallel.py
```

**`demo_memory.py`** - runs a 4-turn conversation. Turn 2 says "the customs duty changes you mentioned" which only resolves if memory works. Turn 4 asks for a summary across the whole conversation. Prints the final messages-state so you can see what got summarised. The memory budget is set tight (4,000 tokens) so summarisation fires.

```
uv run python day-03-agents/demo_memory.py
```

**`demo_error_handling.py`** - registers a tool that always raises. The agent calls it, sees the error in the result, explains the failure to the user, and proceeds with the tools that still work. No stack trace, no crash.

```
uv run python day-03-agents/demo_error_handling.py
```

## The capstone

Day 3's capstone is at `capstone/v3-agent/analyst.py`. Run it interactively:

```
uv run python capstone/v3-agent/analyst.py
```

Or one-shot:

```
uv run python capstone/v3-agent/analyst.py --question "How does this Budget affect the textile industry?" --show-trace
```

The interactive REPL maintains memory across turns within a session. Type "exit", "quit", or Ctrl-D to leave.

## Exercise

Run the agent interactively against the Budget speech. Conduct a multi-turn conversation about a sector of your choice. Observe how memory and parallel tools change the experience compared to the Day 2 single-turn analyst.

After three or four turns, ask the agent to summarise what it told you. Notice that the answer references specific schemes and numbers from earlier turns - this only works because conversation memory is intact.

If you want to see memory summarisation fire, lower the `memory_token_budget` parameter in `analyst.py` from its default 8000 to 2000 and run the same conversation. The agent will collapse older turns into a one-paragraph summary and continue.

## Status

Code shipped. Post 3 walkthrough at [link to be added when published].
