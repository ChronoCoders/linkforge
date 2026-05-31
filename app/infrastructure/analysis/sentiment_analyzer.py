import re
from collections import Counter
from typing import Any, ClassVar, Dict, List, Optional

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class SentimentAnalyzer:
    _analyzer: SentimentIntensityAnalyzer | None = None

    PRAGMATIC_TERMS: ClassVar[list[str]] = [
        "depends",
        "tradeoff",
        "tradeoffs",
        "trade-off",
        "trade-offs",
        "context",
        "nuance",
        "nuanced",
        "however",
        "balanced",
        "balance",
        "pragmatic",
        "reasonable",
        "fair",
        "honest",
        "both",
        "it depends",
        "that said",
        "to be fair",
        "on the other hand",
        "in practice",
        "case by case",
        "context matters",
        "middle ground",
    ]
    TRIBALISM_TERMS: ClassVar[list[str]] = [
        "always",
        "never",
        "obviously",
        "everyone",
        "nobody",
        "cult",
        "brainwashed",
        "sheep",
        "idiots",
        "clowns",
        "morons",
        "stupid",
        "dumb",
        "trash",
        "garbage",
        "superior",
        "inferior",
        "haters",
        "fanboys",
        "zealots",
        "those people",
        "everyone knows",
        "anyone who",
        "real engineers",
        "real programmers",
    ]
    TECHNICAL_TERMS: ClassVar[list[str]] = [
        "implementation",
        "architecture",
        "algorithm",
        "complexity",
        "benchmark",
        "latency",
        "throughput",
        "optimization",
        "memory",
        "compiler",
        "concurrency",
        "performance",
        "thread",
        "allocation",
        "profiling",
        "ownership",
        "borrow",
        "pointer",
        "kernel",
        "async",
        "lock",
    ]

    def _load(self) -> SentimentIntensityAnalyzer:
        if SentimentAnalyzer._analyzer is None:
            SentimentAnalyzer._analyzer = SentimentIntensityAnalyzer()
        return SentimentAnalyzer._analyzer

    def _density(
        self, lowered: str, word_counts: "Counter[str]", n: int, keywords: List[str]
    ) -> float:
        hits = 0
        for kw in keywords:
            if " " in kw or "-" in kw:
                hits += lowered.count(kw)
            else:
                hits += word_counts.get(kw, 0)
        return hits / n

    def _lexical_dimensions(self, text: str, vader: Dict[str, float]) -> Dict[str, float]:
        lowered = text.lower()
        words = re.findall(r"[a-z0-9'+#]+", lowered)
        n = max(len(words), 1)
        word_counts = Counter(words)
        compound = vader.get("compound", 0.0)

        pragmatic = self._density(lowered, word_counts, n, self.PRAGMATIC_TERMS) * 10
        tribalism = self._density(lowered, word_counts, n, self.TRIBALISM_TERMS) * 10
        technical = self._density(lowered, word_counts, n, self.TECHNICAL_TERMS) * 10

        exclamations = text.count("!")
        shouty = sum(1 for w in text.split() if len(w) > 3 and w.isupper())
        tribalism += min(exclamations * 0.05 + shouty * 0.08, 0.4)
        tribalism += max(0.0, abs(compound) - 0.6) * 0.5

        if abs(compound) < 0.5:
            pragmatic += vader.get("neu", 0.0) * 0.2

        return {
            "pragmatic": round(min(pragmatic, 1.0), 4),
            "tribalism": round(min(tribalism, 1.0), 4),
            "technical_score": round(min(technical, 1.0), 4),
        }

    def analyze(
        self, text: str, comments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, float]:
        combined = text or ""
        if comments:
            combined += " " + " ".join(c.get("text", "") for c in comments if isinstance(c, dict))
        combined = combined.strip()
        if not combined:
            return {
                "neg": 0.0,
                "neu": 1.0,
                "pos": 0.0,
                "compound": 0.0,
                "pragmatic": 0.0,
                "tribalism": 0.0,
                "technical_score": 0.0,
            }
        analyzer = self._load()
        scores = dict(analyzer.polarity_scores(combined))
        scores.update(self._lexical_dimensions(combined, scores))
        return scores
