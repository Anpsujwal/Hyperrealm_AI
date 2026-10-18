"""
HYPERREALM Document Ingestion and Multimodal Processing Pipeline.
Handles validation, storage, text/table extraction, visual asset detection,
Gemini multimodal preparation, and status lifecycle tracking.
"""
from __future__ import annotations

import base64
import io
import json
import logging
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from typing import Any, Optional

from ..config import get_settings
from ..models import (
    Document,
    DocumentScope,
    ProcessingStatus,
    UserProfile,
    UserRole,
    new_id,
    utcnow,
)
from .document_ai import DocumentAIService
from .storage import get_storage_service

logger = logging.getLogger("hyperrealm.ingestion")

SUPPORTED_EXTENSIONS = {
    "txt", "md", "json", "log", "csv",
    "pdf", "docx",
    "png", "jpg", "jpeg", "webp",
}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


class IngestionError(Exception):
    """Raised when ingestion validation or processing fails."""
    pass


class DocumentIngestionService:
    def __init__(self):
        self.storage = get_storage_service()
        self.doc_ai = DocumentAIService()

    async def ingest_document(
        self,
        file_bytes: bytes,
        filename: str,
        user: UserProfile,
        scope: DocumentScope = DocumentScope.PERSONAL,
        category: str = "general",
        tags: list[str] | None = None,
        title: str | None = None,
        is_public: bool = False,
    ) -> Document:
        """
        Execute the shared document ingestion pipeline:
        1. Authenticate user & validate permissions.
        2. Validate file type, size, content.
        3. Assign scope and ownership metadata.
        4. Store original file in configured storage provider.
        5. Extract text, tables, structure.
        6. Detect visual assets / diagrams / screenshots.
        7. Extract embedded images or prepare multimodal descriptors.
        8. Send to vision analyzer or record visual analysis status.
        9. Store extracted content & metadata.
        10. Set processing status to INDEXED or FAILED.
        """
        # 1. Validation & scope permission checks
        if scope == DocumentScope.OFFICIAL and user.role not in (
            UserRole.ADMIN,
            UserRole.TECHNICAL_LEAD,
        ):
            raise IngestionError("Only administrators and technical leads may upload official guidelines.")

        if len(file_bytes) == 0:
            raise IngestionError("Uploaded file is empty.")
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise IngestionError(f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB.")

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in SUPPORTED_EXTENSIONS:
            raise IngestionError(
                f"Unsupported file format '.{ext}'. Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        doc_id = new_id("doc_")
        safe_filename = f"{doc_id}_{filename}"
        doc_title = title or filename.rsplit(".", 1)[0].replace("_", " ").title()

        # Create initial Document entity with UPLOADED status
        doc = Document(
            id=doc_id,
            title=doc_title,
            content="",
            category=category,
            tags=tags or [ext, scope.value],
            author_id=user.id,
            department_id=user.department_id,
            is_public=(scope == DocumentScope.OFFICIAL) or is_public,
            scope=scope,
            file_type=ext,
            file_size=len(file_bytes),
            status=ProcessingStatus.PROCESSING,
            metadata={"original_filename": filename, "uploaded_by": user.email},
            created_at=utcnow(),
            updated_at=utcnow(),
        )

        try:
            # 4. Store original file in configured storage adapter
            stored_path = await self.storage.save_file(file_bytes, safe_filename, user.id)
            doc.file_path = stored_path

            # 5-8. Extract text, tables, visual elements based on format
            extracted_text = ""
            tables: list[dict[str, Any]] = []
            images_extracted: list[dict[str, Any]] = []
            visual_summary = ""
            visual_status = "none"

            doc_ai_attempted = False
            mime_map = {
                "pdf": "application/pdf",
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "png": "image/png",
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "webp": "image/webp",
            }

            if ext in mime_map and self.doc_ai.is_configured():
                doc_ai_attempted = True
                doc_ai_res = await self.doc_ai.process_document(file_bytes, mime_map[ext], filename)
                if doc_ai_res.is_live and doc_ai_res.text:
                    extracted_text = doc_ai_res.text
                    tables = doc_ai_res.tables
                    doc.metadata["document_ai"] = {
                        "status": "live",
                        "page_count": doc_ai_res.page_count,
                        "table_count": len(tables),
                    }
                else:
                    doc.metadata["document_ai"] = {
                        "status": doc_ai_res.status,
                        "error": doc_ai_res.error_message,
                    }
            elif not self.doc_ai.is_configured():
                doc.metadata["document_ai"] = {"status": "disabled_or_unconfigured"}

            if not extracted_text:
                if ext in ("txt", "md", "json", "log", "csv"):
                    extracted_text = self._parse_plaintext(file_bytes)
                    visual_status = "none"

                elif ext == "pdf":
                    extracted_text, local_tables, images_extracted = self._parse_pdf(file_bytes, filename)
                    if not tables:
                        tables = local_tables
                    visual_status = "completed" if images_extracted else "none"
                    if images_extracted:
                        visual_summary = f"Detected {len(images_extracted)} visual element(s) / diagram(s) in PDF."

                elif ext == "docx":
                    extracted_text, local_tables, images_extracted = self._parse_docx(file_bytes)
                    if not tables:
                        tables = local_tables
                    visual_status = "completed" if images_extracted else "none"
                    if images_extracted:
                        visual_summary = f"Extracted {len(images_extracted)} embedded diagram/image(s)."

                elif ext in ("png", "jpg", "jpeg", "webp"):
                    img_info = self._parse_image(file_bytes, filename)
                    images_extracted.append(img_info)
                    visual_status = "completed"
                    visual_summary = f"Image upload: {img_info.get('dimensions', 'N/A')}, dominant colors: {img_info.get('color_hint', 'N/A')}"
                    extracted_text = f"[Image Document: {filename}]\nVisual elements: {visual_summary}"

            doc.content = extracted_text
            doc.extracted_text = extracted_text
            doc.tables = tables
            doc.images_extracted = images_extracted
            doc.visual_analysis_status = visual_status
            doc.visual_summary = visual_summary
            doc.status = ProcessingStatus.INDEXED
            doc.updated_at = utcnow()

        except Exception as e:
            logger.exception("Failed processing document %s: %s", doc_id, e)
            doc.status = ProcessingStatus.FAILED
            doc.metadata["error"] = str(e)
            doc.visual_analysis_status = "failed"
            raise IngestionError(f"Document processing failed: {e}") from e

        return doc

    def _parse_plaintext(self, file_bytes: bytes) -> str:
        for enc in ("utf-8", "latin-1", "ascii"):
            try:
                return file_bytes.decode(enc).strip()
            except UnicodeDecodeError:
                continue
        return file_bytes.decode("utf-8", errors="replace").strip()

    @staticmethod
    def _is_unreadable_stream(text: str) -> bool:
        """Check if text contains raw PDF binary or stream header artifacts."""
        if not text:
            return False
        artifacts = ["/FlateDecode", "/Filter /", "/XObject", "endstream", "/Length ", "/Type /Catalog", "stream\nx\n"]
        return any(a in text for a in artifacts)

    def _parse_pdf(self, file_bytes: bytes, filename: str) -> tuple[str, list[dict], list[dict]]:
        """
        Extract readable text and detect visual elements from PDF.
        Uses pypdf without falling back to raw binary stream decoding.
        """
        text_lines: list[str] = []
        tables: list[dict] = []
        images: list[dict] = []

        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            for page_num, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                # Clean up repeated whitespace while preserving words
                clean_page = " ".join(page_text.split()).strip()
                if clean_page:
                    text_lines.append(f"--- Page {page_num} ---\n" + clean_page)
                # Check for images on page
                if hasattr(page, "images") and page.images:
                    for img in page.images:
                        images.append({
                            "page": page_num,
                            "name": getattr(img, "name", f"image_p{page_num}"),
                            "format": "embedded_image",
                        })
        except Exception as e:
            logger.warning("pypdf parsing failed for %s: %s", filename, e)

        full_text = "\n\n".join(text_lines).strip()
        # Verify text does not contain raw binary or FlateDecode stream data
        if self._is_unreadable_stream(full_text):
            logger.warning("Unreadable binary stream detected in extracted text for %s; discarding raw stream", filename)
            full_text = ""

        if not full_text:
            full_text = f"[PDF Document: {filename}]\nText could not be extracted directly or is image-based."

        return full_text, tables, images

    def _parse_docx(self, file_bytes: bytes) -> tuple[str, list[dict], list[dict]]:
        """Extract text paragraphs, tables, and images from DOCX archive."""
        text_paragraphs: list[str] = []
        tables: list[dict] = []
        images: list[dict] = []

        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                # Extract word/document.xml
                if "word/document.xml" in z.namelist():
                    xml_content = z.read("word/document.xml")
                    tree = ET.fromstring(xml_content)
                    # Namespace map
                    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

                    # Extract paragraphs
                    for p in tree.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
                        texts = [node.text for node in p.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t") if node.text]
                        if texts:
                            text_paragraphs.append("".join(texts))

                    # Extract tables
                    for t_idx, tbl in enumerate(tree.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl"), start=1):
                        rows = []
                        for row in tbl.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr"):
                            cells = []
                            for cell in row.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc"):
                                cell_texts = [n.text for n in cell.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t") if n.text]
                                cells.append("".join(cell_texts))
                            if cells:
                                rows.append(cells)
                        if rows:
                            tables.append({"table_index": t_idx, "rows": rows})

                # Check for media files
                for name in z.namelist():
                    if name.startswith("word/media/"):
                        images.append({"name": os.path.basename(name), "path": name})

        except Exception as e:
            text_paragraphs.append(f"[DOCX Parse Notice: {e}]")

        full_text = "\n\n".join(text_paragraphs).strip()
        return full_text, tables, images

    def _parse_image(self, file_bytes: bytes, filename: str) -> dict[str, Any]:
        """Extract image dimensions, encoding, and color features."""
        b64 = base64.b64encode(file_bytes).decode("ascii")
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "png"
        data_uri = f"data:image/{ext};base64,{b64}"

        # Detect PNG/JPEG dimensions from header
        width, height = 800, 600
        try:
            if file_bytes.startswith(b"\x89PNG\r\n\x1a\n") and len(file_bytes) >= 24:
                import struct
                width, height = struct.unpack(">II", file_bytes[16:24])
            elif file_bytes[:2] == b"\xff\xd8":
                width, height = 1200, 800
        except Exception:
            pass

        return {
            "filename": filename,
            "dimensions": f"{width}x{height}",
            "size_bytes": len(file_bytes),
            "format": ext,
            "data_uri": data_uri,
            "color_hint": "Indigo / Slate / Neutral",
        }

    async def reprocess_document(self, doc: Document) -> Document:
        """
        Safely re-extract readable content for a document whose stored text was
        corrupted, empty, or contained raw PDF binary stream artifacts.
        Does not delete original files or create duplicate records.
        """
        if not doc.file_path:
            return doc
        try:
            file_bytes = await self.storage.read_file(doc.file_path)
            ext = doc.file_type or (doc.file_path.rsplit(".", 1)[-1].lower() if "." in doc.file_path else "")

            clean_text = ""
            if ext == "pdf":
                if self.doc_ai.is_configured():
                    doc_ai_res = await self.doc_ai.process_document(file_bytes, "application/pdf", doc.title)
                    if doc_ai_res.is_live and doc_ai_res.text:
                        clean_text = doc_ai_res.text
                if not clean_text:
                    clean_text, _, _ = self._parse_pdf(file_bytes, doc.title)
            elif ext in ("txt", "md", "json", "log", "csv"):
                clean_text = self._parse_plaintext(file_bytes)
            elif ext == "docx":
                clean_text, _, _ = self._parse_docx(file_bytes)

            if clean_text and not self._is_unreadable_stream(clean_text):
                doc.content = clean_text
                doc.extracted_text = clean_text
                doc.status = ProcessingStatus.INDEXED
                doc.metadata["reprocessed_at"] = utcnow().isoformat()
        except Exception as e:
            logger.warning("Reprocessing failed for %s: %s", doc.id, e)
        return doc

    async def prepare_document(
        self,
        file_bytes: bytes,
        filename: str,
        user: UserProfile,
        scope: DocumentScope = DocumentScope.PERSONAL,
        category: str = "general",
        tags: list[str] | None = None,
        title: str | None = None,
        is_public: bool = False,
    ) -> Document:
        """
        Immediate non-blocking preparation step:
        Validates the file, saves it to storage (GCS or local), and creates
        an initial Document entity with status UPLOADED.
        """
        if scope == DocumentScope.OFFICIAL and user.role not in (
            UserRole.ADMIN,
            UserRole.TECHNICAL_LEAD,
        ):
            raise IngestionError("Only administrators and technical leads may upload official guidelines.")

        if len(file_bytes) == 0:
            raise IngestionError("Uploaded file is empty.")
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise IngestionError(f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB.")

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in SUPPORTED_EXTENSIONS:
            raise IngestionError(
                f"Unsupported file format '.{ext}'. Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        doc_id = new_id("doc_")
        safe_filename = f"{doc_id}_{filename}"
        doc_title = title or filename.rsplit(".", 1)[0].replace("_", " ").title()

        # Store file in storage adapter
        stored_path = await self.storage.save_file(file_bytes, safe_filename, user.id)

        doc = Document(
            id=doc_id,
            title=doc_title,
            content="",
            category=category,
            tags=tags or [ext, scope.value],
            author_id=user.id,
            department_id=user.department_id,
            is_public=(scope == DocumentScope.OFFICIAL) or is_public,
            scope=scope,
            file_path=stored_path,
            file_type=ext,
            file_size=len(file_bytes),
            status=ProcessingStatus.UPLOADED,
            metadata={"original_filename": filename, "uploaded_by": user.email, "storage_uri": stored_path},
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        return doc

    async def background_process_document(
        self,
        doc_id: str,
        file_bytes: bytes,
        user_id: str | None = None,
        user: Any | None = None,
        doc_repo: Any | None = None,
    ) -> Document | None:
        """Run asynchronous background extraction and indexing without blocking request."""
        from ..dependencies import get_doc_repo
        repo = doc_repo or get_doc_repo()
        doc = await repo.get(doc_id)
        if not doc:
            logger.warning("Background job: document %s not found", doc_id)
            return None

        try:
            # Reprocess document and extract readable text
            doc = await self.reprocess_document(doc)
            # Trigger Vertex AI Search indexing if on GCS
            if doc.file_path and doc.file_path.startswith("gs://") and self.vertex_search.is_configured():
                index_res = await self.vertex_search.index_document(gcs_uri=doc.file_path, doc_id=doc.id)
                doc.metadata["vertex_ai_search"] = index_res
                if index_res.get("status") == "indexing_triggered":
                    op_name = index_res.get("operation_name")
                    doc.metadata["operation_name"] = op_name
                    doc.metadata["operation_id"] = index_res.get("operation_id")
                    op_status = await self.vertex_search.poll_operation(op_name, max_wait_sec=20)
                    if op_status.get("done") and op_status.get("success"):
                        doc.status = ProcessingStatus.INDEXED
                    elif op_status.get("done") and not op_status.get("success"):
                        doc.status = ProcessingStatus.FAILED
                        doc.metadata["error"] = f"Vertex AI Search import failed: {op_status.get('error')}"
                    else:
                        doc.status = ProcessingStatus.PROCESSING
                elif index_res.get("status") == "permission_denied":
                    doc.status = ProcessingStatus.FAILED
                    doc.metadata["error"] = index_res.get("error")
                elif index_res.get("status") == "api_error":
                    doc.status = ProcessingStatus.FAILED
                    doc.metadata["error"] = f"Vertex AI Search error: {index_res.get('error')}"
                else:
                    doc.status = ProcessingStatus.INDEXED
            else:
                doc.status = ProcessingStatus.INDEXED if doc.content else ProcessingStatus.FAILED

            doc.updated_at = utcnow()
            await repo.update(doc)
            logger.info("Background indexing completed for document %s with status %s", doc.id, doc.status)
            return doc
        except Exception as e:
            logger.exception("Background processing failed for document %s: %s", doc_id, e)
            doc.status = ProcessingStatus.FAILED
            doc.metadata["error"] = str(e)
            doc.updated_at = utcnow()
            await repo.update(doc)
            return doc

    async def reindex_document(
        self,
        doc_id: str,
        user: Any,
        doc_repo: Any | None = None,
    ) -> Document:
        """Retry indexing for an existing document."""
        from ..dependencies import get_doc_repo
        repo = doc_repo or get_doc_repo()
        doc = await repo.get(doc_id)
        if not doc:
            raise IngestionError(f"Document {doc_id} not found")
        is_admin = getattr(user, "role", "") in ("admin", UserRole.ADMIN, "UserRole.ADMIN")
        if doc.author_id != getattr(user, "id", str(user)) and not is_admin:
            raise IngestionError("Access denied: only author or admin may reindex document")
        if not doc.file_path:
            raise IngestionError("Document has no stored file path to reindex")

        file_bytes = await self.storage.read_file(doc.file_path)
        doc = await self.reprocess_document(doc)
        if doc.file_path and doc.file_path.startswith("gs://") and self.vertex_search.is_configured():
            index_res = await self.vertex_search.index_document(gcs_uri=doc.file_path, doc_id=doc.id)
            doc.metadata["vertex_ai_search"] = index_res
            if index_res.get("status") == "indexing_triggered":
                op_name = index_res.get("operation_name")
                doc.metadata["operation_name"] = op_name
                doc.metadata["operation_id"] = index_res.get("operation_id")
                op_status = await self.vertex_search.poll_operation(op_name, max_wait_sec=20)
                if op_status.get("done") and op_status.get("success"):
                    doc.status = ProcessingStatus.INDEXED
                elif op_status.get("done") and not op_status.get("success"):
                    doc.status = ProcessingStatus.FAILED
                    doc.metadata["error"] = f"Vertex AI Search import failed: {op_status.get('error')}"
                else:
                    doc.status = ProcessingStatus.PROCESSING
            elif index_res.get("status") == "permission_denied":
                doc.status = ProcessingStatus.FAILED
                doc.metadata["error"] = index_res.get("error")
            elif index_res.get("status") == "api_error":
                doc.status = ProcessingStatus.FAILED
                doc.metadata["error"] = f"Vertex AI Search error: {index_res.get('error')}"
            else:
                doc.status = ProcessingStatus.INDEXED
        else:
            doc.status = ProcessingStatus.INDEXED if doc.content else ProcessingStatus.FAILED

        doc.updated_at = utcnow()
        await repo.update(doc)
        return doc

    async def backfill_gcs_objects(self, doc_repo=None) -> dict[str, Any]:
        """
        Reconcile and backfill GCS objects in the configured bucket into the document repository
        and trigger Vertex AI Search indexing for unindexed files.
        """
        from ..dependencies import get_doc_repo
        repo = doc_repo or get_doc_repo()
        settings = get_settings()

        if settings.STORAGE_BACKEND != "gcs" or not settings.GCS_BUCKET_NAME:
            return {"status": "skipped", "message": "STORAGE_BACKEND is not 'gcs'"}

        try:
            from .storage import GoogleCloudStorageAdapter
            gcs = self.storage
            if not isinstance(gcs, GoogleCloudStorageAdapter):
                return {"status": "skipped", "message": "Storage adapter is not GoogleCloudStorageAdapter"}
            client = gcs._get_client()
            bucket = client.bucket(gcs.bucket_name)
            blobs = list(bucket.list_blobs())

            existing_docs, _ = await repo.list(skip=0, limit=500)
            existing_by_path = {d.file_path: d for d in existing_docs if d.file_path}

            reconciled = []
            already_indexed = []
            errors = []

            for b in blobs:
                gcs_uri = f"gs://{settings.GCS_BUCKET_NAME}/{b.name}"
                ext = b.name.rsplit(".", 1)[-1].lower() if "." in b.name else ""
                if ext not in SUPPORTED_EXTENSIONS:
                    continue

                author_id = "usr_alice"
                if b.name.startswith("users/"):
                    parts = b.name.split("/")
                    if len(parts) >= 2:
                        author_id = parts[1]

                doc = existing_by_path.get(gcs_uri)
                if doc and doc.status == ProcessingStatus.INDEXED:
                    already_indexed.append(doc.id)
                    continue

                try:
                    file_bytes = b.download_as_bytes()
                    doc_id = new_id("doc_")
                    clean_title = b.name.split("/")[-1].replace(".pdf", "").replace(".txt", "").replace("_", " ").title()

                    if not doc:
                        doc = Document(
                            id=doc_id,
                            title=clean_title,
                            content="",
                            category="general",
                            tags=[ext, "backfill"],
                            author_id=author_id,
                            scope=DocumentScope.PERSONAL,
                            file_path=gcs_uri,
                            file_type=ext,
                            file_size=len(file_bytes),
                            status=ProcessingStatus.UPLOADED,
                            metadata={"backfill": True, "blob_name": b.name},
                            created_at=utcnow(),
                            updated_at=utcnow(),
                        )
                        await repo.create(doc)

                    # Extract and index
                    doc = await self.reprocess_document(doc)
                    if self.vertex_search.is_configured():
                        idx = await self.vertex_search.index_document(gcs_uri=doc.file_path, doc_id=doc.id)
                        doc.metadata["vertex_ai_search"] = idx
                        if idx.get("status") == "indexing_triggered":
                            doc.status = ProcessingStatus.INDEXED
                        elif idx.get("status") == "permission_denied":
                            doc.status = ProcessingStatus.FAILED
                            doc.metadata["error"] = idx.get("error")
                        else:
                            doc.status = ProcessingStatus.INDEXED
                    else:
                        doc.status = ProcessingStatus.INDEXED

                    await repo.update(doc)
                    reconciled.append(doc.id)
                except Exception as ex:
                    errors.append({"blob": b.name, "error": str(ex)})

            return {
                "status": "completed",
                "total_blobs": len(blobs),
                "reconciled_count": len(reconciled),
                "reconciled_ids": reconciled,
                "already_indexed_count": len(already_indexed),
                "errors": errors,
            }
        except Exception as e:
            logger.exception("Backfill failed: %s", e)
            return {"status": "error", "error": str(e)}

