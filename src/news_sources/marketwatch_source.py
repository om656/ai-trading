"""
MarketWatch Source
==================
Fetches news headlines from MarketWatch's public RSS feeds.
No API key required.
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


FEED_URLS = {
    "topstories": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    "marketpulse": "https://feeds.content.dowjones.io/public/rss/mw_marketpulse",
    "realtimeheadlines": "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines",
    "personal_finance": "https://feeds.content.dowjones.io/public/rss/mw_personal_finance",
    "portfolio": "https://feeds.content.dowjones.io/public/rss/mw_portfolio",
}


class MarketWatchSource:
    """
    Fetches MarketWatch news via public RSS feeds.

    Parameters
    ----------
    feed : str
        One of the keys in :data:`FEED_URLS`. Default is ``"topstories"``.
    """

    def __init__(self, feed: str = "topstories"):
        self.feed = feed
        self.name = "marketwatch"
        self._feed_url = FEED_URLS.get(feed, FEED_URLS["topstories"])

    def fetch(self, query: str = "", symbols: Optional[list] = None,
              max_results: int = 20) -> list:
        """
        Fetch recent MarketWatch headlines.

        Parameters
        ----------
        query : str
            Optional filter string (matched against title/description).
        symbols : list[str] | None
        max_results : int

        Returns
        -------
        list[NewsArticle]
        """
        if not _REQUESTS_OK:
            logger.warning("MarketWatchSource: 'requests' not available.")
            return []

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; ai-trading-bot/1.0)",
            "Accept": "application/rss+xml, application/xml, text/xml",
        }
        try:
            resp = requests.get(self._feed_url, headers=headers, timeout=10)
            resp.raise_for_status()
            xml_text = resp.text
        except Exception as exc:
            logger.error("MarketWatchSource fetch error: %s", exc)
            return []

        return self._parse_rss(xml_text, query=query,
                               symbols=symbols, limit=max_results)

    def _parse_rss(self, xml_text: str, query: str = "",
                   symbols: Optional[list] = None, limit: int = 20) -> list:
        articles = []
        query_lower = query.lower() if query else ""

        if _BS4_OK:
            soup = BeautifulSoup(xml_text, "xml")
            items = soup.find_all("item")
            for item in items:
                if len(articles) >= limit:
                    break
                title_tag = item.find("title")
                desc_tag = item.find("description")
                link_tag = item.find("link")
                pub_tag = item.find("pubDate")

                title = title_tag.text.strip() if title_tag else ""
                description = desc_tag.text.strip() if desc_tag else ""

                if query_lower and query_lower not in title.lower() and \
                        query_lower not in description.lower():
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
                    content=description,
                    source=self.name,
                    url=link_tag.text.strip() if link_tag else "",
                    published_at=pub,
                    symbols=list(symbols or []),
                ))
        else:
            # Regex fallback
            titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", xml_text)
            descs = re.findall(r"<description><!\[CDATA\[(.*?)\]\]></description>", xml_text)
            for i, title in enumerate(titles[:limit]):
                if query_lower and query_lower not in title.lower():
                    continue
                articles.append(_make_article(
                    title=title,
                    content=descs[i] if i < len(descs) else "",
                    source=self.name,
                    symbols=list(symbols or []),
                ))
        return articles
