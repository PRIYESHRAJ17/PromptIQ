"""Deterministic Mock Inference Adapter for offline testing and zero-cost local execution."""

import json
import time
from typing import Any

from promptiq.gateway.adapters.base import BaseInferenceAdapter
from promptiq.gateway.models import InferenceRequest, InferenceResponse


class MockInferenceAdapter(BaseInferenceAdapter):
    """Deterministic adapter returning high-fidelity simulated model outputs."""

    provider_name: str = "mock"
    model_id: str = "promptiq-mock-v1"

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        start_time = time.perf_counter()

        prompt_content = " ".join([m.content for m in request.messages])
        task_context = request.task_context

        structured_data: dict[str, Any] | list[Any] | None = None
        response_text = ""

        # Check task context to return context-specific intelligent completions
        if task_context == "discovery":
            structured_data = {
                "inferred_requirements": [
                    {
                        "id": "REQ-INF-001",
                        "text": "System must enforce authentication and tenant isolation.",
                        "category": "security",
                        "priority": "P0",
                        "provenance": "inferred",
                    },
                    {
                        "id": "REQ-INF-002",
                        "text": "System must expose structured REST API with OpenAPI documentation.",
                        "category": "functional",
                        "priority": "P1",
                        "provenance": "inferred",
                    },
                ],
                "inferred_tech_stack": ["Python", "FastAPI", "SQLAlchemy", "PostgreSQL"],
                "suggested_questions": [
                    "What specific authentication providers (e.g. OAuth2, Email/Password) should be prioritized?",
                    "What are the target deployment platforms and expected concurrency?",
                ],
            }
            response_text = json.dumps(structured_data, indent=2)

        elif task_context == "autopsy":
            structured_data = {
                "verdict": "ready_with_caveats",
                "summary": "Prompt is functional but lacks explicit error handling, output schemas, and bounded tool permissions.",
                "quality_scores": {
                    "static_quality": 82.0,
                    "requirement_coverage": 85.0,
                    "target_compatibility": 90.0,
                    "security_robustness": 80.0,
                },
                "findings": [
                    {
                        "category": "ambiguity",
                        "severity": "medium",
                        "finding": "Output format is under-specified regarding error conditions.",
                        "evidence_passage": "Return results as JSON.",
                        "consequence": "Target model may return arbitrary markdown envelopes on failure.",
                        "recommendation": "Explicitly specify the failure JSON envelope schema.",
                    },
                    {
                        "category": "security",
                        "severity": "high",
                        "finding": "Excessive agency: Tool execution does not require explicit approval gates.",
                        "evidence_passage": "Execute shell commands as needed.",
                        "consequence": "Unsandboxed command execution could allow unintended system mutations.",
                        "recommendation": "Constrain shell access to read-only commands and require approval.",
                    },
                ],
            }
            response_text = json.dumps(structured_data, indent=2)

        elif task_context == "research":
            structured_data = {
                "summary": "Official documentation confirms current specification and capabilities.",
                "claims": [
                    {
                        "claim_text": "Model Context Protocol supports standard JSON-RPC tools and resource endpoints.",
                        "support_status": "verified",
                        "confidence_score": 0.98,
                        "source_url": "https://modelcontextprotocol.io/specification/",
                        "excerpt": "MCP standardizes client-to-server tool invocation over stdio and HTTP/SSE transports.",
                    }
                ],
            }
            response_text = json.dumps(structured_data, indent=2)

        else:
            # Default prompt compilation response
            response_text = (
                f"# TARGET INSTRUCTIONS\n\n"
                f"## MISSION\nDeliver the requested requirements with verifiable correctness.\n\n"
                f"## CONTEXT & RULES\n- Strict provenance enforced.\n- Zero-price execution only.\n\n"
                f"Based on user intent: '{prompt_content[:100]}...'"
            )

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return InferenceResponse(
            text=response_text,
            structured_data=structured_data,
            model_id=self.model_id,
            provider=self.provider_name,
            latency_ms=round(latency_ms, 2),
            tokens_used=len(response_text) // 4,
            route_cost=0.0,  # Strict Zero-Price Invariant
        )
