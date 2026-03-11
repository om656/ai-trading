"""
Keyword Analyzer
================
Identifies which keywords in news articles are most correlated with
profitable trading signals.

Usage
-----
    from src.keyword_analyzer import KeywordAnalyzer
    from src.news_impact_analyzer import NewsArticle, MarketImpact

    analyzer = KeywordAnalyzer()
    report = analyzer.analyze(impacts)
    print(report.top_bullish_keywords)
"""

import re
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Stopwords (minimal built-in set; NLTK stopwords used when available)
_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "used",
    "and", "but", "or", "nor", "for", "yet", "so", "at", "by", "in",
    "of", "on", "to", "up", "as", "it", "its", "this", "that", "these",
    "those", "with", "from", "into", "through", "during", "including",
    "until", "against", "among", "throughout", "despite", "towards",
    "upon", "concerning", "not", "no", "nor", "only", "own", "same",
    "than", "then", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such",
    "said", "says", "will", "also", "after", "before", "about",
}

try:
    import nltk
    nltk.data.find("corpora/stopwords")
    from nltk.corpus import stopwords as _nltk_sw
    _STOPWORDS.update(_nltk_sw.words("english"))
except Exception:
    pass


@dataclass
class KeywordReport:
    """Results from a keyword analysis run."""
    top_bullish_keywords: list      # [(word, avg_score, count), ...]
    top_bearish_keywords: list      # [(word, avg_score, count), ...]
    most_frequent_keywords: list    # [(word, count), ...]
    keyword_impact_map: dict        # word → {'avg_score', 'count', 'win_rate'}
    total_articles: int
    summary: str = ""


class KeywordAnalyzer:
    """
    Analyzes which keywords in news articles produce the best trading signals.

    Parameters
    ----------
    min_word_length : int
        Minimum length of a keyword (filters noise).
    min_occurrences : int
        Minimum number of times a keyword must appear to be included.
    top_n : int
        Number of top keywords to report.
    """

    def __init__(
        self,
        min_word_length: int = 4,
        min_occurrences: int = 2,
        top_n: int = 20,
    ):
        self.min_word_length = min_word_length
        self.min_occurrences = min_occurrences
        self.top_n = top_n

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, impacts: list) -> KeywordReport:
        """
        Analyze a list of :class:`~src.news_impact_analyzer.MarketImpact` objects.

        Parameters
        ----------
        impacts : list[MarketImpact]

        Returns
        -------
        KeywordReport
        """
        if not impacts:
            return KeywordReport([], [], [], {}, 0, "No articles to analyze.")

        # word → list of impact scores
        word_scores: defaultdict = defaultdict(list)
        word_counts: Counter = Counter()

        for impact in impacts:
            text = f"{impact.article.title} {impact.article.content}"
            words = self._tokenize(text)
            for word in set(words):   # de-duplicate per article
                word_scores[word].append(impact.impact_score)
                word_counts[word] += 1

        # Build impact map
        impact_map = {}
        for word, scores in word_scores.items():
            if word_counts[word] < self.min_occurrences:
                continue
            avg = float(np.mean(scores))
            win_rate = float(np.mean([1 if s > 0 else 0 for s in scores])) * 100
            impact_map[word] = {
                "avg_score": round(avg, 4),
                "count": word_counts[word],
                "win_rate": round(win_rate, 1),
            }

        sorted_by_score = sorted(
            impact_map.items(), key=lambda x: x[1]["avg_score"], reverse=True
        )
        bullish = [
            (w, v["avg_score"], v["count"])
            for w, v in sorted_by_score
            if v["avg_score"] > 0
        ][: self.top_n]
        bearish = [
            (w, v["avg_score"], v["count"])
            for w, v in reversed(sorted_by_score)
            if v["avg_score"] < 0
        ][: self.top_n]
        most_frequent = [
            (w, c) for w, c in word_counts.most_common(self.top_n)
            if w in impact_map
        ]

        summary = self._build_summary(bullish, bearish, len(impacts))
        return KeywordReport(
            top_bullish_keywords=bullish,
            top_bearish_keywords=bearish,
            most_frequent_keywords=most_frequent,
            keyword_impact_map=impact_map,
            total_articles=len(impacts),
            summary=summary,
        )

    def cluster_by_keyword(self, impacts: list, keyword: str) -> dict:
        """
        Return all articles that contain *keyword* and their aggregate stats.

        Parameters
        ----------
        impacts : list[MarketImpact]
        keyword : str

        Returns
        -------
        dict with keys: articles, avg_impact, win_rate
        """
        kw = keyword.lower()
        matched = [
            i for i in impacts
            if kw in f"{i.article.title} {i.article.content}".lower()
        ]
        if not matched:
            return {"articles": [], "avg_impact": 0.0, "win_rate": 0.0}
        avg_impact = float(np.mean([i.impact_score for i in matched]))
        win_rate = float(np.mean([1 if i.impact_score > 0 else 0 for i in matched])) * 100
        return {
            "articles": matched,
            "avg_impact": round(avg_impact, 4),
            "win_rate": round(win_rate, 1),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _tokenize(self, text: str) -> list:
        words = re.findall(r"\b[a-z]+\b", text.lower())
        return [
            w for w in words
            if len(w) >= self.min_word_length and w not in _STOPWORDS
        ]

    @staticmethod
    def _build_summary(bullish: list, bearish: list, total: int) -> str:
        lines = [
            f"Analyzed {total} articles.",
            f"Top bullish keywords: {', '.join(w for w, _, _ in bullish[:5])}",
            f"Top bearish keywords: {', '.join(w for w, _, _ in bearish[:5])}",
        ]
        return "\n".join(lines)
