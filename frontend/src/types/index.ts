export type TaskFamilyId =
  | 'software_engineering'
  | 'research_intelligence'
  | 'ai_agent_development'
  | 'business_strategy'
  | 'prompt_improvement'
  | 'product_development'
  | 'writing_content'
  | 'data_analysis'
  | 'technical_documentation'
  | 'education_learning'

export interface TaskFamilyMeta {
  id: TaskFamilyId
  name: string
  description: string
  defaultDepth: 'quick' | 'guided' | 'deep'
  icon: string
}

export interface User {
  id: string
  email: string
  full_name?: string
  workspace_id?: string
  created_at: string
}

export interface Project {
  id: string
  name: string
  description?: string
  workspace_id: string
  current_constitution_version: number
  status: string
  created_at: string
  updated_at: string
}

export interface RequirementItem {
  id: string
  text: string
  category: string
  priority: 'P0' | 'P1' | 'P2' | 'P3'
  status: string
  provenance: string
}

export interface DecisionRecord {
  id: string
  decision: string
  rationale: string
  date: string
  supersedes?: string | null
  status?: string
}

export interface ProjectConstitution {
  id: string
  project_id: string
  version: number
  status: string
  is_approved: boolean
  goals: string[]
  requirements: RequirementItem[]
  scope: {
    in_scope?: string[]
    out_of_scope?: string[]
  }
  decisions: DecisionRecord[]
  created_at: string
  updated_at: string
}

export type JobStatus = 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'PAUSED' | 'CANCELLED'

export interface WorkflowJob {
  id: string
  workspace_id: string
  project_id: string
  operation_type: string
  status: JobStatus
  current_stage: string
  retry_count: number
  checkpoint_data?: Record<string, unknown>
  error_message?: string
  result_data?: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface AutopsyFinding {
  id: string
  category: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  finding: string
  evidence_passage?: string
  consequence: string
  recommendation: string
  blocks_release: boolean
}

export interface AutopsyResponse {
  verdict: 'approved' | 'ready_with_caveats' | 'needs_revision' | 'blocked' | 'unsuitable'
  overall_score: number
  findings: AutopsyFinding[]
  quality_scores: Record<string, number>
}

export interface ResearchClaim {
  id: string
  claim_text: string
  support_status: 'FULLY_SUPPORTED' | 'PARTIALLY_SUPPORTED' | 'CONTRADICTED' | 'UNSUPPORTED'
  evidence_passage?: string
  source_id?: string
  source_url?: string
}

export interface ArtifactItem {
  id: string
  project_id: string
  name: string
  artifact_type: string
  content_hash: string
  size_bytes: number
  version: number
  created_at: string
}

export interface QuotaStatus {
  workspace_id: string
  plan_tier: string
  requests_used: number
  requests_limit: number
  reset_in_seconds: number
  zero_price_guarantee: boolean
}

export interface EvidenceItem {
  id: string
  claim: string
  source_url: string
  source_title: string
  char_offset_start: number
  char_offset_end: number
  snippet: string
  support_status: 'supported' | 'contradicted' | 'disputed' | 'unverified'
  confidence_score: number
  contradictory_evidence?: string | null
  verified_at: string
}

export interface CompiledArtifact {
  id: string
  target_format: string
  file_path: string
  content_hash: string
  size_bytes: number
  created_at: string
  download_url: string
}
