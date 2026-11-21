"""Local stdio bridge adapter for connecting local agent tools to the Cloud-Hosted Remote MCP Service.

This client bridge runs lightweight stdio translation locally while all state,
project memory, and zero-price inference execute remotely on the PromptIQ Cloud Service.
"""

import argparse
import json
import os
import sys
import urllib.request


def run_bridge(remote_url: str, auth_token: str | None = None):
    """Bridges stdin/stdout JSON-RPC to the remote PromptIQ MCP HTTP RPC endpoint."""
    if not remote_url.startswith(("http://", "https://")):
        raise ValueError(f"Invalid scheme for remote URL: {remote_url}. Only http:// and https:// are permitted.")

    token = auth_token or os.environ.get("PROMPTIQ_TOKEN")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    while True:
        line = sys.stdin.readline()
        if not line:
            break

        line_str = line.strip()
        if not line_str:
            continue

        # Extract inbound request ID so errors match the pending JSON-RPC request
        req_id = None
        try:
            parsed_req = json.loads(line_str)
            if isinstance(parsed_req, dict):
                req_id = parsed_req.get("id")
        except (json.JSONDecodeError, UnicodeDecodeError):
            req_id = None

        try:
            req_data = line_str.encode("utf-8")
            http_req = urllib.request.Request(remote_url, data=req_data, headers=headers, method="POST")

            with urllib.request.urlopen(http_req, timeout=30.0) as resp:  # nosec B310
                resp_bytes = resp.read()
                sys.stdout.buffer.write(resp_bytes + b"\n")
                sys.stdout.buffer.flush()

        except Exception as e:
            err_resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": f"Bridge error calling remote MCP: {e}"},
            }
            sys.stdout.buffer.write((json.dumps(err_resp) + "\n").encode("utf-8"))
            sys.stdout.buffer.flush()


def main():
    parser = argparse.ArgumentParser(description="PromptIQ Local Stdio Bridge to Cloud-Hosted MCP Service")
    parser.add_argument("--url", default="http://127.0.0.1:8000/api/v1/mcp", help="Remote MCP Streamable HTTP URL")
    parser.add_argument(
        "--token",
        default=None,
        help="User JWT access token for cloud authentication (can also use PROMPTIQ_TOKEN env var)",
    )
    args = parser.parse_args()

    run_bridge(args.url, args.token)


if __name__ == "__main__":
    main()
