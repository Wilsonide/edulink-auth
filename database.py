import contextlib
from typing import AsyncIterator
from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)

from sqlalchemy.orm import declarative_base

Base = declarative_base()

class DatabaseSessionManager:
    def __init__(self):
        self._engine: AsyncEngine | None = None
        self._session_maker: async_sessionmaker | None = None

    def init(self, host: str):
        self._engine = create_async_engine(host,echo=True)
        self._session_maker = async_sessionmaker(autocommit=False, bind=self._engine, expire_on_commit=False)

    async def close(self):
        if self._engine is None:
            raise Exception("Database session manager is not initialized")
        await self._engine.dispose()
        self._engine = None
        self._session_maker = None


    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception("Database session manager is not initialized")
        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception as e:
                print("Error =================================================================", e)
                """ print("Error connecting to database", e) """
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._session_maker is None:
            raise Exception("Database session manager is not initialized")
        sesion = self._session_maker()
        try:
            yield sesion
        except Exception:
            """ await sesion.rollback() """
            raise
        finally:
            await sesion.close()

    async def create_all(self,conn:AsyncConnection):
        await conn.run_sync(Base.metadata.create_all)
        print("Database tables successfully created")
    
    async def drop_all(self,conn:AsyncConnection):
        await conn.run_sync(Base.metadata.create_all)

sessionmanager = DatabaseSessionManager()


async def get_db():
    async with sessionmanager.session() as session:
        yield session