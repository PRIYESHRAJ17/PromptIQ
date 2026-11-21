"""Prompt Autopsy and Adversarial Critique Engine."""

import re
from typing import Any

from promptiq.gateway.gateway import inference_gateway
from promptiq.gateway.models import GatewayMessage, InferenceRequest
from promptiq.schemas.critic import (
    AutopsyRequest,
    AutopsyResponse,
    AutopsyRevisionVerifyResponse,
    AutopsyVerdict,
    CriticFindingSchema,
    FindingResolution,
)


class PromptAutopsyEngine:
    """Diagnoses prompt weaknesses, security risks, contradictions, and missing constraints."""

    # Heuristic detection patterns
    VAGUE_TERMS = re.compile(r"\b(etc|and so on|clean code|best practices|as needed|appropriate|stuff)\b", re.IGNORECASE)
    EXCESSIVE_AGENCY = re.compile(r"\b(do whatever it takes|full access|delete files|bypass|override)\b", re.IGNORECASE)
    INJECTION_RISK = re.compile(r"\b(ignore previous instructions|system prompt override)\b", re.IGNORECASE)

    @classmethod
    async def diagnose_prompt(
        cls,
        request: AutopsyRequest,
        user_id: str = "system",
        db: Any | None = None,
    ) -> AutopsyResponse:
        """Executes multi-dimensional static and heuristic critique of a prompt or package."""
        text = request.prompt_text or ""

        # If package_id is provided, resolve package with tenant isolation check
        if request.package_id and db is not None:
            from sqlalchemy import select

            from promptiq.core.exceptions import NotFoundError
            from promptiq.models.package import PromptPackage
            from promptiq.services.project_service import ProjectService

            stmt = select(PromptPackage).where(PromptPackage.id == request.package_id)
            res = await db.execute(stmt)
            pkg = res.scalar_one_or_none()
            if not pkg:
                raise NotFoundError("PromptPackage", request.package_id)

            # Enforce tenant isolation
            await ProjectService.get_project(db, pkg.project_id, user_id)

            if not text and pkg.files:
                text = "\n\n".join(pkg.files.values())

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
                    blocks_release=False,
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
                    blocks_release=True,
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
                    blocks_release=True,
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
                    blocks_release=False,
                )
            )

        # Check error handling
        if "error" not in text.lower() and "fail" not in text.lower():
            findings.append(
                CriticFindingSchema(
                    category="missing_error_handling",
                    severity="medium",
                    finding="No explicit error handling or stop condition specified.",
                    evidence_passage=None,
                    consequence="Model may enter recursive loops or guess answers when blocked.",
                    recommendation="Specify clear stop conditions and error reporting contracts.",
                    blocks_release=False,
                )
            )

        # Check negative constraints
        negative_words = ["do not", "never", "must not", "prohibit", "exclude", "strictly no"]
        if not any(w in text.lower() for w in negative_words):
            findings.append(
                CriticFindingSchema(
                    category="inadequate_constraints",
                    severity="medium",
                    finding="Prompt lacks negative boundary constraints or explicit prohibitions.",
                    evidence_passage=None,
                    consequence="Model may take unconstrained actions or hallucinate out-of-scope behaviors.",
                    recommendation="Add explicit negative boundaries defining what the model must NOT do.",
                    blocks_release=False,
                )
            )

        # Check for instruction conflicts (e.g. concise vs exhaustive)
        text_lower = text.lower()
        if ("concise" in text_lower or "brief" in text_lower) and ("exhaustive" in text_lower or "cover all" in text_lower):
            findings.append(
                CriticFindingSchema(
                    category="instruction_conflict",
                    severity="high",
                    finding="Conflicting density instructions: prompt demands brevity while requesting exhaustive detail.",
                    evidence_passage="concise vs exhaustive",
                    consequence="Model will produce erratic length responses or truncate important details.",
                    recommendation="Reconcile brevity vs exhaustiveness by specifying section-by-section length targets.",
                    blocks_release=True,
                )
            )

        # Check for unbounded generation
        if "generate everything" in text_lower or "infinite" in text_lower or "without limit" in text_lower:
            findings.append(
                CriticFindingSchema(
                    category="unbounded_generation",
                    severity="high",
                    finding="Unbounded generation directive detected.",
                    evidence_passage="unbounded generation",
                    consequence="Model may exceed output token limits and terminate mid-generation.",
                    recommendation="Define bounded generation limits (e.g. top 5 recommendations, max 2 pages).",
                    blocks_release=True,
                )
            )

        # Check for data privacy risks
        if "print password" in text_lower or "reveal secret" in text_lower or "output api key" in text_lower:
            findings.append(
                CriticFindingSchema(
                    category="data_privacy_leak",
                    severity="critical",
                    finding="Data privacy hazard: prompt requests disclosure of sensitive credentials or keys.",
                    evidence_passage="print password / secret",
                    consequence="Risk of secret leakage and security breach.",
                    recommendation="Strictly redact and prohibit disclosure of credentials, keys, or passwords.",
                    blocks_release=True,
                )
            )

        # Check for testability gaps
        if not any(kw in text_lower for kw in ["test", "verify", "assert", "validate", "acceptance"]):
            findings.append(
                CriticFindingSchema(
                    category="testability_gap",
                    severity="low",
                    finding="Prompt contains no test validation criteria or verification method.",
                    evidence_passage=None,
                    consequence="Output correctness cannot be objectively or deterministically verified.",
                    recommendation="Add observable acceptance criteria or automated test conditions.",
                    blocks_release=False,
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
                sev = f.get("severity", "medium")
                findings.append(
                    CriticFindingSchema(
                        category=f.get("category", "feasibility"),
                        severity=sev,
                        finding=f.get("finding", "Potential weakness identified"),
                        evidence_passage=f.get("evidence_passage"),
                        consequence=f.get("consequence", "Execution failure risk"),
                        recommendation=f.get("recommendation", "Refine instructions"),
                        blocks_release=sev in ("critical", "high"),
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

    @classmethod
    def verify_findings_against_artifact(
        cls,
        original_findings: list[CriticFindingSchema],
        revised_text: str,
    ) -> AutopsyRevisionVerifyResponse:
        """Deterministically evaluates whether the revised artifact addresses prior autopsy findings."""
        resolutions: list[FindingResolution] = []
        revised_lower = (revised_text or "").lower()

        for finding in original_findings:
            f_id = finding.id
            evidence = finding.evidence_passage or ""
            evidence_lower = evidence.lower()

            status = "unresolved"
            reason = "No evidence found that this finding has been addressed in the revised text."
            proof_snippet = None

            if finding.category == "ambiguity":
                vague_matches = cls.VAGUE_TERMS.findall(revised_text)
                if evidence_lower and evidence_lower not in revised_lower:
                    status = "resolved"
                    reason = f"Identified vague passage '{evidence}' was eliminated from the revised text."
                    proof_snippet = "Passage removed"
                elif not vague_matches:
                    status = "resolved"
                    reason = "All vague terminology patterns were eliminated."
                    proof_snippet = "Zero vague matches"
                else:
                    status = "unresolved"
                    reason = f"Vague terms still present in revised prompt: {', '.join(set(vague_matches))}"
                    proof_snippet = vague_matches[0]

            elif finding.category == "security":
                injection_matches = cls.INJECTION_RISK.findall(revised_text)
                agency_matches = cls.EXCESSIVE_AGENCY.findall(revised_text)
                has_safety_guard = any(kw in revised_lower for kw in ["approval", "permission", "halt", "do not execute", "boundaries"])

                if evidence_lower and evidence_lower in revised_lower:
                    status = "unresolved"
                    reason = f"Security vulnerability passage '{evidence}' is still present in revised text."
                    proof_snippet = evidence
                elif not injection_matches and (has_safety_guard or not agency_matches):
                    status = "resolved"
                    reason = "Security risk resolved: hazardous passages removed and/or safety boundaries established."
                    proof_snippet = "Safety boundaries established"
                else:
                    status = "unresolved"
                    reason = "Security risk remains unresolved."

            elif finding.category == "output_contract":
                has_json = "json" in revised_lower
                has_contract = "schema" in revised_lower or "{" in revised_text or "contract" in revised_lower or "format" in revised_lower
                if has_json and has_contract:
                    status = "resolved"
                    reason = "Output contract clearly specified with schema or structured template."
                    proof_snippet = "Schema/structure defined"
                elif not has_json:
                    status = "resolved"
                    reason = "JSON output requirement removed; no longer missing contract."
                else:
                    status = "unresolved"
                    reason = "Requests JSON output but lacks explicit schema or structure."

            elif finding.category in ("missing_requirements", "missing_error_handling"):
                has_error_handling = any(kw in revised_lower for kw in ["error", "fail", "halt", "exception", "abort", "blocker"])
                if has_error_handling:
                    status = "resolved"
                    reason = "Explicit error handling, failure modes, or stop conditions added."
                    proof_snippet = "Error handling present"
                else:
                    status = "unresolved"
                    reason = "Still missing explicit error handling or stop conditions."

            elif finding.category == "inadequate_constraints":
                has_neg = any(kw in revised_lower for kw in ["do not", "never", "must not", "prohibit", "exclude", "strictly no"])
                if has_neg:
                    status = "resolved"
                    reason = "Explicit negative boundary constraints added."
                    proof_snippet = "Negative constraints present"
                else:
                    status = "unresolved"
                    reason = "Still missing negative boundary constraints."

            elif finding.category == "data_privacy_leak":
                has_redaction = any(kw in revised_lower for kw in ["redact", "never disclose", "zero secret", "do not log", "never log", "never print"])
                raw_leak = any(kw in revised_lower for kw in ["print password", "reveal secret", "output api key", "dump password"])
                is_prohibited_context = any(p in revised_lower for p in ["never", "do not", "must not", "prohibit", "redact"])

                if (has_redaction and is_prohibited_context) or not raw_leak:
                    status = "resolved"
                    reason = "Data privacy hazard eliminated and redaction boundaries enforced."
                    proof_snippet = "Redaction rules present"
                else:
                    status = "unresolved"
                    reason = "Credential disclosure instructions still present."

            elif finding.category == "unbounded_generation":
                has_bounds = any(kw in revised_lower for kw in ["maximum", "limit to", "at most", "bounded", "top "])
                if has_bounds:
                    status = "resolved"
                    reason = "Bounded generation limits specified."
                    proof_snippet = "Bounds defined"
                else:
                    status = "unresolved"
                    reason = "Still lacks explicit generation limits."

            elif finding.category == "instruction_conflict":
                has_conflict = ("concise" in revised_lower or "brief" in revised_lower) and ("exhaustive" in revised_lower or "cover all" in revised_lower)
                if not has_conflict:
                    status = "resolved"
                    reason = "Conflicting density directives reconciled."
                    proof_snippet = "Density reconciled"
                else:
                    status = "unresolved"
                    reason = "Conflicting density directives remain unresolved."

            elif finding.category == "testability_gap":
                has_tests = any(kw in revised_lower for kw in ["test", "verify", "assert", "validate", "acceptance"])
                if has_tests:
                    status = "resolved"
                    reason = "Test validation or acceptance criteria added."
                    proof_snippet = "Verification criteria present"
                else:
                    status = "unresolved"
                    reason = "Still missing test validation criteria."

            else:
                if evidence_lower and evidence_lower not in revised_lower:
                    status = "resolved"
                    reason = f"Flagged passage '{evidence}' was removed or refactored."
                    proof_snippet = "Flagged passage removed"
                else:
                    rec_words = [
                        w for w in re.findall(r"\w{4,}", finding.recommendation.lower())
                        if w not in ("with", "that", "this", "from", "should", "must", "replace", "provide")
                    ]
                    matched_words = [w for w in rec_words if w in revised_lower]
                    if len(matched_words) >= 2:
                        status = "resolved"
                        reason = f"Recommendation addressed in revised text (matched: {', '.join(matched_words[:3])})."
                        proof_snippet = f"Matched: {', '.join(matched_words[:3])}"
                    else:
                        status = "unresolved"
                        reason = "Revised text does not reflect the recommendation."

            resolutions.append(
                FindingResolution(
                    finding_id=f_id,
                    status=status,
                    reason=reason,
                    evidence=proof_snippet,
                )
            )

        resolved_count = sum(1 for r in resolutions if r.status == "resolved")
        unresolved_count = len(resolutions) - resolved_count
        all_resolved = unresolved_count == 0

        blocking_unresolved = any(
            f.blocks_release and r.status != "resolved"
            for f, r in zip(original_findings, resolutions, strict=False)
        )

        summary = (
            f"Verified {len(original_findings)} findings: {resolved_count} resolved, {unresolved_count} unresolved. "
            f"Release {'BLOCKED by unresolved critical/high findings' if blocking_unresolved else 'ALLOWED'}."
        )

        return AutopsyRevisionVerifyResponse(
            all_resolved=all_resolved,
            blocks_release=blocking_unresolved,
            resolutions=resolutions,
            resolved_count=resolved_count,
            unresolved_count=unresolved_count,
            summary=summary,
        )

