from fastapi import FastAPI

from src.app.resources.user_router import router as user_routers


def get_app() -> FastAPI:
    app = FastAPI(
        title="My Google Disk",
        description="Author - Denis Sergeev"
    )
    app.include_router(router=user_routers)
    return app
