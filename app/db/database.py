from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import MONGO_URI, PGSQL_URL

# 🔹 Conexión a MongoDB
mongo_client = AsyncIOMotorClient(MONGO_URI)
mongo_db = mongo_client.get_database('ArtNova')

# 🔹 Conexión a PostgreSQL con SQLAlchemy
engine = create_async_engine(PGSQL_URL, future=True, echo=False)

SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with SessionLocal() as session:
        yield session

async def get_mongo_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    yield mongo_db

def get_pgsql_celery():
    return SessionLocal()

def get_mongo_celery() -> AsyncIOMotorDatabase:
    return mongo_db

