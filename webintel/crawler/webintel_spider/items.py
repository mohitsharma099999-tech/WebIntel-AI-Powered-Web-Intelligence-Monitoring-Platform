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
  
   
    url: str = scrapy.Field()                    
    source_url: str = scrapy.Field()             
    domain: str = scrapy.Field()              

    
    title: str = scrapy.Field()
    content: str = scrapy.Field()
    content_hash: str = scrapy.Field()          

    
    status_code: int = scrapy.Field()
    content_type: str = scrapy.Field()
    depth: int = scrapy.Field()
    fetched_at: str = scrapy.Field()            
    spider_name: str = scrapy.Field()

    
    ai_fields: dict = scrapy.Field()

    def set_hash(self) -> None:
        if self.get("content"):
            h = hashlib.sha256(self["content"].encode("utf-8")).hexdigest()
            self["content_hash"] = h

    def set_fetched_at(self) -> None:
        self.setdefault("fetched_at", _utcnow())
