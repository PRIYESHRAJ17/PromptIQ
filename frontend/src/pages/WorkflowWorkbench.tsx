import React, { useState, useEffect } from 'react'
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
  Loader2,
  AlertCircle,
  FileCode,
} from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { WORKFLOW_STAGES } from '@/lib/constants'
import api from '@/lib/api'
import type { WorkflowJob } from '@/types'

interface WorkflowWorkbenchProps {
  jobId?: string | null
}

export function WorkflowWorkbench({ jobId }: WorkflowWorkbenchProps) {
  const [job, setJob] = useState<WorkflowJob | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedSubtaskId, setSelectedSubtaskId] = useState<string | null>(null)
  const [isPausing, setIsPausing] = useState(false)

  useEffect(() => {
    let timer: ReturnType<typeof setInterval> | null = null
    let isCancelled = false

    async function fetchJob() {
      try {
        await api.ensureAuthenticated()
        let targetId = jobId
        if (!targetId) {
          const list = await api.getJobs()
          if (list && list.length > 0) {
            targetId = list[0].id
          }
        }

        if (targetId) {
          const data = await api.getJob(targetId)
          if (!isCancelled) {
            setJob(data)
            if (data.status === 'QUEUED' || data.status === 'RUNNING') {
              timer = setTimeout(fetchJob, 1500)
            }
          }
        }
      } catch (err) {
        console.error('Failed to fetch workflow job:', err)
      } finally {
        if (!isCancelled) setLoading(false)
      }
    }

    fetchJob()

    return () => {
      isCancelled = true
      if (timer) clearTimeout(timer)
    }
  }, [jobId])

  const handlePauseResume = async () => {
    if (!job) return
    setIsPausing(true)
    try {
      if (job.status === 'PAUSED') {
        const updated = await api.resumeJob(job.id)
        setJob(updated)
      } else {
        const updated = await api.pauseJob(job.id)
        setJob(updated)
      }
    } catch (err) {
      alert(`Action failed: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setIsPausing(false)
    }
  }

  if (loading) {
    return (
      <div className="p-16 text-center text-xs text-[#6A6E78]">
        <Loader2 className="w-8 h-8 animate-spin mx-auto mb-3 text-[#C85A32]" />
        Loading workflow execution state...
      </div>
    )
  }

  if (!job) {
    return (
      <div className="p-16 text-center rounded-xl border border-dashed border-[#E8E2D8] dark:border-[#2C313E] bg-white dark:bg-[#1A1D23] max-w-2xl mx-auto space-y-3">
        <Layers className="w-10 h-10 text-[#6A6E78] mx-auto opacity-40" />
        <h3 className="text-base font-bold text-[#1E2229] dark:text-[#F2EFE9]">No Workflow Job Available</h3>
        <p className="text-xs text-[#6A6E78] dark:text-[#9EA3B0]">
          No active or previous workflow jobs were found in this workspace. Launch an autonomous workflow from the New Workflow tab.
        </p>
      </div>
    )
  }

  const subtasks = (job.result_data?.subtasks as any[]) || []
  const iterations = (job.result_data?.iterations as any[]) || []
  const deliverable = job.result_data?.deliverable
  const objective = String(job.checkpoint_data?.objective || job.operation_type)
  const totalDuration = typeof job.result_data?.total_duration_ms === 'number'
    ? `${Math.round(job.result_data.total_duration_ms)}ms`
    : '—'
  const currentStageIndex = WORKFLOW_STAGES.findIndex(
    (s) => s.id === job.current_stage || s.name.toLowerCase().includes((job.current_stage || '').toLowerCase())
  )
  const activeStageIdx = currentStageIndex >= 0 ? currentStageIndex : job.status === 'COMPLETED' ? 10 : 2

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Workbench Header */}
      <div className="bg-white dark:bg-[#1A1D23] border border-[#E8E2D8] dark:border-[#2C313E] rounded-xl p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-xs font-bold text-[#C85A32]">
              {job.id.slice(0, 8)}...
            </span>
            <h2 className="text-base font-bold text-[#1E2229] dark:text-[#F2EFE9] line-clamp-1 max-w-xl">
              {objective}
            </h2>
            <Badge variant={job.status === 'COMPLETED' ? 'success' : job.status === 'RUNNING' ? 'terracotta' : 'warning'}>
              {job.status}
            </Badge>
            <Badge variant="outline">
              [DEMO / MOCK INFERENCE]
            </Badge>
          </div>
          <p className="text-xs text-[#6A6E78] dark:text-[#9EA3B0] mt-1">
            Operation: <span className="font-semibold">{job.operation_type}</span> • Stage: <span className="font-mono">{job.current_stage || 'active'}</span> • Plan ID: <span className="font-mono">{String(job.result_data?.plan_id || 'plan-init')}</span> • Execution duration: <span className="font-mono">{totalDuration}</span>
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handlePauseResume}
            disabled={isPausing || job.status === 'COMPLETED'}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#E8E2D8] dark:border-[#2C313E] bg-white dark:bg-[#20242E] text-xs font-semibold text-[#1E2229] dark:text-[#F2EFE9] hover:bg-[#FAF7F0] transition-colors shadow-xs disabled:opacity-50"
          >
            {job.status === 'PAUSED' ? (
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
        </div>
      </div>

      {/* 11-Stage Workflow Stepper */}
      <div className="bg-white dark:bg-[#1A1D23] border border-[#E8E2D8] dark:border-[#2C313E] rounded-xl p-6 shadow-xs overflow-x-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[#6A6E78]">
            11-Stage PromptIQ Pipeline Execution State
          </h3>
          <span className="text-[11px] text-[#6A6E78] font-mono">
            {job.status === 'COMPLETED' ? 'Pipeline Completed' : `Active Stage: ${WORKFLOW_STAGES[activeStageIdx]?.name || 'Execution'}`}
          </span>
        </div>

        <div className="flex items-center justify-between min-w-[760px]">
          {WORKFLOW_STAGES.map((stg, idx) => {
            const isCompleted = job.status === 'COMPLETED' || idx < activeStageIdx
            const isCurrent = job.status !== 'COMPLETED' && idx === activeStageIdx
            return (
              <div
                key={stg.id}
                className="flex-1 flex flex-col items-center relative group"
              >
                {idx > 0 && (
                  <div
                    className={`absolute top-3.5 -left-1/2 w-full h-0.5 z-0 ${
                      isCompleted ? 'bg-[#2D6A4F] dark:bg-[#7DA18F]' : 'bg-[#E8E2D8] dark:border-[#2C313E]'
                    }`}
                  />
                )}
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold relative z-10 transition-transform ${
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
                Subtask DAG Plan ({subtasks.length} Subtasks)
              </h3>
            </div>
            <span className="text-[11px] text-[#6A6E78]">
              {subtasks.filter((s) => s.status === 'completed').length} / {subtasks.length} Completed
            </span>
          </div>

          <div className="p-4 space-y-3">
            {subtasks.length === 0 ? (
              <div className="p-8 text-center text-xs text-[#6A6E78]">
                <Layers className="w-6 h-6 text-[#6A6E78] mx-auto mb-2 opacity-50" />
                <p>Generating task DAG from intent requirements...</p>
              </div>
            ) : (
              subtasks.map((st) => {
                const isSelected = selectedSubtaskId === st.id
                return (
                  <div
                    key={st.id}
                    onClick={() => setSelectedSubtaskId(isSelected ? null : st.id)}
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
                        <span className="font-mono text-[10px] text-[#6A6E78]">{st.execution_method}</span>
                        <Badge variant={st.status === 'completed' ? 'success' : st.status === 'running' ? 'terracotta' : 'outline'}>
                          {st.status.toUpperCase()}
                        </Badge>
                      </div>
                    </div>

                    <div className="mt-2 text-xs text-[#4A4E58] dark:text-[#A0A5B2] space-y-1">
                      <p><span className="font-semibold text-stone-700 dark:text-stone-300">Objective:</span> {st.objective}</p>
                      <p><span className="font-semibold text-stone-700 dark:text-stone-300">Criteria:</span> {st.verification_criteria}</p>
                    </div>

                    {st.output && (
                      <p className="mt-2 text-xs font-mono text-[#4A4E58] dark:text-[#A0A5B2] bg-[#FAF7F0] dark:bg-[#15181E] p-2.5 rounded-lg border border-[#E8E2D8] dark:border-[#2C313E]">
                        {st.output}
                      </p>
                    )}
                  </div>
                )
              })
            )}

            {/* Deliverable Section */}
            {Boolean(deliverable) && (
              <div className="mt-4 p-4 rounded-xl border border-emerald-200 dark:border-emerald-800/40 bg-emerald-50/50 dark:bg-emerald-950/20 space-y-2">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <h4 className="text-xs font-bold text-emerald-900 dark:text-emerald-200 uppercase tracking-wider">
                    Workflow Deliverable & Acceptance Verification
                  </h4>
                </div>
                <div className="text-xs font-mono text-emerald-800 dark:text-emerald-300 bg-white/80 dark:bg-black/30 p-3 rounded-lg border border-emerald-200 dark:border-emerald-800/40 overflow-x-auto">
                  <pre className="whitespace-pre-wrap">{typeof deliverable === 'string' ? deliverable : JSON.stringify(deliverable, null, 2)}</pre>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Live Sandboxed Tool Activity Logs */}
        <div className="bg-white dark:bg-[#1A1D23] border border-[#E8E2D8] dark:border-[#2C313E] rounded-xl overflow-hidden shadow-xs flex flex-col">
          <div className="p-4 border-b border-[#E8E2D8] dark:border-[#2C313E] bg-[#FAF7F0] dark:bg-[#1E222A] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-[#2D6A4F]" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#1E2229] dark:text-[#F2EFE9]">
                Live Tool Activity Log ({iterations.length})
              </h3>
            </div>
            <span className="text-[10px] font-mono text-[#2D6A4F] flex items-center gap-1">
              <span className={`w-2 h-2 rounded-full ${job.status === 'RUNNING' ? 'bg-[#2D6A4F] animate-pulse' : 'bg-stone-400'}`} />
              {job.status === 'RUNNING' ? 'RECORDING' : 'RECORDED'}
            </span>
          </div>

          <div className="p-3 font-mono text-xs space-y-3 overflow-y-auto max-h-[500px] flex-1">
            {iterations.length === 0 ? (
              <div className="p-8 text-center text-xs text-[#6A6E78]">
                No tool activity recorded yet.
              </div>
            ) : (
              iterations.map((log, i) => (
                <div key={i} className="p-2.5 rounded-lg bg-[#FAF7F0] dark:bg-[#15181E] border border-[#E8E2D8] dark:border-[#2C313E] space-y-1">
                  <div className="flex items-center justify-between text-[10px] text-[#6A6E78]">
                    <span>Iteration {log.iteration}</span>
                    <span className="font-bold text-[#C85A32]">{log.tool_name || log.subtask_id}</span>
                  </div>
                  <div className="text-[11px] font-medium text-[#2D6A4F] dark:text-[#7DA18F]">
                    {log.permission_decision} [{log.duration_ms ? `${Math.round(log.duration_ms)}ms` : '—'}]
                  </div>
                  <div className="text-[11px] text-[#1E2229] dark:text-[#F2EFE9] leading-relaxed">
                    {log.proposed_action}
                  </div>
                  {log.observation && (
                    <div className="text-[10px] text-stone-500 bg-stone-100 dark:bg-stone-800 p-1.5 rounded">
                      {log.observation}
                    </div>
                  )}
                </div>
              ))
            )}
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
