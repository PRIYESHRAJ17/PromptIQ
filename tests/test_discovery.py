"""Test Adaptive Discovery Engine, Question Paths, and Context Extraction."""

import pytest
from httpx import AsyncClient

from promptiq.discovery.extractor import ContextExtractor
from promptiq.discovery.task_paths import get_task_questions


@pytest.mark.asyncio
async def test_initial_four_input_intake(client: AsyncClient, user_auth_headers: dict[str, str]):
    """Tests the initial 4-input discovery intake endpoint."""
    # 1. Create a project
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Discovery Test Project"},
        headers=user_auth_headers,
    )
    project_id = proj_resp.json()["id"]

    # 2. Start discovery with 4 inputs
    intake_payload = {
        "goal": "Build an enterprise incident management CLI in Python and PostgreSQL",
        "deliverable": "complete_package",
        "target": "google-antigravity",
        "target_mode": "specific",
        "context_text": "We need role-based access for Admin and Operator. Uses FastAPI and SQLAlchemy.",
        "depth": "guided",
        "task_type": "software_project",
    }
    disc_resp = await client.post(
        f"/api/v1/projects/{project_id}/discovery/start",
        json=intake_payload,
        headers=user_auth_headers,
    )
    assert disc_resp.status_code == 201
    data = disc_resp.json()

    assert data["project_id"] == project_id
    assert data["depth"] == "guided"
    assert len(data["next_questions"]) > 0

    # Verify extracted facts from context
    extracted = data["extracted_facts"]
    assert any("python" in f["fact"].lower() for f in extracted)
    assert any("admin" in f["fact"].lower() for f in extracted)

    # 3. Submit answers to discovery questions
    session_id = data["id"]
    ans_resp = await client.post(
        f"/api/v1/projects/{project_id}/discovery/sessions/{session_id}/answers",
        json={
            "answers": {
                "problem_statement": "Incident response is slow and uncoordinated.",
                "must_have_features": "Real-time alerts, incident timeline, audit trail.",
            }
        },
        headers=user_auth_headers,
    )
    assert ans_resp.status_code == 200
    ans_data = ans_resp.json()
    assert "problem_statement" in ans_data["answers"]

    # 4. Verify that answered questions are not re-asked (Anti-fatigue invariant)
    next_q_ids = [q["id"] for q in ans_data["next_questions"]]
    assert "problem_statement" not in next_q_ids


@pytest.mark.asyncio
async def test_context_extractor():
    """Tests regex and entity extraction from untrusted context text."""
    sample_text = (
        "Project requires Python 3.13 and FastAPI with PostgreSQL backend. "
        "User roles: Admin, Developer, Customer."
    )
    facts = ContextExtractor.extract_facts_from_text(sample_text, source_label="notes.txt")

    assert len(facts) >= 2
    categories = [f["category"] for f in facts]
    assert "technical" in categories
    assert "users" in categories


@pytest.mark.asyncio
async def test_task_specific_question_paths():
    """Tests specialized question generation for various task types."""
    q_prompt = get_task_questions("prompt_creation", answered_keys=set())
    assert any(q.id == "audience" for q in q_prompt)

    q_research = get_task_questions("research", answered_keys=set())
    assert any(q.id == "source_hierarchy" for q in q_research)

    q_improvement = get_task_questions("prompt_improvement", answered_keys={"existing_prompt"})
    # Answered 'existing_prompt' must not be re-asked
    assert not any(q.id == "existing_prompt" for q in q_improvement)
    assert any(q.id == "current_failures" for q in q_improvement)
