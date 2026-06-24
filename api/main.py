"""
Distributed System Graph API

FastAPI application exposing graph generation, import, analysis, and query capabilities.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.active_tasks: dict = {}
    yield
    for task_id, task in list(app.state.active_tasks.items()):
        task.cancel()
        task_id_ref = task_id
    app.state.active_tasks.clear()


logger = logging.getLogger(__name__)

# Import routers
from api.routers import (
    health,
    graph,
    analysis,
    components,
    statistics,
    simulation,
    classification,
    validation,
    prediction,
    traffic,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize FastAPI app
app = FastAPI(
    title="Distributed System Graph API",
    description="API for generating, analyzing, and querying distributed system graphs",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS to allow frontend access from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Must be False when allow_origins is "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(graph.router)
app.include_router(analysis.router)
app.include_router(components.router)
app.include_router(statistics.router)
app.include_router(simulation.router)
app.include_router(classification.router)
app.include_router(validation.router)
app.include_router(prediction.router)
app.include_router(traffic.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
