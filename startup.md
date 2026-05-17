# Startup

Next steps after the initial scaffold.

## 1. Add your API key

```
cp .env.example .env
```

Open `.env` and set `ANTHROPIC_API_KEY` to your real key.

## 2. Run the smoke test

```
uv run python day-01-prompting/hello_claude.py
```

Expected output: a streamed one-sentence answer, followed by a line like:

```
model=claude-sonnet-4-6 in=... out=... cost~$0.000xxx ...ms
```

A trace record also lands in `traces/YYYY-MM-DD.jsonl`.

## 3. Confirm pricing constants

`day-01-prompting/hello_claude.py` uses rough Sonnet 4.6 prices:

```
PRICE_IN, PRICE_OUT = 3.0, 15.0   # USD per million tokens
```

Update these if the published rates change or if you want a different display.

## 4. Tag the post when Post 1 ships

```
git tag post-01
git push origin post-01
```

Readers can then `git checkout post-01` to land on the exact state at that post.

## 5. Push to GitHub (when ready)

```
gh repo create build-with-claude --public --source=. --remote=origin --push
```

Or create the repo manually and add the remote.
