"""Remote Model Context Protocol (MCP) HTTP and Server-Sent Events (SSE) Transport."""

import asyncio
import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.api.deps import get_current_user, get_db
from promptiq.core.logging import logger
from promptiq.mcp.server import TOOLS, handle_tool_call
from promptiq.models.user import User

router = APIRouter(prefix="/mcp", tags=["Model Context Protocol (Remote)"])

# Active SSE connection sessions: sessionId -> {"queue": asyncio.Queue, "user_id": str}
_active_sse_sessions: dict[str, dict[str, Any]] = {}


@router.get("/sse")
async def mcp_sse_endpoint(
    request: Request,
    user: User = Depends(get_current_user),
):
    """Establishes a persistent Server-Sent Events (SSE) downstream channel for remote MCP clients."""
    session_id = str(uuid.uuid4())
    message_queue: asyncio.Queue = asyncio.Queue()
    _active_sse_sessions[session_id] = {
        "queue": message_queue,
        "user_id": user.id,
    }

    async def sse_event_stream():
        try:
            # First event tells the MCP client where to POST messages
            post_endpoint = f"/api/v1/mcp/messages?sessionId={session_id}"
            yield f"event: endpoint\ndata: {post_endpoint}\n\n"

            while True:
                if await request.is_disconnected():
                    break
                try:
                    # Wait for outgoing message with timeout to permit keepalive ping
                    msg = await asyncio.wait_for(message_queue.get(), timeout=15.0)
                    yield f"event: message\ndata: {json.dumps(msg)}\n\n"
                except TimeoutError:
                    # SSE Keepalive comment
                    yield ": ping\n\n"
        finally:
            _active_sse_sessions.pop(session_id, None)

    return StreamingResponse(
        sse_event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/messages")
async def mcp_receive_message(
    request: Request,
    sessionId: str = Query(..., description="Active MCP session ID from SSE handshake"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Receives JSON-RPC messages from remote MCP client and routes responses back via SSE."""
    session_info = _active_sse_sessions.get(sessionId)
    if not session_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP SSE session not found or expired. Re-establish /sse connection.",
        )

    if session_info["user_id"] != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: MCP SSE session belongs to another tenant.",
        )

    queue = session_info["queue"]

    try:
        rpc_req = await request.json()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON: {e}")

    req_id = rpc_req.get("id")
    method = rpc_req.get("method")
    params = rpc_req.get("params", {})

    response: dict[str, Any] = {"jsonrpc": "2.0", "id": req_id}

    try:
        if method == "initialize":
            response["result"] = {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "promptiq-cloud-mcp", "version": "0.2.0"},
                "capabilities": {"tools": {}},
            }
        elif method == "notifications/initialized":
            return {"status": "acknowledged"}
        elif method == "ping":
            response["result"] = {}
        elif method == "tools/list":
            response["result"] = {"tools": TOOLS}
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            result_data = await handle_tool_call(tool_name, arguments, user.id, db=db)
            response["result"] = {
                "content": [{"type": "text", "text": json.dumps(result_data, indent=2)}]
            }
        else:
            response["error"] = {"code": -32601, "message": f"Method not found: '{method}'"}
    except Exception as err:
        logger.error(f"Remote MCP execution error: {err}")
        response["error"] = {"code": -32603, "message": str(err)}

    # Send response back to client over the persistent SSE stream
    await queue.put(response)
    return {"status": "enqueued"}


@router.post("/rpc")
async def mcp_stateless_rpc(
    rpc_req: dict[str, Any],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stateless HTTP POST JSON-RPC 2.0 endpoint for direct remote agent MCP calls."""
    req_id = rpc_req.get("id")
    method = rpc_req.get("method")
    params = rpc_req.get("params", {})

    response: dict[str, Any] = {"jsonrpc": "2.0", "id": req_id}

    try:
        if method == "initialize":
            response["result"] = {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "promptiq-cloud-mcp", "version": "0.2.0"},
                "capabilities": {"tools": {}},
            }
        elif method == "notifications/initialized":
            response["result"] = {}
        elif method == "ping":
            response["result"] = {}
        elif method == "tools/list":
            response["result"] = {"tools": TOOLS}
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            result_data = await handle_tool_call(tool_name, arguments, user.id, db=db)
            response["result"] = {
                "content": [{"type": "text", "text": json.dumps(result_data, indent=2)}]
            }
        else:
            response["error"] = {"code": -32601, "message": f"Method not found: '{method}'"}

        return response
    except Exception as e:
        logger.error(f"Remote MCP RPC error: {e}")
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32603, "message": str(e)},
        }
