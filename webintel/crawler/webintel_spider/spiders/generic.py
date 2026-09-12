"""Generic site spider with robots.txt compliance and link following."""
from __future__ import annotations

import logging
from urllib.parse import urlparse

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from ..items import WebIntelItem
from ..utils import canonicalise, is_same_domain

log = logging.getLogger(__name__)


class GenericSpider(CrawlSpider):
    """Crawl a site, extracting text content and following internal links.

    Usage:
        scrapy crawl generic -a start_url=https://example.com -a max_pages=100
    """

    name = "generic"

    # -- Configurable via -a flags ----------------------------------------
    def __init__(
        self,
        start_url: str,
        max_pages: int = 100,
        allowed_domain: str | None = None,
        follow_links: bool = True,
        ai_extract: bool = False,
        **kwargs,
    ):
        if not start_url:
            raise ValueError("`start_url` is required")

        self.start_urls = [canonicalise(start_url)]
        self.allowed_domains = [allowed_domain or urlparse(start_url).netloc]
        self.max_pages = int(max_pages)
        self.follow_links = str(follow_links).lower() not in ("0", "false", "no")
        self.ai_extract = str(ai_extract).lower() in ("1", "true", "yes")

        # Rules must be set *before* super().__init__ compiles them
        if self.follow_links:
            self.rules = (
                Rule(
                    LinkExtractor(
                        allow_domains=self.allowed_domains,
                        deny_extensions=[
                            "jpg", "jpeg", "png", "gif", "webp", "svg",
                            "css", "js", "zip", "tar", "gz", "pdf", "mp4",
                        ],
                        unique=True,
                    ),
                    callback="parse_page",
                    follow=True,
                    process_request="canonicalise_request",
                ),
            )

        super().__init__(**kwargs)

        self._seen = 0

    # ---------------------------------------------------------------------
    # Request canonicalisation
    # ---------------------------------------------------------------------
    def canonicalise_request(self, request, response):
        request = request.replace(url=canonicalise(request.url))
        return request

    # ---------------------------------------------------------------------
    # Default callback for start_urls when follow_links is False
    # ---------------------------------------------------------------------
    def parse_start_url(self, response, **kwargs):
        return self.parse_page(response, **kwargs)

    # ---------------------------------------------------------------------
    # Main parser
    # ---------------------------------------------------------------------
    def parse_page(self, response):
        if self._seen >= self.max_pages:
            return
        self._seen += 1

        # Skip non-HTML
        ct = response.headers.get(b"Content-Type", b"").decode().lower()
        if ct and "html" not in ct:
            log.debug("skip non-HTML %s (%s)", response.url, ct)
            return

        # Extract main text
        title = response.css("title::text").get(default="").strip()
        body = " ".join(response.css(
            "body ::text"
        ).getall())
        content = " ".join(body.split())

        if not content:
            log.debug("empty content %s", response.url)
            return

        item = WebIntelItem(
            url=canonicalise(response.url),
            source_url=response.url,
            domain=urlparse(response.url).netloc,
            title=title[:512],
            content=content,
            status_code=response.status,
            content_type=ct,
            depth=response.meta.get("depth", 0),
            spider_name=self.name,
        )
        item.set_hash()
        item.set_fetched_at()

        yield item

    # ---------------------------------------------------------------------
    # Enforce global page cap
    # ---------------------------------------------------------------------
    def _requests_to_follow(self, response):
        if self._seen >= self.max_pages:
            return
        # Only follow same-domain links
        yield from (
            r for r in super()._requests_to_follow(response)
            if is_same_domain(r.url, self.start_urls[0])
        )
