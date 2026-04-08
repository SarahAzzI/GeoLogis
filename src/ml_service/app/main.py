from fastapi import FastAPI, Request
from .api.v1.router.api import api_router
from .model.database import Base, engine
from pathlib import Path

# Initialize database tables on startup
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    version="1.0.0"
)

app.include_router(api_router)