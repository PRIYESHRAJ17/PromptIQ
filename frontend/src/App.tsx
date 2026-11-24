import React, { useState } from 'react'
import Shell from './components/layout/Shell'
import Overview from './pages/Overview'
import Projects from './pages/Projects'
import NewWorkflow from './pages/NewWorkflow'
import WorkflowWorkbench from './pages/WorkflowWorkbench'
import PromptAutopsy from './pages/PromptAutopsy'
import ResearchEvidence from './pages/ResearchEvidence'
import TestLab from './pages/TestLab'
import Artifacts from './pages/Artifacts'
import AgentIntegrations from './pages/AgentIntegrations'
import Settings from './pages/Settings'

export default function App() {
  const [currentPage, setCurrentPage] = useState<string>('overview')
  const [activeJobId, setActiveJobId] = useState<string | null>(null)

  const handleWorkflowCreated = (jobId: string) => {
    setActiveJobId(jobId)
    setCurrentPage('workbench')
  }

  const renderPage = () => {
    switch (currentPage) {
      case 'overview':
        return <Overview onNavigate={setCurrentPage} />
      case 'projects':
        return <Projects />
      case 'new-workflow':
        return <NewWorkflow onWorkflowCreated={handleWorkflowCreated} />
      case 'workbench':
        return <WorkflowWorkbench jobId={activeJobId} />
      case 'autopsy':
        return <PromptAutopsy />
      case 'research':
        return <ResearchEvidence />
      case 'test-lab':
        return <TestLab />
      case 'artifacts':
        return <Artifacts />
      case 'integrations':
        return <AgentIntegrations />
      case 'settings':
        return <Settings />
      default:
        return <Overview onNavigate={setCurrentPage} />
    }
  }

  return (
    <Shell currentRoute={currentPage} onRouteChange={setCurrentPage}>
      {renderPage()}
    </Shell>
  )
}
