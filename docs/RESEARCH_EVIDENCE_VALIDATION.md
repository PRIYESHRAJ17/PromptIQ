# PromptIQ — Research Evidence Validation and Retrieval Architecture

**Version**: 3.0.0  
**Updated**: 2026-11-22  
**Module Reference**: `promptiq/research/`, `promptiq/schemas/research.py`, `tests/test_research_security.py`

---

## 1. Executive Summary

PromptIQ's Research Engine transforms external domain knowledge into an immutable, verifiable **Evidence Ledger**. The engine strictly separates:
1. **Live Web Retrieval**: Genuine outbound HTTP requests to public search endpoints with kernel-level socket pinning and strict SSRF defenses.
2. **Simulated / Grounded Fallback**: Deterministic mock research used during CI test suites or airgapped runs, honestly marked with `is_simulated: true` and surfaced as audit warnings.

Under no circumstances does PromptIQ fabricate citations, hallucinate URLs, or masquerade simulated retrieval as live web discovery.

---

## 2. Research Architecture & Invariants

```
+-------------------------------------------------------------------------------+
|                             RESEARCH ENGINE                                   |
+-------------------------------------------------------------------------------+
                                        |
                 +----------------------+----------------------+
                 |                                             |
                 v                                             v
     [Live Search Mode]                              [Simulated / Test Mode]
  (Requires Internet & DNS)                         (Airgapped / Automated Tests)
                 |                                             |
    +------------+------------+                                v
    |                         |                     [Deterministic Synthetic]
    v                         v                     - Canonical domain stubs
[DNS Pre-Resolution]      [SSRF Defense]            - Grounded text snippets
- socket.getaddrinfo      - Filter private IPs      - Tagged: is_simulated=True
    |                     - Block 169.254.169.254              |
    v                     - Block IPv6 local                   v
[Pinned Socket HTTPS]                               [COMPLETED_WITH_WARNINGS]
- Fixed target IP                                   - Warnings emitted in trace
- Anti-DNS rebinding                                - Zero false live claims
    |
    v
[Evidence Extraction]
- Title, snippet, pub date
- Canonical publisher
- SHA-256 content hash
                 |
                 +----------------------+
                                        |
                                        v
                           +--------------------------+
                           |  EVIDENCE LEDGER SCHEMA  |
                           | - URL & Canonical Domain |
                           | - Support Status         |
                           | - Claim Verification     |
                           +--------------------------+
```

---

## 3. SSRF Defense & Socket-Pinned Retrieval

Outbound web requests pose severe Server-Side Request Forgery (SSRF) and DNS rebinding risks. PromptIQ's `LiveSearchConnector` implements strict multi-layer defense:

### Layer 1: DNS Resolution & Private Subnet Rejection
Before connecting, the hostname is resolved to an IPv4/IPv6 address. The target IP is evaluated against all reserved and non-routable CIDR blocks:
- `127.0.0.0/8` (Loopback)
- `10.0.0.0/8` (Private Class A)
- `172.16.0.0/12` (Private Class B)
- `192.168.0.0/16` (Private Class C)
- `169.254.0.0/16` (Link-Local & Cloud Metadata `169.254.169.254`)
- `0.0.0.0/8`, `100.64.0.0/10`, `198.18.0.0/15`
- `::1` (IPv6 Loopback), `fc00::/7` (Unique Local), `fe80::/10` (Link-Local)

Any matching IP triggers immediate `SSRFProtectionError` and aborts the connection.

### Layer 2: Pinned Socket Connection (Anti-DNS Rebinding)
Standard HTTP client libraries re-resolve DNS during TCP socket handshakes, opening a Time-of-Check to Time-of-Use (TOCTOU) vulnerability where a public hostname rebinds to `127.0.0.1` after validation.

PromptIQ defeats DNS rebinding by:
1. Resolving the IP once and validating it.
2. Monkey-patching / pinning the socket address in the transport adapter (`_pinned_getaddrinfo`), forcing the TCP handshake to connect exclusively to the pre-validated IP address.
3. Preserving the original hostname in the HTTP `Host` header and TLS SNI extension for certificate validation.

### Empirical Verification
The test suite `tests/test_research_security.py` tests and validates **31 malicious SSRF vectors**, including:
- Direct IP notation (`127.0.0.1`, `10.0.0.1`, `169.254.169.254`)
- Hexadecimal IP notation (`0x7f000001`)
- Octal IP notation (`0177.0.0.1`)
- Decimal integer IP (`2130706433`)
- DNS rebinding domains
- Cloud metadata service endpoints (AWS, GCP, Azure, DigitalOcean)

All 31 vectors are blocked with 100% reliability.

---

## 4. Evidence Ledger Schema & Verification

Every retrieved research artifact is stored in the `EvidenceLedger` with cryptographic provenance:

```python
class EvidenceLedgerEntry(BaseModel):
    id: UUID
    source_url: HttpUrl
    publisher: str
    published_date: Optional[datetime]
    title: str
    snippet: str
    content_sha256: str
    domain_authority: float
    support_status: Literal["SUPPORTED", "CONTRADICTED", "INCONCLUSIVE"]
    confidence_score: float
    is_simulated: bool
```

### Claim-to-Evidence Grounding
When PromptIQ compiles domain-specific instructions or architectural proposals:
1. Every factual assertion is extracted into an atomic claim.
2. The claim is matched against the `EvidenceLedger` using string n-gram overlap and semantic containment.
3. Claims supported by evidence receive `SUPPORTED` status.
4. Claims contradicted by authoritative sources are flagged as `CONTRADICTED` and surfaced in Prompt Autopsy.
5. Unsupported claims without evidence are marked `INCONCLUSIVE` and trigger discovery clarification questions.

---

## 5. Simulated Research and Acceptance State Machine Integrity

In Scenario 2 of the acceptance suite (`scenario_2_research_intelligence`):
- Because the automated test runs without external internet dependencies, the connector executes in simulated mode.
- The state machine marks the criterion as satisfied (`SC2-AC-1: Research conducted with structured evidence citations`).
- Because `is_simulated` is `True`, the state machine derives an explicit warning record:
  - `category: "simulated_research"`
  - `message: "Evidence ledger contains simulated research citations; live internet search was unverified"`
- The scenario transitions to `COMPLETED_WITH_WARNINGS`.
- Under negative test 2 (`test_simulated_research_requires_warning_state`), attempting to transition Scenario 2 to `SUCCESS_FULLY_VERIFIED` raises `StateTransitionError: COMPLETED_WITH_WARNINGS required when simulated research or advisory findings exist`.
