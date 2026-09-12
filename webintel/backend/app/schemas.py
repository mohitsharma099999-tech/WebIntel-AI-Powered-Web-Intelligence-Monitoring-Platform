from pydantic import BaseModel, HttpUrl

class ScrapeRequest(BaseModel):
    url: HttpUrl
    use_browser: bool = False

class WebsiteResponse(BaseModel):
    id: int
    url: str
    title: str | None = None
    class Config:
        from_attributes = True

class PageResponse(BaseModel):
    id: int
    url: str
    title: str | None = None
    content: str | None = None
    class Config:
        from_attributes = True
