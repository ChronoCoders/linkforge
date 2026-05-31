from datetime import datetime

import pytest
from pydantic import HttpUrl

from app.domain.entities.post import Post
from app.domain.entities.profile import Profile
from app.infrastructure.database.repositories.post_repository_impl import SQLPostRepository
from app.infrastructure.database.repositories.profile_repository_impl import SQLProfileRepository


@pytest.mark.asyncio
async def test_profile_crud(profile_repo: SQLProfileRepository) -> None:
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
async def test_post_crud(post_repo: SQLPostRepository, profile_repo: SQLProfileRepository) -> None:
    profile = Profile(
        linkedin_url=HttpUrl("https://www.linkedin.com/in/test-seed-profile"),
        full_name="Seed Profile",
        headline="Rust vs C++",
    )
    saved_profile = await profile_repo.save(profile)
    assert saved_profile.id is not None

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
