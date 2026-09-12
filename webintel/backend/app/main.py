from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import Website, Page, Change
from .schemas import ScrapeRequest, WebsiteResponse, PageResponse
from .tasks import scrape_task

Base.metadata.create_all(bind=engine)

app = FastAPI(title="WebIntel API",
              description="AI-powered web intelligence and monitoring platform",
              version="1.0.0")

@app.get("/")
def root():
    return {"name": "WebIntel", "status": "running"}

@app.post("/api/scrape")
def start_scraping(request: ScrapeRequest):
    task = scrape_task.delay(str(request.url), request.use_browser)
    return {"message": "Scraping job queued", "task_id": task.id}

@app.get("/api/websites", response_model=list[WebsiteResponse])
def websites(db: Session = Depends(get_db)):
    return db.query(Website).all()

@app.get("/api/pages", response_model=list[PageResponse])
def pages(db: Session = Depends(get_db)):
    return db.query(Page).all()

@app.get("/api/pages/{page_id}", response_model=PageResponse)
def page(page_id: int, db: Session = Depends(get_db)):
    result = db.query(Page).filter(Page.id == page_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Page not found")
    return result

@app.get("/api/changes")
def changes(db: Session = Depends(get_db)):
    return db.query(Change).order_by(Change.created_at.desc()).all()
