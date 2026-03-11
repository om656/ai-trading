"""Legacy trading system wrapper.

Maintains backward compatibility while using the new modular components.
"""

import logging

from src.sentiment_analyzer import SentimentAnalyzer

logger = logging.getLogger(__name__)


class TradingSystem:
    """News-based trading system with sentiment analysis."""

    def __init__(self, news_api):
        self.news_api = news_api
        self.sentiment = SentimentAnalyzer()

    def trade_based_on_news(self):
        """Fetch headlines, analyze sentiment, and generate signals."""
        result = self.news_api.get_top_headlines()
        articles = result.get("articles", [])
        if not articles:
            logger.info("No articles found")
            return []

        signals = []
        for article in articles:
            title = article.get("title", "")
            if not title:
                continue
            analysis = self.sentiment.analyze(title)
            signal = self.sentiment.get_trading_signal(analysis["score"])
            signals.append({
                "title": title,
                "sentiment": analysis["label"],
                "score": analysis["score"],
                "signal": signal,
            })
            logger.info(
                "%s | Sentiment: %s (%.2f) | Signal: %s",
                title[:60], analysis["label"], analysis["score"], signal,
            )

        return signals