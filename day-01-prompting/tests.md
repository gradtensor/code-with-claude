# Day 1 tests

How to verify that the Day 1 build works end to end. Use this before publishing the post and as a hands-on segment in the training session.

Run from the repo root. All commands assume `.env` exists with a valid `ANTHROPIC_API_KEY`.

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

**Edge case: empty risks**

A short document with no risks should produce an empty `risks` array, not invented ones.

```
echo "Met with Sarah from Acme today. She mentioned the Q4 launch is on track." > /tmp/tiny.txt
uv run python capstone/v1-prompt/analyst.py /tmp/tiny.txt
```

Expected: entities `["Sarah", "Acme"]`, no risks.

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
- The final summary line reads something like: `GCAO output is +25% longer, used +200 more tokens, structured JSON vs unstructured prose.` The numbers will vary; the **"structured JSON vs unstructured prose"** half is the teaching point.

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
