# Why the Union Budget 2026-27 speech is the recurring teaching document

This series uses two documents on purpose. A synthetic quarterly business update at capstone/v1-prompt/sample_input.txt carries the in-post demonstrations. The Union Budget 2026-27 speech, in this folder, carries the reader exercises across Days 1 through 8.

This file explains the choice - why the Budget speech, and how it earns its keep across each day of the curriculum.

## The general case for the Budget speech

Four reasons it was picked.

Every Indian working developer already has intuitions about it. The reader knows roughly what's in the Budget, what got attention in the news, what their own industry got or didn't get. This intuition is the most underrated asset in a teaching document - readers can spot when the model is grounded and when it's bluffing because they know the territory. Synthetic documents do not give you this; you can fabricate ground truth, but the reader has no independent way to verify the model's output.

It is dense, sectoral, and numeric. The speech runs to about 30-40 pages of structured text with named schemes, specific allocations in crores, sectoral programmes, and cross-references between sections. This combination is unusual - most public documents are either dense and unstructured (news articles) or structured and thin (forms). The Budget speech is both dense and structured, which is exactly the shape that exposes the difference between a casual prompt and an engineered one.

It is politically charged without being controversial about facts. Opinions about the Budget vary. The facts - how much was allocated to which scheme - do not. This separation is itself a teaching moment. Working developers building corporate AI systems run into the "what the source says versus what someone thinks about it" problem constantly. The series treats the Budget as a source to be extracted and analysed, never as a thesis to be debated. This framing is established in Day 1 and held throughout.

It is publicly available and stable. The speech was delivered on February 1, 2026 and the text does not change. Anyone can verify outputs against the original. The same document drives the same exercises a year from now, so the post series and the training have stable references.

## How it earns its keep, day by day

For each day, two questions: what aspect of the topic does the Budget speech expose, and what would be lost if we used the synthetic document instead.

### Day 1 - Prompt engineering with GCAO

What it exposes. The v1 GCAO prompt was written against a 1000-word synthetic document with clear named entities, a single timeframe, and a small risk list. The Budget speech is 30 times longer, has hundreds of named entities (schemes, ministries, sectors, states, programmes), and contains overlapping risk surfaces (sectoral delays, fiscal exposure, implementation gaps). Running the v1 prompt against the Budget speech is the first moment a reader sees a perfectly good GCAO prompt produce a thin output. The Context and Action sections need real work to handle a document of this density. This is the exercise - rewrite them, run again, see the difference.

What would be lost without it. Readers would finish Day 1 thinking GCAO is sufficient. The Budget speech proves it is necessary but not sufficient - that prompt engineering is iterative, and that the same framework produces different results depending on how tightly each section is written.

### Day 2 - Context management and MCP

What it exposes. The Budget speech sits at roughly 25,000-40,000 tokens. It fits in Claude's context window, but once you add a multi-turn conversation, retrieved related documents, tool definitions, and few-shot examples, the budget gets tight even when the window is not full. This is the lesson - context is a budget, not a bucket. The Budget speech's natural section structure (Part A, Part B, sectoral programmes, fiscal annexures) maps cleanly to MCP resources. Readers split the document into sections, expose them via an MCP server, and the analyst pulls only what it needs.

What would be lost without it. A small synthetic document does not motivate context budgeting - readers would do the MCP exercise as ritual rather than necessity. The Budget speech makes the budgeting concrete. Readers also see why MCP-served sections are different from RAG chunks: the sections are semantically meaningful units (the textile programme, the rare earth corridor scheme) rather than arbitrary 500-token windows.

### Day 3 - Agentic applications with the Claude API

What it exposes. This is the day the Budget speech earns its keep most clearly. A sectoral question - "how does this Budget affect the textile industry?" - is the centrepiece. The v1 analyst gives a shallow answer because it has no tools and no way to focus its attention. A v3 agent with tools (find_section, extract_allocations, cross_reference_schemes) gives a grounded sectoral analysis: the integrated textile programme with its five sub-parts, the specific allocations, and the cross-references to related schemes elsewhere in the speech. The contrast between Day 1's answer and Day 3's answer is dramatic and entirely demonstrable from the same document.

What would be lost without it. Without a real document that contains sectoral structure, the agent's tool calls look contrived. Why would the agent need to search and cross-reference a 1000-word synthetic update? It wouldn't. The Budget speech is rich enough that tools are not optional - they are the only way to get a good answer. The lesson lands because the necessity is visible.

### Day 4 - Agentic workflow patterns

What it exposes. The five patterns from Anthropic's "Building effective agents" essay each correspond to a different shape of question that the Budget speech naturally asks.

- Routing. Sectoral questions (textile, biopharma, semiconductors) go to sector-specialised sub-prompts. Numeric extraction questions ("how much for R&D") go to extraction tools. Comparison questions ("how does this Budget compare to 2024-25") would route to a comparison agent.
- Parallelisation. Extract allocations from all sectors concurrently rather than one at a time.
- Orchestrator-workers. A coordinator agent decomposes "summarise this Budget for an EV-industry executive" into worker tasks across the relevant sectors.
- Prompt chaining. Extract structured allocations, then validate them, then summarise.
- Evaluator-optimiser. Generate a sectoral summary, then have a second pass check it against the source for groundedness.

The Budget speech motivates every pattern. The reader does not have to take it on faith that these patterns matter - they see why each one fits a kind of question that the document naturally raises.

What would be lost without it. The synthetic document is too small to motivate parallelisation, too uniform to motivate routing, and too shallow to motivate orchestrator-workers. Day 4 would feel like five abstract patterns rather than five tools for a job.

### Day 5 - Data analysis, visualisation, and insights

What it exposes. The Budget speech is a quantitative document hiding inside a prose document. Allocations in crores are scattered across sectoral paragraphs. Extracting them into a structured form (Pydantic models with sector, scheme name, allocation, timeframe) and producing a treemap of where the money goes is a real artifact a working developer would actually build for a client the day after the Budget is announced. The insight memo - what gets the most money, which sectors gained vs. lost, where the surprises are - is exactly what executives ask for in the 48 hours after a Budget speech.

What would be lost without it. A synthetic document produces synthetic charts. Readers do not get to feel "I would actually deploy this." With the Budget speech, the output is a working product. This is also the day where the corporate training has the strongest live demo - produce the Budget allocation treemap in front of the room and the lesson sells itself.

### Day 6 - Evaluation pipelines and quality assessment

What it exposes. The Budget speech is unusually well-suited to evals because it supports three kinds of test cases cleanly.

- Exact match (factual extraction). "How much is allocated to Biopharma SHAKTI?" → ₹10,000 crore. "What is the outlay for the Electronics Components Manufacturing Scheme?" → ₹40,000 crore. The answer is in the source text, verifiable, single-valued. Code-based graders work directly.
- LLM-judge (groundedness). "Is the textile programme summary supported by the source?" The judge prompt includes the relevant section of the speech and scores whether each claim in the summary is grounded in it. This is exactly the production eval pattern for systems that have to defend their answers.
- Recall-based (cross-sectoral). "Identify all R&D-related allocations across all sectors." The ground truth is a list extracted by hand. The grader measures precision and recall against it.

All three grader types appear naturally and produce defensible test cases.

What would be lost without it. Synthetic documents make for easy evals but unconvincing ones - readers know the ground truth was fabricated by the same author who wrote the document, so the evals feel circular. Budget speech evals feel like evals that would survive a code review at a real company.

### Day 7 - Workflow orchestration and automation

What it exposes. The Budget speech is large enough to demonstrate prompt caching's real economics. The system prompt plus the speech is around 30,000 input tokens. Running 20 sectoral queries against this means 600,000 cached input tokens versus 600,000 uncached - at current Sonnet 4.6 pricing, that is roughly a 70-90% cost difference, depending on the cache hit rate. Readers do not have to take prompt caching on faith. They see the numbers move.

Batch processing also motivates here. Fan out 20 sectoral queries to a worker pool, batch the results, ship a sectoral briefing. This is the shape of a real production workload.

What would be lost without it. A synthetic document is too small for caching to look impressive. The savings would be real but not dramatic. The Budget speech makes the production case for caching directly observable.

### Day 8 - Cookbook tour and capstone showcase

What it exposes. Day 8 is more framework-than-document. The Cookbook tour is general. But the capstone showcase - where readers extend the Budget analyst with one Cookbook pattern of their choice - has a real artifact at the end. A working developer leaves the series with a Budget Analyst they can demonstrate to their manager. That artifact is more memorable than a synthetic-document analyser would be.

What would be lost without it. Less. Day 8 is the most document-neutral of the eight. But the Budget Analyst as the final showcase is a much stronger portfolio piece than a generic document analyser.

## What this document does not cover, and where to look instead

Multi-document retrieval. The Budget speech is one document. Real corporate systems often operate across corpora - many documents, retrieved by relevance, with citations. This series does not cover that explicitly. The agentic frame built across Days 2 and 3 (retrieval-as-tool) is the foundation; a reader can slot embedding-based retrieval in as just another tool after finishing the series. See the main README's "what this series does not cover" section for the full reasoning.

Multi-modal content. The Budget speech is text. Charts, images, and tabular data in the actual Budget documents (the Finance Bill, the Receipts Budget, the Demand for Grants) are not covered. A natural extension day, if the series ever grows to ten parts.

Conversational follow-ups. The analyst is single-turn. Building a Budget chatbot that holds a multi-turn conversation about the speech is out of scope for this series but would be a strong next project for readers.

## How to use this document

If you are a reader of the post series: this is context for why the same document keeps appearing across eight posts. You do not need to read it before Post 1; come back if you wonder why the document was chosen.
