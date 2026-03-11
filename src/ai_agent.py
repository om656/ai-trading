"""Main AI trading agent that coordinates all components.

Integrates LSTM predictions, sentiment analysis, LLM reasoning (via Ollama),
yfinance market data, risk management, and trade execution into a unified agent
that responds to text commands.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AITradingAgent:
    """AI-powered trading agent combining LSTM, sentiment analysis, and LLM reasoning.

    Components:
        - MarketData: yfinance-based price and feature retrieval
        - LSTMPredictor: LSTM-GRU ensemble for price prediction
        - SentimentAnalyzer: Multi-model NLP sentiment analysis
        - RiskManager: Kelly Criterion, drawdown controls, circuit breakers
        - Portfolio: Position tracking and trade history
        - TradeExecutor: Paper/live trade execution
        - CommandProcessor: Text command interface
        - Ollama LLM: Natural language reasoning and Q&A
    """

    def __init__(self, paper_trading: bool = True, use_transformer: bool = False):
        from src.config import Config
        from src.market_data import MarketData
        from src.lstm_model import LSTMPredictor
        from src.sentiment_analyzer import SentimentAnalyzer
        from src.risk_manager import RiskManager
        from src.portfolio import Portfolio
        from src.trade_executor import TradeExecutor
        from src.command_processor import CommandProcessor
        from src.news_fetcher import NewsAPI

        self.config = Config
        self.market_data = MarketData(Config.DEFAULT_WATCHLIST)
        self.lstm = LSTMPredictor(
            sequence_length=Config.SEQUENCE_LENGTH,
            n_features=7,
        )
        self.sentiment = SentimentAnalyzer(use_transformer=use_transformer)
        self.risk_manager = RiskManager(initial_capital=Config.INITIAL_CAPITAL)
        self.portfolio = Portfolio(initial_capital=Config.INITIAL_CAPITAL)
        self.news_api = NewsAPI(api_key=Config.NEWS_API_KEY)
        self.executor = TradeExecutor(
            portfolio=self.portfolio,
            risk_manager=self.risk_manager,
            market_data=self.market_data,
            paper_trading=paper_trading,
        )
        self.command_processor = CommandProcessor(self)
        self._ollama_available = False
        self._init_ollama()

        logger.info("AI Trading Agent initialized (paper_trading=%s)", paper_trading)

    def _init_ollama(self):
        """Initialize Ollama LLM connection."""
        try:
            import ollama
            self._ollama_client = ollama
            # Test connection
            ollama.list()
            self._ollama_available = True
            logger.info("Ollama LLM connected (model: %s)", self.config.OLLAMA_MODEL)
        except Exception as e:
            logger.info("Ollama not available (will use rule-based decisions): %s", e)
            self._ollama_client = None
            self._ollama_available = False

    def process_command(self, command: str) -> str:
        """Process a text command and return a response."""
        return self.command_processor.process(command)

    def analyze_symbol(self, symbol: str) -> dict:
        """Perform comprehensive analysis on a symbol."""
        # Get current price
        price_data = self.market_data.get_realtime_price(symbol)
        price = price_data.get("price", 0)

        # Sentiment analysis
        headlines = self.news_api.get_symbol_news(symbol)
        if not headlines:
            headlines = self.news_api.get_rss_headlines(symbol)
        sentiment_result = self.sentiment.analyze_headlines(headlines)

        # LSTM prediction
        prediction = self.predict_price(symbol)
        lstm_signal = prediction.get("signal", "HOLD")

        # Combine signals
        sentiment_signal = self.sentiment.get_trading_signal(sentiment_result["score"])
        combined = self._combine_signals(lstm_signal, sentiment_signal)

        # Ask LLM for reasoning if available
        llm_reasoning = ""
        if self._ollama_available:
            prompt = (
                f"Analyze {symbol} stock: price=${price:.2f}, "
                f"sentiment={sentiment_result['label']} ({sentiment_result['score']:.2f}), "
                f"LSTM prediction signal={lstm_signal}. "
                f"Give a brief trading recommendation in 2-3 sentences."
            )
            llm_reasoning = self.ask_llm(prompt)

        return {
            "symbol": symbol,
            "price": price,
            "sentiment": sentiment_result,
            "lstm_signal": lstm_signal,
            "prediction": prediction,
            "combined_signal": combined,
            "llm_reasoning": llm_reasoning,
        }

    def predict_price(self, symbol: str) -> dict:
        """Generate LSTM price prediction for a symbol."""
        try:
            X, y, scaler = self.market_data.prepare_lstm_features(
                symbol, self.config.SEQUENCE_LENGTH
            )
            if len(X) == 0:
                return {"symbol": symbol, "error": "Insufficient data"}

            # Use last sequence for prediction
            last_sequence = X[-1:]
            predicted_scaled = self.lstm.predict_next(last_sequence)

            # Get current price
            price_data = self.market_data.get_realtime_price(symbol)
            current_price = price_data.get("price", 0)

            # Approximate inverse transform for the close price column
            if scaler is not None and current_price > 0:
                price_range = scaler.data_max_[0] - scaler.data_min_[0]
                predicted_price = predicted_scaled * price_range + scaler.data_min_[0]
            else:
                predicted_price = current_price

            change_pct = (predicted_price - current_price) / current_price if current_price > 0 else 0
            signal = self.lstm.get_prediction_signal(current_price, predicted_price)

            return {
                "symbol": symbol,
                "current_price": current_price,
                "predicted_price": predicted_price,
                "change_pct": change_pct,
                "signal": signal,
            }
        except Exception as e:
            logger.error("Prediction error for %s: %s", symbol, e)
            return {"symbol": symbol, "error": str(e)}

    def get_sentiment(self, symbol: str) -> dict:
        """Get sentiment analysis for a symbol."""
        headlines = self.news_api.get_symbol_news(symbol)
        if not headlines:
            headlines = self.news_api.get_rss_headlines(symbol)
        return self.sentiment.analyze_headlines(headlines)

    def execute_trade(self, symbol: str, signal: str, reason: str = "") -> dict:
        """Execute a trade based on a signal."""
        return self.executor.execute_signal(symbol, signal, reason)

    def scan_watchlist(self) -> list:
        """Scan the watchlist for trading signals."""
        signals = []
        for symbol in self.market_data.watchlist:
            try:
                analysis = self.analyze_symbol(symbol)
                signals.append({
                    "symbol": symbol,
                    "signal": analysis["combined_signal"],
                    "sentiment": analysis["sentiment"]["label"],
                    "reason": f"Sentiment: {analysis['sentiment']['score']:.2f}, LSTM: {analysis['lstm_signal']}",
                })
            except Exception as e:
                logger.error("Error scanning %s: %s", symbol, e)
        return signals

    def get_portfolio_summary(self) -> dict:
        """Get current portfolio summary with live prices."""
        prices = {}
        for symbol in self.portfolio.positions:
            data = self.market_data.get_realtime_price(symbol)
            prices[symbol] = data.get("price", 0)
        return self.portfolio.get_summary(prices)

    def ask_llm(self, question: str) -> str:
        """Ask the Ollama LLM a question about trading."""
        if not self._ollama_available:
            return self._rule_based_response(question)
        try:
            response = self._ollama_client.chat(
                model=self.config.OLLAMA_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an AI trading assistant. Provide concise, "
                            "actionable trading advice based on the data provided. "
                            "Always mention risk considerations."
                        ),
                    },
                    {"role": "user", "content": question},
                ],
            )
            return response["message"]["content"]
        except Exception as e:
            logger.error("LLM error: %s", e)
            return self._rule_based_response(question)

    def get_status(self) -> str:
        """Get system status overview."""
        dd = self.risk_manager.check_drawdown()
        summary = self.get_portfolio_summary()
        return (
            f"AI Trading Agent Status\n"
            f"{'=' * 40}\n"
            f"  Mode: {'Paper' if self.executor.paper_trading else 'Live'} Trading\n"
            f"  LLM: {'Connected' if self._ollama_available else 'Offline (rule-based)'}\n"
            f"  LSTM Model: {'Ready' if self.lstm.model else 'Not loaded'}\n"
            f"  Watchlist: {len(self.market_data.watchlist)} symbols\n"
            f"  Positions: {summary['num_positions']}\n"
            f"  Portfolio: ${summary['total_value']:.2f}\n"
            f"  Drawdown: {dd['current_drawdown']:.2%}\n"
            f"  Circuit Breaker: {'ACTIVE' if dd['circuit_breaker'] else 'OFF'}"
        )

    @staticmethod
    def _combine_signals(lstm_signal: str, sentiment_signal: str) -> str:
        """Combine LSTM and sentiment signals into a final signal."""
        buy_signals = {"BUY", "STRONG_BUY"}
        sell_signals = {"SELL", "STRONG_SELL"}

        if lstm_signal in buy_signals and sentiment_signal in buy_signals:
            return "STRONG_BUY"
        elif lstm_signal in sell_signals and sentiment_signal in sell_signals:
            return "STRONG_SELL"
        elif lstm_signal in buy_signals or sentiment_signal in buy_signals:
            return "BUY"
        elif lstm_signal in sell_signals or sentiment_signal in sell_signals:
            return "SELL"
        return "HOLD"

    @staticmethod
    def _rule_based_response(question: str) -> str:
        """Provide a rule-based response when LLM is unavailable."""
        q = question.lower()
        if "buy" in q or "bullish" in q:
            return ("Based on rule-based analysis: Consider the overall trend, "
                    "volume, and risk/reward ratio before entering a position. "
                    "Always use stop losses.")
        elif "sell" in q or "bearish" in q:
            return ("Based on rule-based analysis: Consider taking profits if "
                    "the position has reached your target. Check for trend "
                    "reversals and tighten stop losses.")
        return ("I'm operating in rule-based mode (no LLM connected). "
                "Install and run Ollama with a model like llama3 for "
                "AI-powered responses: ollama run llama3")
