"""Remote Model Context Protocol (MCP) Transport.

Implements the official Model Context Protocol Streamable HTTP transport as primary,
with backward-compatible support for legacy dual-endpoint SSE.
"""

import asyncio
import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.api.deps import get_current_user, get_db
from promptiq.core.logging import logger
from promptiq.mcp.server import TOOLS, handle_tool_call
from promptiq.models.user import User

router = APIRouter(prefix="/mcp", tags=["Model Context Protocol (Remote)"])

# Legacy SSE active sessions: sessionId -> {"queue": asyncio.Queue, "user_id": str}
_active_sse_sessions: dict[str, dict[str, Any]] = {}


def validate_mcp_origin(request: Request) -> None:
    """Validates Origin header to prevent DNS rebinding attacks as required by the MCP specification."""
    origin = request.headers.get("origin")
    if origin:
        origin_lower = origin.lower()
        # Disallow untrusted origins or suspicious protocols
        if not (
            origin_lower.startswith(
                ("http://localhost", "http://127.0.0.1", "https://", "vscode-webview://")
            )
            or ".google.dev" in origin_lower
            or ".run.app" in origin_lower
        ):
            logger.warning(f"Rejected MCP request with suspicious origin: {origin}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Origin '{origin}' is not permitted by MCP DNS rebinding security policy.",
            )


async def execute_mcp_rpc(
    rpc_req: dict[str, Any],
    user_id: str,
    db: AsyncSession,
) -> dict[str, Any]:
    """Stateless execution of an MCP JSON-RPC 2.0 request against PromptIQ tools."""
    req_id = rpc_req.get("id")
    method = rpc_req.get("method")
    params = rpc_req.get("params", {})

    response: dict[str, Any] = {"jsonrpc": "2.0", "id": req_id}

    if method == "initialize":
        response["result"] = {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "promptiq-cloud-mcp", "version": "0.3.0"},
            "capabilities": {
                "tools": {"listChanged": False},
                "logging": {},
            },
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
        result_data = await handle_tool_call(tool_name, arguments, user_id, db=db)
        response["result"] = {
            "content": [{"type": "text", "text": json.dumps(result_data, indent=2)}]
        }
    else:
        response["error"] = {"code": -32601, "message": f"Method not found: '{method}'"}

    return response


# =========================================================================
# PRIMARY TRANSPORT: Modern Streamable HTTP (Stateless, No Affinity Needed)
# =========================================================================
@router.post("")
@router.post("/")
@router.post("/http")
@router.post("/rpc")
async def mcp_streamable_http_endpoint(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Primary official Model Context Protocol (MCP) Streamable HTTP Transport endpoint.

    Strictly stateless and instance-independent: consecutive requests can hit any Cloud Run
    container instance without session loss or routing errors.
    """
    validate_mcp_origin(request)

    try:
        rpc_req = await request.json()
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"},
            },
        )

    accept_header = request.headers.get("accept", "").lower()

    # If client explicitly requests text/event-stream (request-scoped SSE stream)
    if "text/event-stream" in accept_header and "application/json" not in accept_header:

        async def event_generator():
            try:
                rpc_resp = await execute_mcp_rpc(rpc_req, user.id, db)
                yield f"event: message\ndata: {json.dumps(rpc_resp)}\n\n"
            except Exception as ex:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": rpc_req.get("id"),
                    "error": {"code": -32603, "message": str(ex)},
                }
                yield f"event: message\ndata: {json.dumps(err_resp)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Standard Streamable HTTP JSON response
    try:
        rpc_resp = await execute_mcp_rpc(rpc_req, user.id, db)
        return JSONResponse(content=rpc_resp)
    except Exception as e:
        logger.error(f"MCP execution error: {e}")
        return JSONResponse(
            status_code=200,
            content={
                "jsonrpc": "2.0",
                "id": rpc_req.get("id"),
                "error": {"code": -32603, "message": str(e)},
            },
        )


# =========================================================================
# LEGACY TRANSPORT: Dual-Endpoint SSE (Retained for Backward Compatibility)
# =========================================================================
@router.get("/sse")
async def mcp_legacy_sse_endpoint(
    request: Request,
    user: User = Depends(get_current_user),
):
    """Legacy dual-endpoint SSE GET channel for backward compatibility with older MCP clients."""
    validate_mcp_origin(request)
    session_id = str(uuid.uuid4())
    message_queue: asyncio.Queue = asyncio.Queue()
    _active_sse_sessions[session_id] = {
        "queue": message_queue,
        "user_id": user.id,
    }

    async def sse_event_stream():
        try:
            post_endpoint = f"/api/v1/mcp/messages?sessionId={session_id}"
            yield f"event: endpoint\ndata: {post_endpoint}\n\n"

            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(message_queue.get(), timeout=15.0)
                    yield f"event: message\ndata: {json.dumps(msg)}\n\n"
                except TimeoutError:
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
async def mcp_legacy_receive_message(
    request: Request,
    sessionId: str = Query(..., description="Active MCP session ID from SSE handshake"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Legacy dual-endpoint message poster routing response back through SSE stream."""
    validate_mcp_origin(request)
    session_info = _active_sse_sessions.get(sessionId)
    if not session_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP SSE session not found or expired. Use primary Streamable HTTP endpoint instead.",
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

    try:
        response = await execute_mcp_rpc(rpc_req, user.id, db)
    except Exception as err:
        logger.error(f"Remote MCP execution error: {err}")
        response = {
            "jsonrpc": "2.0",
            "id": rpc_req.get("id"),
            "error": {"code": -32603, "message": str(err)},
        }

    await queue.put(response)
    return {"status": "enqueued"}
