from datetime import datetime, timezone
from typing import Literal, Annotated
from pydantic import BaseModel, Field, ConfigDict, field_validator

CATEGORIES = {"tamilnadu": "Tamilnadu", "india": "India", "world": "World", "sports": "Sports",
              "software-ai": "Software & AI", "product-updates": "Product Updates", "politics": "Politics"}
CategoryName = Literal["Tamilnadu", "India", "World", "Sports", "Software & AI", "Product Updates", "Politics"]


class Classification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    primary_category: CategoryName
    topics: list[str] = Field(max_length=8)
    geographic_scope: Literal["Global", "National", "Regional"]
    country: str | None
    state: str | None
    language: str = Field(min_length=2, max_length=12)
    confidence: float = Field(ge=0, le=1)
    summary: str | None = Field(max_length=1200)

    @field_validator("topics")
    @classmethod
    def validate_topics(cls, values):
        if any(not v.strip() or len(v) > 80 for v in values):
            raise ValueError("Invalid topic")
        return list(dict.fromkeys(v.strip() for v in values))


class ArticleOut(BaseModel):
    id: str
    headline: str
    description: str | None
    summary: str | None
    image_url: str | None
    original_url: str
    source: str
    category_slug: str
    category: str
    topics: list[str]
    geographic_scope: str
    country: str | None
    state: str | None
    language: str
    confidence: float
    classification_method: str
    model_version: str
    summary_method: str
    published_at: datetime
    fetched_at: datetime
    updated_at: datetime
    expires_at: datetime
    demo: bool

    @field_validator("published_at", "fetched_at", "updated_at", "expires_at")
    @classmethod
    def utc_timestamp(cls, value):
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def serialize(article):
    return ArticleOut(**{key: getattr(article, key) for key in ArticleOut.model_fields
                        if key not in {"source", "category", "topics", "demo"}},
        source=article.source.name, category=CATEGORIES[article.category_slug],
        topics=[topic.name for topic in article.topics], demo=article.provider == "demo")


class Page(BaseModel):
    items: list[ArticleOut]
    total: int
    page: int
    page_size: int
    demo_mode: bool


class PreferencesIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    categories: list[str] = Field(default_factory=list, max_length=7)
    topics: list[Annotated[str, Field(min_length=1, max_length=80)]] = Field(default_factory=list, max_length=20)
    language: Literal["en", "ta"] = "en"
    region: Literal["All", "Global", "National", "Regional"] = "All"
    reading_history: bool = False

    @field_validator("categories")
    @classmethod
    def valid_categories(cls, value):
        if any(v not in CATEGORIES for v in value):
            raise ValueError("Unknown category")
        return list(dict.fromkeys(value))
