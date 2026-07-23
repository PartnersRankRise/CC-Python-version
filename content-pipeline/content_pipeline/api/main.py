# Created: Thursday Jul 23, 2026, 4:10 PM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 4:18 PM (UTC-6)

"""FastAPI application entry point."""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env from project root FIRST, before any other imports
# Current file is at: CC-Python-version/content-pipeline/content_pipeline/api/main.py
# So we go up 4 levels: main.py -> api -> content_pipeline -> content-pipeline -> CC-Python-version
env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
if env_path.exists():
    print(f"Loading .env from {env_path}")
    load_dotenv(env_path, verbose=True)
else:
    print(f"WARNING: .env not found at {env_path}")

# NOW import routers after .env is loaded
from content_pipeline.api import clients, runs, run_init_routes

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Content Pipeline API",
    description="Multi-stage blog production pipeline",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler for debugging
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Log all exceptions for debugging."""
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}", exc_info=True)
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__}
    )


# Include routers
app.include_router(clients.router)
app.include_router(runs.router)
app.include_router(run_init_routes.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
