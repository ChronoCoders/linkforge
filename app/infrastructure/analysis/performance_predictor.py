from typing import List, Dict, Any
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction import DictVectorizer
from app.domain.entities.post import Post

class PerformancePredictor:
    def __init__(self):
        self.model = None
        self.vectorizer = DictVectorizer()
        self.scaler = StandardScaler()
        self.known_themes = [
            "tribalism", "personal_story", "technical_deep_dive", "critique",
            "pragmatic_balance", "hft_embedded", "refactoring_safety"
        ]
        self.pipeline = None
        self._engagement_mean: float = 0.0
        self._engagement_std: float = 1.0

    def _post_to_features(self, post: Post) -> Dict[str, float]:
        features: Dict[str, float] = {}
        sentiment = getattr(post, "raw_data", {}).get("sentiment", {}) or {}
        features["compound"] = float(sentiment.get("compound", 0.0))
        features["pragmatic"] = float(sentiment.get("pragmatic", 0.0))
        features["tribalism"] = float(sentiment.get("tribalism", 0.0))
        features["technical_score"] = float(sentiment.get("technical_score", 0.0))

        theme_analysis = getattr(post, "raw_data", {}).get("theme_analysis", {}) or {}
        for theme in self.known_themes:
            features[f"theme_{theme}"] = 1.0 if theme in theme_analysis.get("themes", []) else 0.0

        features["polarization"] = float(theme_analysis.get("polarization_score", 0.0))

        comments = getattr(post, "comments", []) or []
        if comments:
            qualities = [c.get("quality_score", 0.0) for c in comments if isinstance(c, dict)]
            features["avg_comment_quality"] = float(np.mean(qualities)) if qualities else 0.0
        else:
            features["avg_comment_quality"] = 0.0

        return features

    def _compute_engagement_score(self, post: Post) -> float:
        likes = float(getattr(post, "like_count", 0) or 0)
        comments = float(getattr(post, "comment_count", 0) or 0)
        reposts = float(getattr(post, "repost_count", 0) or 0)
        score = likes + comments * 3.0 + reposts * 2.0
        return min(score / 500.0, 10.0)

    def train(self, posts: List[Post]) -> None:
        if len(posts) < 5:
            return

        feature_dicts = [self._post_to_features(p) for p in posts]
        X = self.vectorizer.fit_transform(feature_dicts).toarray()
        y = np.array([self._compute_engagement_score(p) for p in posts])

        self.pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("regressor", RandomForestRegressor(n_estimators=100, random_state=42, max_depth=8))
        ])
        self.pipeline.fit(X, y)
        self.model = self.pipeline

        self._engagement_mean = float(y.mean())
        std = float(y.std())
        self._engagement_std = std if std > 1e-6 else 1.0

    def predict_engagement(self, post: Post) -> float:
        if self.pipeline is None:
            return 0.0
        feat = self.vectorizer.transform([self._post_to_features(post)]).toarray()
        pred = self.pipeline.predict(feat)[0]
        return float(max(0.0, min(pred, 10.0)))

    def predict_success_probability(self, post: Post) -> float:
        if self.pipeline is None:
            return 0.5
        engagement = self.predict_engagement(post)
        z = (engagement - self._engagement_mean) / self._engagement_std
        return float(1.0 / (1.0 + np.exp(-z)))

    def generate_recommendations(self, base_sentiment: Dict[str, float], base_themes: List[str], num: int = 3) -> List[Dict[str, Any]]:
        if self.pipeline is None:
            return []

        candidates = []
        tones = ["pragmatic_balance", "technical_deep_dive", "personal_story"]
        for tone in tones:
            for theme in (base_themes + self.known_themes[:4]):
                if theme == tone:
                    continue
                candidate = type("obj", (object,), {
                    "like_count": 0, "comment_count": 0, "repost_count": 0,
                    "comments": [],
                    "raw_data": {
                        "sentiment": {**base_sentiment, "pragmatic": 0.6 if "pragmatic" in tone else base_sentiment.get("pragmatic", 0.3)},
                        "theme_analysis": {"themes": [tone, theme], "polarization_score": 0.15}
                    }
                })()
                eng = self.predict_engagement(candidate)
                prob = self.predict_success_probability(candidate)
                candidates.append({
                    "tone": tone,
                    "theme": theme,
                    "predicted_engagement": round(eng, 2),
                    "success_probability": round(prob, 3),
                    "confidence": round(min(0.95, 0.6 + (eng / 12)), 3)
                })

        candidates.sort(key=lambda x: (x["success_probability"], x["predicted_engagement"]), reverse=True)
        return candidates[:num]
