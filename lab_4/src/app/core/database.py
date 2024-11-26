from src.app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def make_pg_options(
    app_name: str = settings.app_name,
    timezone: str = settings.timezone,
    statement_timeout: int = 40_000,
    lock_timeout: int = 30_000,
    idle_in_transaction_session_timeout: int = 60_000,
) -> dict[str, str]:
    return {
        "application_name": app_name,
        "timezone": timezone,
        "statement_timeout": str(statement_timeout),
        "lock_timeout": str(lock_timeout),
        "idle_in_transaction_session_timeout": str(idle_in_transaction_session_timeout),
    }


async_engine = create_async_engine(
    url=settings.db_dsn,
    connect_args={"server_settings": make_pg_options()}
)

async_session_maker = async_sessionmaker(
    bind=async_engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
