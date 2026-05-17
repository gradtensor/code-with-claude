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

Each day of the series has two git tags:

- `day-NN-build` - the state of the repo at the end of the build session, before the post is written.
- `post-NN` - the state of the repo when the post publishes, including any edits made during writing.

Sixteen tags total across the eight days. The two states are not identical: small edits (clarifications, prompt hardening, eval polish) often land between the build and the publish. Both tags are kept so readers can check out either reference.

```
git checkout post-01       # the state at Post 1's publish
git checkout day-02-build  # the state at end of Day 2's build session
```

Day 1 uses a legacy build tag name (`post-01-build` rather than `day-01-build`). Day 2 onward follows the standard pattern.

## License

MIT. See [LICENSE](LICENSE).

## About

Prabhu Eshwarla writes and teaches at [GradTensor](https://gradtensor.com) on applied AI engineering. This series is the public, runnable version of the corporate training he delivers to engineering teams adopting Claude in production.
