import asyncio
from datetime import datetime

from sqlalchemy import select

from app.infrastructure.database.session import get_async_session
from app.infrastructure.database.models import ProfileModel, PostModel

RUST_VS_CPP_POSTS = [
    {
        "linkedin_post_id": "7466201982324899840",
        "url": "https://www.linkedin.com/feed/update/urn:li:activity:7466201982324899840/",
        "content": "I owe the C and C++ crowd a more honest post. I've been the Rust guy swinging too hard lately. Honestly, it depends on the context and there are tradeoffs both ways.",
        "like_count": 245,
        "comment_count": 34,
        "repost_count": 12,
        "posted_at": datetime(2026, 5, 28, 14, 30),
        "comments": [
            {"text": "Refreshing to see a balanced take, thanks for the honesty.", "author": "Dev A", "like_count": 14, "quality_score": 0.78},
            {"text": "This is the nuance the community needs.", "author": "Dev B", "like_count": 9, "quality_score": 0.71},
        ],
        "sentiment": {
            "neg": 0.06, "neu": 0.62, "pos": 0.32, "compound": 0.65,
            "pragmatic": 0.82, "tribalism": 0.05, "technical_score": 0.18,
        },
        "theme_analysis": {
            "themes": ["pragmatic_balance", "personal_story"],
            "polarization_score": 0.18,
            "theme_count": 2,
        },
    },
    {
        "linkedin_post_id": "7465859462038343681",
        "url": "https://www.linkedin.com/feed/update/urn:li:activity:7465859462038343681/",
        "content": "Real story from building Ferrous: the mining loop held a read lock too long, causing reader starvation. Classic latency vs throughput tradeoff in a concurrency-heavy path.",
        "like_count": 189,
        "comment_count": 28,
        "repost_count": 8,
        "posted_at": datetime(2026, 5, 27, 11, 15),
        "comments": [
            {"text": "Great deep dive, the lock contention breakdown is gold.", "author": "Dev C", "like_count": 21, "quality_score": 0.88},
            {"text": "Did you consider an RwLock with a fairness policy?", "author": "Dev D", "like_count": 16, "quality_score": 0.84},
        ],
        "sentiment": {
            "neg": 0.04, "neu": 0.61, "pos": 0.35, "compound": 0.71,
            "pragmatic": 0.52, "tribalism": 0.04, "technical_score": 0.85,
        },
        "theme_analysis": {
            "themes": ["technical_deep_dive", "pragmatic_balance"],
            "polarization_score": 0.15,
            "theme_count": 2,
        },
    },
    {
        "linkedin_post_id": "7457857247646269441",
        "url": "https://www.linkedin.com/feed/update/urn:li:activity:7457857247646269441/",
        "content": "C++ is not modern, it's just decorated legacy. Anyone who disagrees is obviously wrong and those people are sheep clinging to the past.",
        "like_count": 312,
        "comment_count": 67,
        "repost_count": 24,
        "posted_at": datetime(2026, 5, 20, 9, 45),
        "comments": [
            {"text": "Hard disagree, this is just tribalism.", "author": "Dev E", "like_count": 41, "quality_score": 0.55},
            {"text": "Modern C++ is nothing like this strawman!", "author": "Dev F", "like_count": 38, "quality_score": 0.48},
        ],
        "sentiment": {
            "neg": 0.31, "neu": 0.49, "pos": 0.20, "compound": -0.42,
            "pragmatic": 0.05, "tribalism": 0.72, "technical_score": 0.30,
        },
        "theme_analysis": {
            "themes": ["critique", "tribalism"],
            "polarization_score": 0.78,
            "theme_count": 2,
        },
    },
    {
        "linkedin_post_id": "7455012398761234560",
        "url": "https://www.linkedin.com/feed/update/urn:li:activity:7455012398761234560/",
        "content": "When I was a junior engineer, a senior dev told me memory safety was 'just a skill issue'. Years later, after a 2am production page from a dangling pointer, I learned the humbling truth: tooling beats discipline every time.",
        "like_count": 421,
        "comment_count": 53,
        "repost_count": 31,
        "posted_at": datetime(2026, 5, 18, 8, 20),
        "comments": [
            {"text": "This hit home, lived the exact same 2am page.", "author": "Dev G", "like_count": 33, "quality_score": 0.81},
            {"text": "Tooling beats discipline is the quote of the year.", "author": "Dev H", "like_count": 27, "quality_score": 0.74},
        ],
        "sentiment": {
            "neg": 0.08, "neu": 0.58, "pos": 0.34, "compound": 0.58,
            "pragmatic": 0.66, "tribalism": 0.10, "technical_score": 0.45,
        },
        "theme_analysis": {
            "themes": ["personal_story", "pragmatic_balance"],
            "polarization_score": 0.22,
            "theme_count": 2,
        },
    },
    {
        "linkedin_post_id": "7452888776655443201",
        "url": "https://www.linkedin.com/feed/update/urn:li:activity:7452888776655443201/",
        "content": "Refactoring a 200k-line C++ codebase to be exception-safe: a pragmatic, incremental migration playbook. Strangler-fig pattern, test coverage gates, and regression budgets so you never block the team.",
        "like_count": 167,
        "comment_count": 19,
        "repost_count": 14,
        "posted_at": datetime(2026, 5, 12, 16, 5),
        "comments": [
            {"text": "Bookmarking this, the regression budget idea is brilliant.", "author": "Dev I", "like_count": 12, "quality_score": 0.79},
            {"text": "How do you handle ABI breaks mid-migration?", "author": "Dev J", "like_count": 8, "quality_score": 0.83},
        ],
        "sentiment": {
            "neg": 0.03, "neu": 0.70, "pos": 0.27, "compound": 0.62,
            "pragmatic": 0.74, "tribalism": 0.03, "technical_score": 0.80,
        },
        "theme_analysis": {
            "themes": ["refactoring_safety", "technical_deep_dive", "pragmatic_balance"],
            "polarization_score": 0.12,
            "theme_count": 3,
        },
    },
    {
        "linkedin_post_id": "7450123445566778880",
        "url": "https://www.linkedin.com/feed/update/urn:li:activity:7450123445566778880/",
        "content": "Hot take: if your HFT matching engine is still in C++, you're leaving microseconds on the table. Real engineers benchmark; everyone else argues on LinkedIn. The order book never lies.",
        "like_count": 288,
        "comment_count": 74,
        "repost_count": 9,
        "posted_at": datetime(2026, 5, 5, 13, 40),
        "comments": [
            {"text": "Strong claim, where are the numbers?", "author": "Dev K", "like_count": 45, "quality_score": 0.52},
            {"text": "This is just rage bait, latency depends on the whole stack.", "author": "Dev L", "like_count": 39, "quality_score": 0.49},
        ],
        "sentiment": {
            "neg": 0.18, "neu": 0.57, "pos": 0.25, "compound": 0.10,
            "pragmatic": 0.12, "tribalism": 0.58, "technical_score": 0.70,
        },
        "theme_analysis": {
            "themes": ["hft_embedded", "tribalism", "technical_deep_dive"],
            "polarization_score": 0.66,
            "theme_count": 3,
        },
    },
]


async def seed():
    async with get_async_session() as db:
        existing_profile = (
            await db.execute(
                select(ProfileModel).where(
                    ProfileModel.linkedin_url == "https://www.linkedin.com/in/altug"
                )
            )
        ).scalar_one_or_none()

        if existing_profile:
            profile = existing_profile
        else:
            profile = ProfileModel(
                linkedin_url="https://www.linkedin.com/in/altug",
                full_name="Altug",
                headline="Systems Programming | Rust & C++",
                about="Building high performance systems. Honest takes on Rust vs C++.",
                follower_count=25000,
            )
            db.add(profile)
            await db.flush()

        for p in RUST_VS_CPP_POSTS:
            existing = (
                await db.execute(
                    select(PostModel).where(
                        PostModel.linkedin_post_id == p["linkedin_post_id"]
                    )
                )
            ).scalar_one_or_none()
            if existing:
                continue
            post = PostModel(
                profile_id=profile.id,
                linkedin_post_id=p["linkedin_post_id"],
                content=p["content"],
                post_type="text",
                like_count=p["like_count"],
                comment_count=p["comment_count"],
                repost_count=p["repost_count"],
                posted_at=p["posted_at"],
                comments=p["comments"],
                raw_data={
                    "url": p["url"],
                    "sentiment": p["sentiment"],
                    "theme_analysis": p["theme_analysis"],
                },
                sentiment_score=p["sentiment"]["compound"],
            )
            db.add(post)
        await db.commit()
        print("Rust vs C++ seed data inserted successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
