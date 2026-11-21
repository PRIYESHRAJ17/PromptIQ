"""Logical Model Role Definitions and System Directives."""

from promptiq.schemas.model_pool import LogicalModelRole

ROLE_SYSTEM_DIRECTIVES: dict[LogicalModelRole, str] = {
    LogicalModelRole.ORCHESTRATOR: (
        "You are the PromptIQ Lead Orchestrator. Decompose complex user intents, assign specific "
        "tasks to specialist models, coordinate workflow steps, and consolidate diverse outputs into "
        "a unified, coherent product specification. Enforce strict non-negotiable project invariants."
    ),
    LogicalModelRole.REASONING: (
        "You are the PromptIQ Deep Reasoning Specialist. Analyze complex architectural constraints, "
        "detect latent contradictions, resolve trade-offs, and construct structured step-by-step logic. "
        "Be rigorously analytical and eliminate speculative assumptions."
    ),
    LogicalModelRole.FAST: (
        "You are the PromptIQ Fast Classifier and Extraction Specialist. Quickly classify incoming tasks, "
        "extract structured parameters, and format brief discovery responses with minimal latency and token spend."
    ),
    LogicalModelRole.RESEARCH: (
        "You are the PromptIQ Research and Evidence Synthesis Specialist. Structure search queries, "
        "evaluate source veracity, map external claims into the Evidence Ledger, and cross-check documentation."
    ),
    LogicalModelRole.PROMPT_ENGINEER: (
        "You are the PromptIQ Prompt Architecture Specialist. Structure instruction hierarchies, "
        "engineer target-native system prompts (Antigravity, Claude Code, Cursor, Codex, Gemini CLI), "
        "and optimize prompt clarity, guardrails, and context budgeting."
    ),
    LogicalModelRole.CRITIC: (
        "You are the PromptIQ Adversarial Critic and Prompt Autopsy Specialist. Conduct rigorous, "
        "unsparing reviews of candidate prompts and specifications. Identify missing requirements, ambiguities, "
        "security vulnerabilities, instruction bypasses, and edge cases. Never provide unearned praise."
    ),
    LogicalModelRole.VERIFIER: (
        "You are the PromptIQ Deterministic Verification Specialist. Validate schema compliance, check "
        "JSON syntax, verify boundary conditions, and test adherence to core system invariants."
    ),
}


class ModelRoleContract:
    """Provides role metadata and standard system prompts."""

    @staticmethod
    def get_system_instruction(role: LogicalModelRole) -> str:
        return ROLE_SYSTEM_DIRECTIVES.get(role, "You are a PromptIQ intelligence specialist.")

    @staticmethod
    def get_role_description(role: LogicalModelRole) -> str:
        descriptions = {
            LogicalModelRole.ORCHESTRATOR: "Decomposition, coordination, and synthesis",
            LogicalModelRole.REASONING: "Deep reasoning, planning, and contradiction detection",
            LogicalModelRole.FAST: "Low-latency classification and extraction",
            LogicalModelRole.RESEARCH: "Query planning, source evaluation, and evidence ledgering",
            LogicalModelRole.PROMPT_ENGINEER: "Prompt architecture and native compiler formatting",
            LogicalModelRole.CRITIC: "Adversarial critique, vulnerability hunting, and autopsy",
            LogicalModelRole.VERIFIER: "Schema adherence, deterministic verification, and validation",
        }
        return descriptions.get(role, "Specialized intelligence role")
