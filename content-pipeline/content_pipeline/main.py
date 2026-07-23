# Created: Thursday Jul 23, 2026, 11:13 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 12:00 PM (UTC-6)

"""Content Pipeline FastAPI application."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from content_pipeline.api import clients, runs, stages

app = FastAPI(
    title="Content Pipeline",
    description="Multi-client blog production pipeline",
    version="0.1.0",
)

# Add CORS middleware for localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(clients.router)
app.include_router(runs.router)
app.include_router(stages.router)


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint for deployment verification."""
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "version": "0.1.0"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
