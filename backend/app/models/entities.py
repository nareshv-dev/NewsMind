from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import Column, Table, String, Text, DateTime, Float, ForeignKey, Integer, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


article_topics = Table("article_topics", Base.metadata,
    Column("article_id", ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
    Column("topic_id", ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True))


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)


class Category(Base):
    __tablename__ = "categories"
    slug: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)


class Topic(Base):
    __tablename__ = "topics"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)


class Article(Base):
    __tablename__ = "articles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    provider: Mapped[str] = mapped_column(String(40))
    provider_ref: Mapped[str] = mapped_column(String(512), unique=True)
    original_url: Mapped[str] = mapped_column(Text)
    normalized_url: Mapped[str] = mapped_column(String(2048), unique=True)
    headline: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    category_slug: Mapped[str] = mapped_column(ForeignKey("categories.slug"), index=True)
    geographic_scope: Mapped[str] = mapped_column(String(20), index=True)
    country: Mapped[str | None] = mapped_column(String(80))
    state: Mapped[str | None] = mapped_column(String(80))
    language: Mapped[str] = mapped_column(String(12), default="en", index=True)
    confidence: Mapped[float] = mapped_column(Float)
    classification_method: Mapped[str] = mapped_column(String(30))
    model_version: Mapped[str] = mapped_column(String(100))
    summary_method: Mapped[str] = mapped_column(String(30), default="source")
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source: Mapped[Source] = relationship(lazy="joined")
    topics: Mapped[list[Topic]] = relationship(secondary=article_topics, lazy="selectin")
    __table_args__ = (Index("ix_articles_feed", "category_slug", "expires_at", "published_at"),)


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="running")
    fetched: Mapped[int] = mapped_column(Integer, default=0)
    stored: Mapped[int] = mapped_column(Integer, default=0)
    skipped: Mapped[int] = mapped_column(Integer, default=0)
    failures: Mapped[list] = mapped_column(JSON, default=list)


class Bookmark(Base):
    __tablename__ = "bookmarks"
    user_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    article_id: Mapped[str] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Preference(Base):
    __tablename__ = "preferences"
    user_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    values: Mapped[dict] = mapped_column(JSON, default=dict)
