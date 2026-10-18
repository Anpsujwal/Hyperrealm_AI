"""
HYPERREALM Document AI Integration Service.
Provides Document AI Layout Parser integration when configured and enabled.
Extracts document layout, hierarchy, text blocks, and structured tables.
Falls back safely to local extraction when Document AI is disabled, unconfigured,
or when cloud permissions are unavailable, reporting explicit diagnostic status.
"""
from __future__ import annotations

import base64
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from ..config import get_settings

logger = logging.getLogger("hyperrealm.document_ai")


class DocumentAIResult(BaseModel):
    is_live: bool = False
    status: str = "unavailable"
    text: str = ""
    tables: List[Dict[str, Any]] = []
    blocks: List[Dict[str, Any]] = []
    page_count: int = 0
    error_message: Optional[str] = None


class DocumentAIService:
    def __init__(self):
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(
            self.settings.DOCUMENT_AI_ENABLED
            and self.settings.DOCUMENT_AI_PROCESSOR_ID
            and self.settings.GOOGLE_CLOUD_PROJECT
        )

    def _get_credentials(self):
        import os
        import google.auth
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request

        creds_file = self.settings.GOOGLE_APPLICATION_CREDENTIALS
        if creds_file and os.path.isfile(creds_file):
            credentials = service_account.Credentials.from_service_account_file(
                creds_file,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
        else:
            credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        credentials.refresh(Request())
        return credentials

    def check_status(self) -> Dict[str, Any]:
        """Diagnostic check of Document AI integration."""
        if not self.settings.DOCUMENT_AI_ENABLED:
            return {
                "status": "disabled",
                "message": "DOCUMENT_AI_ENABLED is false",
                "processor_id": self.settings.DOCUMENT_AI_PROCESSOR_ID,
                "location": self.settings.DOCUMENT_AI_LOCATION,
            }
        if not self.settings.DOCUMENT_AI_PROCESSOR_ID:
            return {
                "status": "unconfigured",
                "message": "DOCUMENT_AI_PROCESSOR_ID is not configured",
                "location": self.settings.DOCUMENT_AI_LOCATION,
            }

        # Check API connectivity
        try:
            import requests

            credentials = self._get_credentials()

            loc = self.settings.DOCUMENT_AI_LOCATION or "eu"
            proj = self.settings.GOOGLE_CLOUD_PROJECT
            proc_id = self.settings.DOCUMENT_AI_PROCESSOR_ID
            url = f"https://{loc}-documentai.googleapis.com/v1/projects/{proj}/locations/{loc}/processors/{proc_id}"

            headers = {
                "Authorization": f"Bearer {credentials.token}",
                "Content-Type": "application/json",
            }
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "status": "live",
                    "display_name": data.get("displayName", proc_id),
                    "type": data.get("type", "UNKNOWN"),
                    "state": data.get("state", "UNKNOWN"),
                    "location": loc,
                }
            elif resp.status_code == 403:
                return {
                    "status": "permission_denied",
                    "code": 403,
                    "message": "Service account lacks 'documentai.processors.get' or Document AI IAM permissions",
                    "location": loc,
                }
            else:
                return {
                    "status": "unavailable",
                    "code": resp.status_code,
                    "message": resp.text[:200],
                    "location": loc,
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "location": self.settings.DOCUMENT_AI_LOCATION,
            }

    async def process_document(
        self,
        file_bytes: bytes,
        mime_type: str,
        filename: str,
    ) -> DocumentAIResult:
        """
        Process a document using Google Document AI Layout Parser if enabled.
        Returns explicit status and never claims live success if the service call fails.
        """
        if not self.is_configured():
            return DocumentAIResult(
                is_live=False,
                status="disabled_or_unconfigured",
                error_message="Document AI is not enabled or processor ID is not set.",
            )

        import asyncio

        def _sync_process() -> DocumentAIResult:
            try:
                import requests

                credentials = self._get_credentials()

                loc = self.settings.DOCUMENT_AI_LOCATION or "eu"
                proj = self.settings.GOOGLE_CLOUD_PROJECT
                proc_id = self.settings.DOCUMENT_AI_PROCESSOR_ID
                endpoint = f"https://{loc}-documentai.googleapis.com/v1/projects/{proj}/locations/{loc}/processors/{proc_id}:process"

                b64_content = base64.b64encode(file_bytes).decode("utf-8")
                payload = {
                    "rawDocument": {
                        "content": b64_content,
                        "mimeType": mime_type,
                    }
                }
                headers = {
                    "Authorization": f"Bearer {credentials.token}",
                    "Content-Type": "application/json",
                }

                resp = requests.post(endpoint, headers=headers, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    doc_obj = data.get("document", {})
                    full_text = doc_obj.get("text", "")
                    pages = doc_obj.get("pages", [])
                    extracted_tables = []
                    extracted_blocks = []

                    for page_idx, page in enumerate(pages, start=1):
                        # Extract tables
                        for t in page.get("tables", []):
                            rows = []
                            for row in t.get("bodyRows", []):
                                cell_texts = []
                                for cell in row.get("cells", []):
                                    cell_text = self._get_layout_text(doc_obj.get("text", ""), cell.get("layout", {}))
                                    cell_texts.append(cell_text)
                                rows.append(cell_texts)
                            if rows:
                                extracted_tables.append({"page": page_idx, "rows": rows})

                        # Extract blocks
                        for b in page.get("blocks", []):
                            b_text = self._get_layout_text(full_text, b.get("layout", {}))
                            if b_text.strip():
                                extracted_blocks.append({"page": page_idx, "text": b_text.strip()})

                    return DocumentAIResult(
                        is_live=True,
                        status="live_success",
                        text=full_text,
                        tables=extracted_tables,
                        blocks=extracted_blocks,
                        page_count=len(pages),
                    )
                else:
                    err_msg = f"Document AI returned HTTP {resp.status_code}: {resp.text[:300]}"
                    logger.warning(err_msg)
                    return DocumentAIResult(
                        is_live=False,
                        status=f"api_error_{resp.status_code}",
                        error_message=err_msg,
                    )
            except Exception as e:
                logger.error("Document AI processing failed: %s", e)
                return DocumentAIResult(
                    is_live=False,
                    status="client_exception",
                    error_message=str(e),
                )

        return await asyncio.to_thread(_sync_process)

    def _get_layout_text(self, full_text: str, layout: Dict[str, Any]) -> str:
        text_anchor = layout.get("textAnchor", {})
        segments = text_anchor.get("textSegments", [])
        collected = []
        for seg in segments:
            start_index = int(seg.get("startIndex", 0))
            end_index = int(seg.get("endIndex", 0))
            if end_index <= len(full_text):
                collected.append(full_text[start_index:end_index])
        return "".join(collected)
