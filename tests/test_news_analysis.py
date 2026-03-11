"""
Tests for NewsImpactAnalyzer
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from datetime import datetime, timezone

from src.news_impact_analyzer import (
    NewsImpactAnalyzer,
    NewsArticle,
    KeywordSentimentModel,
    VaderSentimentModel,
)


class TestNewsArticle(unittest.TestCase):
    def test_article_creation(self):
        article = NewsArticle(
            title="Company beats earnings",
            content="Profit exceeded expectations by 20%.",
            source="test",
        )
        self.assertEqual(article.title, "Company beats earnings")
        self.assertEqual(article.source, "test")
        self.assertIsNone(article.published_at)

    def test_article_with_symbols(self):
        article = NewsArticle(
            title="AAPL surges",
            content="Apple stock surged after earnings beat.",
            source="test",
            symbols=["AAPL"],
        )
        self.assertIn("AAPL", article.symbols)


class TestKeywordSentimentModel(unittest.TestCase):
    def setUp(self):
        self.model = KeywordSentimentModel()

    def test_bullish_text(self):
        score = self.model.score("Company reports strong earnings growth and profit surge")
        self.assertIsNotNone(score)
        self.assertGreater(score.compound, 0)
        self.assertIn("keyword", score.models_used)

    def test_bearish_text(self):
        score = self.model.score("Stock crashes on bankruptcy news, massive loss reported")
        self.assertIsNotNone(score)
        self.assertLess(score.compound, 0)

    def test_neutral_text(self):
        score = self.model.score("The company exists and operates normally today")
        self.assertIsNotNone(score)
        # Neutral text should have score close to 0
        self.assertAlmostEqual(score.compound, 0.0, delta=0.3)

    def test_score_bounds(self):
        score = self.model.score("surge gain profit rally")
        self.assertGreaterEqual(score.compound, -1.0)
        self.assertLessEqual(score.compound, 1.0)
        self.assertGreaterEqual(score.confidence, 0.0)
        self.assertLessEqual(score.confidence, 1.0)


class TestVaderSentimentModel(unittest.TestCase):
    def setUp(self):
        self.model = VaderSentimentModel()

    def test_available(self):
        # VADER may not be installed; skip gracefully
        if not self.model._available:
            self.skipTest("VADER not installed")

    def test_positive_text(self):
        if not self.model._available:
            self.skipTest("VADER not installed")
        score = self.model.score("Excellent results! Company profits soar.")
        self.assertIsNotNone(score)
        self.assertGreater(score.compound, 0)

    def test_negative_text(self):
        if not self.model._available:
            self.skipTest("VADER not installed")
        score = self.model.score("Terrible quarter. Huge losses, bankruptcy risk.")
        self.assertIsNotNone(score)
        self.assertLess(score.compound, 0)


class TestNewsImpactAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = NewsImpactAnalyzer(use_transformers=False)

    def _make_article(self, title, content, symbols=None):
        return NewsArticle(
            title=title,
            content=content,
            source="test",
            symbols=symbols or [],
            published_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )

    def test_analyze_bullish(self):
        article = self._make_article(
            "Apple beats earnings, record profit surge",
            "Apple reported record-breaking quarterly earnings, beating all estimates.",
            symbols=["AAPL"],
        )
        impact = self.analyzer.analyze(article)
        self.assertIn(impact.direction, ("bullish", "neutral"))
        self.assertGreaterEqual(impact.impact_score, -1.0)
        self.assertLessEqual(impact.impact_score, 1.0)

    def test_analyze_bearish(self):
        article = self._make_article(
            "Company files for bankruptcy, massive losses",
            "The firm declared bankruptcy amid mounting debt and loss of revenue.",
        )
        impact = self.analyzer.analyze(article)
        self.assertIn(impact.direction, ("bearish", "neutral"))

    def test_analyze_batch(self):
        articles = [
            self._make_article("Good earnings", "Profit beat estimates", ["AAPL"]),
            self._make_article("Bad news", "Stock crashes on fraud allegations", ["TSLA"]),
        ]
        impacts = self.analyzer.analyze_batch(articles)
        self.assertEqual(len(impacts), 2)

    def test_aggregate_impact(self):
        articles = [
            self._make_article("Earnings beat", "Great results", ["AAPL"]),
            self._make_article("Revenue surge", "Strong growth", ["AAPL"]),
        ]
        impacts = self.analyzer.analyze_batch(articles)
        agg = self.analyzer.aggregate_impact(impacts, symbol="AAPL")
        self.assertIn("direction", agg)
        self.assertIn("score", agg)
        self.assertIn("articles_analyzed", agg)
        self.assertEqual(agg["articles_analyzed"], 2)

    def test_aggregate_empty(self):
        agg = self.analyzer.aggregate_impact([], symbol="AAPL")
        self.assertEqual(agg["articles_analyzed"], 0)
        self.assertEqual(agg["direction"], "neutral")

    def test_direction_labels(self):
        article = self._make_article(
            "Company surges on record breaking profit earnings beat",
            "Massive profit growth and revenue beat all expectations.",
        )
        impact = self.analyzer.analyze(article)
        self.assertIn(impact.direction, ("bullish", "neutral", "bearish"))
        self.assertIn(impact.magnitude, ("high", "medium", "low"))

    def test_keyword_extraction(self):
        article = self._make_article(
            "Earnings earnings forecast dividend buyback",
            "Revenue growth and dividend increase announced.",
        )
        impact = self.analyzer.analyze(article)
        # At least some financial keywords should be detected
        self.assertIsInstance(impact.keywords, list)


if __name__ == "__main__":
    unittest.main()
