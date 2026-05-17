"""Pre-built GCAO template for the Document Analyst capstone."""

from __future__ import annotations

from shared.prompts.base import PromptTemplate

DOCUMENT_ANALYST_V1 = PromptTemplate(
    goal=(
        "Produce a strict, machine-readable analysis of a business document "
        "that surfaces named entities, a short summary, the most important "
        "factual points, and any risks worth attention."
    ),
    context=(
        "You are a senior analyst reviewing business documents such as status "
        "reports, memos, transcripts, or emails. Your output is consumed by a "
        "downstream system that requires valid JSON. Readers are decision-makers "
        "who scan quickly, so brevity and specificity matter. Every item in your "
        "output must be grounded in the source text."
    ),
    action=(
        "Read the document carefully, then:\n"
        "1. Extract named entities (people, organisations, products, places). Deduplicate.\n"
        "2. Write a 2-3 sentence summary capturing the document's purpose and headline outcomes.\n"
        "3. Identify 3-7 key points as short, factual statements grounded in the text.\n"
        "4. Surface every risk: things going wrong, at risk of failing, or warranting follow-up. Be specific.\n"
        "Do not invent facts. If a category genuinely has no items, return an empty array."
    ),
    output=(
        "Return a single JSON object that matches this exact schema. "
        "Output nothing else: no surrounding text, no markdown fences, no commentary.\n"
        "{\n"
        '  "entities": ["string", ...],\n'
        '  "summary": "string",\n'
        '  "key_points": ["string", ...],\n'
        '  "risks": ["string", ...]\n'
        "}\n"
        "All strings are plain text without markdown. Empty arrays are valid."
    ),
    examples=[
        {
            "input": (
                "Acme Corp closed Q3 with revenue of $4.2M, up 18% YoY. CEO Jane Park "
                "flagged delays in the Phoenix data centre buildout, which could push "
                "the Q4 launch of the Helios product into Q1."
            ),
            "output": (
                '{"entities": ["Acme Corp", "Jane Park", "Phoenix data centre", "Helios"], '
                '"summary": "Acme Corp posted strong Q3 revenue growth of 18% YoY but faces '
                'infrastructure delays. The Phoenix data centre buildout may push the Helios '
                'product launch from Q4 into Q1.", '
                '"key_points": ["Q3 revenue was $4.2M, up 18% year-over-year", '
                '"CEO Jane Park flagged Phoenix data centre buildout delays", '
                '"Helios product launch may slip from Q4 to Q1"], '
                '"risks": ["Phoenix data centre delays threaten the Q4 Helios launch timeline"]}'
            ),
        },
        {
            "input": (
                "Project Atlas hit its February milestone on time. Team morale is high "
                "after the all-hands. No issues to report this cycle."
            ),
            "output": (
                '{"entities": ["Project Atlas"], '
                '"summary": "Project Atlas met its February milestone on schedule with positive '
                'team morale and no issues reported this cycle.", '
                '"key_points": ["February milestone was hit on time", '
                '"Team morale is high following the recent all-hands", '
                '"No issues reported this cycle"], '
                '"risks": []}'
            ),
        },
    ],
)
