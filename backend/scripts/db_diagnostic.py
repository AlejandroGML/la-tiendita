"""Diagnostic script — run inside the Fly machine to debug DB connectivity."""
import asyncio
import traceback

from app.config import settings
from app.db.engine import _async_database_url


async def main() -> None:
    print(f"DATABASE_URL: {settings.DATABASE_URL[:80]}")
    normalized = _async_database_url(settings.DATABASE_URL)
    print(f"normalized:   {normalized[:80]}")

    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text

    engine = create_async_engine(normalized)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("SELECT 1:", result.scalar_one())
    except Exception:
        traceback.print_exc()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
