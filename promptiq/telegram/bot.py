"""Telegram Bot companion client interfacing with PromptIQ backend."""

from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from promptiq.core.config import settings
from promptiq.core.exceptions import AuthenticationError
from promptiq.core.logging import logger
from promptiq.core.security import verify_telegram_link_token
from promptiq.critic.autopsy import PromptAutopsyEngine
from promptiq.discovery.adaptive import AdaptiveDiscoveryEngine
from promptiq.research.engine import research_engine
from promptiq.schemas.critic import AutopsyRequest
from promptiq.schemas.discovery import InitialIntakeRequest
from promptiq.schemas.project import ProjectCreate
from promptiq.schemas.research import ResearchRequest
from promptiq.services.auth_service import AuthService
from promptiq.services.project_service import ProjectService


class TelegramBotClient:
    """Conversational Telegram client connected to the shared PromptIQ domain services."""

    def __init__(self, token: str | None = None):
        self.token = token or settings.TELEGRAM_BOT_TOKEN
        self.api_base = f"https://api.telegram.org/bot{self.token}"

    async def send_message(self, chat_id: str | int, text: str, reply_markup: dict[str, Any] | None = None) -> dict[str, Any]:
        """Sends a text message with optional inline keyboard."""
        if not self.token:
            logger.info(f"[Mock Telegram Dispatch] To {chat_id}: {text[:100]}...")
            return {"ok": True, "mock": True, "chat_id": chat_id, "text": text}

        url = f"{self.api_base}/sendMessage"
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        if reply_markup:
            payload["reply_markup"] = reply_markup

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"Telegram dispatch error: {e}")
                return {"ok": False, "error": str(e)}

    async def handle_update(self, db: AsyncSession, update: dict[str, Any]) -> dict[str, Any]:
        """Processes an incoming Telegram webhook or polled update."""
        message = update.get("message") or update.get("callback_query", {}).get("message")
        if not message:
            return {"status": "ignored"}

        chat_id = str(message["chat"]["id"])
        text = (message.get("text") or update.get("callback_query", {}).get("data", "")).strip()

        # Resolve linked user
        user = await AuthService.get_user_by_telegram_id(db, chat_id)

        # 1. Handle Onboarding & Account Linking (/start [token])
        if text.startswith("/start"):
            parts = text.split()
            if len(parts) > 1:
                token_arg = parts[1]
                try:
                    user_id = verify_telegram_link_token(token_arg)
                    user = await AuthService.link_telegram_account(db, user_id, chat_id)
                    reply = (
                        f"✅ Account successfully linked!\n\n"
                        f"Welcome, *{user.full_name}*! Your Telegram companion is now synchronized with your PromptIQ workspace.\n"
                        f"All projects, discovery interviews, and generated prompt packages are accessible across surfaces."
                    )
                except AuthenticationError as e:
                    reply = f"❌ Linking failed: {e.message}. Please generate a new link token from your workspace settings."
            else:
                if user:
                    reply = (
                        f"👋 Welcome back, *{user.full_name}*!\n\n"
                        f"PromptIQ is ready. Select an action:\n"
                        f"• `/build <goal>` — Start discovery for a new software project\n"
                        f"• `/generate <task>` — Quick prompt generation\n"
                        f"• `/review <text>` — Run adversarial prompt autopsy\n"
                        f"• `/research <topic>` — Perform evidence-based research\n"
                        f"• `/projects` — List your linked workspace projects\n"
                    )
                else:
                    reply = (
                        "🚀 *Welcome to PromptIQ!*\n\n"
                        "Universal Prompt Intelligence, Project Engineering, and Cross-Agent Continuity.\n\n"
                        "⚠️ *Account Unlinked*: You are currently using guest mode. To link your account and share memory with your Web/CLI workspace, log into PromptIQ and visit Settings -> Link Telegram."
                    )

            menu = {
                "inline_keyboard": [
                    [{"text": "⚡ Generate Prompt", "callback_data": "/generate"}, {"text": "🔬 Autopsy Review", "callback_data": "/review"}],
                    [{"text": "🛠️ Build Project", "callback_data": "/build"}, {"text": "📚 My Projects", "callback_data": "/projects"}],
                ]
            }
            await self.send_message(chat_id, reply, reply_markup=menu)
            return {"status": "processed", "command": "/start"}

        # Require linked user for project operations
        if not user:
            # Fallback guest user for standalone Telegram interactions if unlinked
            user_stmt_anon = await AuthService.get_user_by_telegram_id(db, "guest")
            if not user_stmt_anon:
                # Create a local guest user
                from promptiq.schemas.auth import UserCreate
                user, _ = await AuthService.register_user(
                    db, UserCreate(email=f"tg_{chat_id}@promptiq.local", password="guest_password_12345", full_name="Telegram User")
                )
                user = await AuthService.link_telegram_account(db, user.id, chat_id)

        # 2. Handle /projects
        if text.startswith("/projects"):
            projects = await ProjectService.list_projects(db, user.id)
            if not projects:
                msg = "📂 You have no projects yet. Use `/build <name>` to start your first project!"
            else:
                lines = [f"• *{p.name}* (v{p.current_constitution_version}) — ID: `{p.id}`" for p in projects[:10]]
                msg = "📂 *Your PromptIQ Projects:*\n\n" + "\n".join(lines)
            await self.send_message(chat_id, msg)
            return {"status": "processed", "command": "/projects"}

        # 3. Handle /review or /autopsy
        if text.startswith("/review") or text.startswith("/autopsy"):
            prompt_content = text.replace("/review", "").replace("/autopsy", "").strip()
            if not prompt_content:
                await self.send_message(chat_id, "ℹ️ Please provide the prompt to review: `/review <paste prompt here>`")
                return {"status": "awaiting_input"}

            autopsy_req = AutopsyRequest(prompt_text=prompt_content, target_environment="google-antigravity")
            res = await PromptAutopsyEngine.diagnose_prompt(autopsy_req, user_id=user.id)

            findings_text = "\n".join([f"• *[{f.severity.upper()}]* {f.finding}" for f in res.findings[:4]])
            msg = (
                f"🔬 *Prompt Autopsy Diagnostic*\n\n"
                f"*Verdict*: `{res.verdict.upper()}`\n"
                f"*Summary*: {res.summary}\n\n"
                f"*Key Findings*:\n{findings_text or 'No material defects found.'}\n\n"
                f"*Quality Scores*:\n"
                f"• Static Quality: {res.quality_scores['static_quality']}%\n"
                f"• Security: {res.quality_scores['security_robustness']}%\n"
                f"• Compatibility: {res.quality_scores['target_compatibility']}%\n"
            )
            await self.send_message(chat_id, msg)
            return {"status": "processed", "command": "/review"}

        # 4. Handle /research
        if text.startswith("/research"):
            query = text.replace("/research", "").strip()
            if not query:
                await self.send_message(chat_id, "ℹ️ Please specify a topic: `/research <topic or question>`")
                return {"status": "awaiting_input"}

            # Get user's active project or create a research project
            projects = await ProjectService.list_projects(db, user.id)
            project_id = projects[0].id if projects else (await ProjectService.create_project(db, user.id, ProjectCreate(name="Research Project"))).id

            res_research = await research_engine.execute_research(
                db, project_id, user.id, ResearchRequest(query=query, mode="quick")
            )

            claims_text = "\n".join([f"• {c.claim_text} ([Source]({c.source_url}))" for c in res_research.claims[:3]])
            msg = (
                f"🔎 *Research Evidence Ledger*\n\n"
                f"*Topic*: {query}\n"
                f"*Status*: {res_research.status.upper()}\n\n"
                f"*Verified Claims*:\n{claims_text or 'No definitive claims verified.'}\n\n"
                f"*Takeaway*: {res_research.summary.get('synthesis', 'Completed')}"
            )
            await self.send_message(chat_id, msg)
            return {"status": "processed", "command": "/research"}

        # 5. Handle /build or /generate (Project Creation & Discovery)
        if text.startswith("/build") or text.startswith("/generate"):
            goal_text = text.replace("/build", "").replace("/generate", "").strip()
            if not goal_text:
                goal_text = "New PromptIQ Project"

            # Create project
            project = await ProjectService.create_project(
                db, user.id, ProjectCreate(name=goal_text[:30], description=goal_text), surface="telegram"
            )

            # Start adaptive discovery
            intake = InitialIntakeRequest(
                goal=goal_text,
                deliverable="complete_package",
                target="google-antigravity",
                depth="guided",
            )
            discovery_resp = await AdaptiveDiscoveryEngine.start_session(db, project.id, user.id, intake)

            q_text = "\n".join([f"👉 {q.question}" for q in discovery_resp.next_questions])
            msg = (
                f"🚀 *Project Initialized: {project.name}*\n"
                f"ID: `{project.id}`\n\n"
                f"To engineer your target instructions, please answer:\n\n{q_text}\n\n"
                f"Reply directly to this message with your details."
            )
            await self.send_message(chat_id, msg)
            return {"status": "processed", "command": "/build"}

        # 6. Default conversational response
        await self.send_message(
            chat_id,
            "💡 PromptIQ understood your message. Use `/projects`, `/build <goal>`, `/review <prompt>`, or `/help`.",
        )
        return {"status": "processed", "command": "default"}


telegram_bot = TelegramBotClient()
