"""Initial news, taxonomy, ingestion, and account schema."""
from alembic import op
from sqlalchemy import Column, String, Text, DateTime, Float, Integer, JSON, ForeignKey

revision = "0001"
down_revision = None


def upgrade():
    op.create_table("sources", Column("id", Integer, primary_key=True), Column("name", String(200), nullable=False, unique=True))
    op.create_table("categories", Column("slug", String(40), primary_key=True), Column("name", String(50), nullable=False, unique=True))
    op.create_table("topics", Column("id", Integer, primary_key=True), Column("name", String(80), nullable=False, unique=True))
    op.create_table("articles",
        Column("id", String(36), primary_key=True), Column("provider", String(40), nullable=False),
        Column("provider_ref", String(512), nullable=False, unique=True), Column("original_url", Text, nullable=False),
        Column("normalized_url", String(2048), nullable=False, unique=True), Column("headline", Text, nullable=False),
        Column("description", Text), Column("summary", Text), Column("image_url", Text),
        Column("source_id", Integer, ForeignKey("sources.id"), nullable=False),
        Column("category_slug", String(40), ForeignKey("categories.slug"), nullable=False),
        Column("geographic_scope", String(20), nullable=False), Column("country", String(80)), Column("state", String(80)),
        Column("language", String(12), nullable=False), Column("confidence", Float, nullable=False),
        Column("classification_method", String(30), nullable=False), Column("model_version", String(100), nullable=False),
        Column("summary_method", String(30), nullable=False), Column("fingerprint", String(64), nullable=False, unique=True),
        Column("content_hash", String(64), nullable=False), Column("published_at", DateTime(timezone=True), nullable=False),
        Column("fetched_at", DateTime(timezone=True), nullable=False), Column("updated_at", DateTime(timezone=True), nullable=False),
        Column("expires_at", DateTime(timezone=True), nullable=False))
    for column in ["source_id", "category_slug", "geographic_scope", "language", "content_hash", "published_at", "expires_at"]:
        op.create_index(f"ix_articles_{column}", "articles", [column])
    op.create_index("ix_articles_feed", "articles", ["category_slug", "expires_at", "published_at"])
    if op.get_bind().dialect.name == "postgresql":
        op.execute("CREATE INDEX ix_articles_search ON articles USING gin (to_tsvector('simple', headline || ' ' || coalesce(description, ''))) ")
    op.create_table("article_topics", Column("article_id", String(36), ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
                    Column("topic_id", Integer, ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True))
    op.create_table("ingestion_runs", Column("id", Integer, primary_key=True), Column("started_at", DateTime(timezone=True), nullable=False),
        Column("finished_at", DateTime(timezone=True)), Column("status", String(30), nullable=False),
        Column("fetched", Integer, nullable=False), Column("stored", Integer, nullable=False), Column("skipped", Integer, nullable=False),
        Column("failures", JSON, nullable=False))
    op.create_table("bookmarks", Column("user_id", String(128), primary_key=True),
        Column("article_id", String(36), ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
        Column("created_at", DateTime(timezone=True), nullable=False))
    op.create_table("preferences", Column("user_id", String(128), primary_key=True), Column("values", JSON, nullable=False))


def downgrade():
    for table in ["preferences", "bookmarks", "ingestion_runs", "article_topics", "articles", "topics", "categories", "sources"]:
        op.drop_table(table)
