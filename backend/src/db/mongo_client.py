from pymongo import AsyncMongoClient
from src.config import MONGODB_URI
from src.logging import logger

class MongoDB:
    client: AsyncMongoClient = None
    db = None

    @classmethod
    async def connect(cls):
        # Create a single client instance
        cls.client = AsyncMongoClient(MONGODB_URI)
        cls.db = cls.client['research_agent']
        logger.info("Connected to MongoDB")

    @classmethod
    async def close(cls):
        if cls.client:
            cls.client.close()
            logger.info("MongoDB connection closed")

# This helper will be used by your FastAPI routes via Dependency Injection
async def get_db():
    return MongoDB.db