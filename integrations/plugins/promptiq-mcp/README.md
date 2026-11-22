# PromptIQ Universal MCP Server

RFC-compliant Model Context Protocol server exposing all PromptIQ intelligence tools over STDIO or SSE.

## Usage
Add to any MCP-compatible client:
```json
{
  "mcpServers": {
    "promptiq": {
      "command": "python",
      "args": ["-m", "promptiq.mcp.server"]
    }
  }
}
```
