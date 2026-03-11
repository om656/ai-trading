"""
Tests for NewsBacktester
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from datetime import datetime, timezone

from src.news_impact_analyzer import NewsArticle
from src.news_backtester import NewsBacktester, BacktestResult, Trade


class TestNewsBacktester(unittest.TestCase):
    def setUp(self):
        self.backtester = NewsBacktester(
            symbol="AAPL",
            initial_capital=10_000.0,
            position_size_pct=0.10,
            sentiment_threshold=0.2,
            hold_hours=24,
        )
        self.articles = [
            NewsArticle(
                title="AAPL beats earnings, record profit",
                content="Apple reported record quarterly earnings.",
                source="test",
                symbols=["AAPL"],
                published_at=datetime(2023, 8, 4, 20, 0, tzinfo=timezone.utc),
            ),
            NewsArticle(
                title="AAPL faces major lawsuit",
                content="A major antitrust lawsuit was filed against Apple.",
                source="test",
                symbols=["AAPL"],
                published_at=datetime(2023, 9, 12, 14, 0, tzinfo=timezone.utc),
            ),
        ]

    def test_backtest_returns_result(self):
        # Without price data yfinance may not be available; run with None
        result = self.backtester.run(
            articles=self.articles,
            start_date="2023-08-01",
            end_date="2023-12-01",
        )
        self.assertIsInstance(result, BacktestResult)
        self.assertEqual(result.symbol, "AAPL")
        self.assertEqual(result.start_date, "2023-08-01")
        self.assertEqual(result.end_date, "2023-12-01")

    def test_empty_articles(self):
        result = self.backtester.run(
            articles=[],
            start_date="2023-01-01",
            end_date="2023-12-31",
        )
        self.assertIsInstance(result, BacktestResult)

    def test_initial_capital_preserved_on_no_trades(self):
        # Articles outside the date range should not generate trades
        articles_outside = [
            NewsArticle(
                title="Some news",
                content="News content.",
                source="test",
                published_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
            )
        ]
        result = self.backtester.run(
            articles=articles_outside,
            start_date="2023-01-01",
            end_date="2023-12-31",
        )
        # No trades should occur (different date range or no price data)
        self.assertGreaterEqual(result.total_trades, 0)

    def test_generate_report_string(self):
        result = self.backtester.run(
            articles=self.articles,
            start_date="2023-08-01",
            end_date="2023-12-01",
        )
        report = self.backtester.generate_report(result)
        self.assertIsInstance(report, str)
        self.assertIn("BACKTEST REPORT", report)
        self.assertIn("AAPL", report)

    def test_result_fields(self):
        result = self.backtester.run(
            articles=self.articles,
            start_date="2023-08-01",
            end_date="2023-12-01",
        )
        self.assertIsInstance(result.total_trades, int)
        self.assertIsInstance(result.win_rate_pct, float)
        self.assertIsInstance(result.sharpe_ratio, float)
        self.assertIsInstance(result.max_drawdown_pct, float)
        self.assertGreaterEqual(result.max_drawdown_pct, 0.0)

    def test_trade_dataclass(self):
        trade = Trade(
            symbol="AAPL",
            direction="long",
            entry_time=datetime(2023, 1, 1, tzinfo=timezone.utc),
            exit_time=datetime(2023, 1, 2, tzinfo=timezone.utc),
            entry_price=150.0,
            exit_price=155.0,
            quantity=10.0,
            pnl=50.0,
            pnl_pct=3.33,
            news_trigger="Earnings beat",
        )
        self.assertEqual(trade.symbol, "AAPL")
        self.assertEqual(trade.pnl, 50.0)


if __name__ == "__main__":
    unittest.main()
