import argparse
import logging
import time
from pathlib import Path
from sqlalchemy import text
from app.core.database import engine, SessionLocal
from app.core.config import settings
from app.services.ingestion import ingest, cleanup
from app.services.providers import NewsAPIProvider
from app.services.rss import RSSProvider

logger = logging.getLogger(__name__)


def run_once():
    if settings.demo_mode:
        raise RuntimeError("Live ingestion is disabled in demo mode. Set DEMO_MODE=false first.")
    # Keep the advisory lock connection open across the entire ingestion run.
    with engine.connect() as lock_connection:
        local_lock = None
        if engine.dialect.name == "postgresql":
            acquired = lock_connection.scalar(text("SELECT pg_try_advisory_lock(742918)"))
            if not acquired:
                logger.info("Another ingestion worker is active")
                return
        else:
            import os
            local_lock = Path(".ingestion.lock")
            try:
                fd = os.open(local_lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
            except FileExistsError:
                logger.info("Another worker is active; see docs for stale-lock recovery")
                return
        try:
            with SessionLocal() as db:
                if settings.news_provider == "rss":
                    provider, queries = RSSProvider(), settings.rss_feeds
                elif settings.news_provider == "newsapi":
                    provider, queries = NewsAPIProvider(), settings.news_queries
                else:
                    raise RuntimeError("NEWS_PROVIDER must be rss or newsapi")
                result = ingest(db, provider, [q.strip() for q in queries.split("|") if q.strip()])
                logger.info("Ingestion %s: fetched=%s stored=%s skipped=%s", result.status, result.fetched, result.stored, result.skipped)
        finally:
            if local_lock:
                local_lock.unlink(missing_ok=True)
            else:
                lock_connection.execute(text("SELECT pg_advisory_unlock(742918)"))


def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["once", "loop", "cleanup"])
    args = parser.parse_args()
    if args.command == "once":
        run_once()
    elif args.command == "cleanup":
        with SessionLocal() as db:
            logger.info("Deleted %s expired articles", cleanup(db))
    else:
        next_fetch = 0
        while True:
            try:
                with SessionLocal() as db:
                    cleanup(db)
                if time.monotonic() >= next_fetch and not settings.demo_mode:
                    run_once()
                    next_fetch = time.monotonic() + settings.fetch_interval_seconds
            except Exception as error:
                logger.error("Worker cycle failed (%s)", type(error).__name__)
                next_fetch = time.monotonic() + 60
            time.sleep(max(1, settings.cleanup_interval_seconds))


if __name__ == "__main__":
    main()
