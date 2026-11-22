import React, { useState } from 'react'
import {
  Activity,
  FolderGit2,
  CheckCircle2,
  Clock,
  Sparkles,
  ArrowUpRight,
  ShieldCheck,
  ChevronRight,
  PlayCircle,
} from 'lucide-react'
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { StatCard } from '@/components/ui/StatCard'
import { Badge } from '@/components/ui/Badge'
import { TASK_FAMILIES } from '@/lib/constants'

interface OverviewProps {
  onNavigate: (route: string) => void
}

const RUN_TRENDS = [
  { day: 'Mon', runs: 12, passed: 11 },
  { day: 'Tue', runs: 18, passed: 17 },
  { day: 'Wed', runs: 15, passed: 14 },
  { day: 'Thu', runs: 24, passed: 22 },
  { day: 'Fri', runs: 30, passed: 29 },
  { day: 'Sat', runs: 22, passed: 21 },
  { day: 'Sun', runs: 28, passed: 27 },
]

const TASK_FAMILY_STATS = [
  { name: 'Software', count: 18, fill: '#C85A32' },
  { name: 'Research', count: 14, fill: '#6B8E7D' },
  { name: 'AI Agents', count: 12, fill: '#D96B43' },
  { name: 'Business', count: 8, fill: '#82A292' },
  { name: 'Prompts', count: 16, fill: '#E07A5F' },
  { name: 'Product', count: 10, fill: '#52796F' },
  { name: 'Docs', count: 9, fill: '#C85A32' },
]

const RECENT_WORKFLOWS = [
  {
    id: 'WF-8921',
    objective: 'Implement distributed idempotency key middleware for FastAPI',
    project: 'Continuous Memory System',
    taskFamily: 'software_engineering',
    status: 'COMPLETED',
    stage: 'remember',
    duration: '2.4s',
    updated: '12 mins ago',
  },
  {
    id: 'WF-8920',
    objective: 'Synthesize state-of-the-art vector indexing techniques for search',
    project: 'Research Intelligence Lab',
    taskFamily: 'research_intelligence',
    status: 'COMPLETED',
    stage: 'deliver',
    duration: '3.8s',
    updated: '45 mins ago',
  },
  {
    id: 'WF-8919',
    objective: 'Refactor legacy async database connection pooling with failover',
    project: 'Core Platform v7',
    taskFamily: 'software_engineering',
    status: 'RUNNING',
    stage: 'execute',
    duration: '1.2s',
    updated: 'Just now',
  },
  {
    id: 'WF-8918',
    objective: 'Remediate severe ambiguity and missing schemas in agent prompts',
    project: 'Prompt Optimization',
    taskFamily: 'prompt_improvement',
    status: 'COMPLETED',
    stage: 'verify',
    duration: '0.8s',
    updated: '2 hours ago',
  },
]

export function Overview({ onNavigate }: OverviewProps) {
  const [selectedRange, setSelectedRange] = useState('7d')

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#F7F2E8] via-[#FDFBF7] to-[#FAF5EE] dark:from-[#1D212A] dark:via-[#191C23] dark:to-[#171920] border border-[#E8E2D8] dark:border-[#2C313E] p-8">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-[#C85A32]/10 text-[#C85A32] dark:text-[#D96B43] mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            <span>PromptIQ V7 Intelligence Operational</span>
          </div>
          <h2 className="font-serif-title text-3xl font-bold tracking-tight text-[#1E2229] dark:text-[#F2EFE9] sm:text-4xl">
            From intent to verified AI execution.
          </h2>
          <p className="mt-2 text-sm text-[#6A6E78] dark:text-[#9EA3B0] leading-relaxed">
            Turn complex engineering goals into structured, executable, and autonomously evaluated AI workflows.
            Zero user API keys required. 100% centrally managed hosted intelligence.
          </p>

          <div className="mt-5 flex items-center gap-3">
            <button
              onClick={() => onNavigate('new-workflow')}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#C85A32] hover:bg-[#B54E29] text-white text-xs font-semibold shadow-xs transition-colors"
            >
              <PlayCircle className="w-4 h-4" />
              <span>Launch New Workflow</span>
            </button>
            <button
              onClick={() => onNavigate('projects')}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-[#E8E2D8] dark:border-[#2C313E] bg-white dark:bg-[#1E222A] text-xs font-semibold text-[#1E2229] dark:text-[#F2EFE9] hover:bg-[#FAF7F0] transition-colors"
            >
              <span>Explore Projects & Memory</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Workflows"
          value="148"
          change="+18.4%"
          trend="up"
          description="Across 10 specialized task families"
          icon={<Activity className="w-4 h-4" />}
        />
        <StatCard
          title="Verification Pass Rate"
          value="96.2%"
          change="+4.1%"
          trend="up"
          description="Test Lab deterministic assertions"
          icon={<CheckCircle2 className="w-4 h-4" />}
        />
        <StatCard
          title="Active Projects"
          value="12"
          change="3 new"
          trend="neutral"
          description="With immutable Project Constitutions"
          icon={<FolderGit2 className="w-4 h-4" />}
        />
        <StatCard
          title="Hosted Quota Usage"
          value="14 / 60"
          change="₹0 Free"
          trend="neutral"
          description="Sliding window reset in 32 mins"
          icon={<ShieldCheck className="w-4 h-4" />}
        />
      </div>

      {/* Visual Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Workflow Execution Trends */}
        <div className="lg:col-span-2 bg-white dark:bg-[#1A1D23] border border-[#E8E2D8] dark:border-[#2C313E] rounded-xl p-6 shadow-xs">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-sm font-semibold text-[#1E2229] dark:text-[#F2EFE9]">
                Workflow Execution Velocity
              </h3>
              <p className="text-xs text-[#6A6E78] dark:text-[#9EA3B0] mt-0.5">
                Completed workflow jobs and verification pass rates
              </p>
            </div>
            <div className="flex gap-1 p-1 rounded-lg bg-[#FAF7F0] dark:bg-[#222631] border border-[#E8E2D8] dark:border-[#2C313E] text-xs">
              {['24h', '7d', '30d'].map((r) => (
                <button
                  key={r}
                  onClick={() => setSelectedRange(r)}
                  className={`px-2.5 py-0.5 rounded-md text-xs font-medium transition-colors ${
                    selectedRange === r
                      ? 'bg-white dark:bg-[#1A1D23] shadow-xs text-[#C85A32] font-semibold'
                      : 'text-[#6A6E78] dark:text-[#9EA3B0]'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={RUN_TRENDS}>
                <defs>
                  <linearGradient id="colorRuns" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#C85A32" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#C85A32" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="day" stroke="#9EA3B0" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#9EA3B0" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderRadius: '8px',
                    border: '1px solid #E8E2D8',
                    fontSize: '12px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="runs"
                  stroke="#C85A32"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorRuns)"
                  name="Executed Workflows"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Task Family Breakdown */}
        <div className="bg-white dark:bg-[#1A1D23] border border-[#E8E2D8] dark:border-[#2C313E] rounded-xl p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-[#1E2229] dark:text-[#F2EFE9]">
                Task Specialization
              </h3>
              <p className="text-xs text-[#6A6E78] dark:text-[#9EA3B0] mt-0.5">
                Distribution across 10 task families
              </p>
            </div>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={TASK_FAMILY_STATS} layout="vertical" margin={{ left: 10 }}>
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" stroke="#9EA3B0" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip />
                <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={16} fill="#C85A32" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Workflow Runs */}
      <div className="bg-white dark:bg-[#1A1D23] border border-[#E8E2D8] dark:border-[#2C313E] rounded-xl overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-[#E8E2D8] dark:border-[#2C313E] flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-[#1E2229] dark:text-[#F2EFE9]">
              Recent Workflow Executions
            </h3>
            <p className="text-xs text-[#6A6E78] dark:text-[#9EA3B0] mt-0.5">
              Autonomous observe-decide-act loop history and terminal states
            </p>
          </div>
          <button
            onClick={() => onNavigate('workbench')}
            className="text-xs font-semibold text-[#C85A32] dark:text-[#D96B43] hover:underline flex items-center gap-1"
          >
            <span>View All Runs</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-[#E8E2D8] dark:border-[#2C313E] bg-[#FAF7F0] dark:bg-[#1E222A] text-[#6A6E78] dark:text-[#9EA3B0]">
                <th className="py-3 px-6 font-semibold">Workflow ID</th>
                <th className="py-3 px-6 font-semibold">Objective</th>
                <th className="py-3 px-6 font-semibold">Task Family</th>
                <th className="py-3 px-6 font-semibold">Status</th>
                <th className="py-3 px-6 font-semibold">Duration</th>
                <th className="py-3 px-6 font-semibold">Updated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E8E2D8] dark:divide-[#2C313E]">
              {RECENT_WORKFLOWS.map((wf) => (
                <tr
                  key={wf.id}
                  onClick={() => onNavigate('workbench')}
                  className="hover:bg-[#FAF7F0] dark:hover:bg-[#222631] cursor-pointer transition-colors"
                >
                  <td className="py-3.5 px-6 font-mono font-medium text-[#C85A32] dark:text-[#D96B43]">
                    {wf.id}
                  </td>
                  <td className="py-3.5 px-6 font-medium text-[#1E2229] dark:text-[#F2EFE9] max-w-xs truncate">
                    {wf.objective}
                  </td>
                  <td className="py-3.5 px-6 text-[#6A6E78] dark:text-[#9EA3B0]">
                    <Badge variant="outline">
                      {TASK_FAMILIES.find((f) => f.id === wf.taskFamily)?.name || wf.taskFamily}
                    </Badge>
                  </td>
                  <td className="py-3.5 px-6">
                    <Badge
                      variant={
                        wf.status === 'COMPLETED'
                          ? 'success'
                          : wf.status === 'RUNNING'
                          ? 'terracotta'
                          : 'warning'
                      }
                    >
                      {wf.status}
                    </Badge>
                  </td>
                  <td className="py-3.5 px-6 text-[#6A6E78] dark:text-[#9EA3B0]">
                    {wf.duration}
                  </td>
                  <td className="py-3.5 px-6 text-[#6A6E78] dark:text-[#9EA3B0]">
                    {wf.updated}
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

