"""Prompt Test Lab: Test execution, deterministic assertions, and benchmarking."""

import re
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.core.config import settings
from promptiq.core.exceptions import NotFoundError
from promptiq.gateway.gateway import inference_gateway
from promptiq.gateway.models import GatewayMessage, InferenceRequest
from promptiq.models.eval import EvaluationRun, EvaluationSuite, FailureRecord
from promptiq.models.package import PromptPackage
from promptiq.schemas.eval import (
    ComparativeRunResponse,
    EvaluationRunRequest,
    EvaluationRunResponse,
    EvaluationSuiteCreate,
)
from promptiq.services.project_service import ProjectService


class PromptTestLab:
    """Executes controlled prompt evaluations, fixed assertions, and failure analysis."""

    @classmethod
    async def create_suite(
        cls,
        db: AsyncSession,
        project_id: str,
        user_id: str,
        suite_in: EvaluationSuiteCreate,
    ) -> EvaluationSuite:
        """Provisions an evaluation suite linked to a project."""
        await ProjectService.get_project(db, project_id, user_id)

        suite = EvaluationSuite(
            project_id=project_id,
            name=suite_in.name,
            description=suite_in.description,
            test_cases=[c.model_dump() for c in suite_in.test_cases],
            assertions=[],
        )
        db.add(suite)
        await db.flush()
        return suite

    @classmethod
    async def run_evaluation(
        cls,
        db: AsyncSession,
        project_id: str,
        user_id: str,
        run_req: EvaluationRunRequest,
    ) -> EvaluationRunResponse:
        """Executes test cases against a compiled package using fixed assertions."""
        await ProjectService.get_project(db, project_id, user_id)

        stmt = select(EvaluationSuite).where(
            EvaluationSuite.id == run_req.suite_id,
            EvaluationSuite.project_id == project_id,
        )
        res = await db.execute(stmt)
        suite = res.scalar_one_or_none()
        if not suite:
            raise NotFoundError("EvaluationSuite", run_req.suite_id)

        stmt_pkg = select(PromptPackage).where(
            PromptPackage.id == run_req.package_id,
            PromptPackage.project_id == project_id,
        )
        res_pkg = await db.execute(stmt_pkg)
        pkg = res_pkg.scalar_one_or_none()
        if not pkg:
            raise NotFoundError("PromptPackage", run_req.package_id)

        # Assemble prompt text from package
        prompt_content = "\n".join(pkg.files.values())

        case_results = []
        passed_count = 0
        start_time = time.perf_counter()

        for case in suite.test_cases:
            case_id = case.get("id", "case-1")
            input_vars = case.get("input_vars", {})
            expected_patterns = case.get("expected_output_patterns", [])
            assertion_type = case.get("assertion_type", "contains")

            # Execute model call through the zero-price gateway
            user_msg = f"Execute test case '{case.get('description')}': Inputs: {input_vars}"
            infer_req = InferenceRequest(
                messages=[GatewayMessage(role="user", content=f"{prompt_content}\n\n{user_msg}")],
                task_context="general",
                user_id=user_id,
            )
            infer_resp = await inference_gateway.generate(infer_req)

            # Evaluate deterministic assertion
            output_text = infer_resp.text
            passed = True
            failure_reason = None

            for pattern in expected_patterns:
                if assertion_type == "contains":
                    if pattern.lower() not in output_text.lower():
                        passed = False
                        failure_reason = f"Missing expected pattern: '{pattern}'"
                        break
                elif assertion_type == "not_contains":
                    if pattern.lower() in output_text.lower():
                        passed = False
                        failure_reason = f"Output contains prohibited pattern: '{pattern}'"
                        break
                elif assertion_type == "regex":
                    if not re.search(pattern, output_text, re.IGNORECASE):
                        passed = False
                        failure_reason = f"Regex match failed for pattern: '{pattern}'"
                        break

            if passed:
                passed_count += 1
            else:
                # Store FailureRecord for failure intelligence
                fail_rec = FailureRecord(
                    project_id=project_id,
                    failure_class="assertion_failure",
                    observed_failure=failure_reason or "Unknown failure",
                    root_cause_hypothesis="Prompt instructions did not sufficiently constrain the model on this edge case.",
                    correction=f"Add explicit directive to cover: {expected_patterns}",
                    regression_seed=case,
                )
                db.add(fail_rec)

            case_results.append({
                "case_id": case_id,
                "passed": passed,
                "failure_reason": failure_reason,
                "latency_ms": infer_resp.latency_ms,
            })

        total_cases = len(suite.test_cases)
        pass_rate = round((passed_count / total_cases * 100.0) if total_cases > 0 else 0.0, 2)
        total_latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        run = EvaluationRun(
            suite_id=suite.id,
            package_id=pkg.id,
            model_id=run_req.model_id,
            provider_route=settings.MANAGED_INFERENCE_PRIMARY_ROUTE,
            pass_rate=pass_rate,
            total_cases=total_cases,
            passed_cases=passed_count,
            results=case_results,
            latency_ms=total_latency_ms,
            cost_estimate=0.0,  # Strict Zero-Price Invariant
        )
        db.add(run)
        await db.flush()

        return EvaluationRunResponse(
            id=run.id,
            suite_id=run.suite_id,
            package_id=run.package_id,
            model_id=run.model_id,
            pass_rate=run.pass_rate,
            total_cases=run.total_cases,
            passed_cases=run.passed_cases,
            results=run.results,
            latency_ms=run.latency_ms,
            cost_estimate=0.0,
            execution_mode="mock" if settings.is_test else "live",
        )

    @classmethod
    async def compare_runs(
        cls,
        db: AsyncSession,
        project_id: str,
        user_id: str,
        baseline_run_id: str,
        candidate_run_id: str,
    ) -> ComparativeRunResponse:
        """Compares two evaluation runs to detect regressions and measure performance improvements."""
        await ProjectService.get_project(db, project_id, user_id)

        stmt_base = select(EvaluationRun).where(EvaluationRun.id == baseline_run_id)
        res_base = await db.execute(stmt_base)
        baseline = res_base.scalar_one_or_none()
        if not baseline:
            raise NotFoundError("EvaluationRun", baseline_run_id)

        stmt_cand = select(EvaluationRun).where(EvaluationRun.id == candidate_run_id)
        res_cand = await db.execute(stmt_cand)
        candidate = res_cand.scalar_one_or_none()
        if not candidate:
            raise NotFoundError("EvaluationRun", candidate_run_id)

        base_cases = {r.get("case_id"): r.get("passed", False) for r in (baseline.results or [])}
        cand_cases = {r.get("case_id"): r.get("passed", False) for r in (candidate.results or [])}

        newly_failed = []
        newly_passed = []

        all_cases = set(base_cases.keys()).union(set(cand_cases.keys()))
        for c_id in sorted(all_cases):
            was_passing = base_cases.get(c_id, False)
            now_passing = cand_cases.get(c_id, False)
            if was_passing and not now_passing:
                newly_failed.append(c_id)
            elif not was_passing and now_passing:
                newly_passed.append(c_id)

        pass_rate_delta = round(candidate.pass_rate - baseline.pass_rate, 2)
        latency_delta_ms = round((candidate.latency_ms or 0.0) - (baseline.latency_ms or 0.0), 2)
        has_regressions = len(newly_failed) > 0

        summary = (
            f"Comparison between baseline {baseline_run_id[:8]} ({baseline.pass_rate}%) "
            f"and candidate {candidate_run_id[:8]} ({candidate.pass_rate}%): "
            f"Pass rate delta: {pass_rate_delta:+.2f}%. "
            f"{len(newly_failed)} regressions, {len(newly_passed)} improvements. "
            f"Latency delta: {latency_delta_ms:+.2f}ms."
        )

        return ComparativeRunResponse(
            baseline_run_id=baseline_run_id,
            candidate_run_id=candidate_run_id,
            baseline_pass_rate=baseline.pass_rate,
            candidate_pass_rate=candidate.pass_rate,
            pass_rate_delta=pass_rate_delta,
            has_regressions=has_regressions,
            newly_failed_cases=newly_failed,
            newly_passed_cases=newly_passed,
            latency_delta_ms=latency_delta_ms,
            summary=summary,
        )

