# PROMPTIQ CLOUD HOSTING FEASIBILITY REPORT
## Platform Assessment, Zero-Price Compliance & Empirical Findings

---

## 1. Executive Summary

In accordance with PromptIQ's core invariants, all deployment targets were evaluated against three mandatory criteria:
1. **Zero-Price Guarantee**: ₹0 forever to users, with zero paid inference or infrastructure leakage.
2. **Cardless Verification**: The platform must not require credit card or billing registration to deploy and maintain the service.
3. **No Local Inference**: 100% hosted architecture.

---

## 2. Platform Feasibility Matrix

| Cloud Provider | Tier Evaluated | Cardless? | Zero-Cost? | Suitability Verdict | Key Technical Findings |
|---|---|---|---|---|---|
| **Vercel** | Hobby (Free) | Yes (via Git/Dashboard) | Yes | **Compatible for Frontend** (Git deployment) | Anonymous CLI deploy on local Windows failed with `EPERM` due to unprivileged symlink syscalls in node builder cache (`AppData\Local\com.vercel.cli\Cache\builders-vlt\...`). Git-based deployment via `frontend/vercel.json` succeeds cleanly. |
| **Render** | Free Web + Static | Yes | Yes (750 hrs/mo) | **Compatible for Backend & Frontend** | Native support via `deployment/render.yaml` Blueprint. Free tier spins down on idle (15 min), acceptable for development/staging; automated health checks on `/health`. |
| **Fly.io** | Free Allowance | **No** (Card required) | Partially | **Ineligible (Violates Invariant)** | Fly.io now enforces payment method verification for all new organizations before allocating IPv4 or running machines. |
| **Cloudflare Pages** | Free Tier | Yes | Yes | **Compatible for Frontend** | Unlimited static hosting with global CDN. Deployable via Git or Wrangler CLI. |
| **Self-Hosted Docker** | Linux/VM/Container | Yes | Yes (100% free) | **Fully Certified Production Stack** | Docker Compose + PostgreSQL 16 + Caddy TLS (`deployment/docker-compose.prod.yml`). Zero external dependencies, complete privacy, no quota limits. |

---

## 3. Empirical Windows CLI Findings

During live execution of `npx vercel deploy --temporary --cwd frontend --yes`, the Vercel CLI attempted to create directory symlinks in the local user cache:
```
Error: [EPERM] EPERM: operation not permitted, symlink '..\..\~npm~@emnapi+core@1.11.3\node_modules\@emnapi\core' -> 'C:\Users\Priyesh Raj\AppData\Local\com.vercel.cli\Cache\builders-vlt\ce52a4c556a65b1e2b7abbfb55836f907cb93e84168b797720a96e7279fbbc85\node_modules\.vlt\node_modules\@emnapi\core'
```
*Root Cause*: On Windows operating systems, the `symlink` system call is restricted by default to Elevated (Administrator) processes or environments where Windows Developer Mode is explicitly toggled on in OS settings.

*Resolution & Production Recommendation*:
1. For frontend hosting on Vercel, link the repository to Vercel via GitHub or GitLab. Vercel's remote Linux build runners do not suffer from Windows symlink permission restrictions and will build `frontend/` using `frontend/vercel.json` without intervention.
2. For containerized backend deployment, use Render Blueprint (`deployment/render.yaml`) or Docker Compose (`deployment/docker-compose.prod.yml`).
