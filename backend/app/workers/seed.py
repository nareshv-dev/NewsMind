"""Explicit, reproducible fictional demo data; never invoked by live ingestion."""
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.entities import Article, Topic
from app.services.ingestion import ensure_categories, store_article

FIXTURES = [
    ("tamilnadu", "A greener commute: imagining the next chapter of Chennai's streets", "A fictional planning exercise explores shaded walking routes, connected cycle lanes and more accessible bus stops in Chennai. This sample illustrates how regional transport coverage appears in NewsMind.", "photo-1654366784694-38e023547208", "Urban life"),
    ("software-ai", "Small AI models, big questions: a guide to running intelligence locally", "This fictional developer workshop compares local AI models on response quality, memory use and privacy. Participants consider when a smaller model is sufficient and when a hosted model is useful.", "photo-1485827404703-89b55fcc595e", "AI models"),
    ("world", "What a resilient city can learn from its waterfront", "A fictional international design forum examines how public waterfronts can combine flood resilience, green spaces and everyday access. The example introduces climate adaptation without reporting a real event.", "photo-1519501025264-65ba15a82390", "Climate"),
    ("sports", "Beyond the scoreboard: the quiet work behind a cricket season", "A fictional cricket academy opens its practice diary to show how coaching, recovery and consistent preparation shape a season. No match results or real players are represented in this sample.", "photo-1540747913346-19e32dc3e97e", "Cricket"),
    ("india", "The reading room returns: a sample look at India's community libraries", "A fictional community-library initiative in India brings shared reading spaces, lending collections and accessible learning sessions together. This demonstration is designed to represent national culture coverage.", "photo-1507842217343-583bb7270b66", "Culture"),
    ("product-updates", "A more thoughtful device: exploring repairable everyday technology", "A fictional product concept uses replaceable components and clearly documented repairs. This example considers practical questions about product longevity, maintenance and responsible gadget design.", "photo-1517336714731-489689fd1ca8", "Gadgets"),
    ("politics", "Reading a policy proposal: the questions that matter before a vote", "A fictional election policy discussion in India examines funding, implementation timelines and public consultation. This sample shows how qualified policy summaries can help readers follow the legislative process.", "photo-1529107386315-e1a2ed48a620", "Policy"),
    ("tamilnadu", "Madurai's public spaces, seen through the eyes of its residents", "A fictional neighbourhood consultation in Madurai gathers ideas for shaded squares, accessible seating and community gathering spaces. This is illustrative regional coverage rather than a report of an actual consultation.", "photo-1606293926075-69a00dbfde81", "Urban life"),
    ("software-ai", "The open-source toolkit making developer workflows simpler", "A fictional software project combines clear documentation, focused tools and transparent release notes. This sample describes developer priorities without claiming a real product release.", "photo-1498050108023-c5249f4df085", "Developer tools"),
    ("sports", "Football at the grassroots: building a place for everyone to play", "A fictional football programme focuses on shared pitches, inclusive coaching and consistent training schedules. This example explores participation without inventing tournament outcomes.", "photo-1574629810360-7efbbe195018", "Football"),
    ("world", "A shared table: an example of international cooperation in practice", "A fictional diplomacy roundtable considers how cities can exchange ideas on housing and public services. This sample shows an international-relations story with no fabricated agreements.", "photo-1451187580459-43490279c0fa", "International relations"),
    ("india", "An everyday journey through India's changing railway stations", "A fictional passenger-experience study in India explores clearer signage, accessible platforms and better connections to local transport. It demonstrates an infrastructure story without announcing real construction.", "photo-1474487548417-781cb71495f3", "Infrastructure"),
    ("product-updates", "Release notes worth reading: a sample of transparent product updates", "A fictional product release note explains what changed, known limitations and migration steps. This example shows a product update without promoting a real service.", "photo-1519389950473-47ba0277781c", "Product launches"),
    ("politics", "Public consultation, explained: from a question to a policy decision", "A fictional government consultation in Tamil Nadu illustrates how feedback may be collected and evaluated. The sample preserves the distinction between a proposed policy and an adopted decision.", "photo-1529107386315-e1a2ed48a620", "Policy"),
    ("software-ai", "Testing an AI assistant: looking beyond a convincing answer", "A fictional AI evaluation exercise checks source grounding, uncertainty and failure handling. This sample introduces useful software testing principles without reporting a real benchmark.", "photo-1485827404703-89b55fcc595e", "AI models"),
    ("tamilnadu", "Coimbatore's makers: a sample story about craft and community", "A fictional workshop series in Coimbatore brings traditional craft and shared learning together. This sample demonstrates local community coverage in the Tamilnadu feed.", "photo-1452860606245-08befc0ff44b", "Culture"),
]


def seed():
    if not settings.demo_mode:
        raise RuntimeError("Seeding requires DEMO_MODE=true; live data is never replaced")
    with SessionLocal() as db:
        ensure_categories(db)
        for index, (category, title, description, image, topic) in enumerate(FIXTURES):
            reference = f"demo:fixture-{index}"
            existing = db.scalar(select(Article).where(Article.provider_ref == reference))
            if existing:
                existing.image_url = f"https://images.unsplash.com/{image}?auto=format&fit=crop&w=1400&q=85"
                continue
            now = datetime.now(timezone.utc)
            store_article(db, {"id": f"fixture-{index}", "title": title, "description": description,
                "url": f"https://example.com/newsmind/demo/{index}", "source": {"name": "NewsMind Demo Desk"},
                "urlToImage": f"https://images.unsplash.com/{image}?auto=format&fit=crop&w=1400&q=85",
                "publishedAt": (now - timedelta(hours=index * 3 + 1)).isoformat()}, "demo", now)
            article = db.scalar(select(Article).where(Article.provider_ref == reference))
            article.category_slug = category
            article.classification_method = "demo_fixture"
            article.model_version = "fixtures:v1"
            topic_record = db.scalar(select(Topic).where(Topic.name == topic))
            if not topic_record:
                topic_record = Topic(name=topic)
                db.add(topic_record)
                db.flush()
            if topic_record not in article.topics:
                article.topics.append(topic_record)
        db.commit()
    print("Demo fixtures seeded. Existing fixtures were preserved. Run cleanup first to refresh expired fixtures.")


if __name__ == "__main__":
    seed()
