import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.api.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
app = FastAPI(title="NewsMind API", version="1.0.0")
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
from slowapi.middleware import SlowAPIMiddleware
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","),
                   allow_methods=["GET", "PUT", "DELETE"], allow_headers=["Authorization", "Content-Type"])


@app.exception_handler(Exception)
async def server_error(request: Request, error: Exception):
    logging.getLogger(__name__).error("Unhandled server error: %s", type(error).__name__)
    return JSONResponse(status_code=500, content={"detail": "Service temporarily unavailable"})

app.include_router(router)
