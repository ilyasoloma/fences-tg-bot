import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

load_dotenv()
client: AsyncIOMotorClient = AsyncIOMotorClient(os.getenv("MONGO_DB_URL", "mongodb://localhost:27017"))
db: AsyncIOMotorDatabase = client.fences


def get_db() -> AsyncIOMotorDatabase:
    return db
