"""Test Prompt Test Lab, Deterministic Assertions, and Promptfoo Exporter."""

import pytest
from httpx import AsyncClient

from promptiq.eval.promptfoo_exporter import PromptfooExporter
from promptiq.models.eval import EvaluationSuite


@pytest.mark.asyncio
async def test_evaluation_lab_execution_and_assertions(
    client: AsyncClient, user_auth_headers: dict[str, str]
):
    """Verifies that the test lab evaluates fixed assertions and tracks pass rates."""
    # 1. Create and approve a project
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Eval Test Project"},
        headers=user_auth_headers,
    )
    project_id = proj_resp.json()["id"]

    await client.post(
        f"/api/v1/projects/{project_id}/constitution/approve",
        json={"approve": True},
        headers=user_auth_headers,
    )

    # 2. Compile package
    compile_resp = await client.post(
        f"/api/v1/projects/{project_id}/compile",
        json={"target_environment": "google-antigravity", "output_type": "complete_package"},
        headers=user_auth_headers,
    )
    package_id = compile_resp.json()["id"]

    # 3. Create Evaluation Suite with passing and failing assertions
    suite_payload = {
        "name": "Core Safety & Adherence Suite",
        "description": "Validates that target instructions adhere to invariants.",
        "test_cases": [
            {
                "id": "tc-1",
                "description": "Check for verification directive",
                "input_vars": {"task": "implement_feature"},
                "expected_output_patterns": ["TARGET INSTRUCTIONS", "correctness"],
                "assertion_type": "contains",
            },
            {
                "id": "tc-2",
                "description": "Check that prompt does not contain prohibited bypass language",
                "input_vars": {"task": "security_check"},
                "expected_output_patterns": ["bypass all rules"],
                "assertion_type": "not_contains",
            },
        ],
    }
    suite_resp = await client.post(
        f"/api/v1/projects/{project_id}/eval/suites",
        json=suite_payload,
        headers=user_auth_headers,
    )
    assert suite_resp.status_code == 201
    suite_id = suite_resp.json()["suite_id"]

    # 4. Run Evaluation
    run_resp = await client.post(
        f"/api/v1/projects/{project_id}/eval/run",
        json={"suite_id": suite_id, "package_id": package_id, "model_id": "promptiq-mock-v1"},
        headers=user_auth_headers,
    )
    assert run_resp.status_code == 200
    run_data = run_resp.json()

    assert run_data["total_cases"] == 2
    assert run_data["passed_cases"] == 2
    assert run_data["pass_rate"] == 100.0
    assert run_data["cost_estimate"] == 0.0  # Zero-price invariant

    # 5. Cross-project isolation: Attempting to run with a package not belonging to project fails
    cross_resp = await client.post(
        f"/api/v1/projects/{project_id}/eval/run",
        json={"suite_id": suite_id, "package_id": "non-existent-or-other-pkg", "model_id": "promptiq-mock-v1"},
        headers=user_auth_headers,
    )
    assert cross_resp.status_code == 404


def test_promptfoo_exporter():
    """Verifies that Promptfoo exporter formats valid YAML/JSON test structures."""
    suite = EvaluationSuite(
        id="suite-123",
        project_id="proj-456",
        name="Security Benchmark",
        test_cases=[
            {
                "description": "Check output JSON validity",
                "input_vars": {"query": "sample"},
                "expected_output_patterns": ["valid_json"],
                "assertion_type": "contains",
            }
        ],
    )
    config = PromptfooExporter.export_suite(suite, prompt_path="prompt.md")

    assert "prompts" in config
    assert "providers" in config
    assert "tests" in config
    assert config["tests"][0]["assert"][0]["value"] == "valid_json"
