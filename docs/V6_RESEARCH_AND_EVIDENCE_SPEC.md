# PROMPTIQ V6 — RESEARCH AND EVIDENCE GRAPH SPECIFICATION

## Executive Overview

PromptIQ V6 replaces naive text scraping with an evidence graph architecture. Every external claim ingested into the platform is verified, sanitized against prompt-injection attacks, cataloged with exact character-offset citations, assessed for contradiction, and assigned an authoritative reliability tier.

---

## 1. Evidence Graph Architecture

**Source**: `promptiq/research/evidence_graph.py` (`EvidenceGraphBuilder`, `SourceReliabilityTier`, `EvidenceNode`, `CitationOffset`)

### Core Model
```python
class EvidenceNode(BaseModel):
    node_id: str
    url: str
    title: str
    source_reliability: SourceReliabilityTier
    raw_content_hash: str  # SHA-256 of downloaded body
    extracted_claims: list[CalibratedClaim]
    citations: list[CitationOffset]
    contradiction_warnings: list[str]
    sanitized: bool = True
```

### Source Reliability Tiers
1. `TIER_1_PRIMARY`: Official API documentation, peer-reviewed standards (IETF, W3C), vendor specifications.
2. `TIER_2_SECONDARY`: Verified technical blogs, engineering benchmarks, known knowledge repositories.
3. `TIER_3_COMMUNITY`: Public forums, discussion threads, community posts. Subject to strict scrutiny.
4. `TIER_4_UNTRUSTED`: Scraped web search snippets, user-supplied URLs without reputation history. Quarantine by default.

---

## 2. Character-Offset Citation Extraction

To eliminate hallucinated quotes, PromptIQ records exact text bounds within the source document:
```python
class CitationOffset(BaseModel):
    citation_id: str
    claim_id: str
    source_url: str
    exact_quote: str
    start_offset: int
    end_offset: int
    context_snippet: str
```
Before any citation is presented in an evidence ledger or compiled prompt, `EvidenceGraphBuilder` verifies:
$$\text{source\_text}[\text{start\_offset} : \text{end\_offset}] \equiv \text{exact\_quote}$$
If the text does not match character-for-character, the citation is rejected with an offset mismatch error.

---

## 3. Contradiction Detection

`EvidenceGraphBuilder.detect_contradictions(claims)` compares extracted claims across sources to identify factual divergence:
- Contradictory numeric claims (e.g., token limits, release dates, rate limits).
- Opposing statements (e.g., "supports async execution" vs "does not support async execution").
- Incompatibilities between constraints (e.g., "zero-price constraint" vs "requires OpenAI API key").

When contradictions are detected:
- The claims are flagged with `EpistemicStatus.CONTRADICTORY_CLAIM`.
- The claim from the higher `SourceReliabilityTier` takes precedence.
- If tiers are identical, a clarifying question is escalated to discovery.

---

## 4. Untrusted Content Sanitization & Prompt-Injection Defense

**Source**: `promptiq/research/evidence_graph.py` (`sanitize_untrusted_content`)

External web pages frequently contain accidental or adversarial instructions designed to hijack LLM reasoning. PromptIQ applies deterministic sanitization prior to ingestion:

1. **System Prompt Leakage Neutralization**:
   - Strips sequences like `Ignore previous instructions and ...`, `System Override:`, `You are now in developer mode`.
2. **Hidden Markdown & HTML Injection**:
   - Strips zero-width unicode characters, hidden HTML comments (`<!-- ... -->`), and obfuscated script tags.
3. **Quarantine Tagging**:
   - Ingested external text is strictly wrapped in boundary delimiters:
     `<untrusted_external_evidence source="url" hash="sha256">...</untrusted_external_evidence>`
   - Prompt compilers instruct models to treat content within these tags as data, never as executable instructions.

---

## 5. Security & SSRF Protection

PromptIQ's research engine blocks 31/31 known Server-Side Request Forgery (SSRF) attack vectors:
- Loopback addresses (`127.0.0.1`, `localhost`, `::1`).
- RFC 1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`).
- Cloud metadata services (`169.254.169.254`, `metadata.google.internal`).
- Hex/Octal/Dotted-integer IP obfuscation (`0x7f000001`, `2130706433`).
- Non-HTTP/HTTPS protocols (`file://`, `gopher://`, `dict://`, `ftp://`).
