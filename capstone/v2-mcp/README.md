# Capstone v2: MCP-served Budget analyst

The v2 capstone replaces the prompt-only baseline with an MCP server that exposes the Budget speech as discrete, named sections. The analyst client lets the model decide which sections to read for each question.

## What changed from v1-prompt

| | v1-prompt | v2-mcp |
|---|---|---|
| Input strategy | Whole document in system prompt | Model picks 1 to 4 sections out of 20 |
| Tools | None | `list_budget_sections`, `read_budget_section` |
| Resources | None | `budget://<section_id>` for MCP-aware clients |
| Input tokens per question | ~30,000 | ~5,000 to ~10,000 |
| Variance across reruns | High | Low (model is grounded in section text) |
| Code shape | Single script | Server + client + a tool-use loop |

This is still a half-agent. The loop runs until the model returns a final answer, but there is no retry logic, no parallel tool calls, no self-correction. Those are Day 3.

## Files

- `server.py` - the MCP server. Reads `fixtures/budget-2026/sections/index.json` at startup, exposes two tools and 20 resources, runs over stdio.

The matching client is at `day-02-context-mcp/with_mcp.py`.

## Run the server standalone

For ad-hoc testing, you can run the server by itself. It will wait for JSON-RPC on stdin and write protocol responses to stdout. Logs go to stderr.

```
uv run python capstone/v2-mcp/server.py
```

Kill with Ctrl-C. You should see two startup log lines on stderr ("loaded N sections" and "starting budget-2026 MCP server on stdio") and no output on stdout. If anything appears on stdout, the protocol is corrupted - check that you are not using `print()` in the server.

## Test with MCP Inspector

The MCP Inspector is the official protocol-aware GUI for debugging an MCP server. It lets you list tools, call them with arbitrary arguments, and read resources without writing a client.

```
npx @modelcontextprotocol/inspector uv run python capstone/v2-mcp/server.py
```

This launches Inspector in your browser, spawns the server as a subprocess, and connects over stdio. You can verify both tools work and that the resource URIs (`budget://<id>`) are browsable.

## Test with the client

End to end, with tool-call trace:

```
uv run python day-02-context-mcp/with_mcp.py "Which sectors got new schemes in this Budget?" --show-trace
```

## Notes

- The server reads the section index at startup. If you change a section file, restart the server.
- The server logs to stderr at INFO level. Override the log level if you need quieter output (`LOG_LEVEL=WARNING` is not wired up but easy to add).
- The Anthropic SDK calls in the client are synchronous and live inside an async MCP session. This is fine for a single-turn analyst. Day 3's agent loop will use the same pattern.
