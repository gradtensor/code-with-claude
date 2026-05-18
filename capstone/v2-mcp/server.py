"""MCP server exposing Budget speech sections as tools and resources.

Two tools:
  - list_budget_sections() -> all section metadata.
  - read_budget_section(section_id) -> the raw text of one section.

Sections are also exposed as MCP resources with URIs `budget://<section_id>`
so MCP-aware clients (Claude Desktop, MCP Inspector) can browse them.

Stdio transport is reserved for the JSON-RPC protocol. All logging must go
to stderr. Never print to stdout.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("budget-mcp")

SECTIONS_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures" / "budget-2026" / "sections"
INDEX_PATH = SECTIONS_DIR / "index.json"


def _load_index() -> list[dict]:
    if not INDEX_PATH.exists():
        raise FileNotFoundError(
            f"section index missing at {INDEX_PATH}. "
            "Run `uv run python fixtures/budget-2026/split_sections.py` first."
        )
    return json.loads(INDEX_PATH.read_text())


INDEX: list[dict] = _load_index()
BY_ID: dict[str, dict] = {s["id"]: s for s in INDEX}
log.info("loaded %d sections from %s", len(INDEX), INDEX_PATH)

mcp = FastMCP("budget-2026")


@mcp.tool()
def list_budget_sections() -> list[dict]:
    """List every section of the Union Budget 2026-27 speech.

    Returns a list of objects with id, title, summary, and char_count for
    each section. Use this first to decide which sections to read.
    """
    return [
        {"id": s["id"], "title": s["title"], "summary": s["summary"], "char_count": s["char_count"]}
        for s in INDEX
    ]


@mcp.tool()
def read_budget_section(section_id: str) -> str:
    """Return the raw text of one section of the Budget speech.

    Pass a section_id from list_budget_sections. Raises ValueError if the
    id is unknown.
    """
    section = BY_ID.get(section_id)
    if section is None:
        raise ValueError(
            f"unknown section_id '{section_id}'. "
            f"Call list_budget_sections to see valid ids."
        )
    path = SECTIONS_DIR / section["filename"]
    return path.read_text()


for _s in INDEX:
    _sid = _s["id"]
    _title = _s["title"]
    _summary = _s["summary"]

    def _make_reader(sid: str):
        def _read() -> str:
            return (SECTIONS_DIR / BY_ID[sid]["filename"]).read_text()

        return _read

    mcp.resource(
        uri=f"budget://{_sid}",
        name=_title,
        description=_summary,
        mime_type="text/plain",
    )(_make_reader(_sid))


if __name__ == "__main__":
    log.info("starting budget-2026 MCP server on stdio")
    mcp.run(transport="stdio")
