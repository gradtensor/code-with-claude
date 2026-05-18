"""Sync ToolSpec adapter for MCP servers.

The MCP Python SDK is async. Our Agent loop is sync (ThreadPoolExecutor for
parallelism). We bridge by running a dedicated asyncio event loop in a
background thread that keeps the MCP session alive across many tool calls.
Each tool handler is a sync function that submits a coroutine via
`asyncio.run_coroutine_threadsafe` and blocks on the result.

This is the cleanest place to put the threading-meets-asyncio dance. Callers
of MCPClient see plain ToolSpecs.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from shared.agent import ToolSpec


class MCPClient:
    """Manages a long-lived MCP session on a background event loop.

    Usage:
        with MCPClient(server_params) as mcp:
            tools = mcp.tool_specs()
            # tools are regular ToolSpec instances usable by the Agent
    """

    def __init__(self, server_params: StdioServerParameters) -> None:
        self.server_params = server_params
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._session: ClientSession | None = None
        self._mcp_tools: list[Any] = []
        self._ready = threading.Event()
        self._shutdown = threading.Event()
        self._startup_error: BaseException | None = None

    def __enter__(self) -> "MCPClient":
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._ready.wait()
        if self._startup_error is not None:
            raise self._startup_error
        return self

    def __exit__(self, *exc_info: Any) -> None:
        if self._loop is not None and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._shutdown.set)
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _run_loop(self) -> None:
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._main())
        except BaseException as e:
            self._startup_error = e
            self._ready.set()

    async def _main(self) -> None:
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                self._session = session
                self._mcp_tools = (await session.list_tools()).tools
                self._ready.set()
                # Block until __exit__ flips the shutdown event.
                while not self._shutdown.is_set():
                    await asyncio.sleep(0.05)

    def tool_specs(self) -> list[ToolSpec]:
        """Return one ToolSpec per MCP tool, with a sync handler over the session."""
        return [self._adapt(t) for t in self._mcp_tools]

    def _adapt(self, mcp_tool: Any) -> ToolSpec:
        name = mcp_tool.name

        def _handle(args: dict[str, Any]) -> str:
            assert self._session is not None and self._loop is not None
            fut = asyncio.run_coroutine_threadsafe(
                self._session.call_tool(name, arguments=args), self._loop
            )
            result = fut.result()
            return "\n".join(c.text for c in result.content if hasattr(c, "text"))

        return ToolSpec(
            name=name,
            description=mcp_tool.description or "",
            input_schema=mcp_tool.inputSchema,
            handler=_handle,
        )
