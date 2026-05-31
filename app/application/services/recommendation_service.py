from typing import Any, Dict, List, Optional

from app.domain.entities.post import Post
from app.domain.entities.profile import Profile
from app.infrastructure.analysis.sentiment_analyzer import SentimentAnalyzer
from app.infrastructure.analysis.text_analyzer import TextAnalyzer


class RecommendationService:
    def __init__(self) -> None:
        self.text_analyzer = TextAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.rust_keywords = [
            "rust",
            "ownership",
            "borrow checker",
            "unsafe",
            "tokio",
            "async",
            "cargo",
        ]
        self.cpp_keywords = [
            "c++",
            "cpp",
            "smart pointers",
            "templates",
            "move semantics",
            "raii",
            "std::",
        ]

    def _analyze_historical_performance(self, posts: List[Post]) -> Dict[str, Any]:
        if not posts:
            return {
                "top_themes": ["technical_deep_dive"],
                "best_tone": "pragmatic_balance",
                "avg_engagement": 0.0,
            }

        scored_posts: List[Dict[str, Any]] = []
        for post in posts:
            engagement = (
                (post.like_count or 0)
                + (post.comment_count or 0) * 3
                + (post.repost_count or 0) * 2
            )
            if post.content and len(post.content) > 50:
                themes = self.text_analyzer.detect_themes(
                    post.content, getattr(post, "comments", None)
                )
                sentiment = self.sentiment_analyzer.analyze(
                    post.content, getattr(post, "comments", None)
                )
                score = engagement * (
                    1 + sentiment.get("pragmatic", 0) - sentiment.get("tribalism", 0) * 0.5
                )
                scored_posts.append(
                    {
                        "themes": themes,
                        "sentiment": sentiment,
                        "score": score,
                        "content": post.content[:300],
                    }
                )

        if not scored_posts:
            return {
                "top_themes": ["technical_deep_dive"],
                "best_tone": "pragmatic_balance",
                "avg_engagement": 0.0,
            }

        scored_posts.sort(key=lambda x: x["score"], reverse=True)
        top = scored_posts[:5]

        theme_counts: Dict[str, int] = {}
        for p in top:
            for t in p["themes"]:
                theme_counts[t] = theme_counts.get(t, 0) + 1

        top_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        best_tone = "pragmatic_balance"
        if top and top[0]["sentiment"].get("pragmatic", 0) > 0.3:
            best_tone = "pragmatic_balance"
        elif top and top[0]["sentiment"].get("technical_score", 0) > 0.3:
            best_tone = "technical_deep_dive"

        avg_eng = sum(p["score"] for p in top) / len(top) if top else 0

        return {
            "top_themes": [t[0] for t in top_themes],
            "best_tone": best_tone,
            "avg_engagement": round(avg_eng, 1),
        }

    def _detect_domain(self, profile: Optional[Profile], posts: List[Post]) -> str:
        text = ""
        if profile:
            text += (profile.headline or "") + " " + (profile.about or "")
        for p in posts[:5]:
            text += " " + (p.content or "")

        text_lower = text.lower()
        rust_score = sum(1 for k in self.rust_keywords if k in text_lower)
        cpp_score = sum(1 for k in self.cpp_keywords if k in text_lower)

        if rust_score > cpp_score:
            return "rust"
        elif cpp_score > rust_score:
            return "cpp"
        return "systems"

    def generate_next_post_plan(
        self, historical_posts: List[Post], profile: Optional[Profile] = None
    ) -> Dict[str, Any]:
        perf = self._analyze_historical_performance(historical_posts)
        domain = self._detect_domain(profile, historical_posts)

        top_themes = perf["top_themes"]
        best_tone = perf["best_tone"]

        if domain == "rust":
            topic = (
                "How Rust's ownership model eliminates entire classes of bugs "
                "that still plague modern C++ codebases"
            )
            structure = [
                "Hook with a real production incident",
                "Ownership rules explained with code comparison",
                "Common C++ footguns that Rust prevents",
                "Performance numbers from real projects",
                "Migration lessons and tooling recommendations",
                "Actionable checklist for teams",
            ]
            hook = (
                "We spent three weeks chasing a use-after-free in production. "
                "The fix in Rust would have been impossible to write."
            )
            length = 1650
        elif domain == "cpp":
            topic = (
                "Modern C++ techniques that deliver Rust-level safety "
                "without forcing a full rewrite"
            )
            structure = [
                "The real cost of memory safety bugs in 2025",
                "RAII + smart pointers patterns done right",
                "Compile-time checks that catch 80% of issues",
                "When to reach for Rust vs staying in C++",
                "Refactoring playbook with before/after",
                "Tooling stack that makes C++ bearable",
            ]
            hook = (
                "Your C++ team is shipping faster than the Rust team next door. "
                "Here's exactly how they're doing it."
            )
            length = 1550
        else:
            topic = "Systems programming in 2025: When to choose Rust, when to double down on C++"
            structure = [
                "Current state of memory safety in production systems",
                "Real performance and safety tradeoffs from shipping code",
                "Team velocity impact of each language choice",
                "Interoperability strategies that actually work",
                "Decision framework for new projects",
                "30-day experiment plan",
            ]
            hook = (
                "After shipping both Rust and C++ services at scale, "
                "the answer isn't what most engineering blogs claim."
            )
            length = 1400

        plan = {
            "topic": topic,
            "tone": best_tone,
            "structure": structure,
            "hook": hook,
            "recommended_length": length,
            "why_it_works": (
                f"Historical data shows {best_tone} tone with "
                f"{top_themes[0] if top_themes else 'technical'} themes "
                "drives the highest engagement in this domain."
            ),
            "key_sections": [
                "Strong real-world example in first 200 words",
                "Code comparison blocks (Rust vs C++ where relevant)",
                "Actionable takeaways in the final 15%",
                "One contrarian but evidence-backed opinion",
            ],
            "domain": domain,
            "predicted_engagement_lift": round(perf["avg_engagement"] * 0.12, 1),
        }

        return plan
