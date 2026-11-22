import React, { useState } from 'react';
import { Terminal, Download, Copy, Check, ExternalLink, Cpu, Sparkles, CheckCircle2 } from 'lucide-react';
import Badge from '../components/ui/Badge';

interface Integration {
  id: string;
  name: string;
  category: string;
  description: string;
  iconBg: string;
  installCommand: string;
  configPath: string;
  zipUrl: string;
  zipSize: string;
  checksum: string;
  capabilities: string[];
}

const INTEGRATIONS: Integration[] = [
  {
    id: 'antigravity',
    name: 'Google Antigravity',
    category: 'Native Plugin',
    description: 'Autonomous multi-agent orchestration with direct access to PromptIQ Project Constitution, task compiler, and autopsy reviewer.',
    iconBg: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
    installCommand: 'agy plugin install promptiq',
    configPath: 'skills/promptiq/SKILL.md',
    zipUrl: '/dist/plugins/promptiq-antigravity.zip',
    zipSize: '14.2 KB',
    checksum: 'a891f7c23de8...f91a',
    capabilities: ['Project Memory Sync', 'Adversarial Autopsy', 'Task Specialization', 'Evidence Offsets'],
  },
  {
    id: 'claude-code',
    name: 'Claude Code',
    category: 'Native CLI Plugin',
    description: 'Subagent orchestration for Anthropic Claude Code terminal sessions with tool calling and strict schema verification.',
    iconBg: 'bg-[#C85A32]/10 text-[#C85A32]',
    installCommand: 'claude plugin install promptiq-claude-code',
    configPath: '.claude-plugin/plugin.json',
    zipUrl: '/dist/plugins/promptiq-claude-code.zip',
    zipSize: '12.8 KB',
    checksum: '3b7c01e92d4f...99ea',
    capabilities: ['Prompt Suites', 'Tool Definitions', 'Negative Constraints', 'Deterministic Scoring'],
  },
  {
    id: 'cursor',
    name: 'Cursor IDE',
    category: 'IDE Rules & MCP',
    description: 'Persistent workspace instruction rules (.cursorrules) and MCP server integration for Cursor AI editor.',
    iconBg: 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
    installCommand: 'curl -sSL https://promptiq.internal/install-cursor.sh | bash',
    configPath: '.cursorrules',
    zipUrl: '/dist/plugins/promptiq-cursor.zip',
    zipSize: '15.6 KB',
    checksum: 'c209f874ab01...8831',
    capabilities: ['Cursor Rules File', 'Workspace Context', 'Supersession Chain', 'Code Autopsy'],
  },
  {
    id: 'openai-codex',
    name: 'OpenAI Codex',
    category: 'CLI & Environment Spec',
    description: 'Structured instruction packages and agent runtime configurations for OpenAI Codex and GPT developer tooling.',
    iconBg: 'bg-stone-500/10 text-stone-700 dark:text-stone-300',
    installCommand: 'npm install -g @promptiq/codex-plugin',
    configPath: 'codex.json',
    zipUrl: '/dist/plugins/promptiq-codex.zip',
    zipSize: '11.4 KB',
    checksum: '77ea1023bc89...41d2',
    capabilities: ['Instruction Manifest', 'Task Archetypes', 'Zero BYOK Enforcement', 'Model Gateway'],
  },
  {
    id: 'gemini-cli',
    name: 'Gemini CLI',
    category: 'Extension Package',
    description: 'First-class extension for Google Gemini CLI with live constitution query and prompt compilation commands.',
    iconBg: 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400',
    installCommand: 'gemini extension add promptiq',
    configPath: 'GEMINI.md',
    zipUrl: '/dist/plugins/promptiq-gemini-cli.zip',
    zipSize: '13.1 KB',
    checksum: '68fae9021cd5...3307',
    capabilities: ['GEMINI.md Directive', 'Context Injection', 'Research Evidence', 'Multi-Pass Judge'],
  },
  {
    id: 'generic-mcp',
    name: 'Universal MCP Server',
    category: 'Model Context Protocol',
    description: 'RFC-compliant Model Context Protocol server exposing all 7 PromptIQ intelligence tools over STDIO or SSE.',
    iconBg: 'bg-purple-500/10 text-purple-600 dark:text-purple-400',
    installCommand: 'npx -y @promptiq/mcp-server',
    configPath: 'mcp.json',
    zipUrl: '/dist/plugins/promptiq-mcp.zip',
    zipSize: '18.9 KB',
    checksum: 'f0183ec90a12...771b',
    capabilities: ['7 Standard MCP Tools', 'Resource Providers', 'Stdio & SSE Transport', 'Zero-Auth Safe'],
  },
];

export default function AgentIntegrations() {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-serif text-3xl font-semibold tracking-tight text-stone-900 dark:text-stone-100">
              Universal Agent Plugins & MCP
            </h1>
            <Badge variant="terracotta">Multi-Surface</Badge>
          </div>
          <p className="mt-1 text-sm text-stone-600 dark:text-stone-400">
            Native, installable integration packages and MCP tool bridges for the leading developer AI agents.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="success">All 6 Targets Ready</Badge>
        </div>
      </div>

      {/* Integration Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {INTEGRATIONS.map((item) => (
          <div
            key={item.id}
            className="flex flex-col justify-between p-5 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900 shadow-xs hover:border-stone-300 dark:hover:border-stone-700 transition-all"
          >
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div className={`p-2.5 rounded-xl ${item.iconBg}`}>
                  <Cpu className="w-5 h-5" />
                </div>
                <Badge variant="neutral">{item.category}</Badge>
              </div>

              <div>
                <h3 className="text-base font-semibold text-stone-900 dark:text-stone-100">
                  {item.name}
                </h3>
                <p className="mt-1 text-xs text-stone-600 dark:text-stone-400 leading-relaxed min-h-[48px]">
                  {item.description}
                </p>
              </div>

              {/* Install Command */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-[11px] text-stone-500 font-medium">
                  <span>Quick Install</span>
                  <button
                    onClick={() => handleCopy(item.installCommand, item.id)}
                    className="inline-flex items-center gap-1 text-[#C85A32] hover:underline"
                  >
                    {copiedId === item.id ? (
                      <>
                        <Check className="w-3 h-3 text-emerald-600" />
                        <span className="text-emerald-600">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3" />
                        <span>Copy</span>
                      </>
                    )}
                  </button>
                </div>
                <div className="p-2 rounded-lg bg-stone-900 text-stone-200 font-mono text-xs overflow-x-auto border border-stone-800">
                  {item.installCommand}
                </div>
              </div>

              {/* Capabilities checklist */}
              <div className="space-y-1.5 pt-2 border-t border-stone-100 dark:border-stone-800/60">
                <div className="text-[11px] font-medium text-stone-500 uppercase tracking-wider">
                  Features Included
                </div>
                <div className="grid grid-cols-2 gap-1 text-[11px] text-stone-700 dark:text-stone-300">
                  {item.capabilities.map((cap) => (
                    <div key={cap} className="flex items-center gap-1.5">
                      <CheckCircle2 className="w-3 h-3 text-emerald-600 shrink-0" />
                      <span className="truncate">{cap}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Bottom Actions */}
            <div className="mt-5 pt-4 border-t border-stone-100 dark:border-stone-800 flex items-center justify-between">
              <span className="text-[11px] font-mono text-stone-400">
                ZIP • {item.zipSize}
              </span>
              <a
                href={item.zipUrl}
                download
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-stone-100 dark:bg-stone-800 hover:bg-[#C85A32] hover:text-white dark:hover:bg-[#C85A32] text-stone-800 dark:text-stone-200 text-xs font-medium transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download ZIP</span>
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
