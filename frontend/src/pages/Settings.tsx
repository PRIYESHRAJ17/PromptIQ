import React, { useState } from 'react';
import { Shield, Key, Database, Server, RefreshCw, CheckCircle2, Lock, AlertCircle, Copy, Check } from 'lucide-react';
import Badge from '../components/ui/Badge';

export default function Settings() {
  const [copiedToken, setCopiedToken] = useState(false);
  const [apiKey, setApiKey] = useState('piq_live_992a7e1f48b105c3d2e');

  const handleCopyToken = () => {
    navigator.clipboard.writeText(apiKey);
    setCopiedToken(true);
    setTimeout(() => setCopiedToken(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <h1 className="font-serif text-3xl font-semibold tracking-tight text-stone-900 dark:text-stone-100">
            Workspace Settings & System Governance
          </h1>
          <Badge variant="terracotta">Production</Badge>
        </div>
        <p className="mt-1 text-sm text-stone-600 dark:text-stone-400">
          Governance controls, zero-price guarantees, API credentials, and runtime security policies.
        </p>
      </div>

      {/* Core Invariants Card */}
      <div className="p-5 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-emerald-600" />
            <h2 className="text-base font-semibold text-stone-900 dark:text-stone-100">
              PromptIQ Core Architectural Invariants
            </h2>
          </div>
          <Badge variant="success">All Invariants Enforced</Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="p-3 rounded-lg bg-stone-50 dark:bg-stone-800/40 border border-stone-200 dark:border-stone-700/60 space-y-1">
            <div className="flex items-center gap-1.5 font-semibold text-stone-900 dark:text-stone-100">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Zero-Price & Anti-BYOK</span>
            </div>
            <p className="text-stone-600 dark:text-stone-400">
              PromptIQ is 100% free to users. User API keys and paid inference fallbacks are cryptographically rejected.
            </p>
          </div>

          <div className="p-3 rounded-lg bg-stone-50 dark:bg-stone-800/40 border border-stone-200 dark:border-stone-700/60 space-y-1">
            <div className="flex items-center gap-1.5 font-semibold text-stone-900 dark:text-stone-100">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>No Local Inference</span>
            </div>
            <p className="text-stone-600 dark:text-stone-400">
              Centrally hosted model architecture. Zero Ollama, llama.cpp, or local GPU dependencies required.
            </p>
          </div>

          <div className="p-3 rounded-lg bg-stone-50 dark:bg-stone-800/40 border border-stone-200 dark:border-stone-700/60 space-y-1">
            <div className="flex items-center gap-1.5 font-semibold text-stone-900 dark:text-stone-100">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Canonical Truth</span>
            </div>
            <p className="text-stone-600 dark:text-stone-400">
              Project Constitution is the immutable single source of truth with strict provenance and supersession logs.
            </p>
          </div>

          <div className="p-3 rounded-lg bg-stone-50 dark:bg-stone-800/40 border border-stone-200 dark:border-stone-700/60 space-y-1">
            <div className="flex items-center gap-1.5 font-semibold text-stone-900 dark:text-stone-100">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Unified Cross-Surface Memory</span>
            </div>
            <p className="text-stone-600 dark:text-stone-400">
              Web application, plugins, CLI, and MCP share the exact same database records, jobs, and token quota.
            </p>
          </div>
        </div>
      </div>

      {/* Backend Connection & API Access */}
      <div className="p-5 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Server className="w-5 h-5 text-[#C85A32]" />
            <h2 className="text-base font-semibold text-stone-900 dark:text-stone-100">
              Backend API & Token Management
            </h2>
          </div>
          <Badge variant="sage">Connected</Badge>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-stone-700 dark:text-stone-300 mb-1">
              Backend Endpoint URL
            </label>
            <input
              type="text"
              readOnly
              value={import.meta.env.VITE_PROMPTIQ_API_URL || 'http://localhost:8000/api/v1'}
              className="w-full px-3 py-2 text-xs font-mono rounded-lg border border-stone-200 dark:border-stone-800 bg-stone-50 dark:bg-stone-950 text-stone-700 dark:text-stone-300"
            />
          </div>

          <div>
            <div className="flex items-center justify-between text-xs font-medium text-stone-700 dark:text-stone-300 mb-1">
              <span>Client Bearer Access Token</span>
              <button
                onClick={handleCopyToken}
                className="inline-flex items-center gap-1 text-[#C85A32] hover:underline"
              >
                {copiedToken ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                    <span className="text-emerald-600">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy Token</span>
                  </>
                )}
              </button>
            </div>
            <div className="relative">
              <input
                type="password"
                readOnly
                value={apiKey}
                className="w-full px-3 py-2 text-xs font-mono rounded-lg border border-stone-200 dark:border-stone-800 bg-stone-50 dark:bg-stone-950 text-stone-700 dark:text-stone-300"
              />
            </div>
            <p className="mt-1 text-[11px] text-stone-500">
              Used by Cursor, Claude Code, Antigravity, and Gemini CLI to authenticate with your PromptIQ workspace.
            </p>
          </div>
        </div>
      </div>

      {/* Quota Governance */}
      <div className="p-5 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-stone-600 dark:text-stone-400" />
            <h2 className="text-base font-semibold text-stone-900 dark:text-stone-100">
              Community Tier Usage & Zero-Cost Allocation
            </h2>
          </div>
          <span className="text-xs font-mono text-stone-500">Tier: Unlimited Free (100% Sponsored)</span>
        </div>

        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-xs font-medium mb-1">
              <span className="text-stone-700 dark:text-stone-300">Daily Inference Operations</span>
              <span className="font-mono text-stone-500">342 / 10,000 reqs</span>
            </div>
            <div className="h-2 w-full bg-stone-100 dark:bg-stone-800 rounded-full overflow-hidden">
              <div className="h-full bg-[#C85A32] rounded-full" style={{ width: '3.4%' }} />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs font-medium mb-1">
              <span className="text-stone-700 dark:text-stone-300">Active Workflow Concurrency</span>
              <span className="font-mono text-stone-500">1 / 5 slots</span>
            </div>
            <div className="h-2 w-full bg-stone-100 dark:bg-stone-800 rounded-full overflow-hidden">
              <div className="h-full bg-emerald-600 rounded-full" style={{ width: '20%' }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
