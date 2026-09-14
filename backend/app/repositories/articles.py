from datetime import datetime, timezone
import re
from sqlalchemy import select, func, or_
from app.models.entities import Article, Source, Topic
from app.core.config import settings


def active_query(now=None):
    stmt = select(Article).where(Article.expires_at > (now or datetime.now(timezone.utc)))
    return stmt if settings.demo_mode else stmt.where(Article.provider != "demo")


def filtered_query(db, q=None, category=None, region=None, source=None, language=None, topic=None, since=None, until=None):
    stmt = active_query()
    if category:
        if category == "tamilnadu":
            stmt = stmt.where(or_(Article.category_slug == category, Article.state == "Tamil Nadu"))
        elif category == "india":
            stmt = stmt.where(or_(Article.category_slug == category, Article.country == "India"))
        elif category == "world":
            stmt = stmt.where(Article.geographic_scope == "Global")
        else:
            stmt = stmt.where(Article.category_slug == category)
    for field, value in [(Article.geographic_scope, region), (Article.language, language)]:
        if value:
            stmt = stmt.where(field == value)
    if source:
        stmt = stmt.where(Article.source.has(Source.name == source))
    if topic:
        stmt = stmt.where(Article.topics.any(Topic.name == topic))
    if since:
        stmt = stmt.where(Article.published_at >= since)
    if until:
        stmt = stmt.where(Article.published_at <= until)
    if q:
        if db.bind.dialect.name == "postgresql":
            document = func.to_tsvector("simple", Article.headline + " " + func.coalesce(Article.description, ""))
            stmt = stmt.where(document.op("@@")(func.plainto_tsquery("simple", q)))
        else:
            # Token conjunction provides a portable local-development search.
            for token in q.split():
                pattern = rf"(?i)\b{re.escape(token)}\b"
                stmt = stmt.where(or_(Article.headline.regexp_match(pattern), Article.description.regexp_match(pattern)))
    return stmt
