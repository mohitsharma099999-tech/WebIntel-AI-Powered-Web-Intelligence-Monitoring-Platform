"""Item pipelines: validation → dedup → database persistence."""
from __future__ import annotations

import logging

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

from .utils import canonicalise

log = logging.getLogger(__name__)



class ValidationPipeline:
    """Reject items missing required fields or with empty content."""

    REQUIRED = ("url", "content")https://github.com/mohitsharma099999-tech/WebIntel-AI-Powered-Web-Intelligence-Monitoring-Platform/tree/main

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        for field in self.REQUIRED:
            if not adapter.get(field):
                raise DropItem(f"missing required field: {field}")

        # Trim runaway content (protects DB + memory)
        content = adapter["content"]
        if len(content) > 5_000_000:
            adapter["content"] = content[:5_000_000]
            log.warning("content truncated for %s", adapter["url"])

        # Fill in hash + timestamps if the spider forgot
        if not adapter.get("content_hash"):
            item.set_hash()
        item.set_fetched_at()

        return item



class DuplicateFilterPipeline:
    """Drop items whose canonical URL or content hash was seen this run."""

    def __init__(self):
        self._urls: set[str] = set()
        self._hashes: set[str] = set()

    def open_spider(self, spider):
        self._urls.clear()
        self._hashes.clear()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        url = canonicalise(adapter["url"])
        adapter["url"] = url

        if url in self._urls:
            raise DropItem(f"duplicate url: {url}")
        self._urls.add(url)https://github.com/mohitsharma099999-tech/WebIntel-AI-Powered-Web-Intelligence-Monitoring-Platform/tree/main

        h = adapter.get("content_hash")
        if h and h in self._hashes:
            raise DropItem(f"duplicate content: {h}")
        if h:
            self._hashes.add(h)

        return item



class DatabasePipeline:
    """Persist scraped items into the WebIntel `websites` / `pages` tables.

    Mirrors the logic in `backend/app/tasks.py` so Scrapy and Celery
    write the same schema.
    """

    def open_spider(self, spider):
        # Imported lazily so Scrapy stays usable without the backend
        from backend.app.change_detector import detect_change
        from backend.app.database import session_scope
        from backend.app.models import Page, Snapshot, Website

        self._session_scope = session_scope
        self._Website = Website
        self._Page = Page
        self._Snapshot = Snapshot
        self._detect_change = detect_change

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        with self._session_scope() as db:
            website = (
                db.query(self._Website)
                .filter(self._Website.url == adapter["url"])
                .one_or_none()
            )
            if website is None:
                website = self._Website(
                    url=adapter["url"],
                    title=adapter.get("title", "")[:512],
                )
                db.add(website)
                db.flush()

            page = (
                db.query(self._Page)
                .filter(self._Page.url == adapter["url"])
                .one_or_none()
            )
            old_hash = page.content_hash if page else None

            if page is None:
                page = self._Page(
                    website_id=website.id,
                    url=adapter["url"],
                    title=adapter.get("title", "")[:512],
                    content=adapter["content"],
                    content_hash=adapter["content_hash"],
                )
                db.add(page)
            else:
                page.title = adapter.get("title", "")[:512]
                page.content = adapter["content"]
                page.content_hash = adapter["content_hash"]

            db.flush()
            db.add(self._Snapshot(
                page_id=page.id,
                content=adapter["content"],
                content_hash=adapter["content_hash"],
            ))
            self._detect_change(
                db, page.id, old_hash, adapter["content_hash"],
            )

        return item



class AIExtractionPipeline:
    """Populate `ai_fields` using the backend extractor. Opt-in via spider attr."""

    FIELDS = ["title", "summary", "topics"]

    def open_spider(self, spider):
        self.enabled = getattr(spider, "ai_extract", False)
        if not self.enabled:
            return
        try:
            from backend.app.ai_extractor import extract_data, AIExtractionError
            self._extract = extract_data
            self._err = AIExtractionError
        except Exception as exc:                     # noqa: BLE001
            log.warning("AI pipeline disabled: %s", exc)
            self.enabled = False

    def process_item(self, item, spider):
        if not self.enabled:
            return item
        adapter = ItemAdapter(item)
        try:
            adapter["ai_fields"] = self._extract(
                adapter["content"], self.FIELDS,
            )
        except self._err as exc:
            log.info("AI extraction failed for %s: %s", adapter["url"], exc)
        return item
