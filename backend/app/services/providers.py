import time
from datetime import datetime, timedelta, timezone
from typing import Protocol
import httpx
from app.core.config import settings


class Provider(Protocol):
    name: str
    def fetch(self, query: str) -> list[dict]: ...


class ProviderError(Exception):
    pass


class NewsAPIProvider:
    name = "newsapi"

    def fetch(self, query):
        if not settings.newsapi_key:
            raise ProviderError("NewsAPI credentials are not configured")
        for attempt in range(3):
            try:
                response = httpx.get("https://newsapi.org/v2/everything", headers={"X-Api-Key": settings.newsapi_key},
                    params={"q": query, "from": (datetime.now(timezone.utc) - timedelta(days=4)).isoformat(),
                            "sortBy": "publishedAt", "pageSize": 100}, timeout=15)
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt == 2:
                        raise ProviderError(f"Upstream temporarily unavailable (HTTP {response.status_code})")
                    delay = min(30, max(1, int(response.headers.get("Retry-After", 2 ** (attempt + 1)))))
                    time.sleep(delay)
                    continue
                if response.status_code != 200:
                    raise ProviderError(f"Upstream rejected request (HTTP {response.status_code})")
                payload = response.json()
                if payload.get("status") != "ok" or not isinstance(payload.get("articles"), list):
                    raise ProviderError("Invalid upstream response")
                return payload["articles"]
            except (httpx.HTTPError, ValueError):
                if attempt == 2:
                    raise ProviderError("Upstream network or response error") from None
                time.sleep(2 ** attempt)
        raise ProviderError("Fetch failed")
