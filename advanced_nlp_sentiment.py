# Advanced NLP Sentiment

"""
This module implements advanced NLP techniques to analyze market sentiment.
Wraps the SentimentAnalyzer for backward compatibility.
"""

import nltk
import requests

from src.sentiment_analyzer import SentimentAnalyzer

_analyzer = SentimentAnalyzer(use_transformer=False)


def analyze_sentiment(text):
    """Analyze sentiment of a text string.

    Returns dict with 'score' (-1 to 1), 'label', and 'details'.
    """
    return _analyzer.analyze(text)


def analyze_headlines(headlines):
    """Analyze sentiment across multiple headlines."""
    return _analyzer.analyze_headlines(headlines)
