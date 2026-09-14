from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete, update, or_
from sqlalchemy.exc import IntegrityError
from app.models.entities import Article, Source, Category, Topic, IngestionRun
from app.schemas.news import CATEGORIES
from app.services.processing import normalize_url, hash_text, publication_time, classify, PROCESSING_VERSION
from app.services.providers import ProviderError
from app.core.config import settings


def ensure_categories(db):
    for slug, name in CATEGORIES.items():
        if not db.get(Category, slug):
            db.add(Category(slug=slug, name=name))
    db.flush()


def store_article(db, raw, provider, now=None):
    now = now or datetime.now(timezone.utc)
    headline = str(raw.get("title") or "").strip()
    if not headline or headline == "[Removed]" or len(headline) > 2000:
        raise ValueError("Invalid headline")
    published = publication_time(raw.get("publishedAt"), now)
    url = normalize_url(str(raw.get("url") or ""))
    if len(url) > 2048:
        raise ValueError("Source URL too long")
    description = str(raw.get("description") or "").strip()[:5000] or None
    source_name = str((raw.get("source") or {}).get("name") or "Unknown source")[:200]
    fingerprint = hash_text(f"{source_name.lower()}|{headline.lower()}|{published.isoformat()}")
    provider_ref = f"{provider}:{raw.get('id') or hash_text(url)}"
    content_hash = hash_text(f"{headline}|{description}")
    existing = db.scalar(select(Article).where(or_(Article.normalized_url == url, Article.fingerprint == fingerprint, Article.provider_ref == provider_ref)))
    if existing:
        # Preserve original expiry and avoid paying to reprocess unchanged content.
        return False
    cache_version = f"{settings.ai_model}:{PROCESSING_VERSION}" if settings.ai_provider == "openai" and settings.openai_api_key else PROCESSING_VERSION
    cached = db.scalar(select(Article).where(Article.content_hash == content_hash,
                       Article.model_version == cache_version, Article.expires_at > now).limit(1))
    processed = classify(headline, description) if not cached else None
    if cached:
        category_slug, topics = cached.category_slug, [t.name for t in cached.topics]
        values = {k: getattr(cached, k) for k in ["summary", "geographic_scope", "country", "state", "language", "confidence", "classification_method", "model_version", "summary_method"]}
    else:
        result = processed.result
        category_slug = next(slug for slug, name in CATEGORIES.items() if name == result.primary_category)
        topics = result.topics
        values = result.model_dump(exclude={"primary_category", "topics"})
        values.update(classification_method=processed.method, model_version=processed.version, summary_method=processed.summary_method)
    if provider == "rss" and values["classification_method"] != "ai":
        hint = raw.get("_feed_category")
        if hint in CATEGORIES and category_slug in {"world", "india", "tamilnadu"}:
            category_slug = hint
        if raw.get("_feed_state") == "Tamil Nadu":
            values.update(country="India", state="Tamil Nadu", geographic_scope="Regional")
            if category_slug in {"world", "india"}:
                category_slug = "tamilnadu"
        elif raw.get("_feed_country") == "India":
            values["country"] = "India"
            if values["geographic_scope"] != "Regional":
                values["geographic_scope"] = "National"
            if category_slug == "world":
                category_slug = "india"
        values["classification_method"] = "feed+heuristic"
        values["model_version"] = "rss:v1"
    source = db.scalar(select(Source).where(Source.name == source_name))
    if not source:
        source = Source(name=source_name)
        db.add(source)
        db.flush()
    topic_records = []
    for name in topics:
        topic = db.scalar(select(Topic).where(Topic.name == name))
        if not topic:
            topic = Topic(name=name)
            db.add(topic)
            db.flush()
        topic_records.append(topic)
    image = raw.get("urlToImage")
    if image:
        try:
            normalize_url(image)
        except ValueError:
            image = None
    db.add(Article(provider=provider, provider_ref=provider_ref, original_url=str(raw["url"]), normalized_url=url,
        headline=headline, description=description, image_url=image, source_id=source.id, category_slug=category_slug,
        fingerprint=fingerprint, content_hash=content_hash, published_at=published, fetched_at=now, updated_at=now,
        expires_at=published + timedelta(days=4), topics=topic_records, **values))
    db.flush()
    return True


def cleanup(db, now=None):
    result = db.execute(delete(Article).where(Article.expires_at <= (now or datetime.now(timezone.utc))))
    # Operational metadata has its own bounded retention and contains no article content.
    db.execute(delete(IngestionRun).where(IngestionRun.started_at < datetime.now(timezone.utc) - timedelta(days=30)))
    db.commit()
    return result.rowcount


def ingest(db, provider, queries):
    ensure_categories(db)
    # The worker holds its exclusive lock here; unfinished runs belong to a prior crash.
    db.execute(update(IngestionRun).where(IngestionRun.status == "running").values(
        status="failed", finished_at=datetime.now(timezone.utc), failures=[{"error": "Previous worker interrupted"}]))
    run = IngestionRun(status="running", failures=[])
    db.add(run)
    db.commit()
    failures = []
    for query in queries:
        try:
            articles = provider.fetch(query)
            run.fetched += len(articles)
            for raw in articles:
                try:
                    with db.begin_nested():
                        added = store_article(db, raw, provider.name)
                    run.stored += int(added)
                    run.skipped += int(not added)
                except (ValueError, IntegrityError, TypeError, AttributeError):
                    run.skipped += 1
        except ProviderError as error:
            failures.append({"query": query, "error": str(error)})
        db.commit()
    run.failures = failures
    run.status = "partial" if failures and run.stored else "failed" if failures else "success"
    run.finished_at = datetime.now(timezone.utc)
    db.commit()
    return run
