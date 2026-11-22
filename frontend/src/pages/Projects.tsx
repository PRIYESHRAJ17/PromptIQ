import React, { useState } from 'react'
import {
  FolderGit2,
  Plus,
  Search,
  BookOpen,
  CheckCircle2,
  FileCode,
  ShieldCheck,
  ChevronRight,
  Database,
  Layers,
  Sparkles,
  X,
} from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { formatDate } from '@/lib/utils'

export function Projects() {
  const [selectedProjectId, setSelectedProjectId] = useState<string>('proj-001')
  const [activeTab, setActiveTab] = useState<'constitution' | 'decisions' | 'requirements' | 'memory'>('constitution')
  const [searchQuery, setSearchQuery] = useState('')

  // Modals
  const [showNewProjectModal, setShowNewProjectModal] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [newProjectDesc, setNewProjectDesc] = useState('')

  const [showNewDecisionModal, setShowNewDecisionModal] = useState(false)
  const [newDecisionTitle, setNewDecisionTitle] = useState('')
  const [newDecisionRationale, setNewDecisionRationale] = useState('')
  const [newDecisionSupersedes, setNewDecisionSupersedes] = useState('')

  const [projects, setProjects] = useState([
    {
      id: 'proj-001',
      name: 'Continuous Memory System',
      description: 'Durable event-driven processing pipeline with cross-session decision tracking',
      version: 2,
      status: 'approved',
      updated_at: '2026-11-22T13:20:00Z',
      requirementsCount: 8,
      decisionsCount: 4,
    },
    {
      id: 'proj-002',
      name: 'Core Platform v7',
      description: 'PromptIQ core intelligence runtime, DAG task planner, and model gateway',
      version: 4,
      status: 'approved',
      updated_at: '2026-11-22T12:45:00Z',
      requirementsCount: 15,
      decisionsCount: 6,
    },
    {
      id: 'proj-003',
      name: 'Universal Agent Integrations',
      description: 'Platform native plugins for Antigravity, Claude Code, Cursor, Codex, Gemini',
      version: 1,
      status: 'approved',
      updated_at: '2026-11-22T11:15:00Z',
      requirementsCount: 6,
      decisionsCount: 2,
    },
  ])

  const [decisions, setDecisions] = useState([
    {
      id: 'DEC-002',
      decision: 'Use NATS JetStream for distributed event streaming',
      rationale: 'Native stream persistence and subject-based routing with zero external daemon requirement in test mode.',
      status: 'active',
      date: '2026-11-22',
      supersedes: 'DEC-001',
    },
    {
      id: 'DEC-001',
      decision: 'Use Redis Sentinel for distributed queueing',
      rationale: 'High throughput and automated leader failover (superseded by DEC-002 for simpler embedded operations).',
      status: 'superseded',
      date: '2026-11-21',
      supersedes: null,
    },
    {
      id: 'DEC-003',
      decision: 'Strict 5-Tier Tool Permission Hierarchy for Autonomous Loop',
      rationale: 'Prevents arbitrary filesystem writes and restricts destructive operations without explicit operator sign-off.',
      status: 'active',
      date: '2026-11-22',
      supersedes: null,
    },
  ])

  const [requirements] = useState([
    {
      id: 'REQ-CORE-001',
      text: 'Pipeline must process at least 1,000 events per second with sub-50ms p95 latency',
      priority: 'P0',
      category: 'performance',
      provenance: 'user_provided',
      status: 'confirmed',
    },
    {
      id: 'REQ-SEC-001',
      text: 'Strictly zero user API keys (anti-BYOK) and cardless ₹0 hosted community inference tier',
      priority: 'P0',
      category: 'security_governance',
      provenance: 'user_provided',
      status: 'confirmed',
    },
    {
      id: 'REQ-MEM-001',
      text: 'Cross-session decision memory with explicit supersession tracking',
      priority: 'P1',
      category: 'architecture',
      provenance: 'inferred',
      status: 'confirmed',
    },
    {
      id: 'REQ-UI-001',
      text: 'Lovable Product Analytics warm aesthetic with terracotta and sage highlights',
      priority: 'P1',
      category: 'user_experience',
      provenance: 'user_provided',
      status: 'confirmed',
    },
  ])

  const currentProject = projects.find((p) => p.id === selectedProjectId) || projects[0]

  const handleCreateProject = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newProjectName.trim()) return
    const newProj = {
      id: `proj-00${projects.length + 1}`,
      name: newProjectName.trim(),
      description: newProjectDesc.trim() || 'New user initialized project workspace',
      version: 1,
      status: 'approved',
      updated_at: new Date().toISOString(),
      requirementsCount: 4,
      decisionsCount: 1,
    }
    setProjects([newProj, ...projects])
    setSelectedProjectId(newProj.id)
    setNewProjectName('')
    setNewProjectDesc('')
    setShowNewProjectModal(false)
  }

  const handleCreateDecision = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newDecisionTitle.trim()) return
    const newDec = {
      id: `DEC-00${decisions.length + 1}`,
      decision: newDecisionTitle.trim(),
      rationale: newDecisionRationale.trim() || 'Adopted to maintain architectural integrity.',
      status: 'active',
      date: new Date().toISOString().split('T')[0],
      supersedes: newDecisionSupersedes.trim() || null,
    }
    setDecisions([newDec, ...decisions])
    setNewDecisionTitle('')
    setNewDecisionRationale('')
    setNewDecisionSupersedes('')
    setShowNewDecisionModal(false)
  }

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold font-serif-title text-[#1E2229] dark:text-[#F2EFE9]">
            Projects & Persistent Memory
          </h2>
          <p className="text-xs text-[#6A6E78] dark:text-[#9EA3B0] mt-0.5">
            Immutable Project Constitutions, versioned decision logs, and continuous cross-session memory
          </p>
        </div>
        <button
          onClick={() => setShowNewProjectModal(true)}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-[#C85A32] hover:bg-[#B54E29] text-white text-xs font-semibold shadow-xs transition-colors self-start"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Project</span>
        </button>
      </div>

      {/* New Project Modal */}
      {showNewProjectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white dark:bg-[#1A1D24] border border-[#E8E2D8] dark:border-[#2C313E] rounded-xl p-6 max-w-md w-full shadow-lg space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-[#1E2229] dark:text-[#F2EFE9]">Create New Project</h3>
              <button onClick={() => setShowNewProjectModal(false)} className="text-[#6A6E78] hover:text-[#1E2229]">
                <X className="w-4 h-4" />
              </button>
            </div>
            <form onSubmit={handleCreateProject} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-[#6A6E78] mb-1">Project Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Financial Ledger Engine"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-[#E8E2D8] dark:border-[#2C313E] bg-[#FAF7F0] dark:bg-[#15181E] text-[#1E2229] dark:text-[#F2EFE9] focus:outline-none focus:ring-1 focus:ring-[#C85A32]"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-[#6A6E78] mb-1">Description</label>
                <textarea
                  rows={3}
                  placeholder="Purpose, core architectural boundaries..."
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-[#E8E2D8] dark:border-[#2C313E] bg-[#FAF7F0] dark:bg-[#15181E] text-[#1E2229] dark:text-[#F2EFE9] focus:outline-none focus:ring-1 focus:ring-[#C85A32]"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowNewProjectModal(false)}
                  className="px-3 py-1.5 text-xs text-[#6A6E78] hover:text-[#1E2229]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs font-bold rounded-lg bg-[#C85A32] text-white hover:bg-[#B54E29]"
                >
                  Create Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* New Decision Modal */}
      {showNewDecisionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white dark:bg-[#1A1D24] border border-[#E8E2D8] dark:border-[#2C313E] rounded-xl p-6 max-w-md w-full shadow-lg space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-[#1E2229] dark:text-[#F2EFE9]">Record Architectural Decision</h3>
              <button onClick={() => setShowNewDecisionModal(false)} className="text-[#6A6E78] hover:text-[#1E2229]">
                <X className="w-4 h-4" />
              </button>
            </div>
            <form onSubmit={handleCreateDecision} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-[#6A6E78] mb-1">Decision Summary</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Use SQLite WAL mode for local zero-dependency storage"
                  value={newDecisionTitle}
                  onChange={(e) => setNewDecisionTitle(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-[#E8E2D8] dark:border-[#2C313E] bg-[#FAF7F0] dark:bg-[#15181E] text-[#1E2229] dark:text-[#F2EFE9] focus:outline-none focus:ring-1 focus:ring-[#C85A32]"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-[#6A6E78] mb-1">Rationale</label>
                <textarea
                  rows={2}
                  placeholder="Why this was chosen and what alternatives were rejected..."
                  value={newDecisionRationale}
                  onChange={(e) => setNewDecisionRationale(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-[#E8E2D8] dark:border-[#2C313E] bg-[#FAF7F0] dark:bg-[#15181E] text-[#1E2229] dark:text-[#F2EFE9] focus:outline-none focus:ring-1 focus:ring-[#C85A32]"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-[#6A6E78] mb-1">Supersedes Existing Decision (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g., DEC-001"
                  value={newDecisionSupersedes}
                  onChange={(e) => setNewDecisionSupersedes(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-[#E8E2D8] dark:border-[#2C313E] bg-[#FAF7F0] dark:bg-[#15181E] text-[#1E2229] dark:text-[#F2EFE9] focus:outline-none focus:ring-1 focus:ring-[#C85A32]"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowNewDecisionModal(false)}
                  className="px-3 py-1.5 text-xs text-[#6A6E78] hover:text-[#1E2229]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs font-bold rounded-lg bg-[#C85A32] text-white hover:bg-[#B54E29]"
                >
                  Record Decision
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Project Selector List */}
        <div className="space-y-3">
          <div className="relative">
            <Search className="w-4 h-4 text-[#6A6E78] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Filter projects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded-lg bg-white dark:bg-[#1A1D23] border border-[#E8E2D8] dark:border-[#2C313E] text-xs focus:outline-none focus:ring-1 focus:ring-[#C85A32]"
            />
          </div>

          <div className="space-y-2">
            {projects
              .filter((p) => p.name.toLowerCase().includes(searchQuery.toLowerCase()))
              .map((proj) => {
                const isSelected = selectedProjectId === proj.id
                return (
                  <div
                    key={proj.id}
                    onClick={() => setSelectedProjectId(proj.id)}
                    className={`p-4 rounded-xl border transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-white dark:bg-[#1E222A] border-[#C85A32] shadow-xs dark:border-[#D96B43]'
                        : 'bg-white/60 dark:bg-[#171920] border-[#E8E2D8] dark:border-[#2C313E] hover:border-[#D5CCC0]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-semibold text-[#1E2229] dark:text-[#F2EFE9]">{proj.name}</h4>
                      <Badge variant="terracotta">v{proj.version}</Badge>
                    </div>
                    <p className="text-xs text-[#6A6E78] dark:text-[#9EA3B0] mt-1 line-clamp-2">
                      {proj.description}
                    </p>
                    <div className="mt-3 pt-3 border-t border-[#F2EDE4] dark:border-[#262B36] flex items-center justify-between text-[11px] text-[#6A6E78] dark:text-[#9EA3B0]">
                      <span>{proj.requirementsCount} requirements</span>
                      <span>{proj.decisionsCount} decisions</span>
                    </div>
                  </div>
                )
              })}
          </div>
        </div>

        {/* Project Constitution & Memory Detail */}
        <div className="lg:col-span-2 bg-white dark:bg-[#1A1D23] border border-[#E8E2D8] dark:border-[#2C313E] rounded-xl overflow-hidden shadow-xs">
          {/* Project Banner */}
          <div className="p-6 border-b border-[#E8E2D8] dark:border-[#2C313E] bg-[#FAF7F0] dark:bg-[#1E222A]">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-[#1E2229] dark:text-[#F2EFE9]">
                    {currentProject.name}
                  </h3>
                  <Badge variant="success">Approved Constitution</Badge>
                </div>
                <p className="text-xs text-[#6A6E78] dark:text-[#9EA3B0] mt-1">
                  {currentProject.description}
                </p>
              </div>
              <div className="text-right">
                <div className="text-xs font-semibold text-[#C85A32]">Version {currentProject.version}.0</div>
                <div className="text-[11px] text-[#6A6E78] mt-0.5">{formatDate(currentProject.updated_at)}</div>
              </div>
            </div>

            {/* Sub-Tabs */}
            <div className="flex flex-wrap items-center justify-between gap-2 mt-6">
              <div className="flex gap-2">
                {[
                  { id: 'constitution', label: 'Constitution Overview' },
                  { id: 'requirements', label: `Requirements (${requirements.length})` },
                  { id: 'decisions', label: `Decision Log (${decisions.length})` },
                  { id: 'memory', label: 'Context Pack' },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                      activeTab === tab.id
                        ? 'bg-white dark:bg-[#1A1D23] text-[#C85A32] shadow-xs font-semibold'
                        : 'text-[#6A6E78] dark:text-[#9EA3B0] hover:text-[#1E2229]'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
              {activeTab === 'decisions' && (
                <button
                  onClick={() => setShowNewDecisionModal(true)}
                  className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-[#C85A32] text-white hover:bg-[#B54E29] transition-colors"
                >
                  + Add Decision
                </button>
              )}
            </div>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'constitution' && (
              <div className="space-y-6">
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-[#6A6E78] mb-2">Core Objective</h4>
                  <div className="p-3.5 rounded-lg bg-[#FAF7F0] dark:bg-[#20242E] text-xs font-medium text-[#1E2229] dark:text-[#F2EFE9] border border-[#E8E2D8] dark:border-[#2C313E]">
                    {currentProject.description}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-lg border border-[#E8E2D8] dark:border-[#2C313E]">
                    <span className="text-xs font-bold uppercase tracking-wider text-[#2D6A4F] dark:text-[#7DA18F]">
                      In Scope
                    </span>
                    <ul className="mt-2 text-xs space-y-1.5 text-[#4A4E58] dark:text-[#A0A5B2]">
                      <li>• High throughput async processing</li>
                      <li>• Dynamic DAG task execution</li>
                      <li>• Universal MCP agent plugins</li>
                      <li>• Zero-price hosted inference</li>
                    </ul>
                  </div>

                  <div className="p-4 rounded-lg border border-[#E8E2D8] dark:border-[#2C313E]">
                    <span className="text-xs font-bold uppercase tracking-wider text-[#B83232] dark:text-[#EF5350]">
                      Out of Scope
                    </span>
                    <ul className="mt-2 text-xs space-y-1.5 text-[#4A4E58] dark:text-[#A0A5B2]">
                      <li>• Paid API keys / BYOK models</li>
                      <li>• Local GPU / Ollama dependencies</li>
                      <li>• Telegram development (excluded sprint)</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'decisions' && (
              <div className="space-y-3">
                {decisions.map((dec) => (
                  <div
                    key={dec.id}
                    className="p-4 rounded-lg border border-[#E8E2D8] dark:border-[#2C313E] bg-[#FAF7F0]/50 dark:bg-[#1E222A]/50"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-xs text-[#C85A32]">{dec.id}</span>
                        <h5 className="text-xs font-semibold text-[#1E2229] dark:text-[#F2EFE9]">{dec.decision}</h5>
                      </div>
                      <Badge variant={dec.status === 'active' ? 'success' : 'outline'}>
                        {dec.status === 'active' ? 'Active' : `Superseded by ${dec.supersedes}`}
                      </Badge>
                    </div>
                    <p className="text-xs text-[#6A6E78] dark:text-[#9EA3B0] mt-2 leading-relaxed">
                      {dec.rationale}
                    </p>
                    <div className="mt-2 text-[10px] text-[#6A6E78] dark:text-[#9EA3B0]">
                      Recorded on {dec.date}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'requirements' && (
              <div className="space-y-2">
                {requirements.map((req) => (
                  <div
                    key={req.id}
                    className="p-3 rounded-lg border border-[#E8E2D8] dark:border-[#2C313E] flex items-center justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <Badge variant={req.priority === 'P0' ? 'terracotta' : 'sage'}>{req.priority}</Badge>
                      <span className="font-mono text-xs text-[#6A6E78]">{req.id}</span>
                      <span className="text-xs font-medium text-[#1E2229] dark:text-[#F2EFE9]">{req.text}</span>
                    </div>
                    <Badge variant="outline">{req.provenance}</Badge>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'memory' && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-[#6A6E78]">
                    Compiled Markdown Instruction Pack
                  </span>
                  <Badge variant="terracotta">Ready for Compilation</Badge>
                </div>
                <div className="p-4 rounded-lg bg-[#FAF7F0] dark:bg-[#15181E] border border-[#E8E2D8] dark:border-[#2C313E] font-mono text-xs text-[#1E2229] dark:text-[#F2EFE9] overflow-x-auto">
                  <pre className="whitespace-pre-wrap leading-relaxed">
{`# Project Constitution: ${currentProject.name}
## Version: ${currentProject.version} (Approved)

### Active Decisions:
${decisions.map(d => `- ${d.id}: ${d.decision}${d.supersedes ? ` (Supersedes ${d.supersedes})` : ''}`).join('\n')}

### Requirements:
${requirements.map(r => `- [${r.priority}] ${r.id}: ${r.text} (${r.provenance})`).join('\n')}`}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Projects
