"""Publisher RSS metadata for personal evaluation; no scraping article bodies."""
import calendar
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
import re
import time
import feedparser
import httpx
from app.services.providers import ProviderError


@dataclass(frozen=True)
class FeedSpec:
    url: str
    source: str
    category: str | None = None
    country: str | None = None
    state: str | None = None


FEEDS = {
    "ndtv-india": FeedSpec("https://feeds.feedburner.com/ndtvnews-india-news", "NDTV.com", country="India"),
    "ndtv-world": FeedSpec("https://feeds.feedburner.com/ndtvnews-world-news", "NDTV.com"),
    "ndtv-sports": FeedSpec("https://feeds.feedburner.com/ndtvsports-latest", "NDTV.com", "sports"),
    "gadgets360": FeedSpec("https://feeds.feedburner.com/gadgets360-latest", "Gadgets 360", "product-updates"),
    "hindu-tamilnadu": FeedSpec("https://www.thehindu.com/news/national/tamil-nadu/feeder/default.rss", "The Hindu", country="India", state="Tamil Nadu"),
    "bbc-world": FeedSpec("https://feeds.bbci.co.uk/news/world/rss.xml", "BBC News"),
    "bbc-sports": FeedSpec("https://feeds.bbci.co.uk/sport/rss.xml", "BBC Sport", "sports"),
    "bbc-technology": FeedSpec("https://feeds.bbci.co.uk/news/technology/rss.xml", "BBC News", "software-ai"),
    "bbc-politics": FeedSpec("https://feeds.bbci.co.uk/news/politics/rss.xml", "BBC News", "politics"),
}


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain_text(value):
    parser = PlainText()
    parser.feed(str(value or ""))
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


def parse_feed(content: bytes, spec: FeedSpec) -> list[dict]:
    feed = feedparser.parse(content)
    if not feed.version or feed.bozo:
        raise ProviderError("Invalid RSS/Atom response")
    articles = []
    for entry in feed.entries[:200]:
        published = entry.get("published_parsed")
        image = next((item.get("url") for item in entry.get("media_thumbnail", []) if item.get("url")), None)
        if not image:
            image = next((item.get("url") for item in entry.get("media_content", [])
                          if item.get("url") and (item.get("medium") == "image" or str(item.get("type", "")).startswith("image/"))), None)
        if not image:
            image = next((item.get("href") for item in entry.get("links", [])
                          if item.get("rel") == "enclosure" and str(item.get("type", "")).startswith("image/")), None)
        articles.append({
            "id": f"{spec.source}:{entry.get('id') or entry.get('link')}",
            "title": plain_text(entry.get("title")), "description": plain_text(entry.get("summary")) or None,
            "url": entry.get("link"), "source": {"name": spec.source}, "urlToImage": image,
            "publishedAt": datetime.fromtimestamp(calendar.timegm(published), timezone.utc).isoformat() if published else None,
            # Hints originate in our allowlisted feed registry, never in article instructions.
            "_feed_category": spec.category, "_feed_country": spec.country, "_feed_state": spec.state,
        })
    return articles


class RSSProvider:
    name = "rss"

    def fetch(self, query):
        spec = FEEDS.get(query)
        if not spec:
            raise ProviderError("Unknown RSS feed ID")
        for attempt in range(3):
            try:
                with httpx.stream("GET", spec.url, timeout=15, follow_redirects=True,
                                  headers={"User-Agent": "NewsMind/0.1 (personal RSS reader)"}) as response:
                    if response.status_code == 429 or response.status_code >= 500:
                        if attempt == 2:
                            raise ProviderError(f"RSS unavailable (HTTP {response.status_code})")
                        time.sleep(min(10, 2 ** (attempt + 1)))
                        continue
                    if response.status_code != 200:
                        raise ProviderError(f"RSS rejected request (HTTP {response.status_code})")
                    chunks, size = [], 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > 2_000_000:
                            raise ProviderError("RSS response exceeds size limit")
                        chunks.append(chunk)
                return parse_feed(b"".join(chunks), spec)
            except httpx.HTTPError:
                if attempt == 2:
                    raise ProviderError("RSS network error") from None
                time.sleep(2 ** attempt)
        raise ProviderError("RSS fetch failed")
