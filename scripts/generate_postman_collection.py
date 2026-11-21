"""Generates Postman Collection v2.1 and Environment files from docs/openapi.json."""

import json
from pathlib import Path


def generate_postman_assets():
    openapi_path = Path("docs/openapi.json")
    if not openapi_path.exists():
        print("docs/openapi.json not found!")
        return

    with open(openapi_path, encoding="utf-8") as f:
        spec = json.load(f)

    # Base collection
    collection = {
        "info": {
            "_postman_id": "promptiq-core-api-v1",
            "name": "PromptIQ Core API",
            "description": (
                "Postman API Collection for PromptIQ: Universal Prompt Intelligence, "
                "Project Engineering, and Cross-Agent Continuity Platform.\n\n"
                "**Core Invariants**:\n"
                "- $0 User Cost / 100% Free\n"
                "- Zero BYOK (Strictly no user-supplied keys)\n"
                "- No local GPU / inference required\n"
                "- Website frontend strictly out of scope\n"
            ),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "auth": {
            "type": "bearer",
            "bearer": [
                {
                    "key": "token",
                    "value": "{{bearerToken}}",
                    "type": "string"
                }
            ]
        },
        "item": [],
        "variable": [
            {"key": "baseUrl", "value": "http://localhost:8000", "type": "string"},
            {"key": "bearerToken", "value": "", "type": "string"},
            {"key": "projectId", "value": "", "type": "string"},
            {"key": "sessionId", "value": "", "type": "string"},
            {"key": "packageId", "value": "", "type": "string"},
        ]
    }

    folders: dict[str, list] = {}

    paths = spec.get("paths", {})
    for path, methods in paths.items():
        for method, op in methods.items():
            if method not in ("get", "post", "put", "delete", "patch"):
                continue

            tags = op.get("tags", ["General"])
            tag = tags[0] if tags else "General"

            summary = op.get("summary", path)
            description = op.get("description", "")

            # URL formatting with Postman variables
            pm_path = path.replace("{project_id}", "{{projectId}}").replace("{session_id}", "{{sessionId}}").replace("{package_id}", "{{packageId}}").replace("{version}", "1")
            path_segments = [p for p in pm_path.strip("/").split("/") if p]

            request_item = {
                "name": summary,
                "request": {
                    "method": method.upper(),
                    "header": [
                        {"key": "Accept", "value": "application/json", "type": "text"}
                    ],
                    "url": {
                        "raw": "{{baseUrl}}/" + "/".join(path_segments),
                        "host": ["{{baseUrl}}"],
                        "path": path_segments
                    },
                    "description": description,
                },
                "response": []
            }

            # Auth override for public endpoints
            if path in ("/health", "/api/v1/auth/register", "/api/v1/auth/login", "/api/v1/telegram/webhook"):
                request_item["request"]["auth"] = {"type": "noauth"}

            # Sample request bodies
            if "requestBody" in op:
                request_item["request"]["header"].append(
                    {"key": "Content-Type", "value": "application/json", "type": "text"}
                )
                sample_body = {}
                if "register" in path:
                    sample_body = {"email": "engineer@example.com", "password": "Password123!", "full_name": "Senior Architect"}
                elif "login" in path:
                    sample_body = {"email": "engineer@example.com", "password": "Password123!"}
                elif path.endswith("/projects") and method == "post":
                    sample_body = {"name": "PromptIQ E-Commerce Engine", "description": "High-throughput checkout service"}
                elif "discovery/start" in path:
                    sample_body = {"goal": "Build an async order processing engine", "deliverable": "complete_package", "target": "google-antigravity", "depth": "guided"}
                elif "discovery/sessions" in path:
                    sample_body = {"answers": {"primary_database": "PostgreSQL", "auth_mechanism": "OAuth2 / JWT"}}
                elif "constitution/approve" in path:
                    sample_body = {"approve": True, "feedback": "Architecture and requirements approved"}
                elif "compile" in path:
                    sample_body = {"target_environment": "google-antigravity", "output_type": "complete_package"}
                elif "critic/autopsy" in path:
                    sample_body = {"prompt_text": "Write code to process orders etc using best practices", "target_environment": "google-antigravity"}
                elif "research" in path:
                    sample_body = {"query": "PostgreSQL connection pooling under high concurrency", "mode": "deep"}
                elif "eval/run" in path:
                    sample_body = {"suite_id": "{{suiteId}}", "package_id": "{{packageId}}", "model_id": "gemini-2.0-flash"}

                request_item["request"]["body"] = {
                    "mode": "raw",
                    "raw": json.dumps(sample_body, indent=2),
                    "options": {"raw": {"language": "json"}}
                }

            if tag not in folders:
                folders[tag] = []
            folders[tag].append(request_item)

    for tag, items in folders.items():
        collection["item"].append({
            "name": tag,
            "item": items,
            "description": f"Endpoints belonging to the {tag} domain"
        })

    # Save collection
    coll_file = Path("docs/promptiq.postman_collection.json")
    with open(coll_file, "w", encoding="utf-8") as f:
        json.dump(collection, f, indent=2)
    print(f"Generated Postman Collection at: {coll_file}")

    # Generate environment file
    env_content = {
        "id": "promptiq-local-env",
        "name": "PromptIQ Local Environment",
        "values": [
            {"key": "baseUrl", "value": "http://localhost:8000", "type": "default", "enabled": True},
            {"key": "bearerToken", "value": "", "type": "secret", "enabled": True},
            {"key": "projectId", "value": "", "type": "default", "enabled": True},
            {"key": "sessionId", "value": "", "type": "default", "enabled": True},
            {"key": "packageId", "value": "", "type": "default", "enabled": True},
        ],
        "_postman_variable_scope": "environment",
    }
    env_file = Path("docs/promptiq.postman_environment.json")
    with open(env_file, "w", encoding="utf-8") as f:
        json.dump(env_content, f, indent=2)
    print(f"Generated Postman Environment at: {env_file}")


if __name__ == "__main__":
    generate_postman_assets()
