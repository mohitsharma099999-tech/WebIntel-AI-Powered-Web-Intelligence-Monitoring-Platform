"""Scrapy settings for the WebIntel crawler."""
from __future__ import annotations

import os

BOT_NAME = "webintel"

SPIDER_MODULES = ["webintel_spider.spiders"]
NEWSPIDER_MODULE = "webintel_spider.spiders"


ROBOTSTXT_OBEY = True
USER_AGENT = os.getenv(
    "CRAWLER_USER_AGENT",
    "WebIntelBot/1.0 (+https://github.com/mohitsharma099999-tech; respectful research)",
)
DOWNLOAD_DELAY = float(os.getenv("CRAWLER_DOWNLOAD_DELAY", "1.0"))
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS = int(os.getenv("CRAWLER_CONCURRENCY", "8"))
CONCURRENT_REQUESTS_PER_DOMAIN = int(os.getenv("CRAWLER_CONCURRENCY_PER_DOMAIN", "2"))
CONCURRENT_REQUESTS_PER_IP = CONCURRENT_REQUESTS_PER_DOMAIN


AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 10.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_DEBUG = False

# Extra per-host throttle 
PER_DOMAIN_MIN_DELAY = 1.0
PER_DOMAIN_JITTER = 0.5


RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [429, 500, 502, 503, 504, 522, 524, 408]
DOWNLOAD_TIMEOUT = 30
DNS_TIMEOUT = 15


ROBOTSTXT_CACHED = True


HTTPCACHE_ENABLED = os.getenv("CRAWLER_HTTPCACHE", "0") == "1"
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504, 400, 401, 403, 404, 429]
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"


DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,  # disable default
    "webintel_spider.middlewares.PoliteRetryMiddleware": 550,
    "webintel_spider.middlewares.PerDomainThrottleMiddleware": 560,
    "webintel_spider.middlewares.StatsMiddleware": 900,
}


ITEM_PIPELINES = {
    "webintel_spider.pipelines.ValidationPipeline": 100,
    "webintel_spider.pipelines.DuplicateFilterPipeline": 200,
    "webintel_spider.pipelines.DatabasePipeline": 300,
    # Uncomment once OPENAI_API_KEY is set and you want AI fields:
    # "webintel_spider.pipelines.AIExtractionPipeline": 400,
}

EXTENSIONS = {
    "webintel_spider.extensions.PeriodicStatsExtension": 500,
}


FEEDS = {
    "output/items-%(time)s.jsonl": {
        "format": "jsonlines",
        "encoding": "utf8",
        "overwrite": False,
        "store_empty": False,
        "indent": None,
    },
}


DEPTH_LIMIT = int(os.getenv("CRAWLER_DEPTH_LIMIT", "3"))
DEPTH_PRIORITY = 1
SCHEDULER_DISK_QUEUE = "scrapy.squeues.PickleFifoDiskQueue"
SCHEDULER_MEMORY_QUEUE = "scrapy.squeues.FifoMemoryQueue"
SCHEDULER_PRIORITY_QUEUE = "scrapy.pqueues.ScrapyPriorityQueue"


REDIRECT_ENABLED = True
REDIRECT_MAX_TIMES = 5
COMPRESSION_ENABLED = True
AJAXCRAWL_ENABLED = False


FEED_EXPORT_ENCODING = "utf-8"


LOG_LEVEL = os.getenv("CRAWLER_LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATEFORMAT = "%Y-%m-%dT%H:%M:%S%z"


REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
TELNETCONSOLE_ENABLED = False
COOKIES_ENABLED = False
