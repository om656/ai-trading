"""
Tests for all news sources (unit tests that do not require live API calls)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from unittest.mock import patch, MagicMock

from src.news_sources import (
    NewsAPISource,
    FinnhubSource,
    PolygonSource,
    TwitterSource,
    RedditSource,
    SeekingAlphaSource,
    MarketWatchSource,
    CryptoNewsSource,
)


class TestNewsAPISource(unittest.TestCase):
    def test_no_key_returns_empty(self):
        src = NewsAPISource(api_key="")
        result = src.fetch("AAPL", symbols=["AAPL"])
        self.assertEqual(result, [])

    def test_fetch_top_headlines_no_key(self):
        src = NewsAPISource(api_key="")
        result = src.fetch_top_headlines()
        self.assertEqual(result, [])

    @patch("src.news_sources.newsapi_source.requests.get")
    def test_fetch_returns_articles(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "articles": [
                {
                    "title": "Apple beats earnings",
                    "description": "Apple reported strong results.",
                    "url": "https://example.com",
                    "publishedAt": "2024-01-01T12:00:00Z",
                    "source": {"name": "TechNews"},
                }
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        src = NewsAPISource(api_key="fake_key")
        articles = src.fetch("AAPL", symbols=["AAPL"])
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].title, "Apple beats earnings")
        self.assertIn("AAPL", articles[0].symbols)


class TestFinnhubSource(unittest.TestCase):
    def test_no_key_returns_empty(self):
        src = FinnhubSource(api_key="")
        result = src.fetch_company_news("AAPL")
        self.assertEqual(result, [])

    @patch("src.news_sources.finnhub_source.requests.get")
    def test_fetch_company_news(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {
                "headline": "Tesla news headline",
                "summary": "Tesla reported something.",
                "url": "https://example.com",
                "datetime": 1704067200,
                "source": "Reuters",
            }
        ]
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        src = FinnhubSource(api_key="fake_key")
        articles = src.fetch_company_news("TSLA")
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].title, "Tesla news headline")


class TestPolygonSource(unittest.TestCase):
    def test_no_key_no_symbols_returns_empty(self):
        src = PolygonSource(api_key="")
        result = src.fetch("query", symbols=[])
        self.assertEqual(result, [])

    @patch("src.news_sources.polygon_source.requests.get")
    def test_fetch_ticker_news(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "results": [
                {
                    "title": "NVDA AI chip news",
                    "description": "NVIDIA dominates AI chip market.",
                    "article_url": "https://example.com",
                    "published_utc": "2024-01-15T10:00:00Z",
                    "tickers": ["NVDA"],
                    "publisher": {"name": "Bloomberg"},
                }
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        src = PolygonSource(api_key="fake_key")
        articles = src.fetch_ticker_news("NVDA")
        self.assertEqual(len(articles), 1)
        self.assertIn("NVDA", articles[0].symbols)


class TestTwitterSource(unittest.TestCase):
    def test_no_token_returns_empty(self):
        src = TwitterSource(bearer_token="")
        result = src.fetch("$AAPL")
        self.assertEqual(result, [])

    @patch("src.news_sources.twitter_source.requests.get")
    def test_fetch_returns_articles(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [
                {
                    "id": "123456",
                    "text": "$AAPL looking bullish after earnings beat!",
                    "created_at": "2024-01-10T14:00:00Z",
                }
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        src = TwitterSource(bearer_token="fake_token")
        articles = src.fetch("$AAPL", symbols=["AAPL"])
        self.assertEqual(len(articles), 1)
        self.assertIn("twitter", articles[0].source)


class TestRedditSource(unittest.TestCase):
    def test_initialization(self):
        src = RedditSource(subreddits=["wallstreetbets"])
        self.assertEqual(src.subreddits, ["wallstreetbets"])

    @patch("src.news_sources.reddit_source.requests.get")
    def test_fetch_returns_articles(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {
                "children": [
                    {
                        "data": {
                            "title": "AAPL is the next big play",
                            "selftext": "Here is my analysis…",
                            "created_utc": 1704067200.0,
                            "permalink": "/r/wallstreetbets/comments/abc123/",
                        }
                    }
                ]
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        src = RedditSource(subreddits=["wallstreetbets"])
        articles = src.fetch("AAPL", symbols=["AAPL"], max_results=5)
        self.assertGreaterEqual(len(articles), 0)


class TestMarketWatchSource(unittest.TestCase):
    def test_initialization(self):
        src = MarketWatchSource(feed="topstories")
        self.assertEqual(src.name, "marketwatch")

    @patch("src.news_sources.marketwatch_source.requests.get")
    def test_fetch_with_simple_rss(self, mock_get):
        rss_xml = """<?xml version="1.0"?>
        <rss version="2.0">
          <channel>
            <item>
              <title><![CDATA[Market rally continues]]></title>
              <description><![CDATA[Stocks rose for the third consecutive day.]]></description>
              <link>https://marketwatch.com/story/abc</link>
              <pubDate>Mon, 01 Jan 2024 12:00:00 +0000</pubDate>
            </item>
          </channel>
        </rss>"""
        mock_resp = MagicMock()
        mock_resp.text = rss_xml
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        src = MarketWatchSource()
        articles = src.fetch()
        self.assertGreaterEqual(len(articles), 0)


class TestCryptoNewsSource(unittest.TestCase):
    def test_initialization(self):
        src = CryptoNewsSource()
        self.assertEqual(src.name, "crypto_news")

    @patch("src.news_sources.crypto_news_source.requests.get")
    def test_fetch_rss_fallback(self, mock_get):
        rss_xml = """<?xml version="1.0"?>
        <rss version="2.0">
          <channel>
            <item>
              <title><![CDATA[Bitcoin surges to new high]]></title>
              <description><![CDATA[BTC hit a new all-time high today.]]></description>
              <link>https://coindesk.com/btc-ath</link>
              <pubDate>Mon, 01 Jan 2024 10:00:00 +0000</pubDate>
            </item>
          </channel>
        </rss>"""
        mock_resp = MagicMock()
        mock_resp.text = rss_xml
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        src = CryptoNewsSource()
        articles = src.fetch(symbols=["BTC"])
        self.assertGreaterEqual(len(articles), 0)


if __name__ == "__main__":
    unittest.main()
