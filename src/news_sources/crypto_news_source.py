"""
Crypto News Source
==================
Aggregates cryptocurrency news from public feeds:
- CoinDesk RSS
- CoinTelegraph RSS
- CryptoPanic API (optional, no key required for public feed)
"""

import logging
import re
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import requests
    _REQUESTS_OK = True
except ImportError:
    _REQUESTS_OK = False

_BS4_OK = False
try:
    from bs4 import BeautifulSoup
    _BS4_OK = True
except ImportError:
    pass


def _make_article(title, content, source, url="", published_at=None, symbols=None):
    from src.news_impact_analyzer import NewsArticle
    return NewsArticle(
        title=title, content=content, source=source,
        url=url, published_at=published_at, symbols=symbols or [],
    )


CRYPTO_FEEDS = {
    "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "cointelegraph": "https://cointelegraph.com/rss",
}

CRYPTOPANIC_URL = "https://cryptopanic.com/api/v1/posts/"


class CryptoNewsSource:
    """
    Fetches cryptocurrency-focused news from multiple public sources.

    Parameters
    ----------
    cryptopanic_token : str | None
        Optional CryptoPanic API auth token (free registration).
        Falls back to CRYPTOPANIC_TOKEN env variable.
    """

    def __init__(self, cryptopanic_token: Optional[str] = None):
        import os
        self.cryptopanic_token = (
            cryptopanic_token or os.getenv("CRYPTOPANIC_TOKEN", "")
        )
        self.name = "crypto_news"

    def fetch(self, query: str = "", symbols: Optional[list] = None,
              max_results: int = 20) -> list:
        """
        Fetch recent crypto news from all configured sources.

        Parameters
        ----------
        query : str
            Optional keyword filter.
        symbols : list[str] | None
            Crypto tickers to tag (e.g. ["BTC", "ETH"]).
        max_results : int

        Returns
        -------
        list[NewsArticle]
        """
        if not _REQUESTS_OK:
            logger.warning("CryptoNewsSource: 'requests' not available.")
            return []

        articles: list = []

        # 1. CryptoPanic API
        if self.cryptopanic_token:
            articles.extend(
                self._fetch_cryptopanic(symbols=symbols, limit=max_results // 2)
            )

        # 2. RSS feeds
        per_feed = max(1, (max_results - len(articles)) // len(CRYPTO_FEEDS))
        for src_name, feed_url in CRYPTO_FEEDS.items():
            if len(articles) >= max_results:
                break
            articles.extend(
                self._fetch_rss(feed_url, src_name, query=query,
                                symbols=symbols, limit=per_feed)
            )

        return articles[:max_results]

    # ------------------------------------------------------------------
    def _fetch_cryptopanic(self, symbols: Optional[list] = None,
                           limit: int = 10) -> list:
        params: dict = {"auth_token": self.cryptopanic_token, "public": "true"}
        if symbols:
            params["currencies"] = ",".join(s.upper() for s in symbols)
        try:
            resp = requests.get(CRYPTOPANIC_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("CryptoPanic fetch error: %s", exc)
            return []

        articles = []
        for item in data.get("results", [])[:limit]:
            pub = None
            if item.get("published_at"):
                try:
                    pub = datetime.fromisoformat(
                        item["published_at"].replace("Z", "+00:00")
                    )
                except ValueError:
                    pass
            currencies = [
                c["code"] for c in item.get("currencies", [])
            ]
            articles.append(_make_article(
                title=item.get("title", ""),
                content=item.get("title", ""),
                source=f"{self.name}/cryptopanic",
                url=item.get("url", ""),
                published_at=pub,
                symbols=currencies or list(symbols or []),
            ))
        return articles

    def _fetch_rss(self, feed_url: str, src_name: str, query: str = "",
                   symbols: Optional[list] = None, limit: int = 10) -> list:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; ai-trading-bot/1.0)"}
        try:
            resp = requests.get(feed_url, headers=headers, timeout=10)
            resp.raise_for_status()
            xml_text = resp.text
        except Exception as exc:
            logger.error("CryptoNewsSource RSS error (%s): %s", src_name, exc)
            return []

        articles = []
        query_lower = query.lower() if query else ""

        if _BS4_OK:
            soup = BeautifulSoup(xml_text, "xml")
            items = soup.find_all("item")[:limit]
            for item in items:
                title_tag = item.find("title")
                desc_tag = item.find("description")
                link_tag = item.find("link")
                pub_tag = item.find("pubDate")

                title = title_tag.text.strip() if title_tag else ""
                desc = desc_tag.text.strip() if desc_tag else ""

                if query_lower and query_lower not in title.lower() \
                        and query_lower not in desc.lower():
                    continue

                pub = None
                if pub_tag and pub_tag.text:
                    try:
                        from email.utils import parsedate_to_datetime
                        pub = parsedate_to_datetime(pub_tag.text)
                    except Exception:
                        pass

                articles.append(_make_article(
                    title=title,
                    content=desc,
                    source=f"{self.name}/{src_name}",
                    url=link_tag.text.strip() if link_tag else "",
                    published_at=pub,
                    symbols=list(symbols or []),
                ))
        else:
            for m in re.finditer(r"<title><!\[CDATA\[(.*?)\]\]></title>", xml_text):
                if len(articles) >= limit:
                    break
                articles.append(_make_article(
                    title=m.group(1),
                    content="",
                    source=f"{self.name}/{src_name}",
                    symbols=list(symbols or []),
                ))
        return articles
