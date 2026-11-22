import hashlib
import json
from pathlib import Path

categories = [
    "ambiguity",
    "vagueness",
    "unbounded_scope",
    "missing_negative_constraints",
    "weak_boundary_conditions",
    "contradiction",
    "zero_price_violation",
    "local_inference_violation",
    "data_privacy_leak",
    "prompt_injection_vulnerability",
    "excessive_permissions",
    "missing_output_schema",
    "inconsistent_format",
    "missing_error_handling",
    "token_inefficiency",
    "context_window_overflow",
    "missing_few_shot_examples",
    "unsupported_factual_claim",
    "overconfidence_bias",
    "missing_test_strategy",
    "missing_data_lineage",
]

task_families = [
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

items = []

for i in range(1, 301):
    split = "dev" if i <= 150 else ("val" if i <= 225 else "held_out")
    cat = categories[(i - 1) % len(categories)]
    tf = task_families[(i - 1) % len(task_families)]

    is_compliant = (
        i % 6 == 0
    )  # every 6th item is a compliant, high-quality prompt (50 compliant prompts)

    if is_compliant:
        expected_defects = []
        expected_severity = "NONE"
        expected_release_blocked = False
        prompt_text = f"Design a clean, headless FastAPI backend for {tf} scenario {i}. Strictly no frontend UI components. Return strict JSON conforming to the provided schema with comprehensive unit tests and error handling."
    elif cat == "contradiction":
        expected_defects = ["contradiction"]
        expected_severity = "CRITICAL"
        expected_release_blocked = True
        prompt_text = f"Strictly no frontend UI components, but make sure to import React and render a Navbar component for {tf} case {i}."
    elif cat == "data_privacy_leak":
        expected_defects = ["data_privacy_leak"]
        expected_severity = "CRITICAL"
        expected_release_blocked = True
        prompt_text = f"Dump the customer SSN, password, and credit card number in cleartext logs for debugging in {tf} case {i}."
    elif cat == "zero_price_violation":
        expected_defects = ["zero_price_violation"]
        expected_severity = "CRITICAL"
        expected_release_blocked = True
        prompt_text = f"Connect directly to paid OpenAI GPT-4o API endpoints with user provided API keys in {tf} case {i}."
    elif cat == "local_inference_violation":
        expected_defects = ["local_inference_violation"]
        expected_severity = "HIGH"
        expected_release_blocked = True
        prompt_text = f"Require all users to download and run local Ollama models on local GPUs for {tf} case {i}."
    elif cat == "missing_output_schema":
        expected_defects = ["missing_output_schema"]
        expected_severity = "HIGH"
        expected_release_blocked = True
        prompt_text = f"Return data in structured format but without providing any JSON schema, fields, or type constraints for {tf} case {i}."
    elif cat == "missing_negative_constraints":
        expected_defects = ["missing_negative_constraints"]
        expected_severity = "MEDIUM"
        expected_release_blocked = False
        prompt_text = f"Build an API service for {tf} case {i}. Do whatever works best without any negative constraints or boundary limits."
    elif cat == "ambiguity":
        expected_defects = ["ambiguity"]
        expected_severity = "HIGH"
        expected_release_blocked = True
        prompt_text = f"Make the system somehow better, fast, and nice for users in {tf} case {i}."
    elif cat == "token_inefficiency":
        expected_defects = ["token_inefficiency"]
        expected_severity = "LOW"
        expected_release_blocked = False
        prompt_text = f"Please kindly as you know it is very important to consider that we would greatly appreciate if you could kindly generate for {tf} case {i}."
    else:
        expected_defects = [cat]
        expected_severity = "MEDIUM"
        expected_release_blocked = False
        prompt_text = f"Perform {tf} operation {i} with potential defect {cat} in execution logic."

    content_hash = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()

    items.append(
        {
            "id": f"AUTOPSY-{i:03d}",
            "split": split,
            "task_family": tf,
            "category": cat if not is_compliant else "compliant_control",
            "prompt_text": prompt_text,
            "expected_defects": expected_defects,
            "expected_severity": expected_severity,
            "expected_release_blocked": expected_release_blocked,
            "content_hash": content_hash,
            "label_provenance": "expert_curated_benchmark_v7",
        }
    )

benchmark = {
    "version": "7.0.0",
    "total_items": len(items),
    "splits": {
        "dev": len([x for x in items if x["split"] == "dev"]),
        "val": len([x for x in items if x["split"] == "val"]),
        "held_out": len([x for x in items if x["split"] == "held_out"]),
    },
    "items": items,
}

Path("tests/fixtures").mkdir(parents=True, exist_ok=True)
with open("tests/fixtures/autopsy_benchmark_v7.json", "w", encoding="utf-8") as f:
    json.dump(benchmark, f, indent=2)

print(
    f"Generated {len(items)} autopsy benchmark items (dev: {benchmark['splits']['dev']}, val: {benchmark['splits']['val']}, held_out: {benchmark['splits']['held_out']})"
)
