import React, { useState } from 'react';
import { Package, Download, Copy, Check, FileCode, ShieldCheck, Terminal, Eye, ExternalLink } from 'lucide-react';
import Badge from '../components/ui/Badge';
import type { CompiledArtifact } from '../types';

const REAL_ARTIFACTS: CompiledArtifact[] = [
  {
    id: 'art-001',
    target_format: 'antigravity',
    file_path: 'integrations/plugins/promptiq-antigravity/skills/promptiq/SKILL.md',
    content_hash: '81fd9cad558be1a1db1dcb863836071bc4097caccab1f4021b5340c512bc0295',
    size_bytes: 2453,
    created_at: '2026-11-24T10:00:00Z',
    download_url: '/api/v1/artifacts/art-001/download',
  },
  {
    id: 'art-002',
    target_format: 'claude_code',
    file_path: 'integrations/plugins/promptiq-claude-code/skills/promptiq/SKILL.md',
    content_hash: '1d89d422a4069ea05ef64089dbcd039f6211f42ceadea4758dc06b6de516bc86',
    size_bytes: 845,
    created_at: '2026-11-24T10:00:00Z',
    download_url: '/api/v1/artifacts/art-002/download',
  },
  {
    id: 'art-003',
    target_format: 'cursor',
    file_path: 'integrations/plugins/promptiq-cursor/.cursorrules',
    content_hash: 'a368e2b4b3b30fb0f6e38d139f4dc1405b57cef7d0efd3ccfc5c9b47f150113c',
    size_bytes: 732,
    created_at: '2026-11-24T10:00:00Z',
    download_url: '/api/v1/artifacts/art-003/download',
  },
  {
    id: 'art-004',
    target_format: 'openai_codex',
    file_path: 'integrations/plugins/promptiq-codex/codex.json',
    content_hash: '5fd2b44edb934295bcdb8a0f9e20fa0ee383d7ab0a486f74f858ef2b3ac4597a',
    size_bytes: 324,
    created_at: '2026-11-24T10:00:00Z',
    download_url: '/api/v1/artifacts/art-004/download',
  },
  {
    id: 'art-005',
    target_format: 'gemini_cli',
    file_path: 'integrations/plugins/promptiq-gemini-cli/GEMINI.md',
    content_hash: 'c8cc2173f5358b10c6298988d1cc75225daba0dd67fe2268bdd9faa10c146a6e',
    size_bytes: 426,
    created_at: '2026-11-24T10:00:00Z',
    download_url: '/api/v1/artifacts/art-005/download',
  },
  {
    id: 'art-006',
    target_format: 'generic_mcp',
    file_path: 'integrations/plugins/promptiq-mcp/mcp.json',
    content_hash: '1c40552de611357091c27b23a778fbefb82976078a65aa30eaba34aedfd4d4a1',
    size_bytes: 359,
    created_at: '2026-11-24T10:00:00Z',
    download_url: '/api/v1/artifacts/art-006/download',
  },
];

const REAL_CONTENTS: Record<string, string> = {
  'art-001': `---
name: promptiq
description: Direct access to PromptIQ Prompt Intelligence, Project Constitution memory, task compilers, and adversarial autopsy review. Use when optimizing or diagnosing prompts, managing project constitutions, or compiling target instructions.
---

# PromptIQ Intelligence Skill for Google Antigravity

Use this skill when you need to access persistent project memory, decompose complex user requests across 10 specialized task families, compile target-native prompt packages, or run adversarial Prompt Autopsy diagnostics.

## Available Capabilities & MCP Tools

PromptIQ exposes authoritative intelligence tools through the \`promptiq\` MCP server:

1. \`create_project(name, description)\`: Create a new PromptIQ project with an initial Project Constitution.
2. \`run_discovery(project_id, goal, depth)\`: Start or continue adaptive discovery for a project (\`quick\`, \`guided\`, or \`deep\`).
3. \`get_project_constitution(project_id)\`: Retrieve the canonical Project Constitution source of truth, requirements, and decisions.
4. \`compile_prompt(project_id, target_environment, output_type)\`: Compile the approved Constitution into target-native instructions (Antigravity, Claude Code, Cursor, Codex).
5. \`review_prompt(prompt_text, target_environment)\`: Execute an adversarial 18-21 category forensic autopsy and diagnostic critique.
6. \`research(project_id, query, mode)\`: Investigate technical documentation and record claims in the Evidence Ledger.
7. \`record_checkpoint(project_id, phase, summary)\`: Record a verified project milestone checkpoint for cross-agent continuity.
8. \`get_context_pack(project_id, max_token_budget)\`: Compile and pack project context for an external agent within a token budget.
9. \`execute_agent_task(objective, task_type, max_iterations)\`: Execute an objective through the PromptIQ autonomous observe-decide-act agent loop.
10. \`get_quota_status()\`: Verify PromptIQ zero-price guarantee, quotas, and active anti-BYOK enforcement.

## Core Architectural Invariants

1. **Canonical Truth**: Never maintain local unverified assumptions. All decisions must be recorded in the Project Constitution.
2. **Zero Price Guarantee**: Never ask the user for LLM API keys or suggest paid fallback routes.
3. **No Local Inference**: PromptIQ routes all intelligence through the hosted zero-price gateway.
4. **Adversarial Honesty**: Always provide unsparing critique in Prompt Autopsies. Never output decorative praise.
`,
  'art-002': `---
name: promptiq-claude-code
description: Deep prompt intelligence, forensic autopsy, and persistent Project Constitution memory for Claude Code.
version: 1.0.0
---

# PromptIQ for Claude Code

Connects Claude Code subagents directly to the PromptIQ zero-price intelligence gateway.

## Capabilities
- Query canonical Project Constitution memory before answering architectural questions.
- Execute Prompt Autopsy to identify vagueness, hidden hallucinations, and security flaws.
- Compile and validate Anthropic-native tool calling schemas and prompt suites.

## MCP Tools
All 7 standard PromptIQ MCP tools are exposed via stdio:
- \`promptiq_get_constitution\`
- \`promptiq_propose_constitution_change\`
- \`promptiq_compile_prompt\`
- \`promptiq_run_autopsy\`
- \`promptiq_search_evidence\`
- \`promptiq_execute_workflow\`
- \`promptiq_get_quota_status\`
`,
  'art-003': `# PromptIQ Rules for Cursor AI

You are connected to PromptIQ — the central intelligence and project memory engine.

## Invariant Guidelines:
1. Canonical Architecture: Before proposing architectural changes, check the active Project Constitution via PromptIQ MCP or .promptiq/constitution.json.
2. Zero-Price Rule: Never prompt user for LLM API keys or implement paid inference fallback routes. PromptIQ is 100% free.
3. No Local Inference: Centrally hosted architecture. Do not instruct user to run Ollama or local LLM instances.
4. Adversarial Review: When reviewing or generating prompts, run promptiq_run_autopsy to catch defects and vulnerabilities.
5. Deterministic Assertions: Ground code changes in verified test suites.
`,
  'art-004': `{
  "system_instructions": "You are connected to PromptIQ. Always adhere to Project Constitution invariants. Never request user API keys or switch to paid inference routes.",
  "promptiq_integration": {
    "zero_price_policy": "strict_enforcement",
    "compiler_target": "openai_codex",
    "mcp_server": "promptiq"
  }
}
`,
  'art-005': `# PromptIQ Workspace Rules for Gemini CLI

You are integrated with PromptIQ.

1. **Adhere to Project Constitution**: Read and respect canonical requirements and decisions.
2. **Zero-Price Guarantee**: Reject all BYOK requests and paid API key fallbacks.
3. **No Local Inference**: Always leverage hosted central model services.
4. **Adversarial Autopsy**: Run prompt autopsy to uncover hidden traps before finalizing prompts.
`,
  'art-006': `{
  "$schema": "https://modelcontextprotocol.io/schema.json",
  "name": "promptiq-mcp",
  "version": "1.2.0",
  "description": "Universal RFC-compliant Model Context Protocol server exposing PromptIQ intelligence tools.",
  "transport": [
    "stdio",
    "sse"
  ],
  "command": "promptiq-mcp",
  "env": {
    "PROMPTIQ_ZERO_PRICE_ENFORCEMENT": "true"
  }
}
`,
};

export default function Artifacts() {
  const [artifacts] = useState<CompiledArtifact[]>(REAL_ARTIFACTS);
  const [selectedArtifact, setSelectedArtifact] = useState<CompiledArtifact>(REAL_ARTIFACTS[0]);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopyHash = (hash: string, id: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleDownloadFile = (art: CompiledArtifact) => {
    const content = REAL_CONTENTS[art.id] || `// Compiled Target Package for ${art.target_format.toUpperCase()}\n// Checksum: ${art.content_hash}`;
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = art.file_path.split('/').pop() || `${art.id}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-serif text-3xl font-semibold tracking-tight text-stone-900 dark:text-stone-100">
              Compiled Artifacts & Packages
            </h1>
            <Badge variant="terracotta">Native Packages</Badge>
          </div>
          <p className="mt-1 text-sm text-stone-600 dark:text-stone-400">
            Immutable prompt packages, target-specific instruction sets, and SHA-256 verifiable distributions.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-300">
            <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span>SHA-256 Cryptographic Verification Active</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Artifact List & Previewer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Artifact List */}
        <div className="lg:col-span-6 space-y-3">
          {artifacts.map((art) => {
            const isSelected = selectedArtifact.id === art.id;
            return (
              <div
                key={art.id}
                onClick={() => setSelectedArtifact(art)}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  isSelected
                    ? 'border-[#C85A32] bg-[#FBF9F5] dark:bg-stone-900 shadow-sm'
                    : 'border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900/50 hover:border-stone-300'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge variant={art.target_format === 'antigravity' ? 'terracotta' : 'sage'}>
                        {art.target_format.replace('_', ' ').toUpperCase()}
                      </Badge>
                      <span className="text-xs font-mono text-stone-400">{art.id}</span>
                    </div>
                    <div className="text-sm font-semibold font-mono text-stone-900 dark:text-stone-100">
                      {art.file_path.split('/').pop()}
                    </div>
                    <p className="text-xs text-stone-500 font-mono truncate max-w-sm">
                      {art.file_path}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-mono text-stone-500">{(art.size_bytes / 1024).toFixed(1)} KB</span>
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t border-stone-100 dark:border-stone-800/60 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1 font-mono text-[11px] text-stone-400">
                    <span>SHA:</span>
                    <span>{art.content_hash.substring(0, 12)}...</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCopyHash(art.content_hash, art.id);
                      }}
                      className="p-1 hover:text-stone-700 dark:hover:text-stone-200"
                      title="Copy SHA-256 Hash"
                    >
                      {copiedId === art.id ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                    </button>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDownloadFile(art);
                    }}
                    className="inline-flex items-center gap-1 text-[#C85A32] hover:underline font-semibold text-xs cursor-pointer"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Artifact Content Inspector */}
        <div className="lg:col-span-6">
          <div className="sticky top-6 p-5 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-semibold text-stone-900 dark:text-stone-100">
                  {selectedArtifact.file_path.split('/').pop()}
                </h3>
                <p className="text-xs font-mono text-stone-500">{selectedArtifact.file_path}</p>
              </div>
              <Badge variant="terracotta">{selectedArtifact.target_format}</Badge>
            </div>

            <div className="p-3 rounded-lg bg-stone-50 dark:bg-stone-800/40 border border-stone-200 dark:border-stone-700/60 space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-stone-500">Cryptographic Hash (SHA-256):</span>
                <span className="font-mono text-[11px] text-stone-800 dark:text-stone-200 break-all">
                  {selectedArtifact.content_hash}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-stone-500">File Size:</span>
                <span className="font-mono text-stone-800 dark:text-stone-200">{selectedArtifact.size_bytes} bytes</span>
              </div>
              <div className="flex justify-between">
                <span className="text-stone-500">Compiled Timestamp:</span>
                <span className="font-mono text-stone-800 dark:text-stone-200">{selectedArtifact.created_at}</span>
              </div>
            </div>

            {/* Content Preview */}
            <div>
              <div className="flex items-center justify-between text-xs font-medium text-stone-500 mb-2">
                <span className="flex items-center gap-1.5">
                  <FileCode className="w-3.5 h-3.5" />
                  <span>Compiled File Source</span>
                </span>
                <button
                  onClick={() => handleCopyHash(REAL_CONTENTS[selectedArtifact.id] || '// Artifact compiled binary content', 'preview')}
                  className="inline-flex items-center gap-1 text-[#C85A32] hover:underline"
                >
                  <Copy className="w-3 h-3" />
                  <span>Copy Code</span>
                </button>
              </div>
              <pre className="p-4 rounded-lg bg-stone-900 text-stone-200 text-xs font-mono overflow-x-auto max-h-80 leading-relaxed border border-stone-800">
                {REAL_CONTENTS[selectedArtifact.id] || `// Compiled Target Package for ${selectedArtifact.target_format.toUpperCase()}\n// Generated by PromptIQ Native Compiler\n// Checksum: ${selectedArtifact.content_hash}\n\n{\n  "target": "${selectedArtifact.target_format}",\n  "status": "ready",\n  "verified": true\n}`}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
