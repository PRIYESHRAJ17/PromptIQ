"""MCP server runner entrypoint."""

import asyncio
from promptiq.mcp.server import run_stdio_mcp_server

if __name__ == "__main__":
    asyncio.run(run_stdio_mcp_server())
