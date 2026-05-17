# Day 1: Advanced prompt engineering with the GCAO framework

Prompt engineering is the foundation of every later capability. This day introduces the GCAO framework (Goal, Context, Action, Output) as a repeatable structure for production prompts. Prompts become first-class Python objects: validated, typed, reusable, and rendered into the system + user split that Claude expects. The capstone v1 ships as a prompt-only document analyst built on these patterns.

## What this teaches

- The GCAO framework as four required sections plus optional few-shot examples.
- Why structured prompts beat ad-hoc ones for production: predictable shape, parseable output, lower variance.
- Treating prompts as code: Pydantic validation, version control, reuse across scripts.
- Splitting the prompt into a system message (the template) and a user message (the input).

## Run the scripts

Setup smoke test:

```
uv run python day-01-prompting/hello_claude.py
```

Side-by-side comparison of an ad-hoc prompt against the GCAO template:

```
uv run python day-01-prompting/before_after.py
```

The capstone v1, which uses the same template, is at `capstone/v1-prompt/`.

## Status

Code shipped. Post 1 walkthrough at [link to be added when published].
