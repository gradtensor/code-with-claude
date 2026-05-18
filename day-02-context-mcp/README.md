# Day 2: Context management and the Model Context Protocol

A model is only as good as the context it sees. This day shows how a naive "stuff everything into the prompt" approach degrades on a long, sectoral document, and replaces it with an MCP server that lets the model pull only the sections it needs.

## What this teaches

- Context as a budget, not a bucket. The full Budget speech fits in the window, but it produces noisy answers and burns tokens on every call.
- The Model Context Protocol (MCP) as a standard way to expose resources and tools to Claude.
- A working MCP server over stdio: section listing tool, section reader tool, and resources for MCP-aware clients.
- A minimal tool-use client loop: discover tools from MCP, translate to the Anthropic SDK schema, call them in a loop until the model returns a final answer.

## Run the scripts

First, make sure the section index exists (only needed once, the result is committed):

```
uv run python fixtures/budget-2026/split_sections.py
```

See the failure mode. Same question, three runs, watch the variance and the cost:

```
uv run python day-02-context-mcp/stuff_everything.py "What is the outlay for the Electronics Components Manufacturing Scheme?" --runs 3
```

See the fix. The model picks the sections to read:

```
uv run python day-02-context-mcp/with_mcp.py "What is the outlay for the Electronics Components Manufacturing Scheme?" --show-trace
```

Compare the variance and the cost across three runs of the MCP version:

```
uv run python day-02-context-mcp/with_mcp.py "How does this Budget affect the textile industry?" --runs 3
```

The matching capstone, which uses the same server, is at `capstone/v2-mcp/`.

## Exercise

Work through this in order.

1. Run `stuff_everything.py` with a sectoral question and `--runs 3`. Read all three answers. Note where they disagree, where they invent, and what the total cost was.

2. Run `with_mcp.py` with the same question and `--show-trace`. Read the tool calls. The model lists sections, picks a few, reads them, then answers. Compare the answer to the stuffed version on three axes: accuracy, variance, and cost.

3. Now run `with_mcp.py` with `--runs 3` on the same question. The answers should be more consistent than the stuffed version because the model is grounded in the specific section text it requested.

4. Open `fixtures/budget-2026/sections/index.json`. Notice that one or two summaries are vague. Edit them to be sharper. Rerun `with_mcp.py` and see whether the model picks better sections.

5. Add a new tool to `capstone/v2-mcp/server.py`. A useful one: `search_budget_sections(query: str)` that returns section ids whose title or summary matches the query. Reload and ask a question that benefits from search.

## Status

Code shipped. Post 2 walkthrough at [link to be added when published].
