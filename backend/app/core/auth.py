from functools import lru_cache
import jwt
from fastapi import HTTPException, Header
from app.core.config import settings


@lru_cache
def jwks_client():
    return jwt.PyJWKClient(f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json", timeout=10)


def current_user(authorization: str | None = Header(default=None)):
    if not settings.supabase_url:
        raise HTTPException(503, "Accounts are not configured")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Sign in required")
    token = authorization[7:]
    try:
        if jwt.get_unverified_header(token).get("alg") not in {"ES256", "RS256"}:
            raise ValueError("Unsupported signing algorithm")
        key = jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(token, key.key, algorithms=["ES256", "RS256"], audience="authenticated",
                             issuer=f"{settings.supabase_url.rstrip('/')}/auth/v1", options={"require": ["exp", "sub", "iss", "aud"]})
        return payload["sub"]
    except Exception:
        raise HTTPException(401, "Invalid or expired session") from None


def ops_access(authorization: str | None = Header(default=None)):
    import secrets
    if not settings.ops_token or not authorization or not secrets.compare_digest(authorization, f"Bearer {settings.ops_token}"):
        raise HTTPException(401, "Operational authorization required")
