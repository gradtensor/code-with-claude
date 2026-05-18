"""Three LLM-backed analyst tools.

These wrap a Claude call inside a tool. The agent treats them like any other
tool. The teaching point is that tools can be anything callable, including
another LLM call, which means an agent's capabilities scale with how
specialised its sub-prompts are.

Each tool returns JSON-parsable text so the calling agent can quote it back
into its own response.
"""

from __future__ import annotations

import json
from typing import Any

from shared.agent import ToolSpec
from shared.client import chat
from shared.config import CHEAP_MODEL


def _extract_json_array(text: str) -> list[dict[str, Any]]:
    """Pull a JSON array out of a model response, tolerating fenced blocks."""
    s = text.strip()
    if s.startswith("```"):
        s = s.strip("`").strip()
        if s.lower().startswith("json"):
            s = s[4:].strip()
    return json.loads(s)


# ----- extract_entities -----------------------------------------------------

_ENTITIES_SYSTEM = (
    "You extract named entities from Indian Union Budget text. "
    "Return a JSON array of objects with keys 'name', 'type', 'context'. "
    "type is one of: person, organisation, scheme, programme, place. "
    "context is a 5-12 word phrase from the source describing what the entity does or got. "
    "No markdown, no commentary, only the JSON array."
)


def extract_entities(text: str) -> list[dict[str, Any]]:
    """Return a list of named entities found in the given Budget text."""
    msg = chat(
        messages=[{"role": "user", "content": text}],
        system=_ENTITIES_SYSTEM,
        model=CHEAP_MODEL,
        max_tokens=2048,
    )
    return _extract_json_array(msg.content[0].text)


def _handle_extract_entities(args: dict[str, Any]) -> str:
    return json.dumps(extract_entities(args["text"]))


extract_entities_tool = ToolSpec(
    name="extract_entities",
    description=(
        "Extract named entities (people, organisations, schemes, programmes, places) from "
        "a passage of Budget text. Returns a JSON array. Use after fetching a section."
    ),
    input_schema={
        "type": "object",
        "properties": {"text": {"type": "string", "description": "The Budget text to scan."}},
        "required": ["text"],
    },
    handler=_handle_extract_entities,
)


# ----- extract_allocations --------------------------------------------------

_ALLOCATIONS_SYSTEM = (
    "You extract rupee allocations from Indian Union Budget text. "
    "Return a JSON array of objects with keys 'amount', 'purpose', 'scheme'. "
    "amount is the original string including ₹ and crore/lakh (e.g. '₹10,000 crore'). "
    "purpose is a 5-15 word phrase describing what the amount is for. "
    "scheme is the named scheme if there is one, otherwise null. "
    "No markdown, no commentary, only the JSON array. Empty array if no allocations."
)


def extract_allocations(text: str) -> list[dict[str, Any]]:
    """Return ₹ allocations found in the text."""
    msg = chat(
        messages=[{"role": "user", "content": text}],
        system=_ALLOCATIONS_SYSTEM,
        model=CHEAP_MODEL,
        max_tokens=2048,
    )
    return _extract_json_array(msg.content[0].text)


def _handle_extract_allocations(args: dict[str, Any]) -> str:
    return json.dumps(extract_allocations(args["text"]))


extract_allocations_tool = ToolSpec(
    name="extract_allocations",
    description=(
        "Extract rupee allocations (₹ amounts with purpose and scheme) from a passage of "
        "Budget text. Returns a JSON array. Amounts stay as strings (e.g. '₹10,000 crore')."
    ),
    input_schema={
        "type": "object",
        "properties": {"text": {"type": "string", "description": "The Budget text to scan."}},
        "required": ["text"],
    },
    handler=_handle_extract_allocations,
)


# ----- find_cross_references ------------------------------------------------

_CROSSREF_SYSTEM = (
    "You decide which sections of an Indian Budget speech are related to a given query "
    "and current section. You will receive: a query, the current section id, and a list of "
    "all section objects with id/title/summary. Return a JSON array of related sections "
    "as objects with keys 'section_id', 'title', 'relevance_reason'. "
    "Only include sections OTHER than the current_section_id. "
    "Pick at most 5 sections, ordered by relevance. "
    "relevance_reason is a 5-15 word phrase. "
    "No markdown, no commentary, only the JSON array."
)


def find_cross_references(
    query: str, current_section_id: str, all_sections: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Return related sections from the section index."""
    user_payload = json.dumps(
        {"query": query, "current_section_id": current_section_id, "all_sections": all_sections}
    )
    msg = chat(
        messages=[{"role": "user", "content": user_payload}],
        system=_CROSSREF_SYSTEM,
        model=CHEAP_MODEL,
        max_tokens=2048,
    )
    return _extract_json_array(msg.content[0].text)


def make_find_cross_references_tool(all_sections: list[dict[str, Any]]) -> ToolSpec:
    """Build a ToolSpec with the section index closed over in the handler."""

    def _handle(args: dict[str, Any]) -> str:
        return json.dumps(
            find_cross_references(args["query"], args["current_section_id"], all_sections)
        )

    return ToolSpec(
        name="find_cross_references",
        description=(
            "Given a query and the section_id you are currently reading, suggest up to 5 "
            "OTHER Budget sections that are related and worth fetching. Use this when a "
            "question may span sectors (e.g. textile + customs, R&D + tax incentives)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The user's question or topic."},
                "current_section_id": {
                    "type": "string",
                    "description": "The id of the section you are currently reading.",
                },
            },
            "required": ["query", "current_section_id"],
        },
        handler=_handle,
    )


ANALYST_TOOLS: list[ToolSpec] = [extract_entities_tool, extract_allocations_tool]
