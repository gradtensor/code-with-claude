"""Reusable agent loop with parallel tool calls, memory, streaming, error handling.

The Agent class is the building block for v3-agent and every later capstone
version. Day 4 will compose multiple Agents into workflow patterns; Day 7 will
add orchestration. The internals stay deliberately simple here: synchronous
public API, ThreadPoolExecutor for tool parallelism, a single summarisation
pass when the conversation outgrows its token budget.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable

from anthropic import Anthropic
from pydantic import BaseModel

from shared.config import CHEAP_MODEL, DEFAULT_MODEL, get_api_key

PRICE_IN, PRICE_OUT = 3.0, 15.0  # Sonnet 4.6 USD per million tokens, rough.

ToolHandler = Callable[[dict[str, Any]], "str | dict[str, Any]"]


@dataclass
class ToolSpec:
    """A tool the agent can call. Handler is invoked with the model's input dict."""

    name: str
    description: str
    input_schema: dict[str, Any]
    handler: ToolHandler


class ToolCallRecord(BaseModel):
    """One tool call as it was executed by the agent."""

    name: str
    input: dict[str, Any]
    output: Any
    duration_ms: float
    started_at_ms: float  # ms since the iteration's start, for parallelism plots
    iteration: int  # which loop iteration this call belonged to, 0-indexed
    error: str | None = None


class AgentResult(BaseModel):
    """The outcome of one Agent.run() turn."""

    final_text: str
    tool_calls: list[ToolCallRecord]
    input_tokens: int
    output_tokens: int
    cost: float
    duration_ms: float
    iterations: int
    memory_summarised: bool = False


def _estimate_tokens(text: str) -> int:
    """Cheap token estimate (chars/4). Avoids a network call per turn."""
    return max(1, len(text) // 4)


def _messages_tokens(messages: list[dict[str, Any]]) -> int:
    """Approximate token count for a list of message dicts."""
    total = 0
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, str):
            total += _estimate_tokens(content)
            continue
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    total += _estimate_tokens(block.get("text", ""))
                elif block.get("type") == "tool_use":
                    total += _estimate_tokens(str(block.get("input", "")))
                elif block.get("type") == "tool_result":
                    c = block.get("content", "")
                    if isinstance(c, str):
                        total += _estimate_tokens(c)
                    else:
                        total += _estimate_tokens(str(c))
            else:
                # SDK Block objects: serialise to string for the estimate.
                total += _estimate_tokens(str(block))
    return total


@dataclass
class Agent:
    """A tool-using agent with conversation memory.

    Construct with a system prompt and a list of ToolSpec. Call .run(message)
    to take one turn. Memory persists across turns until reset_memory() is
    called.
    """

    system_prompt: str
    tools: list[ToolSpec]
    model: str = DEFAULT_MODEL
    max_iterations: int = 10
    memory_token_budget: int = 8000
    client: Anthropic = field(default_factory=lambda: Anthropic(api_key=get_api_key()))
    messages: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._tool_index: dict[str, ToolSpec] = {t.name: t for t in self.tools}
        self._tool_schemas: list[dict[str, Any]] = [
            {"name": t.name, "description": t.description, "input_schema": t.input_schema}
            for t in self.tools
        ]
        self._history_summary: str = ""

    def reset_memory(self) -> None:
        """Drop conversation history. Tools and system prompt are preserved."""
        self.messages = []
        self._history_summary = ""

    def _effective_system(self) -> str:
        if not self._history_summary:
            return self.system_prompt
        return (
            self.system_prompt
            + "\n\n[CONVERSATION SUMMARY of earlier turns: "
            + self._history_summary
            + "]"
        )

    def run(self, user_message: str, stream: bool = False, on_text: Callable[[str], None] | None = None) -> AgentResult:
        """Take one agent turn. on_text(delta) is called per streamed text chunk."""
        started = time.perf_counter()
        memory_summarised = self._maybe_summarise()
        self.messages.append({"role": "user", "content": user_message})

        tool_calls: list[ToolCallRecord] = []
        in_total = 0
        out_total = 0
        final_text = ""
        iterations = 0

        for iteration in range(self.max_iterations):
            iterations = iteration + 1
            iter_started_perf = time.perf_counter()
            if stream:
                msg, text_streamed = self._call_streaming(on_text)
            else:
                msg = self.client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    system=self._effective_system(),
                    tools=self._tool_schemas,
                    messages=self.messages,
                )
                text_streamed = "".join(b.text for b in msg.content if b.type == "text")
            in_total += msg.usage.input_tokens
            out_total += msg.usage.output_tokens

            if msg.stop_reason != "tool_use":
                final_text = text_streamed
                self.messages.append({"role": "assistant", "content": msg.content})
                break

            self.messages.append({"role": "assistant", "content": msg.content})
            tool_use_blocks = [b for b in msg.content if b.type == "tool_use"]
            iter_records, tool_results = self._execute_tools_in_parallel(
                tool_use_blocks, iter_started_perf, iteration
            )
            tool_calls.extend(iter_records)
            self.messages.append({"role": "user", "content": tool_results})
        else:
            final_text = f"(hit MAX_ITERATIONS={self.max_iterations})"

        duration_ms = (time.perf_counter() - started) * 1000
        cost = (in_total * PRICE_IN + out_total * PRICE_OUT) / 1_000_000
        return AgentResult(
            final_text=final_text,
            tool_calls=tool_calls,
            input_tokens=in_total,
            output_tokens=out_total,
            cost=cost,
            duration_ms=duration_ms,
            iterations=iterations,
            memory_summarised=memory_summarised,
        )

    def _call_streaming(self, on_text: Callable[[str], None] | None) -> tuple[Any, str]:
        """Stream one response and return (final_message, accumulated_text)."""
        text_buf: list[str] = []
        with self.client.messages.stream(
            model=self.model,
            max_tokens=2048,
            system=self._effective_system(),
            tools=self._tool_schemas,
            messages=self.messages,
        ) as stream:
            for delta in stream.text_stream:
                text_buf.append(delta)
                if on_text is not None:
                    on_text(delta)
            message = stream.get_final_message()
        return message, "".join(text_buf)

    def _execute_tools_in_parallel(
        self, tool_use_blocks: list[Any], iter_started_perf: float, iteration: int
    ) -> tuple[list[ToolCallRecord], list[dict[str, Any]]]:
        """Run every tool_use block concurrently. Returns (records, tool_result blocks)."""
        records_by_id: dict[str, ToolCallRecord] = {}
        results_by_id: dict[str, dict[str, Any]] = {}

        def _one(block: Any) -> tuple[str, ToolCallRecord, dict[str, Any]]:
            started_at_ms = (time.perf_counter() - iter_started_perf) * 1000
            t0 = time.perf_counter()
            error: str | None = None
            try:
                spec = self._tool_index.get(block.name)
                if spec is None:
                    raise KeyError(f"unknown tool '{block.name}'")
                output = spec.handler(dict(block.input))
                content_str = output if isinstance(output, str) else str(output)
                is_error = False
            except Exception as e:
                output = None
                content_str = f"ERROR: {type(e).__name__}: {e}"
                error = content_str
                is_error = True
            duration_ms = (time.perf_counter() - t0) * 1000
            record = ToolCallRecord(
                name=block.name,
                input=dict(block.input),
                output=output if not is_error else None,
                duration_ms=duration_ms,
                started_at_ms=started_at_ms,
                iteration=iteration,
                error=error,
            )
            result_block = {
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": content_str,
                "is_error": is_error,
            }
            return block.id, record, result_block

        with ThreadPoolExecutor(max_workers=max(1, len(tool_use_blocks))) as pool:
            futures = [pool.submit(_one, b) for b in tool_use_blocks]
            for future in as_completed(futures):
                tid, record, result_block = future.result()
                records_by_id[tid] = record
                results_by_id[tid] = result_block

        # Preserve the model's original tool_use order in the response we send back.
        ordered_records = [records_by_id[b.id] for b in tool_use_blocks]
        ordered_results = [results_by_id[b.id] for b in tool_use_blocks]
        return ordered_records, ordered_results

    def _maybe_summarise(self) -> bool:
        """Summarise older turns if total history exceeds the token budget.

        Cuts only at end-of-turn boundaries (assistant messages with no tool_use
        blocks) so the surviving messages list is always a valid Anthropic API
        history. Summary text accumulates into self._history_summary and is
        injected via _effective_system(). The messages list never gets a fake
        synthetic message inserted.
        """
        if len(self.messages) < 4:
            return False
        if _messages_tokens(self.messages) <= self.memory_token_budget:
            return False

        cut = self._find_turn_boundary()
        if cut is None or cut < 2:
            return False  # nothing safely summarisable yet

        older = self.messages[:cut]
        recent = self.messages[cut:]
        summary_text = self._summarise_older(older)
        if self._history_summary:
            self._history_summary += " " + summary_text
        else:
            self._history_summary = summary_text
        self.messages = recent
        return True

    def _find_turn_boundary(self) -> int | None:
        """Find the latest safe cut point: just past an assistant text-only message.

        Walks backwards from messages[-2] (we need at least one message after the
        cut) to find the nearest assistant message whose content has no tool_use
        block. Returns the index just past that message, or None if no safe cut.
        """
        for i in range(len(self.messages) - 2, -1, -1):
            m = self.messages[i]
            if m["role"] != "assistant":
                continue
            content = m["content"]
            if isinstance(content, str):
                return i + 1
            has_tool_use = any(
                (getattr(b, "type", None) or (b.get("type") if isinstance(b, dict) else None))
                == "tool_use"
                for b in content
            )
            if not has_tool_use:
                return i + 1
        return None

    def _summarise_older(self, older: list[dict[str, Any]]) -> str:
        """Ask a cheap model to condense older turns into one paragraph."""
        rendered = []
        for m in older:
            role = m["role"]
            content = m["content"]
            if isinstance(content, str):
                rendered.append(f"{role.upper()}: {content}")
                continue
            parts: list[str] = []
            for block in content:
                btype = getattr(block, "type", None) or (block.get("type") if isinstance(block, dict) else None)
                if btype == "text":
                    text = getattr(block, "text", None) or block.get("text", "")
                    parts.append(text)
                elif btype == "tool_use":
                    name = getattr(block, "name", None) or block.get("name", "")
                    parts.append(f"[called tool {name}]")
                elif btype == "tool_result":
                    parts.append("[tool result]")
            rendered.append(f"{role.upper()}: {' '.join(parts)}")
        joined = "\n".join(rendered)
        msg = self.client.messages.create(
            model=CHEAP_MODEL,
            max_tokens=400,
            system=(
                "Summarise the following agent conversation in one short paragraph. "
                "Capture what was asked, what was answered, and which tools were used. "
                "Preserve any specific numbers, scheme names, or entity names mentioned."
            ),
            messages=[{"role": "user", "content": joined}],
        )
        return "".join(b.text for b in msg.content if b.type == "text").strip()
