# PromptIQ Antigravity Native Plugin

Official PromptIQ intelligence and orchestration plugin for Google Antigravity.

## Features
- **Project Constitution Sync**: Access and propose changes to persistent architectural state.
- **Task Compiler**: Transform user intent into Antigravity instruction packages across 10 specialized task families.
- **Forensic Autopsy**: Dissect prompts against 21 adversarial failure categories before executing.
- **Evidence Graph**: Query citations with character-exact offsets.

## Installation
```bash
agy plugin install promptiq
# Or load directly from workspace directory
```

## Configuration
Configure `mcp.json` or environment variables:
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
