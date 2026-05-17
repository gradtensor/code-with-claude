# Capstone v1: prompt-only baseline

The first version of the AI Document Analyst. No tools, no agent loop, no retrieval - just a well-engineered prompt built with the GCAO framework (see `shared/prompts/analyst.py`).

## What v1 does

Takes a single plain text document, sends it to Claude with the GCAO-engineered analyst prompt, parses the response as JSON, and validates it against a Pydantic schema. Pretty-prints the result and reports token usage and cost.

## Run it

From the repo root:

```
uv run python capstone/v1-prompt/analyst.py capstone/v1-prompt/sample_input.txt
```

You can pass any plain text file as the argument.

## Input

A single plain text file. PDFs, multi-document inputs, and binary formats are not supported in v1.

## Output schema

```
{
  "entities":   ["string", ...],
  "summary":    "string",
  "key_points": ["string", ...],
  "risks":      ["string", ...]
}
```

Validated with the `DocumentAnalysis` Pydantic model in `analyst.py`.

## Intentionally NOT in v1

- Tool use, function calling, agent loops (Day 3)
- PDF parsing (Day 5)
- Multi-document corpora (Day 4 onward)
- Retrieval, MCP integration (Day 2)
- Evaluation harness (Day 6)
- Markdown or HTML output (later, if needed)

Each later capstone version (v2, v3, ...) adds one capability and lives in its own subfolder.

Ships with Post 1.
