# Build with Claude: From Prompts to Production Agents

Working code for the 8-part blog series and corporate training by Prabhu Eshwarla / GradTensor.

## Status

Work in progress. Posts and code ship one day at a time. Expect the repo to change as each post lands.

## What you'll build

The capstone is an AI Document Analyst. It takes a set of source documents (PDFs, emails, transcripts) and produces structured analysis, summaries, and answers grounded in those documents. Each day adds one capability, so by the end of the series you have a working agent that you understood every layer of.

## The 8-day arc

- Day 1: Advanced prompt engineering with the GCAO framework
- Day 2: Context management and the Model Context Protocol
- Day 3: Building agentic applications with the Claude API
- Day 4: Agentic workflow patterns
- Day 5: Data analysis, visualisation, and insights
- Day 6: Evaluation pipelines and quality assessment
- Day 7: Workflow orchestration and automation
- Day 8: The Claude Cookbook tour and capstone showcase

## Setup

1. Install [uv](https://docs.astral.sh/uv/).
2. Sync dependencies:
   ```
   uv sync
   ```
3. Copy the env template and add your Anthropic API key:
   ```
   cp .env.example .env
   ```
4. Run the smoke test:
   ```
   uv run python day-01-prompting/hello_claude.py
   ```

If the smoke test prints a streamed answer and token counts, your setup works.

## Following along

Each post has a matching git tag (post-01, post-02, etc.). Check out the tag to get the exact state at that post:

```
git checkout post-01
```

## License

MIT. See [LICENSE](LICENSE).

## About

Prabhu Eshwarla writes and teaches at [GradTensor](https://gradtensor.com) on applied AI engineering. This series is the public, runnable version of the corporate training he delivers to engineering teams adopting Claude in production.
