from datetime import datetime, timezone
from sqlalchemy import select
import pytest
from app.services.rss import FeedSpec, parse_feed, plain_text, RSSProvider
from app.services.providers import ProviderError
from app.services.ingestion import store_article
from app.models.entities import Article


def feed(date=None):
    date = date or datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    return f'''<?xml version="1.0"?><rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel><title>Test</title><link>https://example.com</link><description>Test</description><item><title>Public consultation on a policy proposal</title><link>https://example.com/report</link><guid>one</guid><pubDate>{date}</pubDate><description>&lt;p&gt;Government policy is open for public consultation.&lt;/p&gt;</description><media:thumbnail url="https://example.com/photo.jpg"/></item></channel></rss>'''.encode()


def test_parse_and_geography(db):
    spec = FeedSpec("https://example.com/rss", "Test newspaper", country="India", state="Tamil Nadu")
    articles = parse_feed(feed(), spec)
    assert articles[0]["description"] == "Government policy is open for public consultation."
    assert articles[0]["urlToImage"] == "https://example.com/photo.jpg"
    assert store_article(db, articles[0], "rss")
    assert not store_article(db, articles[0], "rss")
    db.commit()
    article = db.scalar(select(Article))
    assert article.state == "Tamil Nadu" and article.category_slug == "politics"
    assert article.classification_method == "feed+heuristic"


def test_invalid_empty_and_expired(db):
    spec = FeedSpec("https://example.com/rss", "Test newspaper")
    with pytest.raises(ProviderError): parse_feed(b"<html>Not an RSS feed</html>", spec)
    with pytest.raises(ProviderError): RSSProvider().fetch("not-allowlisted")
    with pytest.raises(ValueError): store_article(db, parse_feed(feed("Mon, 01 Jan 2024 12:00:00 GMT"), spec)[0], "rss")
    assert parse_feed(b'<rss version="2.0"><channel><title>Empty</title></channel></rss>', spec) == []
    assert plain_text("<p>A &amp; B</p><script>unwanted()</script>") == "A & B"
