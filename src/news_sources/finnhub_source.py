"""
Finnhub Source
==============
Fetches financial news from api.finnhub.io.

Requires: FINNHUB_KEY environment variable (free tier available).
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


class FinnhubSource:
    """
    Wrapper around the Finnhub.io news REST API.

    Parameters
    ----------
    api_key : str | None
        API key. Falls back to FINNHUB_KEY env variable.
    """

    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FINNHUB_KEY", "")
        self.name = "finnhub"

    def fetch_company_news(self, symbol: str,
                           from_date: Optional[str] = None,
                           to_date: Optional[str] = None,
                           max_results: int = 20) -> list:
        """
        Fetch company-specific news for *symbol*.

        Parameters
        ----------
        symbol : str
            Ticker symbol (e.g. "AAPL").
        from_date : str | None
            Start date as "YYYY-MM-DD".
        to_date : str | None
            End date as "YYYY-MM-DD".
        max_results : int

        Returns
        -------
        list[NewsArticle]
        """
        if not self.api_key or not _REQUESTS_OK:
            logger.warning("FinnhubSource: no API key or requests library missing.")
            return []

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        params = {
            "symbol": symbol.upper(),
            "from": from_date or today,
            "to": to_date or today,
            "token": self.api_key,
        }
        try:
            resp = requests.get(f"{self.BASE_URL}/company-news", params=params, timeout=10)
            resp.raise_for_status()
            items = resp.json()
        except Exception as exc:
            logger.error("FinnhubSource fetch error: %s", exc)
            return []

        articles = []
        for item in items[:max_results]:
            pub = None
            if item.get("datetime"):
                try:
                    pub = datetime.fromtimestamp(item["datetime"], tz=timezone.utc)
                except (ValueError, OSError):
                    pass
            articles.append(_make_article(
                title=item.get("headline") or "",
                content=item.get("summary") or "",
                source=f"{self.name}/{item.get('source', '')}",
                url=item.get("url", ""),
                published_at=pub,
                symbols=[symbol.upper()],
            ))
        return articles

    def fetch_market_news(self, category: str = "general",
                          max_results: int = 20) -> list:
        """Fetch general market news."""
        if not self.api_key or not _REQUESTS_OK:
            return []
        params = {"category": category, "token": self.api_key}
        try:
            resp = requests.get(f"{self.BASE_URL}/news", params=params, timeout=10)
            resp.raise_for_status()
            items = resp.json()
        except Exception as exc:
            logger.error("FinnhubSource market news error: %s", exc)
            return []

        articles = []
        for item in items[:max_results]:
            pub = None
            if item.get("datetime"):
                try:
                    pub = datetime.fromtimestamp(item["datetime"], tz=timezone.utc)
                except (ValueError, OSError):
                    pass
            articles.append(_make_article(
                title=item.get("headline") or "",
                content=item.get("summary") or "",
                source=f"{self.name}/{item.get('source', '')}",
                url=item.get("url", ""),
                published_at=pub,
            ))
        return articles

    # Convenience alias
    def fetch(self, query: str, symbols: Optional[list] = None,
              max_results: int = 20) -> list:
        """Generic fetch – delegates to fetch_market_news."""
        articles = self.fetch_market_news(max_results=max_results)
        if symbols:
            for a in articles:
                a.symbols = list(symbols)
        return articles
