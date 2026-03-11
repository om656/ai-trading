"""
Seeking Alpha Source
====================
Fetches analyst article summaries from Seeking Alpha via web scraping.

Note: Seeking Alpha has no official free API. This module uses a
lightweight HTTP GET approach on public article feeds. For production
use, consider the official Seeking Alpha API or a licensed data feed.
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


class SeekingAlphaSource:
    """
    Fetches Seeking Alpha article headlines from their public RSS/JSON feeds.

    Parameters
    ----------
    symbols : list[str] | None
        Ticker symbols to look up.
    """

    RSS_URL = "https://seekingalpha.com/api/sa/combined/{symbol}.xml"

    def __init__(self, symbols: Optional[list] = None):
        self.symbols = [s.upper() for s in (symbols or [])]
        self.name = "seeking_alpha"

    def fetch(self, query: str, symbols: Optional[list] = None,
              max_results: int = 20) -> list:
        """
        Fetch articles for the given symbols.

        Parameters
        ----------
        query : str
            Ignored (symbol-based lookup only).
        symbols : list[str] | None
        max_results : int

        Returns
        -------
        list[NewsArticle]
        """
        if not _REQUESTS_OK:
            logger.warning("SeekingAlphaSource: 'requests' not available.")
            return []

        targets = [s.upper() for s in (symbols or self.symbols)]
        if not targets:
            logger.warning("SeekingAlphaSource: no symbols specified.")
            return []

        articles = []
        per_sym = max(1, max_results // len(targets))
        for sym in targets:
            articles.extend(self._fetch_symbol(sym, limit=per_sym))
            if len(articles) >= max_results:
                break
        return articles[:max_results]

    def _fetch_symbol(self, symbol: str, limit: int = 10) -> list:
        url = self.RSS_URL.format(symbol=symbol.lower())
        headers = {"User-Agent": "Mozilla/5.0 (compatible; ai-trading-bot/1.0)"}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            content = resp.text
        except Exception as exc:
            logger.error("SeekingAlphaSource error for %s: %s", symbol, exc)
            return []

        return self._parse_rss(content, symbol, limit)

    def _parse_rss(self, xml_text: str, symbol: str, limit: int) -> list:
        """Parse RSS XML and return articles."""
        articles = []
        if _BS4_OK:
            soup = BeautifulSoup(xml_text, "xml")
            items = soup.find_all("item")[:limit]
            for item in items:
                title = item.find("title")
                description = item.find("description")
                link = item.find("link")
                pub_date = item.find("pubDate")
                pub = None
                if pub_date and pub_date.text:
                    try:
                        from email.utils import parsedate_to_datetime
                        pub = parsedate_to_datetime(pub_date.text)
                    except Exception:
                        pass
                articles.append(_make_article(
                    title=title.text if title else "",
                    content=description.text if description else "",
                    source=self.name,
                    url=link.text if link else "",
                    published_at=pub,
                    symbols=[symbol],
                ))
        else:
            # Fallback: simple regex-based parsing
            for m in re.finditer(r"<title><!\[CDATA\[(.*?)\]\]></title>", xml_text):
                if len(articles) >= limit:
                    break
                articles.append(_make_article(
                    title=m.group(1),
                    content="",
                    source=self.name,
                    symbols=[symbol],
                ))
        return articles
