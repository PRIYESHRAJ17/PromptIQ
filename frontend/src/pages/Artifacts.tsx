import React, { useState } from 'react';
import { Package, Download, Copy, Check, FileCode, ShieldCheck, Terminal, Eye, ExternalLink } from 'lucide-react';
import Badge from '../components/ui/Badge';
import type { CompiledArtifact } from '../types';

const MOCK_ARTIFACTS: CompiledArtifact[] = [
  {
    id: 'art-001',
    target_format: 'antigravity',
    file_path: 'integrations/plugins/promptiq-antigravity/skills/promptiq/SKILL.md',
    content_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    size_bytes: 4280,
    created_at: '2026-11-22T10:14:00Z',
    download_url: '/api/v1/artifacts/art-001/download',
  },
  {
    id: 'art-002',
    target_format: 'claude_code',
    file_path: 'integrations/plugins/promptiq-claude-code/skills/promptiq/SKILL.md',
    content_hash: '9f83c605ddb57a3e009932ddf428024e3bb3bf28b46cbcf82ff61b4a78bec8a2',
    size_bytes: 3890,
    created_at: '2026-11-22T10:15:00Z',
    download_url: '/api/v1/artifacts/art-002/download',
  },
  {
    id: 'art-003',
    target_format: 'cursor',
    file_path: 'integrations/plugins/promptiq-cursor/.cursorrules',
    content_hash: '7d793037a0760186574b0282f2f435e70d7168d4ed574f71689d742fbee7b38f',
    size_bytes: 5120,
    created_at: '2026-11-22T10:16:00Z',
    download_url: '/api/v1/artifacts/art-003/download',
  },
  {
    id: 'art-004',
    target_format: 'openai_codex',
    file_path: 'integrations/plugins/promptiq-codex/codex.json',
    content_hash: '6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b',
    size_bytes: 3410,
    created_at: '2026-11-22T10:17:00Z',
    download_url: '/api/v1/artifacts/art-004/download',
  },
  {
    id: 'art-005',
    target_format: 'gemini_cli',
    file_path: 'integrations/plugins/promptiq-gemini-cli/GEMINI.md',
    content_hash: 'd4735e3a265e16eee03f59718b9b5d03019c07d8b6c51f90da3a666eec13ab35',
    size_bytes: 4620,
    created_at: '2026-11-22T10:18:00Z',
    download_url: '/api/v1/artifacts/art-005/download',
  },
  {
    id: 'art-006',
    target_format: 'generic_mcp',
    file_path: 'integrations/plugins/promptiq-mcp/tools.json',
    content_hash: '4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce',
    size_bytes: 6180,
    created_at: '2026-11-22T10:19:00Z',
    download_url: '/api/v1/artifacts/art-006/download',
  },
];

const MOCK_CONTENT: Record<string, string> = {
  'art-001': `---
name: promptiq
description: PromptIQ Intelligent Orchestrator for Google Antigravity
version: 1.0.0
---

# PROMPTIQ ORCHESTRATION SKILL

PromptIQ connects Antigravity directly to canonical project memory, task-family prompt compilers, and adversarial autopsy review.

## Invariant Rules
- Canonical truth in Project Constitution
- Zero local LLM dependencies
- Strictly verified zero-price inference gateway
`,
  'art-003': `# Cursor Rules for PromptIQ Managed Architecture

1. Adhere to project invariants defined in .promptiq/constitution.json
2. Never introduce user API key inputs or paid fallback routes
3. Maintain immutable evidence references with character offsets
`,
};

export default function Artifacts() {
  const [artifacts] = useState<CompiledArtifact[]>(MOCK_ARTIFACTS);
  const [selectedArtifact, setSelectedArtifact] = useState<CompiledArtifact>(MOCK_ARTIFACTS[0]);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopyHash = (hash: string, id: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleDownloadFile = (art: CompiledArtifact) => {
    const content = MOCK_CONTENT[art.id] || `// Compiled Target Package for ${art.target_format.toUpperCase()}\n// Checksum: ${art.content_hash}`;
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
                  onClick={() => handleCopyHash(MOCK_CONTENT[selectedArtifact.id] || '// Artifact compiled binary content', 'preview')}
                  className="inline-flex items-center gap-1 text-[#C85A32] hover:underline"
                >
                  <Copy className="w-3 h-3" />
                  <span>Copy Code</span>
                </button>
              </div>
              <pre className="p-4 rounded-lg bg-stone-900 text-stone-200 text-xs font-mono overflow-x-auto max-h-80 leading-relaxed border border-stone-800">
                {MOCK_CONTENT[selectedArtifact.id] || `// Compiled Target Package for ${selectedArtifact.target_format.toUpperCase()}\n// Generated by PromptIQ Native Compiler\n// Checksum: ${selectedArtifact.content_hash}\n\n{\n  "target": "${selectedArtifact.target_format}",\n  "status": "ready",\n  "verified": true\n}`}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
