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

Each day of the series has two git tags, aimed at two different audiences.

**If you are reading the posts and want the code to match what each post discusses,** check out the matching `post-NN` tag:

```
git checkout post-01    # code state as of when Post 1 published
git checkout post-02    # code state as of when Post 2 published
```

**If you are building along day by day and want the state at the end of each build session,** check out the matching `day-NN-build` tag:

```
git checkout day-01-build    # state at end of Day 1's build session
git checkout day-02-build    # state at end of Day 2's build session
```

The two tags for a given day are not identical. Small edits (clarifications, prompt hardening, eval polish, post-2-artifacts archives) typically land between the build session and the post going live. Sixteen tags total across the eight days: eight `day-NN-build` and eight `post-NN`.

## License

MIT. See [LICENSE](LICENSE).

## About

Prabhu Eshwarla writes and teaches at [GradTensor](https://gradtensor.com) on applied AI engineering. This series is the public, runnable version of the corporate training he delivers to engineering teams adopting Claude in production.
