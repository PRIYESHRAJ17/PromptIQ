import asyncio
from sqlalchemy import select
from promptiq.core.database import async_session_factory, init_db
from promptiq.models.user import User
from promptiq.services.project_service import ProjectService
from promptiq.schemas.project import ProjectCreate
from promptiq.models.job import WorkflowJob
from promptiq.services.job_service import WorkflowJobService

async def run_food_donation_slice():
    await init_db()
    async with async_session_factory() as db:
        # Find developer user
        user_res = await db.execute(select(User).where(User.email == 'priyesh@promptiq.org'))
        user = user_res.scalar_one_or_none()
        if not user:
            user = User(email='priyesh@promptiq.org', full_name='Priyesh Raj', hashed_password='dummy')
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Create or find project
        proj = await ProjectService.create_project(
            db,
            user_id=user.id,
            project_in=ProjectCreate(
                name='Food Donation Redistribution Platform',
                description='Secure food donation and surplus redistribution web platform.',
            )
        )
        await db.commit()
        await db.refresh(proj)

        objective = (
            "Build a secure food donation and surplus food redistribution web application. "
            "Define its main modules, user roles, technical architecture, implementation plan, "
            "acceptance criteria and first development task."
        )

        # Create Job
        job = WorkflowJob(
            project_id=proj.id,
            workspace_id=proj.workspace_id,
            user_id=user.id,
            operation_type='agent_workflow',
            current_stage='intent_understanding',
            checkpoint_data={
                'objective': objective,
                'task_type': 'software_engineering',
                'depth': 'deep',
                'target': 'google-antigravity',
            },
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        job_id = job.id
        print(f"Created Workflow Job: {job_id}")

    # Execute workflow slice
    print(f"Executing Workflow Job {job_id}...")
    async with async_session_factory() as exec_db:
        await WorkflowJobService.execute_agent_workflow_job(exec_db, job_id, worker_id="worker-slice-1")
        await exec_db.commit()

    # Verify result
    async with async_session_factory() as db:
        res = await db.execute(select(WorkflowJob).where(WorkflowJob.id == job_id))
        executed_job = res.scalar_one()
        print(f"Job Status: {executed_job.status}")
        print(f"Current Stage: {executed_job.current_stage}")
        result_data = executed_job.result_data or {}
        subtasks = result_data.get("subtasks", [])
        iterations = result_data.get("iterations", [])
        duration = result_data.get("total_duration_ms")
        deliverable = result_data.get("deliverable", "")

        print(f"Subtasks count: {len(subtasks)}")
        print(f"Iterations count: {len(iterations)}")
        print(f"Total duration: {duration} ms")
        print("Deliverable:")
        print(deliverable)

if __name__ == "__main__":
    asyncio.run(run_food_donation_slice())
