# Day 1 tests

How to verify that the Day 1 build works end to end. Use it to gate changes before shipping, or as a hands-on segment in a workshop.

Run from the repo root. All commands assume `.env` exists with a valid `ANTHROPIC_API_KEY`.

## What each test demonstrates

Three tests, three different things being proven. The progression matters.

### Test 1: "Does the plumbing work?"

This is not a test of Claude. It is a test of whether you are correctly set up to use Claude. Every layer of the toolchain runs end to end: uv installs the right packages, python-dotenv reads `.env`, your API key is valid, the anthropic SDK reaches the model, the streaming response renders through rich, and the `shared.tracing` module writes a JSONL record.

A single working API call across all of those layers in under three seconds for a tenth of a US cent. The equivalent of `git --version` or `docker run hello-world`. Every subsequent test depends on this passing.

In a workshop, this is the "everyone got into the building" check. If a participant's smoke test fails, nothing else they do today will work.

### Test 2: "Can a prompt alone do real work?"

This proves three things, in increasing strictness:

1. **The model returns valid JSON.** If the response is markdown, free-form prose, or malformed JSON, `json.loads()` dies. Valid JSON means the GCAO template's `<output>` section is tight enough that the model stays inside the contract.
2. **The JSON matches the schema.** `DocumentAnalysis.model_validate()` rejects any response missing `entities`, `summary`, `key_points`, or `risks`, or with the wrong types. Pydantic passing means the model honoured every field requested.
3. **The content is grounded.** The panels match the source document. Every entity, key point, and risk is actually in the text. The `<action>` section's "Do not invent facts" instruction holds up.

The big claim: you can build a working document analyst with nothing but a well-engineered prompt. No tools, no retrieval, no agent loop. That is the whole point of capstone v1, and it is the foundational claim of Day 1. Structure in the prompt produces structure in the output, and that is often enough to ship.

The lesson: before reaching for an agent framework, reach for a better prompt.

### Test 3: "Why does GCAO matter?"

Same input. Two prompts. One ad-hoc ("Analyse this document and tell me what's important"), one GCAO-engineered. Run both. Compare the outputs side by side. This is the teaching moment of the whole post.

The ad-hoc prompt produces a beautifully formatted markdown report: headers, bullets, a decision-points table, an "Overall Assessment" section. A human would love reading it. A program cannot do anything with it. There is no schema, no parseable structure, no contract.

The GCAO prompt produces a single JSON object. A human would not want to read it raw. But a Pydantic model can validate it, a database can store it, a downstream system can route on its fields, and a regression suite can score it.

Both answers are factually correct. The difference is not quality of analysis. It is **shape**. And shape is what determines whether you have a demo or a system.

The numbers reveal something quietly important: the GCAO output is often *shorter* and at *similar cost* to the ad-hoc output. Structure is not more expensive. A detailed system prompt costs more on input tokens. But it also constrains the output, which usually saves more tokens than it spent.

### The progression

The three tests form a narrative arc:

1. **Test 1** establishes a baseline: you can call Claude.
2. **Test 2** raises the bar: you can call Claude in a way that produces validated, structured, grounded outputs from nothing but a prompt.
3. **Test 3** shows the cost of *not* doing (2): the same effort, the same money, but an output you cannot build a system on top of.

Call, structure, contrast. Run them in that order in a live session and the punchline lands on its own.

### Why this matters for the rest of the series

Every later day depends on structured prompt outputs:

- Day 3 (agents) needs structured tool calls.
- Day 4 (patterns) needs structured intermediate results to chain.
- Day 6 (evals) needs structured outputs to score against.
- Day 7 (orchestration) needs structured outputs to route through queues.

A production agent cannot run on free-form prose. Day 1 proves why with a concrete, runnable demonstration that costs about a US nickel. Everything else in the series is a refinement of what Day 1 established.

## Test 1: Smoke test

**What it proves:** API key works, the SDK is wired up, tracing writes to disk.

```
uv run python day-01-prompting/hello_claude.py
```

**Pass criteria**
- A one-sentence answer streams to the terminal.
- Final line: `model=claude-sonnet-4-6 in=... out=... cost~$0.000... ...ms`
- A file appears at `traces/<today>.jsonl` containing one JSON record.

**Cost:** ~$0.001. **Time:** under 10 seconds.

If this fails, your `.env` or API key is wrong. Fix that before anything else.

## Test 2: Document Analyst v1

**What it proves:** the GCAO template produces a valid `DocumentAnalysis`, the Pydantic schema holds, the JSON parser is robust, the result is grounded in the source.

```
uv run python capstone/v1-prompt/analyst.py capstone/v1-prompt/sample_input.txt
```

**Pass criteria**
- Four rich panels print: Summary (cyan), Entities (blue), Key points (green), Risks (red).
- Final usage line prints token counts and cost.

**Quality checks (eyeball the output)**

The output should be grounded in the sample document. Look for:

- **Entities:** Maya Rodriguez, Tomas Bremer, Reema Iyer, Adaeze Okonkwo, Helios, Aurora, Brennan Industries, Pearmont Financial, Greylock Logistics, Beacon Health.
- **Risks:** Asia-Pacific partner programme delay, Aurora analytics slip, platform team hiring gap, two enterprise churn events, SOC 2 timing concerns.
- **Summary:** mentions both the strong Q3 numbers and the items needing leadership attention.

**Failure modes**
- `pydantic.ValidationError` or `json.JSONDecodeError`: the model deviated from the JSON schema. The prompt needs hardening.
- Entities or risks that aren't in the document: the model is fabricating. The prompt's "Do not invent facts" instruction needs more weight.

**A note on variance**

Two runs on the same input will not produce identical output. Wording shifts, items reorder, occasionally a borderline entity is included or dropped. The list above is what *should generally* appear, not a strict checksum. If two or three items differ run to run, that is normal. If half the list is missing, something is wrong.

**Cost:** ~$0.02. **Time:** 15-25 seconds.

## Test 3: Before/after comparison

**What it proves:** the teaching point of the post. The same input through an ad-hoc prompt versus the GCAO template produces visibly different shapes.

```
uv run python day-01-prompting/before_after.py
```

**Pass criteria**
- Two side-by-side panels print: red "Before" and green "After".
- The **shape difference** is obvious:
  - Before: prose, bullets, headers, conversational.
  - After: a JSON object starting with `{` and ending with `}`.
- The final summary line reads something like: `GCAO output is 12% shorter, used 522 more tokens, structured JSON vs unstructured prose.`

**A note on variance**

The numeric deltas in the summary line vary significantly between runs because the ad-hoc output is unbounded. One run may show "+25% longer", the next "-12% shorter", the next "+40% longer". This is normal and does not indicate a bug. Workshop participants should not panic if their numbers differ from a previous run.

The **"structured JSON vs unstructured prose"** half of the line is what is reproducible, and it is the only half that matters for the teaching point. If that part flips (both runs show "JSON vs JSON" or "prose vs prose"), the test is not working as intended.

**Failure mode**

If both outputs look structured, the ad-hoc prompt got lucky and the contrast is muted. The `AD_HOC_PROMPT` constant in `before_after.py` needs to be weakened.

**Cost:** ~$0.04 (two calls). **Time:** 25-45 seconds.

## Sanity checks (no API cost)

**Validation works**

```
uv run python -c "from shared.prompts import PromptTemplate; PromptTemplate(goal='', context='c', action='a', output='o')"
```

Expected: `pydantic.ValidationError`.

**Trace file accumulates**

```
ls -la traces/
cat traces/$(date -u +%Y-%m-%d).jsonl | wc -l
```

Expected: one line per API call made during testing.

**Friendly error with no key**

```
ANTHROPIC_API_KEY= uv run python capstone/v1-prompt/analyst.py capstone/v1-prompt/sample_input.txt
```

Expected: "Copy .env.example to .env" message, exit code 1, no traceback.

## Total cost

Running all three tests once: roughly 5 to 7 US cents at current Sonnet 4.6 pricing. Numbers vary with output length.

## Use in training

For a live session, the natural order is:
1. Run Test 1 to confirm setup (everyone follows along).
2. Run Test 2 and read the output together.
3. Run Test 3 and discuss what the shape difference buys you in production.
4. Run the sanity checks as a wrap.
