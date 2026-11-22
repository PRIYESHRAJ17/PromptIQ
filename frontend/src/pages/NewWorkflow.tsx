import React, { useState } from 'react'
import {
  Sparkles,
  Bot,
  Code,
  Search,
  TrendingUp,
  Compass,
  FileText,
  BarChart2,
  BookOpen,
  GraduationCap,
  PlayCircle,
  ArrowRight,
  ShieldCheck,
  Check,
} from 'lucide-react'
import { TASK_FAMILIES, TARGET_ENVIRONMENTS } from '@/lib/constants'
import { Badge } from '@/components/ui/Badge'
import type { TaskFamilyId } from '@/types'

interface NewWorkflowProps {
  onWorkflowCreated: (jobId: string) => void
}

const ICON_MAP: Record<string, React.ReactNode> = {
  Code: <Code className="w-5 h-5" />,
  Search: <Search className="w-5 h-5" />,
  Bot: <Bot className="w-5 h-5" />,
  TrendingUp: <TrendingUp className="w-5 h-5" />,
  Sparkles: <Sparkles className="w-5 h-5" />,
  Compass: <Compass className="w-5 h-5" />,
  FileText: <FileText className="w-5 h-5" />,
  BarChart2: <BarChart2 className="w-5 h-5" />,
  BookOpen: <BookOpen className="w-5 h-5" />,
  GraduationCap: <GraduationCap className="w-5 h-5" />,
}

export function NewWorkflow({ onWorkflowCreated }: NewWorkflowProps) {
  const [objective, setObjective] = useState('')
  const [selectedFamily, setSelectedFamily] = useState<TaskFamilyId>('software_engineering')
  const [selectedTarget, setSelectedTarget] = useState('google-antigravity')
  const [depth, setDepth] = useState<'quick' | 'guided' | 'deep'>('guided')
  const [constraints, setConstraints] = useState('Strictly no paid API keys / zero-cost hosted model gateway.')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleLaunch = async () => {
    const finalObjective = objective.trim() || 'Implement distributed idempotency key middleware for FastAPI with zero paid API keys'
    setObjective(finalObjective)
    setIsSubmitting(true)

    // Simulate creation or call API
    setTimeout(() => {
      setIsSubmitting(false)
      onWorkflowCreated('WF-8922')
    }, 600)
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Page Title */}
      <div>
        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-[#C85A32]/10 text-[#C85A32] dark:text-[#D96B43] mb-2">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Autonomous AI Orchestrator</span>
        </div>
        <h2 className="font-serif-title text-3xl font-bold tracking-tight text-[#1E2229] dark:text-[#F2EFE9]">
          Create New Autonomous Workflow
        </h2>
        <p className="text-xs text-[#6A6E78] dark:text-[#9EA3B0] mt-1">
          Specify your goal and constraints. PromptIQ will decompose tasks into a dependency DAG, check tool permissions, and execute the observe-decide-act loop.
        </p>
      </div>

      {/* 1. Objective Input Card */}
      <div className="bg-white dark:bg-[#1A1D23] border border-[#E8E2D8] dark:border-[#2C313E] rounded-xl p-6 shadow-xs space-y-4">
        <label className="block text-xs font-bold uppercase tracking-wider text-[#1E2229] dark:text-[#F2EFE9]">
          1. What is your objective?
        </label>
        <textarea
          rows={3}
          value={objective}
          onChange={(e) => setObjective(e.target.value)}
          placeholder="e.g. Implement distributed idempotency key middleware in FastAPI with Redis/SQLite failover and zero external paid API dependencies..."
          className="w-full p-3.5 rounded-lg bg-[#FAF7F0] dark:bg-[#15171D] border border-[#E8E2D8] dark:border-[#2C313E] text-xs text-[#1E2229] dark:text-[#F2EFE9] focus:outline-none focus:ring-1 focus:ring-[#C85A32] leading-relaxed resize-none"
        />

        <div className="flex flex-wrap gap-2 text-xs text-[#6A6E78]">
          <span className="font-semibold text-xs">Examples:</span>
          {[
            'Implement distributed idempotency key middleware',
            'Synthesize vector indexing literature with character citations',
            'Build 11-stage autonomous observe-decide-act agent loop',
          ].map((ex) => (
            <button
              key={ex}
              onClick={() => setObjective(ex)}
              className="px-2.5 py-1 rounded-md bg-[#FAF7F0] dark:bg-[#20242E] border border-[#E8E2D8] dark:border-[#2C313E] hover:border-[#C85A32] text-xs transition-colors"
            >
              {ex}
            </button>
          ))}
        </div>
      </div>

      {/* 2. Task Family Selection Grid */}
      <div className="space-y-3">
        <label className="block text-xs font-bold uppercase tracking-wider text-[#1E2229] dark:text-[#F2EFE9]">
          2. Select Task Specialization Family (10 Canonical Families)
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {TASK_FAMILIES.map((fam) => {
            const isSelected = selectedFamily === fam.id
            return (
              <div
                key={fam.id}
                onClick={() => setSelectedFamily(fam.id)}
                className={`p-4 rounded-xl border transition-all cursor-pointer flex items-start gap-3.5 ${
                  isSelected
                    ? 'bg-white dark:bg-[#1E222A] border-[#C85A32] shadow-xs ring-1 ring-[#C85A32]'
                    : 'bg-white/60 dark:bg-[#1A1D23] border-[#E8E2D8] dark:border-[#2C313E] hover:border-[#D5CCC0]'
                }`}
              >
                <div
                  className={`p-2 rounded-lg shrink-0 ${
                    isSelected
                      ? 'bg-[#C85A32] text-white'
                      : 'bg-[#FAF7F0] dark:bg-[#252A35] text-[#C85A32] dark:text-[#D96B43]'
                  }`}
                >
                  {ICON_MAP[fam.icon]}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-[#1E2229] dark:text-[#F2EFE9]">{fam.name}</h4>
                    {isSelected && <Check className="w-4 h-4 text-[#C85A32]" />}
                  </div>
                  <p className="text-[11px] text-[#6A6E78] dark:text-[#9EA3B0] mt-1 line-clamp-2 leading-relaxed">
                    {fam.description}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* 3. Target Environment & Constraints */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Target Environment */}
        <div className="bg-white dark:bg-[#1A1D23] border border-[#E8E2D8] dark:border-[#2C313E] rounded-xl p-5 shadow-xs space-y-3">
          <label className="block text-xs font-bold uppercase tracking-wider text-[#1E2229] dark:text-[#F2EFE9]">
            3. Target Compilation Format
          </label>
          <div className="space-y-2">
            {TARGET_ENVIRONMENTS.map((target) => (
              <label
                key={target.id}
                className={`flex items-center justify-between p-3 rounded-lg border text-xs cursor-pointer transition-colors ${
                  selectedTarget === target.id
                    ? 'border-[#C85A32] bg-[#FAF7F0] dark:bg-[#1E222A] font-semibold text-[#C85A32]'
                    : 'border-[#E8E2D8] dark:border-[#2C313E] text-[#1E2229] dark:text-[#F2EFE9]'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <input
                    type="radio"
                    name="targetEnv"
                    checked={selectedTarget === target.id}
                    onChange={() => setSelectedTarget(target.id)}
                    className="text-[#C85A32] focus:ring-[#C85A32]"
                  />
                  <span>{target.name}</span>
                </div>
                <Badge variant="outline">{target.tag}</Badge>
              </label>
            ))}
          </div>
        </div>

        {/* Discovery Depth & Constraints */}
        <div className="bg-white dark:bg-[#1A1D23] border border-[#E8E2D8] dark:border-[#2C313E] rounded-xl p-5 shadow-xs space-y-4">
          <label className="block text-xs font-bold uppercase tracking-wider text-[#1E2229] dark:text-[#F2EFE9]">
            4. Discovery Depth & Policy
          </label>

          <div className="flex gap-2">
            {(['quick', 'guided', 'deep'] as const).map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => setDepth(d)}
                className={`flex-1 py-2 text-xs font-semibold rounded-lg capitalize border transition-all ${
                  depth === d
                    ? 'bg-[#C85A32] text-white border-[#C85A32] shadow-xs'
                    : 'bg-[#FAF7F0] dark:bg-[#1E222A] border-[#E8E2D8] dark:border-[#2C313E] text-[#6A6E78] dark:text-[#9EA3B0]'
                }`}
              >
                {d}
              </button>
            ))}
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-[#6A6E78] mb-1">
              Negative Boundaries & Constraints
            </label>
            <input
              type="text"
              value={constraints}
              onChange={(e) => setConstraints(e.target.value)}
              className="w-full p-2.5 rounded-lg bg-[#FAF7F0] dark:bg-[#15171D] border border-[#E8E2D8] dark:border-[#2C313E] text-xs text-[#1E2229] dark:text-[#F2EFE9] focus:outline-none focus:ring-1 focus:ring-[#C85A32]"
            />
          </div>

          <div className="p-3 rounded-lg bg-[#EBF5EE] text-[#2D6A4F] border border-[#C7E6D3] dark:bg-[#1B2F23] dark:text-[#7DA18F] dark:border-[#2C4A38] text-[11px] flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 shrink-0" />
            <span>Guaranteed zero-cost route. Permission checking enforced on tool calls.</span>
          </div>
        </div>
      </div>

      {/* Launch CTA */}
      <div className="pt-4 flex items-center justify-end gap-4">
        <button
          onClick={handleLaunch}
          disabled={isSubmitting}
          className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-[#C85A32] hover:bg-[#B54E29] disabled:opacity-50 text-white text-xs font-bold shadow-xs transition-all cursor-pointer"
        >
          {isSubmitting ? (
            <span>Decomposing DAG & Planning...</span>
          ) : (
            <>
              <span>Launch Autonomous Workflow</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </div>
  )
}

export default NewWorkflow

