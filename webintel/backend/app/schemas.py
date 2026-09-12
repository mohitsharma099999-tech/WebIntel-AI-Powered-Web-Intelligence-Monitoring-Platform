from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ScrapeRequest(BaseModel):
    url: HttpUrl
    use_browser: bool = False


class ScrapeAccepted(BaseModel):
    message: str
    task_id: str


class WebsiteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    url: str
    title: str | None = None
    created_at: datetime


class PageSummary(BaseModel):
    """Used for list endpoints — no `content` field."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    url: str
    title: str | None = None
    content_hash: str | None = None
    updated_at: datetime


class PageResponse(PageSummary):
    """Full page with content."""
    content: str | None = None


class ChangeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    page_id: int
    change_type: Literal["NEW", "MODIFIED"]
    old_hash: str | None = None
    new_hash: str
    created_at: datetime
