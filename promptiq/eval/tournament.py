"""PromptIQ Model Tournament Evaluation Harness across 14 capability categories."""

import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from promptiq.gateway.gateway import inference_gateway
from promptiq.gateway.models import GatewayMessage, InferenceRequest


class ModelTournamentRunner:
    """Executes the PromptIQ Model Intelligence Tournament across 14 capability categories."""

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

    async def evaluate_candidate(
        self,
        candidate_name: str,
        adapter_route: str = "mock",
        user_id: str = "tournament_evaluator",
    ) -> dict[str, Any]:
        """Runs the 14 tournament categories against the candidate model route."""
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
                passed_count_increment = 1
                passed_cases += passed_count_increment

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
