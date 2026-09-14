from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.auth import current_user, ops_access
from app.models.entities import Article, Source, IngestionRun, Bookmark, Preference
from app.schemas.news import CATEGORIES, Page, ArticleOut, serialize, PreferencesIn
from app.repositories.articles import active_query, filtered_query

router = APIRouter(prefix="/api/v1")


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(select(1))
    latest = db.scalar(select(IngestionRun).order_by(IngestionRun.id.desc()).limit(1))
    return {"status": "ok", "demo_mode": settings.demo_mode, "accounts_configured": bool(settings.supabase_url),
            "provider_configured": settings.news_provider == "rss" or bool(settings.newsapi_key),
            "news_provider": settings.news_provider, "latest_ingestion_status": latest.status if latest else "never_run"}


@router.get("/categories")
def categories():
    return [{"slug": slug, "name": name} for slug, name in CATEGORIES.items()]


@router.get("/sources")
def sources(db: Session = Depends(get_db)):
    return list(db.scalars(select(Source.name).where(Source.id.in_(active_query().with_only_columns(Article.source_id))).order_by(Source.name)))


@router.get("/search", response_model=Page)
@router.get("/articles", response_model=Page)
def articles(q: str | None = Query(None, max_length=200),
             category: Literal["tamilnadu", "india", "world", "sports", "software-ai", "product-updates", "politics"] | None = None,
             region: Literal["Global", "National", "Regional"] | None = None,
             source: str | None = Query(None, max_length=200), language: str | None = Query(None, max_length=12),
             topic: str | None = Query(None, max_length=80), since: datetime | None = None, until: datetime | None = None,
             sort: Literal["newest", "oldest"] = "newest", page: int = Query(1, ge=1, le=10000),
             page_size: int = Query(12, ge=1, le=50), db: Session = Depends(get_db)):
    if any(value and value.tzinfo is None for value in [since, until]):
        raise HTTPException(422, "Dates must include a timezone")
    if since and until and since > until:
        raise HTTPException(422, "Start date must precede end date")
    stmt = filtered_query(db, q, category, region, source, language, topic, since, until)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    order = Article.published_at.desc() if sort == "newest" else Article.published_at.asc()
    rows = db.scalars(stmt.order_by(order, Article.id).offset((page - 1) * page_size).limit(page_size)).unique().all()
    return Page(items=[serialize(a) for a in rows], total=total, page=page, page_size=page_size, demo_mode=settings.demo_mode)


@router.get("/articles/{article_id}", response_model=ArticleOut)
def article(article_id: str, db: Session = Depends(get_db)):
    value = db.scalar(active_query().where(Article.id == article_id))
    if not value:
        raise HTTPException(404, "Article unavailable or its four-day reading window has ended")
    return serialize(value)


@router.get("/bookmarks", response_model=list[ArticleOut])
def bookmarks(user: str = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(active_query().join(Bookmark).where(Bookmark.user_id == user).order_by(Bookmark.created_at.desc())).unique().all()
    return [serialize(a) for a in rows]


@router.put("/bookmarks/{article_id}", status_code=204)
def save_bookmark(article_id: str, user: str = Depends(current_user), db: Session = Depends(get_db)):
    if not db.scalar(active_query().where(Article.id == article_id)):
        raise HTTPException(404, "Article unavailable")
    if not db.get(Bookmark, (user, article_id)):
        db.add(Bookmark(user_id=user, article_id=article_id))
        db.commit()


@router.delete("/bookmarks/{article_id}", status_code=204)
def remove_bookmark(article_id: str, user: str = Depends(current_user), db: Session = Depends(get_db)):
    db.execute(delete(Bookmark).where(Bookmark.user_id == user, Bookmark.article_id == article_id))
    db.commit()


@router.get("/preferences", response_model=PreferencesIn)
def preferences(user: str = Depends(current_user), db: Session = Depends(get_db)):
    record = db.get(Preference, user)
    return record.values if record else PreferencesIn()


@router.put("/preferences", response_model=PreferencesIn)
def update_preferences(value: PreferencesIn, user: str = Depends(current_user), db: Session = Depends(get_db)):
    record = db.get(Preference, user)
    if not record:
        record = Preference(user_id=user)
        db.add(record)
    record.values = value.model_dump()
    db.commit()
    return value


@router.get("/ops/runs", dependencies=[Depends(ops_access)])
def runs(db: Session = Depends(get_db)):
    rows = db.scalars(select(IngestionRun).order_by(IngestionRun.id.desc()).limit(50)).all()
    return [{"id": r.id, "started_at": r.started_at, "finished_at": r.finished_at, "status": r.status,
             "fetched": r.fetched, "stored": r.stored, "skipped": r.skipped, "failures": r.failures} for r in rows]
