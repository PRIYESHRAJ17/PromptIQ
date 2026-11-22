import React, { useState } from 'react'
import {
  PlayCircle,
  CheckCircle2,
  AlertTriangle,
  Clock,
  PauseCircle,
  FileCode,
  Terminal,
  Layers,
  ChevronRight,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react'
import { WORKFLOW_STAGES } from '@/lib/constants'
import { Badge } from '@/components/ui/Badge'

export function WorkflowWorkbench() {
  const [currentStageIndex, setCurrentStageIndex] = useState(8) // stage 9 (verify)
  const [selectedSubtask, setSelectedSubtask] = useState<string>('task-07-verify')

  const subtasks = [
    {
      id: 'task-01-intent',
      name: 'Intent & Boundary Analysis',
      status: 'completed',
      method: 'deterministic_code',
      duration: '0.04s',
      output: 'Parsed 3 objectives, 2 constraints (zero-price, backend-only).',
    },
    {
      id: 'task-02-research',
      name: 'Evidence & Literature Search',
      status: 'completed',
      method: 'data_transform',
      duration: '0.12s',
      output: 'Ingested 4 evidence passages with verified character offsets.',
    },
    {
      id: 'task-03-specification',
      name: 'Typed Prompt Specification',
      status: 'completed',
      method: 'deterministic_code',
      duration: '0.06s',
      output: 'Compiled PPS v2 with 8 requirements and strict schemas.',
    },
    {
      id: 'task-04-generate',
      name: 'Candidate Deliverable Synthesis',
      status: 'completed',
      method: 'model_inference',
      duration: '0.85s',
      output: 'Generated complete Python FastAPI middleware implementation.',
    },
    {
      id: 'task-05-critique',
      name: 'Prompt Autopsy Diagnosis',
      status: 'completed',
      method: 'validator_exec',
      duration: '0.09s',
      output: 'Flagged missing stop condition (severity: medium, non-blocking).',
    },
    {
      id: 'task-06-revise',
      name: 'Dynamic Replan & Remediation',
      status: 'completed',
      method: 'deterministic_code',
      duration: '0.05s',
      output: 'Plan version incremented to v2; injected retry fallback contract.',
    },
    {
      id: 'task-07-verify',
      name: 'Test Lab Deterministic Assertions',
      status: 'running',
      method: 'validator_exec',
      duration: '0.18s',
      output: 'Evaluating 4 schema conformance assertions and negative boundary checks.',
    },
    {
      id: 'task-08-persist',
      name: 'State & Memory Persistence',
      status: 'pending',
      method: 'filesystem_write',
      duration: '—',
      output: 'Awaiting upstream completion.',
    },
  ]

  const toolLogs = [
    {
      timestamp: '14:02:18.102',
      tool: 'data_transform',
      permission: 'read_only [ALLOWED]',
      details: 'Summarized 4 research data points across vector indexing benchmarks.',
      status: 'success',
    },
    {
      timestamp: '14:02:18.245',
      tool: 'validator_exec',
      permission: 'read_only [ALLOWED]',
      details: 'Executed 3 schema assertions against candidate output. Assertions passed: 3/3.',
      status: 'success',
    },
    {
      timestamp: '14:02:18.312',
      tool: 'filesystem_write',
      permission: 'read_only [DENIED]',
      details: 'Permission denied: Tool requires reversible_modification. Triggered dynamic replan (strategy: skip).',
      status: 'replan_triggered',
    },
    {
      timestamp: '14:02:18.318',
      tool: 'replan_engine',
      permission: 'system [ALLOWED]',
      details: 'Plan version updated from v1 -> v2. Subtask task-08-persist marked SKIPPED.',
      status: 'success',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Workbench Header */}
      <div className="bg-white dark:bg-[#1A1D23] border border-[#E8E2D8] dark:border-[#2C313E] rounded-xl p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold text-[#C85A32]">WF-8921</span>
            <h2 className="text-base font-bold text-[#1E2229] dark:text-[#F2EFE9]">
              Implement distributed idempotency key middleware for FastAPI
            </h2>
            <Badge variant="terracotta">Running (Stage 9/11)</Badge>
          </div>
          <p className="text-xs text-[#6A6E78] dark:text-[#9EA3B0] mt-1">
            Autonomous observe-decide-act loop active • Plan ID: <span className="font-mono">plan-179533412</span> • Version 2
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#E8E2D8] dark:border-[#2C313E] text-xs font-semibold text-[#6A6E78] hover:text-[#1E2229] transition-colors">
            <PauseCircle className="w-3.5 h-3.5" />
            <span>Pause Job</span>
          </button>
          <button className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#C85A32] text-white text-xs font-semibold shadow-xs hover:bg-[#B54E29] transition-colors">
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Sync State</span>
          </button>
        </div>
      </div>

      {/* 11-Stage Workflow Stepper */}
      <div className="bg-white dark:bg-[#1A1D23] border border-[#E8E2D8] dark:border-[#2C313E] rounded-xl p-6 shadow-xs overflow-x-auto">
        <h3 className="text-xs font-bold uppercase tracking-wider text-[#6A6E78] mb-4">
          11-Stage PromptIQ Pipeline Execution
        </h3>
        <div className="flex items-center justify-between min-w-[760px]">
          {WORKFLOW_STAGES.map((stg, idx) => {
            const isCompleted = idx < currentStageIndex
            const isCurrent = idx === currentStageIndex
            return (
              <div key={stg.id} className="flex-1 flex flex-col items-center relative">
                {idx > 0 && (
                  <div
                    className={`absolute top-3.5 -left-1/2 w-full h-0.5 z-0 ${
                      isCompleted ? 'bg-[#2D6A4F] dark:bg-[#7DA18F]' : 'bg-[#E8E2D8] dark:bg-[#2C313E]'
                    }`}
                  />
                )}
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold relative z-10 ${
                    isCompleted
                      ? 'bg-[#2D6A4F] text-white shadow-xs'
                      : isCurrent
                      ? 'bg-[#C85A32] text-white ring-4 ring-[#C85A32]/20'
                      : 'bg-[#F2EDE4] dark:bg-[#242831] text-[#6A6E78] dark:text-[#9EA3B0]'
                  }`}
                >
                  {isCompleted ? <CheckCircle2 className="w-4 h-4" /> : idx + 1}
                </div>
                <span
                  className={`mt-2 text-[11px] font-semibold tracking-tight capitalize ${
                    isCurrent
                      ? 'text-[#C85A32] dark:text-[#D96B43]'
                      : isCompleted
                      ? 'text-[#2D6A4F] dark:text-[#7DA18F]'
                      : 'text-[#6A6E78] dark:text-[#9EA3B0]'
                  }`}
                >
                  {stg.name}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* 2-Column Execution Workbench */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Subtask DAG Execution Hierarchy */}
        <div className="lg:col-span-2 bg-white dark:bg-[#1A1D23] border border-[#E8E2D8] dark:border-[#2C313E] rounded-xl overflow-hidden shadow-xs">
          <div className="p-4 border-b border-[#E8E2D8] dark:border-[#2C313E] flex items-center justify-between bg-[#FAF7F0] dark:bg-[#1E222A]">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-[#C85A32]" />
              <h4 className="text-xs font-bold text-[#1E2229] dark:text-[#F2EFE9]">Subtask Execution DAG</h4>
            </div>
            <span className="text-[11px] text-[#6A6E78]">8 subtasks planned</span>
          </div>

          <div className="divide-y divide-[#E8E2D8] dark:divide-[#2C313E]">
            {subtasks.map((st) => {
              const isSelected = selectedSubtask === st.id
              return (
                <div
                  key={st.id}
                  onClick={() => setSelectedSubtask(st.id)}
                  className={`p-4 transition-colors cursor-pointer ${
                    isSelected
                      ? 'bg-[#FAF7F0] dark:bg-[#212632]'
                      : 'hover:bg-[#FDFBF7] dark:hover:bg-[#1D212B]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span className="font-mono text-xs font-semibold text-[#6A6E78]">{st.id}</span>
                      <h5 className="text-xs font-bold text-[#1E2229] dark:text-[#F2EFE9]">{st.name}</h5>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-[#6A6E78] font-mono">{st.duration}</span>
                      <Badge
                        variant={
                          st.status === 'completed'
                            ? 'success'
                            : st.status === 'running'
                            ? 'terracotta'
                            : 'outline'
                        }
                      >
                        {st.status}
                      </Badge>
                    </div>
                  </div>
                  <p className="mt-1.5 text-xs text-[#6A6E78] dark:text-[#9EA3B0] leading-relaxed">
                    {st.output}
                  </p>
                </div>
              )
            })}
          </div>
        </div>

        {/* Live Observe-Decide-Act Tool Logs */}
        <div className="bg-white dark:bg-[#1A1D23] border border-[#E8E2D8] dark:border-[#2C313E] rounded-xl overflow-hidden shadow-xs flex flex-col">
          <div className="p-4 border-b border-[#E8E2D8] dark:border-[#2C313E] flex items-center justify-between bg-[#FAF7F0] dark:bg-[#1E222A]">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-[#C85A32]" />
              <h4 className="text-xs font-bold text-[#1E2229] dark:text-[#F2EFE9]">Tool Activity & Permissions</h4>
            </div>
            <Badge variant="sage">Sandboxed</Badge>
          </div>

          <div className="p-4 space-y-3 flex-1 overflow-y-auto max-h-[460px]">
            {toolLogs.map((log, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-[#FAF7F0] dark:bg-[#15171D] border border-[#E8E2D8] dark:border-[#2C313E] text-xs font-mono space-y-1"
              >
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[#C85A32] font-bold">{log.tool}</span>
                  <span className="text-[#6A6E78]">{log.timestamp}</span>
                </div>
                <div className="text-[10px] text-[#2D6A4F] dark:text-[#7DA18F]">{log.permission}</div>
                <p className="text-[11px] text-[#4A4E58] dark:text-[#A0A5B2] font-sans pt-1">
                  {log.details}
                </p>
              </div>
            ))}
          </div>

          <div className="p-3 border-t border-[#E8E2D8] dark:border-[#2C313E] bg-[#FAF7F0] dark:bg-[#1E222A] text-[11px] text-[#6A6E78] flex items-center justify-between">
            <span>Infinite loop detection: Active</span>
            <span className="text-[#2D6A4F] font-semibold">0 oscillations</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default WorkflowWorkbench

