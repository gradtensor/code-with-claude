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

## Exercise

Work through this in order. Stop and read the output between steps.

1. Run the synthetic comparison first to ground the GCAO contrast on a tractable example:

   ```
   uv run python day-01-prompting/before_after.py
   ```

   Around 30 seconds.

2. Run the v1 analyst against a real document, the Union Budget speech:

   ```
   uv run python capstone/v1-prompt/analyst.py fixtures/budget-2026/budget_speech.txt
   ```

3. Read the output critically. Where does the GCAO prompt struggle? What does it miss? What does it invent? Note three or four specific examples before moving on.

4. Open `shared/prompts/analyst.py` and rewrite the `context` and `action` fields of `DOCUMENT_ANALYST_V1` to better handle a long, multi-sectoral document. Run step 2 again. Note the difference.

5. Now ask a sectoral question by prepending it to the input:

   ```
   { echo "How does this Budget affect the textile industry?"; cat fixtures/budget-2026/budget_speech.txt; } > /tmp/budget_question.txt
   uv run python capstone/v1-prompt/analyst.py /tmp/budget_question.txt
   ```

   The answer will be shallow. This is intentional. A prompt cannot retrieve, filter, or compute. Day 3 fixes this with tools.
