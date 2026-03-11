"""Tests for core trading modules."""

import unittest
from unittest.mock import patch, MagicMock

import numpy as np


class TestConfig(unittest.TestCase):
    def test_config_defaults(self):
        from src.config import Config
        self.assertEqual(Config.INITIAL_CAPITAL, 100000)
        self.assertTrue(Config.PAPER_TRADING)
        self.assertEqual(len(Config.DEFAULT_WATCHLIST), 10)
        self.assertIn("AAPL", Config.DEFAULT_WATCHLIST)


class TestRiskManager(unittest.TestCase):
    def setUp(self):
        from src.risk_manager import RiskManager
        self.rm = RiskManager(initial_capital=100000)

    def test_kelly_criterion_basic(self):
        # 55% win rate, avg win $1.5, avg loss $1.0
        fraction = self.rm.kelly_criterion(0.55, 1.5, 1.0)
        self.assertGreater(fraction, 0)
        self.assertLessEqual(fraction, self.rm.max_position_size)

    def test_kelly_criterion_edge_cases(self):
        self.assertEqual(self.rm.kelly_criterion(0.0, 1.0, 1.0), 0.0)
        self.assertEqual(self.rm.kelly_criterion(1.0, 1.0, 1.0), 0.0)
        self.assertEqual(self.rm.kelly_criterion(0.5, 1.0, 0.0), 0.0)

    def test_position_size_calculation(self):
        shares = self.rm.calculate_position_size(price=150.0, atr=3.0)
        self.assertGreaterEqual(shares, 0)
        # Should not exceed max position size
        max_shares = int((100000 * self.rm.max_position_size) / 150.0)
        self.assertLessEqual(shares, max_shares)

    def test_stop_loss_calculation(self):
        stop = self.rm.calculate_stop_loss(entry_price=100.0, atr=2.0, direction="long")
        self.assertLess(stop, 100.0)
        stop_short = self.rm.calculate_stop_loss(entry_price=100.0, atr=2.0, direction="short")
        self.assertGreater(stop_short, 100.0)

    def test_trailing_stop(self):
        trailing = self.rm.calculate_trailing_stop(highest_price=110.0, direction="long")
        self.assertLess(trailing, 110.0)
        self.assertGreater(trailing, 0)

    def test_drawdown_check(self):
        self.rm.current_capital = 90000  # 10% drawdown
        dd = self.rm.check_drawdown()
        self.assertAlmostEqual(dd["current_drawdown"], 0.10)
        self.assertFalse(dd["circuit_breaker"])

    def test_circuit_breaker_on_max_drawdown(self):
        self.rm.current_capital = 80000  # 20% drawdown, exceeds 15% limit
        dd = self.rm.check_drawdown()
        self.assertTrue(dd["circuit_breaker"])
        self.assertTrue(self.rm.circuit_breaker_active)

    def test_daily_pnl_update(self):
        self.rm.update_daily_pnl(-100)
        self.assertEqual(self.rm.daily_loss, -100)
        self.assertEqual(self.rm.current_capital, 99900)

    def test_daily_reset(self):
        self.rm.daily_loss = -500
        self.rm.circuit_breaker_active = True
        self.rm.reset_daily()
        self.assertEqual(self.rm.daily_loss, 0)
        self.assertFalse(self.rm.circuit_breaker_active)

    def test_trade_risk_assessment(self):
        result = self.rm.assess_trade_risk("AAPL", 150.0, 10)
        self.assertTrue(result["approved"])
        # Large position should be rejected
        result = self.rm.assess_trade_risk("AAPL", 150.0, 10000)
        self.assertFalse(result["approved"])

    def test_circuit_breaker_blocks_position_sizing(self):
        self.rm.circuit_breaker_active = True
        shares = self.rm.calculate_position_size(price=150.0, atr=3.0)
        self.assertEqual(shares, 0)


class TestPortfolio(unittest.TestCase):
    def setUp(self):
        from src.portfolio import Portfolio
        self.portfolio = Portfolio(initial_capital=100000)

    def test_open_position(self):
        result = self.portfolio.open_position("AAPL", 10, 150.0)
        self.assertTrue(result["success"])
        self.assertEqual(self.portfolio.cash, 100000 - 1500)
        self.assertIn("AAPL", self.portfolio.positions)

    def test_close_position(self):
        self.portfolio.open_position("AAPL", 10, 150.0)
        result = self.portfolio.close_position("AAPL", 160.0)
        self.assertTrue(result["success"])
        self.assertEqual(result["pnl"], 100.0)
        self.assertNotIn("AAPL", self.portfolio.positions)

    def test_insufficient_funds(self):
        result = self.portfolio.open_position("AAPL", 10000, 150.0)
        self.assertFalse(result["success"])

    def test_duplicate_position(self):
        self.portfolio.open_position("AAPL", 10, 150.0)
        result = self.portfolio.open_position("AAPL", 5, 155.0)
        self.assertFalse(result["success"])

    def test_close_nonexistent(self):
        result = self.portfolio.close_position("AAPL", 150.0)
        self.assertFalse(result["success"])

    def test_portfolio_value(self):
        self.portfolio.open_position("AAPL", 10, 150.0)
        value = self.portfolio.get_portfolio_value({"AAPL": 160.0})
        self.assertEqual(value, (100000 - 1500) + (10 * 160.0))

    def test_summary(self):
        self.portfolio.open_position("AAPL", 10, 150.0)
        summary = self.portfolio.get_summary({"AAPL": 160.0})
        self.assertEqual(summary["num_positions"], 1)
        self.assertEqual(summary["total_trades"], 1)
        self.assertGreater(summary["total_pnl"], 0)

    def test_trade_stats_empty(self):
        stats = self.portfolio.get_trade_stats()
        self.assertEqual(stats["total_trades"], 0)

    def test_trade_stats_with_trades(self):
        self.portfolio.open_position("AAPL", 10, 150.0)
        self.portfolio.close_position("AAPL", 160.0)
        self.portfolio.open_position("MSFT", 5, 300.0)
        self.portfolio.close_position("MSFT", 290.0)
        stats = self.portfolio.get_trade_stats()
        self.assertEqual(stats["total_trades"], 2)
        self.assertEqual(stats["winning_trades"], 1)
        self.assertEqual(stats["losing_trades"], 1)


class TestPosition(unittest.TestCase):
    def test_unrealized_pnl_long(self):
        from src.portfolio import Position
        pos = Position("AAPL", 10, 150.0, "long")
        self.assertEqual(pos.unrealized_pnl(160.0), 100.0)
        self.assertEqual(pos.unrealized_pnl(140.0), -100.0)

    def test_unrealized_pnl_short(self):
        from src.portfolio import Position
        pos = Position("AAPL", 10, 150.0, "short")
        self.assertEqual(pos.unrealized_pnl(140.0), 100.0)
        self.assertEqual(pos.unrealized_pnl(160.0), -100.0)

    def test_trailing_stop_update(self):
        from src.portfolio import Position
        pos = Position("AAPL", 10, 150.0, "long", stop_loss=145.0)
        pos.update_trailing_stop(160.0, 0.05)
        self.assertEqual(pos.highest_price, 160.0)
        self.assertAlmostEqual(pos.trailing_stop, 152.0)

    def test_should_stop_out(self):
        from src.portfolio import Position
        pos = Position("AAPL", 10, 150.0, "long", stop_loss=145.0, trailing_stop=148.0)
        self.assertFalse(pos.should_stop_out(150.0))
        self.assertTrue(pos.should_stop_out(147.0))

    def test_to_dict(self):
        from src.portfolio import Position
        pos = Position("AAPL", 10, 150.0)
        d = pos.to_dict()
        self.assertEqual(d["symbol"], "AAPL")
        self.assertEqual(d["shares"], 10)


class TestSentimentAnalyzer(unittest.TestCase):
    def test_analyze_returns_score(self):
        from src.sentiment_analyzer import SentimentAnalyzer
        analyzer = SentimentAnalyzer(use_transformer=False)
        result = analyzer.analyze("Stock prices are soaring, great earnings report!")
        self.assertIn("score", result)
        self.assertIn("label", result)

    def test_analyze_negative(self):
        from src.sentiment_analyzer import SentimentAnalyzer
        analyzer = SentimentAnalyzer(use_transformer=False)
        result = analyzer.analyze("Market crash, terrible losses, bankruptcy fears")
        self.assertLess(result["score"], 0)

    def test_analyze_headlines_empty(self):
        from src.sentiment_analyzer import SentimentAnalyzer
        analyzer = SentimentAnalyzer(use_transformer=False)
        result = analyzer.analyze_headlines([])
        self.assertEqual(result["score"], 0.0)
        self.assertEqual(result["label"], "neutral")

    def test_trading_signal(self):
        from src.sentiment_analyzer import SentimentAnalyzer
        analyzer = SentimentAnalyzer(use_transformer=False)
        self.assertEqual(analyzer.get_trading_signal(0.5), "BUY")
        self.assertEqual(analyzer.get_trading_signal(-0.5), "SELL")
        self.assertEqual(analyzer.get_trading_signal(0.0), "HOLD")


class TestCommandProcessor(unittest.TestCase):
    def test_help_command(self):
        from src.command_processor import CommandProcessor
        mock_agent = MagicMock()
        cp = CommandProcessor(mock_agent)
        result = cp.process("help")
        self.assertIn("Available Commands", result)

    def test_empty_command(self):
        from src.command_processor import CommandProcessor
        mock_agent = MagicMock()
        cp = CommandProcessor(mock_agent)
        result = cp.process("")
        self.assertIn("Empty command", result)

    def test_buy_command(self):
        from src.command_processor import CommandProcessor
        mock_agent = MagicMock()
        mock_agent.execute_trade.return_value = {
            "action": "BUY", "symbol": "AAPL", "shares": 10,
            "price": 150.0, "stop_loss": 145.0, "result": {"success": True},
        }
        cp = CommandProcessor(mock_agent)
        result = cp.process("buy AAPL")
        mock_agent.execute_trade.assert_called_once()

    def test_portfolio_command(self):
        from src.command_processor import CommandProcessor
        mock_agent = MagicMock()
        mock_agent.get_portfolio_summary.return_value = {
            "total_value": 100000, "cash": 100000,
            "total_pnl": 0, "return_pct": 0,
            "num_positions": 0, "total_trades": 0,
        }
        cp = CommandProcessor(mock_agent)
        result = cp.process("portfolio")
        self.assertIn("Portfolio Summary", result)


class TestLSTMPredictor(unittest.TestCase):
    def test_prediction_signal(self):
        from src.lstm_model import LSTMPredictor
        predictor = LSTMPredictor()
        self.assertEqual(predictor.get_prediction_signal(100.0, 103.0), "STRONG_BUY")
        self.assertEqual(predictor.get_prediction_signal(100.0, 101.0), "BUY")
        self.assertEqual(predictor.get_prediction_signal(100.0, 100.0), "HOLD")
        self.assertEqual(predictor.get_prediction_signal(100.0, 99.0), "SELL")
        self.assertEqual(predictor.get_prediction_signal(100.0, 97.0), "STRONG_SELL")


class TestMarketData(unittest.TestCase):
    def test_rsi_calculation(self):
        from src.market_data import MarketData
        import pandas as pd
        series = pd.Series([44, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10,
                           45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28,
                           46.28, 46.00, 46.03, 46.41, 46.22, 46.21])
        rsi = MarketData._compute_rsi(series, period=14)
        # RSI should be between 0 and 100
        valid_rsi = rsi.dropna()
        self.assertTrue((valid_rsi >= 0).all())
        self.assertTrue((valid_rsi <= 100).all())


class TestAIAgentCombineSignals(unittest.TestCase):
    def test_combine_signals(self):
        from src.ai_agent import AITradingAgent
        self.assertEqual(AITradingAgent._combine_signals("BUY", "BUY"), "STRONG_BUY")
        self.assertEqual(AITradingAgent._combine_signals("SELL", "SELL"), "STRONG_SELL")
        self.assertEqual(AITradingAgent._combine_signals("BUY", "HOLD"), "BUY")
        self.assertEqual(AITradingAgent._combine_signals("HOLD", "SELL"), "SELL")
        self.assertEqual(AITradingAgent._combine_signals("HOLD", "HOLD"), "HOLD")

    def test_rule_based_response(self):
        from src.ai_agent import AITradingAgent
        resp = AITradingAgent._rule_based_response("Should I buy?")
        self.assertIn("stop loss", resp.lower())


if __name__ == "__main__":
    unittest.main()
