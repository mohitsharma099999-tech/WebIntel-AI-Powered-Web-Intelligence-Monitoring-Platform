from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Website(Base):
    __tablename__ = "websites"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    pages = relationship("Page", back_populates="website")

class Page(Base):
    __tablename__ = "pages"
    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"))
    url = Column(String, nullable=False)
    title = Column(String)
    content = Column(Text)
    content_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    website = relationship("Website", back_populates="pages")

class Snapshot(Base):
    __tablename__ = "snapshots"
    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey("pages.id"))
    content = Column(Text)
    content_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Change(Base):
    __tablename__ = "changes"
    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey("pages.id"))
    change_type = Column(String)
    old_hash = Column(String)
    new_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
