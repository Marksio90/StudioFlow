from fastapi import FastAPI

from app.api.video_projects import router as video_projects_router
from app.api.usage import router as usage_router

app = FastAPI(title="AI Media Operations OS Backend")
app.include_router(video_projects_router)
app.include_router(usage_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}
