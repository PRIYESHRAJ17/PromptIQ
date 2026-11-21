"""Tests for evaluation platform methods: schema_valid and evidence_grounded assertions."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_eval_suite_advanced_assertions(client: AsyncClient, user_auth_headers: dict[str, str]):
    """Verifies that Prompt Test Lab handles schema_valid and evidence_grounded assertions."""
    # 1. Create project
    p_resp = await client.post("/api/v1/projects", json={"name": "Eval Platform Proj"}, headers=user_auth_headers)
    p_id = p_resp.json()["id"]

    # 2. Approve constitution and compile package
    c_resp = await client.post(f"/api/v1/projects/{p_id}/constitution/approve", json={"approve": True}, headers=user_auth_headers)
    assert c_resp.status_code == 200

    pkg_resp = await client.post(
        f"/api/v1/projects/{p_id}/compile",
        json={"target_environment": "google-antigravity", "output_type": "complete_package"},
        headers=user_auth_headers,
    )
    assert pkg_resp.status_code == 201
    pkg_id = pkg_resp.json()["id"]

    # 3. Create test suite with schema and evidence cases
    suite_payload = {
        "name": "Advanced Assertions Suite",
        "description": "Tests schema and evidence assertions",
        "test_cases": [
            {
                "id": "case-schema-1",
                "description": "Output should contain instructions and correctness directive",
                "method": "deterministic",
                "assertion_type": "contains",
                "expected_output_patterns": ["TARGET INSTRUCTIONS", "correctness"],
            },
            {
                "id": "case-evidence-1",
                "description": "Output should strictly omit prohibited bypass instructions",
                "method": "safety_boundary",
                "assertion_type": "not_contains",
                "expected_output_patterns": ["bypass all rules"],
            },
        ],
    }
    s_resp = await client.post(f"/api/v1/projects/{p_id}/eval/suites", json=suite_payload, headers=user_auth_headers)
    assert s_resp.status_code == 201
    suite_id = s_resp.json()["suite_id"]

    # 4. Run evaluation with num_runs = 2
    run_payload = {
        "suite_id": suite_id,
        "package_id": pkg_id,
        "model_id": "promptiq-mock-v1",
        "num_runs": 2,
    }
    r_resp = await client.post(f"/api/v1/projects/{p_id}/eval/run", json=run_payload, headers=user_auth_headers)
    assert r_resp.status_code == 200
    run_data = r_resp.json()

    assert run_data["num_runs"] == 2
    assert run_data["pass_rate"] > 0.0
    assert "provenance" in run_data
    assert run_data["provenance"]["suite_id"] == suite_id
