from datetime import datetime, timedelta, timezone
import pytest
from pydantic import ValidationError
from sqlalchemy import select, func
from app.models.entities import Article, Bookmark
from app.schemas.news import Classification
from app.services.processing import normalize_url, publication_time, classify
from app.services.ingestion import store_article, cleanup, ingest
from app.services.providers import ProviderError
from app.core.config import settings
from app.core.auth import current_user
from app.main import app


def raw(title="Chennai cricket academy", url="https://news.example/story", hours=1):
    return {"title":title,"description":"A cricket academy in Chennai explores accessible sports training." if "Chennai" in title else "A global AI model explores software development workflows.","url":url,
            "source":{"name":"Test source"},"publishedAt":(datetime.now(timezone.utc)-timedelta(hours=hours)).isoformat()}


def test_normalize_and_duplicate(db):
    assert normalize_url("https://NEWS.example/story?a=1&utm_source=x#part") == "https://news.example/story?a=1"
    first = raw()
    assert store_article(db,first,"test")
    assert not store_article(db,{**first,"url":first["url"]+"?utm_source=x"},"test")
    db.commit()
    assert db.scalar(select(func.count()).select_from(Article)) == 1
    # Similar headlines from a different report must remain distinct.
    assert store_article(db,raw("Chennai cricket academy prepares", "https://another.example/report"),"test")


def test_expiry_boundary():
    now=datetime.now(timezone.utc)
    with pytest.raises(ValueError): publication_time(now-timedelta(days=4),now)
    assert publication_time(now-timedelta(days=4)+timedelta(microseconds=1),now)
    for value in [None, now+timedelta(seconds=1), datetime.now()]:
        with pytest.raises(ValueError): publication_time(value,now)


def test_schema_and_fallback(monkeypatch):
    monkeypatch.setattr(settings,"ai_provider","none")
    result=classify("Election policy in Tamil Nadu","Government proposal with public consultation.")
    assert result.method=="heuristic" and result.result.state=="Tamil Nadu"
    assert result.result.primary_category=="Politics"
    with pytest.raises(ValidationError): Classification.model_validate({**result.result.model_dump(),"primary_category":"Fake"})
    with pytest.raises(ValidationError): Classification.model_validate({**result.result.model_dump(),"confidence":1.5})


def test_ai_failure_fallback(monkeypatch):
    import openai
    monkeypatch.setattr(settings,"ai_provider","openai")
    monkeypatch.setattr(settings,"openai_api_key","test-only")
    def unavailable(**kwargs): raise RuntimeError("provider failure")
    monkeypatch.setattr(openai,"OpenAI",unavailable)
    assert classify("Software in India", "Supplied description. "*12).method=="heuristic"


def test_api_filters_pagination_and_expired(client,db):
    store_article(db,raw(),"test")
    store_article(db,raw("Global AI model", "https://news.example/ai",2),"test")
    db.commit()
    assert client.get("/api/v1/articles?category=tamilnadu").json()["total"]==1
    assert client.get("/api/v1/articles?category=india").json()["total"]==1
    assert client.get("/api/v1/search?q=AI&region=Global").json()["total"]==1
    assert client.get("/api/v1/articles?source=Test%20source").json()["total"]==2
    assert client.get("/api/v1/articles?page_size=1&page=2").json()["items"][0]["headline"]=="Global AI model"
    assert client.get("/api/v1/articles?page_size=100").status_code==422
    assert client.get("/api/v1/articles?since=2026-01-01").status_code==422
    old=db.scalar(select(Article).where(Article.headline=="Global AI model"))
    old.expires_at=datetime.now(timezone.utc)-timedelta(seconds=1)
    db.add(Bookmark(user_id="one",article_id=old.id));db.commit()
    assert client.get(f"/api/v1/articles/{old.id}").status_code==404
    assert client.get("/api/v1/search?q=AI").json()["total"]==0
    app.dependency_overrides[current_user]=lambda:"one"
    assert client.get("/api/v1/bookmarks").json()==[]
    assert cleanup(db)==1
    assert db.get(Bookmark,("one",old.id)) is None or db.scalar(select(func.count()).select_from(Bookmark))==0


def test_protected_and_ownership(client,db,monkeypatch):
    monkeypatch.setattr(settings,"supabase_url","https://example.supabase.co")
    assert client.get("/api/v1/bookmarks").status_code==401
    assert client.get("/api/v1/preferences",headers={"Authorization":"Bearer invalid"}).status_code==401
    assert client.get("/api/v1/ops/runs").status_code==401
    store_article(db,raw(),"test");db.commit();article=db.scalar(select(Article))
    db.add(Bookmark(user_id="owner",article_id=article.id));db.commit()
    app.dependency_overrides[current_user]=lambda:"other"
    assert client.get("/api/v1/bookmarks").json()==[]
    assert client.delete(f"/api/v1/bookmarks/{article.id}").status_code==204
    assert db.get(Bookmark,("owner",article.id)) is not None
    assert client.put("/api/v1/preferences",json={"categories":["fake"]}).status_code==422
    assert client.put("/api/v1/preferences",json={"categories":["sports"]}).status_code==200
    assert client.get("/api/v1/preferences").json()["categories"]==["sports"]


def test_ingestion_failures_and_idempotence(db):
    sample=raw()
    class TestProvider:
        name="test"
        def fetch(self,query):
            if query=="failure": raise ProviderError("Unavailable")
            if query=="empty": return []
            return [sample,sample]
    first=ingest(db,TestProvider(),["ok","failure"])
    assert first.status=="partial" and first.stored==1 and first.skipped==1
    assert ingest(db,TestProvider(),["empty"]).status=="success"
    assert ingest(db,TestProvider(),["failure"]).status=="failed"
    assert ingest(db,TestProvider(),["ok"]).stored==0


def test_live_mode_never_serves_fixtures(client,db,monkeypatch):
    store_article(db,raw(),"demo");db.commit()
    monkeypatch.setattr(settings,"demo_mode",False)
    assert client.get("/api/v1/articles").json()["total"]==0
    assert client.get("/api/v1/sources").json()==[]


def test_upstream_rate_limit_and_bounded_retry(monkeypatch):
    import httpx
    from app.services.providers import NewsAPIProvider
    import app.services.providers as providers
    monkeypatch.setattr(settings,"newsapi_key","test-only")
    delays=[]
    monkeypatch.setattr(providers.time,"sleep",delays.append)
    responses=iter([httpx.Response(429,headers={"Retry-After":"900"}),httpx.Response(200,json={"status":"ok","articles":[]})])
    monkeypatch.setattr(providers.httpx,"get",lambda *args,**kwargs:next(responses))
    assert NewsAPIProvider().fetch("test")==[] and delays==[30]
    delays.clear()
    monkeypatch.setattr(providers.httpx,"get",lambda *args,**kwargs:httpx.Response(500))
    with pytest.raises(ProviderError): NewsAPIProvider().fetch("test")
    assert delays==[2,4]


def test_valid_jwt_and_expiry(monkeypatch):
    import jwt
    from types import SimpleNamespace
    from cryptography.hazmat.primitives.asymmetric import rsa
    import app.core.auth as auth
    from fastapi import HTTPException
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    monkeypatch.setattr(settings,"supabase_url","https://test.supabase.co")
    client=SimpleNamespace(get_signing_key_from_jwt=lambda token:SimpleNamespace(key=key.public_key()))
    monkeypatch.setattr(auth,"jwks_client",lambda:client)
    claims={"sub":"verified-owner","iss":"https://test.supabase.co/auth/v1","aud":"authenticated","exp":datetime.now(timezone.utc)+timedelta(minutes=5)}
    token=jwt.encode(claims,key,algorithm="RS256")
    assert auth.current_user(f"Bearer {token}")=="verified-owner"
    expired=jwt.encode({**claims,"exp":datetime.now(timezone.utc)-timedelta(seconds=1)},key,algorithm="RS256")
    with pytest.raises(HTTPException): auth.current_user(f"Bearer {expired}")
    wrong=jwt.encode({**claims,"aud":"anonymous"},key,algorithm="RS256")
    with pytest.raises(HTTPException): auth.current_user(f"Bearer {wrong}")
