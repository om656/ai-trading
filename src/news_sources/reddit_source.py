"""
Reddit Source
=============
Fetches posts from finance-related subreddits using the Reddit JSON API
(no authentication needed for public read access, rate-limited).

Optional: REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET / REDDIT_USER_AGENT
for OAuth2 authentication (higher rate limits).
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


DEFAULT_SUBREDDITS = [
    "wallstreetbets", "investing", "stocks",
    "StockMarket", "options", "CryptoCurrency",
]

DEFAULT_USER_AGENT = (
    os.getenv("REDDIT_USER_AGENT") or "ai-trading-bot/1.0 (by /u/ai_trader_bot)"
)


class RedditSource:
    """
    Fetches Reddit posts from finance subreddits.

    Parameters
    ----------
    subreddits : list[str] | None
        Subreddits to monitor. Defaults to :data:`DEFAULT_SUBREDDITS`.
    client_id : str | None
        Reddit OAuth2 client ID. Falls back to REDDIT_CLIENT_ID env variable.
    client_secret : str | None
        Reddit OAuth2 client secret. Falls back to REDDIT_CLIENT_SECRET env variable.
    """

    BASE_URL = "https://www.reddit.com"
    OAUTH_URL = "https://oauth.reddit.com"

    def __init__(
        self,
        subreddits: Optional[list] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        self.subreddits = subreddits or DEFAULT_SUBREDDITS
        self.client_id = client_id or os.getenv("REDDIT_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("REDDIT_CLIENT_SECRET", "")
        self.name = "reddit"
        self._token: Optional[str] = None

    # ------------------------------------------------------------------
    def _get_token(self) -> Optional[str]:
        """Obtain OAuth2 access token (if credentials provided)."""
        if not (self.client_id and self.client_secret) or not _REQUESTS_OK:
            return None
        try:
            resp = requests.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials"},
                headers={"User-Agent": DEFAULT_USER_AGENT},
                timeout=10,
            )
            resp.raise_for_status()
            self._token = resp.json().get("access_token")
        except Exception as exc:
            logger.debug("Reddit OAuth2 token error: %s", exc)
        return self._token

    def _headers(self) -> dict:
        h = {"User-Agent": DEFAULT_USER_AGENT}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    def _base(self) -> str:
        return self.OAUTH_URL if self._token else self.BASE_URL

    # ------------------------------------------------------------------
    def fetch(self, query: str, symbols: Optional[list] = None,
              max_results: int = 20) -> list:
        """
        Search recent Reddit posts matching *query*.

        Falls back to subreddit hot/new listings if search is unavailable.
        """
        if not _REQUESTS_OK:
            return []
        self._get_token()
        articles = []
        per_sub = max(1, max_results // len(self.subreddits))
        for sub in self.subreddits:
            articles.extend(
                self._fetch_subreddit(sub, query=query, limit=per_sub, symbols=symbols)
            )
            if len(articles) >= max_results:
                break
        return articles[:max_results]

    def _fetch_subreddit(self, subreddit: str, query: str = "",
                         limit: int = 10,
                         symbols: Optional[list] = None) -> list:
        url = f"{self._base()}/r/{subreddit}/search.json"
        params = {
            "q": query,
            "restrict_sr": 1,
            "sort": "new",
            "limit": limit,
            "t": "day",
        }
        try:
            resp = requests.get(url, params=params, headers=self._headers(), timeout=10)
            if resp.status_code == 403:
                # Fallback to public .json endpoint without search
                url = f"{self.BASE_URL}/r/{subreddit}/new.json"
                resp = requests.get(
                    url, params={"limit": limit}, headers=self._headers(), timeout=10
                )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("RedditSource fetch error for r/%s: %s", subreddit, exc)
            return []

        articles = []
        children = data.get("data", {}).get("children", [])
        for child in children[:limit]:
            post = child.get("data", {})
            pub = None
            if post.get("created_utc"):
                try:
                    pub = datetime.fromtimestamp(post["created_utc"], tz=timezone.utc)
                except (ValueError, OSError):
                    pass
            title = post.get("title", "")
            selftext = post.get("selftext", "")
            permalink = post.get("permalink", "")
            articles.append(_make_article(
                title=title,
                content=selftext or title,
                source=f"{self.name}/r/{subreddit}",
                url=f"https://reddit.com{permalink}",
                published_at=pub,
                symbols=list(symbols or []),
            ))
        return articles
