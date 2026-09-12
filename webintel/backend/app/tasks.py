import asyncio
import logging

from celery import Celery
from celery.exceptions import SoftTimeLimitExceeded

from .change_detector import detect_change
from .config import settings
from .database import session_scope
from .models import Page, Snapshot, Website
from .scraper import ScrapeResult, scrape_browser, scrape_http

log = logging.getLogger(__name__)

celery_app = Celery(
    "webintel",
    broker=str(settings.REDIS_URL),
    backend=str(settings.REDIS_URL),
)

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    task_default_retry_delay=10,
    task_max_retries=3,
    broker_connection_retry_on_startup=True,
)


def _run(coro):
    """Run an async coroutine from a sync Celery worker."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(
    bind=True,
    name="webintel.scrape",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3,
)
def scrape_task(self, url: str, use_browser: bool = False) -> dict:
    log.info("scrape.start url=%s browser=%s attempt=%s",
             url, use_browser, self.request.retries)
    try:
        result: ScrapeResult = _run(
            scrape_browser(url) if use_browser else scrape_http(url)
        )
    except SoftTimeLimitExceeded:
        log.warning("scrape.soft_timeout url=%s", url)
        raise

    with session_scope() as db:
        website = db.query(Website).filter(Website.url == url).one_or_none()
        if website is None:
            website = Website(url=url, title=result["title"])
            db.add(website)
            db.flush()

        page = db.query(Page).filter(Page.url == url).one_or_none()
        old_hash = page.content_hash if page else None

        if page is None:
            page = Page(
                website_id=website.id,
                url=url,
                title=result["title"],
                content=result["content"],
                content_hash=result["hash"],
            )
            db.add(page)
        else:
            page.title = result["title"]
            page.content = result["content"]
            page.content_hash = result["hash"]

        db.flush()
        db.add(Snapshot(
            page_id=page.id,
            content=result["content"],
            content_hash=result["hash"],
        ))
        detect_change(db, page.id, old_hash, result["hash"])

        page_id = page.id

    log.info("scrape.done url=%s page_id=%s", url, page_id)
    return {"status": "completed", "page_id": page_id, "url": url,
            "hash": result["hash"]}
