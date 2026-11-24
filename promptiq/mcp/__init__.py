"""MCP module exports."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from promptiq.mcp.server import TOOLS, handle_tool_call, run_stdio_mcp_server
else:
    def __getattr__(name):
        if name in ("TOOLS", "handle_tool_call", "run_stdio_mcp_server"):
            from promptiq.mcp import server
            return getattr(server, name)
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["TOOLS", "handle_tool_call", "run_stdio_mcp_server"]
