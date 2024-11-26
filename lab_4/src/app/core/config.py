from dynaconf import Dynaconf
from pydantic import AnyUrl
from pydantic_settings import BaseSettings

_settings = Dynaconf(
    settings_files=["config.yaml"]
)
_project_timezone = "Europe/Moscow"

_db_dsn = AnyUrl.build(
    scheme="postgresql+asyncpg",
    username=_settings.database.user,
    password=_settings.database.password,
    host=_settings.database.host,
    port=_settings.database.port,
    path=_settings.database.db,
)


class Settings(BaseSettings):
    db_dsn: str
    app_name: str
    timezone: str
    secret_key: str
    algorithm: str


settings = Settings(
    db_dsn=str(_db_dsn),
    app_name="My Google Disk",
    timezone=_project_timezone,
    secret_key=_settings.jwt.secret_key,
    algorithm=_settings.jwt.algorithm
)
