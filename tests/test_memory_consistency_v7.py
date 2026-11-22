"""Comprehensive multi-session persistent memory consistency test suite covering all 10 V7 scenarios."""

import pytest

from promptiq.core.database import async_session_factory, init_db
from promptiq.mcp.server import handle_tool_call
from promptiq.memory.checkpoint import CheckpointManager
from promptiq.memory.context_compiler import ContextCompiler
from promptiq.schemas.auth import UserCreate
from promptiq.schemas.constitution import (
    ConstitutionApprovalRequest,
    ConstitutionUpdate,
    DecisionRecord,
    RequirementItem,
)
from promptiq.schemas.memory import CheckpointCreate, ContextPackRequest
from promptiq.schemas.project import ProjectCreate
from promptiq.services.auth_service import AuthService
from promptiq.services.constitution_service import ConstitutionService
from promptiq.services.job_service import WorkflowJobService
from promptiq.services.project_service import ProjectService


@pytest.mark.asyncio
async def test_persistent_memory_ten_scenarios_continuity():
    await init_db()
    async with async_session_factory() as db:
        # Provision test user and project
        user, _ = await AuthService.register_user(
            db,
            user_in=UserCreate(
                email="memory_test_user@promptiq.internal",
                password="Password123!",
                full_name="Memory Tester",
            ),
        )
        project = await ProjectService.create_project(
            db,
            user.id,
            ProjectCreate(
                name="Continuous Memory System", description="Testing persistent memory continuity"
            ),
        )
        project_id = project.id

        # -------------------------------------------------------------
        # Scenario 1: Store an important project decision
        # -------------------------------------------------------------
        await ConstitutionService.get_current_constitution(db, project_id, user.id)
        update_1 = ConstitutionUpdate(
            goals=["Build durable event-driven processing pipeline"],
            decisions=[
                {
                    "id": "DEC-001",
                    "decision": "Use Redis Sentinel for distributed queueing",
                    "rationale": "High throughput and automated leader failover",
                    "status": "active",
                    "version": 1,
                    "date": "2026-11-22",
                }
            ],
            requirements=[
                RequirementItem(
                    id="REQ-001",
                    text="Pipeline must process at least 1000 events per second",
                    priority="P0",
                )
            ],
            scope_out=["Website frontend UI"],
        )
        await ConstitutionService.update_constitution(db, project_id, user.id, update_1)
        await ConstitutionService.approve_constitution(
            db, project_id, user.id, ConstitutionApprovalRequest(approve=True)
        )

        # -------------------------------------------------------------
        # Scenario 2 & 3: Start new session and retrieve the decision
        # -------------------------------------------------------------
        pack_req = ContextPackRequest(max_token_budget=4000)
        pack_res = await ContextCompiler.compile_context(db, project_id, user.id, pack_req)
        assert "DEC-001" in pack_res.packed_context_markdown
        assert "Redis Sentinel" in pack_res.packed_context_markdown
        assert "goals" in pack_res.items_included

        # -------------------------------------------------------------
        # Scenario 4 & 5: Change the decision and verify old is superseded
        # -------------------------------------------------------------
        update_2 = ConstitutionUpdate(
            decisions=[
                DecisionRecord(
                    id="DEC-001",
                    decision="Use Redis Sentinel for distributed queueing",
                    rationale="Initial choice",
                    date="2026-11-22",
                ),
                DecisionRecord(
                    id="DEC-002",
                    decision="Use NATS JetStream for distributed event streaming",
                    rationale="Native stream persistence and subject-based routing",
                    supersedes="DEC-001",
                    date="2026-11-22",
                ),
            ]
        )
        await ConstitutionService.update_constitution(db, project_id, user.id, update_2)
        const_v2 = await ConstitutionService.get_current_constitution(db, project_id, user.id)
        assert len(const_v2.decisions) == 2
        superseding_decisions = [d for d in const_v2.decisions if d.get("supersedes") == "DEC-001"]
        assert len(superseding_decisions) == 1
        assert superseding_decisions[0]["id"] == "DEC-002"

        # -------------------------------------------------------------
        # Scenario 6: Historical context query
        # -------------------------------------------------------------
        await CheckpointManager.create_checkpoint(
            db,
            project_id,
            user.id,
            CheckpointCreate(
                phase="architecture_baseline",
                summary="Migrated event streaming from Redis Sentinel to NATS JetStream in DEC-002",
            ),
        )
        checkpoints = await CheckpointManager.list_checkpoints(db, project_id, user.id)
        assert any("NATS JetStream" in c.summary for c in checkpoints)

        # -------------------------------------------------------------
        # Scenario 7 & 8: Contradictory fact detection & resolution
        # -------------------------------------------------------------
        conflicts = ContextCompiler.detect_memory_conflicts(
            decisions=[
                {
                    "id": "DEC-UI",
                    "decision": "Strictly no frontend components",
                    "rationale": "Backend only",
                }
            ],
            requirements=[{"id": "REQ-UI", "text": "Must render a React dashboard for monitoring"}],
        )
        assert len(conflicts) > 0
        assert "no-frontend" in conflicts[0]

        # -------------------------------------------------------------
        # Scenario 9: Resume interrupted workflow job
        # -------------------------------------------------------------
        job = await WorkflowJobService.create_job(
            db=db,
            user_id=user.id,
            workspace_id=project.workspace_id,
            operation_type="agent_workflow",
            project_id=project_id,
            checkpoint_data={"objective": "Test workflow continuity", "stage": "interrupted"},
        )
        await WorkflowJobService.pause_job(db, job.id, reason="Simulated pause for approval")
        resumed_job = await WorkflowJobService.resume_job(db, job.id, user.id, project.workspace_id)
        assert resumed_job.status == "QUEUED"
        assert resumed_job.retry_count == 1

        # -------------------------------------------------------------
        # Scenario 10: Cross-surface retrieval (MCP tool call)
        # -------------------------------------------------------------
        mcp_res = await handle_tool_call(
            tool_name="forge.get_context_pack",
            arguments={"project_id": project_id, "max_token_budget": 5000},
            user_id=user.id,
            db=db,
        )
        assert "packed_context_markdown" in mcp_res
        assert "Continuous Memory System" in mcp_res["packed_context_markdown"]

        await db.commit()
