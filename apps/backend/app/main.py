from fastapi import FastAPI

app = FastAPI(title="AI Media Operations OS Backend")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}
