"""Prompt Autopsy and Adversarial Critique Engine."""

import re

from promptiq.gateway.gateway import inference_gateway
from promptiq.gateway.models import GatewayMessage, InferenceRequest
from promptiq.schemas.critic import (
    AutopsyRequest,
    AutopsyResponse,
    AutopsyVerdict,
    CriticFindingSchema,
)


class PromptAutopsyEngine:
    """Diagnoses prompt weaknesses, security risks, contradictions, and missing constraints."""

    # Heuristic detection patterns
    VAGUE_TERMS = re.compile(r"\b(etc|and so on|clean code|best practices|as needed|appropriate|stuff)\b", re.IGNORECASE)
    EXCESSIVE_AGENCY = re.compile(r"\b(do whatever it takes|full access|delete files|bypass|override)\b", re.IGNORECASE)
    INJECTION_RISK = re.compile(r"\b(ignore previous instructions|system prompt override)\b", re.IGNORECASE)

    @classmethod
    async def diagnose_prompt(cls, request: AutopsyRequest, user_id: str = "system") -> AutopsyResponse:
        """Executes multi-dimensional static and heuristic critique of a prompt or package."""
        text = request.prompt_text or ""
        findings: list[CriticFindingSchema] = []

        # 1. Static Heuristic Inspections
        # Check for vague phrasing
        vague_matches = cls.VAGUE_TERMS.findall(text)
        if vague_matches:
            findings.append(
                CriticFindingSchema(
                    category="ambiguity",
                    severity="medium",
                    finding=f"Prompt contains vague language: {', '.join(set(vague_matches))}",
                    evidence_passage=vague_matches[0],
                    consequence="Model will hallucinate or adopt arbitrary assumptions.",
                    recommendation="Replace vague references with concrete, exhaustive specifications.",
                )
            )

        # Check for excessive agency
        agency_matches = cls.EXCESSIVE_AGENCY.findall(text)
        if agency_matches:
            findings.append(
                CriticFindingSchema(
                    category="security",
                    severity="high",
                    finding=f"Excessive agency detected: '{agency_matches[0]}'",
                    evidence_passage=agency_matches[0],
                    consequence="Target agent may perform destructive, unapproved system operations.",
                    recommendation="Add explicit boundary constraints requiring human sign-off for file/command mutations.",
                )
            )

        # Check for prompt injection markers
        injection_matches = cls.INJECTION_RISK.findall(text)
        if injection_matches:
            findings.append(
                CriticFindingSchema(
                    category="security",
                    severity="critical",
                    finding="Prompt contains direct override or prompt injection markers.",
                    evidence_passage=injection_matches[0],
                    consequence="System instructions can be bypassed or hijacked.",
                    recommendation="Remove instructions attempting to override foundational boundaries.",
                )
            )

        # Check output contract
        if "json" in text.lower() and "schema" not in text.lower() and "{" not in text:
            findings.append(
                CriticFindingSchema(
                    category="output_contract",
                    severity="medium",
                    finding="Prompt requests JSON output but lacks an explicit schema.",
                    evidence_passage="JSON",
                    consequence="Model may return markdown-wrapped or malformed JSON keys.",
                    recommendation="Provide an explicit JSON schema or key-value template.",
                )
            )

        # Check error handling
        if "error" not in text.lower() and "fail" not in text.lower():
            findings.append(
                CriticFindingSchema(
                    category="missing_requirements",
                    severity="low",
                    finding="No explicit error handling or stop condition specified.",
                    evidence_passage=None,
                    consequence="Model may enter recursive loops or guess answers when blocked.",
                    recommendation="Specify clear stop conditions and error reporting contracts.",
                )
            )

        # 2. Invoke Gateway for Deep Adversarial Critique
        infer_req = InferenceRequest(
            messages=[
                GatewayMessage(
                    role="user",
                    content=f"Perform strict adversarial prompt autopsy on target '{request.target_environment}':\n\n{text}",
                )
            ],
            system_instruction="Analyze prompt for contradictions, target mismatches, and gaps. Return JSON with findings.",
            task_context="autopsy",
            user_id=user_id,
        )
        infer_resp = await inference_gateway.generate(infer_req)

        # Merge model findings if available
        if infer_resp.structured_data and isinstance(infer_resp.structured_data, dict):
            extra_findings = infer_resp.structured_data.get("findings", [])
            for f in extra_findings:
                findings.append(
                    CriticFindingSchema(
                        category=f.get("category", "feasibility"),
                        severity=f.get("severity", "medium"),
                        finding=f.get("finding", "Potential weakness identified"),
                        evidence_passage=f.get("evidence_passage"),
                        consequence=f.get("consequence", "Execution failure risk"),
                        recommendation=f.get("recommendation", "Refine instructions"),
                    )
                )

        # Determine Verdict
        has_critical = any(f.severity == "critical" for f in findings)
        has_high = any(f.severity == "high" for f in findings)
        has_medium = any(f.severity == "medium" for f in findings)

        if has_critical:
            verdict: AutopsyVerdict = "blocked"
            summary = "Prompt is BLOCKED due to critical security or structural vulnerabilities."
        elif has_high:
            verdict = "needs_revision"
            summary = "Prompt requires revision before safe execution due to high-severity gaps."
        elif has_medium:
            verdict = "ready_with_caveats"
            summary = "Prompt is executable but has minor ambiguities or missing contracts."
        else:
            verdict = "ready"
            summary = "Prompt meets strict quality, security, and contract standards."

        # Calculate multi-axis quality scores
        static_score = max(30.0, 100.0 - (len(vague_matches) * 10.0))
        security_score = 40.0 if has_critical else (70.0 if has_high else 95.0)
        coverage_score = 80.0 if has_medium else 90.0
        compatibility_score = 90.0

        scores = {
            "static_quality": static_score,
            "requirement_coverage": coverage_score,
            "target_compatibility": compatibility_score,
            "security_robustness": security_score,
        }

        # Generate suggested revision
        suggested_revision = (
            f"# REVISED PROMPT (AUTOPSY ENHANCED)\n\n"
            f"{text}\n\n"
            f"## CONSTRAINTS & ERROR CONTRACTS\n"
            f"- If required inputs or dependencies are missing, HALT and report the blocker immediately.\n"
            f"- Do not execute destructive operations without explicit approval.\n"
            f"- Return structured outputs conforming strictly to defined contracts.\n"
        )

        return AutopsyResponse(
            verdict=verdict,
            summary=summary,
            findings=findings,
            quality_scores=scores,
            suggested_revision=suggested_revision,
        )
