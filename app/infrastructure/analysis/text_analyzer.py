from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import numpy as np
from collections import Counter

class TextAnalyzer:
    THEME_KEYWORDS: Dict[str, List[str]] = {
        "tribalism": ["they", "them", "those people", "always", "never", "everyone knows", "cult", "brainwashed", "sheep", "idiots"],
        "personal_story": ["i worked", "when i was", "my experience", "in my team", "i remember", "personally", "my journey"],
        "technical_deep_dive": ["implementation", "architecture", "algorithm", "tradeoff", "complexity", "benchmark", "latency", "throughput", "optimization"],
        "critique": ["broken", "terrible", "awful", "fail", "anti-pattern", "smell", "overengineered", "disaster"],
        "pragmatic_balance": ["depends", "tradeoff", "context matters", "it depends", "balanced view", "nuanced", "however"],
        "hft_embedded": ["hft", "latency", "market data", "order book", "matching engine", "fpga", "colocation", "kernel"],
        "refactoring_safety": ["refactor", "safe", "test coverage", "regression", "strangler", "incremental", "migration"],
    }

    POLARITY_WORDS: Dict[str, List[str]] = {
        "positive": ["excellent", "great", "love", "best", "amazing", "powerful", "elegant"],
        "negative": ["hate", "worst", "broken", "terrible", "awful", "disaster", "pain"],
    }

    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=100, stop_words="english", ngram_range=(1, 2))

    def _normalize(self, text: str) -> str:
        return re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())

    def _calculate_theme_confidence(self, text: str, theme: str, keywords: List[str]) -> float:
        normalized = self._normalize(text)
        words = normalized.split()
        if not words:
            return 0.0
        matches = sum(1 for kw in keywords if kw in normalized)
        density = matches / len(words)
        context_bonus = 0.2 if any(kw in normalized for kw in ["rust", "c++", "performance", "safety"]) else 0.0
        return min(1.0, density * 8 + context_bonus)

    def detect_themes(self, text: str, comments: Optional[List[Dict]] = None) -> List[str]:
        combined = text
        if comments:
            combined += " " + " ".join(c.get("text", "") for c in comments if isinstance(c, dict))
        normalized = self._normalize(combined)
        detected = []
        for theme, keywords in self.THEME_KEYWORDS.items():
            if any(kw in normalized for kw in keywords):
                detected.append(theme)
        return detected or ["general"]

    def detect_themes_with_confidence(self, text: str, comments: Optional[List[Dict]] = None) -> Dict[str, float]:
        combined = text
        if comments:
            combined += " " + " ".join(c.get("text", "") for c in comments if isinstance(c, dict))
        confidences = {}
        for theme, keywords in self.THEME_KEYWORDS.items():
            conf = self._calculate_theme_confidence(combined, theme, keywords)
            if conf > 0.15:
                confidences[theme] = round(conf, 3)
        return confidences or {"general": 0.5}

    def calculate_polarization_score(self, comments: List[Dict[str, Any]]) -> float:
        if not comments or len(comments) < 2:
            return 0.0
        scores = []
        for c in comments:
            text = c.get("text", "") if isinstance(c, dict) else str(c)
            if not text:
                continue
            length = len(text.split())
            question_marks = text.count("?")
            caps = sum(1 for w in text.split() if w.isupper() and len(w) > 3)
            exclamation = text.count("!")
            score = (question_marks * 0.25) + (caps * 0.35) + (exclamation * 0.2) + min(length / 100, 0.8) * 0.2
            scores.append(min(score, 1.0))
        if len(scores) < 2:
            return 0.0
        variance = float(np.var(scores))
        return round(min(variance * 2.8, 1.0), 4)

    def _advanced_polarization(self, text: str, comments: List[Dict]) -> Dict[str, float]:
        base = self.calculate_polarization_score(comments)
        normalized = self._normalize(text)
        polarity_shifts = 0
        for pos in self.POLARITY_WORDS["positive"]:
            if pos in normalized:
                polarity_shifts += 1
        for neg in self.POLARITY_WORDS["negative"]:
            if neg in normalized:
                polarity_shifts += 1
        sentiment_variance = min(len(comments) / 20, 0.4) if comments else 0.0
        advanced_score = min(1.0, base * 0.6 + (polarity_shifts * 0.08) + sentiment_variance)
        return {
            "base_polarization": round(base, 3),
            "polarity_shift_score": round(min(polarity_shifts * 0.1, 0.5), 3),
            "advanced_polarization": round(advanced_score, 3)
        }

    def compare_to_historical(self, current_text: str, historical_posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not historical_posts:
            return {"similarity": 0.0, "trend": "insufficient_data", "delta_polarization": 0.0}
        current_themes = set(self.detect_themes(current_text))
        current_polar = self.calculate_polarization_score([])
        similarities = []
        polar_deltas = []
        for past in historical_posts:
            past_text = past.get("content", "")
            past_themes = set(self.detect_themes(past_text))
            if current_themes and past_themes:
                inter = len(current_themes & past_themes)
                union = len(current_themes | past_themes)
                sim = inter / union if union else 0
                similarities.append(sim)
            past_polar = self.calculate_polarization_score(past.get("comments", []))
            polar_deltas.append(abs(current_polar - past_polar))
        avg_sim = float(np.mean(similarities)) if similarities else 0.0
        avg_delta = float(np.mean(polar_deltas)) if polar_deltas else 0.0
        trend = "increasing_polarization" if avg_delta > 0.15 else "stable"
        return {
            "average_theme_similarity": round(avg_sim, 3),
            "average_polarization_delta": round(avg_delta, 3),
            "trend_direction": trend,
            "historical_posts_analyzed": len(historical_posts)
        }

    def analyze(self, text: str, comments: Optional[List[Dict]] = None, historical_posts: Optional[List[Dict]] = None) -> Dict[str, Any]:
        themes = self.detect_themes(text, comments)
        confidences = self.detect_themes_with_confidence(text, comments)
        polarization = self._advanced_polarization(text, comments or [])
        comparison = self.compare_to_historical(text, historical_posts or []) if historical_posts else {}
        return {
            "themes": themes,
            "theme_confidences": confidences,
            "polarization_score": polarization.get("advanced_polarization", 0.0),
            "polarization_details": polarization,
            "historical_comparison": comparison,
            "theme_count": len(themes)
        }
