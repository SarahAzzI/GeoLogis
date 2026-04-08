from fastapi import FastAPI
from .api.v1.router.api import api_router
from .model.database import Base, engine

Base.metadata.create_all(bind=engine)
 
app = FastAPI(
    title="GeoLogis ML Service",
    version="1.0.0",
)
 
app.include_router(api_router)