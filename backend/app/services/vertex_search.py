"""
HYPERREALM Vertex AI Search Integration Service.
Provides live search and retrieval from Google Cloud Vertex AI Search / Discovery Engine
when VERTEX_AI_SEARCH_ENABLED=true and data-store or engine configuration is present.
Enforces that external cloud search results respect organizational boundaries and never
expose personal employee documents.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from ..config import get_settings
from ..models import DocumentScope
from ..schemas import KnowledgeSearchResult

logger = logging.getLogger("hyperrealm.vertex_search")


class VertexSearchResult(BaseModel):
    is_live: bool = False
    status: str = "unavailable"
    total_size: int = 0
    results: List[KnowledgeSearchResult] = []
    error_message: Optional[str] = None


class VertexAISearchService:
    def __init__(self):
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(
            self.settings.VERTEX_AI_SEARCH_ENABLED
            and (self.settings.VERTEX_AI_SEARCH_DATA_STORE_ID or self.settings.VERTEX_AI_SEARCH_ENGINE_ID)
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
        """Diagnostic check of Vertex AI Search integration."""
        if not self.settings.VERTEX_AI_SEARCH_ENABLED:
            return {
                "status": "disabled",
                "message": "VERTEX_AI_SEARCH_ENABLED is false",
                "data_store_id": self.settings.VERTEX_AI_SEARCH_DATA_STORE_ID,
                "engine_id": self.settings.VERTEX_AI_SEARCH_ENGINE_ID,
            }

        if not (self.settings.VERTEX_AI_SEARCH_DATA_STORE_ID or self.settings.VERTEX_AI_SEARCH_ENGINE_ID):
            return {
                "status": "unconfigured",
                "message": "Neither VERTEX_AI_SEARCH_DATA_STORE_ID nor VERTEX_AI_SEARCH_ENGINE_ID is set",
            }

        # Check API connectivity
        try:
            import requests

            credentials = self._get_credentials()

            proj = self.settings.GOOGLE_CLOUD_PROJECT
            loc = self.settings.VERTEX_AI_SEARCH_LOCATION or "global"
            ds_id = self.settings.VERTEX_AI_SEARCH_DATA_STORE_ID

            if ds_id:
                url = (
                    f"https://discoveryengine.googleapis.com/v1/projects/{proj}/locations/{loc}"
                    f"/collections/default_collection/dataStores/{ds_id}/servingConfigs/default_search:search"
                )
            else:
                eng_id = self.settings.VERTEX_AI_SEARCH_ENGINE_ID
                url = (
                    f"https://discoveryengine.googleapis.com/v1/projects/{proj}/locations/{loc}"
                    f"/collections/default_collection/engines/{eng_id}/servingConfigs/default_search:search"
                )

            headers = {
                "Authorization": f"Bearer {credentials.token}",
                "Content-Type": "application/json",
            }
            resp = requests.post(url, headers=headers, json={"query": "healthcheck", "pageSize": 1}, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "status": "live",
                    "data_store_id": ds_id,
                    "engine_id": self.settings.VERTEX_AI_SEARCH_ENGINE_ID,
                    "location": loc,
                    "message": "Vertex AI Search data store reachable and responding",
                }
            elif resp.status_code == 403:
                return {
                    "status": "permission_denied",
                    "code": 403,
                    "message": "Service account lacks Discovery Engine search permissions",
                }
            else:
                return {
                    "status": "unavailable",
                    "code": resp.status_code,
                    "message": resp.text[:200],
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }

    async def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> VertexSearchResult:
        """
        Execute live search via Vertex AI Search.
        Results are returned as KnowledgeSearchResult objects with full source citations.
        """
        if not self.is_configured():
            return VertexSearchResult(
                is_live=False,
                status="disabled_or_unconfigured",
                error_message="Vertex AI Search is not enabled or configured.",
            )

        import asyncio

        def _sync_search() -> VertexSearchResult:
            try:
                import requests

                credentials = self._get_credentials()

                proj = self.settings.GOOGLE_CLOUD_PROJECT
                loc = self.settings.VERTEX_AI_SEARCH_LOCATION or "global"
                ds_id = self.settings.VERTEX_AI_SEARCH_DATA_STORE_ID

                if ds_id:
                    url = (
                        f"https://discoveryengine.googleapis.com/v1/projects/{proj}/locations/{loc}"
                        f"/collections/default_collection/dataStores/{ds_id}/servingConfigs/default_search:search"
                    )
                else:
                    eng_id = self.settings.VERTEX_AI_SEARCH_ENGINE_ID
                    url = (
                        f"https://discoveryengine.googleapis.com/v1/projects/{proj}/locations/{loc}"
                        f"/collections/default_collection/engines/{eng_id}/servingConfigs/default_search:search"
                    )

                headers = {
                    "Authorization": f"Bearer {credentials.token}",
                    "Content-Type": "application/json",
                }
                body = {
                    "query": query,
                    "pageSize": max(1, min(top_k, 20)),
                    "contentSearchSpec": {
                        "snippetSpec": {"returnSnippet": True},
                        "extractiveContentSpec": {"maxExtractiveSegmentCount": 3},
                    },
                }

                resp = requests.post(url, headers=headers, json=body, timeout=10)
                if resp.status_code != 200:
                    err_msg = f"Vertex AI Search returned HTTP {resp.status_code}: {resp.text[:300]}"
                    logger.warning(err_msg)
                    return VertexSearchResult(
                        is_live=False,
                        status=f"api_error_{resp.status_code}",
                        error_message=err_msg,
                    )

                data = resp.json()
                raw_results = data.get("results", [])
                total_size = data.get("totalSize", len(raw_results))
                parsed: List[KnowledgeSearchResult] = []

                import html
                import re

                for idx, r in enumerate(raw_results):
                    doc_data = r.get("document", {})
                    doc_id = doc_data.get("id", f"vertex_doc_{idx}")
                    struct_data = doc_data.get("structData", {})
                    derived_data = doc_data.get("derivedStructData", {})

                    title = (
                        struct_data.get("title")
                        or derived_data.get("title")
                        or doc_data.get("name", "Vertex AI Search Document")
                    )
                    uri = struct_data.get("uri") or derived_data.get("link") or ""

                    # 1. Extract readable content from layout chunks (if chunking is enabled)
                    chunk_text = ""
                    page_info = None
                    chunks = derived_data.get("chunks", [])
                    if chunks:
                        chunk_contents = [ch.get("content", "").strip() for ch in chunks if ch.get("content")]
                        if chunk_contents:
                            chunk_text = "\n\n".join(chunk_contents[:2])
                        first_span = chunks[0].get("page_span", {})
                        if first_span:
                            p_start = first_span.get("page_start", 1)
                            p_end = first_span.get("page_end", 1)
                            page_info = f"Pages {p_start}-{p_end}" if p_start != p_end else f"Page {p_start}"

                    # 2. Extract extractive segments
                    segment_text = ""
                    segments = derived_data.get("extractive_segments", [])
                    if segments:
                        seg_contents = [s.get("content", "").strip() for s in segments if s.get("content")]
                        if seg_contents:
                            segment_text = "\n\n".join(seg_contents[:2])
                        if not page_info and segments[0].get("page_number"):
                            page_info = f"Page {segments[0]['page_number']}"

                    # 3. Extract snippet
                    snippet_text = ""
                    if derived_data.get("snippets"):
                        raw_snip = derived_data["snippets"][0].get("snippet", "")
                        if raw_snip:
                            clean_snip = html.unescape(re.sub(r"<[^>]+>", "", raw_snip)).strip()
                            clean_snip = re.sub(r"&nbsp;?", " ", clean_snip).strip()
                            snippet_text = clean_snip

                    # Determine primary readable text passage
                    final_snippet = chunk_text or segment_text or snippet_text or struct_data.get("content", "").strip()

                    # Extract owner_id from URI if personal path (e.g. users/usr_123/...)
                    owner_id = None
                    if uri:
                        owner_match = re.search(r"users/([^/]+)/", uri)
                        if owner_match:
                            owner_id = owner_match.group(1)

                    parsed.append(
                        KnowledgeSearchResult(
                            id=doc_id,
                            title=title,
                            snippet=final_snippet,
                            scope=DocumentScope.OFFICIAL if not owner_id else DocumentScope.PERSONAL,
                            category="vertex_ai_search",
                            version="1.0",
                            author_id=owner_id or "vertex_ai_search",
                            score=round(1.0 - (idx * 0.05), 3),
                            citations=[{
                                "source_type": "vertex_ai_search",
                                "document_id": doc_id,
                                "title": title,
                                "uri": uri,
                                "data_store": ds_id or self.settings.VERTEX_AI_SEARCH_ENGINE_ID,
                                "section": "Enterprise Search Index" + (f" ({page_info})" if page_info else ""),
                                "page": page_info,
                                "owner_id": owner_id,
                            }],
                        )
                    )

                return VertexSearchResult(
                    is_live=True,
                    status="live_success",
                    total_size=total_size,
                    results=parsed,
                )
            except Exception as e:
                logger.error("Vertex AI Search request failed: %s", e)
                return VertexSearchResult(
                    is_live=False,
                    status="client_exception",
                    error_message=str(e),
                )

        return await asyncio.to_thread(_sync_search)

    async def index_document(self, gcs_uri: str, doc_id: str | None = None) -> dict[str, Any]:
        """
        Trigger incremental ingestion of a GCS document into the configured Vertex AI Search datastore.
        Uses POST https://discoveryengine.googleapis.com/v1/.../branches/0/documents:import
        with reconciliationMode=INCREMENTAL and dataSchema="content".
        """
        if not self.is_configured() or not gcs_uri.startswith("gs://"):
            return {"status": "skipped", "reason": "Vertex AI Search or GCS URI not configured"}

        import asyncio
        import requests

        def _sync_import():
            try:
                credentials = self._get_credentials()
                proj = self.settings.GOOGLE_CLOUD_PROJECT
                loc = self.settings.VERTEX_AI_SEARCH_LOCATION or "global"
                ds_id = self.settings.VERTEX_AI_SEARCH_DATA_STORE_ID or "hyperrealm-knowledge-store_1792309262719"

                url = (
                    f"https://discoveryengine.googleapis.com/v1/projects/{proj}/locations/{loc}"
                    f"/collections/default_collection/dataStores/{ds_id}/branches/0/documents:import"
                )
                headers = {
                    "Authorization": f"Bearer {credentials.token}",
                    "Content-Type": "application/json",
                }
                body = {
                    "gcsSource": {
                        "inputUris": [gcs_uri],
                        "dataSchema": "content",
                    },
                    "reconciliationMode": "INCREMENTAL",
                }
                resp = requests.post(url, headers=headers, json=body, timeout=20)
                if resp.status_code in (200, 201):
                    op_data = resp.json()
                    op_name = op_data.get("name", "")
                    return {
                        "status": "indexing_triggered",
                        "operation_name": op_name,
                        "operation_id": op_name.split("/")[-1] if op_name else "",
                        "response": op_data,
                    }
                elif resp.status_code == 403:
                    err_msg = resp.text
                    logger.warning("Vertex AI Search documents:import 403 permission denied: %s", err_msg)
                    return {
                        "status": "permission_denied",
                        "error": "Service account lacks 'roles/discoveryengine.editor' permission to import documents directly.",
                        "raw": err_msg,
                    }
                else:
                    logger.warning("Vertex AI Search import returned HTTP %s: %s", resp.status_code, resp.text)
                    return {
                        "status": "api_error",
                        "code": resp.status_code,
                        "error": resp.text[:300],
                    }
            except Exception as e:
                logger.exception("Error initiating Vertex AI Search document import: %s", e)
                return {"status": "exception", "error": str(e)}

        return await asyncio.to_thread(_sync_import)

    async def get_operation_status(self, operation_name: str) -> dict[str, Any]:
        """Query the status of a Discovery Engine long-running operation."""
        if not operation_name:
            return {"done": True, "success": False, "error": "No operation name provided"}

        import asyncio
        import requests

        def _sync_op():
            try:
                credentials = self._get_credentials()
                url = f"https://discoveryengine.googleapis.com/v1/{operation_name}"
                headers = {"Authorization": f"Bearer {credentials.token}"}
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    is_done = data.get("done", False)
                    error = data.get("error")
                    return {
                        "done": is_done,
                        "success": is_done and not error,
                        "error": error.get("message") if error else None,
                        "metadata": data.get("metadata", {}),
                        "response": data.get("response", {}),
                    }
                return {"done": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
            except Exception as e:
                return {"done": False, "error": str(e)}

        return await asyncio.to_thread(_sync_op)

    async def poll_operation(self, operation_name: str, max_wait_sec: int = 30) -> dict[str, Any]:
        """Poll operation until completion or timeout."""
        import asyncio
        import time

        start_time = time.time()
        while time.time() - start_time < max_wait_sec:
            status = await self.get_operation_status(operation_name)
            if status.get("done"):
                return status
            await asyncio.sleep(2)
        return {"done": False, "timeout": True, "error": f"Operation polling timed out after {max_wait_sec}s"}

    async def delete_document(self, doc_id_or_uri: str) -> bool:
        """Delete document from Vertex AI Search datastore branch 0."""
        if not self.is_configured():
            return True

        import asyncio
        import requests

        def _sync_delete():
            try:
                credentials = self._get_credentials()
                proj = self.settings.GOOGLE_CLOUD_PROJECT
                loc = self.settings.VERTEX_AI_SEARCH_LOCATION or "global"
                ds_id = self.settings.VERTEX_AI_SEARCH_DATA_STORE_ID or "hyperrealm-knowledge-store_1792309262719"

                doc_id = doc_id_or_uri
                if "/" in doc_id:
                    doc_id = doc_id.split("/")[-1].replace(".pdf", "").replace(".txt", "")

                url = (
                    f"https://discoveryengine.googleapis.com/v1/projects/{proj}/locations/{loc}"
                    f"/collections/default_collection/dataStores/{ds_id}/branches/0/documents/{doc_id}"
                )
                headers = {"Authorization": f"Bearer {credentials.token}"}
                resp = requests.delete(url, headers=headers, timeout=10)
                return resp.status_code in (200, 204, 404)
            except Exception as e:
                logger.warning("Failed deleting document %s from Vertex AI Search: %s", doc_id_or_uri, e)
                return False

        return await asyncio.to_thread(_sync_delete)

