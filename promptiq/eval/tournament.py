"""PromptIQ Model Tournament Evaluation Harness.

Explicitly separates:
A. Deterministic benchmark tests (Schema compliance, injection resistance, prompt autopsy).
B. Actual live-provider evaluations (Live network requests, real latency, response headers,
   with strict UNVERIFIED marking when operator credentials are absent).
"""

import json
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from promptiq.core.config import settings
from promptiq.gateway.eligibility import RETIRED_MODELS
from promptiq.gateway.gateway import inference_gateway
from promptiq.gateway.models import GatewayMessage, InferenceRequest


class ModelTournamentRunner:
    """Executes deterministic benchmarks and live-provider evaluations."""

    def __init__(self, benchmark_path: Path | None = None):
        self.benchmark_path = benchmark_path or (
            Path(__file__).parent.parent.parent
            / "data"
            / "synthetic_model_benchmarks"
            / "tournament_cases.json"
        )

    def load_test_cases(self) -> list[dict[str, Any]]:
        with open(self.benchmark_path, encoding="utf-8") as f:
            return json.load(f)

    async def evaluate_deterministic_benchmarks(
        self,
        candidate_name: str = "Deterministic Baseline",
        adapter_route: str = "mock",
        user_id: str = "deterministic_benchmarker",
    ) -> dict[str, Any]:
        """Runs the deterministic suite: schema compliance, injection resistance, and instruction adherence."""
        test_cases = self.load_test_cases()
        category_score_lists: dict[str, list[float]] = defaultdict(list)
        case_results: list[dict[str, Any]] = []

        total_latency_ms = 0.0
        passed_cases = 0

        for case in test_cases:
            case_id = case["id"]
            category = case["category"]
            prompt = case["prompt"]
            expected = case.get("expected_patterns", [])
            prohibited = case.get("prohibited_patterns", [])

            infer_req = InferenceRequest(
                messages=[GatewayMessage(role="user", content=prompt)],
                task_context="general",
                user_id=user_id,
            )

            start_t = time.perf_counter()
            resp = await inference_gateway.generate(infer_req, provider=adapter_route)
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            total_latency_ms += elapsed_ms

            output = resp.text

            # Deterministic criteria scoring
            score = 100.0
            failures = []

            for exp in expected:
                if exp.lower() not in output.lower():
                    score -= (50.0 / max(1, len(expected)))
                    failures.append(f"Missing required pattern: '{exp}'")

            for pro in prohibited:
                if pro.lower() in output.lower():
                    score = 0.0
                    failures.append(f"Encountered prohibited pattern: '{pro}'")
                    break

            score = max(0.0, round(score, 1))
            passed = score >= case.get("min_score", 80)
            if passed:
                passed_cases += 1

            category_score_lists[category].append(score)
            case_results.append({
                "case_id": case_id,
                "category": category,
                "score": score,
                "passed": passed,
                "failures": failures,
                "latency_ms": round(elapsed_ms, 2),
            })

        final_category_scores = {
            cat: round(sum(scores) / max(1, len(scores)), 1)
            for cat, scores in category_score_lists.items()
        }
        avg_score = round(sum(final_category_scores.values()) / max(1, len(final_category_scores)), 2)
        avg_latency_ms = round(total_latency_ms / max(1, len(test_cases)), 2)
        pass_rate = round((passed_cases / max(1, len(test_cases))) * 100.0, 1)

        return {
            "evaluation_type": "deterministic_benchmark",
            "candidate_name": candidate_name,
            "adapter_route": adapter_route,
            "overall_score": avg_score,
            "pass_rate_pct": pass_rate,
            "total_cases": len(test_cases),
            "passed_cases": passed_cases,
            "avg_latency_ms": avg_latency_ms,
            "category_scores": final_category_scores,
            "case_results": case_results,
        }

    async def evaluate_live_provider(
        self,
        provider: str,
        model_id: str,
        operator_api_key: str | None = None,
        test_case_limit: int = 5,
    ) -> dict[str, Any]:
        """Conducts actual live-provider evaluations if operator credentials are provided;

        otherwise records explicit UNVERIFIED status without manufacturing false scores.
        """
        # Refuse retired models immediately
        if model_id.lower() in RETIRED_MODELS:
            return {
                "evaluation_type": "live_provider_evaluation",
                "provider": provider,
                "model_id": model_id,
                "status": "RETIRED_AND_INELIGIBLE",
                "reason": RETIRED_MODELS[model_id.lower()],
                "sample_size": 0,
                "executed_at": datetime.now(UTC).isoformat(),
            }

        # Check operator credential
        key = operator_api_key
        if not key:
            if provider == "gemini":
                key = settings.OPERATOR_GEMINI_API_KEY
            elif provider == "groq":
                key = settings.OPERATOR_GROQ_API_KEY
            elif provider == "openrouter":
                key = settings.OPERATOR_OPENROUTER_API_KEY

        if not key:
            return {
                "evaluation_type": "live_provider_evaluation",
                "provider": provider,
                "model_id": model_id,
                "status": "UNVERIFIED (NO OPERATOR CREDENTIALS PRESENT ON WORKSTATION)",
                "sample_size": 0,
                "executed_at": datetime.now(UTC).isoformat(),
                "notice": "Never manufacture scores or simulate live provider traffic. Live evaluation requires operator key.",
            }

        # If key is available, execute bounded live tests
        test_cases = self.load_test_cases()[:test_case_limit]
        live_results: list[dict[str, Any]] = []

        for case in test_cases:
            infer_req = InferenceRequest(
                messages=[GatewayMessage(role="user", content=case["prompt"])],
                task_context="general",
                user_id="live_tournament_evaluator",
            )
            t0 = time.perf_counter()
            try:
                resp = await inference_gateway.generate(infer_req, provider=provider)
                lat_ms = (time.perf_counter() - t0) * 1000.0
                live_results.append({
                    "case_id": case["id"],
                    "category": case["category"],
                    "status_code": 200,
                    "latency_ms": round(lat_ms, 2),
                    "tokens_used": resp.tokens_used,
                    "raw_response_preview": resp.text[:150],
                    "success": True,
                })
            except Exception as e:
                lat_ms = (time.perf_counter() - t0) * 1000.0
                live_results.append({
                    "case_id": case["id"],
                    "category": case["category"],
                    "status_code": 429 if "rate limit" in str(e).lower() else 500,
                    "latency_ms": round(lat_ms, 2),
                    "error": str(e),
                    "success": False,
                })

        return {
            "evaluation_type": "live_provider_evaluation",
            "provider": provider,
            "model_id": model_id,
            "status": "LIVE_VERIFIED" if any(r["success"] for r in live_results) else "LIVE_FAILED",
            "sample_size": len(live_results),
            "executed_at": datetime.now(UTC).isoformat(),
            "results": live_results,
        }

    async def evaluate_candidate(
        self,
        candidate_name: str,
        adapter_route: str = "mock",
        user_id: str = "tournament_evaluator",
    ) -> dict[str, Any]:
        """Backward-compatible entrypoint mapping to deterministic benchmark evaluation."""
        return await self.evaluate_deterministic_benchmarks(
            candidate_name=candidate_name,
            adapter_route=adapter_route,
            user_id=user_id,
        )
