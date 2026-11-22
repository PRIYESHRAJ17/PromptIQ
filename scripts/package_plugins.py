"""
PromptIQ Plugin Packager and Validator
Packages all 6 agent integrations into distributable ZIPs and validates their integrity.
"""

import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INTEGRATIONS_DIR = ROOT / "integrations" / "plugins"
DIST_PLUGINS_DIR = ROOT / "dist" / "plugins"
FRONTEND_PUBLIC_DIR = ROOT / "frontend" / "public" / "dist" / "plugins"
FRONTEND_DIST_DIR = ROOT / "frontend" / "dist" / "dist" / "plugins"

PLUGINS = [
    {
        "id": "promptiq-antigravity",
        "name": "Google Antigravity",
        "zip_name": "promptiq-antigravity.zip",
        "required_files": [
            "manifest.json",
            "skills/promptiq/SKILL.md",
            "rules/promptiq.md",
            "mcp.json",
            "README.md",
        ],
    },
    {
        "id": "promptiq-claude-code",
        "name": "Claude Code",
        "zip_name": "promptiq-claude-code.zip",
        "required_files": [
            ".claude-plugin/plugin.json",
            "skills/promptiq/SKILL.md",
            "mcp.json",
            "README.md",
        ],
    },
    {
        "id": "promptiq-cursor",
        "name": "Cursor IDE",
        "zip_name": "promptiq-cursor.zip",
        "required_files": [
            "plugin.json",
            ".cursorrules",
            "mcp.json",
            "skills/promptiq/SKILL.md",
            "README.md",
        ],
    },
    {
        "id": "promptiq-codex",
        "name": "OpenAI Codex",
        "zip_name": "promptiq-codex.zip",
        "required_files": [
            "plugin.json",
            "codex.json",
            "skills/promptiq/SKILL.md",
            "mcp.json",
            "README.md",
        ],
    },
    {
        "id": "promptiq-gemini-cli",
        "name": "Gemini CLI",
        "zip_name": "promptiq-gemini-cli.zip",
        "required_files": [
            "gemini-extension.json",
            "GEMINI.md",
            "mcp.json",
            "skills/promptiq/SKILL.md",
            "README.md",
        ],
    },
    {
        "id": "promptiq-mcp",
        "name": "Universal MCP",
        "zip_name": "promptiq-mcp.zip",
        "required_files": [
            "mcp.json",
            "tools.json",
            "README.md",
        ],
    },
]


def create_zip(source_dir: Path, output_zip: Path):
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = Path(root) / file
                archive_name = file_path.relative_to(source_dir).as_posix()
                zf.write(file_path, arcname=archive_name)


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def main():
    print("=== PromptIQ Plugin Packaging & Verification ===")
    DIST_PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    FRONTEND_PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    FRONTEND_DIST_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    for p in PLUGINS:
        plugin_dir = INTEGRATIONS_DIR / p["id"]
        if not plugin_dir.exists():
            raise FileNotFoundError(f"Missing plugin directory: {plugin_dir}")

        zip_path = DIST_PLUGINS_DIR / p["zip_name"]
        create_zip(plugin_dir, zip_path)

        # Copy to frontend public and dist for direct browser downloads
        shutil.copy2(zip_path, FRONTEND_PUBLIC_DIR / p["zip_name"])
        shutil.copy2(zip_path, FRONTEND_DIST_DIR / p["zip_name"])

        sha256 = compute_sha256(zip_path)
        size_bytes = zip_path.stat().st_size

        # Validate extraction in temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmp_path)

            missing_files = []
            for req in p["required_files"]:
                target_file = tmp_path / req
                if not target_file.exists():
                    missing_files.append(req)

            if missing_files:
                raise ValueError(f"Plugin {p['id']} missing files in ZIP: {missing_files}")

        print(f"✓ {p['name']} ({p['zip_name']}): {size_bytes} bytes, SHA256: {sha256[:16]}... Validated OK")
        results.append({
            "id": p["id"],
            "name": p["name"],
            "zip_file": p["zip_name"],
            "size_bytes": size_bytes,
            "sha256": sha256,
            "required_files_count": len(p["required_files"]),
            "status": "VALIDATED"
        })

    summary_file = DIST_PLUGINS_DIR / "packages_manifest.json"
    with open(summary_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSuccessfully created and verified all {len(results)} plugin packages in {DIST_PLUGINS_DIR}")


if __name__ == "__main__":
    main()
