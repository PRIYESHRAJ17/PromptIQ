import React, { useState, useEffect } from 'react'
import {
  LayoutDashboard,
  FolderGit2,
  PlusCircle,
  PlayCircle,
  Stethoscope,
  SearchCode,
  FlaskConical,
  Boxes,
  Puzzle,
  Settings,
  Moon,
  Sun,
  ShieldCheck,
  ChevronDown,
  Terminal,
  LogOut,
  Sparkles,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface ShellProps {
  currentRoute: string
  onRouteChange: (route: string) => void
  children: React.ReactNode
}

export function Shell({ currentRoute, onRouteChange, children }: ShellProps) {
  const [darkMode, setDarkMode] = useState(false)
  const [workspaceMenuOpen, setWorkspaceMenuOpen] = useState(false)

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  const navigation = [
    { id: 'overview', name: 'Overview', icon: LayoutDashboard },
    { id: 'projects', name: 'Projects & Memory', icon: FolderGit2 },
    { id: 'new-workflow', name: 'New Workflow', icon: PlusCircle, highlight: true },
    { id: 'workbench', name: 'Workflow Workbench', icon: PlayCircle },
    { id: 'autopsy', name: 'Prompt Autopsy', icon: Stethoscope },
    { id: 'research', name: 'Research & Evidence', icon: SearchCode },
    { id: 'test-lab', name: 'Test Lab', icon: FlaskConical },
    { id: 'artifacts', name: 'Artifacts', icon: Boxes },
    { id: 'integrations', name: 'Agent Integrations', icon: Puzzle },
    { id: 'settings', name: 'Settings', icon: Settings },
  ]

  return (
    <div className="min-h-screen flex bg-[#FBF9F5] dark:bg-[#111317] text-[#1E2229] dark:text-[#F2EFE9] antialiased">
      {/* Sidebar */}
      <aside className="w-64 border-r border-[#E8E2D8] dark:border-[#2C313E] bg-[#F7F4EE] dark:bg-[#16181E] flex flex-col shrink-0 select-none">
        {/* Brand Header */}
        <div className="h-16 px-5 border-b border-[#E8E2D8] dark:border-[#2C313E] flex items-center justify-between">
          <div className="flex items-center gap-2.5 cursor-pointer" onClick={() => onRouteChange('overview')}>
            <div className="w-8 h-8 rounded-lg bg-[#C85A32] flex items-center justify-center text-white font-bold text-base shadow-xs">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <div className="font-serif-title text-xl font-bold tracking-tight text-[#1E2229] dark:text-[#F2EFE9] leading-none">
                PromptIQ
              </div>
              <div className="text-[10px] tracking-wider uppercase font-semibold text-[#6A6E78] dark:text-[#9EA3B0] mt-0.5">
                V7 Intelligence
              </div>
            </div>
          </div>
          <div className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-[#EBF5EE] text-[#2D6A4F] border border-[#C7E6D3] dark:bg-[#1B2F23] dark:text-[#7DA18F] dark:border-[#2C4A38]">
            ₹0 FREE
          </div>
        </div>

        {/* Workspace Selector */}
        <div className="p-3 border-b border-[#E8E2D8] dark:border-[#2C313E]">
          <div
            className="p-2 rounded-lg bg-white dark:bg-[#1E222A] border border-[#E8E2D8] dark:border-[#2C313E] flex items-center justify-between cursor-pointer hover:border-[#D5CCC0] transition-colors"
            onClick={() => setWorkspaceMenuOpen(!workspaceMenuOpen)}
          >
            <div className="flex items-center gap-2 overflow-hidden">
              <div className="w-5 h-5 rounded bg-[#6B8E7D] text-white flex items-center justify-center text-[10px] font-bold">
                P
              </div>
              <span className="text-xs font-medium truncate text-[#1E2229] dark:text-[#F2EFE9]">
                Priyesh Workspace
              </span>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-[#6A6E78] dark:text-[#9EA3B0]" />
          </div>
        </div>

        {/* Navigation List */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const Icon = item.icon
            const isActive = currentRoute === item.id
            return (
              <button
                key={item.id}
                onClick={() => onRouteChange(item.id)}
                className={cn(
                  'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all text-left',
                  isActive
                    ? 'bg-[#C85A32] text-white font-semibold shadow-xs dark:bg-[#D96B43]'
                    : 'text-[#4A4E58] dark:text-[#A0A5B2] hover:bg-[#EDE7DC] dark:hover:bg-[#20242D] hover:text-[#1E2229] dark:hover:text-[#F2EFE9]',
                  item.highlight && !isActive && 'text-[#C85A32] dark:text-[#D96B43] font-semibold bg-[#F8EFE9] dark:bg-[#2B1E19]'
                )}
              >
                <Icon className={cn('w-4 h-4 shrink-0', isActive ? 'text-white' : 'opacity-80')} />
                <span className="truncate">{item.name}</span>
              </button>
            )
          })}
        </nav>

        {/* Zero-Price & Safety Status */}
        <div className="p-3 border-t border-[#E8E2D8] dark:border-[#2C313E]">
          <div className="p-2.5 rounded-lg bg-[#FAF7F0] dark:bg-[#1E222A] border border-[#E8E2D8] dark:border-[#2C313E] text-xs">
            <div className="flex items-center gap-1.5 text-[#2D6A4F] dark:text-[#7DA18F] font-semibold">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Centrally Hosted ₹0</span>
            </div>
            <p className="text-[11px] text-[#6A6E78] dark:text-[#9EA3B0] mt-1 leading-snug">
              No BYOK keys required. 100% free community inference tier.
            </p>
          </div>
        </div>

        {/* User Footer */}
        <div className="p-3 border-t border-[#E8E2D8] dark:border-[#2C313E] flex items-center justify-between">
          <div className="flex items-center gap-2 overflow-hidden">
            <div className="w-7 h-7 rounded-full bg-[#C85A32] text-white flex items-center justify-center text-xs font-semibold">
              PR
            </div>
            <div className="truncate">
              <div className="text-xs font-semibold truncate text-[#1E2229] dark:text-[#F2EFE9]">Priyesh Raj</div>
              <div className="text-[10px] text-[#6A6E78] dark:text-[#9EA3B0] truncate">Operator</div>
            </div>
          </div>
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-1.5 rounded-md hover:bg-[#EDE7DC] dark:hover:bg-[#20242D] text-[#6A6E78] dark:text-[#9EA3B0]"
            title="Toggle theme"
          >
            {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Header */}
        <header className="h-16 border-b border-[#E8E2D8] dark:border-[#2C313E] bg-white/80 dark:bg-[#16181E]/80 backdrop-blur-sm px-8 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-4">
            <h1 className="text-base font-semibold text-[#1E2229] dark:text-[#F2EFE9] capitalize">
              {navigation.find((n) => n.id === currentRoute)?.name || currentRoute}
            </h1>
            <div className="h-4 w-px bg-[#E8E2D8] dark:bg-[#2C313E]" />
            <span className="text-xs text-[#6A6E78] dark:text-[#9EA3B0]">
              From intent to verified AI execution
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => onRouteChange('new-workflow')}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-[#C85A32] hover:bg-[#B54E29] text-white text-xs font-medium shadow-xs transition-colors"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>Create Workflow</span>
            </button>
            <button
              onClick={() => onRouteChange('integrations')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#E8E2D8] dark:border-[#2C313E] bg-white dark:bg-[#1E222A] text-xs font-medium text-[#4A4E58] dark:text-[#A0A5B2] hover:bg-[#FAF7F0] dark:hover:bg-[#252A35] transition-colors"
            >
              <Terminal className="w-3.5 h-3.5 text-[#C85A32]" />
              <span>MCP & Plugins</span>
            </button>
          </div>
        </header>

        {/* Scrollable Page Body */}
        <main className="flex-1 overflow-y-auto p-8">{children}</main>
      </div>
    </div>
  )
}

export default Shell

