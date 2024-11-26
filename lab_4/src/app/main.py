from fastapi import FastAPI

from src.app.resources.user_router import router as user_routers
from src.app.core.logging_config import logger


def get_app() -> FastAPI:
    logger.info("Initializing FastAPI application")
    app = FastAPI(
        title="My Google Disk",
        description="Author - Denis Sergeev"
    )
    logger.debug("Including user routers")
    app.include_router(router=user_routers)
    return app
