"""Safe Command-Line Smoke-Test Utility for Hosted Zero-Price Inference.

Sends short, non-sensitive synthetic prompts to verify live hosted connectivity.
Strictly requires explicit opt-in (--opt-in) to prevent accidental quota consumption.
Never logs credentials, authorization headers, or private user data.
"""

import argparse
import asyncio
import sys
import time
from datetime import UTC, datetime
from typing import Any

import httpx

from promptiq.core.config import settings
from promptiq.core.logging import logger
from promptiq.gateway.account_verification import (
    OperatorAccountVerifier,
    OperatorConfirmationRequiredError,
)
from promptiq.gateway.eligibility import verify_zero_price_route

DEFAULT_SYNTHETIC_PROMPTS = {
    "openai/gpt-oss-120b": "Return valid JSON with three fields: greeting, result, and model_role. Set greeting to Hello, result to 437, and model_role to generator. Use 19 multiplied by 23 for the calculation.",
    "openai/gpt-oss-20b": "Return valid JSON with three fields: greeting, result, and model_role. Set greeting to Hello, result to 437, and model_role to critic. Use 19 multiplied by 23 for the calculation.",
}


async def execute_live_smoke_test(
    provider: str = "groq",
    model_id: str = "openai/gpt-oss-120b",
    opt_in: bool = False,
    synthetic_prompt: str | None = None,
    max_tokens: int = 128,
) -> dict[str, Any]:
    """Executes a single live inference smoke test against an approved zero-price provider."""
    # 1. Zero-price invariant check
    verify_zero_price_route(provider=provider, model_id=model_id, price_per_token=0.0)

    prompt = synthetic_prompt or DEFAULT_SYNTHETIC_PROMPTS.get(
        model_id,
        "Return valid JSON with three fields: greeting, result, and model_role. Set greeting to Hello, result to 437, and model_role to specialist. Use 19 multiplied by 23 for the calculation.",
    )

    # 2. Operator account confirmation gate
    try:
        verification_record = OperatorAccountVerifier.verify_operator_account(
            provider=provider,
            model_id=model_id,
            opt_in_confirmed=opt_in,
        )
    except OperatorConfirmationRequiredError as e:
        logger.info("Live smoke test held: %s", e.message)
        return {
            "status": "BLOCKED_EXTERNAL",
            "provider": provider,
            "model_id": model_id,
            "http_status": None,
            "request_id": None,
            "latency_ms": 0.0,
            "tokens_used": 0,
            "success": False,
            "error": e.message,
            "account_verification_state": "UNVERIFIED",
            "notice": "Never substitute mock execution for live verification. Real operator credentials and opt-in required.",
        }

    api_key = settings.effective_groq_api_key if provider.lower() == "groq" else settings.effective_gemini_api_key

    request_time = datetime.now(UTC).isoformat()
    start_time = time.perf_counter()
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(url, headers=headers, json=payload)
            response_time = datetime.now(UTC).isoformat()
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            req_id = resp.headers.get("x-request-id", "unknown")

            rate_limit_headers = {
                "limit_requests": resp.headers.get("x-ratelimit-limit-requests"),
                "limit_tokens": resp.headers.get("x-ratelimit-limit-tokens"),
                "remaining_requests": resp.headers.get("x-ratelimit-remaining-requests"),
                "remaining_tokens": resp.headers.get("x-ratelimit-remaining-tokens"),
                "reset_requests": resp.headers.get("x-ratelimit-reset-requests"),
                "reset_tokens": resp.headers.get("x-ratelimit-reset-tokens"),
            }

            if resp.status_code == 429:
                return {
                    "status": "QUOTA_EXHAUSTED",
                    "provider": provider,
                    "model_id": model_id,
                    "http_status": 429,
                    "request_id": req_id,
                    "request_timestamp": request_time,
                    "response_timestamp": response_time,
                    "latency_ms": round(latency_ms, 2),
                    "tokens_used": 0,
                    "rate_limit_headers": rate_limit_headers,
                    "account_verification_state": verification_record.verification_state,
                    "success": False,
                    "error": "Rate limit / quota reached. Native hard stop verified.",
                }

            resp.raise_for_status()
            data = resp.json()
            usage = data.get("usage", {})
            response_text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

            # Cost classification rule: if only operator attested, status is LIVE_RESPONSE_RECEIVED_COST_UNVERIFIED
            status = (
                "LIVE_VERIFIED_FREE"
                if verification_record.verification_state == "DASHBOARD_EVIDENCED"
                else "LIVE_RESPONSE_RECEIVED_COST_UNVERIFIED"
            )

            return {
                "status": status,
                "provider": provider,
                "model_id": model_id,
                "http_status": resp.status_code,
                "request_id": req_id,
                "request_timestamp": request_time,
                "response_timestamp": response_time,
                "latency_ms": round(latency_ms, 2),
                "tokens_used": usage.get("total_tokens", len(response_text) // 4),
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "rate_limit_headers": rate_limit_headers,
                "response_text": response_text,
                "account_verification_state": verification_record.verification_state,
                "success": True,
            }
        except httpx.HTTPStatusError as e:
            response_time = datetime.now(UTC).isoformat()
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            err_text = e.response.text[:200]
            # Redact any accidental credential reflections
            err_text = err_text.replace(api_key, "[REDACTED_API_KEY]") if api_key else err_text
            return {
                "status": "PROVIDER_HTTP_ERROR",
                "provider": provider,
                "model_id": model_id,
                "http_status": e.response.status_code,
                "request_id": e.response.headers.get("x-request-id"),
                "request_timestamp": request_time,
                "response_timestamp": response_time,
                "latency_ms": round(latency_ms, 2),
                "tokens_used": 0,
                "account_verification_state": verification_record.verification_state,
                "success": False,
                "error": f"HTTP {e.response.status_code}: {err_text}",
            }
        except Exception as e:
            response_time = datetime.now(UTC).isoformat()
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            err_msg = str(e)
            if api_key:
                err_msg = err_msg.replace(api_key, "[REDACTED_API_KEY]")
            return {
                "status": "NETWORK_FAILURE",
                "provider": provider,
                "model_id": model_id,
                "http_status": None,
                "request_id": None,
                "request_timestamp": request_time,
                "response_timestamp": response_time,
                "latency_ms": round(latency_ms, 2),
                "tokens_used": 0,
                "account_verification_state": verification_record.verification_state,
                "success": False,
                "error": err_msg,
            }


def main() -> None:
    """CLI entrypoint for operator smoke testing."""
    parser = argparse.ArgumentParser(description="PromptIQ Safe Hosted Inference Smoke Test")
    parser.add_argument("--opt-in", action="store_true", help="Explicitly opt-in to execute live inference calls.")
    parser.add_argument("--provider", default="groq", choices=["groq", "gemini"], help="Target provider.")
    parser.add_argument("--model", default="openai/gpt-oss-120b", help="Target model identifier.")
    parser.add_argument("--prompt", default=None, help="Custom synthetic prompt to send.")
    parser.add_argument("--max-tokens", type=int, default=128, help="Maximum completion tokens (default: 128).")

    args = parser.parse_args()
    print("=" * 60)
    print("PROMPTIQ LIVE INFERENCE SMOKE TEST")
    print(f"Target Provider: {args.provider}")
    print(f"Target Model:    {args.model}")
    print(f"Opt-In Status:   {args.opt_in}")
    print("=" * 60)

    result = asyncio.run(execute_live_smoke_test(
        provider=args.provider,
        model_id=args.model,
        opt_in=args.opt_in,
        synthetic_prompt=args.prompt,
        max_tokens=args.max_tokens,
    ))

    print(f"\nExecution Result: {result['status']}")
    print(f"Success:          {result['success']}")
    if result.get("http_status"):
        print(f"HTTP Status:      {result['http_status']}")
    if result.get("request_id"):
        print(f"Request ID:       {result['request_id']}")
    if result.get("request_timestamp"):
        print(f"Req Timestamp:    {result['request_timestamp']}")
    if result.get("response_timestamp"):
        print(f"Resp Timestamp:   {result['response_timestamp']}")
    if result.get("latency_ms"):
        print(f"Latency:          {result['latency_ms']} ms")
    if result.get("tokens_used"):
        print(f"Tokens Used:      {result['tokens_used']} (Prompt: {result.get('prompt_tokens', 0)}, Completion: {result.get('completion_tokens', 0)})")
    if result.get("rate_limit_headers"):
        rem_req = result["rate_limit_headers"].get("remaining_requests")
        rem_tok = result["rate_limit_headers"].get("remaining_tokens")
        if rem_req or rem_tok:
            print(f"Rate Limits Rem:  Requests: {rem_req}, Tokens: {rem_tok}")
    if result.get("account_verification_state"):
        print(f"Account State:    {result['account_verification_state']}")
    if result.get("response_text"):
        print(f"Response Text:    {result['response_text']}")
    if result.get("error"):
        print(f"Error / Hold:     {result['error']}")
    if result.get("notice"):
        print(f"Notice:           {result['notice']}")
    print("=" * 60)

    if not result["success"] and result["status"] != "BLOCKED_EXTERNAL":
        sys.exit(1)


if __name__ == "__main__":
    main()
