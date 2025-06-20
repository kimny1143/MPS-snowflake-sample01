from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, validator


class RSSArticle(BaseModel):
    """RSS article data model"""
    id: str = Field(..., description="Unique identifier for the article")
    title: str = Field(..., max_length=500, description="Article title")
    url: HttpUrl = Field(..., description="Article URL")
    published_at: datetime = Field(..., description="Publication timestamp")
    body: str = Field(..., description="Article body in Markdown format")
    
    @validator('title', 'body')
    def strip_whitespace(cls, v):
        return v.strip() if v else v
    
    @validator('body')
    def validate_body_length(cls, v):
        if len(v) > 1000000:  # 1MB limit
            raise ValueError("Body content exceeds maximum length")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RSSFeed(BaseModel):
    """RSS feed collection model"""
    source_url: HttpUrl = Field(..., description="RSS feed URL")
    fetched_at: datetime = Field(default_factory=datetime.now)
    articles: List[RSSArticle] = Field(..., description="List of articles")
    
    @validator('articles')
    def validate_articles(cls, v):
        if not v:
            raise ValueError("Feed must contain at least one article")
        return v


class LoadResult(BaseModel):
    """Result of data loading operation"""
    status: str = Field(..., pattern="^(success|error)$")
    feed_url: Optional[str] = None
    rows_loaded: Optional[int] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskStatus(BaseModel):
    """Snowflake task status"""
    name: str
    state: str
    schedule: str
    warehouse: str
    last_run_time: Optional[datetime]
    next_run_time: Optional[datetime]