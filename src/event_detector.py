"""
Event Detector
==============
Identifies significant market events from a stream of news articles.

Detects:
- Earnings announcements
- M&A / acquisition news
- FDA decisions
- Central bank announcements
- Macroeconomic data releases
- Executive changes
- Legal / regulatory events
- Product launches

Usage
-----
    from src.event_detector import EventDetector
    from src.news_impact_analyzer import NewsArticle

    detector = EventDetector()
    events = detector.detect(articles)
    for event in events:
        print(event)
"""

import re
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Event taxonomy
# ---------------------------------------------------------------------------

EVENT_PATTERNS: dict = {
    "earnings": {
        "keywords": [
            r"\bearnings\b", r"\brevenue\b", r"\beps\b", r"\bprofit\b",
            r"\bquarterly results\b", r"\bbeat estimates\b", r"\bmissed estimates\b",
        ],
        "impact_multiplier": 1.4,
        "description": "Earnings / financial results announcement",
    },
    "merger_acquisition": {
        "keywords": [
            r"\bacquisition\b", r"\bmerger\b", r"\btakeover\b", r"\bbuyout\b",
            r"\bprivate equity\b", r"\bdeal\b.*\bbillion\b",
        ],
        "impact_multiplier": 1.6,
        "description": "Merger or acquisition announcement",
    },
    "fda_decision": {
        "keywords": [
            r"\bfda\b", r"\bapproval\b", r"\bclinical trial\b", r"\bdrug\b.*\bapproved\b",
            r"\brejected by fda\b",
        ],
        "impact_multiplier": 2.0,
        "description": "FDA approval/rejection",
    },
    "central_bank": {
        "keywords": [
            r"\bfed\b", r"\bfederal reserve\b", r"\binterest rate\b",
            r"\brate hike\b", r"\brate cut\b", r"\bfomc\b", r"\bpowell\b",
        ],
        "impact_multiplier": 1.5,
        "description": "Central bank policy announcement",
    },
    "macro_data": {
        "keywords": [
            r"\binflation\b", r"\bcpi\b", r"\bgdp\b", r"\bjobs report\b",
            r"\bunemployment\b", r"\bnonfarm payrolls\b", r"\bppi\b",
        ],
        "impact_multiplier": 1.3,
        "description": "Macroeconomic data release",
    },
    "executive_change": {
        "keywords": [
            r"\bceo\b.*\bresigns\b", r"\bcfo\b.*\bleaves\b", r"\bnew ceo\b",
            r"\bappoints\b.*\bchief\b", r"\bexecutive.*\bchange\b",
        ],
        "impact_multiplier": 1.2,
        "description": "Executive leadership change",
    },
    "legal_regulatory": {
        "keywords": [
            r"\blawsuit\b", r"\bsettlement\b", r"\bsec\b.*\binvestigation\b",
            r"\bfine\b", r"\bpenalty\b", r"\bantitrust\b", r"\bfraud\b",
        ],
        "impact_multiplier": 1.3,
        "description": "Legal or regulatory action",
    },
    "product_launch": {
        "keywords": [
            r"\blaunch\b", r"\bnew product\b", r"\bannounces\b.*\bproduct\b",
            r"\bunveils\b", r"\breleases\b.*\bversion\b",
        ],
        "impact_multiplier": 1.1,
        "description": "Product launch or announcement",
    },
    "dividend": {
        "keywords": [
            r"\bdividend\b", r"\bspecial dividend\b", r"\bstock split\b",
            r"\bshare buyback\b", r"\brepurchase program\b",
        ],
        "impact_multiplier": 1.2,
        "description": "Dividend or capital return announcement",
    },
    "bankruptcy": {
        "keywords": [
            r"\bbankruptcy\b", r"\bchapter 11\b", r"\bchapter 7\b",
            r"\bdefault\b", r"\binsolvency\b", r"\bliquidation\b",
        ],
        "impact_multiplier": 2.5,
        "description": "Bankruptcy or insolvency filing",
    },
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class DetectedEvent:
    """A market event extracted from a news article."""
    event_type: str
    description: str
    article_title: str
    article_source: str
    published_at: Optional[datetime]
    affected_symbols: list = field(default_factory=list)
    impact_multiplier: float = 1.0
    matched_patterns: list = field(default_factory=list)
    confidence: float = 0.0

    def __str__(self) -> str:
        sym = ", ".join(self.affected_symbols) if self.affected_symbols else "–"
        ts = self.published_at.strftime("%Y-%m-%d %H:%M") if self.published_at else "unknown"
        return (
            f"[{self.event_type.upper()}] {ts} | {sym} | "
            f"Confidence={self.confidence:.2f} | {self.article_title[:80]}"
        )


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------

class EventDetector:
    """
    Detects market-moving events from news articles.

    Parameters
    ----------
    event_types : list[str] | None
        Subset of EVENT_PATTERNS keys to check. Defaults to all.
    min_confidence : float
        Minimum confidence threshold (0–1) to emit an event.
    """

    def __init__(
        self,
        event_types: Optional[list] = None,
        min_confidence: float = 0.2,
    ):
        self.event_types = event_types or list(EVENT_PATTERNS.keys())
        self.min_confidence = min_confidence
        self._patterns = {
            k: v for k, v in EVENT_PATTERNS.items() if k in self.event_types
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, articles: list) -> list:
        """
        Scan *articles* for market events.

        Parameters
        ----------
        articles : list[NewsArticle]

        Returns
        -------
        list[DetectedEvent]
        """
        events: list = []
        for article in articles:
            detected = self._detect_article(article)
            events.extend(detected)
        return events

    def detect_from_impacts(self, impacts: list) -> list:
        """
        Convenience method accepting MarketImpact objects.

        Parameters
        ----------
        impacts : list[MarketImpact]

        Returns
        -------
        list[DetectedEvent]
        """
        return self.detect([i.article for i in impacts])

    def summarize(self, events: list) -> dict:
        """
        Summarize detected events by type.

        Parameters
        ----------
        events : list[DetectedEvent]

        Returns
        -------
        dict[str, int]  – event_type → count
        """
        summary: dict = {}
        for event in events:
            summary[event.event_type] = summary.get(event.event_type, 0) + 1
        return summary

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _detect_article(self, article) -> list:
        text = f"{article.title} {article.content}".lower()
        events = []
        for event_type, spec in self._patterns.items():
            matched = []
            for pattern in spec["keywords"]:
                if re.search(pattern, text, re.IGNORECASE):
                    matched.append(pattern)
            if not matched:
                continue
            confidence = min(1.0, len(matched) / len(spec["keywords"]) + 0.1)
            if confidence < self.min_confidence:
                continue
            events.append(DetectedEvent(
                event_type=event_type,
                description=spec["description"],
                article_title=article.title,
                article_source=article.source,
                published_at=article.published_at,
                affected_symbols=list(article.symbols or []),
                impact_multiplier=spec["impact_multiplier"],
                matched_patterns=matched,
                confidence=round(confidence, 3),
            ))
        return events
