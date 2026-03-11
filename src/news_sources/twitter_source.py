"""
Twitter/X Source
================
Fetches tweets related to trading symbols via the Twitter API v2.

Requires: TWITTER_BEARER_TOKEN environment variable.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import requests
    _REQUESTS_OK = True
except ImportError:
    _REQUESTS_OK = False


def _make_article(title, content, source, url="", published_at=None, symbols=None):
    from src.news_impact_analyzer import NewsArticle
    return NewsArticle(
        title=title, content=content, source=source,
        url=url, published_at=published_at, symbols=symbols or [],
    )


class TwitterSource:
    """
    Fetches tweets from the Twitter API v2 (Bearer Token auth).

    Parameters
    ----------
    bearer_token : str | None
        Bearer token. Falls back to TWITTER_BEARER_TOKEN env variable.
    """

    SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"

    def __init__(self, bearer_token: Optional[str] = None):
        self.bearer_token = bearer_token or os.getenv("TWITTER_BEARER_TOKEN", "")
        self.name = "twitter"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.bearer_token}"}

    def fetch(self, query: str, symbols: Optional[list] = None,
              max_results: int = 20) -> list:
        """
        Search recent tweets matching *query*.

        Parameters
        ----------
        query : str
            Twitter search query (e.g. "$AAPL OR #Apple").
        symbols : list[str] | None
        max_results : int
            Between 10 and 100 (API limit per request).

        Returns
        -------
        list[NewsArticle]
        """
        if not self.bearer_token or not _REQUESTS_OK:
            logger.warning("TwitterSource: bearer token missing or requests not available.")
            return []

        params = {
            "query": f"{query} lang:en -is:retweet",
            "max_results": max(10, min(max_results, 100)),
            "tweet.fields": "created_at,public_metrics,author_id",
        }
        try:
            resp = requests.get(
                self.SEARCH_URL, params=params, headers=self._headers(), timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("TwitterSource fetch error: %s", exc)
            return []

        articles = []
        for tweet in data.get("data", [])[:max_results]:
            pub = None
            if tweet.get("created_at"):
                try:
                    pub = datetime.fromisoformat(
                        tweet["created_at"].replace("Z", "+00:00")
                    )
                except ValueError:
                    pass
            text = tweet.get("text", "")
            tid = tweet.get("id", "")
            articles.append(_make_article(
                title=text[:120],
                content=text,
                source=self.name,
                url=f"https://twitter.com/i/web/status/{tid}",
                published_at=pub,
                symbols=list(symbols or []),
            ))
        return articles
