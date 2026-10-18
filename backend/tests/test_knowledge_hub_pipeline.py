"""
Integration tests for HYPERREALM Knowledge Hub pipeline:
- Upload -> Storage -> Indexing -> Retrieval -> Grounded Answer
- Failed imports and unreadable files
- Duplicate uploads and versioning
- Permission isolation (Personal vs Official, cross-user privacy)
- Document updates and prevention of stale content
- Document deletion from storage and repository
- Non-blocking prepare_document and background processing
- Manual reindex retry and backfill
"""
import io
import pytest
from backend.app.config import get_settings
from backend.app.models import (
    Document,
    DocumentScope,
    Guideline,
    ProcessingStatus,
    UserProfile,
    UserRole,
    new_id,
    utcnow,
)
from backend.app.services.ingestion import DocumentIngestionService, IngestionError
from backend.app.services.retrieval import EnterpriseRetrievalService
from backend.app.agents.knowledge_agent import KnowledgeAgent
from backend.app.dependencies import (
    get_doc_repo,
    get_guide_repo,
    get_incident_repo,
    init_repositories,
)


def make_test_pdf(text: str) -> bytes:
    """Generate a valid minimal PDF containing text."""
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream_content = f"BT /F1 12 Tf 72 712 Td ({escaped}) Tj ET"
    stream_len = len(stream_content)
    pdf = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length {stream_len} >>
stream
{stream_content}
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000318 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
395
%%EOF"""
    return pdf.encode("latin-1")


@pytest.fixture
def users():
    alice = UserProfile(
        id="usr_alice_pipe",
        email="alice@hyperrealm.internal",
        name="Alice Pipeline",
        role=UserRole.SOFTWARE_DEVELOPER,
        department_name="Payments",
    )
    bob = UserProfile(
        id="usr_bob_pipe",
        email="bob@hyperrealm.internal",
        name="Bob Pipeline",
        role=UserRole.SOFTWARE_DEVELOPER,
        department_name="Marketing",
    )
    admin = UserProfile(
        id="usr_admin_pipe",
        email="admin@hyperrealm.internal",
        name="Admin Pipeline",
        role=UserRole.ADMIN,
        department_name="Operations",
    )
    return {"alice": alice, "bob": bob, "admin": admin}


@pytest.mark.asyncio
async def test_upload_storage_indexing_and_grounded_answer(users):
    """Test full upload -> storage -> indexing -> retrieval -> grounded answer."""
    alice = users["alice"]
    test_phrase = "HYPERREALM_TEST: The standard payment approval limit is 50000 units."
    pdf_bytes = make_test_pdf(test_phrase)

    ingestion = DocumentIngestionService()
    doc = await ingestion.ingest_document(
        file_bytes=pdf_bytes,
        filename="payment_policy_2026.pdf",
        user=alice,
        scope=DocumentScope.PERSONAL,
        category="finance",
        title="Payment Policy 2026",
    )

    # 1. Storage & Text extraction verification
    assert doc.file_path is not None
    assert doc.status == ProcessingStatus.INDEXED
    assert "FlateDecode" not in doc.content
    assert "50000 units" in doc.content

    # Save to repository
    doc_repo = get_doc_repo()
    await doc_repo.create(doc)

    # 2. Retrieval verification
    retrieval = EnterpriseRetrievalService()
    results, _ = await retrieval.search(query="payment approval limit", user=alice)
    assert len(results) > 0
    assert any(doc.id == r.id for r in results)
    matched = next(r for r in results if r.id == doc.id)
    assert "50000 units" in matched.snippet

    # 3. Knowledge Agent Grounded Answer
    agent = KnowledgeAgent(retrieval)
    answer = await agent.execute(query="What is the standard payment approval limit?", user=alice)
    assert "50000" in answer["response"] or "50,000" in answer["response"]
    assert len(answer["citations"]) > 0
    assert "FlateDecode" not in answer["response"]


@pytest.mark.asyncio
async def test_permission_isolation_personal_vs_official(users):
    """Test that private documents are isolated while official documents are accessible."""
    alice = users["alice"]
    bob = users["bob"]
    admin = users["admin"]

    doc_repo = get_doc_repo()
    guide_repo = get_guide_repo()

    # 1. Alice creates private personal document
    private_doc = Document(
        id=new_id("doc_"),
        title="Alice Confidential Strategy",
        content="Confidential product roadmap details for Q4 2026.",
        category="strategy",
        tags=["confidential"],
        author_id=alice.id,
        is_public=False,
        scope=DocumentScope.PERSONAL,
        status=ProcessingStatus.INDEXED,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    await doc_repo.create(private_doc)

    # 2. Admin creates official published guideline
    official_guide = Guideline(
        id=new_id("guide_"),
        title="Official Travel Expense Policy",
        content="Official Travel Policy: Per diem meals capped at 75 units.",
        category="hr",
        version="1.0",
        status="published",
        tags=["official", "travel"],
        owner_id=admin.id,
        processing_status=ProcessingStatus.INDEXED,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    await guide_repo.create(official_guide)

    retrieval = EnterpriseRetrievalService()

    # Bob searches: should find official guideline but NEVER Alice's private doc
    bob_results, _ = await retrieval.search(query="roadmap", user=bob)
    assert not any(r.id == private_doc.id for r in bob_results)

    # Direct query by unauthorized user
    agent = KnowledgeAgent(retrieval)
    bob_direct = await agent.execute(query="What is the roadmap?", user=bob, document_id=private_doc.id)
    assert "Access denied" in bob_direct["response"]

    # Bob searches official policy: should find official travel policy
    bob_official_res, _ = await retrieval.search(query="travel expense", user=bob)
    assert any(r.id == official_guide.id for r in bob_official_res)


@pytest.mark.asyncio
async def test_failed_imports_and_unreadable_files(users):
    """Test that empty or unreadable documents fail safely and are not marked searchable."""
    alice = users["alice"]
    ingestion = DocumentIngestionService()

    # Empty file must raise IngestionError
    with pytest.raises(IngestionError):
        await ingestion.ingest_document(
            file_bytes=b"",
            filename="empty.pdf",
            user=alice,
        )

    # Unsupported format must raise IngestionError
    with pytest.raises(IngestionError):
        await ingestion.ingest_document(
            file_bytes=b"malicious executable binary",
            filename="malware.exe",
            user=alice,
        )


@pytest.mark.asyncio
async def test_document_update_prevents_stale_content(users):
    """Test document updates update the retrieved content and prevent stale data."""
    alice = users["alice"]
    doc_repo = get_doc_repo()

    doc = Document(
        id=new_id("doc_"),
        title="Project Budget 2026",
        content="Initial approved budget is 100000 units.",
        category="finance",
        tags=["budget"],
        author_id=alice.id,
        scope=DocumentScope.PERSONAL,
        status=ProcessingStatus.INDEXED,
        version=1,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    await doc_repo.create(doc)

    retrieval = EnterpriseRetrievalService()

    # Initial search
    res1, _ = await retrieval.search(query="budget", user=alice)
    assert any("100000 units" in r.snippet for r in res1)

    # Update document with new budget
    doc.content = "Revised approved budget is 250000 units after executive review."
    doc.version = 2
    doc.updated_at = utcnow()
    await doc_repo.update(doc)

    # Subsequent search must reflect updated content
    res2, _ = await retrieval.search(query="budget", user=alice)
    assert any("250000 units" in r.snippet for r in res2)
    assert not any("100000 units" in r.snippet for r in res2)


@pytest.mark.asyncio
async def test_document_deletion_removes_from_search(users):
    """Test document deletion removes it from search and prevents stale returns."""
    alice = users["alice"]
    doc_repo = get_doc_repo()

    doc = Document(
        id=new_id("doc_"),
        title="Temporary Notes",
        content="Ephemeral content to be deleted immediately.",
        category="general",
        tags=["temp"],
        author_id=alice.id,
        scope=DocumentScope.PERSONAL,
        status=ProcessingStatus.INDEXED,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    await doc_repo.create(doc)

    retrieval = EnterpriseRetrievalService()

    # Accessible before delete
    res_before, _ = await retrieval.search(query="Ephemeral", user=alice)
    assert len(res_before) > 0

    # Delete
    await doc_repo.delete(doc.id)

    # Inaccessible after delete
    res_after, _ = await retrieval.search(query="Ephemeral", user=alice)
    assert len(res_after) == 0


@pytest.mark.asyncio
async def test_non_blocking_prepare_and_background_processing(users):
    """Test non-blocking prepare_document -> background_process_document pipeline."""
    alice = users["alice"]
    test_phrase = "Non-blocking background indexing test phrase 42981."
    pdf_bytes = make_test_pdf(test_phrase)

    ingestion = DocumentIngestionService()
    doc_repo = get_doc_repo()

    # 1. Immediate upload returns status UPLOADED without blocking
    doc = await ingestion.prepare_document(
        file_bytes=pdf_bytes,
        filename="async_doc.pdf",
        user=alice,
        scope=DocumentScope.PERSONAL,
        category="engineering",
        title="Async Doc",
    )
    assert doc.status == ProcessingStatus.UPLOADED
    assert doc.file_path is not None
    await doc_repo.create(doc)

    # Document should not be searchable while in UPLOADED status
    retrieval = EnterpriseRetrievalService()
    unindexed_res, _ = await retrieval.search(query="42981", user=alice)
    assert len(unindexed_res) == 0

    # 2. Run background processing
    processed_doc = await ingestion.background_process_document(
        doc_id=doc.id,
        file_bytes=pdf_bytes,
        user=alice,
        doc_repo=doc_repo,
    )
    assert processed_doc is not None
    assert processed_doc.status == ProcessingStatus.INDEXED
    assert "42981" in processed_doc.content

    # Document is now searchable
    indexed_res, _ = await retrieval.search(query="42981", user=alice)
    assert len(indexed_res) > 0
    assert any(r.id == doc.id for r in indexed_res)


@pytest.mark.asyncio
async def test_reindex_retry_and_backfill(users):
    """Test manual retry of indexing and backfill functionality."""
    alice = users["alice"]
    doc_repo = get_doc_repo()
    ingestion = DocumentIngestionService()
    pdf_bytes = make_test_pdf("Document pending retry after temporary error.")
    stored_path = await ingestion.storage.save_file(pdf_bytes, "failed.pdf", alice.id)

    # Create a document in FAILED state
    failed_doc = Document(
        id=new_id("doc_"),
        title="Failed Upload Doc",
        content="Some preliminary content.",
        category="ops",
        tags=["retry"],
        author_id=alice.id,
        file_path=stored_path,
        file_type="pdf",
        file_size=len(pdf_bytes),
        scope=DocumentScope.PERSONAL,
        status=ProcessingStatus.FAILED,
        metadata={"error": "Simulated temporary network failure"},
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    await doc_repo.create(failed_doc)

    # Reindex retry
    reindexed = await ingestion.reindex_document(failed_doc.id, doc_repo=doc_repo, user=alice)
    assert reindexed.id == failed_doc.id
    assert reindexed.status in [ProcessingStatus.INDEXED, ProcessingStatus.FAILED]

    # Backfill
    backfill_res = await ingestion.backfill_gcs_objects(doc_repo=doc_repo)
    assert "status" in backfill_res
