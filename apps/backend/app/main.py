import os
import time
from collections import defaultdict, deque

from fastapi import FastAPI
import logging
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.channels import router as channels_router
from app.api.video_projects import router as video_projects_router
from app.api.usage import router as usage_router
from app.observability import configure_logging, correlation_id_var

configure_logging()
logger = logging.getLogger("app.request")

app = FastAPI(title="AI Media Operations OS Backend")

allowed_origins = [origin.strip() for origin in os.getenv("CORS_ALLOWLIST", "").split(",") if origin.strip()]
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        now = time.time()
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{request.url.path}"
        queue = self.requests[key]
        while queue and queue[0] <= now - self.window_seconds:
            queue.popleft()
        if len(queue) >= self.max_requests:
            return JSONResponse(status_code=429, content={"detail": "Too Many Requests"})
        queue.append(now)
        correlation_id = request.headers.get("x-correlation-id")
        token = correlation_id_var.set(correlation_id) if correlation_id else None
        try:
            response = await call_next(request)
            logger.info("request", extra={"correlation_id": correlation_id})
            return response
        finally:
            if token is not None:
                correlation_id_var.reset(token)


app.add_middleware(
    RateLimitMiddleware,
    max_requests=int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "60")),
    window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
)

app.include_router(video_projects_router)
app.include_router(channels_router)
app.include_router(usage_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}
