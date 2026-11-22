import json
from pathlib import Path

task_families = [
    {
        "id": "software_engineering",
        "tools": ["filesystem_read", "filesystem_write", "subprocess_exec", "validator_exec"],
        "dag_nodes": [
            "task-01-intent",
            "task-02-research",
            "task-03-specification",
            "task-04-generate",
            "task-07-verify",
        ],
        "eval_method": "deterministic_assertions",
        "sample_goal": "Implement asynchronous token bucket rate limiting middleware in FastAPI",
    },
    {
        "id": "research_intelligence",
        "tools": ["http_fetch", "data_transform", "validator_exec"],
        "dag_nodes": [
            "task-01-intent",
            "task-02-research",
            "task-03-specification",
            "task-04-generate",
            "task-07-verify",
        ],
        "eval_method": "source_citation_grounding",
        "sample_goal": "Investigate consensus algorithms across Raft, Paxos, and Viewstamped Replication",
    },
    {
        "id": "ai_agent_development",
        "tools": ["filesystem_read", "validator_exec"],
        "dag_nodes": [
            "task-01-intent",
            "task-02-research",
            "task-03-specification",
            "task-04-generate",
            "task-07-verify",
        ],
        "eval_method": "permission_boundary_validation",
        "sample_goal": "Design autonomous multi-agent tool execution loop with permission levels",
    },
    {
        "id": "business_strategy",
        "tools": ["data_transform", "validator_exec"],
        "dag_nodes": [
            "task-01-intent",
            "task-03-specification",
            "task-04-generate",
            "task-07-verify",
        ],
        "eval_method": "strategic_rubric_scoring",
        "sample_goal": "Formulate 3-year market penetration roadmap for enterprise AI workflow platform",
    },
    {
        "id": "prompt_improvement",
        "tools": ["validator_exec"],
        "dag_nodes": [
            "task-01-intent",
            "task-03-specification",
            "task-04-generate",
            "task-05-critique",
            "task-07-verify",
        ],
        "eval_method": "token_density_and_autopsy",
        "sample_goal": "Refactor vague SQL generation prompt into target-native Claude Code instructions",
    },
    {
        "id": "product_development",
        "tools": ["filesystem_write", "validator_exec"],
        "dag_nodes": [
            "task-01-intent",
            "task-03-specification",
            "task-04-generate",
            "task-07-verify",
        ],
        "eval_method": "prd_completeness_matrix",
        "sample_goal": "Author comprehensive Product Requirements Document for distributed audit ledger",
    },
    {
        "id": "writing_content",
        "tools": ["validator_exec"],
        "dag_nodes": [
            "task-01-intent",
            "task-03-specification",
            "task-04-generate",
            "task-07-verify",
        ],
        "eval_method": "stylistic_and_length_rubric",
        "sample_goal": "Compose technical whitepaper explaining cryptographic fencing tokens in distributed jobs",
    },
    {
        "id": "data_analysis",
        "tools": ["data_transform", "validator_exec"],
        "dag_nodes": [
            "task-01-intent",
            "task-03-specification",
            "task-04-generate",
            "task-07-verify",
        ],
        "eval_method": "statistical_summary_assertions",
        "sample_goal": "Perform exploratory anomaly detection and percentile analysis on cluster latency logs",
    },
    {
        "id": "technical_documentation",
        "tools": ["filesystem_read", "validator_exec"],
        "dag_nodes": [
            "task-01-intent",
            "task-03-specification",
            "task-04-generate",
            "task-07-verify",
        ],
        "eval_method": "api_schema_fidelity_check",
        "sample_goal": "Generate OpenAPI 3.1 compatible reference documentation for WorkflowJob REST API",
    },
    {
        "id": "education_learning",
        "tools": ["validator_exec"],
        "dag_nodes": [
            "task-01-intent",
            "task-03-specification",
            "task-04-generate",
            "task-07-verify",
        ],
        "eval_method": "pedagogical_progression_check",
        "sample_goal": "Develop modular 6-part curriculum on distributed systems concurrency and consensus",
    },
]

scenarios = []
for tf in task_families:
    # 10 dev + 10 held-out
    for i in range(1, 21):
        is_held_out = i > 10
        split = "held_out" if is_held_out else "dev"
        sc_id = f"TF-{tf['id'][:4].upper()}-{split[:4].upper()}-{i:02d}"
        goal = f"{tf['sample_goal']} - Scenario {i} ({'Held-out Test' if is_held_out else 'Development'})"

        scenarios.append(
            {
                "scenario_id": sc_id,
                "task_family": tf["id"],
                "split": split,
                "is_held_out": is_held_out,
                "goal": goal,
                "expected_tools": tf["tools"],
                "expected_dag_subtasks": tf["dag_nodes"],
                "eval_method": tf["eval_method"],
                "constraints": ["Strictly no frontend UI", "Zero-price hosted gateway exclusively"],
            }
        )

dataset = {
    "version": "7.0.0",
    "total_scenarios": len(scenarios),
    "task_family_count": len(task_families),
    "scenarios_per_family": 20,
    "scenarios": scenarios,
}

Path("tests/fixtures").mkdir(parents=True, exist_ok=True)
with open("tests/fixtures/task_families_benchmark_v7.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2)

print(f"Generated {len(scenarios)} task-family scenarios across {len(task_families)} families.")
