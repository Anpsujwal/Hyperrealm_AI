"""
Tests verifying idempotent database seeding and repeated application startups with SQLite.
"""
from __future__ import annotations

import os
import tempfile
import pytest
import pytest_asyncio

from backend.app.dependencies import init_repositories, get_user_repo, get_dept_repo
from backend.app.models import UserProfile, UserRole, UserStatus, utcnow
from backend.app.seed import seed_all


@pytest.mark.asyncio
async def test_seed_all_fresh_sqlite_db():
    """Verify seeding succeeds on a completely fresh SQLite database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "fresh.db")
        os.environ["REPOSITORY_BACKEND"] = "sqlite"
        os.environ["SQLITE_DB_PATH"] = db_path

        init_repositories("sqlite", force=True)
        await seed_all()

        user_repo = get_user_repo()
        users, count = await user_repo.list(limit=50)
        assert count == 11

        emails = [u.email for u in users]
        assert len(emails) == len(set(emails)), "All user emails must be unique"
        assert "ayesha.hussain@hyperrealm.io" in emails

        admin = await user_repo.get_by_email("ayesha.hussain@hyperrealm.io")
        assert admin is not None
        assert admin.role == UserRole.ADMIN


@pytest.mark.asyncio
async def test_seed_all_repeated_startup_succeeds():
    """Verify that startup and seed_all succeed safely when repeated on an already seeded database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "repeat.db")
        os.environ["REPOSITORY_BACKEND"] = "sqlite"
        os.environ["SQLITE_DB_PATH"] = db_path

        init_repositories("sqlite", force=True)
        # First startup
        await seed_all()

        user_repo = get_user_repo()
        _, count_first = await user_repo.list(limit=50)

        # Second startup simulation
        await seed_all()
        _, count_second = await user_repo.list(limit=50)

        assert count_first == count_second == 11


@pytest.mark.asyncio
async def test_seed_all_preserves_preexisting_users():
    """Verify that existing users and their data are preserved, and missing users are populated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "preserve.db")
        os.environ["REPOSITORY_BACKEND"] = "sqlite"
        os.environ["SQLITE_DB_PATH"] = db_path

        init_repositories("sqlite", force=True)
        user_repo = get_user_repo()

        # Pre-insert existing user Bob with custom job title and skills
        preexisting_bob = UserProfile(
            id="usr_bob",
            email="bob.harris@hyperrealm.io",
            name="Bob Harris Custom",
            role=UserRole.TECHNICAL_LEAD,
            department_id="dept_engineering",
            department_name="Engineering",
            job_title="Distinguished Tech Lead",
            hashed_password="custom_hashed_pw",
            skills=["Custom Skill A", "Custom Skill B"],
            status=UserStatus.ACTIVE,
            created_at=utcnow(),
        )
        await user_repo.create(preexisting_bob)

        # Run seed_all
        await seed_all()

        bob_after = await user_repo.get("usr_bob")
        assert bob_after is not None
        assert bob_after.name == "Bob Harris Custom"
        assert bob_after.job_title == "Distinguished Tech Lead"
        assert "Custom Skill A" in bob_after.skills

        # Other seed users should also have been seeded
        alice = await user_repo.get_by_email("ayesha.hussain@hyperrealm.io")
        assert alice is not None
