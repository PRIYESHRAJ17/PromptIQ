"""Project Constitution Change-Impact Analysis and Requirement DAG Validation."""

from typing import Any

from pydantic import BaseModel, Field


class ChangeImpactReport(BaseModel):
    has_breaking_changes: bool
    requires_recompilation: bool
    requires_reautopsy: bool
    requires_reevaluation: bool
    invalidated_components: list[str] = Field(default_factory=list)
    impact_summary: list[str] = Field(default_factory=list)
    remediation_actions: list[str] = Field(default_factory=list)


class ConstitutionChangeImpactAnalyzer:
    """Analyzes differences between constitution versions and identifies affected downstream artifacts."""

    @classmethod
    def validate_requirement_dependencies(cls, requirements: list[dict[str, Any]]) -> list[str]:
        """Validates that requirement dependency graph has no missing prerequisites or circular dependencies."""
        errors: list[str] = []
        req_ids = {r.get("id") for r in requirements if r.get("id")}

        # 1. Check for missing prerequisites
        for r in requirements:
            r_id = r.get("id")
            deps = r.get("depends_on", []) or []
            for dep in deps:
                if dep not in req_ids:
                    errors.append(
                        f"Requirement '{r_id}' depends on non-existent requirement '{dep}'."
                    )

        # 2. Cycle detection (Tarjan or DFS)
        adj: dict[str, list[str]] = {
            r.get("id"): r.get("depends_on", []) or [] for r in requirements if r.get("id")
        }
        visited: dict[str, int] = {}  # 0 = unvisited, 1 = visiting, 2 = visited

        def dfs(node: str, path: list[str]) -> bool:
            visited[node] = 1
            path.append(node)
            for neighbor in adj.get(node, []):
                if neighbor in visited and visited[neighbor] == 1:
                    cycle = " -> ".join(path + [neighbor])
                    errors.append(f"Circular dependency detected in requirements: {cycle}")
                    return True
                if neighbor not in visited and dfs(neighbor, path):
                    return True
            path.pop()
            visited[node] = 2
            return False

        for node in adj:
            if node not in visited:
                dfs(node, [])

        return errors

    @classmethod
    def analyze_change_impact(
        cls,
        old_constitution: dict[str, Any],
        new_constitution: dict[str, Any],
    ) -> ChangeImpactReport:
        """Determines downstream invalidation impact between two constitution versions."""
        invalidated: list[str] = []
        summary: list[str] = []
        remediation: list[str] = []
        breaking = False
        recompile = False
        reautopsy = False
        reeval = False

        # 1. Goal changes
        old_goals = set(old_constitution.get("goals") or [])
        new_goals = set(new_constitution.get("goals") or [])
        if old_goals != new_goals:
            breaking = True
            recompile = True
            reautopsy = True
            reeval = True
            invalidated.append("primary_goals")
            summary.append(
                f"Goals modified: {len(new_goals - old_goals)} added, {len(old_goals - new_goals)} removed"
            )
            remediation.append(
                "Recompile target prompt packages and execute new test lab evaluation suite"
            )

        # 2. Scope changes (Out of scope / non-goals)
        old_scope = old_constitution.get("scope", {}) or {}
        new_scope = new_constitution.get("scope", {}) or {}
        old_oos = set(old_scope.get("out_of_scope", []) or [])
        new_oos = set(new_scope.get("out_of_scope", []) or [])
        if old_oos != new_oos:
            recompile = True
            reautopsy = True
            invalidated.append("scope_exclusions")
            added_exclusions = new_oos - old_oos
            if added_exclusions:
                breaking = True
                summary.append(f"New prohibitions added to scope: {', '.join(added_exclusions)}")
                remediation.append(
                    "Re-run Prompt Autopsy to verify compliance with new prohibitions"
                )

        # 3. Technical Direction changes
        old_tech = old_constitution.get("technical_direction", {}) or {}
        new_tech = new_constitution.get("technical_direction", {}) or {}
        if old_tech != new_tech:
            recompile = True
            invalidated.append("technical_direction")
            summary.append("Technical stack or architecture pattern modified")
            remediation.append("Regenerate PPS target compilation for new technical configuration")

        # 4. Requirement changes
        old_reqs = {
            r.get("id"): r.get("text")
            for r in old_constitution.get("requirements", [])
            if r.get("id")
        }
        new_reqs = {
            r.get("id"): r.get("text")
            for r in new_constitution.get("requirements", [])
            if r.get("id")
        }
        if old_reqs != new_reqs:
            recompile = True
            reeval = True
            invalidated.append("requirements")
            added_reqs = set(new_reqs.keys()) - set(old_reqs.keys())
            removed_reqs = set(old_reqs.keys()) - set(new_reqs.keys())
            if removed_reqs or added_reqs:
                summary.append(f"Requirements delta: +{len(added_reqs)}, -{len(removed_reqs)}")
                remediation.append(
                    "Update PPS specification requirements and regenerate target prompts"
                )

        return ChangeImpactReport(
            has_breaking_changes=breaking,
            requires_recompilation=recompile,
            requires_reautopsy=reautopsy,
            requires_reevaluation=reeval,
            invalidated_components=invalidated,
            impact_summary=summary,
            remediation_actions=remediation,
        )
