import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from app.infrastructure.database.base import Base
from app.infrastructure.database.repositories.profile_repository_impl import SQLProfileRepository
from app.infrastructure.database.repositories.post_repository_impl import SQLPostRepository
from app.domain.entities.profile import Profile
from app.domain.entities.post import Post, Comment
from pydantic import HttpUrl
from datetime import datetime

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(element, compiler, **kw):
    return "JSON"


@compiles(Vector, "sqlite")
def _compile_vector_sqlite(element, compiler, **kw):
    return "TEXT"

@pytest_asyncio.fixture
async def async_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(async_engine):
    async_session = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session

@pytest_asyncio.fixture
async def profile_repo(db_session):
    return SQLProfileRepository(db_session)

@pytest_asyncio.fixture
async def post_repo(db_session):
    return SQLPostRepository(db_session)

@pytest.mark.asyncio
async def test_profile_crud(profile_repo):
    profile = Profile(
        linkedin_url=HttpUrl("https://www.linkedin.com/in/test-rust-cpp"),
        full_name="Alex Rivera",
        headline="Systems Programming | Rust & C++",
        about="Shipping high performance infrastructure.",
        follower_count=48000,
    )

    saved = await profile_repo.save(profile)
    assert saved.id is not None
    assert saved.full_name == "Alex Rivera"

    fetched = await profile_repo.get_by_id(saved.id)
    assert fetched is not None
    assert str(fetched.linkedin_url) == "https://www.linkedin.com/in/test-rust-cpp"

    by_url = await profile_repo.get_by_url("https://www.linkedin.com/in/test-rust-cpp")
    assert by_url is not None
    assert by_url.id == saved.id

    recent = await profile_repo.list_recent(limit=5)
    assert len(recent) >= 1

    saved.about = "Updated bio for testing."
    updated = await profile_repo.update(saved)
    assert updated.about == "Updated bio for testing."

    deleted = await profile_repo.delete(saved.id)
    assert deleted is True

    after_delete = await profile_repo.get_by_id(saved.id)
    assert after_delete is None

@pytest.mark.asyncio
async def test_post_crud(post_repo, profile_repo):
    profile = Profile(
        linkedin_url=HttpUrl("https://www.linkedin.com/in/test-seed-profile"),
        full_name="Seed Profile",
        headline="Rust vs C++",
    )
    saved_profile = await profile_repo.save(profile)

    post = Post(
        profile_id=saved_profile.id,
        linkedin_post_id="rust-ownership-test",
        content="The borrow checker is a superpower.",
        post_type="text",
        like_count=1240,
        comment_count=187,
        repost_count=92,
        posted_at=datetime(2025, 1, 12),
    )

    saved_post = await post_repo.save(post)
    assert saved_post.id is not None
    assert saved_post.like_count == 1240

    fetched = await post_repo.get_by_id(saved_post.id)
    assert fetched is not None
    assert fetched.content == "The borrow checker is a superpower."

    by_profile = await post_repo.get_by_profile_id(saved_profile.id, limit=10)
    assert len(by_profile) >= 1

    with_analysis = await post_repo.list_posts_with_analysis(saved_profile.id, limit=5)
    assert len(with_analysis) >= 1

    training_posts = await post_repo.get_posts_for_training(limit=10)
    assert len(training_posts) >= 1

    many_posts = [
        Post(
            profile_id=saved_profile.id,
            linkedin_post_id=f"bulk-post-{i}",
            content=f"Test post number {i} about Rust and C++ tradeoffs.",
            like_count=100 * i,
            comment_count=10 * i,
        )
        for i in range(3)
    ]
    saved_many = await post_repo.save_many(many_posts)
    assert len(saved_many) == 3

    deleted_count = await post_repo.delete_by_profile(saved_profile.id)
    assert deleted_count >= 4

    remaining = await post_repo.get_by_profile_id(saved_profile.id)
    assert len(remaining) == 0
