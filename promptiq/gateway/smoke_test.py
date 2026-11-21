"""Safe Command-Line Smoke-Test Utility for Hosted Zero-Price Inference.

Sends short, non-sensitive synthetic prompts to verify live hosted connectivity.
Strictly requires explicit opt-in (--opt-in) to prevent accidental quota consumption.
Never logs credentials, authorization headers, or private user data.
"""

import argparse
import asyncio
import sys
import time
from typing import Any

import httpx

from promptiq.core.config import settings
from promptiq.core.logging import logger
from promptiq.gateway.account_verification import (
    OperatorAccountVerifier,
    OperatorConfirmationRequiredError,
)
from promptiq.gateway.eligibility import verify_zero_price_route


async def execute_live_smoke_test(
    provider: str = "groq",
    model_id: str = "openai/gpt-oss-120b",
    opt_in: bool = False,
    synthetic_prompt: str = "Respond with the single word: OK",
) -> dict[str, Any]:
    """Executes a single live inference smoke test against an approved zero-price provider."""
    # 1. Zero-price invariant check
    verify_zero_price_route(provider=provider, model_id=model_id, price_per_token=0.0)

    # 2. Operator account confirmation gate
    try:
        OperatorAccountVerifier.verify_operator_account(
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
            "notice": "Never substitute mock execution for live verification. Real operator credentials and opt-in required.",
        }

    api_key = settings.effective_groq_api_key if provider.lower() == "groq" else settings.effective_gemini_api_key

    start_time = time.perf_counter()
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": synthetic_prompt}],
        "temperature": 0.0,
        "max_tokens": 16,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(url, headers=headers, json=payload)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            req_id = resp.headers.get("x-request-id", "unknown")
            ratelimit_rem = resp.headers.get("x-ratelimit-remaining-requests")

            if resp.status_code == 429:
                return {
                    "status": "QUOTA_EXHAUSTED",
                    "provider": provider,
                    "model_id": model_id,
                    "http_status": 429,
                    "request_id": req_id,
                    "latency_ms": round(latency_ms, 2),
                    "tokens_used": 0,
                    "success": False,
                    "error": "Rate limit / quota reached. Native hard stop verified.",
                }

            resp.raise_for_status()
            data = resp.json()
            usage = data.get("usage", {})
            response_text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

            return {
                "status": "VERIFIED_LIVE",
                "provider": provider,
                "model_id": model_id,
                "http_status": resp.status_code,
                "request_id": req_id,
                "latency_ms": round(latency_ms, 2),
                "tokens_used": usage.get("total_tokens", len(response_text) // 4),
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "rate_limit_remaining": ratelimit_rem,
                "response_text": response_text[:100],
                "success": True,
            }
        except httpx.HTTPStatusError as e:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "status": "PROVIDER_HTTP_ERROR",
                "provider": provider,
                "model_id": model_id,
                "http_status": e.response.status_code,
                "request_id": e.response.headers.get("x-request-id"),
                "latency_ms": round(latency_ms, 2),
                "tokens_used": 0,
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            }
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "status": "NETWORK_FAILURE",
                "provider": provider,
                "model_id": model_id,
                "http_status": None,
                "request_id": None,
                "latency_ms": round(latency_ms, 2),
                "tokens_used": 0,
                "success": False,
                "error": str(e),
            }


def main() -> None:
    """CLI entrypoint for operator smoke testing."""
    parser = argparse.ArgumentParser(description="PromptIQ Safe Hosted Inference Smoke Test")
    parser.add_argument("--opt-in", action="store_true", help="Explicitly opt-in to execute live inference calls.")
    parser.add_argument("--provider", default="groq", choices=["groq", "gemini"], help="Target provider.")
    parser.add_argument("--model", default="openai/gpt-oss-120b", help="Target model identifier.")

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
    ))

    print(f"\nExecution Result: {result['status']}")
    print(f"Success:          {result['success']}")
    if result.get("http_status"):
        print(f"HTTP Status:      {result['http_status']}")
    if result.get("request_id"):
        print(f"Request ID:       {result['request_id']}")
    if result.get("latency_ms"):
        print(f"Latency:          {result['latency_ms']} ms")
    if result.get("tokens_used"):
        print(f"Tokens Used:      {result['tokens_used']}")
    if result.get("error"):
        print(f"Error / Hold:     {result['error']}")
    if result.get("notice"):
        print(f"Notice:           {result['notice']}")
    print("=" * 60)

    if not result["success"] and result["status"] != "BLOCKED_EXTERNAL":
        sys.exit(1)


if __name__ == "__main__":
    main()
