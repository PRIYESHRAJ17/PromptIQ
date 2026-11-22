import React from 'react'
import {
  Sparkles,
  ArrowRight,
  PlayCircle,
  Stethoscope,
  FolderGit2,
  Puzzle,
  FlaskConical,
  CheckCircle2,
  Clock,
  ChevronRight,
  ShieldCheck,
  Zap,
} from 'lucide-react'
import Badge from '@/components/ui/Badge'
import StatCard from '@/components/ui/StatCard'

interface OverviewProps {
  onNavigate: (route: string) => void
}

const RECENT_WORKFLOWS = [
  {
    id: 'wf-9821',
    title: 'Distributed Stream Ingestion Engine',
    taskFamily: 'software_engineering',
    target: 'Google Antigravity',
    status: 'COMPLETED',
    stage: 'Verification & Packaging',
    duration: '42s',
    updated: '5 mins ago',
  },
  {
    id: 'wf-9820',
    title: 'Adversarial Prompt Security Audit',
    taskFamily: 'prompt_improvement',
    target: 'Claude Code',
    status: 'COMPLETED',
    stage: 'Forensic Autopsy',
    duration: '18s',
    updated: '24 mins ago',
  },
  {
    id: 'wf-9819',
    title: 'PostgreSQL 16 Replication Validator',
    taskFamily: 'data_analysis',
    target: 'Cursor IDE',
    status: 'RUNNING',
    stage: 'Subtask Execution (3/5)',
    duration: '1m 12s',
    updated: 'Just now',
  },
  {
    id: 'wf-9818',
    title: 'MCP Server RFC Specification Suite',
    taskFamily: 'ai_agent_development',
    target: 'Universal MCP',
    status: 'COMPLETED',
    stage: 'Package Verified',
    duration: '35s',
    updated: '1 hour ago',
  },
  {
    id: 'wf-9817',
    title: 'Autonomous Multi-Agent Task Orchestrator',
    taskFamily: 'software_engineering',
    target: 'Google Gemini CLI',
    status: 'COMPLETED',
    stage: 'Evaluation Matrix',
    duration: '54s',
    updated: '2 hours ago',
  },
]

const QUICK_ACTIONS = [
  {
    id: 'new-workflow',
    title: 'Launch Autonomous Workflow',
    description: 'Decompose complex goals into 11-stage verified DAG subtasks',
    icon: PlayCircle,
    color: 'text-[#C85A32]',
    bg: 'bg-[#C85A32]/10',
    route: 'new-workflow',
  },
  {
    id: 'autopsy',
    title: 'Run Prompt Autopsy',
    description: 'Forensic scanner against 21 adversarial failure modes',
    icon: Stethoscope,
    color: 'text-rose-600',
    bg: 'bg-rose-500/10',
    route: 'autopsy',
  },
  {
    id: 'integrations',
    title: 'Install Agent Plugins & MCP',
    description: '6 installable packages: Antigravity, Claude, Cursor, Codex, Gemini',
    icon: Puzzle,
    color: 'text-indigo-600',
    bg: 'bg-indigo-500/10',
    route: 'integrations',
  },
  {
    id: 'projects',
    title: 'Project Memory & Constitution',
    description: 'Single source of truth with immutable supersession tracking',
    icon: FolderGit2,
    color: 'text-emerald-600',
    bg: 'bg-emerald-500/10',
    route: 'projects',
  },
  {
    id: 'test-lab',
    title: 'Evaluation & Test Lab',
    description: 'Deterministic schema assertions and multi-pass consistency scoring',
    icon: FlaskConical,
    color: 'text-amber-600',
    bg: 'bg-amber-500/10',
    route: 'test-lab',
  },
  {
    id: 'artifacts',
    title: 'Compiled Artifacts & Packages',
    description: 'Direct browser downloads with SHA-256 cryptographic verification',
    icon: Zap,
    color: 'text-purple-600',
    bg: 'bg-purple-500/10',
    route: 'artifacts',
  },
]

export function Overview({ onNavigate }: OverviewProps) {
  return (
    <div className="space-y-6 max-w-6xl">
      {/* Welcome Hero Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-[#F7F4EE] dark:bg-[#1A1D24] border border-[#E8E2D8] dark:border-[#2C313E] p-6 sm:p-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="max-w-xl space-y-2">
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-[#C85A32]/10 text-[#C85A32]">
              <Sparkles className="w-3.5 h-3.5" />
              <span>PromptIQ V7 Operational • 100% Free Forever</span>
            </div>
            <h2 className="font-serif-title text-3xl font-bold tracking-tight text-[#1E2229] dark:text-[#F2EFE9] sm:text-4xl">
              From intent to verified AI execution.
            </h2>
            <p className="text-sm text-[#6A6E78] dark:text-[#9EA3B0] leading-relaxed">
              Autonomous prompt intelligence, task-family compilation, and persistent Project Constitution memory. No user API keys required.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 shrink-0">
            <button
              onClick={() => onNavigate('new-workflow')}
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-[#C85A32] hover:bg-[#B54E29] text-white text-xs font-bold shadow-sm transition-all"
            >
              <PlayCircle className="w-4 h-4" />
              <span>Create Workflow</span>
            </button>
            <button
              onClick={() => onNavigate('autopsy')}
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl border border-[#E8E2D8] dark:border-[#2C313E] bg-white dark:bg-[#20242E] hover:bg-[#FAF7F0] text-[#1E2229] dark:text-[#F2EFE9] text-xs font-semibold shadow-xs transition-all"
            >
              <Stethoscope className="w-4 h-4 text-[#C85A32]" />
              <span>Run Autopsy</span>
            </button>
          </div>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Verified Workflows"
          value="148"
          change="+18.4%"
          trend="up"
          description="Across 10 task families"
        />
        <StatCard
          title="Autopsy Pass Rate"
          value="98.4%"
          change="+3.2%"
          trend="up"
          description="21 categories scanned"
        />
        <StatCard
          title="Active Invariants"
          value="100%"
          change="0 bypass"
          trend="up"
          description="Zero BYOK & No Local LLM"
        />
        <StatCard
          title="Supported Targets"
          value="6 Agents"
          change="All Ready"
          trend="neutral"
          description="Antigravity, Claude, Cursor..."
        />
      </div>

      {/* Quick Action Launchpad (Replaced heavy non-interactive graphs) */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold uppercase tracking-wider text-[#6A6E78]">
            Quick Action Launchpad
          </h3>
          <span className="text-xs text-[#6A6E78]">Click any tool to launch directly</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {QUICK_ACTIONS.map((action) => {
            const Icon = action.icon
            return (
              <div
                key={action.id}
                onClick={() => onNavigate(action.route)}
                className="group flex items-start gap-4 p-4 rounded-xl border border-[#E8E2D8] dark:border-[#2C313E] bg-white dark:bg-[#1A1D24] hover:border-[#C85A32] dark:hover:border-[#C85A32] shadow-xs cursor-pointer transition-all hover:translate-y-[-1px]"
              >
                <div className={`p-2.5 rounded-xl ${action.bg} ${action.color} shrink-0 group-hover:scale-105 transition-transform`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-[#1E2229] dark:text-[#F2EFE9] group-hover:text-[#C85A32] transition-colors truncate">
                      {action.title}
                    </h4>
                    <ChevronRight className="w-3.5 h-3.5 text-[#9EA3B0] group-hover:translate-x-1 group-hover:text-[#C85A32] transition-all" />
                  </div>
                  <p className="mt-1 text-[11px] text-[#6A6E78] dark:text-[#9EA3B0] line-clamp-2 leading-relaxed">
                    {action.description}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Recent Workflow Executions Table (All rows clickable to workbench) */}
      <div className="rounded-xl border border-[#E8E2D8] dark:border-[#2C313E] bg-white dark:bg-[#1A1D24] shadow-xs overflow-hidden">
        <div className="p-4 sm:p-5 border-b border-[#E8E2D8] dark:border-[#2C313E] flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-[#1E2229] dark:text-[#F2EFE9]">
              Recent Workflow Executions
            </h3>
            <p className="text-xs text-[#6A6E78] dark:text-[#9EA3B0] mt-0.5">
              Click any execution to open the Workflow Workbench
            </p>
          </div>
          <button
            onClick={() => onNavigate('workbench')}
            className="inline-flex items-center gap-1 text-xs font-semibold text-[#C85A32] hover:underline"
          >
            <span>Open Workbench</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#E8E2D8] dark:border-[#2C313E] bg-[#FAF7F0] dark:bg-[#1E222A] text-[#6A6E78] uppercase tracking-wider text-[10px]">
                <th className="py-3 px-5 font-semibold">Workflow ID</th>
                <th className="py-3 px-5 font-semibold">Goal & Objective</th>
                <th className="py-3 px-5 font-semibold">Target Environment</th>
                <th className="py-3 px-5 font-semibold">Current Stage</th>
                <th className="py-3 px-5 font-semibold">Status</th>
                <th className="py-3 px-5 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E8E2D8] dark:divide-[#2C313E]">
              {RECENT_WORKFLOWS.map((wf) => (
                <tr
                  key={wf.id}
                  onClick={() => onNavigate('workbench')}
                  className="hover:bg-[#FAF7F0] dark:hover:bg-[#20242E] cursor-pointer transition-colors"
                >
                  <td className="py-3.5 px-5 font-mono text-[#6A6E78] font-medium">
                    {wf.id}
                  </td>
                  <td className="py-3.5 px-5 font-semibold text-[#1E2229] dark:text-[#F2EFE9]">
                    {wf.title}
                  </td>
                  <td className="py-3.5 px-5">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-stone-100 dark:bg-stone-800 text-stone-700 dark:text-stone-300">
                      {wf.target}
                    </span>
                  </td>
                  <td className="py-3.5 px-5 text-[#6A6E78] dark:text-[#9EA3B0]">
                    {wf.stage}
                  </td>
                  <td className="py-3.5 px-5">
                    <Badge variant={wf.status === 'COMPLETED' ? 'success' : 'terracotta'}>
                      {wf.status}
                    </Badge>
                  </td>
                  <td className="py-3.5 px-5 text-right">
                    <span className="text-[#C85A32] font-semibold text-[11px] group-hover:underline">
                      Inspect &rarr;
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default Overview
