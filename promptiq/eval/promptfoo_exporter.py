"""Promptfoo configuration exporter."""

from typing import Any

from promptiq.models.eval import EvaluationSuite


class PromptfooExporter:
    """Exports PromptIQ evaluation suites to Promptfoo-compatible YAML/JSON test structures."""

    @staticmethod
    def export_suite(suite: EvaluationSuite, prompt_path: str = "prompt.md") -> dict[str, Any]:
        """Translates an EvaluationSuite into Promptfoo configuration dictionary."""
        promptfoo_tests = []

        for case in suite.test_cases:
            test_entry: dict[str, Any] = {
                "description": case.get("description", "Evaluation case"),
                "vars": case.get("input_vars", {}),
            }

            assertions = []
            for pattern in case.get("expected_output_patterns", []):
                assertion_type = case.get("assertion_type", "contains")
                if assertion_type == "contains":
                    assertions.append({"type": "contains", "value": pattern})
                elif assertion_type == "not_contains":
                    assertions.append({"type": "not-contains", "value": pattern})
                elif assertion_type == "regex":
                    assertions.append({"type": "regex", "value": pattern})

            if assertions:
                test_entry["assert"] = assertions

            promptfoo_tests.append(test_entry)

        return {
            "prompts": [prompt_path],
            "providers": ["promptiq-managed-gateway"],
            "tests": promptfoo_tests,
            "metadata": {
                "suite_id": suite.id,
                "project_id": suite.project_id,
                "exported_by": "PromptIQ Evaluation Engine",
            },
        }
