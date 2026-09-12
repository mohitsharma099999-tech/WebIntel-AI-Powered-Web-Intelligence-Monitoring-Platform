import asyncio
from celery import Celery
from .config import settings
from .database import SessionLocal
from .models import Website, Page, Snapshot
from .scraper import scrape_requests, scrape_browser
from .change_detector import detect_change

celery_app = Celery("webintel", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

@celery_app.task
def scrape_task(url: str, use_browser: bool = False):
    db = SessionLocal()
    try:
        result = asyncio.run(scrape_browser(url)) if use_browser else scrape_requests(url)

        website = db.query(Website).filter(Website.url == url).first()
        if not website:
            website = Website(url=url, title=result["title"])
            db.add(website)
            db.commit()
            db.refresh(website)

        page = db.query(Page).filter(Page.url == url).first()
        old_hash = None

        if page:
            old_hash = page.content_hash
            page.title = result["title"]
            page.content = result["content"]
            page.content_hash = result["hash"]
        else:
            page = Page(website_id=website.id, url=url, title=result["title"],
                        content=result["content"], content_hash=result["hash"])
            db.add(page)

        db.commit()
        db.refresh(page)

        db.add(Snapshot(page_id=page.id, content=result["content"],
                        content_hash=result["hash"]))
        detect_change(db, page.id, old_hash, result["hash"])
        db.commit()

        return {"status": "completed", "page_id": page.id, "url": url, "hash": result["hash"]}
    finally:
        db.close()
