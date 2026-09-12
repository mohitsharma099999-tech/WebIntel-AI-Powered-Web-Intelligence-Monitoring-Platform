import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import settings
from .database import engine, get_db
from .models import Change, Page, Website
from .schemas import (
    ChangeResponse,
    PageResponse,
    PageSummary,
    ScrapeAccepted,
    ScrapeRequest,
    WebsiteResponse,
)
from .tasks import scrape_task

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("webintel.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run Alembic migrations separately in prod:
    #   alembic upgrade head
    log.info("WebIntel starting (version=%s)", settings.APP_VERSION)
    yield
    engine.dispose()
    log.info("WebIntel stopped")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered web intelligence and monitoring platform",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["meta"])
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "ai_enabled": settings.ai_enabled,
    }


@app.post("/api/scrape", response_model=ScrapeAccepted, tags=["scrape"])
def start_scraping(request: ScrapeRequest):
    task = scrape_task.delay(str(request.url), request.use_browser)
    return {"message": "Scraping job queued", "task_id": task.id}


@app.get("/api/websites", response_model=list[WebsiteResponse], tags=["data"])
def list_websites(db: Session = Depends(get_db)):
    return db.query(Website).order_by(Website.created_at.desc()).all()


@app.get("/api/pages", response_model=list[PageSummary], tags=["data"])
def list_pages(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return (
        db.query(Page)
        .order_by(Page.updated_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@app.get("/api/pages/{page_id}", response_model=PageResponse, tags=["data"])
def get_page(page_id: int, db: Session = Depends(get_db)):
    page = db.get(Page, page_id)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@app.get("/api/changes", response_model=list[ChangeResponse], tags=["data"])
def list_changes(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return (
        db.query(Change)
        .order_by(Change.created_at.desc())
        .limit(limit)
        .all()
    )
