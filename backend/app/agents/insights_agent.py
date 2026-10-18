"""
HYPERREALM Insights Agent.
Specialist responsible for architecture proposal evaluation, error log investigation,
historical incident resolution lookup, and multimodal brand compliance analysis.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from ..config import get_settings
from ..dependencies import get_guide_repo, get_incident_repo
from ..models import (
    BrandComplianceReport,
    ComplianceStatus,
    DocumentScope,
    Incident,
    UserProfile,
)
from ..services.retrieval import EnterpriseRetrievalService
from ..services.vision import BrandComplianceService

logger = logging.getLogger("hyperrealm.agents.insights")


class InsightsAgent:
    name = "insights"
    description = (
        "Evaluates technical proposals, investigates error logs against historical incidents, "
        "and performs multimodal brand compliance audits."
    )

    def __init__(
        self,
        retrieval_service: Optional[EnterpriseRetrievalService] = None,
        vision_service: Optional[BrandComplianceService] = None,
    ):
        self.retrieval = retrieval_service or EnterpriseRetrievalService()
        self.vision = vision_service or BrandComplianceService()
        self.incident_repo = get_incident_repo()
        self.guide_repo = get_guide_repo()

    async def execute(
        self,
        prompt: str,
        user: UserProfile,
        attachments: Optional[list[dict[str, Any]]] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Route request according to task type:
        1. If image attachment provided or brand compliance audit requested -> Brand Compliance Audit.
        2. If error log / incident / troubleshooting mentioned -> Error Log & Incident Investigation.
        3. Otherwise -> Technical Proposal & Architecture Evaluation against published guidelines.
        """
        prompt_lower = prompt.lower()

        # 1. Image / Brand Compliance Audit
        if (attachments and any(a.get("type", "").startswith("image") for a in attachments)) or \
           ("brand" in prompt_lower and ("audit" in prompt_lower or "complian" in prompt_lower or "design" in prompt_lower)):
            image_bytes = None
            image_url = None
            filename = "audit_asset.png"

            if attachments:
                img_att = next((a for a in attachments if a.get("type", "").startswith("image")), None)
                if img_att:
                    image_url = img_att.get("url")
                    filename = img_att.get("name", filename)

            report = await self.vision.audit_image(
                image_bytes=image_bytes,
                image_url=image_url,
                image_filename=filename,
                user=user,
            )

            response_text = (
                f"**Brand Compliance Evaluation Report (Guideline: {report.guideline_reference})**\n\n"
                f"**Status:** {report.status.value.replace('_', ' ').title()}\n"
                f"**Summary:** {report.summary}\n\n"
                f"**Key Checks:**\n" +
                "\n".join(f"- **{c.get('requirement')}**: {c.get('result')} ({c.get('observed_evidence')})" for c in report.checks[:3]) +
                f"\n\n**Recommendations:**\n" +
                "\n".join(f"- {r}" for r in report.recommendations) +
                "\n\n*Note: This evaluation is an automated assessment and does not constitute formal brand sign-off.*"
            )

            return {
                "agent_id": self.name,
                "response": response_text,
                "compliance_report": report,
                "citations": [{
                    "source_type": "official_guideline",
                    "title": report.guideline_reference,
                    "version": report.guideline_version,
                }],
            }

        # 2. Error log investigation & Historical Incidents
        if any(w in prompt_lower for w in ("error", "exception", "incident", "stack trace", "fail", "timeout", "bug")):
            return await self._investigate_error(prompt, user)

        # 3. Technical Proposal Evaluation against guidelines
        return await self._evaluate_technical_proposal(prompt, user)

    async def _investigate_error(self, prompt: str, user: UserProfile) -> dict[str, Any]:
        """Search historical incident records & runbooks for matching resolutions."""
        settings = get_settings()
        results, _ = await self.retrieval.search(
            query=prompt,
            user=user,
            scopes=[DocumentScope.HISTORICAL],
            top_k=3,
        )

        match = results[0] if results else None
        citations = match.citations if match else []
        response = None
        is_sim = settings.is_demo

        if not settings.is_demo:
            try:
                from .adk_runtime import call_gemini_model
                sys_inst = (
                    f"You are the Hyperrealm Insights & Troubleshooting Specialist serving engineer {user.name}. "
                    "Analyze runtime errors and stack traces. Ground your hypothesis and troubleshooting steps "
                    "in the provided historical incidents and runbooks."
                )
                incident_ctx = f"Historical Incident Context:\nTitle: {match.title}\nResolution: {match.snippet}" if match else "No exact historical incident matched in runbook."
                live_res = await call_gemini_model(prompt=live_prompt, system_instruction=sys_inst)
                if live_res:
                    response = f"**Incident Investigation & Analysis**\n\n" + live_res
                    is_sim = False
            except Exception as exc:
                logger.warning("Gemini error investigation failed (%s), using local response", exc)

        if not response:
            if match:
                response = (
                    f"**Historical Incident Investigation**\n\n"
                    f"I identified a related historical incident: **{match.title}**\n\n"
                    f"**Historical Resolution:**\n> {match.snippet}\n\n"
                    f"**Evidence-based Troubleshooting Steps:**\n"
                    f"1. Check underlying connection pool and token cache TTL as applied in previous incident resolution.\n"
                    f"2. Validate telemetry metrics against runbook threshold SLAs.\n"
                    f"3. If recurrence persists, escalate to the assigned on-call team."
                )
            else:
                response = (
                    f"**Troubleshooting Hypothesis (No Direct Historical Match Found)**\n\n"
                    f"No prior incident perfectly matches this error pattern in the historical records.\n\n"
                    f"**Hypothesis:**\n"
                    f"- The failure likely originates from network timeout, token expiration, or concurrency limits.\n"
                    f"- Review active service logs for HTTP status code 401/429/504.\n"
                    f"- Verify that circuit-breaker and retry configurations align with HYPERREALM Engineering Guidelines."
                )

        return {
            "agent_id": self.name,
            "response": response,
            "citations": citations,
            "is_simulated": is_sim,
        }

    async def _evaluate_technical_proposal(self, prompt: str, user: UserProfile) -> dict[str, Any]:
        """Compare technical proposal against published guidelines and architecture standards."""
        settings = get_settings()
        guides, _ = await self.guide_repo.list(skip=0, limit=10, status="published")
        citations = []
        guideline_summaries = []

        for g in guides[:2]:
            citations.append({
                "source_type": "official_guideline",
                "guideline_id": g.id,
                "title": g.title,
                "version": g.version,
            })
            guideline_summaries.append(f"• **{g.title} (v{g.version})**: {g.changelog or g.category}")

        outcome = "Recommended with Conditions"
        if "bypass" in prompt.lower() or "plain text" in prompt.lower() or "hardcode" in prompt.lower():
            outcome = "Not Recommended"
        elif "compliant" in prompt.lower() or "standard" in prompt.lower():
            outcome = "Recommended"

        response = None
        is_sim = settings.is_demo

        if not settings.is_demo:
            try:
                from .adk_runtime import call_gemini_model
                sys_inst = (
                    f"You are the Hyperrealm Architecture & Quality Gate Evaluator serving {user.name}. "
                    "Evaluate technical proposals against published organizational guidelines. Cite standards."
                )
                eval_prompt = (
                    f"Technical Proposal:\n{prompt}\n\n"
                    f"Authoritative Guidelines:\n" + "\n".join(guideline_summaries) + "\n\n"
                    f"Evaluate this architecture proposal for security, resilience, zero-trust compliance, and quality gates."
                )
                response = await call_gemini_model(prompt=eval_prompt, system_instruction=sys_inst)
                is_sim = False
            except Exception as exc:
                logger.warning("Gemini proposal evaluation failed (%s), using local response", exc)

        if not response:
            response = (
                f"**Technical Proposal Evaluation**\n\n"
                f"**Outcome:** `{outcome}`\n\n"
                f"**Evaluation against Published Standards:**\n"
                f"I reviewed your proposal against company architecture and security guidelines:\n" +
                "\n".join(guideline_summaries) + "\n\n"
                f"**Findings & Conditions:**\n"
                f"- **Security & Auth:** Ensure all authorization follows OAuth 2.0 with short-lived tokens and token rotation.\n"
                f"- **Resilience & SLA:** Introduce fallback circuit-breakers for downstream integration dependencies.\n"
                f"- **Telemetry:** Metrics and structured audit logs must emit to OpenTelemetry collectors.\n\n"
                f"*Disclaimer: This evaluation is an advisory analysis and does not replace final technical lead approval.*"
            )

        return {
            "agent_id": self.name,
            "response": response,
            "citations": citations,
            "outcome": outcome,
            "is_simulated": is_sim,
        }
