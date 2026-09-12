"""Item definitions for WebIntel Scrapy spiders."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone

import scrapy


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class WebIntelItem(scrapy.Item):
    """A single scraped page.

    Uses a dataclass mixin so type-checkers and IDEs understand fields,
    while still being a real `scrapy.Item` for pipeline compatibility.
    """

    # -- Identity ----------------------------------------------------------
    url: str = scrapy.Field()                    # canonical URL
    source_url: str = scrapy.Field()             # original URL from spider
    domain: str = scrapy.Field()                 # netloc, for per-domain rules

    # -- Content -----------------------------------------------------------
    title: str = scrapy.Field()
    content: str = scrapy.Field()
    content_hash: str = scrapy.Field()           # SHA-256 of content

    # -- Metadata ----------------------------------------------------------
    status_code: int = scrapy.Field()
    content_type: str = scrapy.Field()
    depth: int = scrapy.Field()
    fetched_at: str = scrapy.Field()             # ISO-8601 UTC
    spider_name: str = scrapy.Field()

    # -- Optional AI fields (populated by pipeline) ------------------------
    ai_fields: dict = scrapy.Field()

    def set_hash(self) -> None:
        if self.get("content"):
            h = hashlib.sha256(self["content"].encode("utf-8")).hexdigest()
            self["content_hash"] = h

    def set_fetched_at(self) -> None:
        self.setdefault("fetched_at", _utcnow())
