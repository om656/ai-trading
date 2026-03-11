"""
Polygon Source
==============
Fetches market news from api.polygon.io.

Requires: POLYGON_KEY environment variable (free tier available).
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


class PolygonSource:
    """
    Wrapper around the Polygon.io Ticker News REST API.

    Parameters
    ----------
    api_key : str | None
        API key. Falls back to POLYGON_KEY env variable.
    """

    BASE_URL = "https://api.polygon.io/v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("POLYGON_KEY", "")
        self.name = "polygon"

    def fetch_ticker_news(self, symbol: str, max_results: int = 20) -> list:
        """
        Fetch news for a specific ticker symbol.

        Parameters
        ----------
        symbol : str
            Ticker symbol (e.g. "TSLA").
        max_results : int

        Returns
        -------
        list[NewsArticle]
        """
        if not self.api_key or not _REQUESTS_OK:
            logger.warning("PolygonSource: no API key or requests library missing.")
            return []

        params = {
            "ticker": symbol.upper(),
            "limit": min(max_results, 50),
            "apiKey": self.api_key,
        }
        try:
            resp = requests.get(f"{self.BASE_URL}/reference/news", params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("PolygonSource fetch error: %s", exc)
            return []

        articles = []
        for item in data.get("results", [])[:max_results]:
            pub = None
            if item.get("published_utc"):
                try:
                    pub = datetime.fromisoformat(
                        item["published_utc"].replace("Z", "+00:00")
                    )
                except ValueError:
                    pass
            tickers = item.get("tickers") or [symbol.upper()]
            articles.append(_make_article(
                title=item.get("title") or "",
                content=item.get("description") or "",
                source=f"{self.name}/{item.get('publisher', {}).get('name', '')}",
                url=item.get("article_url", ""),
                published_at=pub,
                symbols=tickers,
            ))
        return articles

    def fetch(self, query: str, symbols: Optional[list] = None,
              max_results: int = 20) -> list:
        """Generic fetch – iterates over supplied symbols."""
        if not symbols:
            return []
        articles = []
        per_symbol = max(1, max_results // len(symbols))
        for sym in symbols:
            articles.extend(self.fetch_ticker_news(sym, max_results=per_symbol))
        return articles[:max_results]
