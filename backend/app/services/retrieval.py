"""
HYPERREALM Enterprise Retrieval Service.
Provides scoped, access-controlled retrieval across personal knowledge,
official published guidelines, project documents, and historical incidents/runbooks.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Optional

from ..dependencies import (
    get_doc_repo,
    get_guide_repo,
    get_incident_repo,
    get_project_repo,
)
from ..models import (
    Document,
    DocumentScope,
    Guideline,
    Incident,
    UserProfile,
    UserRole,
)
from ..schemas import KnowledgeSearchResult
from .vertex_search import VertexAISearchService

logger = logging.getLogger("hyperrealm.retrieval")


class EnterpriseRetrievalService:
    """
    Unified enterprise search service enforcing authorization and scope boundaries.
    """

    def __init__(self):
        self.vertex_search = VertexAISearchService()

    @property
    def doc_repo(self):
        return get_doc_repo()

    @property
    def guide_repo(self):
        return get_guide_repo()

    @property
    def incident_repo(self):
        return get_incident_repo()

    @property
    def project_repo(self):
        return get_project_repo()

    async def search(
        self,
        query: str,
        user: UserProfile,
        scopes: list[DocumentScope] | None = None,
        top_k: int = 5,
    ) -> tuple[list[KnowledgeSearchResult], list[str]]:
        """
        Execute scoped retrieval for user:
        1. Query personal documents belonging to user.
        2. Query official guidelines (published only).
        3. Query authorized project documents.
        4. Query historical incidents/runbooks.
        5. Compute relevance scores and rank.
        6. Identify discrepancies between personal docs and official guidelines.
        """
        if scopes is None:
            scopes = [DocumentScope.PERSONAL, DocumentScope.OFFICIAL]

        results: list[KnowledgeSearchResult] = []
        tokens = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 2]
        personal_matches: list[Document] = []
        official_matches: list[Guideline] = []

        # ── 1. Personal & Company Documents Scope ─────────────────────────────
        if DocumentScope.PERSONAL in scopes:
            # Query documents authored by user or marked as public / accessible
            user_docs, _ = await self.doc_repo.list(skip=0, limit=100, author_id=user.id)
            all_docs, _ = await self.doc_repo.list(skip=0, limit=100)
            seen_ids = set()
            docs = []
            for d in user_docs + all_docs:
                if d.id not in seen_ids:
                    # Accessible if authored by current user, or marked public, or not private
                    if d.author_id == user.id or d.is_public or d.scope != DocumentScope.PERSONAL:
                        docs.append(d)
                        seen_ids.add(d.id)

            for doc in docs:
                score = self._compute_relevance(query, tokens, doc.title, doc.content or doc.extracted_text or "")
                if score > 0.05 or not tokens:
                    snippet = self._make_snippet(query, doc.content or doc.extracted_text or "")
                    doc_scope = DocumentScope.PERSONAL if doc.author_id == user.id else DocumentScope.OFFICIAL
                    results.append(
                        KnowledgeSearchResult(
                            id=doc.id,
                            title=doc.title,
                            snippet=snippet,
                            scope=doc_scope,
                            category=doc.category,
                            version=str(doc.version),
                            author_id=doc.author_id,
                            score=round(score, 3),
                            citations=[{
                                "source_type": "personal_document" if doc.author_id == user.id else "company_document",
                                "document_id": doc.id,
                                "title": doc.title,
                                "version": str(doc.version),
                                "author": user.name if doc.author_id == user.id else "HYPERREALM Org",
                                "section": "User Knowledge Hub" if doc.author_id == user.id else "Enterprise Policies",
                            }],
                        )
                    )
                    personal_matches.append(doc)

        # ── 2. Official Guidelines Scope (published only for non-admin) ────────
        if DocumentScope.OFFICIAL in scopes:
            guidelines, _ = await self.guide_repo.list(skip=0, limit=100, status="published")
            for guide in guidelines:
                score = self._compute_relevance(query, tokens, guide.title, guide.content)
                if score > 0.05 or not tokens:
                    snippet = self._make_snippet(query, guide.content)
                    results.append(
                        KnowledgeSearchResult(
                            id=guide.id,
                            title=guide.title,
                            snippet=snippet,
                            scope=DocumentScope.OFFICIAL,
                            category=guide.category,
                            version=guide.version,
                            author_id=guide.owner_id,
                            score=round(score, 3),
                            citations=[{
                                "source_type": "official_guideline",
                                "guideline_id": guide.id,
                                "title": guide.title,
                                "version": guide.version,
                                "effective_date": guide.effective_date.isoformat() if guide.effective_date else None,
                                "section": "Authoritative Policy",
                            }],
                        )
                    )
                    official_matches.append(guide)

            # Query live Vertex AI Search for enterprise store if configured
            if self.vertex_search.is_configured():
                vs_res = await self.vertex_search.search(query=query, top_k=top_k)
                if vs_res.is_live and vs_res.results:
                    is_admin = getattr(user, "role", "") in ("admin", UserRole.ADMIN, "UserRole.ADMIN")
                    for vs_item in vs_res.results:
                        # RBAC: if document is under a user folder, enforce ownership
                        if vs_item.scope == DocumentScope.PERSONAL and vs_item.author_id != user.id and not is_admin:
                            continue
                        # Only include results with actual readable content
                        if vs_item.snippet and not vs_item.snippet.startswith("[No readable"):
                            results.append(vs_item)

        # ── 3. Project Scope ───────────────────────────────────────────────────
        if DocumentScope.PROJECT in scopes:
            user_projects = user.project_ids or []
            if user_projects:
                proj_docs, _ = await self.doc_repo.list(skip=0, limit=100, scope=DocumentScope.PROJECT.value)
                for doc in proj_docs:
                    # Check if doc belongs to user's assigned projects
                    doc_proj = doc.metadata.get("project_id")
                    if doc_proj and doc_proj in user_projects:
                        score = self._compute_relevance(query, tokens, doc.title, doc.content)
                        if score > 0.05 or not tokens:
                            snippet = self._make_snippet(query, doc.content)
                            results.append(
                                KnowledgeSearchResult(
                                    id=doc.id,
                                    title=doc.title,
                                    snippet=snippet,
                                    scope=DocumentScope.PROJECT,
                                    category=doc.category,
                                    version=str(doc.version),
                                    author_id=doc.author_id,
                                    score=round(score, 3),
                                    citations=[{
                                        "source_type": "project_document",
                                        "document_id": doc.id,
                                        "title": doc.title,
                                        "project_id": doc_proj,
                                    }],
                                )
                            )

        # ── 4. Historical Scope (Incidents & Runbooks) ─────────────────────────
        if DocumentScope.HISTORICAL in scopes:
            incidents, _ = await self.incident_repo.list(skip=0, limit=100)
            for inc in incidents:
                score = self._compute_relevance(query, tokens, inc.title, f"{inc.description} {inc.resolution_notes}")
                if score > 0.05 or not tokens:
                    snippet = self._make_snippet(query, inc.description + " Resolution: " + inc.resolution_notes)
                    results.append(
                        KnowledgeSearchResult(
                            id=inc.id,
                            title=f"Incident {inc.id}: {inc.title}",
                            snippet=snippet,
                            scope=DocumentScope.HISTORICAL,
                            category="incident",
                            version="1.0",
                            author_id=inc.reporter_id,
                            score=round(score, 3),
                            citations=[{
                                "source_type": "incident_record",
                                "incident_id": inc.id,
                                "severity": inc.severity.value if hasattr(inc.severity, "value") else str(inc.severity),
                                "status": inc.status.value if hasattr(inc.status, "value") else str(inc.status),
                            }],
                        )
                    )

        # Sort results by relevance score descending
        results.sort(key=lambda r: r.score, reverse=True)
        top_results = results[:top_k]

        # Detect discrepancies between personal documents and official guidelines
        discrepancies = self._detect_discrepancies(personal_matches, official_matches)

        return top_results, discrepancies

    def _compute_relevance(self, query: str, tokens: list[str], title: str, content: str) -> float:
        """Compute keyword overlap & phrase match score."""
        title_lower = title.lower()
        content_lower = content.lower()
        query_lower = query.lower()

        score = 0.0
        # Exact query match in title
        if query_lower in title_lower:
            score += 0.6
        elif any(t in title_lower for t in tokens):
            score += 0.35

        # Phrase match in content
        if query_lower in content_lower:
            score += 0.4

        # Token overlap
        if tokens:
            matches = sum(1 for t in tokens if t in content_lower)
            score += 0.3 * (matches / len(tokens))

        return min(score, 1.0)

    def _make_snippet(self, query: str, content: str, max_chars: int = 240) -> str:
        """Extract relevant snippet around query terms."""
        if not content:
            return "No content available."
        clean = " ".join(content.split())
        query_terms = [q.lower() for q in query.split() if len(q) > 3]
        for term in query_terms:
            idx = clean.lower().find(term)
            if idx != -1:
                start = max(0, idx - 60)
                end = min(len(clean), idx + max_chars - 60)
                snip = clean[start:end].strip()
                prefix = "..." if start > 0 else ""
                suffix = "..." if end < len(clean) else ""
                return f"{prefix}{snip}{suffix}"
        return clean[:max_chars] + ("..." if len(clean) > max_chars else "")

    def _detect_discrepancies(
        self, personal_docs: list[Document], official_guides: list[Guideline]
    ) -> list[str]:
        """
        Identify if any employee notes contradict published company guidelines.
        Enforces policy precedence: official published guidelines are authoritative.
        """
        discrepancies: list[str] = []
        for p_doc in personal_docs:
            p_text = (p_doc.content or "").lower()
            for guide in official_guides:
                g_text = guide.content.lower()
                # Check known security/coding policy discrepancies
                if "jwt" in p_text and "jwt" in g_text:
                    if ("localstorage" in p_text or "in-memory" in p_text) and "http-only" in g_text:
                        discrepancies.append(
                            f"Notice: Personal KT '{p_doc.title}' references client-side token storage, "
                            f"whereas official guideline '{guide.title}' (v{guide.version}) strictly mandates "
                            f"HTTP-only cookies. The published official guideline is authoritative."
                        )
                if "approval" in p_text and "approval" in g_text:
                    if "bypass" in p_text or "skip" in p_text:
                        discrepancies.append(
                            f"Discrepancy: Personal KT '{p_doc.title}' describes expedited manual steps, "
                            f"which conflicts with official policy '{guide.title}'. The official guideline is authoritative."
                        )
        return discrepancies
    def _detect_discrepancies(
        self, personal_docs: list[Document], official_guides: list[Guideline]
    ) -> list[str]:
        """
        Identify if any employee notes contradict published company guidelines.
        Enforces policy precedence: official published guidelines are authoritative.
        """
        discrepancies: list[str] = []
        for p_doc in personal_docs:
            p_text = (p_doc.content or "").lower()
            for guide in official_guides:
                g_text = guide.content.lower()
                # Check known security/coding policy discrepancies
                if "jwt" in p_text and "jwt" in g_text:
                    if ("localstorage" in p_text or "in-memory" in p_text) and "http-only" in g_text:
                        discrepancies.append(
                            f"Notice: Personal KT '{p_doc.title}' references client-side token storage, "
                            f"whereas official guideline '{guide.title}' (v{guide.version}) strictly mandates "
                            f"HTTP-only cookies. The published official guideline is authoritative."
                        )
                if "approval" in p_text and "approval" in g_text:
                    if "bypass" in p_text or "skip" in p_text:
                        discrepancies.append(
                            f"Discrepancy: Personal KT '{p_doc.title}' describes expedited manual steps, "
                            f"which conflicts with official policy '{guide.title}'. The official guideline is authoritative."
                        )
        return discrepancies


# Backward-compatible alias
RetrievalService = EnterpriseRetrievalService
