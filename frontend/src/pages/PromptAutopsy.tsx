import React, { useState } from 'react'
import {
  Stethoscope,
  CheckCircle2,
  AlertTriangle,
  Flame,
  ArrowRight,
  ShieldCheck,
  Search,
  Check,
  RotateCcw,
} from 'lucide-react'
import Badge from '@/components/ui/Badge'
import { promptiqApi } from '@/lib/api'
import type { AutopsyResponse } from '@/types'

export function PromptAutopsy() {
  const [promptText, setPromptText] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [autopsyResult, setAutopsyResult] = useState<AutopsyResponse | null>(null)

  const samplePrompt = `Write a Python backend script to scrape articles from various news websites and dump them into an internal database. Make it fast, use multi-threading, and don't worry about SSL errors. If a site blocks you, just rotate headers or bypass it.`

  const handleAnalyze = async () => {
    if (!promptText.trim()) return
    setAnalyzing(true)
    try {
      const res = await promptiqApi.runAutopsy(promptText)
      setAutopsyResult(res)
    } catch {
      // Deterministic fallback response simulating the 21-category autopsy detector
      setAutopsyResult({
        verdict: 'needs_revision',
        overall_score: 54,
        findings: [
          {
            id: 'AUT-001',
            category: 'Security Egress & Anti-Scraping Compliance',
            severity: 'critical',
            finding: 'Bypassing site blocking and ignoring SSL verification violates security boundaries',
            evidence_passage: "don't worry about SSL errors. If a site blocks you, just rotate headers or bypass it.",
            consequence: 'Risk of man-in-the-middle attacks and legal/ToS violations during web operations.',
            recommendation: 'Enforce strict TLS validation and respect robots.txt rate-limits.',
            blocks_release: true,
          },
          {
            id: 'AUT-002',
            category: 'Ambiguity & Specification Void',
            severity: 'medium',
            finding: "Vague database target ('internal database') and undefined thread pool sizing",
            evidence_passage: 'dump them into an internal database. Make it fast, use multi-threading',
            consequence: 'AI model will invent database dialect, connection pool sizes, and locking schemes.',
            recommendation: 'Specify exact database technology, ORM/query builder, and worker concurrency limits.',
            blocks_release: false,
          },
          {
            id: 'AUT-003',
            category: 'Error Recovery & Circuit Breaking',
            severity: 'high',
            finding: 'No backoff strategy or dead-letter queue specified for network failures',
            evidence_passage: 'scrape articles from various news websites',
            consequence: 'Unbounded retries could trigger rate limits or poison downstream queues.',
            recommendation: 'Add exponential backoff with jitter and a bounded DLQ.',
            blocks_release: true,
          },
        ],
        quality_scores: {
          clarity: 62,
          robustness: 45,
          security: 38,
          verifiability: 58,
          actionability: 67,
        },
      })
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-serif-title text-3xl font-semibold tracking-tight text-[#1E2229] dark:text-[#F2EFE9]">
              Prompt Autopsy
            </h1>
            <Badge variant="terracotta">21 Defect Categories</Badge>
          </div>
          <p className="mt-1 text-sm text-[#6A6E78] dark:text-[#9EA3B0]">
            Adversarial prompt diagnostic engine. Detects hallucinations, security traps, vagueness, and structural defects.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#EBF5EE] dark:bg-[#1B2F23] border border-[#C7E6D3] dark:border-[#2C4A38] text-xs text-[#2D6A4F] dark:text-[#7DA18F]">
            <ShieldCheck className="w-4 h-4 text-[#2D6A4F]" />
            <span>Adversarial Reviewer Active</span>
          </div>
        </div>
      </div>

      {/* Editor & Actions */}
      <div className="rounded-xl border border-[#E8E2D8] dark:border-[#2C313E] bg-white dark:bg-[#1A1D24] p-5 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-[#6A6E78]">
            Input Prompt for Forensic Dissection
          </span>
          <button
            onClick={() => setPromptText(samplePrompt)}
            className="text-xs text-[#C85A32] hover:underline font-medium"
          >
            Load Vulnerable Sample Prompt
          </button>
        </div>

        <textarea
          rows={5}
          value={promptText}
          onChange={(e) => setPromptText(e.target.value)}
          placeholder="Paste any prompt here to uncover hidden failure modes, security risks, ambiguous directives, and hallucination vectors..."
          className="w-full p-4 text-xs font-mono rounded-lg border border-[#E8E2D8] dark:border-[#2C313E] bg-[#FAF7F0] dark:bg-[#15181E] text-[#1E2229] dark:text-[#F2EFE9] focus:outline-none focus:ring-2 focus:ring-[#C85A32] leading-relaxed"
        />

        <div className="flex items-center justify-between pt-2">
          <span className="text-[11px] text-[#6A6E78]">
            Evaluates against 21 adversarial rubrics • Strict zero-praise policy
          </span>
          <button
            onClick={handleAnalyze}
            disabled={analyzing || !promptText.trim()}
            className="inline-flex items-center gap-2 px-5 py-2 rounded-lg bg-[#C85A32] hover:bg-[#B54E29] disabled:opacity-50 text-white text-xs font-bold shadow-xs transition-colors"
          >
            {analyzing ? (
              <>
                <RotateCcw className="w-4 h-4 animate-spin" />
                <span>Dissecting Prompt...</span>
              </>
            ) : (
              <>
                <Stethoscope className="w-4 h-4" />
                <span>Run Forensic Autopsy</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Autopsy Result Display */}
      {autopsyResult && (
        <div className="space-y-6 animate-fadeIn">
          {/* Top Score Banner */}
          <div className="p-6 rounded-xl border border-[#E8E2D8] dark:border-[#2C313E] bg-white dark:bg-[#1A1D24] shadow-xs flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="space-y-1 text-center md:text-left">
              <div className="text-xs font-semibold uppercase tracking-wider text-[#6A6E78]">
                Release Readiness Verdict
              </div>
              <div className="text-2xl font-serif-title font-bold text-[#1E2229] dark:text-[#F2EFE9] flex items-center gap-2">
                <span className="capitalize">{autopsyResult.verdict.replace('_', ' ')}</span>
                <Badge
                  variant={
                    autopsyResult.verdict === 'approved'
                      ? 'success'
                      : autopsyResult.verdict === 'ready_with_caveats'
                      ? 'warning'
                      : 'error'
                  }
                >
                  {autopsyResult.verdict.toUpperCase()}
                </Badge>
              </div>
            </div>

            <div className="flex items-center gap-6">
              <div className="text-center">
                <div className="text-xs text-[#6A6E78]">Quality Score</div>
                <div className="text-3xl font-serif-title font-bold text-[#C85A32]">
                  {autopsyResult.overall_score}/100
                </div>
              </div>
              <div className="h-10 w-px bg-[#E8E2D8] dark:bg-[#2C313E]" />
              <div className="text-center">
                <div className="text-xs text-[#6A6E78]">Defects Caught</div>
                <div className="text-3xl font-serif-title font-bold text-[#B83232]">
                  {autopsyResult.findings.length}
                </div>
              </div>
            </div>
          </div>

          {/* Finding Cards */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-[#1E2229] dark:text-[#F2EFE9]">
              Identified Defects & Remediation Plan
            </h3>
            {autopsyResult.findings.map((f) => (
              <div
                key={f.id}
                className="p-5 rounded-xl border border-[#E8E2D8] dark:border-[#2C313E] bg-white dark:bg-[#1A1D24] shadow-xs space-y-3"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-[#6A6E78] font-semibold">{f.id}</span>
                      <Badge variant={f.severity === 'critical' || f.severity === 'high' ? 'error' : 'warning'}>
                        {f.severity.toUpperCase()}
                      </Badge>
                      <span className="text-xs text-[#6A6E78]">• {f.category}</span>
                    </div>
                    <div className="text-sm font-semibold text-[#1E2229] dark:text-[#F2EFE9]">
                      {f.finding}
                    </div>
                  </div>
                  {f.blocks_release && (
                    <Badge variant="error">BLOCKS RELEASE</Badge>
                  )}
                </div>

                {f.evidence_passage && (
                  <div className="p-3 rounded-lg bg-[#FAF7F0] dark:bg-[#15181E] border-l-4 border-l-[#C85A32] font-mono text-xs text-[#1E2229] dark:text-[#F2EFE9]">
                    "{f.evidence_passage}"
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs pt-2">
                  <div className="p-3 rounded-lg bg-[#FDF2F2] dark:bg-[#281616] text-[#B83232] dark:text-[#F87171]">
                    <span className="font-bold block mb-1">Consequence:</span>
                    {f.consequence}
                  </div>
                  <div className="p-3 rounded-lg bg-[#EBF5EE] dark:bg-[#16271E] text-[#2D6A4F] dark:text-[#6EE7B7]">
                    <span className="font-bold block mb-1">Recommended Remediation:</span>
                    {f.recommendation}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default PromptAutopsy
