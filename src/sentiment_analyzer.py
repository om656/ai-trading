"""Sentiment analysis using multiple NLP models."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Multi-model sentiment analysis for financial news.

    Uses VADER for fast rule-based analysis and optionally
    a transformer model (FinBERT) for higher accuracy.
    """

    def __init__(self, use_transformer: bool = False):
        self.use_transformer = use_transformer
        self._vader = None
        self._transformer_pipeline = None
        self._init_vader()
        if use_transformer:
            self._init_transformer()

    def _init_vader(self):
        """Initialize VADER sentiment analyzer."""
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self._vader = SentimentIntensityAnalyzer()
            logger.info("VADER sentiment analyzer initialized")
        except ImportError:
            logger.warning("vaderSentiment not available")

    def _init_transformer(self):
        """Initialize transformer-based sentiment model (FinBERT)."""
        try:
            from transformers import pipeline
            self._transformer_pipeline = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                truncation=True,
            )
            logger.info("FinBERT transformer pipeline initialized")
        except Exception as e:
            logger.warning("Transformer model not available: %s", e)
            self._transformer_pipeline = None

    def analyze(self, text: str) -> dict:
        """Analyze sentiment of a text string.

        Returns dict with 'score' (-1 to 1), 'label', and 'confidence'.
        """
        results = {}

        # VADER analysis
        if self._vader:
            scores = self._vader.polarity_scores(text)
            results["vader"] = {
                "score": scores["compound"],
                "positive": scores["pos"],
                "negative": scores["neg"],
                "neutral": scores["neu"],
            }

        # Transformer analysis
        if self._transformer_pipeline:
            try:
                output = self._transformer_pipeline(text[:512])[0]
                label = output["label"].lower()
                score = output["score"]
                if label == "negative":
                    score = -score
                elif label == "neutral":
                    score = 0.0
                results["transformer"] = {
                    "score": score,
                    "label": label,
                    "confidence": output["score"],
                }
            except Exception as e:
                logger.error("Transformer analysis failed: %s", e)

        # Combined score
        all_scores = [v["score"] for v in results.values() if "score" in v]
        combined_score = sum(all_scores) / len(all_scores) if all_scores else 0.0

        label = "neutral"
        if combined_score > 0.05:
            label = "positive"
        elif combined_score < -0.05:
            label = "negative"

        return {
            "score": combined_score,
            "label": label,
            "details": results,
        }

    def analyze_headlines(self, headlines: list) -> dict:
        """Analyze sentiment across multiple headlines.

        Returns aggregate sentiment with individual scores.
        """
        if not headlines:
            return {"score": 0.0, "label": "neutral", "headlines": []}

        results = []
        for headline in headlines:
            result = self.analyze(headline)
            result["text"] = headline
            results.append(result)

        scores = [r["score"] for r in results]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        label = "neutral"
        if avg_score > 0.05:
            label = "positive"
        elif avg_score < -0.05:
            label = "negative"

        return {
            "score": avg_score,
            "label": label,
            "count": len(results),
            "headlines": results,
        }

    def get_trading_signal(self, score: float) -> str:
        """Convert a sentiment score to a trading signal."""
        from src.config import Config
        if score >= Config.SENTIMENT_THRESHOLD_BUY:
            return "BUY"
        elif score <= Config.SENTIMENT_THRESHOLD_SELL:
            return "SELL"
        return "HOLD"
