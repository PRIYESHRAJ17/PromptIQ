"""Specialist Agent Orchestrator with task contracts and bounded budgets."""

from typing import Any

from promptiq.gateway.gateway import inference_gateway
from promptiq.gateway.models import GatewayMessage, InferenceRequest


class SpecialistOrchestrator:
    """Executes structured multi-specialist pipelines with deterministic budgets."""

    @classmethod
    async def run_pipeline(
        cls,
        task_name: str,
        input_context: str,
        user_id: str = "system",
        specialists: list[str] | None = None,
        max_steps: int = 5,
    ) -> dict[str, Any]:
        """Runs a bounded sequential specialist task graph."""
        active_specialists = specialists or ["prompt_architect", "prompt_auditor"]
        results: dict[str, Any] = {}
        current_context = input_context

        for idx, specialist in enumerate(active_specialists):
            if idx >= max_steps:
                break

            infer_req = InferenceRequest(
                messages=[
                    GatewayMessage(
                        role="user",
                        content=f"You are the {specialist} specialist. Review and refine:\n\n{current_context}",
                    )
                ],
                system_instruction=f"Act as the {specialist}. Provide objective, verifiable analysis. No filler.",
                task_context="general",
                user_id=user_id,
            )

            infer_resp = await inference_gateway.generate(infer_req)
            results[specialist] = {
                "output": infer_resp.text,
                "latency_ms": infer_resp.latency_ms,
                "tokens_used": infer_resp.tokens_used,
            }
            # Append output for downstream specialist
            current_context += f"\n\n[{specialist} Output]:\n{infer_resp.text[:500]}"

        return {
            "task_name": task_name,
            "steps_completed": len(results),
            "specialist_outputs": results,
            "status": "completed",
        }
