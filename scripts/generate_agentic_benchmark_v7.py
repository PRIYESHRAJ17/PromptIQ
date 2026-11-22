"""Generates tests/fixtures/agentic_benchmark_v7.json containing 50 diverse agentic benchmarks across all 10 task families."""

import json
from pathlib import Path

FAMILIES = [
    "software_engineering",
    "research_intelligence",
    "ai_agent_development",
    "business_strategy",
    "prompt_improvement",
    "product_development",
    "writing_content",
    "data_analysis",
    "technical_documentation",
    "education_learning",
]

TEMPLATES = {
    "software_engineering": [
        ("Implement distributed idempotency key middleware for FastAPI", "high", False),
        ("Refactor legacy async database connection pooling to handle failover", "medium", True),
        ("Develop deterministic rate limiter using token bucket algorithm", "medium", False),
        ("Patch unsafe subprocess invocation with sanitized argument list", "high", True),
        ("Build automated database migration rollback verification suite", "medium", False),
    ],
    "research_intelligence": [
        (
            "Synthesize state-of-the-art vector indexing techniques for low-latency search",
            "medium",
            False,
        ),
        (
            "Investigate zero-price inference tier stability across global cloud providers",
            "high",
            True,
        ),
        (
            "Analyze trade-offs between local embedding models and remote embedding APIs",
            "medium",
            False,
        ),
        (
            "Verify factual support for latency claims in distributed storage whitepapers",
            "high",
            True,
        ),
        ("Compare memory footprint of SQLite WAL mode versus PostgreSQL embedded", "low", False),
    ],
    "ai_agent_development": [
        ("Design an 11-stage observe-decide-act loop with bounded permission tiers", "high", False),
        ("Implement cyclic dependency detector for autonomous agent task DAGs", "medium", True),
        (
            "Build deterministic tool call verification harness with schema assertions",
            "medium",
            False,
        ),
        ("Author agent fallback protocol for degraded inference provider response", "high", True),
        ("Construct agent execution trace visualizer with millisecond precision", "medium", False),
    ],
    "business_strategy": [
        ("Formulate zero-price unit economics model for hosted developer tools", "medium", False),
        (
            "Evaluate competitive positioning of PromptIQ versus commercial prompt suites",
            "high",
            True,
        ),
        ("Develop developer adoption strategy focusing on open MCP ecosystem", "medium", False),
        ("Audit risk mitigation strategy for open-source AI platform compliance", "high", True),
        ("Create SLA framework for non-commercial community agent platforms", "low", False),
    ],
    "prompt_improvement": [
        (
            "Optimize system instruction for structured JSON extraction without markdown fences",
            "medium",
            False,
        ),
        (
            "Remediate severe ambiguity and missing output schemas in multi-turn prompts",
            "high",
            True,
        ),
        (
            "Compile multi-target prompt package for Claude Code and Google Antigravity",
            "medium",
            False,
        ),
        ("Eliminate contradictory constraints in complex agent system instructions", "high", True),
        ("Refactor monolithic prompt into composable dynamic context modules", "medium", False),
    ],
    "product_development": [
        (
            "Define product requirements document for cross-surface session continuity",
            "medium",
            False,
        ),
        ("Design telemetry specification for agent execution without logging PII", "high", True),
        (
            "Specify user-approval workflow for destructive agentic tool invocations",
            "medium",
            False,
        ),
        (
            "Map error recovery user journey when background workflow encounters rate limit",
            "high",
            True,
        ),
        ("Draft feature roadmap for MCP server extensions in PromptIQ", "low", False),
    ],
    "writing_content": [
        ("Draft engineering deep dive on deterministic DAG scheduling in Python", "medium", False),
        ("Author technical blog post on zero-price hosted AI architectures", "high", True),
        ("Write comprehensive release notes for PromptIQ V7 major milestone", "medium", False),
        (
            "Compose developer tutorial on writing custom MCP tools with permission bounds",
            "high",
            True,
        ),
        (
            "Draft incident post-mortem template for distributed workflow worker crashes",
            "low",
            False,
        ),
    ],
    "data_analysis": [
        (
            "Analyze latency distribution percentiles (p50, p95, p99) of model gateway",
            "medium",
            False,
        ),
        ("Detect anomalous execution spikes across background worker job queues", "high", True),
        ("Compute token consumption efficiency across prompt compilation targets", "medium", False),
        ("Evaluate test coverage correlation with defect escape rates in releases", "high", True),
        (
            "Profile SQLite database query execution plans for context pack compilation",
            "low",
            False,
        ),
    ],
    "technical_documentation": [
        (
            "Document complete OpenAPI contract for PromptIQ Project Constitution API",
            "medium",
            False,
        ),
        (
            "Author comprehensive architecture guide on tenant isolation and row-level security",
            "high",
            True,
        ),
        (
            "Write deployment manual for air-gapped internal PromptIQ agent instances",
            "medium",
            False,
        ),
        (
            "Document security boundary between MCP clients and host execution environment",
            "high",
            True,
        ),
        ("Produce reference manual for PromptIQ Task Family Specialization Registry", "low", False),
    ],
    "education_learning": [
        ("Design interactive curriculum on autonomous agent loop architecture", "medium", False),
        ("Develop hands-on coding lab for building custom SSRF-safe tool plugins", "high", True),
        ("Create training module on identifying prompt injection attack vectors", "medium", False),
        ("Author step-by-step tutorial on debugging DAG execution deadlocks", "high", True),
        ("Prepare quick-reference cheat sheet for PromptIQ CLI and MCP commands", "low", False),
    ],
}


def generate_benchmark():
    tasks = []
    task_idx = 1
    replan_count = 0

    for family in FAMILIES:
        scenarios = TEMPLATES[family]
        for title, complexity, requires_replan in scenarios:
            tid = f"AGENT-{task_idx:03d}"
            if requires_replan:
                replan_count += 1
                permissions = ["read_only"]  # Restricted permissions trigger permission replan/skip
            else:
                permissions = ["read_only", "reversible_modification"]

            tasks.append(
                {
                    "task_id": tid,
                    "task_family": family,
                    "task_name": title,
                    "objective": f"{title}. Deliver verifiable artifacts with clear status.",
                    "complexity": complexity,
                    "requires_replan": requires_replan,
                    "granted_permissions": permissions,
                    "expected_status": "completed",
                }
            )
            task_idx += 1

    assert len(tasks) == 50, f"Expected 50 tasks, got {len(tasks)}"
    assert replan_count == 20, f"Expected 20 replan tasks, got {replan_count}"

    output_path = Path("tests/fixtures/agentic_benchmark_v7.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"benchmark_version": "v7", "total_tasks": 50, "tasks": tasks}, f, indent=2)

    print(f"Generated {len(tasks)} tasks ({replan_count} replan cases) in {output_path}")


if __name__ == "__main__":
    generate_benchmark()
