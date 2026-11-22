import React, { useState } from 'react'
import {
  Boxes,
  Shield,
  RotateCcw,
  CheckCircle2,
  PauseCircle,
  PlayCircle,
  Layers,
  ChevronRight,
  Terminal,
} from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { WORKFLOW_STAGES } from '@/lib/constants'

export function WorkflowWorkbench() {
  const [currentStageIndex, setCurrentStageIndex] = useState(8)
  const [isPaused, setIsPaused] = useState(false)
  const [selectedSubtaskId, setSelectedSubtaskId] = useState<string>('task-04-validate')

  const [subtasks, setSubtasks] = useState([
    {
      id: 'task-01-discover',
      name: 'Task Family Archetype Identification',
      status: 'completed',
      method: 'classify_intent',
      duration: '12ms',
      output: 'Matched archetype: software_engineering (backend middleware)',
    },
    {
      id: 'task-02-constitution',
      name: 'Constitution Requirement Resolution',
      status: 'completed',
      method: 'resolve_constitution',
      duration: '18ms',
      output: 'Invariants checked: zero-price anti-BYOK, no-local-inference, 5-tier permissions.',
    },
    {
      id: 'task-03-dag',
      name: 'DAG Subtask Decomposition',
      status: 'completed',
      method: 'plan_dag',
      duration: '45ms',
      output: 'Generated 8 dependency-ordered execution steps (Plan v1).',
    },
    {
      id: 'task-04-validate',
      name: 'Tool Invocation & Execution',
      status: 'running',
      method: 'execute_tool_sandbox',
      duration: '142ms',
      output: 'Evaluating candidate middleware implementation against schema assertions.',
    },
    {
      id: 'task-05-autopsy',
      name: 'Forensic Prompt Autopsy Check',
      status: 'pending',
      method: 'critic_autopsy',
      duration: '—',
      output: 'Scheduled after tool validation pass.',
    },
    {
      id: 'task-06-persist',
      name: 'State & Memory Persistence',
      status: 'pending',
      method: 'filesystem_write',
      duration: '—',
      output: 'Awaiting upstream completion.',
    },
  ])

  const [toolLogs, setToolLogs] = useState([
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
      details: 'Plan version updated from v1 -> v2. Subtask task-06-persist marked SKIPPED.',
      status: 'success',
    },
  ])

  const handleToggleSubtask = (id: string) => {
    setSelectedSubtaskId(id)
    setSubtasks((prev) =>
      prev.map((st) =>
        st.id === id
          ? {
              ...st,
              status: st.status === 'completed' ? 'running' : 'completed',
              duration: st.duration === '—' ? '28ms' : st.duration,
            }
          : st
      )
    )
  }

  const handleAddReplan = () => {
    const newLog = {
      timestamp: new Date().toISOString().split('T')[1].slice(0, 12),
      tool: 'replan_engine',
      permission: 'system [ALLOWED]',
      details: `Interactive replan step triggered by user. Shifted to Stage ${currentStageIndex + 1}.`,
      status: 'success',
    }
    setToolLogs([newLog, ...toolLogs])
    if (currentStageIndex < WORKFLOW_STAGES.length - 1) {
      setCurrentStageIndex(currentStageIndex + 1)
    }
  }

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Workbench Header */}
      <div className="bg-white dark:bg-[#1A1D23] border border-[#E8E2D8] dark:border-[#2C313E] rounded-xl p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold text-[#C85A32]">WF-8921</span>
            <h2 className="text-base font-bold text-[#1E2229] dark:text-[#F2EFE9]">
              Implement distributed idempotency key middleware for FastAPI
            </h2>
            <Badge variant={isPaused ? 'warning' : 'terracotta'}>
              {isPaused ? 'PAUSED' : `RUNNING (Stage ${currentStageIndex + 1}/${WORKFLOW_STAGES.length})`}
            </Badge>
          </div>
          <p className="text-xs text-[#6A6E78] dark:text-[#9EA3B0] mt-1">
            Autonomous observe-decide-act loop active • Plan ID: <span className="font-mono">plan-179533412</span> • Version 2
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setIsPaused(!isPaused)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#E8E2D8] dark:border-[#2C313E] bg-white dark:bg-[#20242E] text-xs font-semibold text-[#1E2229] dark:text-[#F2EFE9] hover:bg-[#FAF7F0] transition-colors shadow-xs"
          >
            {isPaused ? (
              <>
                <PlayCircle className="w-3.5 h-3.5 text-[#2D6A4F]" />
                <span>Resume Job</span>
              </>
            ) : (
              <>
                <PauseCircle className="w-3.5 h-3.5 text-[#C85A32]" />
                <span>Pause Job</span>
              </>
            )}
          </button>
          <button
            onClick={handleAddReplan}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#C85A32] hover:bg-[#B54E29] text-white text-xs font-semibold shadow-xs transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Step Forward</span>
          </button>
        </div>
      </div>

      {/* 11-Stage Workflow Stepper (Clickable stages!) */}
      <div className="bg-white dark:bg-[#1A1D23] border border-[#E8E2D8] dark:border-[#2C313E] rounded-xl p-6 shadow-xs overflow-x-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[#6A6E78]">
            11-Stage PromptIQ Pipeline Execution
          </h3>
          <span className="text-[11px] text-[#6A6E78]">Click any stage step to inspect</span>
        </div>

        <div className="flex items-center justify-between min-w-[760px]">
          {WORKFLOW_STAGES.map((stg, idx) => {
            const isCompleted = idx < currentStageIndex
            const isCurrent = idx === currentStageIndex
            return (
              <div
                key={stg.id}
                onClick={() => setCurrentStageIndex(idx)}
                className="flex-1 flex flex-col items-center relative cursor-pointer group"
              >
                {idx > 0 && (
                  <div
                    className={`absolute top-3.5 -left-1/2 w-full h-0.5 z-0 ${
                      isCompleted ? 'bg-[#2D6A4F] dark:bg-[#7DA18F]' : 'bg-[#E8E2D8] dark:border-[#2C313E]'
                    }`}
                  />
                )}
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold relative z-10 transition-transform group-hover:scale-110 ${
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
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#1E2229] dark:text-[#F2EFE9]">
                Subtask DAG Plan (Plan Version 2)
              </h3>
            </div>
            <span className="text-[11px] text-[#6A6E78]">Click any task to toggle state</span>
          </div>

          <div className="p-4 space-y-3">
            {subtasks.map((st) => {
              const isSelected = selectedSubtaskId === st.id
              return (
                <div
                  key={st.id}
                  onClick={() => handleToggleSubtask(st.id)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'border-[#C85A32] bg-[#FAF7F0]/60 dark:bg-[#20242E]'
                      : 'border-[#E8E2D8] dark:border-[#2C313E] hover:border-[#D5CCC0]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span className="font-mono text-xs text-[#6A6E78] font-bold">{st.id}</span>
                      <h4 className="text-xs font-semibold text-[#1E2229] dark:text-[#F2EFE9]">{st.name}</h4>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[10px] text-[#6A6E78]">{st.duration}</span>
                      <Badge variant={st.status === 'completed' ? 'success' : st.status === 'running' ? 'terracotta' : 'outline'}>
                        {st.status.toUpperCase()}
                      </Badge>
                    </div>
                  </div>

                  <p className="mt-2 text-xs font-mono text-[#4A4E58] dark:text-[#A0A5B2] bg-[#FAF7F0] dark:bg-[#15181E] p-2.5 rounded-lg border border-[#E8E2D8] dark:border-[#2C313E]">
                    {st.output}
                  </p>
                </div>
              )
            })}
          </div>
        </div>

        {/* Live Sandboxed Tool Activity Logs */}
        <div className="bg-white dark:bg-[#1A1D23] border border-[#E8E2D8] dark:border-[#2C313E] rounded-xl overflow-hidden shadow-xs flex flex-col">
          <div className="p-4 border-b border-[#E8E2D8] dark:border-[#2C313E] bg-[#FAF7F0] dark:bg-[#1E222A] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-[#2D6A4F]" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#1E2229] dark:text-[#F2EFE9]">
                Live Tool Activity Log
              </h3>
            </div>
            <span className="text-[10px] font-mono text-[#2D6A4F] flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-[#2D6A4F] animate-pulse" />
              RECORDING
            </span>
          </div>

          <div className="p-3 font-mono text-xs space-y-3 overflow-y-auto max-h-96 flex-1">
            {toolLogs.map((log, i) => (
              <div key={i} className="p-2.5 rounded-lg bg-[#FAF7F0] dark:bg-[#15181E] border border-[#E8E2D8] dark:border-[#2C313E] space-y-1">
                <div className="flex items-center justify-between text-[10px] text-[#6A6E78]">
                  <span>{log.timestamp}</span>
                  <span className="font-bold text-[#C85A32]">{log.tool}</span>
                </div>
                <div className="text-[11px] font-medium text-[#2D6A4F] dark:text-[#7DA18F]">{log.permission}</div>
                <div className="text-[11px] text-[#1E2229] dark:text-[#F2EFE9] leading-relaxed">{log.details}</div>
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
