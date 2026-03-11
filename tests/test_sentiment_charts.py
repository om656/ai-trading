"""
Tests for sentiment_charts module
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
import tempfile
import numpy as np
from datetime import datetime, timezone, timedelta

from src import sentiment_charts as sc


def _timestamps(n: int):
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return [base + timedelta(hours=i) for i in range(n)]


class TestSentimentCharts(unittest.TestCase):
    """Tests that chart functions run without errors and save files."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.n = 20
        rng = np.random.default_rng(0)
        self.timestamps = _timestamps(self.n)
        self.scores = list(rng.uniform(-1, 1, self.n))

    def _path(self, filename: str) -> str:
        return os.path.join(self.tmpdir, filename)

    def test_plot_sentiment_over_time(self):
        if not sc._PLT_OK:
            self.skipTest("matplotlib not available")
        fig = sc.plot_sentiment_over_time(
            timestamps=self.timestamps,
            scores=self.scores,
            symbol="AAPL",
            save_path=self._path("ot.png"),
        )
        self.assertIsNotNone(fig)
        self.assertTrue(os.path.exists(self._path("ot.png")))

    def test_plot_sentiment_by_symbol(self):
        if not sc._PLT_OK:
            self.skipTest("matplotlib not available")
        symbol_scores = {"AAPL": 0.4, "TSLA": -0.3, "MSFT": 0.1}
        fig = sc.plot_sentiment_by_symbol(
            symbol_scores=symbol_scores,
            save_path=self._path("by_sym.png"),
        )
        self.assertIsNotNone(fig)
        self.assertTrue(os.path.exists(self._path("by_sym.png")))

    def test_plot_sentiment_vs_price(self):
        if not sc._PLT_OK:
            self.skipTest("matplotlib not available")
        prices = list(150.0 + np.cumsum(np.random.randn(self.n)))
        fig = sc.plot_sentiment_vs_price(
            timestamps=self.timestamps,
            sentiment_scores=self.scores,
            prices=prices,
            symbol="AAPL",
            save_path=self._path("vs_price.png"),
        )
        self.assertIsNotNone(fig)
        self.assertTrue(os.path.exists(self._path("vs_price.png")))

    def test_plot_sentiment_heatmap(self):
        if not sc._PLT_OK:
            self.skipTest("matplotlib not available")
        symbols = ["AAPL", "TSLA", "MSFT"]
        dates = [datetime(2024, 1, d) for d in range(1, 6)]
        matrix = np.random.uniform(-1, 1, (len(symbols), len(dates)))
        fig = sc.plot_sentiment_heatmap(
            symbols=symbols,
            dates=dates,
            scores=matrix,
            save_path=self._path("heatmap.png"),
        )
        self.assertIsNotNone(fig)
        self.assertTrue(os.path.exists(self._path("heatmap.png")))

    def test_plot_sentiment_distribution(self):
        if not sc._PLT_OK:
            self.skipTest("matplotlib not available")
        fig = sc.plot_sentiment_distribution(
            scores=self.scores,
            save_path=self._path("dist.png"),
        )
        self.assertIsNotNone(fig)
        self.assertTrue(os.path.exists(self._path("dist.png")))

    def test_plot_sentiment_strength(self):
        if not sc._PLT_OK:
            self.skipTest("matplotlib not available")
        fig = sc.plot_sentiment_strength_over_time(
            timestamps=self.timestamps,
            scores=self.scores,
            window=5,
            save_path=self._path("strength.png"),
        )
        self.assertIsNotNone(fig)
        self.assertTrue(os.path.exists(self._path("strength.png")))

    def test_color_for_score(self):
        self.assertEqual(sc._color_for_score(0.5), "#2ecc71")
        self.assertEqual(sc._color_for_score(-0.5), "#e74c3c")
        self.assertEqual(sc._color_for_score(0.0), "#95a5a6")


if __name__ == "__main__":
    unittest.main()
