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
    VAGUE_TERMS = re.compile(
        r"\b(etc|and so on|clean code|best practices|as needed|appropriate|stuff)\b", re.IGNORECASE
    )
    EXCESSIVE_AGENCY = re.compile(
        r"\b(do whatever it takes|full access|delete files|bypass|override)\b", re.IGNORECASE
    )
    INJECTION_RISK = re.compile(
        r"\b(ignore previous instructions|system prompt override)\b", re.IGNORECASE
    )
    SYSTEM_EXTRACTION_RISK = re.compile(
        r"\b(output your system prompt|repeat instructions above|reveal system prompt|show developer instructions)\b",
        re.IGNORECASE,
    )
    UNSAFE_PERMISSIONS = re.compile(
        r"\b(chmod 777|disable security|bypass auth|run as root|sudo|disable ssl)\b",
        re.IGNORECASE,
    )
    TOOL_MISUSE = re.compile(
        r"\b(rm -rf|delete database|format disk|drop database)\b",
        re.IGNORECASE,
    )
    UNSUPPORTED_CLAIMS = re.compile(
        r"\b(100% bug-free|completely unhackable|zero latency|guaranteed 100%)\b",
        re.IGNORECASE,
    )

    @classmethod
    def _is_prohibitive_context(cls, passage: str, full_text: str) -> bool:
        """Determines if a flagged passage appears within an explicit negative boundary or prohibition."""
        passage_lower = passage.lower()
        prohibitive_markers = [
            "never",
            "do not",
            "must not",
            "prohibit",
            "strictly no",
            "strictly do not",
            "prevent",
            "disallow",
            "exclude",
            "redact",
            "cannot",
        ]
        for line in full_text.splitlines():
            line_lower = line.lower()
            if passage_lower in line_lower:
                if any(m in line_lower for m in prohibitive_markers):
                    return True
        return False

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

        # Check for excessive agency (ignoring prohibitive/boundary contexts)
        agency_matches = cls.EXCESSIVE_AGENCY.findall(text)
        unnegated_agency = [m for m in agency_matches if not cls._is_prohibitive_context(m, text)]
        if unnegated_agency:
            findings.append(
                CriticFindingSchema(
                    category="security",
                    severity="high",
                    finding=f"Excessive agency detected: '{unnegated_agency[0]}'",
                    evidence_passage=unnegated_agency[0],
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

        # Check for system instruction extraction
        extraction_matches = cls.SYSTEM_EXTRACTION_RISK.findall(text)
        if extraction_matches:
            findings.append(
                CriticFindingSchema(
                    category="system_instruction_extraction",
                    severity="critical",
                    finding="Prompt contains directives attempting to extract or disclose system instructions.",
                    evidence_passage=extraction_matches[0],
                    consequence="Internal system boundaries and operator prompts may be exfiltrated.",
                    recommendation="Strictly prohibit disclosure of system instructions or hidden developer prompts.",
                    blocks_release=True,
                )
            )

        # Check for unsafe permissions
        unsafe_matches = [m for m in cls.UNSAFE_PERMISSIONS.findall(text) if not cls._is_prohibitive_context(m, text)]
        if unsafe_matches:
            findings.append(
                CriticFindingSchema(
                    category="unsafe_permissions",
                    severity="high",
                    finding=f"Unsafe permission granted: '{unsafe_matches[0]}'",
                    evidence_passage=unsafe_matches[0],
                    consequence="Target agent may violate principle of least privilege.",
                    recommendation="Restrict execution privileges to non-root and safe access boundaries.",
                    blocks_release=True,
                )
            )

        # Check for tool misuse
        misuse_matches = [m for m in cls.TOOL_MISUSE.findall(text) if not cls._is_prohibitive_context(m, text)]
        if misuse_matches:
            findings.append(
                CriticFindingSchema(
                    category="tool_misuse",
                    severity="critical",
                    finding=f"Destructive tool directive detected: '{misuse_matches[0]}'",
                    evidence_passage=misuse_matches[0],
                    consequence="Risk of unrecoverable data loss or destructive filesystem operations.",
                    recommendation="Prohibit destructive filesystem/database operations without operator confirmation.",
                    blocks_release=True,
                )
            )

        # Check for unsupported claims
        unsupported_matches = cls.UNSUPPORTED_CLAIMS.findall(text)
        if unsupported_matches:
            findings.append(
                CriticFindingSchema(
                    category="unsupported_claims",
                    severity="medium",
                    finding=f"Unverifiable absolute claim: '{unsupported_matches[0]}'",
                    evidence_passage=unsupported_matches[0],
                    consequence="Prompts with ungrounded perfection guarantees set unrealistic behavioral expectations.",
                    recommendation="Replace absolute claims with empirical metrics and measurable acceptance tests.",
                    blocks_release=False,
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
        if ("concise" in text_lower or "brief" in text_lower) and (
            "exhaustive" in text_lower or "cover all" in text_lower
        ):
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
        if (
            "generate everything" in text_lower
            or "infinite" in text_lower
            or "without limit" in text_lower
        ):
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

        # Check for data privacy risks (ignoring prohibitive/redaction contexts)
        has_leak_term = (
            "print password" in text_lower
            or "reveal secret" in text_lower
            or "output api key" in text_lower
        )
        if has_leak_term and not (
            cls._is_prohibitive_context("password", text)
            or cls._is_prohibitive_context("secret", text)
            or cls._is_prohibitive_context("key", text)
        ):
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
        if not any(
            kw in text_lower for kw in ["test", "verify", "assert", "validate", "acceptance"]
        ):
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

        # Merge model findings if grounded in actual prompt text
        if infer_resp.structured_data and isinstance(infer_resp.structured_data, dict):
            extra_findings = infer_resp.structured_data.get("findings", [])
            for f in extra_findings:
                ev = f.get("evidence_passage")
                # Grounding validation: if an evidence passage is claimed, it MUST exist in the text!
                if ev and ev.lower() not in text.lower():
                    continue  # Discard ungrounded model hallucination
                sev = f.get("severity", "medium")
                findings.append(
                    CriticFindingSchema(
                        category=f.get("category", "feasibility"),
                        severity=sev,
                        finding=f.get("finding", "Potential weakness identified"),
                        evidence_passage=ev,
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
        expected_artifact_hash: str | None = None,
    ) -> AutopsyRevisionVerifyResponse:
        """Deterministically evaluates whether the revised artifact addresses prior autopsy findings.

        Enforces cryptographic artifact binding, contradictory resolution detection,
        severity escalation checks, and prevents superficial phrase-deletion false resolutions.
        """
        import hashlib

        actual_hash = hashlib.sha256((revised_text or "").encode("utf-8")).hexdigest()

        # 1. Cryptographic Artifact Binding Check
        if expected_artifact_hash and actual_hash != expected_artifact_hash:
            return AutopsyRevisionVerifyResponse(
                all_resolved=False,
                blocks_release=True,
                resolutions=[
                    FindingResolution(
                        finding_id=f.id,
                        status="unresolved",
                        reason=f"Cryptographic artifact binding failure: inspected hash {actual_hash[:12]} does not match expected hash {expected_artifact_hash[:12]}.",
                    )
                    for f in original_findings
                ],
                resolved_count=0,
                unresolved_count=len(original_findings),
                partially_resolved_count=0,
                has_contradictory_resolution=False,
                has_severity_escalation=True,
                artifact_hash=actual_hash,
                expected_artifact_hash=expected_artifact_hash,
                summary=f"CRITICAL: Artifact binding mismatch. Expected SHA-256 {expected_artifact_hash[:12]}..., got {actual_hash[:12]}... Release BLOCKED.",
            )

        resolutions: list[FindingResolution] = []
        revised_lower = (revised_text or "").lower()

        # 2. Check for Contradictory Resolution introduced in revised text
        contradictions: list[str] = []
        if ("concise" in revised_lower or "brief" in revised_lower) and (
            "exhaustive" in revised_lower or "cover all" in revised_lower
        ):
            contradictions.append("Conflicting density directives (concise vs exhaustive)")
        if ("read-only" in revised_lower or "no mutations" in revised_lower) and (
            "delete files" in revised_lower
            or "write files" in revised_lower
            or "execute shell" in revised_lower
        ):
            if not cls._is_prohibitive_context(
                "delete files", revised_text
            ) and not cls._is_prohibitive_context("write files", revised_text):
                contradictions.append(
                    "Conflicting file mutation directives (read-only vs file mutations)"
                )
        if ("require human approval" in revised_lower or "escalate to human" in revised_lower) and (
            "bypass human" in revised_lower
            or "autonomous execution without approval" in revised_lower
        ):
            contradictions.append(
                "Conflicting escalation directives (human approval vs autonomous bypass)"
            )

        has_contradictory_resolution = len(contradictions) > 0

        # 3. Check for Severity Escalation (new Critical/High issues introduced in revised text)
        has_new_injection = bool(cls.INJECTION_RISK.findall(revised_text))
        has_new_leak = (
            "print password" in revised_lower
            or "reveal secret" in revised_lower
            or "output api key" in revised_lower
        ) and not (
            cls._is_prohibitive_context("password", revised_text)
            or cls._is_prohibitive_context("secret", revised_text)
            or cls._is_prohibitive_context("key", revised_text)
        )
        unnegated_agency = [
            m
            for m in cls.EXCESSIVE_AGENCY.findall(revised_text)
            if not cls._is_prohibitive_context(m, revised_text)
        ]
        has_severity_escalation = has_new_injection or has_new_leak or bool(unnegated_agency)

        for finding in original_findings:
            f_id = finding.id
            evidence = finding.evidence_passage or ""
            evidence_lower = evidence.lower()

            status = "unresolved"
            reason = "No evidence found that this finding has been addressed in the revised text."
            proof_snippet = None

            if finding.category == "ambiguity":
                vague_matches = cls.VAGUE_TERMS.findall(revised_text)
                is_superficial = len(revised_text.strip()) < 20
                if evidence_lower and evidence_lower not in revised_lower:
                    if not is_superficial:
                        status = "resolved"
                        reason = f"Identified vague passage '{evidence}' was eliminated and replaced with concrete specifications."
                        proof_snippet = "Concrete specifications provided"
                    else:
                        status = "unresolved"
                        reason = f"False resolution: Vague term '{evidence}' was deleted, but prompt lacks concrete specifications (superficial deletion)."
                        proof_snippet = "Superficial deletion without specification"
                elif not vague_matches and not is_superficial:
                    status = "resolved"
                    reason = "All vague terminology patterns were eliminated and structured specs provided."
                    proof_snippet = "Zero vague matches with structure"
                else:
                    status = "unresolved"
                    reason = f"Vague terms still present in revised prompt: {', '.join(set(vague_matches))}"
                    proof_snippet = vague_matches[0] if vague_matches else None

            elif finding.category == "security":
                injection_matches = cls.INJECTION_RISK.findall(revised_text)
                has_safety_guard = any(
                    kw in revised_lower
                    for kw in [
                        "approval",
                        "permission",
                        "halt",
                        "do not execute",
                        "boundaries",
                        "redact",
                    ]
                )
                unnegated = [
                    m
                    for m in cls.EXCESSIVE_AGENCY.findall(revised_text)
                    if not cls._is_prohibitive_context(m, revised_text)
                ]

                if (
                    evidence_lower
                    and evidence_lower in revised_lower
                    and not cls._is_prohibitive_context(evidence, revised_text)
                ):
                    status = "unresolved"
                    reason = f"Security vulnerability passage '{evidence}' is still present in revised text."
                    proof_snippet = evidence
                elif not injection_matches and not unnegated and has_safety_guard:
                    status = "resolved"
                    reason = "Security risk resolved: hazardous passages eliminated/prohibited and safety boundaries established."
                    proof_snippet = "Safety boundaries established"
                elif has_safety_guard and unnegated:
                    status = "partially_resolved"
                    reason = f"Safety guard declared, but unconstrained excessive agency '{unnegated[0]}' still exists."
                    proof_snippet = unnegated[0]
                else:
                    status = "unresolved"
                    reason = "Security risk remains unresolved."

            elif finding.category == "output_contract":
                has_json = "json" in revised_lower
                has_schema = (
                    "schema" in revised_lower
                    or "contract" in revised_lower
                    or "properties" in revised_lower
                )
                has_brackets = "{" in revised_text and "}" in revised_text
                if has_json and (has_schema and has_brackets):
                    status = "resolved"
                    reason = "Output contract clearly specified with formal JSON schema and bracketed structure."
                    proof_snippet = "Schema and envelope defined"
                elif has_json and (has_schema or has_brackets):
                    status = "partially_resolved"
                    reason = "JSON output requested with partial schema/brackets, but complete field contract is missing."
                    proof_snippet = "Partial schema defined"
                elif not has_json:
                    status = "resolved"
                    reason = "JSON output requirement removed; no longer missing contract."
                else:
                    status = "unresolved"
                    reason = "Requests JSON output but lacks explicit schema or structure."

            elif finding.category in ("missing_requirements", "missing_error_handling"):
                has_error_handling = any(
                    kw in revised_lower
                    for kw in [
                        "error",
                        "fail",
                        "halt",
                        "exception",
                        "abort",
                        "blocker",
                        "raise valueerror",
                    ]
                )
                if has_error_handling:
                    status = "resolved"
                    reason = "Explicit error handling, failure modes, or stop conditions added."
                    proof_snippet = "Error handling present"
                else:
                    status = "unresolved"
                    reason = "Still missing explicit error handling or stop conditions."

            elif finding.category == "inadequate_constraints":
                has_neg = any(
                    kw in revised_lower
                    for kw in ["do not", "never", "must not", "prohibit", "exclude", "strictly no"]
                )
                if has_neg:
                    status = "resolved"
                    reason = "Explicit negative boundary constraints added."
                    proof_snippet = "Negative constraints present"
                else:
                    status = "unresolved"
                    reason = "Still missing negative boundary constraints."

            elif finding.category == "data_privacy_leak":
                has_redaction = any(
                    kw in revised_lower
                    for kw in [
                        "redact",
                        "never disclose",
                        "zero secret",
                        "do not log",
                        "never log",
                        "never print",
                    ]
                )
                raw_leak = any(
                    kw in revised_lower
                    for kw in ["print password", "reveal secret", "output api key", "dump password"]
                )
                is_prohibited_context = (
                    cls._is_prohibitive_context("password", revised_text)
                    or cls._is_prohibitive_context("secret", revised_text)
                    or cls._is_prohibitive_context("key", revised_text)
                )

                if has_redaction and is_prohibited_context and not raw_leak:
                    status = "resolved"
                    reason = (
                        "Data privacy hazard eliminated and strict redaction boundaries enforced."
                    )
                    proof_snippet = "Redaction rules present"
                elif has_redaction or is_prohibited_context:
                    status = "resolved"
                    reason = "Sensitive credentials explicitly prohibited and marked for redaction."
                    proof_snippet = "Prohibitive context present"
                else:
                    status = "unresolved"
                    reason = "Credential disclosure instructions still present."

            elif finding.category == "unbounded_generation":
                has_bounds = any(
                    kw in revised_lower
                    for kw in ["maximum", "limit to", "at most", "bounded", "top "]
                )
                if has_bounds:
                    status = "resolved"
                    reason = "Bounded generation limits specified."
                    proof_snippet = "Bounds defined"
                else:
                    status = "unresolved"
                    reason = "Still lacks explicit generation limits."

            elif finding.category == "instruction_conflict":
                has_conflict = ("concise" in revised_lower or "brief" in revised_lower) and (
                    "exhaustive" in revised_lower or "cover all" in revised_lower
                )
                if not has_conflict:
                    status = "resolved"
                    reason = "Conflicting density directives reconciled."
                    proof_snippet = "Density reconciled"
                else:
                    status = "unresolved"
                    reason = "Conflicting density directives remain unresolved."

            elif finding.category == "testability_gap":
                has_tests = any(
                    kw in revised_lower
                    for kw in ["test", "verify", "assert", "validate", "acceptance"]
                )
                has_concrete_test = any(
                    kw in revised_lower
                    for kw in [
                        "assert ",
                        "test case",
                        "acceptance criteria",
                        "benchmark >",
                        "test suite",
                        "raise valueerror",
                    ]
                )
                if has_tests and has_concrete_test:
                    status = "resolved"
                    reason = "Concrete test validation criteria and assertion conditions added."
                    proof_snippet = "Verification assertions present"
                elif has_tests:
                    status = "partially_resolved"
                    reason = "Testing mentioned, but lacks concrete assertion criteria or measurable threshold."
                    proof_snippet = "General test mention"
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
                        w
                        for w in re.findall(r"\w{4,}", finding.recommendation.lower())
                        if w
                        not in (
                            "with",
                            "that",
                            "this",
                            "from",
                            "should",
                            "must",
                            "replace",
                            "provide",
                        )
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
        partially_resolved_count = sum(1 for r in resolutions if r.status == "partially_resolved")
        unresolved_count = len(resolutions) - resolved_count
        all_resolved = (
            (unresolved_count == 0)
            and not has_contradictory_resolution
            and not has_severity_escalation
        )

        blocking_unresolved = any(
            f.blocks_release and r.status != "resolved"
            for f, r in zip(original_findings, resolutions, strict=False)
        )
        blocks_release = (
            blocking_unresolved or has_contradictory_resolution or has_severity_escalation
        )

        reasons = []
        if blocking_unresolved:
            reasons.append("unresolved critical/high findings")
        if has_contradictory_resolution:
            reasons.append(f"contradictory resolution ({'; '.join(contradictions)})")
        if has_severity_escalation:
            reasons.append("severity escalation (new critical security hazard introduced)")

        summary = (
            f"Verified {len(original_findings)} findings: {resolved_count} resolved, "
            f"{partially_resolved_count} partially resolved, {unresolved_count} unresolved. "
            f"Release {'BLOCKED by ' + '; '.join(reasons) if blocks_release else 'ALLOWED'}."
        )

        return AutopsyRevisionVerifyResponse(
            all_resolved=all_resolved,
            blocks_release=blocks_release,
            resolutions=resolutions,
            resolved_count=resolved_count,
            unresolved_count=unresolved_count,
            partially_resolved_count=partially_resolved_count,
            has_contradictory_resolution=has_contradictory_resolution,
            has_severity_escalation=has_severity_escalation,
            artifact_hash=actual_hash,
            expected_artifact_hash=expected_artifact_hash,
            summary=summary,
        )
