# PromptIQ Plugin for Cursor IDE

Full workspace integration package for Cursor AI IDE.

## Installation
1. Copy `.cursorrules` to your project root.
2. In Cursor Settings -> Features -> MCP, add:
   - Name: `promptiq`
   - Type: `command`
   - Command: `python -m promptiq.mcp.server`
