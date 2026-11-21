# Groq Terms & Public Deployment Status (Phase 3.4.2)
## Legal Analysis of "Not for Consumer Use" vs. Customer Application End Users

**Audit Date**: 2026-11-22  
**Target Provider**: Groq, Inc.  
**Governing Documents**: Groq Services Agreement, AI Model Terms, Privacy Policy  
**Public Deployment Status**: `REVIEW_REQUIRED` (HELD / UNAPPROVED for Unrestricted Consumer Production)  
**Internal Developer Testing Status**: `PERMITTED` (Internal Synthetic Developer Testing Only)  

---

## 1. The Legal Tension in the Groq Services Agreement

The Groq Services Agreement contains two clauses that sit in direct tension:

1. **The Consumer Restriction Clause**:
   > *"Cloud Services and the AI Model Services under this Agreement are not for consumer use."*
2. **The Customer Application & End User Authorization**:
   > *"Customer may integrate the Cloud Services and AI Model Services into Customer Applications and make them available to authorized End Users."*

---

## 2. Rigorous Analysis Across Use Contexts

### Context A: Internal Operator Development & Testing
- **User**: The PromptIQ operator and software engineering team.
- **Activity**: Developing prompts, testing API schemas, running synthetic benchmarks.
- **Legal Characterization**: B2B developer activity.
- **Verdict**: **`PERMITTED`**. The operator is a developer building a software application.

### Context B: Public Deployment to General End Users
- **Target Audience**: Software developers, founders, researchers, students, and general users.
- **The Consumer Dilemma**: If PromptIQ offers free, open public access on the internet, retail consumers, hobbyists, high school students, and minors will use the platform.
- **Why a "Developer Attestation" Click-Wrap Does NOT Solve the Issue**:
  - Simply asking users to click a checkbox stating "I am a professional developer" is a legally fragile fiction if the service is publicly accessible without corporate domain verification or enterprise contracting.
  - Minors cannot legally waive consumer protection rights through a click-wrap checkbox.
- **Verdict**: **`REVIEW_REQUIRED` (HELD)**. Unrestricted public release with Groq as the underlying inference provider cannot be approved based on speculative legal interpretation.

---

## 3. Mandatory Provider Clarification Protocol

To graduate Groq from `REVIEW_REQUIRED` to `VERIFIED_ELIGIBLE` for public production:
1. **Direct Communication**: Operator must contact Groq Sales/Legal (`support@groq.com` / `legal@groq.com`) requesting written clarification:
   > *"Does integrating GroqCloud Free/Developer APIs into a free, publicly accessible prompt engineering educational tool accessible by students and independent developers violate the 'not for consumer use' clause of the Groq Services Agreement?"*
2. **Alternative Deployment Path**: If Groq confirms that public educational tools constitute consumer distribution, PromptIQ must:
   - Restrict Groq routes exclusively to verified business/developer accounts (e.g., GitHub/Google Workspace domain sign-in).
   - Route general public/student users through providers whose terms expressly authorize consumer and minor educational access.

---

## 4. Phase 3.4.2 Invariant

For all Phase 3.4.2 activities:
- All prompts are strictly synthetic, non-sensitive, and free of proprietary or personal data.
- No public production deployment is initiated.
