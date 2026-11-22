import React, { useState } from 'react';
import { Search, ExternalLink, CheckCircle2, AlertTriangle, XCircle, ShieldCheck, Database, Filter } from 'lucide-react';
import Badge from '../components/ui/Badge';
import type { EvidenceItem } from '../types';

const MOCK_EVIDENCE: EvidenceItem[] = [
  {
    id: 'ev-001',
    claim: 'PostgreSQL 16 logical replication supports bi-directional failover with pg_createsubscriber.',
    source_url: 'https://www.postgresql.org/docs/16/logical-replication.html',
    source_title: 'PostgreSQL Official Documentation: Chapter 31. Logical Replication',
    char_offset_start: 1420,
    char_offset_end: 1680,
    snippet: 'PostgreSQL 16 introduces pg_createsubscriber to convert a physical replica into a logical replica, enabling zero-downtime failover topologies.',
    support_status: 'supported',
    confidence_score: 0.98,
    contradictory_evidence: null,
    verified_at: '2026-11-22T08:30:00Z',
  },
  {
    id: 'ev-002',
    claim: 'Redis 7 ACL rules can restrict Redis Sentinel reconfiguration commands without master auth.',
    source_url: 'https://redis.io/docs/management/security/acl/',
    source_title: 'Redis Security: Access Control Lists (ACLs)',
    char_offset_start: 3105,
    char_offset_end: 3340,
    snippet: 'Sentinel commands require specific @admin category rules when user-level ACLs are applied to sentinel instances.',
    support_status: 'supported',
    confidence_score: 0.94,
    contradictory_evidence: null,
    verified_at: '2026-11-22T09:15:00Z',
  },
  {
    id: 'ev-003',
    claim: 'FastAPI dependency injection executes async generators in the same event loop context as route handlers.',
    source_url: 'https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/',
    source_title: 'FastAPI: Dependencies with yield and contextvars',
    char_offset_start: 890,
    char_offset_end: 1140,
    snippet: 'The code prior to yield runs before the request, and code after yield runs after the response has been sent, within the matching async context.',
    support_status: 'supported',
    confidence_score: 0.99,
    contradictory_evidence: null,
    verified_at: '2026-11-22T10:00:00Z',
  },
  {
    id: 'ev-004',
    claim: 'SQLite WAL mode allows multiple concurrent write transactions across multiple operating system processes.',
    source_url: 'https://www.sqlite.org/wal.html',
    source_title: 'SQLite Documentation: Write-Ahead Logging',
    char_offset_start: 510,
    char_offset_end: 780,
    snippet: 'WAL mode permits multiple simultaneous readers, but only one write transaction may occur at any one time.',
    support_status: 'contradicted',
    confidence_score: 0.97,
    contradictory_evidence: 'WAL allows concurrent readers with a single writer; concurrent multi-process writes result in SQLITE_BUSY unless external serialization is implemented.',
    verified_at: '2026-11-22T10:45:00Z',
  },
  {
    id: 'ev-005',
    claim: 'Tailwind CSS v4 fully supports legacy tailwind.config.js configurations without the Vite plugin.',
    source_url: 'https://tailwindcss.com/docs/v4-beta',
    source_title: 'Tailwind CSS v4 Migration Guide',
    char_offset_start: 112,
    char_offset_end: 380,
    snippet: 'Tailwind v4 is CSS-first and replaces tailwind.config.js with CSS theme variables and Vite/PostCSS bundler plugins.',
    support_status: 'disputed',
    confidence_score: 0.88,
    contradictory_evidence: 'Legacy JS configs require explicit @config directives in CSS and are deprecated in favor of CSS variables.',
    verified_at: '2026-11-22T11:20:00Z',
  },
];

export default function ResearchEvidence() {
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedItem, setSelectedItem] = useState<EvidenceItem | null>(MOCK_EVIDENCE[0]);

  const filteredEvidence = MOCK_EVIDENCE.filter((item) => {
    if (filterStatus !== 'all' && item.support_status !== filterStatus) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        item.claim.toLowerCase().includes(q) ||
        item.source_title.toLowerCase().includes(q) ||
        item.source_url.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const getStatusBadge = (status: EvidenceItem['support_status']) => {
    switch (status) {
      case 'supported':
        return <Badge variant="success">Supported</Badge>;
      case 'contradicted':
        return <Badge variant="danger">Contradicted</Badge>;
      case 'disputed':
        return <Badge variant="warning">Disputed</Badge>;
      default:
        return <Badge variant="neutral">Unverified</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-serif text-3xl font-semibold tracking-tight text-stone-900 dark:text-stone-100">
              Research & Evidence Graph
            </h1>
            <Badge variant="terracotta">Evidence Ledger</Badge>
          </div>
          <p className="mt-1 text-sm text-stone-600 dark:text-stone-400">
            Immutable research claims, exact character offset provenance, and adversarial contradiction analysis.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-300">
            <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span>Zero Hallucination Gate Active</span>
          </div>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900/50">
          <div className="text-xs text-stone-500 font-medium">Total Claims Evaluated</div>
          <div className="mt-1 text-2xl font-semibold text-stone-900 dark:text-stone-100">142</div>
          <div className="mt-1 text-xs text-stone-500">Across 10 project workspaces</div>
        </div>
        <div className="p-4 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900/50">
          <div className="text-xs text-stone-500 font-medium">Supported Claims</div>
          <div className="mt-1 text-2xl font-semibold text-emerald-600 dark:text-emerald-400">128</div>
          <div className="mt-1 text-xs text-emerald-600 dark:text-emerald-400 font-medium">90.1% confidence rate</div>
        </div>
        <div className="p-4 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900/50">
          <div className="text-xs text-stone-500 font-medium">Contradictions Caught</div>
          <div className="mt-1 text-2xl font-semibold text-rose-600 dark:text-rose-400">9</div>
          <div className="mt-1 text-xs text-stone-500">Auto-flagged before compilation</div>
        </div>
        <div className="p-4 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900/50">
          <div className="text-xs text-stone-500 font-medium">Avg Offset Precision</div>
          <div className="mt-1 text-2xl font-semibold text-stone-900 dark:text-stone-100">±14 chars</div>
          <div className="mt-1 text-xs text-stone-500">Exact source text anchoring</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between p-3 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900/50">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search claims, sources, URLs..."
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-stone-200 dark:border-stone-800 bg-transparent text-stone-900 dark:text-stone-100 focus:outline-none focus:ring-2 focus:ring-[#C85A32]"
          />
        </div>
        <div className="flex items-center gap-1.5 w-full sm:w-auto">
          <Filter className="w-3.5 h-3.5 text-stone-400" />
          <span className="text-xs text-stone-500">Status:</span>
          {['all', 'supported', 'contradicted', 'disputed'].map((status) => (
            <button
              key={status}
              onClick={() => setFilterStatus(status)}
              className={`px-2.5 py-1 text-xs rounded-md transition-colors capitalize ${
                filterStatus === status
                  ? 'bg-[#C85A32] text-white font-medium'
                  : 'bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-400 hover:text-stone-900'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid: Evidence List & Deep Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Claim Ledger */}
        <div className="lg:col-span-7 space-y-3">
          {filteredEvidence.map((item) => {
            const isSelected = selectedItem?.id === item.id;
            return (
              <div
                key={item.id}
                onClick={() => setSelectedItem(item)}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  isSelected
                    ? 'border-[#C85A32] bg-[#FBF9F5] dark:bg-stone-900 shadow-sm'
                    : 'border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900/50 hover:border-stone-300'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-medium text-stone-400">{item.id}</span>
                      {getStatusBadge(item.support_status)}
                      <span className="text-xs text-stone-500 font-mono">
                        {(item.confidence_score * 100).toFixed(0)}% confidence
                      </span>
                    </div>
                    <p className="text-sm font-medium text-stone-900 dark:text-stone-100 line-clamp-2">
                      {item.claim}
                    </p>
                  </div>
                  {item.support_status === 'supported' && (
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                  )}
                  {item.support_status === 'contradicted' && (
                    <XCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
                  )}
                  {item.support_status === 'disputed' && (
                    <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                  )}
                </div>

                <div className="mt-3 pt-3 border-t border-stone-100 dark:border-stone-800/60 flex items-center justify-between text-xs text-stone-500">
                  <span className="truncate max-w-[280px] font-mono text-[11px] text-stone-600 dark:text-stone-400">
                    {item.source_title}
                  </span>
                  <span>Char [{item.char_offset_start}:{item.char_offset_end}]</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right: Detailed Claim Inspector */}
        <div className="lg:col-span-5">
          {selectedItem ? (
            <div className="sticky top-6 p-5 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900 space-y-5">
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-stone-400">{selectedItem.id}</span>
                  {getStatusBadge(selectedItem.support_status)}
                </div>
                <h3 className="mt-2 text-base font-semibold text-stone-900 dark:text-stone-100">
                  {selectedItem.claim}
                </h3>
              </div>

              {/* Source Document Details */}
              <div className="p-3 rounded-lg bg-stone-50 dark:bg-stone-800/50 border border-stone-200 dark:border-stone-700/60 space-y-2">
                <div className="text-xs font-medium text-stone-500 uppercase tracking-wider">Source Reference</div>
                <div className="text-sm font-medium text-stone-800 dark:text-stone-200">
                  {selectedItem.source_title}
                </div>
                <a
                  href={selectedItem.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs text-[#C85A32] hover:underline break-all"
                >
                  <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                  <span>{selectedItem.source_url}</span>
                </a>
              </div>

              {/* Exact Text Snippet & Anchoring */}
              <div>
                <div className="flex items-center justify-between text-xs font-medium text-stone-500 mb-1.5">
                  <span>Exact Match Snippet</span>
                  <span className="font-mono text-[11px]">Offset: {selectedItem.char_offset_start}-{selectedItem.char_offset_end}</span>
                </div>
                <div className="p-3 rounded-lg border border-stone-200 dark:border-stone-800 bg-stone-50 dark:bg-stone-950 font-mono text-xs text-stone-800 dark:text-stone-300 leading-relaxed border-l-4 border-l-[#C85A32]">
                  "{selectedItem.snippet}"
                </div>
              </div>

              {/* Contradiction Analysis */}
              {selectedItem.contradictory_evidence && (
                <div className="p-3.5 rounded-lg border border-rose-200 dark:border-rose-900/50 bg-rose-50 dark:bg-rose-950/30 space-y-1.5">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-rose-800 dark:text-rose-300">
                    <AlertTriangle className="w-4 h-4 text-rose-600" />
                    <span>Contradictory Evidence Identified</span>
                  </div>
                  <p className="text-xs text-rose-700 dark:text-rose-400 leading-normal">
                    {selectedItem.contradictory_evidence}
                  </p>
                </div>
              )}

              {/* Verification Metadata */}
              <div className="pt-3 border-t border-stone-200 dark:border-stone-800 space-y-2 text-xs text-stone-500">
                <div className="flex justify-between">
                  <span>Confidence Metric:</span>
                  <span className="font-mono font-medium text-stone-800 dark:text-stone-200">
                    {(selectedItem.confidence_score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Verified Timestamp:</span>
                  <span className="font-mono text-stone-800 dark:text-stone-200">{selectedItem.verified_at}</span>
                </div>
                <div className="flex justify-between">
                  <span>Verification Policy:</span>
                  <span className="text-stone-800 dark:text-stone-200">Adversarial Double-Pass</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-12 text-center border border-dashed border-stone-200 dark:border-stone-800 rounded-xl text-stone-400">
              <Database className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Select any claim from the ledger to inspect evidence provenance.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
